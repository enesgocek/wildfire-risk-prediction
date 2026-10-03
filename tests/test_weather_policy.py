"""Physical bounds, missingness, area sensitivity and sealed-date regression cases."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction import weather_policy as policy


@pytest.fixture
def observations():
    frame = pd.DataFrame({f: [1.0] * 5 for f in policy.RAW_FEATURES})
    for name in policy.RAW_FEATURES:
        frame[name + "_valid_area_fraction"] = 1.0
    frame["grid_id"] = [f"grid-{i}" for i in range(5)]
    frame["prediction_timestamp_utc"] = "2018-01-01T00:00:00Z"
    frame["source_last_timestamp_utc"] = "2017-12-31T23:00:00Z"
    frame["available_at"] = None
    frame["source_collection"] = "ECMWF/ERA5_LAND/HOURLY"
    frame["processing_version"] = "era5_land_past_v1"
    return frame


def test_aggregate_rain_floor_preserves_observations_and_positive_drizzle(observations):
    observations["rain_24h_raw_mm"] = [-0.0001, -0.00001, -0.01, 0.0, 0.0000001]
    before = observations.copy(deep=True)
    result = policy.transform(observations)
    np.testing.assert_allclose(
        result.rain_24h_nonnegative_mm, [0, 0, np.nan, 0, 0.0000001], equal_nan=True
    )
    assert result.rain_24h_roundoff_clipped.tolist() == [True, True, False, False, False]
    assert result.weather_large_negative_rain.tolist() == [False, False, True, False, False]
    assert not result.loc[2, "weather_observed_eligible"]
    pd.testing.assert_frame_equal(observations, before)
    pd.testing.assert_frame_equal(result[before.columns], before)


def test_partial_and_missing_coverage_never_become_zero_weather(observations):
    for name in policy.RAW_FEATURES:
        observations[name + "_valid_area_fraction"] = [1, 0.95, 0.89, 0, 1 - 5e-10]
        observations.loc[3, name] = np.nan
    result = policy.transform(observations)
    assert result.weather_primary_eligible.tolist() == [True, False, False, False, True]
    assert result.weather_sensitivity90_eligible.tolist() == [True, True, False, False, True]
    assert result.weather_observed_eligible.tolist() == [True, True, True, False, True]
    assert result.weather_partial_area.tolist() == [False, True, True, False, False]
    assert np.isnan(result.loc[3, "rain_24h_nonnegative_mm"])
    assert len(result) == len(observations)


@pytest.mark.parametrize("fraction", [-0.1, 1.1, np.nan])
def test_invalid_coverage_is_rejected(observations, fraction):
    observations.loc[0, "temperature_mean_c_valid_area_fraction"] = fraction
    with pytest.raises(ValueError, match="coverage"):
        policy.transform(observations)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_missingness_mismatch_or_infinity_is_rejected(observations, value):
    observations.loc[0, "temperature_mean_c"] = value
    with pytest.raises(ValueError):
        policy.transform(observations)


@pytest.mark.parametrize(
    "column,value",
    [
        ("prediction_timestamp_utc", "2025-01-01T00:00:00Z"),
        ("source_last_timestamp_utc", "2018-01-01T00:00:00Z"),
        ("available_at", "2017-12-31T23:30:00Z"),
        ("processing_version", "unknown"),
    ],
)
def test_source_contract_cannot_silently_change(observations, column, value):
    observations.loc[0, column] = value
    with pytest.raises(ValueError, match="contract"):
        policy.transform(observations)


def test_last_validation_day_is_allowed_and_qa_is_not_a_model_feature(observations):
    observations["prediction_timestamp_utc"] = "2024-12-31T00:00:00Z"
    observations["source_last_timestamp_utc"] = "2024-12-30T23:00:00Z"
    assert policy.transform(observations).weather_primary_eligible.all()
    assert len(policy.MODEL_FEATURES) == 11
    assert not any("negative_hours" in name or "eligible" in name for name in policy.MODEL_FEATURES)


def test_prepare_rejects_final_test_before_reading_any_manifest(monkeypatch, tmp_path):
    directory = Path(__file__).resolve().parents[1] / "scripts/meteorology"
    monkeypatch.syspath_prepend(str(directory))
    spec = importlib.util.spec_from_file_location(
        "model_weather", directory / "prepare_model_weather.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "MANIFEST", tmp_path / "does-not-exist.json")
    with pytest.raises(ValueError, match="2018–2024"):
        module.prepare("2025-01-01", "2025-01-02")
