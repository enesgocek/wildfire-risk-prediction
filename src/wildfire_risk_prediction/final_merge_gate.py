"""Future final assembly must require a fresh, hash-bound user approval receipt."""

import hashlib
import json
import re
from datetime import datetime, timedelta

PARTS = ("weather", "landscape", "vegetation", "observation", "targets")


def review_digest(review):
    return hashlib.sha256(
        json.dumps(review, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def require_final_merge_approval(review, approval):
    """Programming guard, not authentication or an independent scientific acceptance."""
    if not isinstance(review, dict) or not isinstance(approval, dict):
        raise PermissionError("Final merge review and explicit user approval are required")
    if (
        review.get("status") != "all_parts_final_review_passed"
        or review.get("scientific_protocol_status") != "accepted"
        or review.get("split") != "train_2018_2023"
        or review.get("final_test_accessed") is not False
        or set(review.get("parts", {})) != set(PARTS)
    ):
        raise PermissionError("Final part/scientific review is incomplete")
    for part in review["parts"].values():
        if (
            not isinstance(part, dict)
            or part.get("status") != "passed"
            or not isinstance(part.get("manifest_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", part["manifest_sha256"])
        ):
            raise PermissionError("Every final part needs a passing review and manifest hash")
    if (
        approval.get("decision") != "approve_final_merge"
        or approval.get("approved_by") != "user"
        or approval.get("source") != "explicit_user_message"
        or approval.get("review_sha256") != review_digest(review)
    ):
        raise PermissionError("Explicit user approval must match this exact final review")
    try:
        stamp = datetime.fromisoformat(approval["approved_at_utc"].replace("Z", "+00:00"))
        if stamp.utcoffset() != timedelta(0):
            raise ValueError("Explicit UTC approval time")
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise PermissionError("A recorded UTC user approval time is required") from exc
    return True
