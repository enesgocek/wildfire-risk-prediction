"""Training-only candidate batch planning; source references are distinct from byte acceptance."""

import calendar
import re
from pathlib import PurePosixPath

from wildfire_risk_prediction import dataset_contract as contract
from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_month

VERSION = "training_candidate_batch_plan_v1"
INDEX_VERSION = "training_candidate_batch_result_v1"
GRID_COUNT = 2899


def digest_value(value):
    join.require(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "SHA-256 identity"
    )
    return value


def public_path(value, prefix):
    join.require(isinstance(value, str) and "\\" not in value, "Relative POSIX source path")
    path = PurePosixPath(value)
    join.require(
        not path.is_absolute()
        and ".." not in path.parts
        and value.startswith(prefix)
        and ":" not in value
        and path.suffix == ".json",
        "Public report path",
    )
    return value


def calendar_inventory(split="train"):
    join.require(split in {"train", "validation"}, "Final test calendar not opened here")
    years = range(2018, 2024) if split == "train" else [2024]
    entries = []
    for year in years:
        for m in range(1, 13):
            days = calendar.monthrange(year, m)[1]
            entries.append(
                {
                    "month": f"{year}-{m:02}",
                    "split": split,
                    "calendar_days": days,
                    "candidate_rows_before_exclusions": GRID_COUNT * days,
                    "vegetation_long_rows": GRID_COUNT * days * 2,
                }
            )
    return entries


def vegetation_reference(entry):
    month = entry["month"]
    days = feature_month.calendar_days(month)
    prefix = f"outputs/reports/landscape/month_v1/{month}/"
    path = public_path(entry["readback"], prefix)
    join.require(
        PurePosixPath(path).parent.as_posix() == prefix.rstrip("/"), "Month readback parent"
    )
    join.require(entry["daily_rows"] == GRID_COUNT * len(days) * 2, "Vegetation calendar rows")
    return {
        "readback": path,
        "readback_sha256": digest_value(entry["readback_sha256"]),
        "manifest_sha256": digest_value(entry["manifest_sha256"]),
        "daily_table_sha256": digest_value(entry["daily_table_sha256"]),
        "daily_rows": entry["daily_rows"],
        "table_bytes_verified_by_this_plan": False,
    }


def candidate_reference(entry):
    month = entry["month"]
    days = feature_month.calendar_days(month)
    join.require(entry["rows"] == len(days) * GRID_COUNT, "Candidate calendar rows")
    path = public_path(entry["path"], "outputs/reports/dataset/feature_month_v1/")
    join.require(PurePosixPath(path).name == "readback.json", "Candidate report name")
    return {
        "month": month,
        "path": path,
        "sha256": digest_value(entry["sha256"]),
        "rows": entry["rows"],
        "manifest_sha256": digest_value(entry["manifest_sha256"]),
    }


def build_plan(source_entries, candidate_entries, code_sha256):
    sources, candidates = {}, {}
    for entry in source_entries:
        month = entry["month"]
        join.require(month not in sources, "Duplicate source month")
        sources[month] = vegetation_reference(entry)
    for entry in candidate_entries:
        ref = candidate_reference(entry)
        join.require(ref["month"] not in candidates, "Duplicate candidate month")
        candidates[ref["month"]] = ref
    join.require(code_sha256, "Explicit batch method identities")
    for name, digest in code_sha256.items():
        join.require(
            name.startswith(("src/", "scripts/")) and ".." not in PurePosixPath(name).parts,
            "Method path",
        )
        digest_value(digest)
    entries = []
    for expected in calendar_inventory():
        month = expected["month"]
        source, candidate = sources.get(month), candidates.get(month)
        entries.append(
            {
                **expected,
                "vegetation_source_reference": source,
                "candidate_readback_reference": candidate,
                "action": "verify_existing_candidate"
                if candidate
                else ("build_from_pinned_sources" if source else "await_source_reference"),
            }
        )
    return {
        "version": VERSION,
        "contract_version": contract.VERSION,
        "scope": "training_candidate_features_only",
        "split": "train",
        "grid_count": GRID_COUNT,
        "entries": entries,
        "expected_calendar_days": sum(e["calendar_days"] for e in entries),
        "expected_candidate_rows_before_exclusions": sum(
            e["candidate_rows_before_exclusions"] for e in entries
        ),
        "source_reference_months": len(sources),
        "candidate_reference_months": len(candidates),
        "code_sha256": code_sha256,
        "validation_preparation": {
            "entries": calendar_inventory("validation"),
            "status": "separate_validation_source_preparation_required",
            "executable_by_this_training_batch": False,
        },
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "final_test_accessed": False,
        "release_blockers": contract.release_blockers(),
    }


def validate_plan(plan):
    """Reconstruct the strict plan; caller-supplied approval flags cannot relax it."""
    sources, candidates = [], []
    for entry in plan["entries"]:
        feature_month.calendar_days(entry["month"])
        if source := entry["vegetation_source_reference"]:
            sources.append({"month": entry["month"], **source})
        if candidate := entry["candidate_readback_reference"]:
            candidates.append(candidate)
    expected = build_plan(sources, candidates, plan["code_sha256"])
    join.require(plan == expected, "Batch calendar/schema/acceptance drift")
    return plan


def candidate_inventory(references):
    validated = [candidate_reference(e) for e in references]
    months = [e["month"] for e in validated]
    join.require(len(months) == len(set(months)), "Duplicate index month")
    missing = [e["month"] for e in calendar_inventory() if e["month"] not in months]
    return {
        "verified_candidate_months": len(months),
        "missing_candidate_months": missing,
        "candidate_calendar_complete": not missing,
        "verified_candidate_rows": sum(e["rows"] for e in validated),
        "labels_created": False,
        "model_ready": False,
        "final_test_accessed": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "release_blockers": contract.release_blockers(),
        "validation_ready": False,
    }


def delivery_inventory(plan, observation_log_months):
    """Separate source references, joined candidates and satellite log-only evidence."""
    validate_plan(plan)
    join.require(
        observation_log_months == sorted(set(observation_log_months)),
        "Ordered unique satellite log months",
    )
    for month in observation_log_months:
        feature_month.calendar_days(month)
    return {
        "scope": "training_delivery_reference_inventory_only",
        "entries": [
            {
                "month": e["month"],
                "calendar_days": e["calendar_days"],
                "weather_reference": "accepted_past_weather_calendar_metadata",
                "static_reference": "accepted_static_manifest_metadata",
                "vegetation_reference_present": e["vegetation_source_reference"] is not None,
                "joined_candidate_reference_present": e["candidate_readback_reference"] is not None,
                "satellite_evidence": (
                    "log_catalogue_complete_only"
                    if e["month"] in observation_log_months
                    else "not_registered_as_complete_in_selected_log_readback"
                ),
                "satellite_payload_bytes_verified_by_this_check": False,
                "daily_observation_status": "unknown",
                "binary_label_ready": False,
            }
            for e in plan["entries"]
        ],
        "counts": {
            "training_calendar_months": 72,
            "vegetation_source_reference_months": plan["source_reference_months"],
            "joined_candidate_reference_months": plan["candidate_reference_months"],
            "satellite_log_catalogue_months": len(observation_log_months),
            "binary_label_months_admitted": 0,
        },
        "validation": {
            "calendar_months": 12,
            "weather_calendar_metadata_prepared": True,
            "vegetation_and_satellite": "separate_validation_preparation_and_acceptance_required",
            "validation_feature_files_read": False,
        },
        "final_test_accessed": False,
        "labels_created": False,
        "model_ready": False,
        "release_blockers": contract.release_blockers(),
    }
