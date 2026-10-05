import importlib.util
from pathlib import Path

import numpy as np
import pytest
import shapely

SPEC = importlib.util.spec_from_file_location(
    "raster_diagnostic", Path(__file__).parents[1] / "scripts/firms/check_area_grid_sensitivity.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_aligned_rectangle_has_known_area():
    assert (
        module.sampled_area(shapely.box(0, 0, 100, 100), shapely.box(0, 0, 50, 100), 10, (0, 0))
        == 5000
    )


def test_origin_changes_membership_with_closed_boundary_rule():
    region = shapely.box(0, 0, 20, 10)
    coverage = shapely.box(0, 0, 9, 10)
    assert module.sampled_area(region, coverage, 10, (0, 0)) == 100
    assert module.sampled_area(region, coverage, 10, (0.5, 0)) == 50
    # Exactly on x=10 is included by the declared closed-polygon rule.
    assert module.sampled_area(region, shapely.box(0, 0, 10, 10), 10, (0.5, 0)) == 150


@pytest.mark.parametrize("phase", module.PHASES)
def test_full_and_empty_coverage_preserve_exact_region_denominator(phase):
    region = shapely.box(1, 2, 19, 28).difference(shapely.box(4, 4, 8, 12))
    assert module.sampled_area(region, shapely.box(-50, -50, 50, 50), 10, phase) == region.area
    assert module.sampled_area(region, shapely.GeometryCollection(), 10, phase) == 0


def test_adjacent_analysis_regions_share_global_lattice_and_neighbor_coverage():
    coverage = shapely.box(-100, -100, 100, 100)
    first, second = shapely.box(0, 0, 7, 10), shapely.box(7, 0, 20, 10)
    whole = first.union(second)
    for phase in module.PHASES:
        a = module.sampled_area(first, coverage, 10, phase)
        b = module.sampled_area(second, coverage, 10, phase)
        assert a + b == module.sampled_area(whole, coverage, 10, phase) == 200


def test_negative_coordinates_use_floor_not_truncation():
    region = shapely.box(-19, -11, -1, -2)
    assert module.sampled_area(region, shapely.box(-30, -30, 0, 0), 10, (0, 0)) == region.area


def test_narrow_region_with_center_in_neighbor_is_not_lost():
    assert module.sampled_area(shapely.box(1, 1, 2, 9), shapely.box(0, 0, 10, 10), 10, (0, 0)) == 8


def test_polygon_hole_is_not_filled_by_center_sampling():
    coverage = shapely.box(0, 0, 30, 30).difference(shapely.box(10, 10, 20, 20))
    assert module.sampled_area(shapely.box(0, 0, 30, 30), coverage, 10, (0, 0)) == 800


def test_empty_comparison_region_is_zero():
    assert (
        module.sampled_area(shapely.GeometryCollection(), shapely.box(0, 0, 10, 10), 10, (0, 0))
        == 0
    )


@pytest.mark.parametrize(
    "resolution, phase",
    [
        (0, (0, 0)),
        (-1, (0, 0)),
        (np.nan, (0, 0)),
        (10, (1, 0)),
        (10, (-0.5, 0)),
        (10, (0,)),
        (10, (0, np.nan)),
    ],
)
def test_invalid_lattice_rejected(resolution, phase):
    with pytest.raises(ValueError, match="Invalid resolution"):
        module.sampled_area(shapely.box(0, 0, 10, 10), shapely.box(0, 0, 5, 10), resolution, phase)


def test_large_allocation_is_rejected_before_meshgrid():
    with pytest.raises(ValueError, match="Too many lattice"):
        module.sampled_area(shapely.box(0, 0, 1e6, 1e6), shapely.box(0, 0, 1e6, 1e6), 1, (0, 0))
