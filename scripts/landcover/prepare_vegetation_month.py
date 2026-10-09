"""Bounded training month: verify/reuse full-grid cutoffs, then assemble daily candidates."""

import argparse
import importlib.util
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from wildfire_risk_prediction.vegetation_series import (
    CADENCE_DAYS,
    RETENTION_DAYS,
    VERSION,
    WINDOWS,
    daily_candidates,
    month_schedule,
)

ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["download", "prepare"])
    parser.add_argument("--month", default="2018-08")
    args = parser.parse_args()
    days, cutoffs = month_schedule(args.month)
    full = load_module(
        "full_grid_builder", ROOT / "scripts/landcover/prepare_vegetation_full_grid.py"
    )
    verifier = load_module(
        "full_grid_verifier", ROOT / "scripts/quality/verify_vegetation_full_grid.py"
    )
    output = ROOT / "data/interim/vegetation/month_v1" / args.month
    report_dir = ROOT / "outputs/reports/landscape/month_v1" / args.month
    if (output / "manifest.json").exists():
        raise ValueError("Completed month retained; use its offline verifier")
    features = json.loads(full.PARTS.read_text())["features"]
    if len(features) != 2899:
        raise ValueError("Unexpected project grid")
    groups = full.batches(features, 64)
    grid_ids = [f["properties"]["grid_id"] for group in groups for f in group]
    initialized = False
    snapshots, sources, actions = [], {}, []
    begun = time.monotonic()
    for cutoff in cutoffs:
        target = cutoff.date().isoformat()
        name = target + "_b64"
        directory = ROOT / "data/interim/vegetation/full_grid_v1" / name
        manifest_path = directory / "manifest.json"
        if not manifest_path.exists():
            if args.command != "download":
                raise ValueError("Missing cutoff; prepare makes no network requests")
            if not initialized:
                import ee

                load_dotenv(ROOT / ".env", override=False)
                project = os.getenv("GEE_PROJECT_ID", "").strip()
                if not project:
                    raise ValueError("Earth Engine project missing")
                ee.Initialize(project=project)
                ee.data.setDeadline(180000)
                initialized = True
            spec = full.contract(target, 64)
            raw_root = ROOT / "data/raw/vegetation/full_grid_v1" / name
            requests = [
                (window, group, raw_root / f"{window}days_batch_{n:03d}.json")
                for window in WINDOWS
                for n, group in enumerate(groups)
            ]
            started = time.monotonic()
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = {
                    pool.submit(full.extract, spec, group, window, path): path
                    for window, group, path in requests
                }
                for n, future in enumerate(as_completed(futures), 1):
                    print(f"Month {target} {future.result()} {n}/{len(requests)}", flush=True)
            full.prepare(
                spec,
                requests,
                directory,
                ROOT / "outputs/reports/landscape/full_grid_v1" / name,
                time.monotonic() - started,
            )
            action = "prepared"
        else:
            action = "verified_reused"
        checked = verifier.verify(directory)
        manifest = json.loads(manifest_path.read_text())
        if manifest["contract"] != full.contract(target, 64):
            raise ValueError("Weekly snapshot contract changed")
        table = pd.read_csv(ROOT / manifest["table"])
        table["snapshot_manifest_sha256"] = full.sha(manifest_path)
        snapshots.append(table)
        sources[manifest_path.relative_to(ROOT).as_posix()] = full.sha(manifest_path)
        actions.append({"cutoff": target, "action": action, "verified_rows": checked["rows"]})
        print(f"MONTH CUTOFF VERIFIED {target}: {action}", flush=True)
    combined = pd.concat(snapshots, ignore_index=True)
    daily = daily_candidates(combined, grid_ids, args.month)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "daily_candidates.csv"
    temp = output / "daily_candidates.tmp"
    daily.to_csv(temp, index=False)
    pd.testing.assert_frame_equal(
        daily.where(daily.notna(), np.nan), pd.read_csv(temp), check_dtype=False
    )
    temp.replace(path)
    manifest = {
        "version": VERSION,
        "month": args.month,
        "grid_count": len(grid_ids),
        "days": len(days),
        "cutoffs": [t.isoformat() for t in cutoffs],
        "windows": list(WINDOWS),
        "cadence_days": CADENCE_DAYS,
        "max_snapshot_age_days": RETENTION_DAYS,
        "snapshot_manifests": sources,
        "series_helper_sha256": full.sha(
            ROOT / "src/wildfire_risk_prediction/vegetation_series.py"
        ),
        "builder_sha256": full.sha(Path(__file__)),
        "table": path.relative_to(ROOT).as_posix(),
        "table_sha256": full.sha(path),
        "rows": len(daily),
        "historical_availability_verified": False,
        "final_test_accessed": False,
        "fire_labels_created": False,
    }
    full.save(output / "manifest.json", manifest)
    summaries = [
        {
            "window_days": int(window),
            "rows": len(frame),
            "supported_rows": int(frame.vegetation_present.sum()),
            "missing_rows": int((~frame.vegetation_present).sum()),
        }
        for window, frame in daily.groupby("window_days")
    ]
    report = {
        "status": "retrospective_training_month_prepared",
        "actions": actions,
        "summaries": summaries,
        "invocation_wall_seconds": round(time.monotonic() - begun, 3),
        "table_bytes": path.stat().st_size,
        "manifest_sha256": full.sha(output / "manifest.json"),
        "operationally_eligible_rows_with_current_availability": 0,
        "daily_rows_are_fresh_daily_images": False,
        "limits": [
            "One training month, experimental cadence/retention, no model-quality proof",
            "Historical availability unknown; no labels or final test",
            "Weekly summaries carried from past; no future backfill or 60-day substitution",
        ],
    }
    full.save(report_dir / "preparation.json", report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            f"MONTH PREPARATION STOPPED: {type(error).__name__}; checkpoints retained", flush=True
        )
        raise SystemExit(1) from None
