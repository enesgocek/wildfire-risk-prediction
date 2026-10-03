"""Reject loose or ambiguous coordinate matches and held-out control anchors."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "control", Path(__file__).resolve().parents[1] / "scripts/firms/check_l2_firms_control.py"
)
control = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(control)


def test_float32_native_coordinate_matches_rounded_archive():
    sparse = {
        "FP_latitude": np.array([38.789913], dtype="float32"),
        "FP_longitude": np.array([26.921642], dtype="float32"),
    }
    assert control.coordinate_match(38.78991, 26.92164, sparse) == 0


def test_nearby_pixel_in_same_grid_is_not_accepted():
    sparse = {"FP_latitude": [38.78993], "FP_longitude": [26.92164]}
    with pytest.raises(ValueError, match="Missing or ambiguous"):
        control.coordinate_match(38.78991, 26.92164, sparse)


def test_two_native_pixels_in_rounding_cell_are_ambiguous():
    sparse = {"FP_latitude": [38.789911, 38.789913], "FP_longitude": [26.92164, 26.921641]}
    with pytest.raises(ValueError, match="Missing or ambiguous"):
        control.coordinate_match(38.78991, 26.92164, sparse)


@pytest.mark.parametrize("lat,lon", [(np.nan, 26.0), (38.0, np.inf), (91.0, 26.0)])
def test_invalid_archive_coordinate_is_rejected(lat, lon):
    with pytest.raises(ValueError, match="Invalid archived coordinate"):
        control.coordinate_match(lat, lon, {"FP_latitude": [], "FP_longitude": []})


@pytest.mark.parametrize("year", [2024, 2025])
def test_control_guard_precedes_candidate_or_satellite_reads(tmp_path, year):
    path = tmp_path / "selection.json"
    path.write_text(
        json.dumps({"anchor": {"detection_timestamp_utc": f"{year}-01-13T01:02:00+00:00"}})
    )
    with pytest.raises(ValueError, match="Only training controls"):
        control.check(path)
