import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import pytest


@pytest.fixture
def audit():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/quality/audit_source_conditioned_catalogue_time.py"
    )
    spec = importlib.util.spec_from_file_location("source_catalogue_context_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def detection(stamp, key="one", cell="A"):
    return {"detection_timestamp_utc": stamp, "detection_id": key, "grid_id": cell}


def test_future_context_fields_not_accessed(audit):
    index, count = audit.fit_catalogue_index(
        [{"detection_timestamp_utc": f"{y}-05-01T12:00:00+00:00"} for y in (2017, 2023, 2024, 2025)]
    )
    assert index == {} and count == 0


def test_right_closed_windows_and_previous_context_are_separate(audit):
    index, _ = audit.fit_catalogue_index(
        [
            detection("2021-05-01T00:00:00+00:00", "at_start"),
            detection("2021-05-02T00:00:00+00:00", "at_end"),
            detection("2021-05-02T00:00:00.000001+00:00", "after_end"),
        ]
    )
    r = audit.inspect_window(index, ["A"], "2021-05-01T00:00:00+00:00")
    assert r["preceding_catalogue_detection_rows"] == r["window_catalogue_detection_rows"] == 1
    assert not r["window_hit_proves_new_event"] and not r["previous_hit_proves_same_event"]
    assert r["target"] is None


def test_empty_window_and_truncated_history_do_not_prove_negative_or_new_fire(audit):
    r = audit.inspect_window({}, ["A"], "2018-01-01T00:00:00+00:00")
    assert not r["preceding_context_within_fit_period"]
    assert r["window_catalogue_detection_rows"] == 0
    assert not r["no_hit_proves_fire_absence"] and not r["window_hit_proves_new_event"]


def test_union_of_cells_does_not_duplicate_same_cell_or_select_one_detection(audit):
    index, count = audit.fit_catalogue_index(
        [
            detection("2021-05-01T12:00:00+00:00", "one", "A"),
            detection("2021-05-01T13:00:00+00:00", "two", "B"),
        ]
    )
    r = audit.inspect_window(index, ["A", "A", "B"], "2021-05-01T00:00:00+00:00")
    assert count == 2 and r["window_catalogue_detection_rows"] == 2


def test_duplicate_catalogue_id_is_rejected(audit):
    row = detection("2021-05-01T12:00:00+00:00")
    with pytest.raises(ValueError, match="Unique catalogue"):
        audit.fit_catalogue_index([row, row])


@pytest.mark.parametrize(
    "stamp", ["2023-01-01T00:00:00+00:00", "2022-12-31T00:00:00+00:00", "2021-05-01T12:00:00+00:00"]
)
def test_source_windows_outside_fit_or_midnight_fail(audit, stamp):
    with pytest.raises(ValueError):
        audit.inspect_window({}, ["A"], stamp)


def test_exact_preceding_seven_day_left_boundary_is_excluded(audit):
    stamp = datetime(2021, 4, 24, tzinfo=UTC)
    index = {"A": [(stamp, "left_endpoint")]}
    r = audit.inspect_window(index, ["A"], "2021-05-01T00:00:00+00:00")
    assert r["preceding_catalogue_detection_rows"] == 0


def test_all_nine_hypotheses_survive_no_matches_and_outside_fit_is_not_scored(audit):
    case = {
        "archive_row": "one",
        "diagnostic_focus": True,
        "researcher_retained_outside_L": False,
        "target": None,
        "membership": "review_unassigned",
        "spatial_alternatives": [
            {"radius_projection_plane_m": r, "grid_ids": ["A"]} for r in (0, 250, 1000)
        ],
        "temporal_alternatives": [
            {
                "day_shift": shift,
                "inside_fit": shift != 1,
                "window_start_utc": f"2022-12-{30 + shift}T00:00:00+00:00",
            }
            for shift in (-1, 0, 1)
        ],
    }
    rows, summaries = audit.examine_cases([case, {"diagnostic_focus": False}], {})
    assert len(rows) == len(summaries) == 9
    assert all(r["target"] is None and r["membership"] == "review_unassigned" for r in rows)
    assert sum(x["in_fit_reviewed"] for x in summaries) == 6
    assert sum(x["with_window_catalogue_context"] for x in summaries) == 0
