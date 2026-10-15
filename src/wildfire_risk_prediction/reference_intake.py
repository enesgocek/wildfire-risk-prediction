"""Conservative, value-free diagnostics for normalized training reference records."""

import re
from collections import Counter
from datetime import time

import numpy as np

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.reference_readiness import matching_readiness

FIELDS = (
    "reference_id",
    "source_id",
    "source_record_id",
    "reported_date",
    "reported_clock_local",
    "time_semantics",
    "time_standard",
    "event_time_lower_utc",
    "event_time_upper_utc",
    "reported_province",
    "reported_district",
    "location_kind",
    "longitude",
    "latitude",
    "source_crs",
    "location_uncertainty_m",
    "record_origin",
    "source_document_sha256",
    "use_terms",
)
PROVINCES = {"Antalya", "Muğla", "İzmir", "Mersin"}
REVIEW_FLAGS = (
    "use_terms_reviewed",
    "independence_reviewed",
    "record_access_reviewed",
    "coordinate_reference_reviewed",
    "time_definition_reviewed",
)


class RecordError(ValueError):
    """A fixed reason code only; never expose original input values."""


def text_cell(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if not isinstance(value, str) or len(value) > 4096:
        raise RecordError("non_text_or_oversized_cell")
    return value.strip() or None


def number_cell(value):
    if value is None:
        return None
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", value):
        raise RecordError("invalid_explicit_decimal")
    result = float(value)
    if not np.isfinite(result):
        raise RecordError("nonfinite_numeric_value")
    return result


def record_issues(row, source, evidence):
    """Check readiness only; documented source reviews cannot prove a negative label."""
    issues = []
    for field in ("reference_id", "source_id", "source_record_id"):
        if row[field] is None:
            issues.append(f"missing_{field}")
    if source is None:
        issues.append("source_not_in_inventory")
    if row["reported_province"] not in PROVINCES:
        issues.append("province_missing_or_outside_requested_scope")
    if row["record_origin"] is None:
        issues.append("record_origin_missing")
    sha = row["source_document_sha256"]
    if sha is None:
        issues.append("source_document_missing")
    elif not re.fullmatch(r"[a-f0-9]{64}", sha):
        raise RecordError("invalid_source_document_hash")
    elif sha not in evidence.get("verified_document_sha256", []):
        issues.append("source_document_not_locally_verified")
    if row["use_terms"] is None:
        issues.append("use_terms_missing")
    for flag in REVIEW_FLAGS:
        if evidence.get(flag) is not True:
            issues.append(flag + "_pending")
    if row["source_crs"] != "EPSG:4326":
        issues.append("explicit_longitude_latitude_crs_not_ready")
    if row["time_standard"] is None:
        issues.append("source_time_standard_missing")
    clock = row["reported_clock_local"]
    if clock is not None:
        if not re.fullmatch(r"\d{2}:\d{2}(?::\d{2})?", clock):
            raise RecordError("invalid_reported_clock")
        try:
            time.fromisoformat(clock)
        except ValueError:
            raise RecordError("invalid_reported_clock") from None
    numeric = {k: number_cell(row[k]) for k in ("longitude", "latitude", "location_uncertainty_m")}
    lon, lat = numeric["longitude"], numeric["latitude"]
    if (lon is None) != (lat is None):
        raise RecordError("partial_coordinates")
    if lon is not None and row["source_crs"] != "EPSG:4326":
        # Other coordinate systems require an explicit, separately reviewed conversion.
        # Do not interpret easting/northing as longitude/latitude.
        numeric["longitude"] = numeric["latitude"] = None
    if source is not None:
        try:
            decision = matching_readiness({**row, **numeric, "target": None}, source)
        except (ValueError, TypeError, OverflowError):
            raise RecordError("invalid_date_time_coordinates_or_training_scope") from None
        issues.extend(decision["unresolved_requirements"])
    else:
        # Validate training/time/coordinate syntax even when inventory lookup failed.
        try:
            matching_readiness(
                {**row, **numeric, "target": None},
                {
                    "source_id": row["source_id"],
                    "lineage_status": "unverified",
                    "access_status": "unverified",
                },
            )
        except (ValueError, TypeError, OverflowError):
            raise RecordError("invalid_date_time_coordinates_or_training_scope") from None
    return sorted(set(issues))


def audit_intake(frame, sources, evidence_by_source):
    """All cells are strings/empty, as read by dtype=str and keep_default_na=False.

    Accept only the normalized allowlist, never arbitrary incoming spreadsheets.
    Return row numbers and fixed codes, not names, coordinates, IDs or free text.
    """
    require(
        frame.columns.is_unique and set(frame.columns) == set(FIELDS),
        "Exact normalized incident columns required; inspect provider files separately",
    )
    for key, evidence in evidence_by_source.items():
        require(key in sources, "Source evidence inventory identity")
        for flag in REVIEW_FLAGS:
            require(type(evidence.get(flag, False)) is bool, "Explicit source review booleans")
        hashes = evidence.get("verified_document_sha256", [])
        require(
            isinstance(hashes, list)
            and all(isinstance(h, str) and re.fullmatch(r"[a-f0-9]{64}", h) for h in hashes),
            "Verified document hash inventory",
        )
    for key, source in sources.items():
        require(
            source.get("source_id") == key
            and all(
                isinstance(source.get(k), str) and source[k]
                for k in ("lineage_status", "access_status")
            ),
            "Complete source inventory identity and review state",
        )
    cleaned = []
    for values in frame[list(FIELDS)].to_dict("records"):
        try:
            cleaned.append({k: text_cell(v) for k, v in values.items()})
        except RecordError:
            cleaned.append(None)
    references = Counter(r["reference_id"] for r in cleaned if r and r["reference_id"])
    identities = Counter(
        (r["source_id"], r["source_record_id"])
        for r in cleaned
        if r and r["source_id"] and r["source_record_id"]
    )
    result = []
    for index, row in enumerate(cleaned, 1):
        status = "needs_source_review"
        if row is None:
            codes, status = ["non_text_or_oversized_cell"], "invalid_record"
        else:
            duplicate = []
            if row["reference_id"] and references[row["reference_id"]] > 1:
                duplicate.append("duplicate_reference_id")
            if (
                row["source_id"]
                and row["source_record_id"]
                and identities[row["source_id"], row["source_record_id"]] > 1
            ):
                duplicate.append("duplicate_source_record_id")
            try:
                codes = record_issues(
                    row, sources.get(row["source_id"]), evidence_by_source.get(row["source_id"], {})
                )
            except RecordError as error:
                codes, status = [str(error)], "invalid_record"
            codes = sorted(set(codes + duplicate))
            if duplicate:
                status = "invalid_record"
            elif not codes:
                status = "ready_for_matching_review_only"
        result.append(
            {
                "input_record_number": index,
                "row_status": status,
                "reason_codes": codes,
                "can_review_matching": status == "ready_for_matching_review_only",
                "target": None,
                "daily_observation_status": "unknown",
                "positive_label_permitted": False,
                "negative_label_permitted": False,
                "supports_absence_inference": False,
            }
        )
    return result
