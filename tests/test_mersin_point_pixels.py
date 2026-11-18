import importlib.util
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import Point, box


@pytest.fixture
def review(monkeypatch):
    folder = Path(__file__).parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "point_review_test", folder / "audit_mersin_point_pixels.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_overlapping_pixels_are_unioned_for_area(review):
    polygons = np.array([box(-500, -500, 500, 500)] * 2, dtype=object)
    result = review.context(polygons, np.array([5, 5]), np.array([True, True]), Point(0, 0), 250)
    assert result["domain_fraction"] == pytest.approx(1)
    assert result["nominal_land_fraction"] == pytest.approx(1)
    assert result["class_fractions"]["5"] == pytest.approx(1)


def test_point_on_class_boundary_preserves_both_codes(review):
    polygons = np.array([box(-500, -500, 0, 500), box(0, -500, 500, 500)], dtype=object)
    result = review.context(polygons, np.array([4, 5]), np.array([False, True]), Point(0, 0), 250)
    assert result["point_mask_codes"] == [4, 5]
    assert result["class_fractions"]["4"] == pytest.approx(0.5)
    assert result["class_fractions"]["5"] == pytest.approx(0.5)


def test_empty_support_and_non_nominal_land_stay_explicit(review):
    polygons = np.array([box(-500, -500, 500, 500)], dtype=object)
    bad = review.context(polygons, np.array([5]), np.array([False]), Point(0, 0), 250)
    assert bad["point_mask_codes"] == [5] and not bad["point_nominal_land"]
    empty = review.context(polygons, np.array([5]), np.array([True]), Point(2000, 0), 250)
    assert empty["domain_fraction"] == 0 and empty["point_mask_codes"] == []
