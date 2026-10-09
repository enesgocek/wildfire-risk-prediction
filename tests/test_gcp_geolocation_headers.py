"""Keep exact header references distinct from nominal time matching and path formatting."""

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
module = importlib.import_module("collect_gcp_geolocation_headers")
GEO = "VNP03IMG.A2023365.0106.002.2024006061118.nc"
FIRE = "VNP14IMG.A2023365.0106.002.2023365085734.nc"


def pair():
    return {
        "sample_id": "SNPP:2023365.0106",
        "sources": [{"role": "geolocation", "filename": GEO}, {"role": "fire", "filename": FIRE}],
    }


def test_capture_identifies_different_processing_file_without_accepting_same_timestamp():
    actual = GEO.replace("2024006061118", "2023365061118")
    row = module.header_row(
        pair(),
        {"ShortName": "VNP14IMG", "VNP03IMG": actual},
        {"ShortName": "VNP03IMG", "LocalGranuleID": GEO},
    )
    assert row["declared_fields"]["VNP03IMG"]["geolocation_filenames"] == [actual]
    assert row["declared_fields"]["VNP03IMG"]["literal_matches_selected"] is False
    assert row["fire_short_name_matches"] is row["geolocation_short_name_matches"] is True
    assert row["selected_geo_local_id_matches"] is True


def test_full_path_is_reported_separately_from_exact_literal_match():
    record = module.safe_reference("/public/processing/input/" + GEO, GEO)
    assert record["geolocation_filenames"] == [GEO]
    assert record["literal_matches_selected"] is False and record["nonstandard_format"] is True
    assert "/public" not in json.dumps(record)


def test_input_pointer_list_keeps_only_public_geolocation_filenames():
    row = module.header_row(
        pair(),
        {
            "InputPointer": "radiance.nc," + GEO + " SECRET_SESSION_VALUE",
            "unrelated": "SECRET_CONNECTION_VALUE",
        },
        {"LocalGranuleID": GEO},
    )
    assert row["input_pointer"]["geolocation_filenames"] == [GEO]
    assert "SECRET" not in json.dumps(row)


def test_exact_reference_is_distinguishable_from_missing_header():
    exact = module.safe_reference(GEO, GEO)
    absent = module.safe_reference("", GEO)
    assert exact["literal_matches_selected"] is True and exact["nonstandard_format"] is False
    assert absent["geolocation_filenames"] == [] and absent["literal_matches_selected"] is False


def test_reference_size_bound():
    with pytest.raises(ValueError, match="Header reference bound"):
        module.safe_reference("x" * 8193, GEO)
