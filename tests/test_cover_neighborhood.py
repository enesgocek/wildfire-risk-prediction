from contextlib import contextmanager

import numpy as np
import pandas as pd
import pytest
from pyproj import Geod, Transformer
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from wildfire_risk_prediction.cover_neighborhood import describe_neighborhoods

X, Y = Transformer.from_crs(4326, 3857, always_xy=True).transform(26, 37)


@contextmanager
def raster(fill=40, crs=3857):
    data = np.full((31, 31), fill, dtype="int16")
    if fill == 40:
        data[15, 16] = 20
    with (
        MemoryFile() as mem,
        mem.open(
            driver="GTiff",
            height=31,
            width=31,
            count=1,
            dtype="int16",
            crs=f"EPSG:{crs}",
            nodata=-9999,
            transform=from_origin(X - 1550, Y + 1550, 100, 100),
        ) as ds,
    ):
        ds.write(data, 1)
        yield ds


def point():
    return pd.DataFrame({"detection_id": ["p1"], "longitude": [26.0], "latitude": [37.0]})


def test_geodesic_neighborhood_sees_adjacent_cover_without_relabeling_center():
    with raster() as ds:
        result = describe_neighborhoods(point(), ds, (50, 90))
    assert result.center_cover_group_2017.eq("agriculture").all()
    assert result.forest_shrub_pixel_centers.tolist() == [0, 1]
    assert result.mapped_pixel_centers.tolist() == [1, 5]
    assert result.forest_shrub_center_count_fraction.tolist() == [0, 0.2]
    # 100 Web Mercator meters are less than 90 geodesic meters here.
    lon, lat = Transformer.from_crs(3857, 4326, always_xy=True).transform(X + 100, Y)
    expected = Geod(ellps="WGS84").inv(26, 37, lon, lat)[2]
    assert result.iloc[1].nearest_forest_shrub_center_within_radius_m == pytest.approx(expected)
    assert result.target.isna().all()
    assert not result.habitat_eligibility_accepted.any()
    assert not result.radius_is_accepted_geolocation_error_bound.any()


def test_unknown_neighborhood_fraction_stays_missing():
    with raster(fill=-9999) as ds:
        result = describe_neighborhoods(point(), ds, (100,))
    assert result.mapped_pixel_centers.eq(0).all()
    assert result.unknown_or_masked_centers.gt(0).all()
    assert result.forest_shrub_center_count_fraction.isna().all()


def test_counts_nested_but_fraction_not_forced_monotonic():
    with raster() as ds:
        result = describe_neighborhoods(point(), ds, (50, 90, 200))
    assert result.mapped_pixel_centers.is_monotonic_increasing
    assert result.forest_shrub_pixel_centers.is_monotonic_increasing
    assert (
        result.iloc[2].forest_shrub_center_count_fraction
        < result.iloc[1].forest_shrub_center_count_fraction
    )


@pytest.mark.parametrize("radii", [(), (0,), (-1,), (100, 100), (1001,)])
def test_invalid_exploratory_radii_rejected(radii):
    with raster() as ds, pytest.raises(ValueError):
        describe_neighborhoods(point(), ds, radii)


def test_unimplemented_map_crs_and_outside_working_envelope_rejected():
    with raster(crs=4326) as ds, pytest.raises(ValueError):
        describe_neighborhoods(point(), ds)
    p = point()
    p["latitude"] = 60.0
    with raster() as ds, pytest.raises(ValueError):
        describe_neighborhoods(p, ds)
