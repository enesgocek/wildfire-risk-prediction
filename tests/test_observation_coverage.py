"""Avoid turning missing requests, outages or non-detections into negative labels."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "coverage", Path(__file__).resolve().parents[1] / "scripts/firms/review_observation_coverage.py"
)
coverage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(coverage)


def table_rows(*rows):
    header = "<tr><th>Year-Day</th><th>Date</th><th>Start</th><th>End</th><th>Comment</th></tr>"
    return (
        "<table>"
        + header
        + "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
        + "</table>"
    )


def test_source_parser_keeps_only_training_and_preserves_interval_edges():
    html = table_rows(
        ["2022-207 - 2022-208", "July 26, 2022 - July 27, 2022", "16:00:00", "15:48:00", "test"],
        ["2024-001", "January 1, 2024", "00:00:00", "00:06:00", "validation"],
        ["2025-001", "January 1, 2025", "00:00:00", "00:06:00", "final"],
    )
    result = coverage.parse_outages(html, "SNPP")
    assert len(result) == 1
    assert result[0]["start_utc"] == "2022-07-26T16:00:00+00:00"
    assert result[0]["end_utc"] == "2022-07-27T15:48:00+00:00"


@pytest.mark.parametrize("year_day,end", [("2022-207", "15:00:00"), ("2022-207 junk", "17:00:00")])
def test_ambiguous_or_reversed_outage_fails_closed(year_day, end):
    with pytest.raises(ValueError):
        coverage.parse_outages(table_rows([year_day, "test", "16:00:00", end, "test"]), "SNPP")


def test_overlap_is_union_and_midnight_end_does_not_exclude_next_day():
    intervals = [
        {"start_utc": "2022-07-26T16:00:00Z", "end_utc": "2022-07-27T00:00:00Z"},
        {"start_utc": "2022-07-26T17:00:00Z", "end_utc": "2022-07-26T18:00:00Z"},
    ]
    assert coverage.overlap_seconds(pd.Timestamp("2022-07-26", tz="UTC"), intervals) == 28800
    assert coverage.overlap_seconds(pd.Timestamp("2022-07-27", tz="UTC"), intervals) == 0


def test_non_leap_day_366_is_not_silently_shifted_to_next_year():
    with pytest.raises(ValueError, match="day-of-year"):
        coverage.parse_outages(
            table_rows(["2021-366", "test", "16:00:00", "17:00:00", "test"]), "SNPP"
        )


def test_positive_counts_and_zeros_never_certify_negative_labels():
    raw = pd.DataFrame({"detection_timestamp_utc": ["2018-04-01T01:00:00Z"]})
    empty = raw.iloc[:0].copy()
    result = coverage.daily_diagnostics(raw, empty, empty, "N20", [])
    assert len(result) == 2191
    january = result.loc[result.date_utc.eq("2018-01-01")].iloc[0]
    april = result.loc[result.date_utc.eq("2018-04-01")].iloc[0]
    april2 = result.loc[result.date_utc.eq("2018-04-02")].iloc[0]
    assert pd.isna(january.turkey_detection_count) and not january.zero_turkey_detections
    assert not january.within_archive_request
    assert april.turkey_detection_count == 1 and not april.zero_turkey_detections
    assert april2.turkey_detection_count == 0 and april2.zero_turkey_detections
    assert not result.negative_label_permitted.any()
    assert result.pixel_observation_status.eq("unknown").all()


def test_validation_detections_cannot_enter_training_diagnostics():
    frame = pd.DataFrame({"detection_timestamp_utc": ["2024-01-01T00:00:00Z"]})
    with pytest.raises(ValueError, match="training"):
        coverage.daily_diagnostics(frame, frame.iloc[:0], frame.iloc[:0], "SNPP", [])
