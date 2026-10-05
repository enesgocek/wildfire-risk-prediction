"""Offline training-only summer control inventory and cost options; no downloads.

Control sampling emphasizes many thermal detections, not representative fire
incidence. Archive Type is recorded, never trusted as confirmed ignition cause.
"""

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

SPEC = importlib.util.spec_from_file_location(
    "summer_inventory", Path(__file__).with_name("inventory_l2_catalogue.py")
)
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)
audit, ROOT, OUTPUT = inventory.audit, inventory.ROOT, inventory.OUTPUT
START, END = pd.Timestamp("2018-01-01T00:00Z"), pd.Timestamp("2024-01-01T00:00Z")


def nominal_groups(fires, detections):
    """Nominal [start,end) minute matching only, with missing/overlap accounting."""
    times = pd.to_datetime(detections.detection_timestamp_utc, utc=True)
    audit.require(times.notna().all() and times.is_monotonic_increasing, "Bad detection times")
    audit.require(((times >= START) & (times < END)).all(), "Non-training detections")
    observed = times.array.asi8
    used = np.zeros(len(observed), dtype="int64")
    rows = []
    for row in fires.itertuples():
        start, end = pd.Timestamp(row.start_utc), pd.Timestamp(row.end_utc)
        audit.require(
            start.tzinfo is not None and end.tzinfo is not None and start < end, "Bad interval"
        )
        audit.require(START <= start < END and end <= END, "Non-training granule interval")
        lo, hi = np.searchsorted(observed, [start.value, end.value], side="left")
        subset = detections.iloc[lo:hi]
        used[lo:hi] += 1
        nominal_high = subset.loc[subset.confidence.isin(["n", "h"])]
        rows.append(
            {
                "sensor": row.sensor,
                "pair_key": row.pair_key,
                "pilot_detection_count": len(subset),
                "pilot_nominal_high_all_types": len(nominal_high),
                "pilot_grid_count": subset.grid_id.nunique(),
                "nominal_high_grid_count": nominal_high.grid_id.nunique(),
                **{
                    f"archive_type{t}_nominal_high": int(nominal_high.type.eq(str(t)).sum())
                    for t in range(4)
                },
            }
        )
    return pd.DataFrame(rows), {
        "training_detection_count": len(observed),
        "uniquely_matched_to_nominal_fire_interval": int((used == 1).sum()),
        "unmatched_to_nominal_fire_interval": int((used == 0).sum()),
        "ambiguous_nominal_interval_match": int((used > 1).sum()),
        "unmatched_by_utc_day": {
            str(day): int(count)
            for day, count in times.loc[used == 0]
            .dt.strftime("%Y-%m-%d")
            .value_counts()
            .sort_index()
            .items()
        },
        "unmatched_interpretation": (
            "Catalogue/time reconciliation unresolved; not absence and not a reason to delete fires"
        ),
        "match_definition": (
            "Archive acquisition minute in nominal [start,end); native check pending"
        ),
    }


def shortlist_pairs(pairs):
    eligible = pairs.loc[
        pairs.pair_status.eq("nominal_unique_pair")
        & pairs.month.isin([6, 7, 8])
        & pairs.pilot_nominal_high_all_types.gt(0)
        & pairs.day_night.isin(["DAY", "NIGHT"])
    ].copy()
    # Explicit stress-sample ranking; NOT an observation or vegetation threshold.
    ordered = eligible.sort_values(
        ["pilot_nominal_high_all_types", "nominal_high_grid_count", "day", "pair_key"],
        ascending=[False, False, True, True],
        kind="stable",
    )
    result = ordered.drop_duplicates(["year", "sensor", "day_night"])
    audit.require(len(result) > 0, "No summer controls")
    return result.sort_values(["year", "sensor", "day_night"]).reset_index(drop=True)


def day_plan(pairs, day):
    selected = pairs.loc[pairs.day.eq(day)].sort_values(["start_utc", "sensor"])
    audit.require(
        len(selected) > 0 and selected.pair_status.eq("nominal_unique_pair").all(),
        "Day has unresolved catalogue pairs",
    )
    audit.require(set(selected.sensor) == {"SNPP", "N20"}, "Day needs both sensors")
    for sensor in ("SNPP", "N20"):
        sample = selected.loc[selected.sensor.eq(sensor)]
        audit.require(set(sample.day_night) >= {"DAY", "NIGHT"}, "Need day/night per sensor")
        audit.require(
            sample.pilot_nominal_high_all_types.sum() > 0, "Need thermal control per sensor"
        )
    return selected


def describe_option(selected, purpose):
    audit.require(not selected.duplicated(["sensor", "pair_key"]).any(), "Duplicate planned pairs")
    return {
        "purpose": purpose,
        "days": sorted(selected.day.unique().tolist()),
        "pair_ids": [f"{r.sensor}:{r.pair_key}" for r in selected.itertuples()],
        "granule_pairs": len(selected),
        "source_files": len(selected) * 2,
        "catalogue_bytes_estimate": float(selected.pair_bytes_estimate.sum()),
        "largest_temporary_pair_bytes_estimate": float(selected.pair_bytes_estimate.max()),
        "pilot_nominal_high_records_all_types": int(selected.pilot_nominal_high_all_types.sum()),
        "raw_download_started": False,
        "negative_label_permitted": False,
        "cloud_condition": "not_assessed",
        "actual_input_identity_verified": False,
    }


def main():
    catalog_path = OUTPUT / "l2_training_catalogue_inventory.json"
    catalog_report = json.loads(catalog_path.read_text(encoding="utf-8"))
    review_path = OUTPUT / "training_review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    audit.require(
        catalog_report["script_sha256"] == audit.digest(Path(inventory.__file__)), "Stale inventory"
    )
    sources = {
        str(catalog_path.relative_to(ROOT)): audit.digest(catalog_path),
        str(review_path.relative_to(ROOT)): audit.digest(review_path),
    }
    for record in catalog_report["outputs"].values():
        path = ROOT / record["path"]
        audit.require(audit.digest(path) == record["sha256"], "Catalogue CSV changed")
        sources[str(path.relative_to(ROOT))] = record["sha256"]
    for collection in catalog_report["catalogue"].values():
        for page in collection["pages"]:
            audit.require(
                audit.digest(ROOT / page["path"]) == page["sha256"], "Catalogue page changed"
            )
    granules = pd.read_csv(
        ROOT / catalog_report["outputs"]["granules"]["path"], dtype={"pair_key": str}
    )
    pairs = pd.read_csv(ROOT / catalog_report["outputs"]["pairs"]["path"], dtype={"pair_key": str})
    for name in ("fire_concepts", "geolocation_concepts"):
        pairs[name] = pairs[name].fillna("")
    pd.testing.assert_frame_equal(
        inventory.pair_catalogue(granules)
        .sort_values(["sensor", "pair_key"])
        .reset_index(drop=True),
        pairs.sort_values(["sensor", "pair_key"]).reset_index(drop=True),
        check_exact=True,
    )
    for row in granules.itertuples():
        audit.require(
            audit.product_identity(row.filename)[:3] == (row.sensor, row.role, row.pair_key),
            "Wrong granule key",
        )
        start, end = pd.Timestamp(row.start_utc), pd.Timestamp(row.end_utc)
        audit.require(START <= start < end <= END, "Non-training granule")
        audit.require(
            not row.actual_input_identity_verified and not row.negative_label_permitted,
            "Premature catalogue validation",
        )
    pair_details = granules.loc[
        granules.role.eq("fire"), ["sensor", "pair_key", "start_utc", "day_night"]
    ]
    pair_sizes = (
        granules.groupby(["sensor", "pair_key"])
        .catalogue_size_bytes_estimate.sum()
        .rename("pair_bytes_estimate")
    )
    pairs = pairs.merge(pair_details, on=["sensor", "pair_key"], how="left", validate="one_to_one")
    pairs = pairs.merge(pair_sizes, on=["sensor", "pair_key"], validate="one_to_one")
    stats, matching = [], {}
    for sensor, filename in (
        ("SNPP", "firms_pilot_2018_2024.csv"),
        ("N20", "firms_noaa20_pilot_2018_2024.csv"),
    ):
        path = ROOT / "data/interim" / filename
        provenance = next(
            p["input_sha256"] for p in review["input_provenance"] if p["sensor"] == sensor
        )
        expected = provenance[str(path.relative_to(ROOT))]
        audit.require(audit.digest(path) == expected, "Pilot source changed")
        sources[str(path.relative_to(ROOT))] = expected
        pilot = pd.read_csv(path, dtype="string")
        times = pd.to_datetime(pilot.detection_timestamp_utc, utc=True)
        # Validation records are neither ranked nor used to compute sample statistics.
        pilot = pilot.loc[(times >= START) & (times < END)].copy()
        audit.require(pilot.source_record_number.is_unique, "Duplicate source record")
        audit.require(
            pilot.type.isin(["0", "1", "2", "3"]).all()
            and pilot.confidence.isin(["l", "n", "h"]).all(),
            "Unknown archive codes",
        )
        pilot = pilot.sort_values("detection_timestamp_utc", kind="stable").reset_index(drop=True)
        counts, reconciliation = nominal_groups(
            granules.loc[granules.sensor.eq(sensor) & granules.role.eq("fire")], pilot
        )
        matching[sensor] = reconciliation
        stats.append(counts)
    pairs = pairs.merge(
        pd.concat(stats), on=["sensor", "pair_key"], how="left", validate="one_to_one"
    )
    count_columns = [n for n in stats[0].columns if n not in {"sensor", "pair_key"}]
    pairs[count_columns] = pairs[count_columns].fillna(0).astype("int64")
    pairs["year"], pairs["month"] = pairs.day.str[:4].astype(int), pairs.day.str[5:7].astype(int)
    shortlist = shortlist_pairs(pairs)
    candidate_days, excluded_days = {}, []
    for day in sorted(shortlist.day.unique()):
        try:
            candidate_days[day] = day_plan(pairs, day)
        except ValueError as error:
            excluded_days.append({"day": day, "reason": str(error)})
    audit.require(
        len({d[:4] for d in candidate_days}) >= 3, "Need three training years for cost options"
    )
    cheapest = min(candidate_days, key=lambda d: (candidate_days[d].pair_bytes_estimate.sum(), d))
    one_day = candidate_days[cheapest]
    small = one_day.sort_values(
        ["pilot_nominal_high_all_types", "pair_bytes_estimate", "pair_key"],
        ascending=[False, True, True],
    ).drop_duplicates("sensor")
    years = sorted({d[:4] for d in candidate_days})
    selected_years = [years[0], years[len(years) // 2], years[-1]]
    three_days = [
        min(
            (d for d in candidate_days if d.startswith(year)),
            key=lambda d: (candidate_days[d].pair_bytes_estimate.sum(), d),
        )
        for year in selected_years
    ]
    options = {
        "A_two_pairs": describe_option(
            small, "Lowest traffic: two sensor granules, no daily comparison"
        ),
        "B_one_day": describe_option(
            one_day, "One complete nominal catalogue day, both sensors/day/night"
        ),
        "C_three_days": describe_option(
            pd.concat([candidate_days[d] for d in three_days]),
            "Three training years, both sensors/day/night per day",
        ),
    }
    output_hashes = {}
    for name, table in (("pairs", pairs), ("shortlist", shortlist)):
        path = OUTPUT / f"summer_control_{name}.csv"
        table.to_csv(path, index=False)
        reread = pd.read_csv(path, dtype={"pair_key": str})
        for column in ("fire_concepts", "geolocation_concepts"):
            reread[column] = reread[column].fillna("")
        pd.testing.assert_frame_equal(
            table.reset_index(drop=True),
            reread,
            check_dtype=False,
            check_exact=False,
            rtol=1e-12,
            atol=1e-6,
        )
        output_hashes[str(path.relative_to(ROOT))] = audit.digest(path)
    for name, option in options.items():
        table = pairs.loc[(pairs.sensor + ":" + pairs.pair_key).isin(option["pair_ids"])]
        selected_granules = granules.merge(
            table[["sensor", "pair_key"]], on=["sensor", "pair_key"], validate="many_to_one"
        )
        path = OUTPUT / f"summer_control_{name}_granules.csv"
        selected_granules.to_csv(path, index=False)
        audit.require(len(selected_granules) == option["source_files"], "File count differs")
        output_hashes[str(path.relative_to(ROOT))] = audit.digest(path)
    for path, digest in sources.items():
        audit.require(audit.digest(ROOT / path) == digest, "Source changed during selection")
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "offline_cost_options_prepared_no_download",
        "script_sha256": audit.digest(Path(__file__)),
        "sources_sha256": sources,
        "outputs_sha256": output_hashes,
        "training_nominal_matching": matching,
        "shortlist_pair_count": len(shortlist),
        "shortlist_years": sorted(shortlist.year.unique().tolist()),
        "excluded_shortlist_days": excluded_days,
        "options": options,
        "option_selected": None,
        "raw_granules_downloaded": 0,
        "negative_label_permitted": False,
        "selection_definition": (
            "JJA, nominal unique pair, positive n/h thermal count of any archive Type; "
            "largest count per year/sensor/day-night, ties by distinct grids/day/key"
        ),
        "limitations": [
            "High-detection controls; not representative incidence or threshold calibration",
            "Archive Type 0 and 2 both retained; NASA correction confirmation pending",
            "A nominal catalogue match is not actual InputPointer or native pixel verification",
            "No cloud, vegetation fire, ignition cause or independent orbit confirmation",
            "Complete nominal catalogue day is not physical full-day coverage or absence",
            "2024/2025 not used for selection; existing pilot CSV includes unused 2024 records",
            "Sizes are frozen catalogue estimates; scratch also needs environment and output space",
            "Options are alternatives, not cumulative; no notebook or cloud job started",
        ],
    }
    path = OUTPUT / "summer_control_inventory.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Report: {path}")
    print(json.dumps(options, indent=2))


if __name__ == "__main__":
    main()
