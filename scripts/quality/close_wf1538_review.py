"""Record the explicit WF1538 retention decision and account for the frozen ten-row work package."""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from prepare_marmaris_native_pair import write

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PARENT = BASE / "wf1538_membership_review_v1/20261119T183610Z_76a3a7bc/readback.json"
SUMMARY = BASE / "source_sample_native_summary_v1/20261119T175128Z_e277cfc3/readback.json"
PRIOR = BASE / "marmaris_L_proposal_v1/20261119T134021Z_5272c4bd/readback.json"
DECISION = ROOT / "configs/wf1538_review_retention_v1.json"
PINS = {
    PARENT: "8feb16a2fd70290bfb17c25ec50dd5a51eeab0d9377d4b9838a5252cf9436468",
    SUMMARY: "bf56b8ed36b6a12ac5c2e9c36f8ba7235013854a79cd0f93a4aaed8e3da107a0",
    PRIOR: "89d0305b9f5c54809e6c1170a30c21fe1a0230da4afc65720d5eef5bc8c5f476",
}


def main():
    require(
        all(digest(p) == h for p, h in PINS.items()), "Exact decision parent and previous proposals"
    )
    parent, summary, prior = [
        json.loads(p.read_text(encoding="utf-8")) for p in (PARENT, SUMMARY, PRIOR)
    ]
    require(
        parent["producer_sha256"]
        == digest(ROOT / "scripts/quality/prepare_wf1538_membership_review.py"),
        "Current parent code",
    )
    require(
        all(digest(ROOT / n) == h for n, h in parent["input_sha256"].items()),
        "Parent inputs and human notes",
    )
    decision = json.loads(DECISION.read_text(encoding="utf-8"))
    require(
        decision["decision_parent_sha256"] == PINS[PARENT]
        and decision["selected_option"] == "A_retain_review_unassigned"
        and decision["archive_row"] == "WF1538"
        and decision["new_L_memberships"] == 0
        and decision["source_row_deleted"] is False
        and decision["positive_label_permitted"] is False
        and decision["negative_label_permitted"] is False
        and decision["training_authorized"] is False
        and decision["final_merge_permitted"] is False,
        "Explicit bounded A decision",
    )
    require(
        all(digest(ROOT / n) == h for n, h in prior["input_sha256"].items()), "Prior L/U unchanged"
    )
    for name, h in prior["artifact_sha256"].items():
        require(digest(PRIOR.parent / name) == h, "Two-case review index unchanged")
    with (PRIOR.parent / "two_case_review_index.csv").open(encoding="utf-8", newline="") as f:
        prior_rows = list(csv.DictReader(f))
    require(
        len(prior_rows) == 2 and all(r["target"] == "" for r in prior_rows),
        "Previous proposals remain unlabelled",
    )
    rows = []
    for original in summary["source_rows"]:
        row = {
            "archive_row": original["archive_row"],
            "source_date": original["source_date"],
            "first_pair_review_status": original["review_status"],
            "followup_review_completed": original["archive_row"] == "WF1538",
            "human_cover_note_recorded_in_this_package": original["archive_row"] == "WF1538",
            "current_membership": "review_unassigned",
            "new_L_membership": False,
            "target": None,
        }
        rows.append(row)
    require(
        len(rows) == 10 and len({r["archive_row"] for r in rows}) == 10, "Frozen ten-row accounting"
    )
    require(
        summary["raw_reviewed_rows"] == 8
        and {
            r["archive_row"]
            for r in rows
            if not r["first_pair_review_status"].startswith("single_pair")
        }
        == {"WF1342", "WF1556"},
        "Two source metadata limitations retained",
    )
    out = (
        BASE
        / "wf1538_review_retention_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    with (out / "ten_row_review_status.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "status": "WF1538_retained_review_unassigned_by_explicit_researcher_decision",
        "decision": decision,
        "researcher_cover_notes": parent["researcher_cover_notes"],
        "measurement_work_package_status": (
            "eight_of_eight_planned_first_pairs_and_one_targeted_followup_reviewed"
        ),
        "frozen_source_rows_retained": 10,
        "source_rows_raw_reviewed": 8,
        "source_metadata_limit_rows_retained": ["WF1342", "WF1556"],
        "source_metadata_limits_resolved": False,
        "same_physical_fire_verified": False,
        "previous_possible_L_proposals_unchanged": 2,
        "U_sample_rows_unchanged": 2048,
        "U_sha256_unchanged": prior["U_sample_sha256_unchanged"],
        "new_L_memberships": 0,
        "verified_positive_labels_created": 0,
        "verified_negative_labels_created": 0,
        "overall_stage_one_accepted": False,
        "method_accepted": False,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {
            **{p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
            DECISION.relative_to(ROOT).as_posix(): digest(DECISION),
        },
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {"ten_row_review_status.csv": digest(out / "ten_row_review_status.csv")},
    }
    write(out / "readback.json", result)
    write(out / "completion_readback.json", {"report_sha256": digest(out / "readback.json")})
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))
    print("PASS explicit A retained; ten source rows and prior L/U unchanged")


if __name__ == "__main__":
    main()
