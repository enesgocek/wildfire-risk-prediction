"""Offline target readiness review of nine already accepted exploratory training catalogs."""

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction import target_admission as target
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "outputs/reports/events/review_v1/20261010T001137Z_320433ed/review.json"
SOURCE_SHA = "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    source = ROOT / SOURCE
    require(sha(source) == SOURCE_SHA, "Existing event readback changed")
    reviewed = json.loads(source.read_text())
    require(
        reviewed["status"] == "passed_training_graph_partition_readback"
        and reviewed["final_test_accessed"] is False
        and reviewed["labels_created"] is False
        and reviewed["negative_label_permitted"] is False
        and reviewed["daily_observation_status"] == "unknown"
        and reviewed["scenario_selected"] is None,
        "Existing scope/gates",
    )
    scenarios = {f"d{d}m_t{t}h" for d in (500, 1000, 2000) for t in (24, 48, 72)}
    require(set(reviewed["artifact_sha256"]) == scenarios, "All nine exploratory scenarios")
    inputs = {SOURCE: SOURCE_SHA}
    for name, digest in reviewed["code_sha256"].items():
        require(sha(ROOT / name) == digest, "Previous event method changed")
        inputs[name] = digest
    for name in [
        "src/wildfire_risk_prediction/target_admission.py",
        "src/wildfire_risk_prediction/feature_join.py",
        __file__,
    ]:
        relative = Path(name).relative_to(ROOT).as_posix() if Path(name).is_absolute() else name
        inputs[relative] = sha(ROOT / relative)
    out = (
        ROOT
        / "outputs/reports/dataset/target_admission_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    summaries, artifacts = [], {}
    for scenario in sorted(scenarios):
        path = source.parent / f"{scenario}_review.csv"
        digest = reviewed["artifact_sha256"][scenario]["review_sha256"]
        require(sha(path) == digest, "Catalog changed")
        inputs[path.relative_to(ROOT).as_posix()] = digest
        catalog = pd.read_csv(path)
        diagnostic, summary = target.review_catalog(catalog)
        output = out / f"{scenario}_admission.csv"
        diagnostic.to_csv(output, index=False)
        reread = pd.read_csv(output)
        target.assert_targets_unassigned(reread)
        pd.testing.assert_frame_equal(diagnostic, reread, check_dtype=False)
        # Separate scalar checks on the reread artifact, not a second review_catalog call.
        first = pd.to_datetime(reread.first_detection_utc, format="ISO8601", utc=True).dt.as_unit(
            "ns"
        )
        start = pd.to_datetime(
            reread.candidate_prediction_timestamp_utc, format="ISO8601", utc=True
        ).dt.as_unit("ns")
        end = pd.to_datetime(
            reread.target_end_inclusive_utc, format="ISO8601", utc=True
        ).dt.as_unit("ns")
        require(
            (first.gt(start) & first.le(end)).all()
            and (end.astype("int64") - start.astype("int64")).eq(target.DAY_NS).all(),
            "Independent right-closed window readback",
        )
        pd.testing.assert_series_equal(
            catalog.earliest_grid_ids_json, reread.earliest_grid_ids_json
        )
        require(reread.cluster_id.tolist() == catalog.cluster_id.tolist(), "Cluster keys retained")
        summaries.append({"scenario": scenario, **summary})
        artifacts[output.name] = sha(output)
    require(all(sha(ROOT / name) == digest for name, digest in inputs.items()), "Inputs changed")
    report = {
        "status": "closed_target_admission_readback_passed",
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "policy": target.specification(),
        "source_sha256": SOURCE_SHA,
        "inputs_sha256": inputs,
        "artifact_sha256": artifacts,
        "scenarios": summaries,
        "retained_inputs_unchanged": True,
        "labels_created": False,
        "binary_targets_created": 0,
        "scenario_selected": None,
        "network_requests": 0,
        "final_test_accessed": False,
        "model_ready": False,
        "limits": [
            "Training exploratory clusters; no wildfire or habitat acceptance",
            "Scenario counts overlap and cannot be summed as independent events",
            "Boundary flags are review requirements; no embargo/exclusion policy selected",
            "Identity disjointness has synthetic tests; no finalized event IDs exist",
        ],
    }
    (out / "readback.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "scenarios": 9,
                "binary_targets_created": 0,
                "report": (out / "readback.json").relative_to(ROOT).as_posix(),
            }
        )
    )


if __name__ == "__main__":
    main()
