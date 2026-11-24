"""Boundary checks for supplementary context, without physical-event acceptance."""

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest
from pyproj import Geod

from wildfire_risk_prediction.target_admission import detection_windows

QUALITY = Path(__file__).resolve().parents[1] / "scripts/quality"
sys.path.insert(0, str(QUALITY))
spec = importlib.util.spec_from_file_location(
    "mesogeos_candidate_context", QUALITY / "review_mesogeos_candidate_context.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_earlier_simultaneous_future_and_spatially_distant_records_are_separate():
    timestamp = pd.Timestamp("2022-05-02T12:00:00Z")
    far_lon, far_lat, _ = Geod(ellps="WGS84").fwd(30, 37, 90, 3000)
    frame = pd.DataFrame(
        {
            "timestamp": [
                timestamp - pd.Timedelta(hours=24),
                timestamp - pd.Timedelta(hours=24, seconds=1),
                timestamp,
                timestamp + pd.Timedelta(hours=24),
                timestamp + pd.Timedelta(hours=24, seconds=1),
                timestamp - pd.Timedelta(hours=1),
            ],
            "longitude": [30, 30, 30, 30, 30, far_lon],
            "latitude": [37, 37, 37, 37, 37, far_lat],
        }
    )
    result = module.history_counts(frame, timestamp, 30, 37)
    assert len(result) == 9
    for row in result:
        assert row["earlier_VIIRS_centers"] == (1 if row["history_hours"] == 24 else 2)
        assert row["simultaneous_VIIRS_centers"] == 1
        assert row["later_24h_VIIRS_centers"] == 1


def test_empty_observation_context_is_only_zero_counts():
    frame = pd.DataFrame(
        {"timestamp": pd.to_datetime([], utc=True), "longitude": [], "latitude": []}
    )
    result = module.history_counts(frame, pd.Timestamp("2022-01-02T12:00:00Z"), 30, 37)
    assert len(result) == 9
    assert all(row["earlier_VIIRS_centers"] == 0 for row in result)
    assert all("target" not in row and "new_event_verified" not in row for row in result)


@pytest.mark.parametrize(
    "clock, expected",
    [("2022-05-02T00:00:00Z", "2022-05-01"), ("2022-05-02T00:01:00Z", "2022-05-02")],
)
def test_exact_midnight_is_not_assigned_to_the_next_window(clock, expected):
    window = detection_windows(pd.Series([clock])).iloc[0]
    assert str(window.prediction_timestamp_utc.date()) == expected
