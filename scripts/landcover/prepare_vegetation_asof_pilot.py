"""Offline daily as-of examples from the matched seasonal snapshots, not a full series."""

import hashlib
import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from wildfire_risk_prediction.vegetation import VERSION, WINDOWS, as_of_snapshots, prediction_time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/interim/vegetation/seasonal_v1"
REPORT = ROOT / "outputs/reports/landscape/seasonal_v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_path = OUT / "manifest_32cells.json"
    manifest = json.loads(manifest_path.read_text())
    source = ROOT / manifest["table"]
    if sha(source) != manifest["table_sha256"]:
        raise ValueError("Snapshot input changed")
    snapshots = pd.read_csv(source)
    if manifest["contract"]["version"] != VERSION:
        raise ValueError("Snapshot version changed")
    ids = manifest["contract"]["grid_ids"]
    # One day before and ten days from each cutoff: explicit future/age-expiry examples.
    dates = sorted(
        {
            prediction_time(d) + timedelta(days=lag)
            for d in manifest["dates"]
            for lag in range(-1, 10)
        }
    )
    summaries, hashes = [], {}
    for mode in ["retrospective", "operational"]:
        tables = []
        for window in WINDOWS:
            source_window = snapshots[snapshots.window_days.eq(window)]
            table = as_of_snapshots(source_window, ids, dates, window, mode=mode)
            provenance = source_window[
                [
                    "grid_id",
                    "snapshot_cutoff_utc",
                    "window_start_utc",
                    "source_acquisition_latest_utc",
                    "processing_version",
                ]
            ]
            table = table.merge(
                provenance,
                on=["grid_id", "snapshot_cutoff_utc"],
                how="left",
                validate="many_to_one",
            )
            table["usage"] = (
                "retrospective_candidate_only"
                if mode == "retrospective"
                else ("availability_gate_example_only_not_operational_validation")
            )
            tables.append(table)
        combined = pd.concat(tables, ignore_index=True)
        path = OUT / f"daily_asof_{mode}_pilot.csv"
        combined.to_csv(path, index=False)
        restored = pd.read_csv(path)
        expected = combined.where(combined.notna(), np.nan)
        pd.testing.assert_frame_equal(expected, restored, check_dtype=False)
        hashes[path.relative_to(ROOT).as_posix()] = sha(path)
        summaries.append(
            {
                "mode": mode,
                "rows": len(combined),
                "supported_rows": int(combined.vegetation_present.sum()),
                "missing_rows": int((~combined.vegetation_present).sum()),
            }
        )
    report = {
        "status": "daily_asof_pilot_prepared",
        "snapshot_manifest_sha256": sha(manifest_path),
        "table_sha256": hashes,
        "summaries": summaries,
        "cells": len(ids),
        "prediction_dates": [d.isoformat() for d in dates],
        "max_snapshot_age_days": 8,
        "cadence_days_proposed": 7,
        "windows": list(WINDOWS),
        "final_test_accessed": False,
        "limits": [
            "Four seasonal cutoffs and 44 sample dates, not full daily coverage",
            "Eight-day retention is experimental, not model-quality validated",
            "Unknown historical release means zero operationally eligible rows",
            "No interpolation, future backfill, zero fill or fire labels",
        ],
    }
    (REPORT / "daily_asof_pilot.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": report["status"], "summaries": summaries}, indent=2))


if __name__ == "__main__":
    main()
