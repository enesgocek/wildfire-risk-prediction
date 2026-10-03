"""Meaningful guards for geometry diagnostics; no footprint certification."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "diagnosis", Path(__file__).resolve().parents[1] / "scripts/firms/audit_l2_geometry.py"
)
diagnosis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diagnosis)


@pytest.mark.parametrize(
    "column,count",
    [
        (0, 1),
        (1279, 1),
        (1280, 2),
        (2015, 2),
        (2016, 3),
        (4383, 3),
        (4384, 2),
        (5119, 2),
        (5120, 1),
        (6399, 1),
    ],
)
def test_zero_based_aggregation_boundaries(column, count):
    assert diagnosis.aggregation_count(column) == count


@pytest.mark.parametrize("column", [-1, 6400, 1.5])
def test_invalid_native_column_rejected(column):
    with pytest.raises(ValueError, match="native column"):
        diagnosis.aggregation_count(column)


def test_scale_and_offset_applied_after_fill_removal():
    class Field:
        nodata, scales, offsets = -32768, (0.01,), (2.0,)

        def read(self, band, window):
            return np.array([[6207, -32768]])

    values = diagnosis.decoded(Field(), None)
    assert values[0, 0] == pytest.approx(64.07)
    assert np.isnan(values[0, 1])


def test_rounded_archive_dimensions_cannot_explain_large_difference():
    assert diagnosis.rounded_difference(0.495, 0.49)["within_archive_rounding_interval"]
    assert not diagnosis.rounded_difference(0.535, 0.49)["within_archive_rounding_interval"]


def test_regular_geographic_patch_has_known_distances_and_missing_terrain_is_retained():
    lon, lat = np.meshgrid(np.arange(3) * 0.001, np.arange(3) * 0.001)
    height = np.zeros((3, 3))
    height[0, 0] = np.nan
    metrics = diagnosis.neighborhood_metrics(lon, lat, height)
    assert metrics["left_spacing_m"] == pytest.approx(111.319, abs=0.002)
    assert metrics["above_spacing_m"] == pytest.approx(110.574, abs=0.002)
    assert metrics["scan_spacing_asymmetry"] < 1e-9
    assert not metrics["terrain_neighborhood_complete"]
    assert metrics["terrain_height_range_m"] is None


def test_geodesic_lengths_and_area_agree_for_small_equatorial_rectangle():
    lon, lat = np.array([0, 0.001, 0.001, 0]), np.array([0.001, 0.001, 0, 0])
    x, y = diagnosis.PROJECT.transform(lon, lat)
    metrics = diagnosis.dimension_metrics(np.column_stack([x, y]))
    assert metrics["estimated_scan_km"] == pytest.approx(0.111319, abs=0.000002)
    assert metrics["estimated_track_km"] == pytest.approx(0.110574, abs=0.000002)
    assert metrics["equal_area_km2"] == pytest.approx(metrics["geodesic_area_km2"], rel=1e-8)


def test_invalid_corner_geometry_is_rejected():
    with pytest.raises(ValueError, match="Invalid local polygon"):
        diagnosis.dimension_metrics(np.array([[0, 0], [1, 1], [0, 1], [1, 0]]))


def test_duplicate_swaths_rejected_before_control_reads():
    with pytest.raises(ValueError, match="distinct swaths"):
        diagnosis.run(["2019013.0100", "SNPP:2019013.0100"])


def test_held_out_year_rejected_before_control_reads():
    with pytest.raises(ValueError, match="training sample"):
        diagnosis.run(["2025001.0100"])


def test_archived_reference_matches_source_row_and_coordinates():
    pilot = pd.DataFrame(
        [
            {
                "source_record_number": "10",
                "latitude": "38.0",
                "longitude": "27.0",
                "detection_timestamp_utc": "2019-01-13T01:02Z",
                "scan": "0.49",
                "track": "0.65",
            }
        ]
    )
    match = {
        "detection_id": "SNPP_815579_10",
        "archive_latitude": 38.0,
        "archive_longitude": 27.0,
        "archive_timestamp_utc": "2019-01-13T01:02Z",
    }
    assert diagnosis.archive_reference(pilot, match)["archive_scan_km"] == 0.49
    match["archive_latitude"] = 39.0
    with pytest.raises(ValueError, match="coordinate/time mismatch"):
        diagnosis.archive_reference(pilot, match)
