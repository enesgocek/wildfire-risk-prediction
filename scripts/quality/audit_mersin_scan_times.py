"""Compare individual VIIRS scan times with two readings of Mersin archive clocks."""

import hashlib
import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from uuid import uuid4

import pandas as pd
from audit_mersin_observation_context import AREA_CLASSES, incident_windows
from audit_mersin_open_incidents import ARCHIVE, GRID, PINS, PROVINCES, ROOT
from audit_stage_one_selection import BASE, OBS, read_report, verify

from wildfire_risk_prediction.feature_join import require, utc_times
from wildfire_risk_prediction.observation_window import review_window, source_schedule
from wildfire_risk_prediction.observation_window_source import read_month_offline
from wildfire_risk_prediction.target_admission import specification


def selected_windows(windows):
    raw = windows.loc[windows.basis.eq("if_source_utc")].copy()
    raw["year"] = raw.stated_time.dt.year
    raw["minute"] = raw.stated_time.dt.hour * 60 + raw.stated_time.dt.minute
    # Clock extremes expose sensitivity to UTC midnight. Selection ignores satellite data.
    groups = raw.sort_values(["minute", "stated_time", "archive_row"]).groupby(["year", "small"])
    ids = pd.concat([groups.head(1), groups.tail(1)]).archive_row
    require(len(ids) == ids.nunique() == 24, "Expected two distinct rows per year and area class")
    return windows.loc[windows.archive_row.isin(ids)].copy()


def compare_scan_times(scans, stated):
    inside = scans.loc[scans.window_classification.eq("inside")]
    land = inside.loc[inside.land_nominal_input_no_residual.gt(0)]
    thermal = inside.loc[(inside.nominal_confidence_fire + inside.high_confidence_fire).gt(0)]
    start, end = utc_times(land.start_utc), utc_times(land.end_utc)
    last_before = end.loc[end.lt(stated)].max()
    first_after = start.loc[start.gt(stated)].min()
    thermal_start = utc_times(thermal.start_utc)
    return {
        "land_scan_envelopes_in_window": len(land),
        "minutes_since_previous_land_scan": (
            (stated - last_before).total_seconds() / 60 if pd.notna(last_before) else None
        ),
        "minutes_to_next_land_scan": (
            (first_after - stated).total_seconds() / 60 if pd.notna(first_after) else None
        ),
        "land_scan_envelope_contains_stated_minute_instant": bool(
            (start.le(stated) & end.ge(stated)).any()
        ),
        "thermal_scan_before": bool(utc_times(thermal.end_utc).lt(stated).any()),
        "thermal_scan_at_or_after": bool(thermal_start.ge(stated).any()),
    }


def main():
    for path in (ARCHIVE, GRID, PROVINCES):
        verify(path, PINS[path])
    windows = selected_windows(incident_windows())
    master = read_report(OBS / "accepted_readback.json")
    reports = {report["month"]: report for report in master["reports"]}
    deferred = set(master["missing_source_days"])
    windows["day"] = windows.prediction_timestamp_utc.str[:10]
    schedules = {day: source_schedule(day, deferred) for day in windows.day.unique()}
    requested = defaultdict(lambda: defaultdict(set))
    for row in windows.itertuples(index=False):
        schedule = schedules[row.day]
        for day in schedule.loc[
            schedule.source_status.eq("available_training_packet"), "source_nominal_day"
        ]:
            requested[day[:7]][day].add(row.grid_id)
    frames, inputs, inner = {}, {}, {}
    for month, dates in sorted(requested.items()):
        package = read_month_offline(ROOT, reports[month], dates, time.monotonic() + 120)
        frames.update(package["frames"])
        inputs.update(package["inputs"])
        inner.update(package["inner"])

    rows = []
    for row in windows.itertuples(index=False):
        schedule = schedules[row.day]
        parts = [frames[d] for d in schedule.source_nominal_day if d in frames]
        frame = pd.concat(parts, ignore_index=True)
        scans, summary = review_window(
            frame.loc[frame.grid_id.eq(row.grid_id)], row.day, row.grid_id, schedule
        )
        rows.append(
            {
                "archive_row": row.archive_row,
                "area_class": AREA_CLASSES[row.small],
                "basis": row.basis,
                "stated_utc": row.stated_time.isoformat(),
                "all_three_source_packets_present": summary["all_three_nominal_packets_present"],
                **compare_scan_times(scans, row.stated_time),
            }
        )
    result = {
        "selection": "earliest_and_latest_recorded_clock_per_year_and_final_area_class",
        "archive_rows": int(windows.archive_row.nunique()),
        "monthly_payload_count": len(requested),
        "nominal_days_read": len(frames),
        "source_payload_sha256": inputs,
        "daily_member_sha256": inner,
        "rows": rows,
        "target_admission": specification(),
    }
    out = BASE / "mersin_scan_times_v1" / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Output roundtrip")
    print(path.relative_to(ROOT).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
