"""Verify frozen observation/reference summaries; never infer labels from coverage."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCES = {
    "observation": (
        "observation_protocol_evidence_v1/20261015T143126Z_dc01eb0c",
        "c87a96944635f650a9eb30005d959a56d998cd73154b3b48441a80e0e1a59df2",
    ),
    "selection": (
        "protocol_selection_v1/20261015T194012Z_72ade129",
        "e19de33e0db98948369c971a6d4d9966caf208574df73ad3059e8b26a6159242",
    ),
    "reference": (
        "reference_intake_v1/20261015T195625Z_e277865f",
        "1f6fef07264e955725793e0bc8da4ba817741d0a13b4478981580f9c7fb8c0e1",
    ),
}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def main():
    pins, reports = {}, {}
    for role, (relative, expected) in SOURCES.items():
        folder = BASE / relative
        report = folder / "readback.json"
        require(sha(report) == expected, "Changed report")
        pins[report.relative_to(ROOT).as_posix()] = expected
        record = json.loads(report.read_text())
        for name, digest in record["artifact_sha256"].items():
            artifact = folder / name
            require(artifact.resolve().is_relative_to(folder.resolve()), "Nonlocal artifact")
            require(sha(artifact) == digest, "Changed artifact")
            pins[artifact.relative_to(ROOT).as_posix()] = digest
        for gate in (
            "negative_label_permitted",
            "labels_created",
            "model_ready",
            "final_merge_performed",
        ):
            require(record[gate] is False, "Unexpected open acceptance gate")
        require(record["daily_observation_status"] == "unknown", "Observation state changed")
        reports[role] = record
    require(reports["selection"]["parent_sha256"] == SOURCES["observation"][1], "Lineage")
    require(
        reports["observation"]["unit_count"] == reports["selection"]["unit_count"] == 156,
        "Changed pilot",
    )
    require(reports["reference"]["matching_ready_context_records"] == 0, "New reference exists")
    require(reports["reference"]["institutional_incident_rows"] == 0, "New incident rows exist")
    pins[Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__))
    result = {
        "source_sha256": pins,
        "scope": "current_byte_readback_of_previous_pilot_not_new_observation_or_error_estimation",
        "pilot_units": 156,
        "pilot_days": reports["selection"]["target_days"],
        "pilot_grids": reports["selection"]["distinct_grids"],
        "thermal_witness_units_not_verified_new_fires": reports["observation"][
            "thermal_definite_units"
        ],
        "thermal_absent_units_not_verified_negatives": 156
        - reports["observation"]["thermal_definite_units"],
        "context_records": reports["reference"]["public_context_records"],
        "matching_ready_reference_records": 0,
        "population_error_rate_estimated": False,
        "observation_policy_accepted": False,
        "PU_method_accepted": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    for relative, expected in pins.items():
        require(sha(ROOT / relative) == expected, "Input changed during run")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = BASE / "label_evidence_readiness_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    report = out / "readback.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(json.loads(report.read_text()) == result, "JSON readback")
    print(out.relative_to(ROOT))
    print("report_sha256", sha(report))
    print("pins", len(pins))


if __name__ == "__main__":
    main()
