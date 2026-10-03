"""Prevent scan-crossing footprints, overlap inflation and time/holdout mistakes."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import shapely

SPEC = importlib.util.spec_from_file_location(
    "area", Path(__file__).resolve().parents[1] / "scripts/firms/estimate_l2_observed_area.py"
)
area = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(area)


def test_regular_scan_interiors_have_analytically_known_area():
    x, y = np.meshgrid(np.arange(5, dtype=float), np.arange(32, dtype=float))
    corners, valid = area.interior_corners(x, y)
    assert corners.shape == (30, 3, 4, 2)
    assert valid.all()
    polygons = shapely.polygons(corners[valid])
    np.testing.assert_allclose(shapely.area(polygons), 1.0)
    assert shapely.union_all(polygons).area == 90


def test_64_lines_are_not_interpolated_across_scan_boundary():
    x, y = np.meshgrid(np.arange(5, dtype=float), np.arange(64, dtype=float))
    y[32:] -= 10  # Overlap/discontinuity between two detector scans.
    with pytest.raises(ValueError, match="one scan"):
        area.interior_corners(x, y)


def test_missing_neighbor_leaves_geometry_unreconstructed():
    x, y = np.meshgrid(np.arange(5, dtype=float), np.arange(32, dtype=float))
    x[16, 2] = np.nan
    _, valid = area.interior_corners(x, y)
    assert (~valid).sum() == 9


def test_large_coordinate_discontinuity_is_not_an_enormous_pixel():
    x, y = np.meshgrid(np.arange(5, dtype=float), np.arange(32, dtype=float))
    x[:, 3:] += 1e7
    _, valid = area.interior_corners(x, y)
    assert not valid[:, 1:].any()


def test_duplicate_and_overlapping_polygons_are_counted_once():
    first, second = shapely.box(0, 0, 2, 2), shapely.box(1, 0, 3, 2)
    result = area.union_clipped([first, first, second], shapely.box(0, 0, 4, 4))
    assert result.area == 6


def test_aoi_hole_and_outside_center_do_not_use_center_assignment():
    domain = shapely.Polygon(
        [(0, 0), (4, 0), (4, 4), (0, 4)], holes=[[(1, 1), (3, 1), (3, 3), (1, 3)]]
    )
    footprint = shapely.box(-2, 0, 1, 4)  # Its center lies outside the AOI.
    assert not shapely.covers(domain, footprint.centroid)
    assert area.union_clipped([footprint], domain).area == 4


def test_empty_geometry_does_not_become_observed_area():
    assert area.union_clipped([], shapely.box(0, 0, 5, 5)).area == 0


def test_area_output_preserves_unobserved_rows_and_never_permits_labels(tmp_path, monkeypatch):
    import geopandas as gpd

    monkeypatch.setattr(area, "OUTPUT", tmp_path)
    parts = gpd.GeoDataFrame(
        {"grid_id": ["A", "B"]},
        geometry=[shapely.box(0, 0, 5, 5), shapely.box(5, 0, 10, 5)],
        crs=6933,
    )
    empty = shapely.GeometryCollection()
    unions = {
        "reconstructed_domain": [parts.geometry[0], empty],
        "nominal_nonfire_land": [shapely.box(0, 0, 2, 5), empty],
        "cloud": [shapely.box(2, 0, 5, 5), empty],
    }
    table, _ = area.write_area_output("toy", parts, unions)
    assert table.grid_id.tolist() == ["A", "B"]
    assert table.nominal_nonfire_land_fraction_estimate.tolist() == [0.4, 0.0]
    assert table.daily_observation_status.eq("unknown").all()
    assert table.negative_label_permitted.eq(False).all()


def test_self_intersecting_geometry_is_rejected_instead_of_repaired():
    invalid = shapely.Polygon([(0, 0), (1, 1), (0, 1), (1, 0), (0, 0)])
    with pytest.raises(ValueError, match="Invalid geometry"):
        area.union_clipped([invalid], shapely.box(-1, -1, 2, 2))


def test_tai93_uses_product_offset_not_current_tai_utc_offset():
    result = area.tai93_utc([821494810.308835], 10)
    expected = pd.Timestamp("2019-01-13T01:00:00.308835Z")
    assert abs((result[0] - expected).total_seconds()) < 1e-6


@pytest.mark.parametrize("values", [[-999.9], [np.nan]])
def test_fill_scan_time_is_not_a_real_time(values):
    with pytest.raises(ValueError, match="Invalid scan times"):
        area.tai93_utc(values, 10)


@pytest.mark.parametrize("key", ["2024013.0100", "N20:2025013.0100"])
def test_holdout_swaths_are_rejected_before_reading(key):
    with pytest.raises(ValueError, match="training"):
        area.parse_key(key)
