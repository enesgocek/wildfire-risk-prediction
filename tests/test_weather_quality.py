"""Catch impossible values without silently correcting source data."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "quality", Path(__file__).resolve().parents[1] / "scripts/quality/audit_project.py"
)
quality = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(quality)


@pytest.fixture
def weather():
    values = {
        "temperature_mean_c": [20.0],
        "temperature_min_c": [15.0],
        "temperature_max_c": [30.0],
        "dewpoint_mean_c": [10.0],
        "wind_speed_mean_ms": [1.0],
        "wind_speed_max_ms": [3.0],
        "soil_water_layer_1_mean": [0.2],
        "rain_negative_hours_24h_mean": [0.0],
        "rain_negative_hours_336h_mean": [0.0],
    }
    result = pd.DataFrame(values)
    for name in values:
        result[name + "_valid_area_fraction"] = 1.0
    return result


@pytest.mark.parametrize(
    "feature,value",
    [
        ("temperature_min_c", 25.0),
        ("dewpoint_mean_c", 25.0),
        ("wind_speed_mean_ms", -1.0),
        ("soil_water_layer_1_mean", 1.5),
        ("rain_negative_hours_24h_mean", 25.0),
    ],
)
def test_impossible_values_are_rejected(weather, feature, value):
    weather.loc[0, feature] = value
    with pytest.raises(ValueError):
        quality.check_weather_values(weather)
    assert weather.loc[0, feature] == value  # Audit must not mutate the observation.


def test_min_mean_relationship_is_not_assumed_for_different_coverage(weather):
    weather.loc[0, "temperature_min_c"] = 25.0
    weather.loc[0, "temperature_min_c_valid_area_fraction"] = 0.5
    quality.check_weather_values(weather)
