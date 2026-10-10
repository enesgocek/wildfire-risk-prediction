"""Offline partition/readback of four accepted training days; no extraction or labels."""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_partition as store

ROOT = Path(__file__).resolve().parents[2]
PILOTS = [
    (
        "20261010T120407Z_d4282cbe",
        "b1b3f95757e3ce657042a80e086e309e8efa58acced87ef993571dfbd90b71f0",
    ),
    (
        "20261010T120945Z_c66a13c1",
        "e413d28fbb2da46524f0a11ea022766be5d71976d423681fdeb226a76f496519",
    ),
    (
        "20261010T120947Z_b843472f",
        "007887f69e0eafe580f4e83043f0bddf2c1a6257d02da101c0695620aaf3c778",
    ),
    (
        "20261010T120949Z_b9f7fdfa",
        "7b2e544a9e8ce1789c5623adaf18d1eb16abcf2a8d52c74217edba35e11006e0",
    ),
]


def run():
    inputs = {}

    def retained(name, expected=None):
        path = ROOT / name
        join.require(
            path.resolve().is_relative_to(ROOT) and path.is_file() and not path.is_symlink(),
            "Retained project file",
        )
        data = path.read_bytes()
        digest = store.digest(data)
        join.require(expected is None or expected == digest, "Retained source hash")
        if name in inputs:
            join.require(inputs[name] == digest, "Source changed between pilot reads")
        inputs[name] = digest
        return data

    grid = json.loads(retained("data/interim/grid_aoi_parts.geojson"))
    ids = sorted(f["properties"]["grid_id"] for f in grid["features"])
    join.require(len(ids) == len(set(ids)) == 2899, "Canonical project grid")
    sources = {}
    for folder, digest in PILOTS:
        base = f"outputs/reports/dataset/feature_join_v1/{folder}"
        report = json.loads(retained(f"{base}/readback.json", digest))
        join.training_day(report["day"])
        join.require(
            report["status"] == "feature_join_pilot_readback_passed"
            and report["split"] == "train"
            and report["rows"] == 2899
            and report["candidate_features"] == join.feature_names()
            and report["retained_inputs_unchanged"] is True
            and all(
                report[f] is False for f in ["labels_created", "model_ready", "final_test_accessed"]
            ),
            "Accepted pilot identity",
        )
        for name, expected in report["inputs_sha256"].items():
            retained(name, expected)
        join.require(report["day"] not in sources, "Repeated source pilot day")
        sources[report["day"]] = (base, report)
        for kind in ["features", "provenance"]:
            retained(f"{base}/{kind}.csv", report[f"{kind}_sha256"])
    for name in ["src/wildfire_risk_prediction/feature_partition.py", __file__]:
        name = Path(name)
        retained(name.relative_to(ROOT).as_posix() if name.is_absolute() else name.as_posix())

    def frames():
        for day, (base, report) in sorted(sources.items()):
            tables = [
                store.parse_csv(retained(f"{base}/{kind}.csv", report[f"{kind}_sha256"]))
                for kind in ["features", "provenance"]
            ]
            yield day, *tables

    output = (
        ROOT
        / "outputs/reports/dataset/feature_partition_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )
    manifest_sha = store.write_pilot(output, frames(), ids)
    checked, missing = [], {f: 0 for f in join.feature_names()}
    for day, features, qa in store.iter_pilot(
        output, expected_manifest_sha256=manifest_sha, grid_ids=ids
    ):
        base, source = sources[day]
        for kind, actual in [("features", features), ("provenance", qa)]:
            expected = store.parse_csv(retained(f"{base}/{kind}.csv", source[f"{kind}_sha256"]))
            expected = expected.set_index("grid_id").loc[ids].reset_index()
            pd.testing.assert_frame_equal(actual, expected, check_dtype=False, check_exact=True)
        for field in missing:
            missing[field] += int(features[field].isna().sum())
        checked.append(day)
    join.require(checked == sorted(sources), "Every source day read back")
    for name, digest in inputs.items():
        join.require(store.digest((ROOT / name).read_bytes()) == digest, "Input changed")
    manifest = json.loads((output / "manifest.json").read_bytes())
    report = {
        "status": "feature_partition_pilot_readback_passed",
        "version": store.VERSION,
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "manifest_sha256": manifest_sha,
        "rows": manifest["rows"],
        "days": checked,
        "month_coverage": {"2018-08": {"pilot_days": 4, "calendar_days": 31}},
        "candidate_features": len(join.feature_names()),
        "missing_by_feature": missing,
        "data_part_bytes": sum(
            a["bytes"] for e in manifest["days"] for a in e["artifacts"].values()
        ),
        "inputs_sha256": inputs,
        "inputs_unchanged": True,
        "network_requests": 0,
        "labels_created": False,
        "model_ready": False,
        "final_test_accessed": False,
        "historical_availability_verified": False,
        "limits": [
            "Four previously accepted days; no new source extraction or whole-month acceptance",
            "Reader bounds data frames to one day; no full-period memory/runtime benchmark",
            "No imputation, model, label policy, habitat decision or operational availability",
        ],
    }
    (output / "readback.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["status", "rows", "days", "data_part_bytes"]}))
    print("Report:", (output / "readback.json").relative_to(ROOT).as_posix())


if __name__ == "__main__":
    run()
