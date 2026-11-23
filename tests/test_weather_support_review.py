import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction import weather_policy
from wildfire_risk_prediction.ranking_queries import DYNAMIC_FEATURES
from wildfire_risk_prediction.weather_support_review import inspect


def sample():
    x = pd.DataFrame({name: [1.0] * 4 for name in DYNAMIC_FEATURES})
    x.insert(0, "prediction_timestamp_utc", "2022-01-01T00:00:00+00:00")
    x.insert(0, "grid_id", ["a", "b", "c", "d"])
    x.loc[3, weather_policy.MODEL_FEATURES] = np.nan
    q = x[["grid_id", "prediction_timestamp_utc"]].copy()
    q["weather_policy_version"] = weather_policy.VERSION
    q["weather_min_valid_area_fraction"] = [1, 0.95, 0.03, 0]
    q["weather_missing_any"] = [False, False, False, True]
    q["weather_large_negative_rain"] = False
    q["weather_primary_eligible"] = [True, False, False, False]
    q["weather_sensitivity90_eligible"] = [True, True, False, False]
    q["weather_observed_eligible"] = [True, True, True, False]
    q["weather_partial_area"] = [False, True, True, False]
    for w in (30, 60):
        q[f"vegetation_{w}d_vegetation_present"] = True
    return x, q


def test_finite_value_is_not_full_area_and_all_rows_are_retained():
    x, q = sample()
    result = inspect(x, q)
    assert len(result) == len(x)
    assert result.dynamic_15_complete.tolist() == [True, True, True, False]
    assert result.primary_full_area_and_dynamic_15_complete.tolist() == [True, False, False, False]
    assert result.sensitivity_90_area_and_dynamic_15_complete.tolist() == [True, True, False, False]
    assert result.weather_no_valid_area_support.tolist() == [False, False, False, True]
    assert result.weather_finite_but_partial_area.tolist() == [False, True, True, False]
    assert pd.isna(x.loc[3, "temperature_mean_c"])


def test_missing_vegetation_presence_is_not_invented_cloud_cause():
    x, q = sample()
    x.loc[0, "vegetation_30d_ndvi_median_mean"] = np.nan
    x.loc[1, "vegetation_30d_ndmi_median_mean"] = np.nan
    q.loc[1, "vegetation_30d_vegetation_present"] = False
    result = inspect(x, q)
    assert result.vegetation_30d_snapshot_absent.tolist() == [False, True, False, False]
    assert result.vegetation_30d_present_but_missing_requires_review.tolist() == [
        True,
        False,
        False,
        False,
    ]


def test_profile_override_or_closed_year_is_rejected():
    x, q = sample()
    q.loc[2, "weather_primary_eligible"] = True
    with pytest.raises(ValueError, match="fixed source QA"):
        inspect(x, q)
    x, q = sample()
    x["prediction_timestamp_utc"] = "2023-01-01T00:00:00+00:00"
    q["prediction_timestamp_utc"] = x.prediction_timestamp_utc
    with pytest.raises(ValueError, match="already opened pilot"):
        inspect(x, q)
