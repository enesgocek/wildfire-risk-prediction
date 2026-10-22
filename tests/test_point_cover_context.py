from contextlib import contextmanager

import numpy as np
import pandas as pd
import pytest
from pyproj import Transformer
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from wildfire_risk_prediction.point_cover_context import sample_centers

X, Y = Transformer.from_crs(4326, 3857, always_xy=True).transform(26, 37)
TO_GEO = Transformer.from_crs(3857, 4326, always_xy=True)


def points(offsets):
    xy = [TO_GEO.transform(X + dx, Y + dy) for dx, dy in offsets]
    return pd.DataFrame(
        {
            "detection_id": [f"p{i}" for i in range(len(xy))],
            "longitude": [x for x, _ in xy],
            "latitude": [y for _, y in xy],
        }
    )


@contextmanager
def raster(values=None):
    with MemoryFile() as mem:
        with mem.open(
            driver="GTiff",
            height=2,
            width=2,
            count=1,
            dtype="int16",
            crs="EPSG:3857",
            nodata=-9999,
            transform=from_origin(X - 500, Y + 500, 1000, 1000),
        ) as ds:
            ds.write(np.array(values or [[111, 40], [50, -9999]], dtype="int16"), 1)
            yield ds


def test_xy_projection_and_direct_pixel_read_agree():
    source = points([(0, 0), (1000, 0), (0, -1000)])
    original = source.copy(deep=True)
    with raster() as ds:
        result = sample_centers(source, ds)
        assert result.center_cover_code_2017.tolist() == [111, 40, 50]
        assert result.center_cover_group_2017.tolist() == ["forest", "agriculture", "urban_built"]
        for row in result.itertuples():
            assert (
                ds.read(1)[row.reference_map_row, row.reference_map_column]
                == row.center_cover_code_2017
            )
    assert (
        not result.point_cover_is_fire_truth.any() and not result.current_year_cover_verified.any()
    )
    pd.testing.assert_frame_equal(source, original)


def test_nodata_and_outside_are_unknown_not_water_or_fire_absence():
    with raster() as ds:
        result = sample_centers(points([(1000, -1000), (10000, 10000)]), ds)
    assert result.center_cover_code_2017.isna().all()
    assert result.center_cover_group_2017.eq("unknown_or_unmapped").all()
    assert pd.isna(result.reference_map_row.iloc[1])


@pytest.mark.parametrize("case", ["empty", "duplicate", "nonfinite", "invalid_latitude"])
def test_invalid_point_inventory_fails(case):
    p = points([(0, 0)])
    if case == "empty":
        p = p.iloc[:0]
    elif case == "duplicate":
        p = pd.concat([p, p])
    elif case == "nonfinite":
        p.loc[0, "longitude"] = np.nan
    elif case == "invalid_latitude":
        p.loc[0, "latitude"] = 91
    with raster() as ds, pytest.raises(ValueError):
        sample_centers(p, ds)


def test_unsupported_raster_class_fails():
    with raster([[999, 40], [50, -9999]]) as ds, pytest.raises(ValueError):
        sample_centers(points([(0, 0)]), ds)
