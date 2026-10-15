import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "pilot_triage", Path(__file__).parents[1] / "scripts/quality/triage_observation_pilot_times.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def scans():
    return pd.DataFrame(
        {
            "scan_index": [0, 1],
            "first_native_row": [0, 32],
            "start_utc": ["2018-02-14T00:00:01Z", "2018-02-14T00:00:02Z"],
            "end_utc": ["2018-02-14T00:00:01.5Z", "2018-02-14T00:00:02.5Z"],
        }
    )


def test_full_previous_day_witness_can_exclude_only_that_target_window():
    frame = scans()
    assert (
        module.classify_pair(frame, "2018-02-15", 2)["decision"] == "outside_by_full_scan_witness"
    )
    assert (
        module.classify_pair(frame, "2018-02-14", 2)["decision"] == "retain_raw_inside_or_boundary"
    )


@pytest.mark.parametrize("change", ["missing", "duplicate", "row_binding", "reversed"])
def test_incomplete_or_corrupt_time_witness_fails_closed(change):
    frame = scans()
    if change == "missing":
        frame = frame.iloc[:1]
    elif change == "duplicate":
        frame.loc[1, "scan_index"] = 0
    elif change == "row_binding":
        frame.loc[1, "first_native_row"] = 31
    else:
        frame.loc[0, "end_utc"] = "2018-02-13T23:59:59Z"
    with pytest.raises(ValueError):
        module.classify_pair(frame, "2018-02-15", 2)


def test_boundary_crossing_granule_must_stay_in_raw_queue():
    frame = scans()
    frame.loc[1, "start_utc"] = "2018-02-14T23:59:59.5Z"
    frame.loc[1, "end_utc"] = "2018-02-15T00:00:00.1Z"
    result = module.classify_pair(frame, "2018-02-15", 2)
    assert result["decision"] == "retain_raw_inside_or_boundary"
    assert result["boundary_scan_count"] == 1


def test_exact_day_end_is_inside_but_open_left_boundary_is_uncertain():
    frame = scans().iloc[:1].copy()
    frame.loc[0, "start_utc"] = "2018-02-15T23:59:59.5Z"
    frame.loc[0, "end_utc"] = "2018-02-16T00:00:00Z"
    assert module.classify_pair(frame, "2018-02-15", 1)["inside_scan_count"] == 1
    frame.loc[0, "start_utc"] = "2018-02-15T00:00:00Z"
    frame.loc[0, "end_utc"] = "2018-02-15T00:00:00.5Z"
    assert module.classify_pair(frame, "2018-02-15", 1)["boundary_scan_count"] == 1


@pytest.mark.parametrize("day", ["2024-02-15", "2025-02-15"])
def test_holdout_cannot_be_opened_by_time_filter(day):
    with pytest.raises(ValueError):
        module.classify_pair(scans(), day, 2)
