"""Target windows preserve nanosecond boundaries, source gaps and closed label gates."""

import json

import pandas as pd
import pytest

from wildfire_risk_prediction.observation_window import (
    COUNTS,
    FIELDS,
    classify_intervals,
    loaded_envelope_metrics,
    review_window,
    source_schedule,
)


def row(index, start, end, source="2022-01-18", fire=0):
    return {
        "grid_id": "G",
        "sensor": "SNPP",
        "pair_key": "2022018.2354",
        "scan_index": index,
        "start_utc": start,
        "end_utc": end,
        "pixel_center_count": 10,
        "land_nominal_input_no_residual": 10 - fire,
        "nominal_confidence_fire": fire,
        "high_confidence_fire": 0,
        "source_nominal_day": source,
    }


def crossing():
    return row(202, "2022-01-18T23:59:59.481722951Z", "2022-01-19T00:00:00.045531034Z", fire=1)


def test_crossing_thermal_is_ambiguous_in_both_windows_without_duplicate_positive():
    frame = pd.DataFrame([crossing()])
    for day in ("2022-01-18", "2022-01-19"):
        scans, result = review_window(frame, day, "G", source_schedule(day, set()))
        assert scans.window_classification.tolist() == ["boundary_unknown"]
        assert result["loaded_thermal_center_definite_count"] == 0
        assert result["loaded_thermal_center_boundary_count"] == 1
        assert pd.isna(result["target"])
        assert not result["negative_label_permitted"]
        assert not result["positive_label_permitted"]
        assert not result["exact_target_window_coverage_proven"]


@pytest.mark.parametrize(
    "start,end,status",
    [
        ("2022-01-18T00:00:00Z", "2022-01-18T00:00:00Z", "outside"),
        ("2022-01-18T00:00:00Z", "2022-01-18T00:00:00.000000001Z", "boundary_unknown"),
        ("2022-01-18T00:00:00.000000001Z", "2022-01-18T00:00:01Z", "inside"),
        ("2022-01-18T23:59:59Z", "2022-01-19T00:00:00Z", "inside"),
        ("2022-01-19T00:00:00Z", "2022-01-19T00:00:00Z", "inside"),
        ("2022-01-19T00:00:00Z", "2022-01-19T00:00:00.000000001Z", "boundary_unknown"),
        ("2022-01-19T00:00:00.000000001Z", "2022-01-19T00:00:01Z", "outside"),
    ],
)
def test_exact_open_left_closed_right_nanosecond_semantics(start, end, status):
    f = pd.DataFrame([row(1, start, end)])
    assert classify_intervals(f, "2022-01-18").tolist() == [status]


def test_neighbour_packet_inside_is_carried_once_and_conflicting_duplicate_rejected():
    a = row(203, "2022-01-19T00:00:01Z", "2022-01-19T00:00:02Z", fire=1)
    b = {**a, "source_nominal_day": "2022-01-19"}
    frame = pd.DataFrame([a, b])
    scans, summary = review_window(frame, "2022-01-19", "G", source_schedule("2022-01-19", set()))
    assert summary["duplicate_rows_removed"] == 1
    assert summary["loaded_thermal_center_definite_count"] == 1
    assert json.loads(scans.source_nominal_days_json.iloc[0]) == ["2022-01-18", "2022-01-19"]
    frame.loc[1, "nominal_confidence_fire"] = 2
    with pytest.raises(ValueError, match="Conflicting duplicate"):
        review_window(frame, "2022-01-19", "G", source_schedule("2022-01-19", set()))


def test_missing_and_out_of_training_sources_remain_explicit_not_observed_zero():
    deferred = {"2023-12-31"}
    schedule = source_schedule("2023-12-31", deferred)
    assert schedule.source_status.tolist() == [
        "available_training_packet",
        "deferred_source_day",
        "outside_training_not_read",
    ]
    empty = pd.DataFrame(columns=FIELDS + ["source_nominal_day"])
    _, result = review_window(empty, "2023-12-31", "G", schedule)
    assert not result["all_three_nominal_packets_present"]
    assert result["loaded_any_center_definite_count"] == 0
    assert result["daily_observation_status"] == "unknown"
    assert json.loads(result["unread_nominal_days_json"]) == ["2023-12-31", "2024-01-01"]
    assert source_schedule("2018-01-01", set()).source_status.iloc[0] == "outside_training_not_read"
    for day in ("2024-01-01", "2025-01-01"):
        with pytest.raises(ValueError, match="Training only"):
            source_schedule(day, set())


def test_envelope_union_does_not_double_count_overlaps_and_rejects_crossing():
    frame = pd.DataFrame(
        [
            row(1, "2022-01-18T01:00:00Z", "2022-01-18T01:00:02Z"),
            row(2, "2022-01-18T01:00:01Z", "2022-01-18T01:00:03Z"),
        ]
    )
    union, gap = loaded_envelope_metrics(frame, "2022-01-18")
    assert union == 3 and gap == 23 * 3600 - 3
    with pytest.raises(ValueError, match="Wholly inside"):
        loaded_envelope_metrics(pd.DataFrame([crossing()]), "2022-01-18")


@pytest.mark.parametrize(
    "problem", ["negative", "fractional", "missing_time", "naive_time", "reverse", "source", "key"]
)
def test_corrupt_scan_or_unrequested_source_fails(problem):
    frame = pd.DataFrame([crossing()])
    if problem in ("negative", "fractional"):
        frame[COUNTS[0]] = -1 if problem == "negative" else 1.5
    elif problem == "missing_time":
        frame["start_utc"] = None
    elif problem == "naive_time":
        frame["start_utc"] = "2022-01-18T23:59:59"
    elif problem == "reverse":
        frame["end_utc"] = "2022-01-18T00:00:00Z"
    elif problem == "source":
        frame["source_nominal_day"] = "2024-01-01"
    else:
        frame["pair_key"] = None
    with pytest.raises(ValueError):
        review_window(frame, "2022-01-18", "G", source_schedule("2022-01-18", set()))
