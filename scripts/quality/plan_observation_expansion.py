"""Offline calendar-cluster pilot, provincial coverage and accepted native-source workload."""

import hashlib
import io
import json
import socket
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import require, training_day
from wildfire_risk_prediction.observation_expansion import (
    calendar_dates,
    province_support,
    raw_references,
    select_core,
    unique_sources,
)
from wildfire_risk_prediction.observation_window import source_schedule

ROOT = Path(__file__).resolve().parents[2]
OBS = Path("outputs/reports/dataset/observation_materialization_v1/20261014T145638Z_c0881064")
PILOT = Path("outputs/reports/dataset/label_protocol_v1/20261014T193224Z_54fdbb95")
WATER = Path("outputs/reports/dataset/water_scope_v1/20261014T185242Z_f2e469bd")
DELIVERY = "outputs/gcp_delivery/2026-10-14/compact/products"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline expansion planning")


def run():
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(
            path.resolve().is_relative_to(ROOT) and path.is_file() and not path.is_symlink(),
            "Project-local regular planning input",
        )
        digest = sha(path)
        require(expected is None or digest == expected, "Planning input hash changed")
        pins[path.relative_to(ROOT).as_posix()] = digest
        return path

    def report(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    config = report("configs/observation_expansion_v1.json")
    require(
        config["status"] == "method_pilot_plan_not_label_policy"
        and config["negative_label_permitted"] is False
        and config["population_error_estimation_permitted"] is False
        and config["cloud_execution_authorized_by_this_config"] is False,
        "Planning-only configuration",
    )
    require(
        config["maximum_units_per_day_province_signal"] == 2
        and config["prefer_different_cover_group_for_second_unit"] is True,
        "Fixed within-cell selection design",
    )
    dates = calendar_dates(config["training_years"], config["season_dates"])
    require(len(dates) == 12, "Twelve prespecified training days")
    master = report(
        OBS / "accepted_readback.json",
        "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14",
    )
    require(
        master["daily_observation_status"] == "unknown" and not master["negative_label_permitted"],
        "Accepted closed observation inventory",
    )
    months = {r["month"]: r for r in master["reports"]}
    pilot_report = report(
        PILOT / "readback.json", "534d67c44cad55a267aaf57330b4396a9cbb6aa65baa8bfdd71b9037b7bb0cab"
    )
    pilot = pd.read_csv(
        retained(
            PILOT / "pilot_protocol_review.csv",
            pilot_report["artifact_sha256"]["pilot_protocol_review.csv"],
        ),
        float_precision="round_trip",
    )
    require(
        len(pilot) == 400
        and pilot.review_unit_id.is_unique
        and pilot.target.isna().all()
        and pilot.route_is_label_admission.eq(False).all(),
        "Unchanged unlabelled 400-unit pilot",
    )
    boundary_folder = Path(config["boundary_folder"])
    boundary = report(boundary_folder / "readback.json", config["boundary_readback_sha256"])
    retained("scripts/earth_engine/prepare_province_boundaries.py", boundary["script_sha256"])
    provinces = gpd.read_file(
        retained(boundary_folder / "provinces.geojson", boundary["boundary_sha256"])
    )
    require(set(provinces.province) == set(config["provinces"]), "Same four source provinces")
    retained("data/aoi/aoi.geojson", boundary["original_aoi_sha256"])
    parts = gpd.read_file(
        retained(
            "data/interim/grid_aoi_parts.geojson",
            "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9",
        )
    )
    geographic, intersections = province_support(parts, provinces)
    require(
        len(geographic) == 2899 and geographic.primary_province.notna().all(),
        "Full provincial support",
    )
    print("Province/grid intersection audit passed", flush=True)
    cover = pd.read_csv(
        retained(
            "data/interim/grid_landcover_2017.csv",
            "dae1f0a1fdf07dbfa173814c7ebdc9e3c8df81809b69d6a672857111731e544c",
        )
    )
    require(
        cover.grid_id.is_unique
        and cover.reference_year.eq(2017).all()
        and set(cover.grid_id) == set(geographic.grid_id),
        "Frozen 2017 cover grid",
    )
    for c in ("forest_fraction", "shrub_fraction", "agriculture_fraction", "water_fraction"):
        require(
            np.allclose(
                pilot[c], pilot.grid_id.map(cover.set_index("grid_id")[c]), rtol=1e-10, atol=1e-10
            ),
            "Cover matches accepted pilot provenance",
        )
    fractions = cover[
        ["herbaceous_fraction", "agriculture_fraction", "water_fraction", "urban_fraction"]
    ].copy()
    fractions["forest_shrub"] = cover.forest_fraction + cover.shrub_fraction
    require(
        np.isfinite(fractions.to_numpy()).all()
        and fractions.ge(0).all().all()
        and fractions.sum(axis=1).le(1 + 1e-6).all(),
        "Disjoint cover diagnostics",
    )
    fractions["other"] = (1 - fractions.sum(axis=1)).clip(lower=0)
    cover["cover_group"] = fractions.idxmax(axis=1).str.replace("_fraction", "", regex=False)
    water_report = report(
        WATER / "readback.json", "7b5d296bae6c3744790817409db4bce3a947e92919a06abde9271eac07814cae"
    )
    water = pd.read_csv(
        retained(
            WATER / "grid_water_scope.csv", water_report["artifact_sha256"]["grid_water_scope.csv"]
        )
    )
    require(water.grid_id.is_unique and set(water.grid_id) == set(geographic.grid_id), "Water keys")
    selected_days = []
    needed_months = sorted(set(dates.target_day.str[:7]))
    for month in needed_months:
        meta = report(OBS / month / "readback.json")
        require(meta == months[month], "Monthly observation inventory agreement")
        frame = pd.read_csv(
            retained(OBS / month / "observations.csv.gz", meta["table_sha256"]),
            float_precision="round_trip",
        )
        frame = frame.loc[frame.obs_nominal_granule_day.isin(dates.target_day)].copy()
        require(len(frame) == 2899, "Prespecified day has the full grid")
        selected_days.append(frame)
    candidates = pd.concat(selected_days, ignore_index=True)
    candidates = candidates.merge(geographic, on="grid_id", how="left", validate="many_to_one")
    candidates = candidates.merge(
        cover[
            [
                "grid_id",
                "cover_group",
                "forest_fraction",
                "shrub_fraction",
                "agriculture_fraction",
                "water_fraction",
            ]
        ],
        on="grid_id",
        how="left",
        validate="many_to_one",
    )
    candidates = candidates.merge(
        water[["grid_id", "water_scope_included"]], on="grid_id", how="left", validate="many_to_one"
    )
    candidates["signal_group"] = np.where(
        ~candidates.obs_product_present,
        "source_product_absent",
        np.where(
            candidates.obs_nominal_confidence_fire.add(candidates.obs_high_confidence_fire).gt(0),
            "thermal_center_present",
            "no_selected_thermal_center",
        ),
    )
    core, quotas = select_core(candidates, dates, config["provinces"], config["selection_seed"])
    existing = pilot.merge(geographic, on="grid_id", how="left", validate="many_to_one")
    existing["population_error_estimation_permitted"] = False
    stress = existing.loc[existing.proposed_review_route.isin(config["priority_routes"])].copy()
    stress["selection_plan"] = "existing_priority"
    plans = {"calendar_core": core, "existing_priority": stress, "existing_400_reference": existing}
    registry = report(
        "configs/gcp_source_blocks_2026-10-13.json",
        "c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95",
    )
    # Only the two registered day identities are used; no source resolution is inferred here.
    deferred = {"2018-06-13", "2023-12-31"}
    require(set(registry["deferred_days"]) == deferred, "Retained deferred-day registry")
    requests = []
    for name, units in plans.items():
        for row in units.itertuples(index=False):
            day = str(row.prediction_timestamp_utc)[:10]
            for request in source_schedule(day, deferred).to_dict("records"):
                requests.append(
                    {"selection_plan": name, "review_unit_id": row.review_unit_id, **request}
                )
    requests = pd.DataFrame(requests)
    source_days = sorted(
        requests.loc[
            requests.source_status.eq("available_training_packet"), "source_nominal_day"
        ].unique()
    )
    references, day_inventory = [], []
    for month in sorted({d[:7] for d in source_days}):
        meta = months[month]
        days = [d for d in source_days if d[:7] == month]
        names = meta["input_payload_sha256"]
        archive = None
        name = DELIVERY + "/month/" + month + "/payload.zip"
        if month == "2023-07":
            name = "outputs/cloud_month/received/l2_month_2023_07_results.zip"
            archive = zipfile.ZipFile(retained(name, names[name]))
        elif name in names:
            archive = zipfile.ZipFile(retained(name, names[name]))
        try:
            for day in days:
                training_day(day)
                require(
                    day in meta["days"] and day not in meta["missing_source_days"],
                    "Accepted source day",
                )
                if month == "2023-07":
                    data = archive.read(day + "/report.json")
                else:
                    daily_data = (
                        archive.read(day + ".zip")
                        if archive
                        else retained(
                            DELIVERY + "/day/" + day + "/payload.zip",
                            names[DELIVERY + "/day/" + day + "/payload.zip"],
                        ).read_bytes()
                    )
                    with zipfile.ZipFile(io.BytesIO(daily_data)) as daily:
                        data = daily.read("report.json")
                record = json.loads(data)
                require(
                    record["day"] == day
                    and record["parts_sha256"]
                    == "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9",
                    "Accepted daily source identity",
                )
                refs = raw_references(record)
                references.append(refs)
                day_inventory.append(
                    {
                        "source_nominal_day": day,
                        "pair_count": refs.sample_id.nunique(),
                        "file_count": len(refs),
                        "stored_raw_bytes": int(refs.bytes.sum()),
                        "report_sha256": hashlib.sha256(data).hexdigest(),
                    }
                )
        finally:
            if archive:
                archive.close()
        print("Verified source metadata:", month, len(days), flush=True)
    queue = unique_sources(pd.concat(references, ignore_index=True))
    local = []
    for path in sorted((ROOT / "data/raw/firms_observation").rglob("*.nc")):
        retained(path.relative_to(ROOT))
        local.append(
            {
                "filename": path.name,
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha(path),
            }
        )
    local = pd.DataFrame(local)
    require(not local.duplicated(["filename", "sha256"]).any(), "Unambiguous local file inventory")
    matched = set(zip(local.filename, local.sha256, strict=True))
    queue["local_exact_hash_match"] = [
        (n, h) in matched for n, h in zip(queue.filename, queue.sha256, strict=True)
    ]
    budgets, plan_sources = [], []
    for name, units in plans.items():
        scope = requests.loc[requests.selection_plan.eq(name)]
        wanted = set(
            scope.loc[scope.source_status.eq("available_training_packet"), "source_nominal_day"]
        )
        files = queue.loc[queue.source_day.isin(wanted)]
        plan_sources.extend({"selection_plan": name, "source_id": s} for s in files.source_id)
        budgets.append(
            {
                "selection_plan": name,
                "unit_count": len(units),
                "target_days": units.prediction_timestamp_utc.nunique(),
                "available_source_days": len(wanted),
                "deferred_source_days": scope.loc[
                    scope.source_status.eq("deferred_source_day"), "source_nominal_day"
                ].nunique(),
                "outside_training_days_not_read": scope.loc[
                    scope.source_status.eq("outside_training_not_read"), "source_nominal_day"
                ].nunique(),
                "unique_native_pairs": files.sample_id.nunique(),
                "unique_raw_files": len(files),
                "stored_raw_bytes": int(files.bytes.sum()),
                "local_exact_hash_match_files": int(files.local_exact_hash_match.sum()),
                "raw_bytes_not_locally_verified": int(
                    files.loc[~files.local_exact_hash_match, "bytes"].sum()
                ),
                "current_remote_availability_checked": False,
                "compute_seconds_estimate": None,
                "cloud_cost_try_estimate": None,
            }
        )
    protected = report(PROTECTED)
    for name, digest in protected.items():
        retained(name, digest)
    retained(Path(__file__).relative_to(ROOT))
    for name in ("observation_expansion.py", "observation_window.py", "feature_join.py"):
        retained("src/wildfire_risk_prediction/" + name)
    out = (
        ROOT
        / "outputs/reports/dataset/observation_expansion_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    budget_table = pd.DataFrame(budgets)
    # CSV represents unknown numeric estimates as NaN; the JSON keeps explicit null.
    budget_table[["compute_seconds_estimate", "cloud_cost_try_estimate"]] = np.nan
    tables = {
        "calendar.csv": dates,
        "province_grid.csv": geographic,
        "province_intersections.csv": intersections,
        "calendar_core.csv": core,
        "quota_gaps.csv": quotas,
        "existing_priority.csv": stress,
        "existing_400_geography.csv": existing,
        "source_day_requests.csv": requests,
        "source_day_inventory.csv": pd.DataFrame(day_inventory),
        "native_source_queue.csv": queue,
        "local_native_inventory.csv": local,
        "plan_source_links.csv": pd.DataFrame(plan_sources),
        "workload_comparison.csv": budget_table,
    }
    artifacts = {}
    for name, frame in tables.items():
        path = out / name
        frame.to_csv(path, index=False)
        pd.testing.assert_frame_equal(
            frame.reset_index(drop=True),
            pd.read_csv(path, float_precision="round_trip"),
            check_dtype=False,
        )
        artifacts[name] = sha(path)
    result = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "planning_inventory_passed",
        "calendar_days": len(dates),
        "calendar_candidate_rows": len(candidates),
        "calendar_core_units": len(core),
        "core_requested_slots": int(quotas.requested_units.sum()),
        "unfilled_core_slots": int(quotas.unfilled_slots.sum()),
        "priority_units": len(stress),
        "province_primary_grid_counts": geographic.primary_province.value_counts().to_dict(),
        "multi_province_grids": int(geographic.province_intersection_count.gt(1).sum()),
        "unassigned_province_area_m2": float(geographic.unassigned_province_area_m2.sum()),
        "province_overlap_sum_excess_m2": float(geographic.province_overlap_sum_excess_m2.sum()),
        "workloads": budgets,
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "protected_inputs_verified": len(protected),
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "final_merge_performed": False,
        "validation_accessed": False,
        "final_test_accessed": False,
        "native_jobs_started": 0,
        "raw_downloads_started": 0,
        "cloud_jobs_started": 0,
        "network_requests": 0,
        "population_error_estimation_permitted": False,
        "limits": [
            "Prespecified shared dates form a purpose-selected method pilot",
            "Quota gaps remain, no outcome-guided date replacement",
            "Original 400-unit weights are provenance, not weights for the new subset",
            "Source bytes cover listed AOI granules, not proved minimum grid-specific work",
            "Expected historical identities are not proof of current NASA source availability",
            "No runtime or monetary price extrapolation from file bytes",
            "Province boundaries are geography audit metadata, not historical predictors",
        ],
    }
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Planning input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == result, "Planning report readback")
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Planning artifact closure")
    completion = {
        "status": "passed",
        "report_sha256": sha(path),
        "inputs_verified": len(pins),
        "artifacts_verified": len(artifacts),
    }
    (out / "completion_readback.json").write_text(
        json.dumps(completion, indent=2) + "\n", encoding="utf-8"
    )
    print("Expansion plan:", out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
