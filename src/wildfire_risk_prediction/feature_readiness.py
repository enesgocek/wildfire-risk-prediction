"""Read saved candidate values/provenance without selecting a scientific inclusion policy."""

import numpy as np

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_partition as parts
from wildfire_risk_prediction import landscape, weather_policy


def inspect_day(features, provenance, grid_ids, day, static):
    """Check stored past windows and source-aligned static values; count joint missingness.

    Acquisition time is checked, publication availability is deliberately still unknown.
    Complete cases and weather profiles are descriptions, never admitted training rows.
    """
    features, qa = parts.check_day(features, provenance, grid_ids, day)
    target = join.training_day(day)
    static = join.grid_rows(static, features.grid_id.tolist(), "retained static")
    for name in landscape.COVER_FEATURES + landscape.TERRAIN_FEATURES:
        np.testing.assert_allclose(features[name], static[name], rtol=0, atol=0, equal_nan=True)
    join.require(qa.static_reference_year.eq(2017).all(), "Static reference year")
    join.require(
        qa.static_historical_available_at.isna().all() and qa.weather_available_at.isna().all(),
        "Unknown publication availability must not be invented",
    )
    for name, hours in (
        ("weather_source_last_timestamp_utc", 1),
        ("weather_rain_interval_end_utc", 1),
        ("weather_source_window_start_utc", 24),
        ("weather_source_window_end_exclusive_utc", 0),
    ):
        join.require(join.utc_times(qa[name]).eq(join.past_hours(target, hours)).all(), name)
    join.require(
        qa.weather_source_collection.eq("ECMWF/ERA5_LAND/HOURLY").all()
        and qa.weather_policy_version.eq(weather_policy.VERSION).all()
        and qa.static_processing_version.eq(landscape.VERSION).all(),
        "Stored source versions",
    )
    for field in join.WEATHER_QA:
        if field not in ("weather_policy_version", "weather_min_valid_area_fraction"):
            join.boolean(qa[field], field)
    minimum = qa.weather_min_valid_area_fraction
    join.require(minimum.between(0, 1).all(), "Weather area fraction")
    complete_weather = features[weather_policy.MODEL_FEATURES].notna().all(axis=1)
    join.require(
        complete_weather.eq(~qa.weather_missing_any & ~qa.weather_large_negative_rain).all(),
        "Weather missingness flags disagree with stored model values",
    )
    for profile, threshold in (("primary", 1), ("sensitivity90", 0.9), ("observed", 0)):
        area = (
            minimum.gt(0)
            if threshold == 0
            else minimum.ge(threshold - weather_policy.AREA_TOLERANCE)
        )
        join.require(
            qa[f"weather_{profile}_eligible"].eq(complete_weather & area).all(),
            "Weather profile disagrees with values/coverage",
        )
    rain = [f"rain_{hours}h_nonnegative_mm" for hours in weather_policy.RAIN_HOURS]
    join.require((features[rain].isna() | features[rain].ge(0)).all().all(), "Negative rain")
    for window in join.WINDOWS:
        prefix = f"vegetation_{window}d_"
        present = qa[prefix + "vegetation_present"]
        join.boolean(present, prefix + "present")
        fields = [prefix + f for f in join.VEGETATION_FEATURES]
        values = features[fields]
        join.require(
            values[present].notna().all().all()
            and values[present].abs().le(1 + 1e-7).all().all()
            and values[~present].isna().all().all(),
            "Vegetation value/support disagreement",
        )
        cutoff = join.utc_times(qa[prefix + "snapshot_cutoff_utc"])
        start = join.utc_times(qa[prefix + "window_start_utc"])
        acquired = join.utc_times(qa[prefix + "source_acquisition_latest_utc"])
        age = (target - cutoff).dt.total_seconds() / 86400
        join.require(
            (
                cutoff[present].notna()
                & start[present].notna()
                & acquired[present].notna()
                & age[present].between(0, 8)
                & acquired[present].ge(start[present])
                & acquired[present].lt(cutoff[present])
                & (cutoff[present] - start[present]).dt.days.eq(window)
                & (cutoff[present] - start[present]).dt.total_seconds().eq(window * 86400)
            ).all(),
            "Vegetation strict past window",
        )
        np.testing.assert_allclose(
            qa.loc[present, prefix + "snapshot_age_days"], age[present], rtol=0, atol=1e-9
        )
        latest = qa[prefix + "latest_pixel_age_mean_days"]
        median = qa[prefix + "median_pixel_age_mean_days"]
        join.require(
            (
                latest[present].ge(age[present])
                & median[present].ge(latest[present])
                & median[present].le(window + age[present] + 1e-7)
            ).all(),
            "Vegetation pixel ages",
        )
        join.require(
            qa[prefix + "available_at"].isna().all()
            and qa[prefix + "selection_mode"].eq("retrospective").all()
            and qa[prefix + "series_version"].eq("vegetation_training_month_v1").all(),
            "Vegetation retrospective identity",
        )
        support = qa[prefix + "support_to_aoi_ratio"]
        join.require(
            (support[present].gt(0) & np.isfinite(support[present])).all(),
            "Vegetation area support",
        )
        absent_fields = [
            prefix + name
            for name in (
                "snapshot_cutoff_utc",
                "window_start_utc",
                "source_acquisition_latest_utc",
                "snapshot_age_days",
                "latest_pixel_age_mean_days",
                "median_pixel_age_mean_days",
                "support_to_aoi_ratio",
            )
        ]
        join.require(qa.loc[~present, absent_fields].isna().all().all(), "Absent support filled")
    families = {
        "weather": weather_policy.MODEL_FEATURES,
        "cover": landscape.COVER_FEATURES,
        "terrain": landscape.TERRAIN_FEATURES,
        "vegetation30": ["vegetation_30d_" + f for f in join.VEGETATION_FEATURES],
        "vegetation60": ["vegetation_60d_" + f for f in join.VEGETATION_FEATURES],
    }
    mask = np.zeros(len(features), dtype=np.uint8)
    for bit, fields in enumerate(families.values()):
        mask |= features[fields].isna().any(axis=1).to_numpy(np.uint8) << bit
    hist = np.bincount(mask, minlength=32)
    return {
        "day": day,
        "rows": len(features),
        "complete_27_feature_rows": int(hist[0]),
        "missing_by_feature": {f: int(features[f].isna().sum()) for f in join.feature_names()},
        "missing_family_bit_order": list(families),
        "joint_missing_family_counts": hist.tolist(),
        "weather_profile_counts": {
            p: int(qa[f"weather_{p}_eligible"].sum())
            for p in ("primary", "sensitivity90", "observed")
        },
        "publication_availability_verified": False,
        "eligible_labeled_rows": None,
    }
