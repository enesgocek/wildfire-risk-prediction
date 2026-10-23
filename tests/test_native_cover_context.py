from contextlib import contextmanager

import numpy as np
import pytest
from pyproj import Transformer
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from shapely.geometry import Polygon

from wildfire_risk_prediction.native_cover_context import (
    center_patch_polygon,
    overlap_reference_map,
    rounded_coordinate_matches,
)


def test_coordinate_matching_preserves_none_and_ambiguity():
    assert rounded_coordinate_matches(37, 26, [37.000004, 37.01], [26, 26]).tolist() == [0]
    assert rounded_coordinate_matches(37, 26, [37.000006], [26]).size == 0
    assert rounded_coordinate_matches(37, 26, [37, 37], [26, 26]).tolist() == [0, 1]


def regular_patch():
    x, y = Transformer.from_crs(4326, 6933, always_xy=True).transform(26, 37)
    xx, yy = np.meshgrid(x + np.arange(-1, 2) * 400, y + np.arange(-1, 2) * 300)
    return Transformer.from_crs(6933, 4326, always_xy=True).transform(xx, yy)


def test_patch_reconstructs_known_rectangular_cell():
    polygon = center_patch_polygon(*regular_patch(), 15)
    assert polygon.area == pytest.approx(400 * 300, rel=1e-7)


@pytest.mark.parametrize("row", [0, 31, 32, 63])
def test_scan_boundaries_rejected(row):
    with pytest.raises(ValueError, match="Scan boundary"):
        center_patch_polygon(*regular_patch(), row)


def test_invalid_patch_not_replaced_with_zero_area():
    lon, lat = regular_patch()
    lon[0, 0] = np.nan
    with pytest.raises(ValueError):
        center_patch_polygon(lon, lat, 15)


@contextmanager
def small_map(values):
    x, y = Transformer.from_crs(4326, 3857, always_xy=True).transform(26, 37)
    with (
        MemoryFile() as mem,
        mem.open(
            driver="GTiff",
            height=1,
            width=2,
            count=1,
            dtype="int16",
            crs="EPSG:3857",
            nodata=-9999,
            transform=from_origin(x, y, 100, 100),
        ) as ds,
    ):
        ds.write(np.asarray([values], dtype="int16"), 1)
        yield ds


def map_cell_region(ds, x0, x1):
    xy = [ds.transform @ (c, r) for c, r in [(x0, 0), (x1, 0), (x1, 1), (x0, 1)]]
    x, y = Transformer.from_crs(3857, 6933, always_xy=True).transform(*np.asarray(xy).T)
    return Polygon(zip(x, y, strict=True))


def test_partial_map_intersection_uses_area_not_center_count():
    with small_map([20, 40]) as ds:
        result = overlap_reference_map(map_cell_region(ds, 0.5, 2), ds)
    assert result["forest_shrub_fraction_of_mapped_area"] == pytest.approx(1 / 3)
    assert result["reference_cover_groups"] == ["agriculture", "shrub"]


@pytest.mark.parametrize("unknown", [-9999, 0])
def test_unknown_map_area_remains_in_full_support_denominator(unknown):
    with small_map([20, unknown]) as ds:
        result = overlap_reference_map(map_cell_region(ds, 0, 2), ds)
    assert result["forest_shrub_fraction_of_mapped_area"] == pytest.approx(1)
    assert result["forest_shrub_fraction_of_entire_support"] == pytest.approx(0.5)
    assert result["unknown_or_outside_reference_area_m2"] > 0


def test_all_unknown_has_no_mapped_fraction():
    with small_map([-9999, 0]) as ds:
        result = overlap_reference_map(map_cell_region(ds, 0, 2), ds)
    assert np.isnan(result["forest_shrub_fraction_of_mapped_area"])


def test_outside_map_not_counted_as_known_nonforest():
    with small_map([20, 40]) as ds:
        result = overlap_reference_map(map_cell_region(ds, -1, 1), ds)
    assert result["forest_shrub_fraction_of_mapped_area"] == pytest.approx(1)
    assert result["forest_shrub_fraction_of_entire_support"] == pytest.approx(0.5)
