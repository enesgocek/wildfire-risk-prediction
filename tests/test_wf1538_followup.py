import importlib.util
from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
from exactextract import exact_extract
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from shapely.geometry import box


@pytest.fixture
def audit(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "wf1538_test", folder / "audit_wf1538_native_support.py"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.mark.parametrize("flag", [0, 64768, 1 << 8, 1 << 15])
def test_fire_test_bits_are_not_a_shifted_geolocation_failure(audit, flag):
    result = audit.qa_context(flag)
    assert result["input_low7"] == 0
    assert result["geolocation_non_nominal"] is False
    assert result["m13_non_nominal"] is False
    assert result["residual_bowtie"] is False
    assert "geolocation_low7" not in result


@pytest.mark.parametrize(
    "bit,key", [(5, "geolocation_non_nominal"), (6, "m13_non_nominal"), (22, "residual_bowtie")]
)
def test_input_and_residual_warning_bits_are_preserved_separately(audit, bit, key):
    result = audit.qa_context(1 << bit)
    assert result[key] is True
    assert result["qa_set_bits"] == [bit]


@pytest.mark.parametrize("flag", [-1, 2**32, 1.5])
def test_non_uint32_qa_is_rejected(audit, flag):
    with pytest.raises(ValueError):
        audit.qa_context(flag)


def test_exactextract_frac_is_of_the_polygon_not_of_one_raster_cell(audit):
    values = np.array([[1, 2], [1, 2]], dtype="uint8")
    with MemoryFile() as memory:
        with memory.open(
            driver="GTiff",
            height=2,
            width=2,
            count=1,
            dtype="uint8",
            crs=3035,
            transform=from_origin(0, 200, 100, 100),
        ) as ds:
            ds.write(values, 1)
        with memory.open() as ds:
            polygon = box(75, 25, 125, 175)
            areas = audit.class_areas(ds, polygon)
            result = exact_extract(
                ds,
                gpd.GeoDataFrame(geometry=[polygon], crs=ds.crs),
                ["unique", "frac"],
                output="pandas",
            ).iloc[0]
            fractions = dict(
                zip(map(int, result["unique"]), map(float, result["frac"]), strict=True)
            )
    assert polygon.area == 7500
    assert areas == pytest.approx({1: 3750, 2: 3750})
    assert {k: f * polygon.area for k, f in fractions.items()} == pytest.approx(areas)
    assert sum(fractions.values()) == pytest.approx(1)
