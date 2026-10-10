"""One training day's retrospective features; no targets, fitting or operational claim."""

import re

import numpy as np
import pandas as pd

from wildfire_risk_prediction import landscape, weather_policy
from wildfire_risk_prediction import vegetation as vegetation_policy

VERSION = "retrospective_feature_join_v1"
HOUR_NS = 3_600_000_000_000
KEYS = ["grid_id", "prediction_timestamp_utc"]
WINDOWS = (30, 60)
VEGETATION_FEATURES = ["ndvi_median_mean", "ndmi_median_mean"]
WEATHER_QA = [
    "weather_min_valid_area_fraction",
    "weather_missing_any",
    "weather_partial_area",
    "weather_large_negative_rain",
    "weather_primary_eligible",
    "weather_sensitivity90_eligible",
    "weather_observed_eligible",
    "weather_policy_version",
]
STATIC_QA = [
    "reference_year",
    "terrain_valid_area_m2",
    "aspect_valid_area_m2",
    "aoi_area_m2",
    "terrain_support_to_aoi_ratio",
    "terrain_support_close_to_aoi",
    "historical_available_at",
    "processing_version",
    "landcover_suitability_decided",
]
VEGETATION_QA = [
    "vegetation_present",
    "snapshot_cutoff_utc",
    "snapshot_age_days",
    "window_start_utc",
    "source_acquisition_latest_utc",
    "latest_pixel_age_mean_days",
    "median_pixel_age_mean_days",
    "support_to_aoi_ratio",
    "available_at",
    "processing_version",
    "source_batch",
    "snapshot_manifest_sha256",
    "selection_mode",
    "series_version",
]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def training_day(value):
    """Guard before source paths/reads; this pilot deliberately covers training only."""
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), "Day format")
    day = pd.Timestamp(value, tz="UTC")
    require(2018 <= day.year <= 2023, "Training only; validation/final test sealed here")
    return day


def utc_times(values):
    present = values.dropna()
    require(
        present.map(
            lambda s: (
                isinstance(s, str)
                and bool(
                    re.fullmatch(
                        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|\+00:00)", s
                    )
                )
            )
        ).all(),
        "Explicit UTC ISO timestamps required",
    )
    return pd.to_datetime(values, format="ISO8601", utc=True, errors="raise").dt.as_unit("ns")


def boolean(values, name):
    require(values.map(lambda x: isinstance(x, (bool, np.bool_))).all(), f"Boolean: {name}")


def grid_rows(frame, ids, name):
    require(
        frame.grid_id.notna().all()
        and frame.grid_id.is_unique
        and len(frame) == len(ids)
        and set(frame.grid_id) == set(ids),
        f"Grid keys: {name}",
    )
    return frame.set_index("grid_id").loc[ids].reset_index()


def feature_names():
    return (
        weather_policy.MODEL_FEATURES
        + landscape.COVER_FEATURES
        + landscape.TERRAIN_FEATURES
        + [f"vegetation_{w}d_{f}" for w in WINDOWS for f in VEGETATION_FEATURES]
    )


def past_hours(target, hours):
    return pd.Timestamp(target.value - hours * HOUR_NS, unit="ns", tz="UTC")


def join_day(weather, static, vegetation, grid_ids, day):
    """Return allowlisted features plus separate provenance/QA; preserve every cell and NaN."""
    target = training_day(day)
    ids = list(grid_ids)
    require(
        ids and all(isinstance(g, str) and g for g in ids) and len(ids) == len(set(ids)),
        "Canonical grid identities",
    )
    weather = grid_rows(weather.copy(), ids, "weather")
    static = grid_rows(static.copy(), ids, "static")
    require(utc_times(weather.prediction_timestamp_utc).eq(target).all(), "Weather day")
    require(weather.available_at.isna().all(), "Weather availability must remain unknown")
    require(
        utc_times(weather.source_last_timestamp_utc).eq(past_hours(target, 1)).all(),
        "Explicit past weather source timestamp",
    )
    recomputed = weather_policy.transform(weather)
    pd.testing.assert_frame_equal(
        weather[weather_policy.MODEL_FEATURES + WEATHER_QA],
        recomputed[weather_policy.MODEL_FEATURES + WEATHER_QA],
        check_dtype=False,
        check_exact=False,
        rtol=1e-12,
        atol=1e-12,
    )
    require(
        utc_times(weather.weather_source_window_end_exclusive_utc).eq(target).all(),
        "Weather window end",
    )
    require(
        utc_times(weather.weather_source_window_start_utc).eq(past_hours(target, 24)).all(),
        "Weather window start",
    )
    require(
        utc_times(weather.rain_interval_end_utc).eq(past_hours(target, 1)).all(),
        "Rain interval end",
    )
    for hours in weather_policy.RAIN_HOURS:
        require(
            utc_times(weather[f"rain_{hours}h_interval_start_exclusive_utc"])
            .eq(past_hours(target, hours + 1))
            .all(),
            "Rain past interval",
        )
    landscape.validate_cover(static, ids)
    require(
        static.processing_version.eq(landscape.VERSION).all()
        and static.usage.eq("retrospective_candidate_features_only").all()
        and static.historical_available_at.isna().all(),
        "Static provenance",
    )
    boolean(static.landcover_suitability_decided, "habitat")
    require(not static.landcover_suitability_decided.any(), "Habitat policy still undecided")
    values = static[landscape.TERRAIN_FEATURES]
    require(
        np.isfinite(values.to_numpy(float)[values.notna().to_numpy()]).all(),
        "Finite terrain values",
    )
    require(
        static.aoi_area_m2.gt(0).all()
        and static.terrain_valid_area_m2.ge(0).all()
        and static.aspect_valid_area_m2.ge(0).all(),
        "Static support",
    )
    require(
        static.loc[static.terrain_valid_area_m2.eq(0), landscape.TERRAIN_FEATURES]
        .isna()
        .all()
        .all(),
        "Unsupported terrain filled",
    )
    require(
        static.loc[static.aspect_valid_area_m2.eq(0), ["northness_mean", "eastness_mean"]]
        .isna()
        .all()
        .all(),
        "Unsupported aspect filled",
    )

    require(
        len(vegetation) == 2 * len(ids) and set(vegetation.window_days) == set(WINDOWS),
        "Two complete vegetation windows required",
    )
    require(utc_times(vegetation.prediction_timestamp_utc).eq(target).all(), "Vegetation day")
    features = weather[KEYS + weather_policy.MODEL_FEATURES].copy()
    features["prediction_timestamp_utc"] = target.isoformat()
    for field in landscape.COVER_FEATURES + landscape.TERRAIN_FEATURES:
        features[field] = static[field]
    qa = features[KEYS].copy()
    for field in WEATHER_QA + [
        "source_last_timestamp_utc",
        "available_at",
        "source_collection",
        "weather_source_window_start_utc",
        "weather_source_window_end_exclusive_utc",
        "rain_interval_end_utc",
    ]:
        qa[field if field.startswith("weather_") else "weather_" + field] = weather[field]
    for field in STATIC_QA:
        qa["static_" + field] = static[field]
    for window in WINDOWS:
        v = grid_rows(
            vegetation.loc[vegetation.window_days.eq(window)].copy(), ids, f"vegetation {window}"
        )
        boolean(v.vegetation_present, "vegetation_present")
        present = v.vegetation_present
        require(
            v.available_at.isna().all()
            and v.selection_mode.eq("retrospective").all()
            and v.usage.eq("retrospective_candidate_only").all()
            and v.series_version.eq("vegetation_training_month_v1").all(),
            "Vegetation usage/version/availability",
        )
        cutoff = utc_times(v.snapshot_cutoff_utc)
        start = utc_times(v.window_start_utc)
        acquired = utc_times(v.source_acquisition_latest_utc)
        age = (target - cutoff).dt.total_seconds() / 86400
        require(
            (
                cutoff[present].notna()
                & acquired[present].notna()
                & age[present].between(0, 8)
                & start[present].notna()
                & (cutoff[present].astype("int64") - start[present].astype("int64")).eq(
                    window * 24 * HOUR_NS
                )
                & acquired[present].ge(start[present])
                & acquired[present].lt(cutoff[present])
            ).all(),
            "Vegetation strict past window",
        )
        require(
            np.allclose(v.loc[present, "snapshot_age_days"], age[present], rtol=0, atol=1e-9),
            "Snapshot age mismatch",
        )
        require(
            v.loc[present, "processing_version"].eq(vegetation_policy.VERSION).all(),
            "Vegetation processing version",
        )
        indices = v[VEGETATION_FEATURES]
        require(
            np.isfinite(indices[present].to_numpy(float)).all()
            and indices[present].abs().le(1 + 1e-7).all().all()
            and indices[~present].isna().all().all(),
            "Vegetation indices/missingness",
        )
        require(
            v.loc[present, "support_to_aoi_ratio"].gt(0).all()
            and np.isfinite(v.loc[present, "support_to_aoi_ratio"]).all(),
            "Vegetation support",
        )
        latest, median = v.latest_pixel_age_mean_days, v.median_pixel_age_mean_days
        require(
            (
                latest[present].ge(age[present])
                & median[present].ge(latest[present])
                & median[present].le(window + age[present] + 1e-7)
            ).all(),
            "Pixel age bounds",
        )
        require(
            v.loc[
                ~present,
                [
                    "snapshot_cutoff_utc",
                    "snapshot_age_days",
                    "window_start_utc",
                    "source_acquisition_latest_utc",
                    "support_to_aoi_ratio",
                    "latest_pixel_age_mean_days",
                    "median_pixel_age_mean_days",
                ],
            ]
            .isna()
            .all()
            .all(),
            "Missing vegetation provenance filled",
        )
        require(
            v.loc[present, "snapshot_manifest_sha256"]
            .map(lambda s: isinstance(s, str) and bool(re.fullmatch(r"[0-9a-f]{64}", s)))
            .all(),
            "Snapshot provenance hash",
        )
        for field in VEGETATION_FEATURES:
            features[f"vegetation_{window}d_{field}"] = v[field]
        for field in VEGETATION_QA:
            qa[f"vegetation_{window}d_{field}"] = v[field]
    qa["usage"] = "retrospective_candidate_only"
    qa["operational_eligible"] = False
    qa["habitat_eligibility_decided"] = False
    qa["join_version"] = VERSION
    require(features.columns.tolist() == KEYS + feature_names(), "Feature allowlist")
    return features, qa
