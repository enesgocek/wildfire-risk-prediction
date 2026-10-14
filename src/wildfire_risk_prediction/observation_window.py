"""Training target-window diagnostics from neighbouring nominal source days."""

import json

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import require, training_day, utc_times

VERSION = "observation_window_v1"
KEYS = ["grid_id", "sensor", "pair_key", "scan_index"]
COUNTS = [
    "pixel_center_count",
    "land_nominal_input_no_residual",
    "nominal_confidence_fire",
    "high_confidence_fire",
]
FIELDS = KEYS + ["start_utc", "end_utc", *COUNTS]


def source_schedule(day, deferred):
    """Describe three nominal packets before any source access; never request holdout."""
    target = training_day(day)
    rows = []
    for offset in (-1, 0, 1):
        source = target + pd.Timedelta(offset, unit="D")
        name = source.strftime("%Y-%m-%d")
        status = (
            "outside_training_not_read"
            if not 2018 <= source.year <= 2023
            else "deferred_source_day"
            if name in deferred
            else "available_training_packet"
        )
        rows.append({"source_nominal_day": name, "source_status": status})
    return pd.DataFrame(rows)


def classify_intervals(frame, day):
    """Closed scan envelope versus open-left, closed-right (T,T+24h]."""
    target = training_day(day)
    start, end = utc_times(frame.start_utc), utc_times(frame.end_utc)
    require(start.notna().all() and end.notna().all() and start.le(end).all(), "Scan times")
    inside = start.gt(target) & end.le(target + pd.Timedelta(24, unit="h"))
    outside = end.le(target) | start.gt(target + pd.Timedelta(24, unit="h"))
    return pd.Series(
        np.select([inside, outside], ["inside", "outside"], default="boundary_unknown"),
        index=frame.index,
    )


def unique_scans(frame):
    """A repeated granule is counted once; conflicting repeats fail closed."""
    require(frame[KEYS].notna().all().all(), "Scan keys")
    values = frame[COUNTS].to_numpy(float)
    require(
        np.isfinite(values).all() and (values >= 0).all() and (values == np.floor(values)).all(),
        "Integer scan counts",
    )
    require(
        frame.land_nominal_input_no_residual.le(frame.pixel_center_count).all()
        and (frame.nominal_confidence_fire + frame.high_confidence_fire)
        .le(frame.pixel_center_count)
        .all(),
        "Class counts within center count",
    )
    repeated = frame.loc[frame.duplicated(KEYS, keep=False)]
    if not repeated.empty:
        for _, group in repeated.groupby(KEYS, sort=False):
            require(len(group[FIELDS].drop_duplicates()) == 1, "Conflicting duplicate source scan")
    result = frame.drop_duplicates(KEYS).copy()
    if not result.empty:
        origins = frame.groupby(KEYS, sort=False).source_nominal_day.agg(
            lambda x: json.dumps(sorted(set(x)))
        )
        result["source_nominal_days_json"] = [origins.loc[tuple(x)] for x in result[KEYS].values]
    else:
        result["source_nominal_days_json"] = pd.Series(dtype=str)
    return result.drop(columns="source_nominal_day").reset_index(drop=True)


def loaded_envelope_metrics(frame, day):
    """Duration/gap of retained scan envelopes, never continuous observation."""
    begin = training_day(day).value
    finish = begin + pd.Timedelta(24, unit="h").value
    if frame.empty:
        return 0.0, 86400.0
    start, end = utc_times(frame.start_utc), utc_times(frame.end_utc)
    require(
        ((start.astype("int64") > begin) & (end.astype("int64") <= finish)).all(),
        "Wholly inside envelope metrics",
    )
    intervals = sorted(zip(start.astype("int64"), end.astype("int64"), strict=True))
    cursor, union, gap = begin, 0, 0
    for a, b in intervals:
        gap = max(gap, a - cursor)
        union += max(0, b - max(a, cursor))
        cursor = max(cursor, b)
    gap = max(gap, finish - cursor)
    return union / 1e9, gap / 1e9


def review_window(frame, day, grid_id, schedule):
    """Report definite and ambiguous loaded counts without inferring absent observations."""
    expected = source_schedule(
        day,
        set(schedule.loc[schedule.source_status.eq("deferred_source_day"), "source_nominal_day"]),
    )
    pd.testing.assert_frame_equal(schedule.reset_index(drop=True), expected)
    allowed = set(
        schedule.loc[schedule.source_status.eq("available_training_packet"), "source_nominal_day"]
    )
    require(
        frame.grid_id.eq(grid_id).all() and set(frame.source_nominal_day) <= allowed,
        "Requested grid and permitted source days only",
    )
    scans = unique_scans(frame)
    scans["window_classification"] = classify_intervals(scans, day)
    scans["prediction_timestamp_utc"] = training_day(day).isoformat()
    inside = scans.window_classification.eq("inside")
    boundary = scans.window_classification.eq("boundary_unknown")
    summary = {
        "grid_id": grid_id,
        "prediction_timestamp_utc": training_day(day).isoformat(),
        "loaded_unique_scan_rows": len(scans),
        "duplicate_rows_removed": len(frame) - len(scans),
        "loaded_inside_scan_rows": int(inside.sum()),
        "loaded_boundary_scan_rows": int(boundary.sum()),
        "loaded_outside_scan_rows": int((~inside & ~boundary).sum()),
        "all_three_nominal_packets_present": bool(
            schedule.source_status.eq("available_training_packet").all()
        ),
        "unread_nominal_days_json": json.dumps(sorted(set(schedule.source_nominal_day) - allowed)),
        "loaded_scan_boundary_ambiguity_absent": not bool(boundary.any()),
        "exact_target_window_coverage_proven": False,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "target": pd.NA,
        "processing_version": VERSION,
    }
    for name, counts in {
        "any_center": scans.pixel_center_count,
        "nominal_land_center": scans.land_nominal_input_no_residual,
        "thermal_center": scans.nominal_confidence_fire + scans.high_confidence_fire,
    }.items():
        summary[f"loaded_{name}_definite_count"] = int(counts[inside].sum())
        summary[f"loaded_{name}_boundary_count"] = int(counts[boundary].sum())
        selected = scans.loc[inside & counts.gt(0)]
        union, gap = loaded_envelope_metrics(selected, day)
        summary[f"loaded_{name}_envelope_union_seconds"] = union
        summary[f"loaded_{name}_longest_envelope_gap_seconds"] = gap
    return scans, summary
