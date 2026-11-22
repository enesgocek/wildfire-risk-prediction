import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def reader():
    path = Path(__file__).resolve().parents[1] / "scripts/quality/inspect_fwi_grib_header.py"
    spec = importlib.util.spec_from_file_location("fwi_grib_header_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_grib_signature_accepts_only_bounded_local_container_header(reader, tmp_path):
    path = tmp_path / "day.grib"
    path.write_bytes(b"GRIB\x00\x00\x00\x02padding")
    actual, edition = reader.check_file(path, tmp_path)
    assert actual == path.resolve() and edition == 2
    path.write_bytes(b"<html>login required</html>")
    with pytest.raises(ValueError, match="signature"):
        reader.check_file(path, tmp_path)


def test_companion_cannot_escape_raw_store_or_disguise_NetCDF(reader, tmp_path):
    path = tmp_path / "day.nc"
    path.write_bytes(b"GRIB\x00\x00\x00\x02padding")
    with pytest.raises(ValueError, match="Explicit GRIB"):
        reader.check_file(path, tmp_path)
    with pytest.raises(ValueError, match="Local companion"):
        reader.check_file(path, tmp_path / "subdir")
