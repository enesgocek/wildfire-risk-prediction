"""Finite, resumable 2021-2024 download -> prepare -> audit run.

Years advance only after their audit passes. Independent months download in at
most three processes. Only transient network failures are retried. No scheduler,
background service, label generation, final-test access or automatic Git push.
"""

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "outputs/logs/meteorology"
STATE = ROOT / "outputs/reports/meteorology/remaining_years_run.json"
MET = ROOT / "scripts/meteorology/prepare_era5_land.py"
AUDIT = ROOT / "scripts/quality/audit_project.py"


def year_windows(first, last):
    if not 2021 <= first <= last <= 2024:
        raise ValueError("Only remaining years 2021-2024; final test is sealed.")
    return [(f"{y}-01-01", f"{y + 1}-01-01") for y in range(first, last + 1)]


def month_windows(year):
    if not 2021 <= year <= 2024:
        raise ValueError("Only 2021-2024 download months are allowed.")
    return [
        (f"{year}-{m:02d}-01", f"{year}-{m + 1:02d}-01" if m < 12 else f"{year + 1}-01-01")
        for m in range(1, 13)
    ]


def transient_failure(text):
    markers = [
        "TimeoutError:",
        "URLError:",
        "ConnectionResetError:",
        "ConnectionAbortedError:",
        "RemoteDisconnected:",
        "HTTP Error 429",
        "HTTP Error 500",
        "HTTP Error 502",
        "HTTP Error 503",
        "HTTP Error 504",
        "Too many concurrent aggregations",
        "ServiceUnavailable:",
        "ConnectionError:",
    ]
    return any(marker in text for marker in markers)


def stage(command, label, retry=False):
    path = LOGS / (label + ".log")
    for attempt in range(1, 6 if retry else 2):
        with path.open("a", encoding="utf-8") as log:
            log.write(f"\nAttempt {attempt} at {datetime.now(UTC).isoformat()}\n")
            log.flush()
            result = subprocess.run(
                command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=False
            )
        if result.returncode == 0:
            return str(path.relative_to(ROOT))
        tail = path.read_text(encoding="utf-8", errors="replace")[-16000:]
        # Ignore errors from an earlier attempt if a later failure has another cause.
        tail = tail.rsplit(f"Attempt {attempt} at ", 1)[-1]
        if not retry or attempt == 5 or not transient_failure(tail):
            raise RuntimeError(f"{label} failed (exit {result.returncode}); inspect {path}")
        delay = min(5 * 2 ** (attempt - 1), 45)
        print(f"Transient failure: {label}; retry in {delay}s", flush=True)
        time.sleep(delay)


def save(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(".part")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(STATE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first-year", type=int, default=2021)
    parser.add_argument("--last-year", type=int, default=2024)
    parser.add_argument("--workers", type=int, choices=[1, 2, 3], default=3)
    args = parser.parse_args()
    windows = year_windows(args.first_year, args.last_year)  # Before any subprocess.
    predecessor = args.first_year - 1
    previous = (
        ROOT
        / "outputs/reports/quality"
        / (f"project_audit_{predecessor}-01-01_{predecessor + 1}-01-01.json")
    )
    prerequisite = json.loads(previous.read_text(encoding="utf-8"))
    if prerequisite["errors"] or prerequisite["status"] != "passed_with_open_gates":
        raise ValueError("The preceding year's audit must pass before continuing.")
    LOGS.mkdir(parents=True, exist_ok=True)
    state = {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "status": "running",
        "requested_years": list(range(args.first_year, args.last_year + 1)),
        "workers": args.workers,
        "completed_years": [],
        "current_year": None,
        "stage": None,
        "final_test_accessed": False,
        "processing_script_sha256": hashlib.sha256(MET.read_bytes()).hexdigest(),
    }
    save(state)
    try:
        for start, end in windows:
            year = int(start[:4])
            state.update(current_year=year, stage="download")
            save(state)
            print(f"YEAR {year}: download", flush=True)
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = {
                    pool.submit(
                        stage,
                        [sys.executable, "-u", str(MET), "download", "--start", a, "--end", b],
                        f"download_{a}_{b}",
                        True,
                    ): a
                    for a, b in month_windows(year)
                }
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception:
                        for pending in futures:
                            pending.cancel()
                        raise
                    print(f"MONTH {futures[future][:7]}: downloaded and verified", flush=True)
            state["stage"] = "prepare"
            save(state)
            print(f"YEAR {year}: prepare", flush=True)
            stage(
                [sys.executable, "-u", str(MET), "prepare", "--start", start, "--end", end],
                f"prepare_{start}_{end}",
            )
            state["stage"] = "audit"
            save(state)
            print(f"YEAR {year}: audit", flush=True)
            stage(
                [sys.executable, "-u", str(AUDIT), "--weather-start", start, "--weather-end", end],
                f"audit_{start}_{end}",
            )
            report_path = ROOT / "outputs/reports/quality" / f"project_audit_{start}_{end}.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            if report["errors"] or report["status"] != "passed_with_open_gates":
                raise ValueError(f"{year}: audit did not pass.")
            state["completed_years"].append(
                {
                    "year": year,
                    "rows": report["checks"]["meteorology"]["total_rows"],
                    "audit": str(report_path.relative_to(ROOT)),
                }
            )
            save(state)
            print(f"YEAR {year}: COMPLETE", flush=True)
        state.update(
            status="complete", stage="finished", finished_at_utc=datetime.now(UTC).isoformat()
        )
        save(state)
        print("Remaining years complete; control returns to the user.", flush=True)
    except Exception as error:
        state.update(status="failed", error_type=type(error).__name__, error=str(error))
        save(state)
        raise


if __name__ == "__main__":
    main()
