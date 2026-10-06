"""Offline training-date sampling feasibility. Does not create labels or cloud jobs."""

import hashlib
import io
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "outputs/reports/observation_coverage"
OUT = REPORTS / "sampling_feasibility"
SEED = 20261006  # Fixed before computing any retained-outcome metrics; never optimize this seed.
START, END = "2018-01-01", "2023-12-31"
WEATHER = [
    "temperature_max_c",
    "wind_speed_max_ms",
    "rain_168h_nonnegative_mm",
    "soil_water_layer_1_mean",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calendar():
    return pd.date_range(START, END).strftime("%Y-%m-%d").tolist()


def cyclic_block(days, start, count):
    """Uniform start on a cyclic month gives every day inclusion probability k/n."""
    require(0 < count <= len(days) and 0 <= start < len(days), "Invalid monthly block")
    return {days[(start + offset) % len(days)] for offset in range(count)}


def sample_dates(count, seed=SEED):
    require(isinstance(count, int) and 0 < count <= 28, "Invalid sampling size")
    selected, probability = set(), {}
    all_days = calendar()
    for month in sorted({day[:7] for day in all_days}):
        days = [day for day in all_days if day.startswith(month)]
        # Separate stable generator per month; increasing k keeps the same start.
        rng = np.random.default_rng(np.random.SeedSequence([seed, int(month.replace("-", ""))]))
        start = int(rng.integers(len(days)))
        chosen = cyclic_block(days, start, count)
        selected.update(chosen)
        probability.update({day: count / len(days) for day in chosen})
    return selected, probability


def guards(selected):
    require(set(selected) <= set(calendar()), "Sampling outside training")
    requested = {
        (date.fromisoformat(day) + timedelta(days=offset)).isoformat()
        for day in selected
        for offset in (-1, 0, 1)
    }
    return requested & set(calendar()), sorted(requested - set(calendar()))


def target_day(timestamps):
    # Target is (T,T+24h]; an exact midnight detection belongs to the preceding T.
    stamps_ns = pd.to_datetime(timestamps, utc=True).dt.as_unit("ns").astype("int64")
    return pd.to_datetime(stamps_ns - 1, unit="ns", utc=True).dt.strftime("%Y-%m-%d")


def read_catalogue(pair_path, granule_path):
    pairs = pd.read_csv(pair_path, dtype={"pair_key": str})
    sources = pd.read_csv(granule_path, dtype={"pair_key": str})
    for table in (pairs, sources):
        require(table.negative_label_permitted.eq(False).all(), "Catalogue label permission")
        require(
            table.actual_input_identity_verified.eq(False).all(), "Unexpected input verification"
        )
    require(pairs.day.between(START, END).all(), "Catalogue outside training")
    require(not pairs.duplicated(["sensor", "pair_key"]).any(), "Duplicate pair identity")
    require(sources.start_utc.str[:10].between(START, END).all(), "Source outside training")
    require(sources.concept_id.is_unique, "Duplicate source identity")
    require(sources.role.isin(["fire", "geolocation"]).all(), "Unexpected source role")
    require(
        np.isfinite(sources.catalogue_size_bytes_estimate).all()
        and sources.catalogue_size_bytes_estimate.gt(0).all(),
        "Invalid source estimate",
    )
    nominal = pairs.loc[pairs.pair_status.eq("nominal_unique_pair")].copy()
    chosen = sources.merge(nominal[["sensor", "pair_key", "day"]], validate="many_to_one")
    roles = chosen.groupby(["sensor", "pair_key"]).role.agg(list)
    require(len(roles) == len(nominal), "Missing nominal sources")
    require(all(sorted(value) == ["fire", "geolocation"] for value in roles), "Source roles")
    require(chosen.start_utc.str[:10].eq(chosen.day).all(), "Source date mismatch")
    require(len(chosen) == 2 * len(nominal), "Nominal source count")
    chosen["estimated_bytes"] = chosen.catalogue_size_bytes_estimate.round().astype("int64")
    sizes = chosen.groupby(["sensor", "pair_key"]).estimated_bytes.sum()
    nominal["estimated_bytes"] = [sizes.loc[(r.sensor, r.pair_key)] for r in nominal.itertuples()]
    return pairs, nominal


def cost(dates, pairs, nominal, seconds_per_pair):
    picked = nominal.loc[nominal.day.isin(dates)]
    pending = picked.loc[~picked.day.str.startswith("2023-07")]
    unpaired = pairs.loc[pairs.day.isin(dates) & ~pairs.pair_status.eq("nominal_unique_pair")]
    return {
        "nominal_pairs": len(picked),
        "nominal_source_files": len(picked) * 2,
        "pending_nominal_pairs": len(pending),
        "reused_July_nominal_pairs": len(picked) - len(pending),
        "pending_catalogue_estimated_GB_decimal": int(pending.estimated_bytes.sum()) / 1e9,
        "pending_pair_phase_hours_extrapolated": len(pending) * seconds_per_pair / 3600,
        "unpaired_records_not_discarded_or_negative": len(unpaired),
    }


def load_events(firms):
    results, paths = {}, []
    identities = set(firms.detection_id)
    for path in sorted((ROOT / "data/interim/event_grouping").glob("*_assignments.csv")):
        table = pd.read_csv(path, usecols=["detection_id", "timestamp", "cluster_id"])
        require(table.detection_id.is_unique, "Duplicate grouping assignment")
        require(set(table.detection_id) == identities, "Grouping population changed")
        joined = table.merge(
            firms[["detection_id", "detection_timestamp_utc"]], validate="one_to_one"
        )
        require(
            pd.to_datetime(joined.timestamp, utc=True)
            .eq(pd.to_datetime(joined.detection_timestamp_utc, utc=True))
            .all(),
            "Grouping timestamp changed",
        )
        # Explicitly parse before minimum: CSV lexical ordering is not a time contract.
        first = (
            table.assign(stamp=pd.to_datetime(table.timestamp, utc=True))
            .groupby("cluster_id")
            .stamp.min()
        )
        results[path.stem.removesuffix("_assignments")] = target_day(first).reset_index(drop=True)
        paths.append(path)
    require(len(results) == 9, "Expected nine exploratory grouping scenarios")
    return results, paths


def weather_summary(preparation, ids):
    expected = {r["date"]: r for r in preparation["days"] if r["split"] == "train"}
    require(set(expected) == set(calendar()), "Weather training calendar")

    def read(day):
        path = ROOT / "data/interim/meteorology/model_v1/daily" / f"{day}.csv"
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == expected[day]["output_sha256"], "Weather SHA")
        table = pd.read_csv(
            io.BytesIO(data),
            usecols=["grid_id", "prediction_timestamp_utc", "weather_primary_eligible", *WEATHER],
        )
        require(len(table) == len(ids) and set(table.grid_id) == ids, "Weather grid coverage")
        require(table.grid_id.is_unique, "Weather duplicate grid")
        require(table.prediction_timestamp_utc.eq(day + "T00:00:00Z").all(), "Weather time")
        require(table.weather_primary_eligible.isin([True, False]).all(), "Weather eligibility")
        values = table.loc[table.weather_primary_eligible, WEATHER]
        require(len(values) == expected[day]["weather_primary_eligible"], "Weather eligible count")
        require(len(values) > 0 and np.isfinite(values.to_numpy()).all(), "Missing weather")
        return {
            "date": day,
            "weather_primary_rows": len(values),
            **{name: float(values[name].mean()) for name in WEATHER},
        }

    rows = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for count, row in enumerate(pool.map(read, calendar()), 1):
            rows.append(row)
            if count % 250 == 0:
                print(f"Weather source SHA and summary: {count}/2191 days", flush=True)
    return pd.DataFrame(rows)


def weighted_ecdf_distance(full, selected, weights):
    full, selected, weights = np.asarray(full), np.asarray(selected), np.asarray(weights)
    require(len(selected) > 0 and len(selected) == len(weights), "ECDF shape")
    require(np.isfinite(weights).all() and (weights > 0).all(), "ECDF weight")
    order = np.argsort(selected)
    sample, w = selected[order], weights[order]
    cumulative = np.r_[0, np.cumsum(w) / w.sum()]
    points = np.unique(np.r_[full, sample])
    base = np.searchsorted(np.sort(full), points, side="right") / len(full)
    estimate = cumulative[np.searchsorted(sample, points, side="right")]
    return float(np.max(np.abs(base - estimate)))


def weather_compare(weather, dates, probability):
    sample = weather.loc[weather.date.isin(dates)]
    weights = np.array([1 / probability[day] for day in sample.date])
    output = {}
    for name in WEATHER:
        full, values = weather[name].to_numpy(), sample[name].to_numpy()
        std = float(np.std(full))
        q10, q90 = np.quantile(full, [0.1, 0.9])
        output[name] = {
            "daily_AOI_mean_population_mean": float(full.mean()),
            "weighted_sample_mean": float(np.average(values, weights=weights)),
            "absolute_standardized_mean_shift": float(
                abs(np.average(values, weights=weights) - full.mean()) / std if std else 0
            ),
            "weighted_ECDF_distance_descriptive": weighted_ecdf_distance(full, values, weights),
            "days_at_or_below_population_q10": int((values <= q10).sum()),
            "days_at_or_above_population_q90": int((values >= q90).sum()),
        }
    return output


def july_summary(path, ids):
    rows = []
    with zipfile.ZipFile(path) as archive:
        require(archive.testzip() is None, "July archive CRC")
        for day in pd.date_range("2023-07-01", "2023-07-31").strftime("%Y-%m-%d"):
            center = pd.read_csv(io.BytesIO(archive.read(day + "/centers.csv")))
            area = pd.read_csv(io.BytesIO(archive.read(day + "/area.csv")))
            report = json.loads(archive.read(day + "/report.json"))
            require(
                report["day"] == day and report["negative_label_permitted"] is False, "July policy"
            )
            for name, table in (("centers.csv", center), ("area.csv", area)):
                require(set(table.grid_id) == ids and table.grid_id.is_unique, "July grids")
                require(table.daily_observation_status.eq("unknown").all(), "July observation")
                require(table.negative_label_permitted.eq(False).all(), "July negative labels")
                require(
                    hashlib.sha256(archive.read(day + "/" + name)).hexdigest()
                    == report["outputs_sha256"][name],
                    "July table SHA",
                )
            rows.append(
                {
                    "date": day,
                    "cloud_estimated_AOI_area_share": float(
                        area.cloud_area_estimate_m2.sum() / area.aoi_area_m2.sum()
                    ),
                    "grid_share_without_nominal_land_center": float(
                        center.land_nominal_input_no_residual.eq(0).mean()
                    ),
                    "median_longest_nominal_center_envelope_gap_hours": float(
                        center.nominal_land_center_longest_envelope_gap_seconds.median() / 3600
                    ),
                }
            )
    return pd.DataFrame(rows)


def outcome_metrics(firms, events, dates):
    picked = firms.loc[firms.target_day.isin(dates)]
    event_counts = {name: int(days.isin(dates).sum()) for name, days in events.items()}
    return {
        "candidate_detections_retained": len(picked),
        "candidate_grid_target_days_retained": len(
            picked.drop_duplicates(["grid_id", "target_day"])
        ),
        "candidate_grids_retained": int(picked.grid_id.nunique()),
        "exploratory_first_detection_counts": event_counts,
        "exploratory_event_counts_are_not_final_fire_counts": True,
    }


def spatial_cover_summary(firms, ids):
    """Descriptive spatial/2017-cover checks; no new land eligibility threshold."""
    path = ROOT / "data/interim/grid_landcover_2017.csv"
    cover = pd.read_csv(path, usecols=["grid_id", "reference_year", "natural_vegetation_fraction"])
    require(cover.grid_id.is_unique and set(cover.grid_id) == ids, "Landcover grid")
    require(cover.reference_year.eq(2017).all(), "Landcover must precede training")
    # Match the existing landcover audit's 1e-6 numeric tolerance. Source is unchanged.
    require(
        cover.natural_vegetation_fraction.between(-1e-6, 1 + 1e-6).all(),
        "Landcover fraction",
    )
    cover["cover_bin_descriptive_only"] = pd.cut(
        cover.natural_vegetation_fraction.clip(0, 1),
        [-0.001, 0.1, 0.5, 0.9, 1.0],
        labels=["0_to_10_percent", "10_to_50_percent", "50_to_90_percent", "90_to_100_percent"],
    ).astype(str)
    indexes = cover.grid_id.str.extract(r"^E6933_5K_V1_C(-?\d+)_R(-?\d+)$").astype(int)
    cover["spatial_block_50km"] = (
        (indexes[0] // 10).astype(str) + ":" + (indexes[1] // 10).astype(str)
    )
    joined = firms.merge(cover, validate="many_to_one")
    require(len(joined) == len(firms), "Landcover join lost FIRMS")
    rows = []
    for count in (7, 14, 21):
        dates, _ = sample_dates(count)
        retained = joined.target_day.isin(dates)
        for dimension in ("cover_bin_descriptive_only", "spatial_block_50km"):
            for name, group in joined.groupby(dimension, observed=True):
                picked = group.loc[retained.loc[group.index]]
                rows.append(
                    {
                        "days_per_month": count,
                        "dimension": dimension,
                        "group": name,
                        "population_candidate_detections": len(group),
                        "retained_candidate_detections": len(picked),
                        "population_candidate_grids": int(group.grid_id.nunique()),
                        "retained_candidate_grids": int(picked.grid_id.nunique()),
                        "retained_candidate_grid_target_days": len(
                            picked.drop_duplicates(["grid_id", "target_day"])
                        ),
                    }
                )
    return pd.DataFrame(rows), path


def assess():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = {
        "firms": ROOT / "data/interim/firms_combined_candidates_2018_2024.csv",
        "grid": ROOT / "data/aoi/grid_5km.geojson",
        "pairs": REPORTS / "l2_training_catalogue_pairs.csv",
        "sources": REPORTS / "l2_training_catalogue_granules.csv",
        "benchmark": REPORTS / "gcp_benchmark_received_verification.json",
        "weather_preparation": ROOT
        / "outputs/reports/meteorology/model_weather_2018-01-01_2025-01-01.json",
        "july_proof": REPORTS / "colab_month_received_verification.json",
        "july_archive": ROOT / "outputs/cloud_month/received/l2_month_2023_07_results.zip",
    }
    fingerprints = {name: sha(path) for name, path in paths.items()}
    ids = {f["properties"]["grid_id"] for f in json.loads(paths["grid"].read_text())["features"]}
    require(len(ids) == 2899, "Expected frozen grid")
    firms = pd.read_csv(
        paths["firms"],
        usecols=["detection_id", "detection_timestamp_utc", "grid_id", "source_sensor"],
    )
    timestamps = pd.to_datetime(firms.detection_timestamp_utc, utc=True)
    firms = firms.loc[timestamps.dt.year.between(2018, 2023)].copy()
    require(len(firms) == 30295 and firms.detection_id.is_unique, "Training FIRMS identity")
    require(set(firms.grid_id) <= ids, "FIRMS grid membership")
    firms["target_day"] = target_day(firms.detection_timestamp_utc)
    require(firms.target_day.between(START, END).all(), "Boundary FIRMS requires explicit handling")
    pairs, nominal = read_catalogue(paths["pairs"], paths["sources"])
    benchmark = json.loads(paths["benchmark"].read_text())
    require(
        benchmark["status"] == "independent_gcp_two_arm_readback_passed", "Benchmark not verified"
    )
    arm = next(arm for arm in benchmark["summary"]["arms"] if arm["workers"] == 2)
    require(arm["completed_pairs"] == 6, "Benchmark scope")
    seconds_per_pair = arm["cold_pair_wall_seconds"] / 6
    events, event_paths = load_events(firms)
    fingerprints.update({p.name: sha(p) for p in event_paths})
    spatial, cover_path = spatial_cover_summary(firms, ids)
    fingerprints["landcover_2017"] = sha(cover_path)
    spatial.to_csv(OUT / "spatial_landcover_retention.csv", index=False)
    preparation = json.loads(paths["weather_preparation"].read_text())
    require(preparation["labels_created"] is False, "Weather report contains labels")
    weather = weather_summary(preparation, ids)
    weather.to_csv(OUT / "training_daily_weather_summary.csv", index=False)
    july_proof = json.loads(paths["july_proof"].read_text())
    require(july_proof["complete_month"] is True, "July incomplete")
    require(july_proof["received_sha256"] == fingerprints["july_archive"], "July archive SHA")
    july = july_summary(paths["july_archive"], ids)
    july.to_csv(OUT / "july_observation_proxy_summary.csv", index=False)

    all_days = set(calendar())
    baseline = cost(all_days, pairs, nominal, seconds_per_pair)
    fire_days = set(firms.target_day)
    all_first_days = {day for dates in events.values() for day in dates}
    contrasts = {
        "all_candidate_detection_dates": {
            "target_days": len(fire_days),
            "cost_without_guards_or_extra_control_dates": cost(
                fire_days, pairs, nominal, seconds_per_pair
            ),
        },
        "union_first_dates_across_nine_exploratory_rules": {
            "target_days": len(all_first_days),
            "cost_without_guards_or_extra_control_dates": cost(
                all_first_days, pairs, nominal, seconds_per_pair
            ),
        },
    }
    scenarios, strata_rows, seed_rows = {}, [], []
    population = firms.groupby(firms.target_day.str[:7]).size()
    for count in (7, 14, 21):
        dates, probability = sample_dates(count)
        source_days, external = guards(dates)
        metrics = outcome_metrics(firms, events, dates)
        scenario_cost = cost(source_days, pairs, nominal, seconds_per_pair)
        metrics.update(
            target_days=len(dates),
            possible_grid_target_rows_before_eligibility=len(dates) * len(ids),
            weather_primary_rows_before_labels=int(
                weather.loc[weather.date.isin(dates)].weather_primary_rows.sum()
            ),
            source_days_including_provisional_adjacent_day_guards=len(source_days),
            guard_dates_outside_training_not_read=external,
            cost_with_provisional_guards=scenario_cost,
            reduction_pending_pairs_vs_full=1
            - scenario_cost["pending_nominal_pairs"] / baseline["pending_nominal_pairs"],
            weather_daily_AOI_means=weather_compare(weather, dates, probability),
        )
        selected_july = july.loc[july.date.isin(dates)]
        metrics["July_only_observation_proxies_not_labels"] = {
            name: {
                "full_month_mean": float(july[name].mean()),
                "sample_mean": float(selected_july[name].mean()),
            }
            for name in july.columns
            if name != "date"
        }
        sample = firms.loc[firms.target_day.isin(dates)]
        metrics["retained_candidates_by_year"] = (
            sample.groupby(sample.target_day.str[:4]).size().to_dict()
        )
        metrics["retained_candidates_by_sensor"] = sample.groupby("source_sensor").size().to_dict()
        metrics["candidate_grids_lost_from_training_sample"] = int(
            firms.grid_id.nunique() - sample.grid_id.nunique()
        )
        block_rows = spatial.loc[
            spatial.days_per_month.eq(count) & spatial.dimension.eq("spatial_block_50km")
        ]
        metrics["50km_blocks_with_population_candidates"] = len(block_rows)
        metrics["50km_blocks_with_zero_retained_candidates"] = int(
            block_rows.retained_candidate_detections.eq(0).sum()
        )
        metrics["zero_retained_candidate_year_month_strata"] = []
        for month in sorted({day[:7] for day in all_days}):
            chosen = sample.loc[sample.target_day.str.startswith(month)]
            if population.get(month, 0) > 0 and len(chosen) == 0:
                metrics["zero_retained_candidate_year_month_strata"].append(month)
            strata_rows.append(
                {
                    "days_per_month": count,
                    "year_month": month,
                    "calendar_days": sum(day.startswith(month) for day in all_days),
                    "selected_days": sum(day.startswith(month) for day in dates),
                    "population_candidate_detections": int(population.get(month, 0)),
                    "retained_candidate_detections": len(chosen),
                    "retained_candidate_grids": int(chosen.grid_id.nunique()),
                }
            )
        schedule = pd.DataFrame(
            {
                "target_day": sorted(dates),
                "day_inclusion_probability": [probability[day] for day in sorted(dates)],
                "design_inverse_probability_weight": [
                    1 / probability[day] for day in sorted(dates)
                ],
                "negative_label_permitted": False,
                "daily_observation_status": "unknown",
            }
        )
        schedule.to_csv(OUT / f"proposed_dates_{count}_days_per_month.csv", index=False)
        pd.DataFrame({"source_day": sorted(source_days)}).to_csv(
            OUT / f"provisional_source_days_{count}_days_per_month.csv", index=False
        )
        # Other seeds measure design sensitivity only. They never replace the fixed proposal.
        for seed in range(100):
            trial, _ = sample_dates(count, seed)
            outcomes = outcome_metrics(firms, events, trial)
            seed_rows.append(
                {
                    "days_per_month": count,
                    "seed": seed,
                    **{
                        key: outcomes[key]
                        for key in (
                            "candidate_detections_retained",
                            "candidate_grid_target_days_retained",
                            "candidate_grids_retained",
                        )
                    },
                    **outcomes["exploratory_first_detection_counts"],
                }
            )
        scenarios[str(count)] = metrics
    strata = pd.DataFrame(strata_rows)
    strata.to_csv(OUT / "monthly_retention.csv", index=False)
    seeds = pd.DataFrame(seed_rows)
    seeds.to_csv(OUT / "design_seed_sensitivity.csv", index=False)
    variability = {}
    for count in (7, 14, 21):
        group = seeds.loc[seeds.days_per_month.eq(count)]
        variability[str(count)] = {
            name: {str(q): float(group[name].quantile(q)) for q in (0.05, 0.5, 0.95)}
            for name in group.columns
            if name not in ("days_per_month", "seed")
        }
    report = {
        "status": "offline_feasibility_measured_model_sufficiency_unproven",
        "method": "nested_uniform_random_cyclic_month_blocks_v1",
        "fixed_seed": SEED,
        "seed_selected_before_outcome_metrics": True,
        "training_period": [START, END],
        "full_training_calendar_days": len(all_days),
        "full_training_candidate_detections": len(firms),
        "full_training_candidate_grids": int(firms.grid_id.nunique()),
        "exploratory_first_detection_population": {
            name: len(days) for name, days in events.items()
        },
        "full_remaining_training_cost": baseline,
        "outcome_dependent_contrasts_not_recommended_training_design": contrasts,
        "scenarios": scenarios,
        "100_seed_design_sensitivity_quantiles_not_statistical_confidence_intervals": variability,
        "inputs_sha256": fingerprints,
        "analysis_code_sha256": sha(Path(__file__)),
        "outputs_sha256": {p.name: sha(p) for p in sorted(OUT.glob("*.csv"))},
        "limitations": [
            "No new native products processed; model quality is unmeasured.",
            "Cyclic blocks may split at month boundaries; guards are source-only.",
            "Provisional +/-1 source-day buffer is not a verified scan-boundary or label policy.",
            "All FIRMS/grouping records remain intact; only proposed training dates differ.",
            "Exploratory grouping can merge fires; no scenario is a final event rule.",
            "Nominal-pair costs exclude selected unpaired records requiring investigation.",
            "Six-pair speed excludes daily union, Drive, retries and implementation.",
            "Weather uses eligible daily AOI means, not full cell-level distributions.",
            "2017 cover bins/50km blocks are diagnostics, not province IDs or eligibility rules.",
            "Dissolved AOI has no individual province IDs; province boundary audit remains open.",
            "Design weights do not correct cloud/missingness or event linkage bias.",
            "Unsampled 2024 validation and sealed 2025 evaluation costs require separate planning.",
        ],
        "next_gate": (
            "native coverage, spatial/landcover retention, nested learning curves on holdout; "
            "then choose or expand scope"
        ),
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_sufficient": None,
        "production_scope_approved": False,
        "cloud_resources_changed": False,
        "new_raw_downloads": 0,
        "final_test_data_read": False,
        "validation_data_used_for_sampling": False,
    }
    require(all(sha(path) == fingerprints[name] for name, path in paths.items()), "Input mutated")
    require(sha(cover_path) == fingerprints["landcover_2017"], "Landcover mutated")
    (OUT / "assessment.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps({"status": report["status"], "report": str(OUT / "assessment.json")}, indent=2)
    )


if __name__ == "__main__":
    assess()
