"""Training-month snapshot schedule and daily retrospective candidates, without labels."""

import re
from datetime import timedelta

import pandas as pd

from wildfire_risk_prediction.vegetation import as_of_snapshots, prediction_time

VERSION = "vegetation_training_month_v1"
WINDOWS = (30, 60)
CADENCE_DAYS = 7
RETENTION_DAYS = 8


def month_schedule(month):
    if not isinstance(month, str) or not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError("Use YYYY-MM")
    first = prediction_time(month + "-01", training_only=True)
    end = (pd.Timestamp(first) + pd.offsets.MonthBegin(1)).to_pydatetime()
    days = [first + timedelta(days=n) for n in range((end - first).days)]
    return days, days[::CADENCE_DAYS]


def daily_candidates(snapshots, grid_ids, month):
    days, cutoffs = month_schedule(month)
    ids = list(grid_ids)
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Grid identities")
    expected = {(g, t.isoformat(), w) for g in ids for t in cutoffs for w in WINDOWS}
    keys = [
        tuple(row)
        for row in snapshots[["grid_id", "snapshot_cutoff_utc", "window_days"]].to_numpy()
    ]
    if len(keys) != len(expected) or set(keys) != expected:
        raise ValueError("Incomplete or duplicate weekly snapshot keys")
    if not snapshots.available_at.isna().all():
        raise ValueError("Historical availability remains unknown in this experiment")
    tables = []
    for window in WINDOWS:
        source = snapshots[snapshots.window_days.eq(window)]
        table = as_of_snapshots(
            source, ids, days, window, max_snapshot_age_days=RETENTION_DAYS, mode="retrospective"
        )
        provenance = source[
            [
                "grid_id",
                "snapshot_cutoff_utc",
                "window_start_utc",
                "processing_version",
                "source_acquisition_latest_utc",
                "source_batch",
                "snapshot_manifest_sha256",
            ]
        ]
        table = table.merge(
            provenance, on=["grid_id", "snapshot_cutoff_utc"], how="left", validate="many_to_one"
        )
        table["usage"] = "retrospective_candidate_only"
        table["series_version"] = VERSION
        tables.append(table)
    result = pd.concat(tables, ignore_index=True)
    if (
        len(result) != len(ids) * len(days) * len(WINDOWS)
        or result.duplicated(["grid_id", "prediction_timestamp_utc", "window_days"]).any()
    ):
        raise ValueError("Daily keys")
    return result
