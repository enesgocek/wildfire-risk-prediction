"""Complete training-month candidate features around the frozen daily partition format."""

import calendar
import json
import re
from pathlib import Path

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_partition as parts

VERSION = "training_feature_month_candidates_v1"
FALSE_FLAGS = (
    "model_ready",
    "labels_created",
    "final_test_accessed",
    "historical_availability_verified",
    "habitat_eligibility_decided",
    "negative_label_permitted",
    "qa_columns_are_model_inputs",
)


def calendar_days(month):
    join.require(isinstance(month, str) and re.fullmatch(r"\d{4}-\d{2}", month), "Month format")
    first = join.training_day(month + "-01")
    return [
        f"{month}-{d:02}" for d in range(1, calendar.monthrange(first.year, first.month)[1] + 1)
    ]


def write_month(folder, days, grid_ids, month):
    """Require an ordered complete calendar; incomplete output never has a month manifest.

    Only candidate features are accepted here. Scientific labels and historical source
    availability require separate decisions. Existing sources and destinations are untouched.
    """
    expected = calendar_days(month)
    ids, grid_sha = parts.grid_identity(grid_ids)
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)

    def checked_days():
        seen = 0
        for day, features, provenance in days:
            join.require(
                seen < len(expected) and day == expected[seen], "Complete ordered calendar"
            )
            seen += 1
            yield day, features, provenance
        join.require(seen == len(expected), "Incomplete month calendar")

    part_sha = parts.write_pilot(folder / "parts", checked_days(), ids)
    manifest = {
        "version": VERSION,
        "scope": "complete_training_month_candidates_only",
        "month": month,
        "split": "train",
        "days": expected,
        "grid_count": len(ids),
        "grid_identity_sha256": grid_sha,
        "rows": len(ids) * len(expected),
        "parts_manifest_sha256": part_sha,
        "daily_observation_status": "unknown",
        **dict.fromkeys(FALSE_FLAGS, False),
    }
    data = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    (folder / "month_manifest.json").write_bytes(data)
    return parts.digest(data)


def iter_month(folder, *, expected_manifest_sha256, grid_ids):
    """Check both calendar manifests before reading any CSV; then stream one checked day."""
    folder = Path(folder).resolve()
    ids, grid_sha = parts.grid_identity(grid_ids)
    path = folder / "month_manifest.json"
    join.require(not path.is_symlink(), "Month manifest symlink")
    data = path.read_bytes()
    join.require(
        isinstance(expected_manifest_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", expected_manifest_sha256)
        and parts.digest(data) == expected_manifest_sha256,
        "Month manifest identity",
    )
    manifest = json.loads(data)
    days = calendar_days(manifest["month"])
    join.require(
        manifest["version"] == VERSION
        and manifest["scope"] == "complete_training_month_candidates_only"
        and manifest["split"] == "train"
        and manifest["daily_observation_status"] == "unknown"
        and all(manifest[f] is False for f in FALSE_FLAGS),
        "Month scope/acceptance changed",
    )
    join.require(
        manifest["days"] == days
        and manifest["rows"] == len(days) * len(ids)
        and manifest["grid_count"] == len(ids)
        and manifest["grid_identity_sha256"] == grid_sha,
        "Month calendar/grid inventory",
    )
    part_folder = folder / "parts"
    part_path = part_folder / "manifest.json"
    join.require(not part_folder.is_symlink() and not part_path.is_symlink(), "Parts symlink")
    data = part_path.read_bytes()
    join.require(parts.digest(data) == manifest["parts_manifest_sha256"], "Parts manifest identity")
    part_manifest = json.loads(data)
    join.require(
        [e["day"] for e in part_manifest["days"]] == days
        and part_manifest["rows"] == manifest["rows"],
        "Parts complete month calendar",
    )
    yield from parts.iter_pilot(
        part_folder, expected_manifest_sha256=manifest["parts_manifest_sha256"], grid_ids=ids
    )
