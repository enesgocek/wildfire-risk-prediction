import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def review():
    p = Path(__file__).resolve().parents[1] / "scripts/quality/review_fwi_local_time.py"
    spec = importlib.util.spec_from_file_location("fwi_clock_review", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def message():
    # Synthetic byte layout, not a claim that the synthetic raster is a real provider field.
    s1 = bytes.fromhex("0000001501006200001cff0407e606010c00000001")
    s4 = bytes.fromhex(
        "00000033040000005d04055ad600620a02ff0401ffffffffffffffffffffff010107e606010000000100000000080100000003"
    )
    others = [bytes([0, 0, 0, 5, i]) for i in (3, 5, 6, 7)]
    body = s1 + others[0] + s4 + b"".join(others[1:]) + b"7777"
    return b"GRIB\x00\x00\x02\x02" + (16 + len(body)).to_bytes(8, "big") + body


def test_local_clock_never_relabels_noon_as_UTC_issue_or_publication(review):
    r = review.local_clock(message())
    assert r["local_reference_wall_clock_without_timezone"] == "2022-06-01T12:00:00"
    assert r["forcing_timestamps_UTC"][0] == "2022-06-01T00:00:00+00:00"
    assert r["forcing_last_UTC"] == "2022-06-01T21:00:00+00:00"
    assert len(r["forcing_timestamps_UTC"]) == 8
    assert r["publication_or_acquisition_timestamp"] is None


def test_broken_or_concatenated_message_is_rejected(review):
    raw = message()
    for bad in (raw[:-1], raw + raw, raw[:16] + b"\x00\x00\x00\x00" + raw[20:]):
        with pytest.raises(ValueError):
            review.sections(bad)


def test_unsupported_reference_or_template_never_gets_a_clock(review):
    raw = bytearray(message())
    raw[16 + 11] = 1
    with pytest.raises(ValueError, match="local time"):
        review.local_clock(raw)
    raw = bytearray(message())
    raw[16 + 21 + 5 + 8] = 0
    with pytest.raises(ValueError, match="4.93"):
        review.local_clock(raw)


def test_format_equivalence_preserves_masks_and_reports_quantization(review):
    a = np.ma.array([1.0, 2.0, 999.0], mask=[False, False, True])
    b = np.ma.array([1.0, 2.0005, -999.0], mask=[False, False, True])
    r = review.compare_arrays(a, b, 0.001)
    assert r["finite_points_compared"] == 2 and r["exact_equal_finite_points"] == 1
    json.dumps(review.compare_arrays(a, b, np.float32(0.001)), allow_nan=False)
    with pytest.raises(ValueError, match="tolerance"):
        review.compare_arrays(a, b, 0.0001)
    with pytest.raises(ValueError, match="mask"):
        review.compare_arrays(a, np.ma.array(b.data, mask=False), 0.001)
