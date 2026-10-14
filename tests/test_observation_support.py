"""Daily union, within-swath support and temporal absence are different quantities."""

import numpy as np
import pytest
import shapely
from shapely.geometry import GeometryCollection, box

from wildfire_risk_prediction.observation_support import overlap_bounds, spatial_support


def test_overlap_can_be_clear_at_one_time_and_cloudy_at_another():
    land = box(0, 0, 1, 1)
    cloud = box(0, 0, 2, 1)
    low, high = overlap_bounds(2, 1, 2)
    measured = land.intersection(cloud).area
    assert low == measured == high == 1
    # Subtracting cloud would erase an actual earlier clear-land observation.
    assert land.difference(cloud).area == 0
    assert land.area == 1


def test_same_daily_union_has_different_single_swath_and_repeated_support():
    left, right, full = box(0, 0, 1, 1), box(1, 0, 2, 1), box(0, 0, 2, 1)
    a = spatial_support([[left], [right]])
    b = spatial_support([[full], [left]])
    assert a[0][0].equals(b[0][0])
    assert a[1][0].area == 0 and b[1][0].area == 1
    assert a[2][0] == 1 and b[2][0] == 2


def test_repeated_support_counts_area_once_and_handles_empty_swath():
    p = box(0, 0, 1, 1)
    union, repeated, maximum = spatial_support([[p], [GeometryCollection()], [p], [p]])
    assert union[0].area == repeated[0].area == maximum[0] == 1


def test_vector_bounds_and_zero_domain():
    low, high = overlap_bounds([0, 10, 10], [0, 8, 2], [0, 7, 3])
    np.testing.assert_array_equal(low, [0, 5, 0])
    np.testing.assert_array_equal(high, [0, 7, 2])


@pytest.mark.parametrize(
    "areas",
    [(1, 2, 0), (1, 0, 2), (-1, 0, 0), (1, -1, 0), (1, 0, -1), (np.nan, 0, 0), (1, np.inf, 0)],
)
def test_invalid_area_evidence_fails(areas):
    with pytest.raises(ValueError):
        overlap_bounds(*areas)


@pytest.mark.parametrize(
    "swaths",
    [
        [],
        [[]],
        [[None]],
        [[box(0, 0, 1, 1)], []],
        [[shapely.from_wkt("POLYGON ((0 0, 1 1, 1 0, 0 1, 0 0))")]],
    ],
)
def test_invalid_geometry_evidence_fails(swaths):
    with pytest.raises(ValueError):
        spatial_support(swaths)
