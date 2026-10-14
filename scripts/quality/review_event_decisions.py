"""Offline decision sensitivity from accepted training review packets; no relabelling."""

import hashlib
import json
import socket
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.event_decision_review import protocol, sensitivity
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.label_review import REVIEW_FIELDS

ROOT = Path(__file__).resolve().parents[2]
PACKET = "outputs/reports/dataset/label_review_v1/20261014T153649Z_ca3fb92e"
PERIMETER = "outputs/reports/dataset/perimeter_review_v1/20261014T162023Z_61ec4cba"
MEMBERS = "outputs/reports/dataset/decision_review_v1/20261010T124447Z_f3e2eef2/event_members.csv"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline event decision review")


def run():
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular decision input")
        digest = sha(path)
        require(expected is None or digest == expected, "Decision input hash changed")
        pins[name] = digest
        return path

    def packet(directory, digest):
        saved = json.loads(retained(directory + "/readback.json", digest).read_text())
        require(not saved["labels_created"] and not saved["model_ready"], "Unlabelled inputs")
        return {
            name: retained(directory + "/" + name, h)
            for name, h in saved["artifact_sha256"].items()
        }

    packet_files = packet(
        PACKET, "36ce8565a452efbf2a4f1e69fe3254ae33ccdd818eb08584f57b41a9eaf28037"
    )
    perimeter_files = packet(
        PERIMETER, "32f85afaf1b2a223bae1c7e4003a2f953fa8563d03c97925ca5b0d12b9126810"
    )
    cases = pd.read_csv(packet_files["purposive_event_cases.csv"])
    members = pd.read_csv(
        retained(MEMBERS, "bb24d25379acde97d65edd7bcff93e07b2b0ec61f84adb811ecfcf06e958c391")
    )
    spatial = pd.read_csv(perimeter_files["case_spatial_summary.csv"])
    links = pd.read_csv(
        perimeter_files["case_reference_spatial_links.csv"], dtype={"reference_id": str}
    )
    forms = pd.read_csv(packet_files["review_decisions_template.csv"])
    require(
        len(forms) == 453
        and forms.review_status.eq("not_reviewed").all()
        and forms[REVIEW_FIELDS].isna().all().all(),
        "Human forms remain unreviewed",
    )
    for name in (
        "src/wildfire_risk_prediction/event_decision_review.py",
        "src/wildfire_risk_prediction/target_admission.py",
        "scripts/quality/review_event_decisions.py",
        PROTECTED,
    ):
        retained(name)
    for name, digest in json.loads((ROOT / PROTECTED).read_text()).items():
        retained(name, digest)
    review, families = sensitivity(cases, members, spatial, links)
    draft = protocol()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/event_decisions_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (("case_decision_queue.csv", review), ("overlap_families.csv", families)):
        path = out / name
        frame.to_csv(path, index=False, mode="x")
        reread = pd.read_csv(path, float_precision="round_trip")
        pd.testing.assert_frame_equal(frame.reset_index(drop=True), reread, check_dtype=False)
        artifacts[name] = sha(path)
    path = out / "decision_protocol_draft.json"
    path.write_text(json.dumps(draft, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == draft, "Protocol JSON readback")
    artifacts[path.name] = sha(path)
    reason_counts = Counter(
        reason for text in review.review_reasons_json for reason in json.loads(text)
    )
    result = {
        "status": "decision_sensitivity_readback_passed",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "case_variants": len(review),
        "distinct_membership_patterns": review.membership_sha256.nunique(),
        "review_overlap_families": len(families),
        "families_with_multiple_first_times": int(families.first_time_variants.gt(1).sum()),
        "families_with_multiple_first_grid_sets": int(families.first_grid_set_variants.gt(1).sum()),
        "families_with_multiple_target_windows": int(families.target_window_variants.gt(1).sum()),
        "families_with_split_merge_context": int(families.multiple_cases_in_one_scenario.sum()),
        "reason_counts_case_variants_nonexclusive": dict(sorted(reason_counts.items())),
        "review_order_group_counts": review.review_order_group.value_counts().to_dict(),
        "human_forms_not_reviewed": len(forms),
        "protocol_status": draft["status"],
        "scenario_selected": None,
        "event_identities_accepted": 0,
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "limits": [
            "Purposive cases; no population error rate or independent fire count",
            "Transitive detection overlap groups review cases, not physical events",
            "Only scenarios represented in this packet; absent comparisons are not agreement",
            "EFFIS is supporting context, not independent ground truth or UTC-resolved identity",
            "Review ordering is not an exclusion or label-admission decision",
        ],
    }
    require(all(sha(ROOT / name) == h for name, h in pins.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Report JSON readback")
    require(all(sha(out / name) == h for name, h in artifacts.items()), "Artifact closure")
    closure = {
        "status": "passed",
        "report_sha256": sha(path),
        "input_files_verified": len(pins),
        "artifacts_verified": len(artifacts),
    }
    (out / "completion_readback.json").write_text(
        json.dumps(closure, indent=2) + "\n", encoding="utf-8"
    )
    print("Event decision result:", out.relative_to(ROOT).as_posix())
    return out


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
