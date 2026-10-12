"""Offline full-month candidate join/readback using already accepted training sources."""

import argparse
import hashlib
import json
import shutil
import socket
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_month as month_store
from wildfire_risk_prediction import landscape, weather_policy
from wildfire_risk_prediction import vegetation_series as series

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "outputs/reports/dataset/feature_join_v1/20261010T120407Z_d4282cbe/readback.json"
BASELINE_SHA = "b1b3f95757e3ce657042a80e086e309e8efa58acced87ef993571dfbd90b71f0"
WEATHER_REPORT = "outputs/reports/meteorology/model_weather_2018-01-01_2025-01-01.json"
GRID = "data/interim/grid_aoi_parts.geojson"
STATIC = "data/interim/landscape/v1/grid_static.csv"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny_network(*args, **kwargs):
    raise RuntimeError("Network forbidden in the offline feature-month check")


def run(month, vegetation_readback, expected_readback_sha256):
    days = month_store.calendar_days(month)  # Held-out scope gate before source access.
    join.require(
        Path(vegetation_readback).parent.as_posix()
        == f"outputs/reports/landscape/month_v1/{month}",
        "Readback must belong to the selected training month",
    )
    started = time.monotonic()
    inputs = {}

    def retained(name, expected=None):
        name = Path(name).as_posix()
        path = ROOT / name
        join.require(
            name.startswith(("data/interim/", "outputs/reports/", "src/", "scripts/"))
            and path.resolve().is_relative_to(ROOT)
            and path.is_file()
            and not path.is_symlink(),
            "Public retained project source",
        )
        digest = sha(path)
        join.require(expected is None or digest == expected, "Source identity changed")
        join.require(name not in inputs or inputs[name] == digest, "Input changed between reads")
        inputs[name] = digest
        return path

    def record(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    baseline = record(BASELINE, BASELINE_SHA)
    join.require(
        baseline["status"] == "feature_join_pilot_readback_passed"
        and baseline["retained_inputs_unchanged"] is True
        and baseline["final_test_accessed"] is False,
        "Accepted baseline",
    )
    pins = {Path(k).as_posix(): v for k, v in baseline["inputs_sha256"].items()}
    for name, digest in pins.items():
        if "vegetation/" not in name and "month_v1/" not in name:
            retained(name, digest)
    grid = record(GRID, pins[GRID])
    ids = sorted(f["properties"]["grid_id"] for f in grid["features"])
    join.require(len(ids) == len(set(ids)) == 2899, "Canonical project grid")
    static_manifest = record("data/interim/landscape/v1/manifest.json")
    join.require(
        static_manifest["table"] == STATIC
        and static_manifest["table_sha256"] == inputs[STATIC]
        and static_manifest["parts_sha256"] == inputs[GRID]
        and static_manifest["version"] == landscape.VERSION,
        "Static identity",
    )
    static = pd.read_csv(ROOT / STATIC, float_precision="round_trip")
    weather_report = record(WEATHER_REPORT, pins[WEATHER_REPORT])
    join.require(
        weather_report["labels_created"] is False
        and weather_report["final_test_accessed"] is False,
        "Weather report scope",
    )
    policy = record("data/interim/meteorology/model_v1/policy_manifest.json")
    join.require(policy["policy"] == weather_policy.specification(), "Weather policy unchanged")
    selected = [e for e in weather_report["days"] if e["date"] in days]
    join.require(
        len(selected) == len(days)
        and sorted(e["date"] for e in selected) == days
        and all(e["split"] == "train" for e in selected),
        "Complete training weather calendar",
    )
    entries = {e["date"]: e for e in selected}
    raw_roundtrip_max_difference = 0.0
    readback = record(vegetation_readback, expected_readback_sha256)
    join.require(
        readback["status"] == "monthly_daily_readback_passed"
        and readback["month"] == month
        and readback["final_test_accessed"] is False
        and readback["historical_availability_verified"] is False,
        "Accepted vegetation month",
    )
    manifest = record(
        f"data/interim/vegetation/month_v1/{month}/manifest.json", readback["manifest_sha256"]
    )
    veg_path = f"data/interim/vegetation/month_v1/{month}/daily_candidates.csv"
    join.require(
        manifest["month"] == month
        and manifest["version"] == series.VERSION
        and manifest["days"] == len(days)
        and manifest["grid_count"] == len(ids)
        and manifest["rows"] == readback["verified_daily_rows"] == 2 * len(ids) * len(days)
        and manifest["table"] == veg_path
        and manifest["windows"] == list(join.WINDOWS)
        and manifest["cadence_days"] == series.CADENCE_DAYS
        and manifest["max_snapshot_age_days"] == series.RETENTION_DAYS
        and all(
            manifest[f] is False
            for f in [
                "final_test_accessed",
                "historical_availability_verified",
                "fire_labels_created",
            ]
        ),
        "Vegetation source calendar/policy",
    )
    for name, digest in manifest["snapshot_manifests"].items():
        retained(name, digest)
    retained("src/wildfire_risk_prediction/vegetation_series.py", manifest["series_helper_sha256"])
    retained("scripts/landcover/prepare_vegetation_month.py", manifest["builder_sha256"])
    path = retained(veg_path, manifest["table_sha256"])
    join.require(path.stat().st_size < 120_000_000, "Bounded one-month input")
    vegetation = pd.read_csv(path, float_precision="round_trip")
    targets = [d + "T00:00:00+00:00" for d in days]
    join.require(
        len(vegetation) == manifest["rows"]
        and sorted(vegetation.prediction_timestamp_utc.unique()) == targets
        and not vegetation.duplicated(join.KEYS + ["window_days"]).any(),
        "Vegetation daily key inventory",
    )
    for name in [
        "src/wildfire_risk_prediction/feature_partition.py",
        "src/wildfire_risk_prediction/feature_month.py",
        "scripts/quality/verify_feature_month.py",
        "scripts/landcover/run_vegetation_training_v2.py",
        "scripts/landcover/vegetation_iso_adapter.py",
        "scripts/landcover/prepare_vegetation_period.py",
        "scripts/landcover/prepare_vegetation_full_grid.py",
        "scripts/cloud/run_gcp_source_aware_continuation_v6.py",
    ]:
        retained(name)
    join.require(shutil.disk_usage(ROOT).free >= 12 * 2**30, "Disk reserve before month join")
    output = (
        ROOT
        / "outputs/reports/dataset/feature_month_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )

    def weather_for(day):
        nonlocal raw_roundtrip_max_difference
        entry = entries[day]
        model = retained(
            f"data/interim/meteorology/model_v1/daily/{day}.csv", entry["output_sha256"]
        )
        raw_path = retained(f"data/interim/meteorology/daily/{day}.csv", entry["source_sha256"])
        weather = pd.read_csv(model, float_precision="round_trip")
        raw = pd.read_csv(raw_path, float_precision="round_trip")
        pd.testing.assert_frame_equal(
            weather[raw.columns], raw, check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12
        )
        numeric = raw.select_dtypes(include="number").columns
        delta = (weather[numeric] - raw[numeric]).abs().max().max()
        raw_roundtrip_max_difference = max(raw_roundtrip_max_difference, float(delta))
        return weather

    def vegetation_for(day):
        return vegetation.loc[vegetation.prediction_timestamp_utc.eq(day + "T00:00:00+00:00")]

    def frames():
        for day in days:
            join.require(
                shutil.disk_usage(ROOT).free >= 10 * 2**30, "Disk reserve during month join"
            )
            weather = weather_for(day)
            features, qa = join.join_day(weather, static, vegetation_for(day), ids, day)
            yield day, features, qa

    manifest_sha = month_store.write_month(output, frames(), ids, month)
    missing = dict.fromkeys(join.feature_names(), 0)
    support = dict.fromkeys([str(w) for w in join.WINDOWS], 0)
    checked = []
    # Separate readback path compares stored values directly to source identities, not another join.
    for day, features, qa in month_store.iter_month(
        output, expected_manifest_sha256=manifest_sha, grid_ids=ids
    ):
        saved = features.set_index("grid_id").loc[ids]
        quality = qa.set_index("grid_id").loc[ids]
        weather = weather_for(day)
        for source, fields in [
            (weather, weather_policy.MODEL_FEATURES),
            (static, landscape.COVER_FEATURES + landscape.TERRAIN_FEATURES),
        ]:
            pd.testing.assert_frame_equal(
                saved[fields],
                source.set_index("grid_id").loc[ids, fields],
                check_dtype=False,
                check_exact=True,
            )
        for field in join.WEATHER_QA:
            pd.testing.assert_series_equal(
                quality[field],
                weather.set_index("grid_id").loc[ids, field],
                check_names=False,
                check_dtype=False,
                check_exact=True,
            )
        for field in join.STATIC_QA:
            pd.testing.assert_series_equal(
                quality["static_" + field],
                static.set_index("grid_id").loc[ids, field],
                check_names=False,
                check_dtype=False,
                check_exact=True,
            )
        for window in join.WINDOWS:
            daily = vegetation_for(day)
            source = daily.loc[daily.window_days.eq(window)]
            source = source.set_index("grid_id").loc[ids]
            for field in join.VEGETATION_FEATURES:
                pd.testing.assert_series_equal(
                    saved[f"vegetation_{window}d_{field}"],
                    source[field],
                    check_names=False,
                    check_dtype=False,
                    check_exact=True,
                )
            for field in join.VEGETATION_QA:
                pd.testing.assert_series_equal(
                    quality[f"vegetation_{window}d_{field}"],
                    source[field],
                    check_names=False,
                    check_dtype=False,
                    check_exact=True,
                )
            support[str(window)] += int(source.vegetation_present.sum())
        for field in missing:
            missing[field] += int(saved[field].isna().sum())
        checked.append(day)
    join.require(checked == days, "All calendar days independently checked")
    join.require(all(sha(ROOT / k) == v for k, v in inputs.items()), "Protected sources changed")
    part_manifest = json.loads((output / "parts/manifest.json").read_bytes())
    report = {
        "status": "complete_month_candidate_readback_passed",
        "version": month_store.VERSION,
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "month": month,
        "split": "train",
        "days": checked,
        "rows": len(days) * len(ids),
        "candidate_features": join.feature_names(),
        "missing_by_feature": missing,
        "vegetation_supported_cell_days": support,
        "manifest_sha256": manifest_sha,
        "inputs_sha256": inputs,
        "inputs_unchanged": True,
        "data_part_bytes": sum(
            a["bytes"] for e in part_manifest["days"] for a in e["artifacts"].values()
        ),
        "elapsed_seconds": time.monotonic() - started,
        "raw_weather_comparison_rtol": 1e-12,
        "raw_weather_comparison_atol": 1e-12,
        "raw_weather_max_absolute_roundtrip_difference": raw_roundtrip_max_difference,
        "network_requests": 0,
        "daily_observation_status": "unknown",
        **dict.fromkeys(month_store.FALSE_FLAGS, False),
        "limits": [
            "One complete training month; candidate features only, no target/habitat acceptance",
            "Existing source readbacks reused; raw extraction or field validation not repeated",
            "CSV pilot storage; no full-period production or storage-format performance claim",
        ],
    }
    report_path = output / "readback.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["status", "month", "rows", "data_part_bytes"]}))
    print("Report:", report_path.relative_to(ROOT).as_posix())
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", required=True)
    parser.add_argument("--vegetation-readback", required=True)
    parser.add_argument("--expected-readback-sha256", required=True)
    args = parser.parse_args()
    socket.socket.connect = deny_network
    socket.socket.connect_ex = deny_network
    socket.create_connection = deny_network
    run(args.month, args.vegetation_readback, args.expected_readback_sha256)
