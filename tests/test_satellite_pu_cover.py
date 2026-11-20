import importlib.util
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin


@pytest.fixture
def cover(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "sat_cover_test", folder / "prepare_satellite_pu_cover.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scheme_definitions_and_unknown_are_not_interchangeable(cover):
    assert cover.context(111, "CGLS2017") == cover.context(20, "CGLS2017") == "forest_shrub"
    assert cover.context(40, "CGLS2017") == cover.context(211, "CORINE2018") == "agriculture"
    assert cover.context(324, "CORINE2018") == "forest_shrub"
    assert cover.context(321, "CORINE2018") == "other"
    assert cover.context(None, "CORINE2018") == cover.context(0, "CGLS2017") == "unmapped"
    with pytest.raises(ValueError):
        cover.context(311, "CGLS2017")


def test_masked_and_outside_pixels_do_not_turn_into_classes_and_legend_is_decoded(cover, tmp_path):
    path = tmp_path / "toy.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=1,
        dtype="int16",
        crs=4326,
        transform=from_origin(30, 38, 1, 1),
        nodata=-9999,
    ) as raster:
        raster.write(np.array([[7, -9999], [9, 10]], dtype=np.int16), 1)
    result = cover.sample_centers(
        path, [30.5, 31.5, 29], [37.5, 37.5, 37.5], legend={"7": {"clc_code": 311}}
    )
    assert [x["class_code"] for x in result] == [311, None, None]
    assert result[0]["raw_raster_value"] == 7
    assert result[0]["raster_row"] == result[0]["raster_column"] == 0
