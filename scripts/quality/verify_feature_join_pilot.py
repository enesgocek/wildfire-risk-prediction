"""Offline one-day join/readback of retained training features; no labels or downloads."""

import argparse
import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import landscape, weather_policy

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def run(day):
    target = join.training_day(day)  # Scope gate before any source read.
    inputs = {}

    def retained(name):
        path = ROOT / name
        join.require(path.is_file() and not path.is_symlink(), "Retained regular input")
        inputs[name] = sha(path)
        return path

    def record(name):
        return json.loads(retained(name).read_text(encoding="utf-8"))

    grid_path = "data/interim/grid_aoi_parts.geojson"
    ids = sorted(f["properties"]["grid_id"] for f in record(grid_path)["features"])
    join.require(len(ids) == len(set(ids)) == 2899, "Project grid")
    model_report = record("outputs/reports/meteorology/model_weather_2018-01-01_2025-01-01.json")
    join.require(
        model_report["final_test_accessed"] is False and model_report["labels_created"] is False,
        "Weather report scope",
    )
    weather_entry = next(d for d in model_report["days"] if d["date"] == day)
    join.require(weather_entry["split"] == "train", "Training weather entry")
    weather_path = f"data/interim/meteorology/model_v1/daily/{day}.csv"
    retained(weather_path)
    join.require(inputs[weather_path] == weather_entry["output_sha256"], "Weather output hash")
    raw_path = f"data/interim/meteorology/daily/{day}.csv"
    retained(raw_path)
    join.require(inputs[raw_path] == weather_entry["source_sha256"], "Weather source hash")
    policy_path = "data/interim/meteorology/model_v1/policy_manifest.json"
    policy = record(policy_path)
    join.require(
        inputs[policy_path] == model_report["policy_manifest_sha256"]
        and policy["policy"] == weather_policy.specification(),
        "Weather policy",
    )
    for name, digest in [
        ("src/wildfire_risk_prediction/weather_policy.py", policy["policy_code_sha256"]),
        ("scripts/meteorology/prepare_era5_land.py", policy["source_processing_code_sha256"]),
        ("scripts/meteorology/prepare_model_weather.py", model_report["preparation_code_sha256"]),
        (policy["review"], policy["review_sha256"]),
    ]:
        retained(name)
        join.require(inputs[name] == digest, "Weather method/review changed")
    weather = pd.read_csv(ROOT / weather_path)
    raw = pd.read_csv(ROOT / raw_path)
    pd.testing.assert_frame_equal(
        weather[raw.columns], raw, check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12
    )

    static_manifest = record("data/interim/landscape/v1/manifest.json")
    static_path = "data/interim/landscape/v1/grid_static.csv"
    retained(static_path)
    join.require(
        static_manifest["table"] == static_path
        and inputs[static_path] == static_manifest["table_sha256"]
        and static_manifest["parts_sha256"] == inputs[grid_path]
        and static_manifest["version"] == landscape.VERSION
        and all(
            static_manifest[f] is False
            for f in [
                "final_test_accessed",
                "labels_created",
                "historical_availability_verified",
                "habitat_eligibility_decided",
            ]
        ),
        "Static manifest",
    )
    static_report = record("outputs/reports/landscape/local_readback.json")
    join.require(
        static_report["status"] == "passed_local_integral_readback"
        and static_report["source_and_output_hashes_verified"] is True,
        "Existing static readback",
    )
    static = pd.read_csv(ROOT / static_path)
    month = day[:7]
    manifest_name = f"data/interim/vegetation/month_v1/{month}/manifest.json"
    manifest = record(manifest_name)
    readback = record(f"outputs/reports/landscape/month_v1/{month}/iso_v2_offline_readback.json")
    join.require(
        readback["status"] == "monthly_daily_readback_passed"
        and readback["manifest_sha256"] == inputs[manifest_name]
        and readback["month"] == month
        and readback["final_test_accessed"] is False,
        "Existing vegetation acceptance",
    )
    veg_path = f"data/interim/vegetation/month_v1/{month}/daily_candidates.csv"
    retained(veg_path)
    join.require(
        manifest["table"] == veg_path
        and inputs[veg_path] == manifest["table_sha256"]
        and manifest["rows"] == readback["verified_daily_rows"]
        and all(
            manifest[f] is False
            for f in [
                "final_test_accessed",
                "historical_availability_verified",
                "fire_labels_created",
            ]
        ),
        "Vegetation manifest",
    )
    for name, digest in manifest["snapshot_manifests"].items():
        retained(name)
        join.require(inputs[name] == digest, "Snapshot manifest changed")
    chunks = pd.read_csv(ROOT / veg_path, chunksize=20000)
    vegetation = pd.concat(
        [c.loc[c.prediction_timestamp_utc.eq(target.isoformat())] for c in chunks],
        ignore_index=True,
    )
    for name in [
        "src/wildfire_risk_prediction/feature_join.py",
        "src/wildfire_risk_prediction/landscape.py",
        "src/wildfire_risk_prediction/vegetation.py",
        __file__,
    ]:
        retained(Path(name).relative_to(ROOT).as_posix() if Path(name).is_absolute() else name)
    features, qa = join.join_day(weather, static, vegetation, ids, day)
    folder = (
        ROOT
        / "outputs/reports/dataset/feature_join_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )
    folder.mkdir(parents=True, exist_ok=False)
    features.to_csv(folder / "features.csv", index=False)
    qa.to_csv(folder / "provenance.csv", index=False)
    saved = pd.read_csv(folder / "features.csv").set_index("grid_id").loc[ids]
    saved_qa = pd.read_csv(folder / "provenance.csv")
    pd.testing.assert_frame_equal(
        qa, saved_qa, check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12
    )
    join.require(saved.prediction_timestamp_utc.eq(target.isoformat()).all(), "Readback keys")
    # Independent column-by-column comparison to source keys; never call join again.
    for source, fields in [
        (weather, weather_policy.MODEL_FEATURES),
        (static, landscape.COVER_FEATURES + landscape.TERRAIN_FEATURES),
    ]:
        original = source.set_index("grid_id").loc[ids]
        pd.testing.assert_frame_equal(
            saved[fields],
            original[fields],
            check_dtype=False,
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )
    for window in join.WINDOWS:
        original = vegetation.loc[vegetation.window_days.eq(window)].set_index("grid_id").loc[ids]
        for field in join.VEGETATION_FEATURES:
            pd.testing.assert_series_equal(
                saved[f"vegetation_{window}d_{field}"],
                original[field],
                check_names=False,
                check_dtype=False,
                check_exact=False,
                rtol=1e-12,
                atol=1e-12,
            )
    join.require(
        all(sha(ROOT / name) == digest for name, digest in inputs.items()),
        "Retained inputs changed during readback",
    )
    report = {
        "status": "feature_join_pilot_readback_passed",
        "version": join.VERSION,
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "day": day,
        "split": "train",
        "rows": len(saved),
        "candidate_feature_count": len(join.feature_names()),
        "candidate_features": join.feature_names(),
        "qa_columns_are_model_inputs": False,
        "missing_by_feature": {f: int(saved[f].isna().sum()) for f in join.feature_names()},
        "weather_primary_eligible": int(weather.weather_primary_eligible.sum()),
        "vegetation_supported": {
            str(w): int(vegetation.loc[vegetation.window_days.eq(w), "vegetation_present"].sum())
            for w in join.WINDOWS
        },
        "inputs_sha256": inputs,
        "retained_inputs_unchanged": True,
        "features_sha256": sha(folder / "features.csv"),
        "provenance_sha256": sha(folder / "provenance.csv"),
        "network_requests": 0,
        "labels_created": False,
        "model_ready": False,
        "final_test_accessed": False,
        "historical_availability_verified": False,
        "operational_eligible_rows": 0,
        "habitat_eligibility_decided": False,
        "limits": [
            "One training day, all cells retained; no model or event acceptance",
            "Derived source hashes and existing readback records reused; "
            "raw extraction not repeated",
            "Historical availability unknown; no imputation, labels or final-test data",
        ],
    }
    (folder / "readback.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "rows": len(saved),
                "candidate_features": len(join.feature_names()),
                "report": (folder / "readback.json").relative_to(ROOT).as_posix(),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day", default="2018-08-01")
    run(parser.parse_args().day)
