"""Offline quality summary from a pinned, fully audited training candidate index."""

import argparse
import json
import socket
from datetime import UTC, datetime

from prepare_dataset import ROOT, candidate_report, new_directory, read_record, sha

from wildfire_risk_prediction import dataset_batch as batch
from wildfire_risk_prediction import dataset_contract as contract
from wildfire_risk_prediction import dataset_quality as quality
from wildfire_risk_prediction.feature_join import require

REGISTRY = "configs/gcp_source_blocks_2026-10-13.json"
REGISTRY_SHA = "c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95"


def profile(audit_path, expected_sha256):
    batch.public_path(audit_path, "outputs/reports/dataset/candidate_audit_v1/")
    audited, audit_sha = read_record(audit_path, expected_sha256)
    require(
        audited["status"] == "candidate_index_structural_readback_passed"
        and audited["candidate_calendar_complete"] is True
        and audited["verified_candidate_months"] == 72
        and audited["verified_candidate_rows"] == 6351709
        and audited["scientific_acceptance_granted"] is False
        and audited["daily_observation_status"] == "unknown"
        and all(
            audited[f] is False
            for f in (
                "labels_created",
                "model_ready",
                "final_test_accessed",
                "negative_label_permitted",
                "validation_ready",
            )
        ),
        "Complete accepted candidate audit; scientific gates remain closed",
    )
    refs = [batch.candidate_reference(ref) for ref in audited["reports"]]
    require(batch.candidate_inventory(refs)["candidate_calendar_complete"], "Complete references")
    index_path = audited["source_index"]
    batch.public_path(index_path, "outputs/reports/dataset/candidate_batch_v1/")
    index, index_sha = read_record(index_path, audited["source_index_sha256"])
    require(
        index["status"] == "completed_selected_candidate_months"
        and index["reports"] == refs
        and index["error_type"] is None
        and index["daily_observation_status"] == "unknown"
        and all(
            index[f] is False
            for f in (
                "labels_created",
                "model_ready",
                "final_test_accessed",
                "negative_label_permitted",
            )
        ),
        "Final batch and accepted index identity",
    )
    pins = {audit_path: audit_sha, index_path: index_sha}
    reports = []
    for ref in refs:
        reports.append(candidate_report(ref))
        pins[ref["path"]] = ref["sha256"]
    require(sha(ROOT / REGISTRY) == REGISTRY_SHA, "Frozen source gap registry")
    registry = json.loads((ROOT / REGISTRY).read_text(encoding="utf-8"))
    require(
        registry["daily_observation_status"] == "unknown"
        and registry["negative_label_permitted"] is False,
        "Source gap policy",
    )
    pins[REGISTRY] = REGISTRY_SHA
    for name in (
        "scripts/quality/profile_training_dataset.py",
        "src/wildfire_risk_prediction/dataset_quality.py",
        "scripts/quality/prepare_dataset.py",
        "src/wildfire_risk_prediction/dataset_batch.py",
        "src/wildfire_risk_prediction/dataset_contract.py",
        "src/wildfire_risk_prediction/feature_join.py",
        "src/wildfire_risk_prediction/feature_month.py",
        "src/wildfire_risk_prediction/target_admission.py",
    ):
        pins[name] = sha(ROOT / name)
    value = {
        "status": "training_candidate_quality_summary_passed",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        **quality.summarize(reports),
        "source_gap_review": quality.source_gap_review(registry["deferred_days"]),
        "source_file_sha256": pins,
        "candidate_feature_csvs_reread": False,
        "source_month_report_bytes_verified": True,
        "new_imputation_applied": False,
        "network_requests": 0,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "final_test_accessed": False,
        "release_blockers": contract.release_blockers(),
    }
    require(all(sha(ROOT / p) == h for p, h in pins.items()), "Quality inputs changed")
    folder = new_directory("quality_profile_v1")
    with (folder / "readback.json").open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print("Quality report:", (folder / "readback.json").relative_to(ROOT).as_posix())
    print("Quality SHA256:", sha(folder / "readback.json"))
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted-audit", required=True)
    parser.add_argument("--expected-audit-sha256", required=True)
    args = parser.parse_args()

    def deny(*args, **kwargs):
        raise RuntimeError("Network forbidden during offline quality profiling")

    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    socket.create_connection = deny
    profile(args.accepted_audit, args.expected_audit_sha256)


if __name__ == "__main__":
    main()
