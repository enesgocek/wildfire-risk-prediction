import struct

import pytest
from pyproj import Transformer
from shapely.geometry import box

from wildfire_risk_prediction.mesogeos_review import (
    FIELDS,
    acquisition_clock_candidate,
    read_open_year_rows,
    review_points,
)


def make_dbf(path, rows):
    width = 80
    header_size = 33 + 32 * len(FIELDS)
    record_size = 1 + width * len(FIELDS)
    header = bytearray(header_size)
    header[0] = 3
    struct.pack_into("<IHH", header, 4, len(rows), header_size, record_size)
    for i, name in enumerate(FIELDS):
        offset = 32 + 32 * i
        encoded = name.encode("ascii")
        header[offset : offset + len(encoded)] = encoded
        header[offset + 11] = ord("C")
        header[offset + 16] = width
    header[-1] = 13
    body = bytearray(header)
    for row in rows:
        body.extend(b" ")
        for name in FIELDS:
            value = row.get(name, "")
            raw = value if isinstance(value, bytes) else value.encode("ascii")
            body.extend(raw.ljust(width, b" "))
    path.write_bytes(bytes(body) + b"\x1a")


def test_closed_year_bytes_never_reach_text_decoder(tmp_path):
    path = tmp_path / "test.dbf"
    make_dbf(
        path,
        [
            {"YEAR": "2023", "IGNITION_D": "2023-01-01", "COMMUNE": b"\xff"},
            {"YEAR": "2022", "IGNITION_D": "2023-01-01", "COMMUNE": b"\xff"},
            {
                "YEAR": "2022",
                "IGNITION_D": "2022-01-01",
                "ACQ_DATE": "2023-01-01",
                "COMMUNE": b"\xff",
            },
            {"YEAR": "2022", "IGNITION_D": "2022-01-01", "ACQ_DATE": "2022-01-01", "id": "open"},
        ],
    )
    rows, counts, _ = read_open_year_rows(path, "ascii")
    assert [r["id"] for r in rows] == ["open"]
    assert rows[0]["source_record_index"] == 3
    assert counts["open_year_rows_decoded"] == 1


def test_non_numeric_missing_values_are_not_replaced_by_zero(tmp_path):
    path = tmp_path / "test.dbf"
    make_dbf(path, [{"YEAR": "2020", "IGNITION_D": "2020-01-01", "FIREDATE": "2023-01-01"}])
    rows, _, _ = read_open_year_rows(path, "ascii")
    assert rows[0]["FIREDATE"] == ""
    assert rows[0]["FIREDATE_redacted_outside_open_years"]


@pytest.mark.parametrize("clock", ["2460", "2400", "1260", "nan", "-5", "1:00"])
def test_bad_clocks_are_not_forced_into_timestamps(clock):
    assert acquisition_clock_candidate({"ACQ_DATE": "2022-01-01", "ACQ_TIME": clock}) is None


def test_leading_zero_clock_is_conditional_and_date_is_not_shifted():
    assert (
        acquisition_clock_candidate({"ACQ_DATE": "2022-01-01", "ACQ_TIME": "5"})
        == "2022-01-01T00:05:00+00:00"
    )


def test_coordinate_disagreement_is_retained_without_label_acceptance():
    x, y = Transformer.from_crs(4326, 5643, always_xy=True).transform(30, 37)
    row = {
        "source_record_index": 0,
        "geometry_h": f"POINT ({x} {y})",
        "LONGITUDE": "31",
        "LATITUDE": "37",
        "IGNITION_D": "2022-09-30",
        "ACQ_DATE": "2022-09-30",
        "ACQ_TIME": "1000",
        "AREA_HA": "nan",
    }
    result, issues = review_points([row], box(29.5, 36.5, 30.5, 37.5))
    assert not issues
    assert len(result) == 1
    assert result[0]["coordinate_pair_distance_m"] > 80000
    assert result[0]["native_point_in_AOI"]
    assert not result[0]["attribute_point_in_AOI"]
    assert result[0]["target"] is result[0]["accepted_L_membership"] is None
    assert result[0]["negative_label_permitted"] is False
    assert result[0]["area_ha_numeric"] is None
