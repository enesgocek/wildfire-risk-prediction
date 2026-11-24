"""A malformed or over-read binary must not be accepted as reference metadata."""

import copy
import json
import struct
from pathlib import Path

import pytest

from wildfire_risk_prediction.mesogeos_reference import dbf_header, shp_header, validate_proposal


def minimal_dbf():
    raw = bytearray(65)
    raw[0] = 3
    struct.pack_into("<IHH", raw, 4, 2, 65, 11)
    raw[32:42] = b"IGNITION_D"
    raw[43] = ord("C")
    raw[48] = 10
    raw[-1] = 13
    return bytes(raw)


def test_dbf_reads_schema_without_record_values():
    result = dbf_header(minimal_dbf())
    assert result["record_values_read"] == 0
    assert result["record_count_declared"] == 2
    assert result["fields"] == [{"name": "IGNITION_D", "type": "C", "width": 10, "decimals": 0}]


@pytest.mark.parametrize("raw", [b"<html>login", minimal_dbf()[:-1], minimal_dbf() + b"event"])
def test_non_header_or_record_bytes_are_rejected(raw):
    with pytest.raises(ValueError):
        dbf_header(raw)


def test_shapefile_header_has_no_geometry_or_date_values():
    raw = bytearray(100)
    struct.pack_into(">I", raw, 0, 9994)
    struct.pack_into(">I", raw, 24, 1000)
    struct.pack_into("<II", raw, 28, 1000, 5)
    struct.pack_into("<dddd", raw, 36, 25, 35, 37, 40)
    result = shp_header(bytes(raw))
    assert result["file_bytes_declared"] == 2000
    assert result["xy_bounds_declared"] == [25, 35, 37, 40]
    assert result["feature_values_read"] == 0
    with pytest.raises(ValueError):
        shp_header(bytes(raw) + b"geometry")


def test_declared_dbf_size_must_match_schema():
    raw = bytearray(minimal_dbf())
    struct.pack_into("<H", raw, 10, 12)
    with pytest.raises(ValueError, match="field widths"):
        dbf_header(bytes(raw))


def test_nonfinite_index_bounds_are_rejected():
    raw = bytearray(100)
    struct.pack_into(">I", raw, 0, 9994)
    struct.pack_into("<II", raw, 28, 1000, 5)
    struct.pack_into("<dddd", raw, 36, float("nan"), 0, 1, 1)
    with pytest.raises(ValueError, match="bounds"):
        shp_header(bytes(raw))


@pytest.fixture
def proposal():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "configs/mesogeos_reference_pilot_proposal_v1.json"
        ).read_bytes()
    )


def test_real_proposal_remains_a_bounded_context_review(proposal):
    validate_proposal(proposal)


@pytest.mark.parametrize(
    "change", ["future_year", "negative", "training", "large_transfer", "parent_path", "execution"]
)
def test_proposal_rejects_scope_expansion(proposal, change):
    altered = copy.deepcopy(proposal)
    if change == "future_year":
        altered["permitted_years"].append(2023)
    elif change == "negative":
        altered["source_absence_is_negative"] = True
    elif change == "training":
        altered["new_model_training"] = True
    elif change == "large_transfer":
        altered["files"][0]["expected_bytes"] = 180000000
    elif change == "parent_path":
        altered["files"][0]["name"] = "../source.cpg"
    else:
        altered["execute_authorized"] = True
    with pytest.raises(ValueError):
        validate_proposal(altered)
