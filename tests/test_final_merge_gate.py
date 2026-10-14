"""Approval is tied to the complete final review, not a general wish to proceed."""

import copy

import pytest

from wildfire_risk_prediction.final_merge_gate import (
    PARTS,
    require_final_merge_approval,
    review_digest,
)


def synthetic_receipts():
    review = {
        "status": "all_parts_final_review_passed",
        "scientific_protocol_status": "accepted",
        "split": "train_2018_2023",
        "final_test_accessed": False,
        "parts": {p: {"status": "passed", "manifest_sha256": "a" * 64} for p in PARTS},
    }
    approval = {
        "decision": "approve_final_merge",
        "approved_by": "user",
        "source": "explicit_user_message",
        "review_sha256": review_digest(review),
        "approved_at_utc": "2026-10-14T12:00:00Z",
    }
    return review, approval


def test_missing_approval_rejected_and_synthetic_matching_receipt_passes():
    review, approval = synthetic_receipts()
    for a, b in ((None, None), (review, None), (None, approval)):
        with pytest.raises(PermissionError):
            require_final_merge_approval(a, b)
    assert require_final_merge_approval(review, approval)
    assert review_digest(dict(reversed(list(review.items())))) == review_digest(review)


@pytest.mark.parametrize(
    "problem",
    [
        "changed_part",
        "failed_part",
        "missing_part",
        "bad_hash",
        "science_open",
        "wrong_split",
        "auto_approval",
        "wrong_intent",
        "missing_time",
        "non_utc",
        "final_open",
    ],
)
def test_stale_incomplete_or_unauthorized_receipts_fail(problem):
    review, approval = synthetic_receipts()
    original = copy.deepcopy(review)
    if problem == "changed_part":
        review["parts"]["weather"]["manifest_sha256"] = "b" * 64
    elif problem == "failed_part":
        review["parts"]["targets"]["status"] = "failed"
    elif problem == "missing_part":
        review["parts"].pop("landscape")
    elif problem == "bad_hash":
        review["parts"]["vegetation"]["manifest_sha256"] = "not-a-hash"
    elif problem == "science_open":
        review["scientific_protocol_status"] = "unaccepted"
    elif problem == "wrong_split":
        review["split"] = "final_test_2025"
    elif problem == "auto_approval":
        approval["source"] = "automated_check"
    elif problem == "wrong_intent":
        approval["decision"] = "continue_preparation"
    elif problem == "missing_time":
        approval.pop("approved_at_utc")
    elif problem == "non_utc":
        approval["approved_at_utc"] = "2026-10-14T12:00:00"
    else:
        review["final_test_accessed"] = True
    with pytest.raises(PermissionError):
        require_final_merge_approval(review, approval)
    assert original["parts"]["weather"]["manifest_sha256"] == "a" * 64
