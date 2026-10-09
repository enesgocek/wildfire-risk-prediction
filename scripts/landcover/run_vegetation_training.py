"""Finite training supervisor: automatically resume bounded queues, stop on errors/disk limits."""

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
import platform
import re
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "training_period_queue", ROOT / "scripts/landcover/prepare_vegetation_period.py"
)
queue = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(queue)
VERSION = "vegetation_training_supervisor_v1"


def runtime():
    return {
        "python": platform.python_version(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("earthengine-api", "pandas", "numpy", "python-dotenv", "pyproj")
        },
        "source_sha256": {
            **queue.fingerprints(),
            "scripts/landcover/prepare_vegetation_period.py": queue.sha(
                ROOT / "scripts/landcover/prepare_vegetation_period.py"
            ),
            "supervisor": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "uv.lock": queue.sha(ROOT / "uv.lock"),
            "pyproject.toml": queue.sha(ROOT / "pyproject.toml"),
        },
    }


@contextmanager
def supervisor_lock(job_id):
    path = ROOT / "outputs/cache/vegetation_training_supervisor.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump({"pid": os.getpid(), "job_id": job_id}, handle)
    try:
        yield
    finally:
        path.unlink()


def run(start, end, hours=24, batch_minutes=240, min_free_gib=10, job_id=None, max_batches=24):
    selected = queue.plan(start, end)
    if not math.isfinite(hours) or not 1 <= hours <= 48:
        raise ValueError("Overall runtime must be 1–48 hours")
    if not math.isfinite(batch_minutes) or not 1 <= batch_minutes <= 240:
        raise ValueError("Batch runtime must be 1–240 minutes")
    if not math.isfinite(min_free_gib) or min_free_gib < 1:
        raise ValueError("Disk reserve must be at least 1 GiB")
    if type(max_batches) is not int or not 1 <= max_batches <= 24:
        raise ValueError("At most 24 bounded queues per invocation")
    job_id = job_id or datetime.now(UTC).strftime("%Y%m%dt%H%M%Sz_") + uuid.uuid4().hex[:8]
    if not re.fullmatch(r"[a-z0-9_]+", job_id):
        raise ValueError("Job identity")
    directory = ROOT / "outputs/reports/landscape/training_supervisor_v1" / job_id
    if (directory / "progress.json").exists():
        raise ValueError("Existing supervisor record retained; use a new job identity")
    pinned = runtime()
    begun = time.monotonic()
    deadline = begun + hours * 3600
    entries = {}
    report = {
        **selected,
        "version": VERSION,
        "job_id": job_id,
        "pid": os.getpid(),
        "status": "running",
        "started_at_utc": datetime.now(UTC).isoformat(),
        "hours_limit": hours,
        "batch_minutes_limit": batch_minutes,
        "max_batches": max_batches,
        "min_free_gib": min_free_gib,
        "runtime": pinned,
        "batches": [],
        "verified_months": [],
    }

    def publish():
        report["updated_at_utc"] = datetime.now(UTC).isoformat()
        report["elapsed_seconds"] = round(time.monotonic() - begun, 3)
        queue.save(directory / "progress.json", report)

    def live_progress(batch_directory, batch_report):
        if runtime() != pinned:
            raise ValueError("Code/grid/environment changed before acceptance")
        if not (
            set(r["month"] for r in batch_report["verified_months"])
            <= set(selected["selected_months"])
        ):
            raise ValueError("Batch month outside supervisor scope")
        for entry in batch_report["verified_months"]:
            previous = entries.get(entry["month"])
            if previous and previous["manifest_sha256"] != entry["manifest_sha256"]:
                raise ValueError("Previously verified month changed")
            entries[entry["month"]] = entry
        report["verified_months"] = [entries[key] for key in sorted(entries)]
        report["current_month"] = batch_report.get("current_month")
        report["active_batch_status"] = batch_report["status"]
        report["active_batch_report"] = (
            (batch_directory / "progress.json").relative_to(ROOT).as_posix()
        )
        publish()

    with supervisor_lock(job_id):
        directory.mkdir(parents=True, exist_ok=True)
        try:
            publish()
            for number in range(1, max_batches + 1):
                remaining = (deadline - time.monotonic()) / 60
                if remaining < 1:
                    report["status"] = "paused_overall_time_budget"
                    break
                if runtime() != pinned:
                    raise ValueError("Code/grid/environment changed; retained results")
                report["batch_number"] = number
                publish()
                print(f"SUPERVISOR BATCH {number}: automatic training continuation", flush=True)
                batch_report, batch_directory = queue.run(
                    start,
                    end,
                    max_new_months=72,
                    max_run_minutes=min(batch_minutes, remaining),
                    min_free_gib=min_free_gib,
                    on_progress=live_progress,
                )
                report["batches"].append(
                    {
                        "status": batch_report["status"],
                        "report": (batch_directory / "progress.json").relative_to(ROOT).as_posix(),
                        "report_sha256": queue.sha(batch_directory / "progress.json"),
                    }
                )
                status = batch_report["status"]
                if status == "selected_training_range_verified":
                    if set(entries) != set(selected["selected_months"]):
                        raise ValueError("Incomplete cumulative acceptance")
                    report["status"] = "selected_training_range_verified"
                    break
                if status not in {
                    "paused_time_budget",
                    "paused_time_budget_checkpoints_retained",
                    "paused_new_month_budget",
                }:
                    report["status"] = status
                    break
                publish()
            else:
                report["status"] = "paused_batch_count_budget"
        except KeyboardInterrupt:
            report["status"] = "interrupted_checkpoints_retained"
        except Exception as error:
            report["status"] = "failed_checkpoints_retained"
            report["error_type"] = type(error).__name__
        finally:
            publish()
    print(
        json.dumps(
            {
                "status": report["status"],
                "verified_months": len(report["verified_months"]),
                "selected_months": len(selected["selected_months"]),
                "report": (directory / "progress.json").relative_to(ROOT).as_posix(),
            },
            indent=2,
        ),
        flush=True,
    )
    return report, directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2018-01")
    parser.add_argument("--end", default="2023-12")
    parser.add_argument("--hours", type=float, default=24)
    parser.add_argument("--batch-minutes", type=float, default=240)
    parser.add_argument("--min-free-gib", type=float, default=10)
    parser.add_argument("--job-id")
    args = parser.parse_args()
    report, _ = run(
        args.start, args.end, args.hours, args.batch_minutes, args.min_free_gib, args.job_id
    )
    return int(report["status"] == "failed_checkpoints_retained")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"SUPERVISOR STOPPED: {type(error).__name__}; existing results retained", flush=True)
        raise SystemExit(1) from None
