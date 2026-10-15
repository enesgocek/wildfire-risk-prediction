"""Check reference matching readiness; a missing incident never becomes a negative label."""

import re

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import require, training_day, utc_times


def turkish_area(value):
    require(
        isinstance(value, str) and bool(re.fullmatch(r"\d{1,3}(?:\.\d{3})*,\d+|\d+,\d+", value)),
        "Explicit Turkish area format",
    )
    result = float(value.replace(".", "").replace(",", "."))
    require(np.isfinite(result) and result > 0, "Positive reported burned area")
    return result


def matching_readiness(row, source):
    """Only documented point/time/lineage can support later event matching review."""
    require(row["source_id"] == source["source_id"], "Exact reference source")
    training_day(row["reported_date"])
    require(row.get("target") is None, "Reference import never assigns a training target")
    reasons = []
    if source["lineage_status"] != "documented_independent_incident_record":
        reasons.append("independent_incident_lineage_not_established")
    if source["access_status"] != "local_event_records_verified":
        reasons.append("event_record_access_not_verified")
    lon, lat = row.get("longitude"), row.get("latitude")
    require((lon is None) == (lat is None), "Both coordinates or neither")
    if lon is None:
        reasons.append("origin_coordinates_missing")
    else:
        require(
            np.isfinite([lon, lat]).all() and abs(lon) <= 180 and abs(lat) <= 90, "Coordinate range"
        )
    if row.get("location_kind") != "reported_origin_point":
        reasons.append("origin_point_not_documented")
    uncertainty = row.get("location_uncertainty_m")
    if uncertainty is None:
        reasons.append("location_uncertainty_unknown")
    else:
        require(np.isfinite(uncertainty) and uncertainty >= 0, "Location uncertainty")
    lower, upper = row.get("event_time_lower_utc"), row.get("event_time_upper_utc")
    require((lower is None) == (upper is None), "Both time bounds or neither")
    if lower is None:
        reasons.append("explicit_utc_time_bounds_missing")
    else:
        times = utc_times(pd.Series([lower, upper]))
        require(
            times.iloc[0] <= times.iloc[1] and times.dt.year.between(2018, 2023).all(),
            "Ordered training time bounds",
        )
    if row.get("time_semantics") not in {"first_alert", "reported_outbreak", "estimated_ignition"}:
        reasons.append("incident_time_semantics_not_documented")
    return {
        "reference_id": row["reference_id"],
        "source_id": row["source_id"],
        "can_review_exact_grid_time_match": not reasons,
        "unresolved_requirements": reasons,
        "first_satellite_detection_time_proven": False,
        "supports_negative_label": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "target": None,
        "daily_observation_status": "unknown",
    }
