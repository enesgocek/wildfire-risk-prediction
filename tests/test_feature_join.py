"""Feature join boundaries: leakage, lost keys, unknown availability and missing support."""

from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import landscape, weather_policy


@pytest.fixture
def sources():
    day = "2018-08-01"
    target = join.training_day(day).to_pydatetime()
    weather = pd.DataFrame(
        {
            "grid_id": ["g1", "g2"],
            "prediction_timestamp_utc": [target.isoformat()] * 2,
            "source_last_timestamp_utc": [(target - timedelta(hours=1)).isoformat()] * 2,
            "available_at": [None] * 2,
            "source_collection": ["ECMWF/ERA5_LAND/HOURLY"] * 2,
            "processing_version": ["era5_land_past_v1"] * 2,
            "weather_source_window_start_utc": [(target - timedelta(days=1)).isoformat()] * 2,
            "weather_source_window_end_exclusive_utc": [target.isoformat()] * 2,
            "rain_interval_end_utc": [(target - timedelta(hours=1)).isoformat()] * 2,
        }
    )
    for hours in weather_policy.RAIN_HOURS:
        weather[f"rain_{hours}h_interval_start_exclusive_utc"] = (
            target - timedelta(hours=hours + 1)
        ).isoformat()
    for field in weather_policy.RAW_FEATURES:
        weather[field] = [1.0, np.nan]
        weather[field + "_valid_area_fraction"] = [1.0, 0.0]
    weather = weather_policy.transform(weather)
    static = pd.DataFrame(
        {
            "grid_id": ["g1", "g2"],
            "reference_year": [2017] * 2,
            "covered_area_km2": [1.0] * 2,
            "processing_version": [landscape.VERSION] * 2,
            "historical_available_at": [None] * 2,
            "usage": ["retrospective_candidate_features_only"] * 2,
            "landcover_suitability_decided": [False] * 2,
            "terrain_valid_area_m2": [1e6, 0.0],
            "aspect_valid_area_m2": [1e6, 0.0],
            "aoi_area_m2": [1e6] * 2,
            "terrain_support_to_aoi_ratio": [1.0, 0.0],
            "terrain_support_close_to_aoi": [True, False],
        }
    )
    for code in landscape.CLASS_CODES:
        static[f"lc_{code}_fraction"] = float(code == 111)
    for field in landscape.COVER_FEATURES + ["unknown_fraction"]:
        static[field] = float(field in {"forest_fraction", "natural_vegetation_fraction"})
    for field in landscape.TERRAIN_FEATURES:
        static[field] = [0.5, np.nan]
    rows = []
    for window in join.WINDOWS:
        for grid_id in ["g1", "g2"]:
            present = grid_id == "g1" or window == 60
            row = {
                "grid_id": grid_id,
                "prediction_timestamp_utc": target.isoformat(),
                "window_days": window,
                "vegetation_present": present,
                "available_at": None,
                "selection_mode": "retrospective",
                "usage": "retrospective_candidate_only",
                "series_version": "vegetation_training_month_v1",
                "snapshot_cutoff_utc": target.isoformat() if present else None,
                "snapshot_age_days": 0.0 if present else np.nan,
                "window_start_utc": (target - timedelta(days=window)).isoformat()
                if present
                else None,
                "source_acquisition_latest_utc": (target - timedelta(days=1)).isoformat()
                if present
                else None,
                "processing_version": "landsat_seasonal_window_v1" if present else None,
                "support_to_aoi_ratio": 0.8 if present else np.nan,
                "source_batch": "30days_batch_000.json" if present else None,
                "snapshot_manifest_sha256": "a" * 64 if present else None,
                "latest_pixel_age_mean_days": 1.0 if present else np.nan,
                "median_pixel_age_mean_days": 2.0 if present else np.nan,
                "ndvi_median_mean": 0.2 if present else np.nan,
                "ndmi_median_mean": 0.3 if present else np.nan,
            }
            rows.append(row)
    return weather, static, pd.DataFrame(rows), ["g2", "g1"], day


def test_join_preserves_keys_missingness_and_separate_windows(sources):
    copies = [frame.copy(deep=True) for frame in sources[:3]]
    result, qa = join.join_day(*sources)
    assert result.grid_id.tolist() == ["g2", "g1"]
    assert result.columns.tolist() == join.KEYS + join.feature_names()
    assert len(join.feature_names()) == 27
    assert pd.isna(result.iloc[0].temperature_mean_c)
    assert pd.isna(result.iloc[0].vegetation_30d_ndvi_median_mean)
    assert result.iloc[0].vegetation_60d_ndvi_median_mean == 0.2
    assert not qa.operational_eligible.any()
    assert "weather_primary_eligible" not in result
    for copy, source in zip(copies, sources[:3], strict=True):
        pd.testing.assert_frame_equal(copy, source)


def test_source_targets_and_observation_columns_cannot_leak(sources):
    for source in sources[:3]:
        source["target"] = 1
        source["daily_observation_status"] = "observed"
        source["event_id"] = "future-event"
    result, qa = join.join_day(*sources)
    assert not {"target", "daily_observation_status", "event_id"} & set(result)
    assert not {"target", "daily_observation_status", "event_id"} & set(qa)


@pytest.mark.parametrize("which", [0, 1, 2])
def test_duplicate_or_lost_source_keys_rejected(sources, which):
    values = list(sources)
    values[which] = pd.concat([values[which], values[which].iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError):
        join.join_day(*values)
    values[which] = sources[which].iloc[1:]
    with pytest.raises(ValueError):
        join.join_day(*values)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_acquisition_latest_utc", "2018-08-01T00:00:00+00:00"),
        ("snapshot_cutoff_utc", "2018-08-02T00:00:00+00:00"),
        ("snapshot_age_days", 4),
        ("available_at", "2018-07-31T00:00:00+00:00"),
        ("source_acquisition_latest_utc", "2018-07-31T00:00:00"),
        ("vegetation_present", "False"),
    ],
)
def test_vegetation_time_availability_and_boolean_guards(sources, field, value):
    sources[2][field] = sources[2][field].astype(object)
    sources[2].loc[0, field] = value
    with pytest.raises(ValueError):
        join.join_day(*sources)


def test_weather_feature_tampering_and_future_interval_rejected(sources):
    sources[0].loc[0, "rain_24h_nonnegative_mm"] = 99
    with pytest.raises(AssertionError):
        join.join_day(*sources)
    sources[0].loc[0, "rain_24h_nonnegative_mm"] = 1
    sources[0].loc[0, "rain_interval_end_utc"] = "2018-08-01T23:00:00Z"
    with pytest.raises(ValueError, match="Rain interval"):
        join.join_day(*sources)


def test_missing_vegetation_cannot_be_filled_from_other_window(sources):
    sources[2].loc[1, "ndvi_median_mean"] = 0.2
    with pytest.raises(ValueError, match="missingness"):
        join.join_day(*sources)


@pytest.mark.parametrize(
    "day", ["2017-12-31", "2024-01-01", "2025-01-01", "2018-08-01T00:00:00Z", "2018-02-30"]
)
def test_training_only_scope(day):
    with pytest.raises(ValueError):
        join.training_day(day)
