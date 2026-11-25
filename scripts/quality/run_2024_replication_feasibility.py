"""Bounded offline 2024 source/weather readiness; no fitted models or source memberships."""

import argparse
import csv
import json
import math
import re
import socket
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
from pyproj import Transformer, network
from shapely.geometry import Point, shape

from wildfire_risk_prediction import weather_policy
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require, utc_times
from wildfire_risk_prediction.source_year_scan import canonical_utc_text, normalized_year_rows

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
DECISION = ROOT / "configs/2024_source_replication_feasibility_execution_v1.json"
PROPOSAL = ROOT / "configs/2024_source_replication_feasibility_proposal_v1.json"
SOURCE = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
SOURCE_SHA = "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5"
CELL = BASE / "cell_cover_scope_v1/20261119T002103Z_099cd518"


def save(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def table(path, records):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def deny_network(*args, **kwargs):
    raise RuntimeError("Offline feasibility only")


def work(out):
    started = time.monotonic()
    socket.create_connection = deny_network
    socket.socket.connect = deny_network
    network.set_network_enabled(False)
    decision = json.loads(DECISION.read_bytes())
    require(
        decision["scientific_years_for_this_review"] == [2024]
        and decision["local_time_limit_seconds"] == 900,
        "Bounded selected scope",
    )
    pins = {}

    def pin(path, expected=None):
        value = digest(path)
        require(expected is None or value == expected, "Immutable input changed")
        pins[path.relative_to(ROOT).as_posix()] = value
        return path

    def budget():
        require(time.monotonic() - started < 900, "Time budget exceeded")

    pin(DECISION)
    pin(ROOT / "src/wildfire_risk_prediction/source_year_scan.py")
    pin(ROOT / "src/wildfire_risk_prediction/feature_join.py")
    pin(PROPOSAL, decision["proposal_sha256"])
    preparation = BASE / "stage_transition_review_v1/20261124T235727Z_04796a5a/readback.json"
    pin(preparation, decision["preparation_receipt_sha256"])
    pin(SOURCE, SOURCE_SHA)  # Opaque integrity hash does not decode closed years.
    aoi = shape(
        json.loads(
            pin(
                ROOT / "data/aoi/aoi.geojson",
                "d727a6c1e320650a47fd18c7077af847a82d4c99cdc87e49a3c32cb144ea7c22",
            ).read_bytes()
        )["features"][0]["geometry"]
    )
    cell_receipt = json.loads(
        pin(
            CELL / "readback.json",
            "1831e4d0f67789883d9d98f636c6df23194609dbf53a3f74b127ab8c68993f59",
        ).read_bytes()
    )
    cell_path = pin(
        CELL / "cell_map_comparison.csv", cell_receipt["artifact_sha256"]["cell_map_comparison.csv"]
    )
    cells = {r["grid_id"]: r for r in read_rows(cell_path)}
    counts = Counter()
    with SOURCE.open("rb") as handle:
        source_rows = list(normalized_year_rows(handle, year=2024, counts=counts))
    require(source_rows, "No 2024 source rows")
    timestamps = utc_times(
        pd.Series([canonical_utc_text(r["detection_timestamp_utc"]) for r in source_rows])
    )
    require(timestamps.dt.year.eq(2024).all(), "Selected-year guard")
    ids = [r["detection_id"] for r in source_rows]
    require(len(ids) == len(set(ids)), "Unique source detection IDs")
    to_grid = Transformer.from_crs(4326, 6933, always_xy=True)
    selected, daily = [], Counter()
    for row, timestamp in zip(source_rows, timestamps, strict=True):
        budget()
        lon, lat = float(row["longitude"]), float(row["latitude"])
        require(
            math.isfinite(lon) and math.isfinite(lat) and 20 <= lon <= 40 and 30 <= lat <= 45,
            "Source coordinate domain",
        )
        require(row["source_sensor"] in {"SNPP", "N20"}, "Known source sensor")
        gx, gy = to_grid.transform(lon, lat)
        computed = f"E6933_5K_V1_C{math.floor(gx / 5000)}_R{math.floor(gy / 5000)}"
        require(computed == row["grid_id"], "Source grid coordinate consistency")
        quality = row["type"] == "0" and row["confidence"] in {"n", "h"}
        point_in = aoi.covers(Point(lon, lat))
        cell = cells.get(computed)
        water = cell is not None and cell["water_scope_included"] == "True"
        eligible = quality and point_in and water
        counts["existing_type_confidence_rule_pass"] += int(quality)
        counts["point_in_four_province_AOI"] += int(point_in)
        counts["point_and_quality_and_water_scope"] += int(eligible)
        counts["sensor_" + row["source_sensor"]] += 1
        if eligible:
            # At exact midnight the right-closed target belongs to the previous day.
            start = (timestamp - pd.Timedelta(1, unit="ns")).normalize()
            boundary = start.year != 2024 or start + pd.Timedelta(1, unit="D") >= pd.Timestamp(
                "2025-01-01", tz="UTC"
            )
            selected.append(
                {
                    "detection_id": row["detection_id"],
                    "source_sensor": row["source_sensor"],
                    "detection_timestamp_utc": timestamp.isoformat(),
                    "source_timestamp_text_preserved": row["detection_timestamp_utc"],
                    "grid_id": computed,
                    "longitude": lon,
                    "latitude": lat,
                    "type": row["type"],
                    "confidence": row["confidence"],
                    "source_version_field_not_processing_version_proof": row["version"],
                    "conditional_prediction_timestamp_utc": start.isoformat(),
                    "window_boundary_review": boundary,
                    "first_72h_history_boundary_review": timestamp
                    < pd.Timestamp("2024-01-04", tz="UTC"),
                    "target": None,
                    "accepted_L_membership": None,
                    "daily_observation_status": "unknown",
                    "negative_label_permitted": False,
                }
            )
        daily[(timestamp.date().isoformat(), row["source_sensor"], "all")] += 1
        daily[(timestamp.date().isoformat(), row["source_sensor"], "scope")] += int(eligible)
    table(out / "qualified_catalog_2024.csv", selected)
    day_rows = []
    for offset in range(366):
        day = (date(2024, 1, 1) + timedelta(days=offset)).isoformat()
        for sensor in ("SNPP", "N20"):
            day_rows.append(
                {
                    "day": day,
                    "sensor": sensor,
                    "catalog_rows": daily[(day, sensor, "all")],
                    "scope_rows": daily[(day, sensor, "scope")],
                    "zero_count_is_negative_or_good_observation": False,
                }
            )
    table(out / "catalog_days_2024.csv", day_rows)
    save(out / "source_checkpoint.json", {"counts": dict(counts), "selected_rows": len(selected)})
    # Only 2024 daily weather bodies. No 2023 raw source body is read for lag context.
    policy_path = ROOT / "data/interim/meteorology/model_v1/policy_manifest.json"
    require(
        json.loads(pin(policy_path).read_bytes())["policy"] == weather_policy.specification(),
        "Existing weather rule unchanged",
    )
    pin(Path(weather_policy.__file__))
    # The original serializer already used these tolerances for CSV round trips.
    pin(ROOT / "scripts/meteorology/prepare_model_weather.py")
    weather_summary = []
    catalog_weather_support = []
    for offset in range(366):
        budget()
        day = (date(2024, 1, 1) + timedelta(days=offset)).isoformat()
        raw_path = ROOT / "data/interim/meteorology/daily" / (day + ".csv")
        model_path = ROOT / "data/interim/meteorology/model_v1/daily" / (day + ".csv")
        if not (raw_path.is_file() and model_path.is_file()):
            weather_summary.append(
                {
                    "day": day,
                    "files_present": False,
                    "rows": 0,
                    "primary_eligible": 0,
                    "weather_complete": 0,
                    "policy_readback_pass": False,
                    "maximum_serialization_abs_difference": None,
                }
            )
            continue
        pin(raw_path)
        pin(model_path)
        raw, model = [pd.read_csv(p, float_precision="round_trip") for p in (raw_path, model_path)]
        require(
            len(raw) == len(model) == 2899 and set(raw.grid_id) == set(cells),
            "Daily weather cell inventory",
        )
        raw_times = utc_times(raw.prediction_timestamp_utc.map(canonical_utc_text))
        require(raw_times.eq(pd.Timestamp(day, tz="UTC")).all(), "Daily 2024 time contract")
        recalculated = weather_policy.transform(raw)
        require(list(recalculated.columns) == list(model.columns), "Existing weather model schema")
        maximum_difference = 0.0
        for field in model.columns:
            if pd.api.types.is_bool_dtype(model[field]):
                require(model[field].equals(recalculated[field]), "Exact weather QA booleans")
            elif pd.api.types.is_numeric_dtype(model[field]):
                actual, expected = model[field].to_numpy(), recalculated[field].to_numpy()
                require(
                    np.array_equal(pd.isna(actual), pd.isna(expected)), "Exact weather missingness"
                )
                require(
                    np.allclose(actual, expected, rtol=1e-12, atol=1e-12, equal_nan=True),
                    "Original CSV serialization tolerance",
                )
                finite = np.isfinite(actual) & np.isfinite(expected)
                if finite.any():
                    maximum_difference = max(
                        maximum_difference, float(np.max(np.abs(actual[finite] - expected[finite])))
                    )
            else:
                require(
                    model[field].equals(recalculated[field]), "Weather key/metadata/QA readback"
                )
        complete = np.isfinite(model[weather_policy.MODEL_FEATURES].to_numpy(float)).all(axis=1)
        support = model.set_index("grid_id").weather_primary_eligible
        for source_row in selected:
            if source_row["conditional_prediction_timestamp_utc"][:10] == day:
                catalog_weather_support.append(
                    {
                        "detection_id": source_row["detection_id"],
                        "grid_id": source_row["grid_id"],
                        "conditional_prediction_timestamp_utc": source_row[
                            "conditional_prediction_timestamp_utc"
                        ],
                        "weather_primary_eligible": bool(support.loc[source_row["grid_id"]]),
                        "window_boundary_review": source_row["window_boundary_review"],
                        "first_72h_history_boundary_review": source_row[
                            "first_72h_history_boundary_review"
                        ],
                        "new_S_or_Y_or_L": False,
                    }
                )
        weather_summary.append(
            {
                "day": day,
                "files_present": True,
                "rows": len(model),
                "primary_eligible": int(model.weather_primary_eligible.sum()),
                "weather_complete": int(complete.sum()),
                "policy_readback_pass": True,
                "maximum_serialization_abs_difference": maximum_difference,
            }
        )
        if (offset + 1) % 60 == 0:
            table(out / "weather_readiness_2024.csv", weather_summary)
            print("Weather days checked:", offset + 1, flush=True)
    table(out / "weather_readiness_2024.csv", weather_summary)
    table(out / "catalog_weather_support.csv", catalog_weather_support)
    # Path/stat inventory only for other vegetation stores, not their data contents.
    inventory, vegetation_2024 = [], []
    for relative in ("data/raw/vegetation", "data/interim/vegetation"):
        parent = ROOT / relative
        for path in parent.rglob("*"):
            budget()
            if path.is_file() and re.search(
                r"(?<!\d)2024(?!\d)", path.relative_to(parent).as_posix()
            ):
                require(not path.is_symlink(), "Regular vegetation metadata path")
                vegetation_2024.append(
                    {
                        "path": path.relative_to(ROOT).as_posix(),
                        "bytes": path.stat().st_size,
                        "body_read": False,
                        "feature_compatibility_accepted": False,
                    }
                )
    if vegetation_2024:
        table(out / "vegetation_2024_path_candidates.csv", vegetation_2024)
    for relative in (
        "data/raw/vegetation/full_grid_v1",
        "data/interim/vegetation/full_grid_v1",
        "data/interim/vegetation/month_v1",
    ):
        parent = ROOT / relative
        inventory.append(
            {
                "root": relative,
                "root_exists": parent.is_dir(),
                "paths_naming_2024": sum(
                    str(r["path"]).startswith(relative + "/") for r in vegetation_2024
                ),
                "scientific_bodies_read": False,
            }
        )
    table(out / "vegetation_store_scope.csv", inventory)
    # Generic pilot names may not name a year: inspect date/key metadata only.
    generic_metadata = []
    for parent in (
        ROOT / "data/interim/vegetation/pilot_v1",
        ROOT / "data/interim/vegetation/seasonal_v1",
    ):
        for path in parent.glob("*.csv"):
            budget()
            with path.open("rb") as handle:
                fields = next(csv.reader([handle.readline().decode("utf-8-sig").strip()]))
                time_key = next(
                    (k for k in ("prediction_timestamp_utc", "snapshot_cutoff_utc") if k in fields),
                    None,
                )
                rows_2024, grids_2024 = 0, set()
                if time_key:
                    ti, gi = fields.index(time_key), fields.index("grid_id")
                    for raw in handle:
                        require(b'"' not in raw, "Normalized pilot metadata layout")
                        values = raw.rstrip(b"\r\n").split(b",")
                        require(len(values) == len(fields), "Pilot metadata field boundary")
                        if values[ti][:4] == b"2024":
                            rows_2024 += 1
                            grids_2024.add(values[gi].decode("ascii"))
            generic_metadata.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "timestamp_key": time_key,
                    "metadata_rows_2024": rows_2024,
                    "metadata_grids_2024": len(grids_2024),
                    "NDVI_NDMI_values_read": False,
                }
            )
    table(out / "generic_vegetation_metadata.csv", generic_metadata)
    require(
        all(digest(ROOT / p) == h for p, h in pins.items()),
        "Input closure including unchanged source",
    )
    budget()
    result = {
        "status": "2024_feasibility_complete_primary_15_feature_scoring_not_started",
        "analysis_date": "2026-11-25",
        "elapsed_seconds": time.monotonic() - started,
        "source_counts": dict(counts),
        "scope_catalog_rows": len(selected),
        "scope_source_days": len({r["detection_timestamp_utc"][:10] for r in selected}),
        "scope_cells": len({r["grid_id"] for r in selected}),
        "source_version_fields": dict(
            Counter(r["source_version_field_not_processing_version_proof"] for r in selected)
        ),
        "source_rows_are_independent_fires": False,
        "weather_days_checked": len(weather_summary),
        "weather_days_recalculated_equal": sum(r["policy_readback_pass"] for r in weather_summary),
        "weather_rows": sum(r["rows"] for r in weather_summary),
        "weather_primary_eligible_rows": sum(r["primary_eligible"] for r in weather_summary),
        "weather_11_complete_rows": sum(r["weather_complete"] for r in weather_summary),
        "weather_CSV_comparison": {
            "rtol": 1e-12,
            "atol": 1e-12,
            "origin": "scripts/meteorology/prepare_model_weather.py:CSV_serialization_check",
            "missingness_and_QA_booleans_exact": True,
            "maximum_abs_difference": max(
                r["maximum_serialization_abs_difference"] or 0 for r in weather_summary
            ),
        },
        "vegetation_paths_naming_2024": len(vegetation_2024),
        "generic_vegetation_2024_metadata_rows": sum(
            r["metadata_rows_2024"] for r in generic_metadata
        ),
        "weather_primary_supported_catalog_rows": sum(
            r["weather_primary_eligible"] for r in catalog_weather_support
        ),
        "catalog_rows_with_weather_day_file": len(catalog_weather_support),
        "weather_primary_supported_nonboundary_catalog_rows": sum(
            r["weather_primary_eligible"]
            and not r["window_boundary_review"]
            and not r["first_72h_history_boundary_review"]
            for r in catalog_weather_support
        ),
        "vegetation_known_store_inventory": inventory,
        "vegetation_inventory_is_global_disk_absence_proof": False,
        "historical_2024_weather_audit_preexisted": True,
        "new_2023_or_2025_scientific_bodies_read": False,
        "new_model_training_or_predictions": False,
        "new_S_or_Y_or_L": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "final_merge": False,
        "input_sha256": pins,
        "artifact_sha256": {
            p.name: digest(p) for p in out.iterdir() if p.is_file() and p.name != "child.log"
        },
        "streaming_log_excluded_until_parent_close": True,
        "producer_sha256": digest(Path(__file__)),
    }
    save(out / "readback.json", result)
    print("2024 source and local input review completed; no predictions or labels", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker:
        out = args.worker.resolve()
        require(out.is_relative_to(BASE / "2024_replication_feasibility_v1"), "Review output scope")
        work(out)
        return
    out = (
        BASE
        / "2024_replication_feasibility_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    print(out.relative_to(ROOT).as_posix(), flush=True)
    with (out / "child.log").open("w", encoding="utf-8") as log:
        try:
            child = subprocess.run(
                [sys.executable, str(Path(__file__)), "--worker", str(out)],
                cwd=ROOT,
                stdout=log,
                stderr=log,
                timeout=900,
                check=False,
            )
            status = "completed" if child.returncode == 0 else "failed_outputs_retained"
            result = {"status": status, "returncode": child.returncode}
        except subprocess.TimeoutExpired:
            result = {"status": "timeout_outputs_retained", "limit_seconds": 900}
    result["closed_child_log_sha256"] = digest(out / "child.log")
    if (out / "readback.json").is_file():
        result["readback_sha256"] = digest(out / "readback.json")
    save(out / "launcher_receipt.json", result)
    print(result["status"], flush=True)


if __name__ == "__main__":
    main()
