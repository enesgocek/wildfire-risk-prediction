import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "timing", Path(__file__).parents[1] / "scripts/firms/audit_l2_observation_timing.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
BEGIN, END = pd.Timestamp("2019-01-14T00:00:00Z"), pd.Timestamp("2019-01-15T00:00:00Z")


def shifted(stamp, seconds=0, nanoseconds=0):
    return pd.Timestamp(stamp.value + seconds * 1_000_000_000 + nanoseconds, unit="ns", tz="UTC")


def test_empty_envelopes_keep_whole_day_gap():
    assert module.envelope_metrics([], BEGIN, END) == (0, 86400)


def test_union_overlaps_duplicates_and_day_edges():
    intervals = [
        ("2019-01-14T06:00:00Z", "2019-01-14T06:00:20Z"),
        ("2019-01-14T06:00:10Z", "2019-01-14T06:00:30Z"),
        ("2019-01-14T18:00:00Z", "2019-01-14T18:00:10Z"),
        ("2019-01-14T06:00:00Z", "2019-01-14T06:00:20Z"),
    ]
    assert module.envelope_metrics(intervals[::-1], BEGIN, END) == (40, 43170)


def test_touching_envelopes_and_closed_day_end():
    intervals = [
        (shifted(END, -2), shifted(END, -1)),
        (shifted(END, -1), END),
    ]
    assert module.envelope_metrics(intervals, BEGIN, END) == (2, 86398)


@pytest.mark.parametrize(
    "interval",
    [
        (BEGIN, shifted(BEGIN, 1)),
        (shifted(BEGIN, -1), shifted(BEGIN, 1)),
        (shifted(END, -1), shifted(END, 1)),
        (END, END),
        (END, BEGIN),
        ("2019-01-14T12:00:00", "2019-01-14T12:00:01"),
    ],
)
def test_ambiguous_outside_reversed_and_naive_intervals_are_rejected(interval):
    with pytest.raises(ValueError):
        module.envelope_metrics([interval], BEGIN, END)


def test_subsecond_envelopes_are_not_rounded_to_full_scan_period():
    start = shifted(BEGIN, 1)
    assert module.envelope_metrics(
        [(start, shifted(start, nanoseconds=564_000_123))], BEGIN, END
    ) == (0.564000123, 86398.435999877)


def test_geo_coded_fields_and_side_bit_are_separate():
    assert module.scan_quality_fields(271) == {
        "geo_gap_code": 3,
        "geo_encoder_code": 3,
        "geo_sce_side": 1,
        "geo_other_bits": 0,
    }
    assert module.scan_quality_fields(256)["geo_other_bits"] == 0
    assert module.scan_quality_fields(512 | 16)["geo_other_bits"] == 528


@pytest.mark.parametrize("value", [-999, 8192, 0.5])
def test_invalid_scan_quality_is_rejected(value):
    with pytest.raises(ValueError):
        module.scan_quality_fields(value)


def test_fire_and_overlapping_bad_flags_never_enter_nominal_land_counts():
    mask = np.array([5, 5, 5, 9, 4, 1], dtype="uint8")
    qa = np.array([0, 1 << 5, 1 << 22, 0, 1 << 5, (1 << 5) | (1 << 22)], dtype="uint32")
    result = module.count_centers(["a"] * 6, np.array([0] * 6), mask, qa).iloc[0]
    assert result.pixel_center_count == 6
    assert result.land == 3 and result.high_confidence_fire == 1
    assert result.land_nominal_input_no_residual == 1
    assert result.input_non_nominal == result.geo_non_nominal == 3
    assert result.residual_bowtie == 2
    assert result[list(module.audit.CLASSES)].sum() == 6


def test_granules_from_same_orbit_count_once_and_no_centers_stay_unknown():
    frame = module.count_centers(
        ["a", "a", "a"], np.array([0, 1, 2]), np.array([5, 5, 5]), np.zeros(3, dtype="uint32")
    )
    frame["sensor"] = ["SNPP", "SNPP", "N20"]
    frame["pair_key"] = ["x", "y", "z"]
    frame["orbit_id"] = ["SNPP:10", "SNPP:10", "N20:10"]
    frame["sensor_mode"] = [5, 5, 4]
    frame["day_window_status"] = ["inside", "inside", "boundary_unknown"]
    frame["start_utc"] = ["2019-01-14T01:00:00Z", "2019-01-14T01:00:10Z", "2019-01-14T00:00:00Z"]
    frame["end_utc"] = ["2019-01-14T01:00:01Z", "2019-01-14T01:00:11Z", "2019-01-14T00:00:01Z"]
    daily = module.summarize_grid(frame, {"a", "b"}, BEGIN).set_index("grid_id")
    assert daily.loc["a", "nominal_land_center_granule_count"] == 2
    assert daily.loc["a", "nominal_land_center_orbit_count"] == 1
    assert daily.loc["a", "nominal_land_center_envelope_union_seconds"] == 2
    assert daily.loc["a", "boundary_unknown_scan_count"] == 1
    assert daily.loc["b", "nominal_land_center_longest_envelope_gap_seconds"] == 86400
    assert daily.loc["b", "nominal_land_center_orbit_count"] == 0
    assert daily.daily_observation_status.eq("unknown").all()
    assert daily.negative_label_permitted.eq(False).all()
    frame.loc[2, "day_window_status"] = "inside"
    frame.loc[2, "start_utc"] = "2019-01-14T02:00:00Z"
    frame.loc[2, "end_utc"] = "2019-01-14T02:00:01Z"
    daily = module.summarize_grid(frame, {"a", "b"}, BEGIN).set_index("grid_id")
    assert daily.loc["a", "nominal_land_center_orbit_count"] == 2


def test_csv_preserves_granule_identifiers_with_trailing_zero(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "timing_verifier",
        Path(__file__).parents[1] / "scripts/firms/verify_l2_observation_timing.py",
    )
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    path = tmp_path / "centers.csv"
    path.write_text("pair_key,sensor\n2019014.1200,SNPP\n2019014.0930,N20\n", encoding="utf-8")
    assert verifier.read_result_table(path).pair_key.tolist() == ["2019014.1200", "2019014.0930"]
