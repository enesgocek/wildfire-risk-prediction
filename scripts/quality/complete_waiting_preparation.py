"""Close the bounded, existing-evidence preparations; institutional decisions stay open."""

import argparse
import json
import socket
from datetime import UTC, datetime

from prepare_dataset import ROOT, new_directory, sha

from wildfire_risk_prediction.dataset_execution import preflight_training_merge
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

EVIDENCE = dict(
    [
        (
            "outputs/reports/dataset/event_lineage_v1/20261016T190431Z_31a64912/readback.json",
            "dd4652f7bb900c08f3de8e5a96bc9f0f329d90f3eb43b314d4d9c615577b792b",
        ),
        (
            "outputs/reports/dataset/reference_intake_v1/20261015T195625Z_e277865f/readback.json",
            "1f6fef07264e955725793e0bc8da4ba817741d0a13b4478981580f9c7fb8c0e1",
        ),
        (
            "outputs/reports/dataset/preparation_inventory_v1/20261016T145525Z_f9625e9e/readback.json",
            "1832b3b6426030ffc5165c600c593e877c7ab88ebba185469c51258ceb55a73e",
        ),
    ]
)


def run(feature_path, expected_sha):
    def deny(*args, **kwargs):
        raise RuntimeError("Offline bounded preparation closeout")

    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    socket.create_connection = deny
    require(
        feature_path.startswith("outputs/reports/dataset/waiting_features_v1/")
        and (ROOT / feature_path).resolve().is_relative_to(ROOT),
        "Feature audit path",
    )
    pins = {}

    def retain(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained preparation input",
        )
        actual = sha(path)
        require(expected is None or actual == expected, "Pinned preparation changed")
        pins[name] = actual
        return path

    feature = json.loads(retain(feature_path, expected_sha).read_text(encoding="utf-8"))
    require(
        feature["status"] == "training_feature_preparation_readback_passed"
        and feature["rows"] == 6351709
        and feature["days"] == 2191
        and feature["daily_files_content_hash_verified"] == 4382
        and feature["scientific_acceptance_granted"] is False
        and feature["fresh_final_five_part_review"] is False,
        "Full current feature preparation, not final approval",
    )
    folder_name = feature_path.rsplit("/", 1)[0]
    closure = json.loads(retain(folder_name + "/completion_readback.json").read_text())
    require(closure["report_sha256"] == expected_sha, "Feature report closure")
    for name, digest in feature["artifact_sha256"].items():
        retain(folder_name + "/" + name, digest)
    for name, digest in EVIDENCE.items():
        value = json.loads(retain(name, digest).read_text(encoding="utf-8"))
        parent_folder = name.rsplit("/", 1)[0]
        closed = json.loads(retain(parent_folder + "/completion_readback.json").read_text())
        require(closed["report_sha256"] == digest, "Existing evidence closure")
        for filename, expected in value["artifact_sha256"].items():
            retain(parent_folder + "/" + filename, expected)
    for name in (
        "docs/RESPONSE_WAITING_PREPARATION_2026-10-17.md",
        "docs/WEATHER_POLICY.md",
        "docs/HABITAT_REVIEW_2026-10-10.md",
        "configs/final_merge_review_v1.json",
        "configs/first_cell_candidates_v1.json",
        "scripts/quality/complete_waiting_preparation.py",
        "scripts/quality/preflight_training_merge.py",
        "src/wildfire_risk_prediction/dataset_execution.py",
        "src/wildfire_risk_prediction/target_admission.py",
        "src/wildfire_risk_prediction/final_merge_gate.py",
    ):
        retain(name)
    rejected = False
    try:
        preflight_training_merge(ROOT)
    except PermissionError:
        rejected = True
    require(rejected, "Missing real review/approval must stop before data access")
    state = specification()
    require(
        state["daily_observation_status"] == "unknown"
        and state["negative_label_permitted"] is False
        and state["positive_label_permitted"] is False,
        "Closed scientific state",
    )
    dependencies = [
        {"id": "source_semantics", "reply": "NASA_FIRMS", "decision": "source_type_version"},
        {
            "id": "source_exceptions",
            "reply": "applicable_source_explanation_if_provided",
            "decision": "two_days_and_affected_windows",
        },
        {"id": "incident_reference", "reply": "OGM", "decision": "time_location_matching"},
        {"id": "reference_coverage", "reply": "OGM", "decision": "record_scope"},
        {
            "id": "event_rule",
            "reply": "independent_incident_evidence_if_provided",
            "decision": "birth_continuation_grouping",
        },
        {
            "id": "negative_policy",
            "reply": "observation_and_reference_limits_if_provided",
            "decision": "sufficient_observation_and_uncertainty",
        },
        {
            "id": "habitat",
            "reply": "institutional_scope_if_provided",
            "decision": "mixed_cover_agriculture_historical_limits",
        },
        {
            "id": "boundary",
            "reply": "time_definitions_if_provided",
            "decision": "embargo_source_gap_windows",
        },
        {"id": "use_terms", "reply": "OGM", "decision": "access_publication_redistribution"},
    ]
    for row in dependencies:
        row.update(
            {
                "status": "pending_evidence_and_researcher_decision",
                "reply_alone_grants_acceptance": False,
            }
        )
    folder = new_directory("waiting_preparation_v1")
    artifacts = {
        "reply_dependencies.json": dependencies,
        "execution_readiness.json": {
            "real_missing_approval_rejected": rejected,
            "normalized_five_part_manifest_byte_checker_prepared": True,
            "current_binary_label_builder": "not_accepted_new_protocol_required",
            "final_dataset_writer": "not_implemented_pending_accepted_target_contract",
            "real_review_or_user_approval_created": False,
            "real_label_generation": False,
            "final_merge_executed": False,
        },
        "input_manifest.json": pins,
    }
    for name, value in artifacts.items():
        (folder / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    hashes = {name: sha(folder / name) for name in artifacts}
    summary = {
        "status": "existing_evidence_preparation_complete_waiting_for_replies",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "feature_report": feature_path,
        "feature_report_sha256": expected_sha,
        "preparation_packages": {
            "feature_checks": "completed_retrospective_candidates_only",
            "reply_decision_dossier": "prepared_decisions_open",
            "execution_preparation": "preflight_ready_scientific_builder_deferred",
        },
        "dependency_topics": len(dependencies),
        "new_institutional_reply_read": False,
        "all_possible_project_work_complete": False,
        "scientific_acceptance_granted": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "positive_label_permitted": False,
        "labels_created": False,
        "final_merge_executed": False,
        "model_fitted": False,
        "validation_data_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "artifact_sha256": hashes,
    }
    (folder / "readback.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for name, expected in pins.items():
        require(sha(ROOT / name) == expected, "Preparation input changed during closure")
    for name, value in artifacts.items():
        require(
            sha(folder / name) == hashes[name]
            and json.loads((folder / name).read_text(encoding="utf-8")) == value,
            "Preparation artifact readback",
        )
    (folder / "completion_readback.json").write_text(
        json.dumps(
            {
                "status": "waiting_preparation_outputs_verified",
                "report_sha256": sha(folder / "readback.json"),
                "artifact_sha256": hashes,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("WAITING PREPARATION", folder.relative_to(ROOT).as_posix())
    return folder


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-report", required=True)
    parser.add_argument("--expected-feature-sha256", required=True)
    args = parser.parse_args()
    run(args.feature_report, args.expected_feature_sha256)
