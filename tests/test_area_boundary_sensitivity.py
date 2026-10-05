import importlib.util
from pathlib import Path

import numpy as np
import pytest
import shapely

SPEC = importlib.util.spec_from_file_location(
    "sensitivity", Path(__file__).parents[1] / "scripts/firms/check_area_boundary_sensitivity.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_join_adjacent_cells_before_erosion():
    regions = [shapely.box(0, 0, 100, 100), shapely.box(100, 0, 200, 100)]
    domain, scenarios = module.scenario_areas(regions, regions, [-10, 0, 10])
    # Full observation has no false gap along the analysis grid's shared border.
    np.testing.assert_allclose(domain, [7200, 7200])
    np.testing.assert_allclose(scenarios, np.tile(domain, (3, 1)))


def test_partial_coverage_offsets_have_independent_expected_areas():
    regions = [shapely.box(0, 0, 100, 100), shapely.box(100, 0, 200, 100)]
    coverage = [shapely.box(0, 0, 100, 100), shapely.GeometryCollection()]
    domain, scenarios = module.scenario_areas(regions, coverage, [-10, 0, 10])
    np.testing.assert_allclose(domain, [7200, 7200])
    np.testing.assert_allclose(scenarios, [[6400, 0], [7200, 0], [7200, 800]])


def test_holes_are_excluded_in_all_scenarios():
    region = shapely.box(0, 0, 200, 200).difference(shapely.box(80, 80, 120, 120))
    domain, scenarios = module.scenario_areas([region], [region], [-10, 0, 10])
    assert 0 < domain[0] < region.area
    np.testing.assert_allclose(scenarios[:, 0], domain[0])


def test_empty_coverage_and_narrow_cell_are_preserved():
    regions = [shapely.box(0, 0, 200, 200), shapely.box(500, 0, 505, 100)]
    domain, scenarios = module.scenario_areas(
        regions, [shapely.GeometryCollection(), shapely.GeometryCollection()], [-10, 0, 10]
    )
    assert domain[1] == 0
    np.testing.assert_array_equal(scenarios, 0)


@pytest.mark.parametrize("offsets", [[-1, 1], [0, 0], [0, float("nan")], [1, 0]])
def test_bad_scenarios_rejected(offsets):
    with pytest.raises(ValueError):
        module.scenario_areas(
            [shapely.box(0, 0, 100, 100)], [shapely.GeometryCollection()], offsets
        )


def test_overlapping_regions_rejected():
    regions = [shapely.box(0, 0, 100, 100), shapely.box(50, 0, 150, 100)]
    with pytest.raises(ValueError, match="overlap"):
        module.scenario_areas(regions, regions, [-10, 0, 10])


def test_coverage_outside_region_rejected():
    with pytest.raises(ValueError, match="outside"):
        module.scenario_areas(
            [shapely.box(0, 0, 100, 100)], [shapely.box(90, 0, 110, 100)], [-10, 0, 10]
        )


def test_offsets_cannot_erase_whole_comparison_domain():
    with pytest.raises(ValueError, match="No AOI interior"):
        module.scenario_areas(
            [shapely.box(0, 0, 10, 10)], [shapely.GeometryCollection()], [-10, 0, 10]
        )


def test_halo_scenarios_match_independent_global_union():
    regions = np.asarray(
        [shapely.box(0, 0, 10, 10), shapely.box(10, 0, 20, 10), shapely.box(20, 0, 30, 10)],
        dtype=object,
    )
    # Overlap is removed before indexing; separated pieces remain multipart.
    observed = shapely.union_all(
        [shapely.box(1, 1, 13, 4), shapely.box(9, 2, 14, 5), shapely.box(24, 1, 29, 8)]
    )
    offsets = [-1, 0, 1]
    pieces = shapely.intersection(regions, observed)
    denominator, scenarios = module.scenario_areas(regions, pieces, offsets)
    comparison = shapely.intersection(regions, shapely.union_all(regions).buffer(-1, quad_segs=16))
    np.testing.assert_allclose(denominator, shapely.area(comparison))
    for index, offset in enumerate(offsets):
        shifted = observed if offset == 0 else observed.buffer(offset, quad_segs=16)
        np.testing.assert_allclose(
            scenarios[index], shapely.area(shapely.intersection(comparison, shifted)), atol=1e-8
        )
