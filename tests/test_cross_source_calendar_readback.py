import importlib.util
from pathlib import Path

import pytest


def test_standard_time_reader_rejects_future_weather_and_sealed_year():
    path = Path(__file__).resolve().parents[1] / "scripts/quality/verify_cross_source_calendar.py"
    spec = importlib.util.spec_from_file_location("cross_source_readback_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    row = {
        "prediction_timestamp_utc": "2022-07-03T00:00:00+00:00",
        "weather_source_last_timestamp_utc": "2022-07-02T23:00:00+00:00",
        "weather_rain_interval_end_utc": "2022-07-02T23:00:00+00:00",
        "weather_available_at": "",
        "static_reference_year": "2017",
        "operational_eligible": "False",
    }
    for window in (30, 60):
        row[f"vegetation_{window}d_vegetation_present"] = "False"
        row[f"vegetation_{window}d_available_at"] = ""
    module.check_past(row)
    with pytest.raises(ValueError, match="Past weather"):
        module.check_past(
            row | {"weather_source_last_timestamp_utc": row["prediction_timestamp_utc"]}
        )
    with pytest.raises(ValueError, match="Strict 2022"):
        module.check_past(row | {"prediction_timestamp_utc": "2023-07-03T00:00:00+00:00"})
