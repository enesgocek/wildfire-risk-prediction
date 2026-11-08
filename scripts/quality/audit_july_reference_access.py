"""Read the public access receipt and bound date-only incident context in UTC."""

from collections import Counter
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import pandas as pd
from audit_menderes_hona_context import INPUTS, PRIOR
from prepare_pu_calendar_sample import digest
from review_anamur_preevent_cover import CASE_RECEIPT, CASE_SHA
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json

from wildfire_risk_prediction.feature_join import require, training_day
from wildfire_risk_prediction.target_admission import detection_windows, specification

OUT = BASE / "july_reference_access_v1"
ACCESS = OUT / "sources/zenodo_access_2026-11-08.json"
PINS = {
    ACCESS: "56edcc82f0861a5b8828c52e52713e84c164219796ed15a7f207b9760f9cd27c",
    PRIOR: INPUTS[PRIOR],
    CASE_RECEIPT: CASE_SHA,
}
LOCAL = ZoneInfo("Europe/Istanbul")


def date_context(local_date):
    """Use the stated local calendar day as context without inventing an incident hour."""
    training_day(local_date.isoformat())
    start = datetime.combine(local_date, time.min, LOCAL).astimezone(UTC)
    stop = datetime.combine(local_date + timedelta(days=1), time.min, LOCAL).astimezone(UTC)
    # The UTC windows are left-open and the local calendar day is right-open.
    # A source-day start on UTC midnight is an instant in the preceding window.
    last_instant = stop - timedelta(microseconds=1)
    edge_windows = detection_windows(pd.Series([start.isoformat(), last_instant.isoformat()]))
    first, last = edge_windows.prediction_timestamp_utc.tolist()
    overlaps = []
    for prediction in pd.date_range(first, last, freq="D").to_pydatetime():
        duration = min(stop, prediction + timedelta(days=1)) - max(start, prediction)
        overlaps.append(
            {
                "prediction_utc": prediction.isoformat(),
                "hours_of_date_context": duration.total_seconds() / 3600,
            }
        )
    return {
        "reported_local_date": local_date.isoformat(),
        "start_utc_inclusive": start.isoformat(),
        "end_utc_exclusive": stop.isoformat(),
        "candidate_windows": overlaps,
    }


def compare_reported_time(reported):
    utc = pd.Timestamp(reported).tz_convert(UTC)
    local_date = utc.tz_convert(LOCAL).date()
    context = date_context(local_date)
    mapped = detection_windows(pd.Series([utc.isoformat()])).iloc[0].prediction_timestamp_utc
    require(
        mapped.isoformat() in {row["prediction_utc"] for row in context["candidate_windows"]},
        "Reported approximate time inside date context",
    )
    return {
        **context,
        "approximate_reported_time_utc": utc.isoformat(),
        "window_of_approximate_time_utc": mapped.isoformat(),
        "target": None,
    }


def main():
    require(all(digest(path) == value for path, value in PINS.items()), "Frozen receipts")
    access = read_json(ACCESS)
    require(
        access["record"]["access_right"] == "embargoed"
        and access["record"]["public_file_count"] == 0
        and access["file_listing"]["http_status"] == 403
        and access["record"]["doi"] == access["registration"]["doi"],
        "Observed public metadata without public incident files",
    )
    menderes = read_json(PRIOR)["cases"]["menderes"]["reported_onset_local"]
    anamur = read_json(CASE_RECEIPT)["cases"]["anamur_belensazak_approximate"]
    (menderes_time,) = menderes
    cases = {
        "menderes": compare_reported_time(menderes_time),
        "anamur": compare_reported_time(anamur["reported_start_utc"]),
    }
    shapes = Counter()
    for stamp in pd.date_range("2019-01-01", "2020-12-31", freq="D"):
        windows = date_context(stamp.date())["candidate_windows"]
        shapes[tuple(r["hours_of_date_context"] for r in windows)] += 1
    require(shapes == {(3.0, 21.0): 731}, "Two distinct UTC windows for each date")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    path = OUT / stamp / "readback.json"
    path.parent.mkdir(parents=True, exist_ok=False)
    report = {
        "source_sha256": {p.relative_to(ROOT).as_posix(): v for p, v in PINS.items()},
        "producer_sha256": digest(Path(__file__)),
        "public_access": access,
        "source_incident_rows_read": 0,
        "date_only_sensitivity": cases,
        "calendar_2019_2020": {
            "local_calendar_days_checked": sum(shapes.values()),
            "local_days_with_two_utc_windows": shapes[(3.0, 21.0)],
            "hours_in_each_utc_window": [3, 21],
        },
        "target_admission": specification(),
    }
    write_json(path, report)
    require(read_json(path) == report, "Output roundtrip")
    print(path.relative_to(ROOT).as_posix(), digest(path))


if __name__ == "__main__":
    main()
