"""Bounded, single-writer training queue around the frozen month builder and readback."""

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from wildfire_risk_prediction.vegetation_series import month_schedule

ROOT = Path(__file__).resolve().parents[2]
VERSION = "vegetation_training_queue_v1"
DEPENDENCIES = (
    "scripts/landcover/prepare_vegetation_month.py",
    "scripts/landcover/prepare_vegetation_full_grid.py",
    "scripts/quality/verify_vegetation_month.py",
    "scripts/quality/verify_vegetation_full_grid.py",
    "src/wildfire_risk_prediction/vegetation.py",
    "src/wildfire_risk_prediction/vegetation_series.py",
    "data/interim/grid_aoi_parts.geojson",
)
GIB = 1024**3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(path)


def months_between(start, end):
    # Validate BOTH endpoints before any filesystem or network operation.
    month_schedule(start)
    month_schedule(end)
    if start > end:
        raise ValueError("Reversed training range")
    year, month = map(int, start.split("-"))
    result = []
    while (name := f"{year:04d}-{month:02d}") <= end:
        result.append(name)
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return result


def manifest_path(month):
    return ROOT / "data/interim/vegetation/month_v1" / month / "manifest.json"


def plan(start, end):
    months = months_between(start, end)
    present = [month for month in months if manifest_path(month).is_file()]
    return {
        "version": VERSION,
        "selected_months": months,
        "manifest_present_unverified": present,
        "pending_months": [month for month in months if month not in present],
        "expected_daily_rows": sum(len(month_schedule(m)[0]) * 2899 * 2 for m in months),
        "windows": [30, 60],
        "cadence_days": 7,
        "max_snapshot_age_days": 8,
        "months_processed_concurrently": 1,
        "earth_engine_requests_concurrently": 2,
        "historical_availability_verified": False,
        "fire_labels_created": False,
        "final_test_accessed": False,
    }


def fingerprints():
    return {name: sha(ROOT / name) for name in DEPENDENCIES}


def require_unchanged(pinned):
    if fingerprints() != pinned:
        raise ValueError("Queue source/grid changed; accepted outputs retained")


@contextmanager
def single_writer():
    path = ROOT / "outputs/cache/vegetation_training_queue.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Never automatically remove a stale lock or allow overlapping runs.
    with path.open("x", encoding="utf-8") as handle:
        json.dump({"pid": os.getpid(), "created_at_utc": datetime.now(UTC).isoformat()}, handle)
    try:
        yield
    finally:
        path.unlink()


def run_child(arguments, log_path, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Invocation budget reached")
    with log_path.open("x", encoding="utf-8") as log:
        child = subprocess.Popen(
            [sys.executable, *arguments],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            code = child.wait(timeout=remaining)
        except BaseException:
            child.kill()
            child.wait()
            raise
    if code:
        raise RuntimeError("Month command failed; checkpoints retained")


def verified_entry(month, report_path):
    report = json.loads(report_path.read_text(encoding="utf-8"))
    path = manifest_path(month)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    expected = len(month_schedule(month)[0]) * 2899 * 2
    if not (
        report["status"] == "monthly_daily_readback_passed"
        and report["month"] == manifest["month"] == month
        and report["manifest_sha256"] == sha(path)
        and report["verified_daily_rows"] == manifest["rows"] == expected
        and report["final_test_accessed"] is False
        and report["historical_availability_verified"] is False
    ):
        raise ValueError("Independent monthly evidence mismatch")
    return {
        "month": month,
        "daily_rows": expected,
        "manifest_sha256": sha(path),
        "daily_table_sha256": manifest["table_sha256"],
        "readback_sha256": sha(report_path),
        "readback": report_path.relative_to(ROOT).as_posix(),
    }


def run(start, end, max_new_months=1, max_run_minutes=45, min_free_gib=10):
    selected = plan(start, end)
    if type(max_new_months) is not int or not 1 <= max_new_months <= 72:
        raise ValueError("New month budget must be 1–72")
    if not math.isfinite(max_run_minutes) or not 1 <= max_run_minutes <= 240:
        raise ValueError("Time budget must be 1–240 minutes")
    if not math.isfinite(min_free_gib) or min_free_gib < 1:
        raise ValueError("At least 1 GiB disk reserve required")
    pinned = fingerprints()
    begun = time.monotonic()
    deadline = begun + max_run_minutes * 60
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8]
    directory = ROOT / "outputs/reports/landscape/period_v1" / run_id
    report = {
        **selected,
        "run_id": run_id,
        "status": "running",
        "code_grid_sha256": pinned,
        "queue_runner_sha256": sha(Path(__file__)),
        "max_new_months": max_new_months,
        "max_run_minutes": max_run_minutes,
        "min_free_gib": min_free_gib,
        "verified_months": [],
        "new_months": 0,
    }
    with single_writer():
        directory.mkdir(parents=True, exist_ok=False)
        try:
            save(directory / "progress.json", report)
            for month in selected["selected_months"]:
                report["current_month"] = month
                require_unchanged(pinned)
                if time.monotonic() >= deadline:
                    report["status"] = "paused_time_budget"
                    break
                existing = manifest_path(month).is_file()
                if not existing and report["new_months"] >= max_new_months:
                    report["status"] = "paused_new_month_budget"
                    break
                if shutil.disk_usage(ROOT).free < min_free_gib * GIB:
                    report["status"] = "paused_disk_reserve"
                    break
                save(directory / "progress.json", report)
                if not existing:
                    print(f"QUEUE PREPARE {month}: two requests, one month", flush=True)
                    run_child(
                        [
                            "scripts/landcover/prepare_vegetation_month.py",
                            "download",
                            "--month",
                            month,
                        ],
                        directory / f"{month}_prepare.log",
                        deadline,
                    )
                require_unchanged(pinned)
                report_name = f"queue_{run_id.lower()}.json"
                print(f"QUEUE READBACK {month}: {'reuse' if existing else 'new'}", flush=True)
                run_child(
                    [
                        "-W",
                        "error::DeprecationWarning",
                        "scripts/quality/verify_vegetation_month.py",
                        "--month",
                        month,
                        "--report-name",
                        report_name,
                    ],
                    directory / f"{month}_readback.log",
                    deadline,
                )
                require_unchanged(pinned)
                evidence = ROOT / "outputs/reports/landscape/month_v1" / month / report_name
                entry = verified_entry(month, evidence)
                entry["action"] = "verified_reused" if existing else "prepared_verified"
                report["verified_months"].append(entry)
                report["new_months"] += int(not existing)
                save(directory / "progress.json", report)
                print(f"QUEUE MONTH VERIFIED {month}: {entry['daily_rows']} rows", flush=True)
            else:
                report["status"] = "selected_training_range_verified"
        except subprocess.TimeoutExpired:
            report["status"] = "paused_time_budget_checkpoints_retained"
        except TimeoutError:
            report["status"] = "paused_time_budget_checkpoints_retained"
        except KeyboardInterrupt:
            report["status"] = "interrupted_checkpoints_retained"
        except Exception as error:
            report["status"] = "failed_checkpoints_retained"
            report["error_type"] = type(error).__name__
            # External error text/credentials are never echoed or added to public reports.
        finally:
            report["elapsed_seconds"] = round(time.monotonic() - begun, 3)
            save(directory / "progress.json", report)
    return report, directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "run"])
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--max-new-months", type=int, default=1)
    parser.add_argument("--max-run-minutes", type=float, default=45)
    parser.add_argument("--min-free-gib", type=float, default=10)
    args = parser.parse_args()
    if args.command == "plan":
        print(json.dumps(plan(args.start, args.end), indent=2))
        return 0
    report, directory = run(
        args.start, args.end, args.max_new_months, args.max_run_minutes, args.min_free_gib
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "verified_months": [r["month"] for r in report["verified_months"]],
                "new_months": report["new_months"],
                "report": (directory / "progress.json").relative_to(ROOT).as_posix(),
                "elapsed_seconds": report["elapsed_seconds"],
            },
            indent=2,
        ),
        flush=True,
    )
    if report["status"] == "interrupted_checkpoints_retained":
        return 130
    return int(report["status"] == "failed_checkpoints_retained")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"QUEUE STOPPED: {type(error).__name__}; existing files retained", flush=True)
        raise SystemExit(1) from None
