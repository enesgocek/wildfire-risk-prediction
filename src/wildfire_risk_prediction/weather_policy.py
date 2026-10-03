"""Versioned retrospective weather baseline; no fitting, labels or imputation."""

import numpy as np
import pandas as pd

VERSION = "weather_model_v1"
AREA_TOLERANCE = 1e-9
NEGATIVE_RAIN_TOLERANCE_MM = 0.0001  # Project QC bound, not an ECMWF standard.
PHYSICAL_FEATURES = [
    "temperature_mean_c",
    "temperature_min_c",
    "temperature_max_c",
    "dewpoint_mean_c",
    "wind_speed_mean_ms",
    "wind_speed_max_ms",
    "soil_water_layer_1_mean",
]
RAIN_HOURS = [24, 72, 168, 336]
RAW_FEATURES = (
    PHYSICAL_FEATURES
    + [f"rain_{h}h_raw_mm" for h in RAIN_HOURS]
    + [
        "rain_negative_hours_24h_mean",
        "rain_negative_hours_336h_mean",
    ]
)
MODEL_FEATURES = PHYSICAL_FEATURES + [f"rain_{h}h_nonnegative_mm" for h in RAIN_HOURS]


def specification():
    return {
        "version": VERSION,
        "primary_minimum_valid_area_fraction": 1.0,
        "sensitivity_minimum_valid_area_fraction": 0.9,
        "area_numerical_tolerance": AREA_TOLERANCE,
        "negative_rain_tolerance_mm": NEGATIVE_RAIN_TOLERANCE_MM,
        "rain_method": (
            "Floor only aggregate sums in [-tolerance,0) to zero; larger negatives "
            "become NaN with a QC flag. Positive sums unchanged. Not hourly correction."
        ),
        "missing_policy": "Preserve NaN, retain all rows; no neighbour fill or imputation.",
        "model_features": MODEL_FEATURES,
        "qa_features_are_model_inputs": False,
        "usage": "retrospective_reanalysis_only",
        "eligibility_is_not_fire_label_or_landcover_suitability": True,
        "final_test_accessed": False,
    }


def transform(frame):
    """Retain observations; attach derived rainfall and experiment eligibility."""
    required = (
        RAW_FEATURES
        + [f + "_valid_area_fraction" for f in RAW_FEATURES]
        + [
            "grid_id",
            "prediction_timestamp_utc",
            "source_last_timestamp_utc",
            "available_at",
            "source_collection",
            "processing_version",
        ]
    )
    absent = set(required) - set(frame.columns)
    if absent or frame.empty:
        raise ValueError(f"Missing weather schema or empty input: {sorted(absent)}")
    timestamp = pd.to_datetime(frame.prediction_timestamp_utc, utc=True, errors="raise")
    last = pd.to_datetime(frame.source_last_timestamp_utc, utc=True, errors="raise")
    # Explicit nanoseconds also avoid pandas/NumPy generic timedelta coercion.
    time_ns = timestamp.dt.as_unit("ns").astype("int64")
    last_ns = last.dt.as_unit("ns").astype("int64")
    if not (
        timestamp.ge(pd.Timestamp("2018-01-01", tz="UTC")).all()
        and timestamp.lt(pd.Timestamp("2025-01-01", tz="UTC")).all()
        and timestamp.eq(timestamp.dt.normalize()).all()
        and last_ns.eq(time_ns - 3_600_000_000_000).all()
        and frame.available_at.isna().all()
        and frame.source_collection.eq("ECMWF/ERA5_LAND/HOURLY").all()
        and frame.processing_version.eq("era5_land_past_v1").all()
        and frame.grid_id.notna().all()
        and pd.MultiIndex.from_arrays([frame.grid_id, timestamp]).is_unique
    ):
        raise ValueError("Weather source/time/key contract violation; 2025 is sealed.")
    for feature in RAW_FEATURES:
        values = frame[feature]
        fraction = frame[feature + "_valid_area_fraction"]
        if not (
            fraction.between(0, 1).all()
            and np.isfinite(values.dropna()).all()
            and values.isna().eq(fraction.eq(0)).all()
        ):
            raise ValueError(f"Invalid value or missingness/coverage: {feature}")
    result = frame.copy()
    fractions = result[[f + "_valid_area_fraction" for f in RAW_FEATURES]]
    result["weather_min_valid_area_fraction"] = fractions.min(axis=1)
    result["weather_missing_any"] = result[RAW_FEATURES].isna().any(axis=1)
    result["weather_partial_area"] = (
        ~result.weather_missing_any & result.weather_min_valid_area_fraction.lt(1 - AREA_TOLERANCE)
    )
    severe = pd.Series(False, index=frame.index)
    for hours in RAIN_HOURS:
        raw = frame[f"rain_{hours}h_raw_mm"]
        small = raw.lt(0) & raw.ge(-NEGATIVE_RAIN_TOLERANCE_MM)
        bad = raw.lt(-NEGATIVE_RAIN_TOLERANCE_MM)
        result[f"rain_{hours}h_nonnegative_mm"] = raw.mask(small, 0.0).mask(bad)
        result[f"rain_{hours}h_roundoff_clipped"] = small
        severe |= bad
    result["weather_large_negative_rain"] = severe
    complete = ~result.weather_missing_any & ~severe
    minimum = result.weather_min_valid_area_fraction
    result["weather_primary_eligible"] = complete & minimum.ge(1 - AREA_TOLERANCE)
    result["weather_sensitivity90_eligible"] = complete & minimum.ge(0.9 - AREA_TOLERANCE)
    result["weather_observed_eligible"] = complete & minimum.gt(0)
    result["weather_policy_version"] = VERSION
    return result


def counts(frame):
    names = [
        "weather_missing_any",
        "weather_partial_area",
        "weather_large_negative_rain",
        "weather_primary_eligible",
        "weather_sensitivity90_eligible",
        "weather_observed_eligible",
    ] + [f"rain_{h}h_roundoff_clipped" for h in RAIN_HOURS]
    return {"rows": len(frame), **{name: int(frame[name].sum()) for name in names}}
