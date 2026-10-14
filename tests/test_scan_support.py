"""Repeated area requires both common ground support and separated acquisition envelopes."""

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from wildfire_risk_prediction.scan_support import read_scan_table, temporal_repeat_support


def scans():
    return pd.DataFrame(
        [
            {
                "grid_id": "G",
                "scan_id": "a",
                "orbit_id": "SNPP:1",
                "start_utc": "2019-01-14T01:00:00Z",
                "end_utc": "2019-01-14T01:00:01Z",
            },
            {
                "grid_id": "G",
                "scan_id": "b",
                "orbit_id": "SNPP:2",
                "start_utc": "2019-01-14T07:00:01Z",
                "end_utc": "2019-01-14T07:00:02Z",
            },
        ]
    )


def review(frame=None, shapes=None, **kwargs):
    return temporal_repeat_support(
        scans() if frame is None else frame,
        [box(0, 0, 2, 1), box(1, 0, 3, 1)] if shapes is None else shapes,
        box(0, 0, 3, 1),
        "2019-01-14",
        **kwargs,
    )


def test_exact_gap_edge_and_spatial_intersection():
    repeats, pairs = review()
    assert repeats[1].area == repeats[6].area == 1 and repeats[12].area == 0
    assert len(pairs) == 1 and pairs.minimum_gap_hours.iloc[0] == 6


def test_one_nanosecond_below_cut_is_not_included():
    f = scans()
    f.loc[1, "start_utc"] = "2019-01-14T07:00:00.999999999Z"
    repeats, _ = review(f)
    assert repeats[1].area == 1 and repeats[6].area == 0


def test_identical_orbit_in_multiple_granules_is_not_a_repeat():
    f = scans()
    f.loc[1, "orbit_id"] = "SNPP:1"
    repeats, pairs = review(f)
    assert all(g.is_empty for g in repeats.values()) and pairs.empty


def test_same_orbit_number_on_different_satellite_is_distinct():
    f = scans()
    f.loc[1, "orbit_id"] = "N20:1"
    assert review(f)[0][6].area == 1


def test_nonoverlapping_space_does_not_count_despite_separated_times():
    repeats, pairs = review(shapes=[box(0, 0, 1, 1), box(2, 0, 3, 1)])
    assert all(g.is_empty for g in repeats.values()) and pairs.empty


def test_overlapping_time_envelopes_do_not_meet_positive_gap():
    f = scans()
    f.loc[0, "end_utc"] = "2019-01-14T08:00:00Z"
    assert review(f)[1].empty


def test_boundaries_are_excluded_but_day_end_is_included():
    f = scans()
    f.loc[0, "start_utc"] = "2019-01-14T00:00:00Z"
    assert review(f)[1].empty
    f = scans()
    f.loc[1, "start_utc"] = "2019-01-14T23:59:59Z"
    f.loc[1, "end_utc"] = "2019-01-15T00:00:00Z"
    assert review(f)[0][12].area == 1
    f.loc[1, "end_utc"] = "2019-01-15T00:00:00.000000001Z"
    assert review(f)[1].empty


def test_repeated_pairs_count_area_once_and_input_order_does_not_matter():
    f = scans()
    third = f.iloc[1].copy()
    third.update(
        {
            "scan_id": "c",
            "orbit_id": "N20:3",
            "start_utc": "2019-01-14T20:00:00Z",
            "end_utc": "2019-01-14T20:00:01Z",
        }
    )
    f = pd.concat([f, third.to_frame().T], ignore_index=True).iloc[::-1]
    repeats, pairs = review(f, [box(1, 0, 3, 1), box(1, 0, 3, 1), box(0, 0, 2, 1)])
    assert repeats[1].area == 2 and len(pairs) == 3


def test_empty_support_is_valid_without_inventing_observations():
    repeats, pairs = review(scans().iloc[:0], [])
    assert pairs.empty and all(g.is_empty for g in repeats.values())


@pytest.mark.parametrize("cuts", [[], [0], [-1], [np.nan], [np.inf], [1, 1]])
def test_bad_hour_cuts_fail(cuts):
    with pytest.raises(ValueError):
        review(gaps=cuts)


@pytest.mark.parametrize(
    "column,value",
    [
        ("orbit_id", "SNPP:0"),
        ("orbit_id", "1"),
        ("scan_id", "a"),
        ("grid_id", "OTHER"),
        ("start_utc", "2019-01-14T07:00:01"),
        ("end_utc", "2019-01-14T07:00:01Z"),
    ],
)
def test_invalid_scan_evidence_fails(column, value):
    f = scans()
    f.loc[1, column] = value
    with pytest.raises(ValueError):
        review(f)


@pytest.mark.parametrize(
    "shapes", [[None, box(0, 0, 1, 1)], [], [box(0, 0, 4, 1), box(0, 0, 1, 1)]]
)
def test_invalid_or_outside_geometry_fails(shapes):
    with pytest.raises(ValueError):
        review(shapes=shapes)


def test_closed_holdout_even_when_empty():
    with pytest.raises(ValueError):
        temporal_repeat_support(scans().iloc[:0], [], box(0, 0, 1, 1), "2025-01-14")


def persisted():
    return pd.DataFrame(
        [
            {
                "grid_id": "G",
                "sensor": "SNPP",
                "pair_key": "2019014.0100",
                "scan_index": 5,
                "scan_id": "SNPP:2019014.0100:5",
            }
        ]
    )


def test_scan_readback_preserves_decimal_looking_identity_and_trailing_zeros(tmp_path):
    path = tmp_path / "scan.csv"
    f = persisted()
    f.to_csv(path, index=False)
    actual = read_scan_table(path)
    assert actual.pair_key.iloc[0] == "2019014.0100"
    pd.testing.assert_frame_equal(actual, f)


@pytest.mark.parametrize(
    "column,value",
    [("pair_key", "2019014.01"), ("scan_id", "N20:2019014.0100:5"), ("scan_index", 5.5)],
)
def test_persisted_compound_identity_mismatch_is_rejected(tmp_path, column, value):
    path = tmp_path / "scan.csv"
    f = persisted()
    f[column] = f[column].astype(object)
    f.loc[0, column] = value
    f.to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_scan_table(path)
