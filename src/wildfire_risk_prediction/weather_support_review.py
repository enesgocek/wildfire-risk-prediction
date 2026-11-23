"""Reconcile frozen model-input completeness with pre-existing weather QA profiles."""

import numpy as np
import pandas as pd

from . import weather_policy
from .feature_join import KEYS, require
from .ranking_queries import DYNAMIC_FEATURES

PROFILES = {
    "primary_full_area": "weather_primary_eligible",
    "sensitivity_90_area": "weather_sensitivity90_eligible",
    "observed_positive_area": "weather_observed_eligible",
}


def inspect(features, provenance):
    pd.testing.assert_frame_equal(features[KEYS], provenance[KEYS], check_exact=True)
    require(not features.duplicated(KEYS).any(), "Unique diagnostic keys")
    require(
        provenance.weather_policy_version.eq(weather_policy.VERSION).all(),
        "Existing weather policy",
    )
    dates = pd.to_datetime(features.prediction_timestamp_utc, utc=True, format="ISO8601")
    require(dates.dt.year.between(2018, 2022).all(), "Only already opened pilot years")
    fraction = provenance.weather_min_valid_area_fraction
    require(fraction.between(0, 1).all(), "Valid source area coverage")
    complete_source = ~provenance.weather_missing_any & ~provenance.weather_large_negative_rain
    expected = {
        "primary_full_area": complete_source & fraction.ge(1 - weather_policy.AREA_TOLERANCE),
        "sensitivity_90_area": complete_source & fraction.ge(0.9 - weather_policy.AREA_TOLERANCE),
        "observed_positive_area": complete_source & fraction.gt(0),
    }
    result = features[KEYS].copy()
    result["dynamic_15_complete"] = np.isfinite(
        features[DYNAMIC_FEATURES].to_numpy(dtype=float)
    ).all(axis=1)
    result["weather_11_complete"] = np.isfinite(
        features[weather_policy.MODEL_FEATURES].to_numpy(dtype=float)
    ).all(axis=1)
    result["weather_min_valid_area_fraction"] = fraction
    for profile, column in PROFILES.items():
        require(
            provenance[column].dtype == bool and provenance[column].eq(expected[profile]).all(),
            "Stored profile agrees with fixed source QA rule",
        )
        result[profile] = provenance[column]
        result[profile + "_and_dynamic_15_complete"] = (
            provenance[column] & result.dynamic_15_complete
        )
    result["weather_no_valid_area_support"] = (
        ~result.weather_11_complete & fraction.eq(0) & provenance.weather_missing_any
    )
    result["weather_missing_other_reason_requires_review"] = (
        ~result.weather_11_complete & ~result.weather_no_valid_area_support
    )
    result["weather_finite_but_partial_area"] = (
        result.weather_11_complete & provenance.weather_partial_area
    )
    for window in (30, 60):
        fields = [f"vegetation_{window}d_{v}_median_mean" for v in ("ndvi", "ndmi")]
        missing = features[fields].isna().any(axis=1)
        present = provenance[f"vegetation_{window}d_vegetation_present"]
        require(present.dtype == bool, "Explicit retained-snapshot presence flag")
        result[f"vegetation_{window}d_missing"] = missing
        result[f"vegetation_{window}d_snapshot_absent"] = missing & ~present
        result[f"vegetation_{window}d_present_but_missing_requires_review"] = missing & present
    return result
