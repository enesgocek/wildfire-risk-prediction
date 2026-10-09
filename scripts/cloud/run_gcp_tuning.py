"""4/8/12/4 matched cold profiles on the existing VM; original production remains immutable."""

import argparse
import concurrent.futures
import contextlib
import datetime as dt
import getpass
import hashlib
import importlib
import json
import os
import signal
import statistics
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path

from gcp_tuning_resources import Sampler

ORIGINAL_SCOPE = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
ARMS = (("four_before", 4), ("eight", 8), ("twelve", 12), ("four_after", 4))
PACKAGE = Path(__file__).resolve().parent
ORIGINAL = Path.home() / "wildfire-gcp-production-package"
WORK = Path.home() / "wildfire-gcp-tuning-v1"
PRODUCTION = Path.home() / "wildfire-gcp-production-v1"
EXPORT = Path.home() / "gcp_tuning_results.zip"
CHILD_LIMIT = 900
ACTIVE = {}
ACTIVE_LOCK = threading.Lock()


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def atomic(path, value):
    data = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    pending = path.with_suffix(".pending")
    pending.write_bytes(data)
    pending.replace(path)


def checked_package():
    path = PACKAGE / "tuning_manifest.json"
    spec = json.loads(path.read_text())
    require(spec["protocol"] == "gcp_parallel_tuning_v1", "Tuning protocol")
    require(spec["arms"] == [[a, n] for a, n in ARMS], "Fixed tuning arms")
    require(spec["negative_label_permitted"] is False, "Tuning policy")
    require(
        set(spec["files"])
        == {
            "run_gcp_tuning.py",
            "gcp_tuning_resources.py",
            "tuning_plan.json",
            "month_manifest.zip",
        },
        "Tuning files",
    )
    for name, checksum in spec["files"].items():
        target = PACKAGE / name
        require(not target.is_symlink() and sha(target) == checksum, "Tuning member SHA")
    original_manifest = ORIGINAL / "production_manifest.json"
    require(sha(original_manifest) == ORIGINAL_SCOPE, "Original production scope")
    original = json.loads(original_manifest.read_text())
    for name, checksum in original["files"].items():
        require(Path(name).name == name and "\\" not in name, "Original file path")
        target = ORIGINAL / name
        require(not target.is_symlink() and sha(target) == checksum, "Original production SHA")
    require(len(original["files"]) == 11, "Original file count")
    sys.path.insert(0, str(ORIGINAL))
    return spec, sha(path), importlib.import_module("run_gcp_production")


@contextlib.contextmanager
def production_lock():
    import fcntl

    path = PRODUCTION / "job.lock"
    require(path.is_file() and not path.is_symlink(), "Original job lock required")
    with path.open("r+") as file:
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def remaining_seconds(value, now=None):
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "Google deadline timezone")
    now = now or dt.datetime.now(dt.UTC)
    seconds = (parsed - now).total_seconds()
    require(4200 <= seconds <= 7260, "Use new two-hour VM deadline; at least 70min remaining")
    require(parsed < dt.datetime(2026, 10, 24, tzinfo=dt.UTC), "Trial safety bound")
    return min(5400, seconds - 900)  # 90min benchmark; preserve 15min for export/Stop.


def install_alarm(deadline):
    """Main-thread watchdog also interrupts a stalled Drive request or metadata setup."""
    previous = signal.getsignal(signal.SIGALRM)

    def expired(signum, frame):
        raise TimeoutError("Tuning active budget reached")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, deadline - time.monotonic()))

    def cancel():
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)

    return cancel


def kill_active():
    with ACTIVE_LOCK:
        for process in list(ACTIVE.values()):
            if process.poll() is None:
                try:
                    if os.getpgid(process.pid) == process.pid:
                        os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


def run_child(runner, kind, root, plan, value, auth, deadline, sampler):
    command = [
        sys.executable,
        str(ORIGINAL / "run_gcp_production.py"),
        "--child",
        kind,
        "--root",
        str(root),
        "--plan",
        str(plan),
        "--sample" if kind == "pair" else "--day",
        value,
    ]
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=runner.environment(auth),
    )
    with ACTIVE_LOCK:
        ACTIVE[process.pid] = process
    try:
        while process.poll() is None:
            if sampler.failed or time.monotonic() >= min(deadline, started + CHILD_LIMIT):
                try:
                    if os.getpgid(process.pid) == process.pid:
                        os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=30)
                require(False, "Child resource/deadline guard")
            time.sleep(0.25)
        require(process.returncode == 0, "Frozen scientific child failed")
        return time.monotonic() - started
    except BaseException:
        # A child leader may exit while its audit subprocess still occupies our own group.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        raise
    finally:
        with ACTIVE_LOCK:
            ACTIVE.pop(process.pid, None)


def pair_check(runner, root, pair, month_sha, reference):
    native, original_check = runner.pair_checker(root, pair, month_sha, root / "inputs")

    def check(path):
        original_check(path)
        inputs = root / "inputs"
        record = json.loads((inputs / (pair["stem"] + "_checkpoint.json")).read_text())
        require(record is not None, "Scientific checkpoint")
        require(
            record["metrics"]["downloaded_payload_bytes"]
            == sum(s["bytes"] for s in pair["sources"]),
            "Cold source download required",
        )
        audit = json.loads((inputs / (pair["stem"] + "_audit.json")).read_text())
        for role, expected in reference["source_sha256"].items():
            require(audit["sources"][role]["sha256"] == expected, "Original raw source SHA differs")
        for suffix, expected in reference["exact_csv_sha256"].items():
            require(
                sha(inputs / (pair["stem"] + "_" + suffix)) == expected,
                "Native counts/scan CSV differs from verified production",
            )
        return record

    return native, check


def execute_arm(
    arm,
    workers,
    runner,
    core,
    meta,
    plan_path,
    plan,
    selected,
    references,
    store,
    auth,
    deadline,
    sampler,
):
    sampler.arm, sampler.phase = arm, "pairs_and_publication"
    started = time.monotonic()
    root = WORK / arm
    require(not root.exists(), "Cold profile requires fresh work root")
    root.mkdir()
    month_sha = sha(plan_path)
    dayroots = {}
    for day in ("2023-10-13", "2023-10-14", "2023-10-15"):
        pairs = [p for p in selected if p["start_utc"].startswith(day)]
        dayroot = root / day
        runner.ensure_root(dayroot, core, meta, pairs)
        dayroots[day] = dayroot
    records, publication = [], 0.0
    iterator = iter(selected)
    tasks = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:

        def submit(pair):
            require(
                not sampler.failed and time.monotonic() + CHILD_LIMIT < deadline,
                "Profile cannot safely admit another child",
            )
            childroot = root / ("pair_" + hashlib.sha256(pair["sample_id"].encode()).hexdigest())
            runner.ensure_root(childroot, core, meta, [pair])
            future = pool.submit(
                run_child,
                runner,
                "pair",
                childroot,
                plan_path,
                pair["sample_id"],
                auth,
                deadline,
                sampler,
            )
            tasks[future] = (pair, childroot)

        for _ in range(min(workers, len(selected))):
            submit(next(iterator))
        try:
            while tasks:
                done, _ = concurrent.futures.wait(
                    tasks, timeout=2, return_when=concurrent.futures.FIRST_COMPLETED
                )
                require(not sampler.failed and time.monotonic() < deadline, "Profile guard reached")
                for future in done:
                    pair, childroot = tasks.pop(future)
                    child_seconds = future.result()
                    # Refill before serial publishing, so remaining workers can keep doing science.
                    next_pair = next(iterator, None)
                    if next_pair is not None:
                        submit(next_pair)
                    dayroot = dayroots[pair["start_utc"][:10]]
                    native, check = pair_check(
                        runner, dayroot, pair, month_sha, references[pair["sample_id"]]
                    )
                    publish_start = time.monotonic()
                    marker = store.save(
                        arm + ":" + pair["sample_id"],
                        childroot / "pair.zip",
                        runner.pair_names(pair, native),
                        check,
                    )
                    publication += time.monotonic() - publish_start
                    checkpoint = json.loads(
                        (dayroot / "inputs" / (pair["stem"] + "_checkpoint.json")).read_text()
                    )
                    records.append(
                        {
                            "sample_id": pair["sample_id"],
                            "child_wall_seconds": child_seconds,
                            "metrics": checkpoint["metrics"],
                            "completion": marker,
                        }
                    )
                    runner.owned_remove(childroot, root)
                    print(f"{arm}: pair saved/verified {len(records)}/{len(selected)}", flush=True)
        except BaseException:
            kill_active()
            raise
    days = []
    for day, dayroot in dayroots.items():
        require(
            time.monotonic() + CHILD_LIMIT < deadline and not sampler.failed,
            "Daily profile reserve reached",
        )
        sampler.phase = "daily_union"
        reduce_start = time.monotonic()
        run_child(runner, "day", dayroot, plan_path, day, None, deadline, sampler)
        reduce_seconds = time.monotonic() - reduce_start
        pairs = [p for p in selected if p["start_utc"].startswith(day)]
        compact, _ = runner.science(dayroot)
        context = {
            "production_month_manifest_sha256": month_sha,
            "catalogue_gap_records": [
                r for r in plan["unpaired_catalogue_records"] if r["day"] == day
            ],
        }

        def check(path, dayroot=dayroot, day=day, pairs=pairs, context=context):
            return runner.restore_daily(path, dayroot, day, pairs, context)

        sampler.phase = "daily_publication"
        publish_start = time.monotonic()
        marker = store.save(arm + ":day:" + day, dayroot / "day.zip", set(compact.NAMES), check)
        publish_seconds = time.monotonic() - publish_start
        publication += publish_seconds
        target = root / (day + ".zip")
        target.write_bytes((dayroot / "day.zip").read_bytes())
        days.append(
            {
                "day": day,
                "reduce_seconds": reduce_seconds,
                "publish_seconds": publish_seconds,
                "completion": marker,
            }
        )
        runner.owned_remove(dayroot, root)
    result = {
        "arm": arm,
        "workers": workers,
        "pair_count": len(records),
        "day_count": len(days),
        "wall_seconds": time.monotonic() - started,
        "pair_publication_seconds": publication - sum(d["publish_seconds"] for d in days),
        "total_publication_seconds": publication,
        "pairs": records,
        "days": days,
        "resources": sampler.summary(arm),
    }
    result["pairs_per_hour"] = len(records) * 3600 / result["wall_seconds"]
    atomic(root / "arm_summary.json", result)
    return result


def collect_export(summary):
    atomic(WORK / "result_summary.json", summary)
    pending = EXPORT.with_suffix(".pending")
    with zipfile.ZipFile(pending, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ("result_summary.json", "resource_samples.csv"):
            archive.write(WORK / name, name)
        for name in ("tuning_manifest.json", "tuning_plan.json", "month_manifest.zip"):
            archive.write(PACKAGE / name, name)
        for arm, _ in ARMS:
            directory = WORK / arm
            for path in sorted(directory.glob("*.zip")):
                archive.write(path, f"{arm}/{path.name}")
            if (directory / "arm_summary.json").is_file():
                archive.write(directory / "arm_summary.json", f"{arm}/arm_summary.json")
    require(pending.stat().st_size < 150_000_000, "Export size bound")
    pending.replace(EXPORT)


def study(args, auth):
    spec, scope, runner = checked_package()
    require(
        not WORK.exists() and not EXPORT.exists(), "Existing tuning run; do not repeat cold test"
    )
    duration = remaining_seconds(args.termination)
    deadline = time.monotonic() + duration  # Includes setup, not only timed arms.
    with production_lock():
        args.shutdown_allowed = True
        old_progress = sha(PRODUCTION / "progress.json")
        WORK.mkdir(mode=0o700)
        sampler = Sampler(WORK)
        sampler.begin()
        arms = []
        summary = {
            "status": "running",
            "tuning_scope_sha256": scope,
            "original_production_scope_sha256": ORIGINAL_SCOPE,
            "actual_vm_termination_timestamp": args.termination,
            "arms": arms,
            "negative_label_permitted": False,
            "daily_observation_status": "unknown",
            "production_months_added": 0,
        }
        cancel_alarm = None
        try:
            cancel_alarm = install_alarm(deadline)
            _, _, catalogue, sources = runner.read_scope(ORIGINAL)
            meta = WORK / "metadata"
            plan = runner.validate_month(
                PACKAGE / "month_manifest.zip",
                "2023-10",
                sources.loc[sources.day.str.startswith("2023-10")],
                catalogue,
                meta,
            )
            require(
                sha(meta / "month.json") == spec["production_month_manifest_sha256"],
                "Original October metadata changed",
            )
            approved = json.loads((PACKAGE / "tuning_plan.json").read_text())
            ids = approved["sample_ids"]
            selected = [p for p in plan["pairs"] if p["sample_id"] in set(ids)]
            require(len(ids) == len(set(ids)) == len(selected) == 28, "Matched 28-pair population")
            expected = [
                p["sample_id"] for p in plan["pairs"] if p["start_utc"][:10] in approved["days"]
            ]
            require([p["sample_id"] for p in selected] == ids == expected, "Full three-day scope")
            require(set(approved["references"]) == set(ids), "Reference population")
            source_bytes = sum(s["bytes"] for p in selected for s in p["sources"])
            require(
                source_bytes * len(ARMS) == spec["nominal_raw_download_bytes"], "Cold byte scope"
            )
            require(
                __import__("shutil").disk_usage(WORK).free > source_bytes + 8 * 2**30,
                "Disk budget for all selected sources",
            )
            core = WORK / "core"
            runner.template(ORIGINAL, core)
            backend = runner.ProductionDriveStore.from_file(args.connection)
            backend.api.token()
            quota = json.loads(backend.api.request("/about?fields=storageQuota(limit,usage)"))[
                "storageQuota"
            ]
            require(
                "limit" not in quota or int(quota["limit"]) - int(quota["usage"]) > 3 * 2**30,
                "Drive test quota reserve",
            )
            require(
                backend.used_bytes("jobs/" + scope) == 0,
                "Previous benchmark namespace; refuse reuse",
            )
            store = runner.VerifiedJobStore(
                backend, scope, spec["files"]["run_gcp_tuning.py"], 2 * 2**30
            )
            for arm, workers in ARMS:
                require(
                    time.monotonic() + 1500 < deadline and not sampler.failed,
                    "Not enough reserve for next profile",
                )
                print("PROFILE START", arm, "workers", workers, flush=True)
                result = execute_arm(
                    arm,
                    workers,
                    runner,
                    core,
                    meta,
                    meta / "month.json",
                    plan,
                    selected,
                    approved["references"],
                    store,
                    auth,
                    deadline,
                    sampler,
                )
                arms.append(result)
                print("PROFILE COMPLETE", arm, round(result["wall_seconds"], 2), flush=True)
                atomic(WORK / "progress.json", {"completed_arms": [r["arm"] for r in arms]})
            drift = arms[-1]["wall_seconds"] / arms[0]["wall_seconds"]
            baseline = statistics.mean([arms[0]["wall_seconds"], arms[-1]["wall_seconds"]])
            summary.update(
                status="all_profiles_completed",
                baseline_repeat_ratio=drift,
                baseline_stable=0.8 <= drift <= 1.25,
                speedup_vs_mean_four={r["arm"]: baseline / r["wall_seconds"] for r in arms[1:3]},
                raw_downloaded_bytes=source_bytes * len(arms),
                peak_sampled_resource_limit_hit=sampler.failed,
            )
        except Exception as error:
            kill_active()
            summary.update(
                status="partial_test_retained",
                error_type=type(error).__name__,
                failed_arm=sampler.arm,
                failed_phase=sampler.phase,
                remaining_profiles_not_completed=True,
            )
            print("Test stopped safely:", type(error).__name__, flush=True)
        finally:
            if cancel_alarm is not None:
                cancel_alarm()
            sampler.close()
            summary["production_progress_unchanged"] = (
                sha(PRODUCTION / "progress.json") == old_progress
            )
            summary["peak_sampled_resource_limit_hit"] = sampler.failed
            if not summary["production_progress_unchanged"] or sampler.failed:
                summary["status"] = "partial_test_retained"
            checked_package()
            collect_export(summary)
            print("Download:", EXPORT, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connection", type=Path, required=True)
    parser.add_argument("--termination", required=True)
    parser.add_argument("--poweroff", action="store_true")
    parser.add_argument("--supervise", action="store_true")
    parser.add_argument("--auth-fd", type=int)
    args = parser.parse_args()
    _, _, runner = checked_package()
    require(
        sys.platform == "linux" and sys.version_info[:2] == (3, 12), "Existing Linux Python 3.12"
    )
    runner.vm_identity()
    require(os.cpu_count() == 8, "Use existing eight-vCPU VM for matched test")
    require(sys.prefix != sys.base_prefix, "Use existing virtual environment")
    from gcp_tuning_resources import memory_values

    require(memory_values(Path("/proc/meminfo").read_text())[0] >= 24 * 2**30, "VM RAM")
    if args.supervise:
        args.shutdown_allowed = False
        auth = runner.read_auth(args.auth_fd)
        try:
            study(args, auth)
        finally:
            kill_active()
            if args.poweroff and args.shutdown_allowed:
                result = subprocess.run(
                    ["sudo", "-n", "shutdown", "-h", "now"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=30,
                )
                print("Guest poweroff requested:", result.returncode == 0, flush=True)
        return
    remaining_seconds(args.termination)
    require(args.connection.is_file() and not args.connection.is_symlink(), "Private connection")
    require(
        subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
        ).returncode
        == 0,
        "Existing dependencies",
    )
    require(not WORK.exists() and not EXPORT.exists(), "Existing test outputs; do not rerun")
    with production_lock():
        pass
    require(
        subprocess.run(
            ["sudo", "-n", "true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode
        == 0,
        "Guest shutdown privilege",
    )
    auth = {
        "username": getpass.getpass("Earthdata kullanıcı adı (gizli): "),
        "password": getpass.getpass("Earthdata parola (gizli): "),
    }
    require(
        all(isinstance(v, str) and 0 < len(v) <= 2048 for v in auth.values()),
        "Credentials required",
    )
    read_fd, write_fd = os.pipe()
    command = [
        sys.executable,
        str(Path(__file__)),
        "--supervise",
        "--connection",
        str(args.connection),
        "--termination",
        args.termination,
        "--auth-fd",
        str(read_fd),
    ]
    if args.poweroff:
        command.append("--poweroff")
    with (Path.home() / "gcp_tuning_launcher.log").open("ab") as log:
        process = subprocess.Popen(
            command,
            pass_fds=(read_fd,),
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            env=runner.environment(),
        )
    os.close(read_fd)
    os.write(write_fd, json.dumps(auth).encode())
    os.close(write_fd)
    print("Detached tuning launch requested; PID:", process.pid)
    print("Progress:", Path.home() / "gcp_tuning_launcher.log")


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except Exception as error:
        print("Tuning failed:", type(error).__name__, "; no credentials logged", flush=True)
        raise SystemExit(1) from None
