"""A nearby land cell or precise image fit must not become a verified source position."""

import importlib.util
from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import Point, box

SPEC = importlib.util.spec_from_file_location(
    "marmaris_marker",
    Path(__file__).resolve().parents[1] / "scripts/quality/review_marmaris_published_marker.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_aoi_miss_is_not_snapped_to_nearby_land():
    grid = gpd.GeoDataFrame({"grid_id": ["land"]}, geometry=[box(0, 0, 5, 5)], crs=6933)
    point = Point(-0.01, 2)
    assert grid.intersects(point.buffer(0.02)).any()
    assert MODULE.covered_keys(grid, point) == []
    assert MODULE.covered_keys(grid, Point(0, 2)) == ["land"]


def test_affine_consistency_does_not_claim_physical_accuracy():
    anchors = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0], [10.0, 10.0], [5.0, 5.0]])
    transform = np.array([[2.0, 0.5], [-0.2, 3.0], [100.0, 200.0]])
    targets = np.c_[anchors, np.ones(5)] @ transform
    marker = np.array([-5.0, 4.0])
    coeff, receipt = MODULE.affine_fit(anchors, targets, marker)
    np.testing.assert_allclose(np.r_[marker, 1] @ coeff, np.r_[marker, 1] @ transform)
    assert receipt["max_omitted_control_error_m"] < 1e-10
    assert receipt["marker_inside_control_hull"] is False
    assert receipt["is_physical_location_accuracy_bound"] is False


def test_collinear_registration_is_rejected():
    anchors = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])
    with pytest.raises(ValueError, match="Noncollinear"):
        MODULE.affine_fit(anchors, anchors, np.array([1.0, 1.0]))


def test_control_deletion_that_loses_map_span_is_rejected():
    anchors = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [1.0, 2.0]])
    with pytest.raises(ValueError, match="Omitted controls"):
        MODULE.affine_fit(anchors, anchors, np.array([1.0, 1.0]))
