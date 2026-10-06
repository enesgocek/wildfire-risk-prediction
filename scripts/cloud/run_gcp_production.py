"""Bounded full-training queue. No final labels, paid upgrades or automatic VM restarts."""

import argparse
import ast
import concurrent.futures
import contextlib
import datetime as dt
import getpass
import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

from gcp_production_support import (
    atomic_json,
    build_month,
    checked_spec,
    digest,
    json_bytes,
    month_names,
    owned_remove,
    pack_flat,
    read_scope,
    science,
    template,
    validate_month,
)
from production_drive_store import ProductionDriveStore
from verified_job_store import VerifiedJobStore, require

PACKAGE = Path(__file__).resolve().parent
WORK_NAME = "wildfire-gcp-production-v1"
TASK_TIMEOUT = 900
PUBLISH_RESERVE = 900
STOP_RESERVE = 900
MAX_RUNTIME = 24 * 3600  # First documented VM run is 8h; same package can later resume under 24h.
MIN_DISK = 6 * 2**30


def safe_guard(error):
    """Only literal guard labels from reviewed code may appear in public logs."""
    labels = {
        "Downloaded size differs",
        "Earthdata login failed",
        "Expected NASA filename not downloaded",
    }
    for name in (
        "run_gcp_production.py",
        "gcp_production_support.py",
        "verified_job_store.py",
        "drive_job_store.py",
        "production_drive_store.py",
    ):
        for node in ast.walk(ast.parse((PACKAGE / name).read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "require"
                and len(node.args) > 1
            ):
                label = node.args[1]
                if isinstance(label, ast.Constant) and isinstance(label.value, str):
                    labels.add(label.value)
    value = error.args[0] if len(error.args) == 1 else None
    return value if isinstance(value, str) and value in labels else "No external error text logged"


def discard_partial_sources(raw, pair):
    """Interrupted, wrong-length scratch files are never reused as NASA sources."""
    for source in pair["sources"]:
        target = raw / source["filename"]
        require(Path(source["filename"]).name == source["filename"], "Raw source basename")
        require(
            not target.is_symlink() and target.resolve().is_relative_to(raw.resolve()),
            "Raw source path",
        )
        if target.exists() and target.stat().st_size != source["bytes"]:
            target.unlink()


def deadline_seconds(value, now=None):
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "Actual VM deadline needs timezone")
    now = now or dt.datetime.now(dt.UTC)
    seconds = (parsed - now).total_seconds()
    require(2 * PUBLISH_RESERVE < seconds <= MAX_RUNTIME, "VM deadline must leave 30min to 24h")
    # Screenshot showed trial end 26 Oct; never run beyond the conservative earlier bound.
    trial_bound = dt.datetime(2026, 10, 24, tzinfo=dt.UTC)
    seconds = min(seconds, (trial_bound - now).total_seconds())
    require(seconds > 2 * PUBLISH_RESERVE, "Trial safety date reached")
    return seconds - STOP_RESERVE


def environment(credentials=None):
    result = os.environ.copy()
    for key in list(result):
        if key.startswith("EARTHDATA_") or key in {"PYTHONPATH", "PYTHONHOME"}:
            result.pop(key)
    result["PYTHONNOUSERSITE"] = "1"
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "GDAL_NUM_THREADS"):
        result[key] = "1"
    if credentials is not None:
        result["EARTHDATA_USERNAME"] = credentials["username"]
        result["EARTHDATA_PASSWORD"] = credentials["password"]
    return result


def ensure_root(root, template_root, metadata, pairs):
    require(not root.is_symlink(), "Production root symlink")
    if not root.exists():
        shutil.copytree(template_root, root)
    target = root / "production_metadata"
    target.mkdir(exist_ok=True)
    names = {
        Path(pair["metadata"][role]).name for pair in pairs for role in ("fire", "geolocation")
    }
    for name in names:
        source = metadata / name
        dest = target / source.name
        if dest.exists():
            require(dest.read_bytes() == source.read_bytes(), "Persisted metadata changed")
        else:
            shutil.copyfile(source, dest)


def pair_names(pair, native):
    return {f"{pair['stem']}_{suffix}" for suffix in (*native.SUFFIXES, "checkpoint.json")}


def cleanup_committed_task(work, sample_id):
    task = work / "tasks" / hashlib.sha256(sample_id.encode()).hexdigest()
    # Caller has independently verified the immutable remote completion first.
    if task.exists():
        owned_remove(task, work / "tasks")


def pair_checker(root, pair, month_sha, output):
    _, native = science(root)

    def check(path):
        native.restore_pair(path, pair, month_sha, output)
        require(
            native.checkpoint_read(pair, output, month_sha) is not None, "Pair scientific readback"
        )

    return native, check


def child_pair(args):
    if os.name == "posix":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (6 * 2**30, 6 * 2**30))
    root = args.root.resolve()
    plan = json.loads(args.plan.read_text())
    selected = [p for p in plan["pairs"] if p["sample_id"] == args.sample]
    require(len(selected) == 1, "Child pair identity")
    pair = selected[0]
    month_sha = digest(args.plan)
    _, native = science(root)
    native.OUTPUT = root / "summer/results"
    native.OUTPUT.mkdir(parents=True, exist_ok=True)
    raw = root / "summer/raw" / pair["stem"]
    started = time.monotonic()
    with (
        open(os.devnull, "w") as quiet,
        contextlib.redirect_stdout(quiet),
        contextlib.redirect_stderr(quiet),
    ):
        existing = native.checkpoint_read(pair, native.OUTPUT, month_sha)
        transferred = 0
        if existing is None:
            discard_partial_sources(raw, pair)
            transferred = native.download_pair(pair, raw)
            native.child_audit(pair, raw)
            native.compare_pair(pair, native.OUTPUT)
            memory = json.loads((native.OUTPUT / f"{pair['stem']}_memory.json").read_text())
            require(0 < memory["child_peak_rss_bytes"] < 6 * 2**30, "Worker RSS exceeds budget")
            record = {
                "sample_id": pair["sample_id"],
                "manifest_sha256": month_sha,
                "worker_sha256": digest(Path(native.__file__)),
                "outputs": {
                    f"{pair['stem']}_{s}": digest(native.OUTPUT / f"{pair['stem']}_{s}")
                    for s in native.SUFFIXES
                },
                "metrics": {
                    "elapsed_seconds": time.monotonic() - started,
                    "downloaded_payload_bytes": transferred,
                    **memory,
                },
            }
            atomic_json(native.OUTPUT / f"{pair['stem']}_checkpoint.json", record)
            require(
                native.checkpoint_read(pair, native.OUTPUT, month_sha) == record,
                "Child checkpoint readback",
            )
        pack_flat(native.OUTPUT, pair_names(pair, native), root / "pair.zip")
    atomic_json(
        root / "task_metrics.json",
        {
            "sample_id": pair["sample_id"],
            "seconds": time.monotonic() - started,
            "downloaded_payload_bytes": transferred,
        },
    )


def child_day(args):
    plan = json.loads(args.plan.read_text())
    pairs = [p for p in plan["pairs"] if p["start_utc"].startswith(args.day)]
    require(pairs, "No nominal pairs for daily union")
    compact, _ = science(args.root)
    lineage = {
        "production_month_manifest_sha256": digest(args.plan),
        "catalogue_gap_records": [
            r for r in plan["unpaired_catalogue_records"] if r["day"] == args.day
        ],
    }
    compact.reduce_day(
        args.day, pairs, args.root / "inputs", args.root / "daily", lineage, verify_geometry=True
    )
    pack_flat(args.root / "daily", compact.NAMES, args.root / "day.zip")


def run_child(kind, root, plan, value, credentials=None):
    failure = root / "failure.json"
    if failure.exists():
        failure.unlink()
    command = [
        sys.executable,
        str(PACKAGE / "run_gcp_production.py"),
        "--child",
        kind,
        "--root",
        str(root),
        "--plan",
        str(plan),
    ]
    command += ["--sample" if kind == "pair" else "--day", value]
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=environment(credentials),
    )
    try:
        code = process.wait(timeout=TASK_TIMEOUT)
        if code != 0:
            if failure.exists():
                record = json.loads(failure.read_text())
                guard = safe_guard(ValueError(record.get("guard")))
                print("Child failed:", kind, value, guard, flush=True)
            require(False, "Production child failed; scratch retained")
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise RuntimeError("Production child timeout; scratch retained") from None


def restore_daily(path, root, day, pairs, lineage):
    compact, _ = science(root)
    target = root / ("restored_" + day)
    target.mkdir(exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        require(set(archive.namelist()) == set(compact.NAMES), "Daily ZIP members")
        require(len(archive.namelist()) == len(compact.NAMES), "Daily duplicate members")
        require(archive.testzip() is None, "Daily CRC")
        for name in compact.NAMES:
            data = archive.read(name)
            dest = target / name
            if dest.exists():
                require(dest.read_bytes() == data, "Existing daily product changed")
            else:
                dest.write_bytes(data)
    return compact.validate_day(target, day, [p["sample_id"] for p in pairs], lineage)


def queue(args, work, credentials):
    spec, scope_sha, catalogue, sources = read_scope(PACKAGE)
    backend = ProductionDriveStore.from_file(args.connection)
    store = VerifiedJobStore(
        backend, scope_sha, spec["files"]["run_gcp_production.py"], 200_000_000_000
    )
    stop_at = time.monotonic() + deadline_seconds(args.termination)
    core = work / "core"
    template(PACKAGE, core)
    require(shutil.disk_usage(work).free >= MIN_DISK, "Insufficient scratch disk")
    backend.api.token()
    # Indexed lookup/quota initialization exercises actual Drive before any raw request.
    backend.used_bytes("jobs/" + scope_sha)
    progress = {
        "status": "running",
        "queue_manifest_sha256": scope_sha,
        "existing_months": ["2023-07"],
        "days_verified_this_invocation": [],
        "pairs_processed_this_invocation": 0,
        "pairs_reused_this_invocation": 0,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "actual_vm_termination_timestamp": args.termination,
        "four_worker_speedup_proven": False,
    }
    atomic_json(work / "progress.json", progress)
    initial_verified = False
    for month in spec["months"]:
        if time.monotonic() + TASK_TIMEOUT + PUBLISH_RESERVE >= stop_at:
            break
        rows = sources.loc[sources.day.str.startswith(month)]
        month_dir = work / "months" / month
        meta = month_dir / "metadata"
        month_dir.mkdir(parents=True, exist_ok=True)

        def metadata_check(path, month=month, rows=rows, meta=meta):
            return validate_month(path, month, rows, catalogue, meta)

        saved = store.restore("manifest:" + month, month_names(rows), metadata_check)
        if saved is None:
            print("Preparing verified metadata:", month, "sources:", len(rows), flush=True)
            cache = month_dir / "public_cache"
            cache.mkdir(exist_ok=True)
            build_month(month, rows, catalogue, cache, meta)
            pack_flat(meta, month_names(rows), month_dir / "manifest.zip")
            saved = store.save(
                "manifest:" + month, month_dir / "manifest.zip", month_names(rows), metadata_check
            )
        plan_path = meta / "month.json"
        plan = json.loads(plan_path.read_text())
        month_sha = digest(plan_path)
        monthly_archive = month_dir / "daily_archives"
        monthly_archive.mkdir(exist_ok=True)
        month_core = month_dir / "science"
        ensure_root(month_core, core, meta, plan["pairs"])
        receipt_names = {"receipt.json", *[day + ".zip" for day in plan["days"]]}

        def check_month_result(
            path,
            receipt_names=receipt_names,
            month_sha=month_sha,
            plan=plan,
            month_core=month_core,
            month=month,
        ):
            with zipfile.ZipFile(path) as archive:
                require(set(archive.namelist()) == receipt_names, "Monthly result members")
                require(len(archive.namelist()) == len(receipt_names), "Monthly result duplicate")
                require(archive.testzip() is None, "Monthly result CRC")
                receipt = json.loads(archive.read("receipt.json"))
                require(
                    receipt["month"] == month and receipt["daily_observation_status"] == "unknown",
                    "Monthly result identity/policy",
                )
                require(
                    set(receipt["day_records"]) == set(plan["days"]),
                    "Monthly completion record days",
                )
                require(receipt["month_manifest_sha256"] == month_sha, "Monthly result lineage")
                require(
                    receipt["days"] == plan["days"]
                    and receipt["negative_label_permitted"] is False,
                    "Monthly result days/policy",
                )
                require(
                    receipt["unpaired_catalogue_records"] == plan["unpaired_catalogue_records"],
                    "Monthly result gaps",
                )
                for d in plan["days"]:
                    record = receipt["day_records"][d]
                    require(
                        record["task_id"] == "day:" + d
                        and record["manifest_sha256"] == scope_sha
                        and record["worker_sha256"] == store.worker_sha,
                        "Monthly day completion identity",
                    )
                    require(
                        record["negative_label_permitted"] is False
                        and record["daily_observation_status"] == "unknown",
                        "Monthly day completion policy",
                    )
                    day_pairs = [p for p in plan["pairs"] if p["start_utc"].startswith(d)]
                    content = archive.read(d + ".zip")
                    require(
                        hashlib.sha256(content).hexdigest()
                        == receipt["day_records"][d]["payload_sha256"],
                        "Monthly nested day SHA",
                    )
                    with tempfile.TemporaryDirectory(dir=month_core) as temporary:
                        nested = Path(temporary) / "day.zip"
                        nested.write_bytes(content)
                        lineage = {
                            "production_month_manifest_sha256": month_sha,
                            "catalogue_gap_records": [
                                r for r in plan["unpaired_catalogue_records"] if r["day"] == d
                            ],
                        }
                        restore_daily(nested, month_core, d, day_pairs, lineage)
                    owned_remove(month_core / ("restored_" + d), month_core)

        month_prior = store.restore("month:" + month, receipt_names, check_month_result)
        if month_prior is not None:
            for pair in plan["pairs"]:
                cleanup_committed_task(work, pair["sample_id"])
            initial_verified = True
            progress["existing_months"].append(month)
            atomic_json(work / "progress.json", progress)
            owned_remove(month_core, month_dir)
            print("Month compact verified/reused:", month, flush=True)
            continue
        day_records = {}
        for day in plan["days"]:
            if time.monotonic() + TASK_TIMEOUT + PUBLISH_RESERVE >= stop_at:
                break
            pairs = [p for p in plan["pairs"] if p["start_utc"].startswith(day)]
            require(pairs, "Day has no nominal pair; catalogue review needed")
            dayroot = work / "days" / day
            ensure_root(dayroot, core, meta, pairs)
            lineage = {
                "production_month_manifest_sha256": month_sha,
                "catalogue_gap_records": [
                    r for r in plan["unpaired_catalogue_records"] if r["day"] == day
                ],
            }
            compact, _ = science(dayroot)

            def daily_check(
                path,
                dayroot=dayroot,
                day=day,
                pairs=pairs,
                lineage=lineage,
                monthly_archive=monthly_archive,
            ):
                result = restore_daily(path, dayroot, day, pairs, lineage)
                # Keep exact saved bytes for the independently checked monthly compact.
                shutil.copyfile(path, monthly_archive / (day + ".zip"))
                return result

            prior = store.restore("day:" + day, set(compact.NAMES), daily_check)
            if prior is not None:
                for pair in pairs:
                    cleanup_committed_task(work, pair["sample_id"])
                day_records[day] = prior
                initial_verified = True
                progress["days_verified_this_invocation"].append(day)
                atomic_json(work / "progress.json", progress)
                owned_remove(dayroot, work / "days")
                print("Day verified/reused:", day, flush=True)
                continue
            pending = []
            verified_ids = set()
            for pair in pairs:
                native, check = pair_checker(dayroot, pair, month_sha, dayroot / "inputs")
                record = store.restore(pair["sample_id"], pair_names(pair, native), check)
                if record is not None:
                    cleanup_committed_task(work, pair["sample_id"])
                    verified_ids.add(pair["sample_id"])
                    progress["pairs_reused_this_invocation"] += 1
                else:
                    pending.append(pair)
            workers = 4 if initial_verified else 2
            print(
                f"Production day {day}: pending {len(pending)}/{len(pairs)}, workers {workers}",
                flush=True,
            )
            # Small bounded waves leave time to publish all finished children.
            for start in range(0, len(pending), workers):
                if time.monotonic() + TASK_TIMEOUT + PUBLISH_RESERVE >= stop_at:
                    break
                wave = pending[start : start + workers]
                roots = {}
                wave_bytes = sum(s["bytes"] for p in wave for s in p["sources"])
                required_disk = MIN_DISK + wave_bytes + len(wave) * 300_000_000
                require(shutil.disk_usage(work).free >= required_disk, "Low disk; records retained")
                for pair in wave:
                    root = work / "tasks" / hashlib.sha256(pair["sample_id"].encode()).hexdigest()
                    ensure_root(root, core, meta, [pair])
                    roots[pair["sample_id"]] = root
                with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                    jobs = {
                        pool.submit(
                            run_child,
                            "pair",
                            roots[p["sample_id"]],
                            plan_path,
                            p["sample_id"],
                            credentials,
                        ): p
                        for p in wave
                    }
                    for future in concurrent.futures.as_completed(jobs):
                        pair = jobs[future]
                        future.result()
                        root = roots[pair["sample_id"]]
                        native, check = pair_checker(dayroot, pair, month_sha, dayroot / "inputs")
                        store.save(
                            pair["sample_id"], root / "pair.zip", pair_names(pair, native), check
                        )
                        verified_ids.add(pair["sample_id"])
                        progress["pairs_processed_this_invocation"] += 1
                        atomic_json(work / "progress.json", progress)
                        # Safe only after completed marker and independent readback.
                        _, child_native = science(root)
                        child_native.OUTPUT = root / "summer/results"
                        child_native.cleanup_pair(pair, root / "summer/raw" / pair["stem"])
                        owned_remove(root, work / "tasks")
                        print("Pair saved/verified:", pair["sample_id"], flush=True)
            complete = verified_ids == {p["sample_id"] for p in pairs}
            if not complete or time.monotonic() + TASK_TIMEOUT + PUBLISH_RESERVE >= stop_at:
                progress["status"] = "paused_at_runtime_reserve"
                atomic_json(work / "progress.json", progress)
                return
            run_child("day", dayroot, plan_path, day)
            day_records[day] = store.save(
                "day:" + day, dayroot / "day.zip", set(compact.NAMES), daily_check
            )
            progress["days_verified_this_invocation"].append(day)
            atomic_json(work / "progress.json", progress)
            initial_verified = True
            owned_remove(dayroot, work / "days")
            print(
                "DAY COMMITTED:", day, "observation unknown; negative labels forbidden", flush=True
            )
        if len(
            [d for d in progress["days_verified_this_invocation"] if d.startswith(month)]
        ) == len(plan["days"]):
            atomic_json(
                monthly_archive / "receipt.json",
                {
                    "month": month,
                    "month_manifest_sha256": month_sha,
                    "days": plan["days"],
                    "day_records": day_records,
                    "unpaired_catalogue_records": plan["unpaired_catalogue_records"],
                    "negative_label_permitted": False,
                    "daily_observation_status": "unknown",
                },
            )
            pack_flat(monthly_archive, receipt_names, month_dir / "month_results.zip")
            store.save(
                "month:" + month, month_dir / "month_results.zip", receipt_names, check_month_result
            )
            owned_remove(month_core, month_dir)
            progress["existing_months"].append(month)
            atomic_json(work / "progress.json", progress)
            print(
                "MONTH NOMINAL DIAGNOSTICS COMPLETE:",
                month,
                "unpaired records:",
                len(plan["unpaired_catalogue_records"]),
                flush=True,
            )
        else:
            break
    progress["status"] = "invocation_finished_no_automatic_restart"
    atomic_json(work / "progress.json", progress)


def vm_identity():
    expected = {
        "instance/name": "wildfire-cpu-pilot",
        "project/project-id": "dogalafetonlemesistemi",
        "instance/zone": "projects/493037734618/zones/europe-west3-c",
    }
    for field, value in expected.items():
        request = urllib.request.Request(
            "http://metadata.google.internal/computeMetadata/v1/" + field,
            headers={"Metadata-Flavor": "Google"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            require(response.read(512).decode().strip() == value, "Expected GCP VM identity")


def read_auth(fd):
    with os.fdopen(fd, "rb") as stream:
        data = stream.read(8193)
    require(0 < len(data) <= 8192, "Credential pipe bound")
    value = json.loads(data)
    require(set(value) == {"username", "password"}, "Credential pipe schema")
    require(
        all(isinstance(v, str) and 0 < len(v) <= 2048 for v in value.values()),
        "Credential pipe values",
    )
    return value


def supervise(args):
    import fcntl

    work = Path.home() / WORK_NAME
    work.mkdir(mode=0o700, exist_ok=True)
    require(not work.is_symlink(), "VM scratch root symlink")
    with (work / "job.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        credentials = read_auth(args.auth_fd)
        with (work / "launcher.log").open("ab") as log:
            read_fd, write_fd = os.pipe()
            command = [
                sys.executable,
                str(PACKAGE / "run_gcp_production.py"),
                "--queue",
                "--connection",
                str(args.connection),
                "--termination",
                args.termination,
                "--auth-fd",
                str(read_fd),
            ]
            proc = subprocess.Popen(
                command,
                pass_fds=(read_fd,),
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                env=environment(),
            )
            os.close(read_fd)
            os.write(write_fd, json_bytes(credentials))
            os.close(write_fd)
            try:
                code = proc.wait(timeout=deadline_seconds(args.termination) + 120)
                print("Queue invocation exit:", code, flush=True)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                print("Runtime reserve reached; saved checkpoints retained", flush=True)
        if args.poweroff:
            # Guest shutdown, never resource deletion/restart/billing mutation.
            result = subprocess.run(
                ["sudo", "-n", "shutdown", "-h", "now"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
            print("Guest poweroff requested:", result.returncode == 0, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--connection", type=Path)
    parser.add_argument("--termination")
    parser.add_argument("--auth-fd", type=int)
    parser.add_argument("--supervise", action="store_true")
    parser.add_argument("--queue", action="store_true")
    parser.add_argument("--poweroff", action="store_true")
    parser.add_argument("--child", choices=["pair", "day"])
    parser.add_argument("--root", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--sample")
    parser.add_argument("--day")
    args = parser.parse_args()
    checked_spec(PACKAGE)
    if args.child:
        try:
            (child_pair if args.child == "pair" else child_day)(args)
        except Exception as error:
            atomic_json(
                args.root / "failure.json",
                {
                    "stage": args.child,
                    "error_type": type(error).__name__,
                    "guard": safe_guard(error),
                },
            )
            raise
        return
    require(
        platform.system() == "Linux" and platform.machine() == "x86_64", "Ubuntu x86_64 required"
    )
    require(
        sys.version_info[:2] == (3, 12) and sys.prefix != sys.base_prefix,
        "Existing Python 3.12 venv required",
    )
    require(
        args.connection is not None and args.termination,
        "Connection and actual VM deadline required",
    )
    if args.queue:
        credentials = read_auth(args.auth_fd)
        queue(args, Path.home() / WORK_NAME, credentials)
        return
    if args.supervise:
        supervise(args)
        return
    vm_identity()
    require(os.cpu_count() >= 8, "Expected eight-vCPU machine")
    require(
        os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") >= 24 * 2**30, "Expected VM RAM"
    )
    deadline_seconds(args.termination)
    ProductionDriveStore.from_file(args.connection).api.token()
    require(
        subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0,
        "Venv dependency check",
    )
    import rasterio

    with rasterio.Env() as env:
        require("HDF5" in env.drivers(), "HDF5 driver required")
    if args.poweroff:
        require(
            subprocess.run(
                ["sudo", "-n", "true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).returncode
            == 0,
            "Guest Stop privilege unavailable",
        )
    work = Path.home() / WORK_NAME
    work.mkdir(mode=0o700, exist_ok=True)
    require(shutil.disk_usage(work).free >= MIN_DISK, "Insufficient VM disk")
    print("Gizli girişte yazdıkların görünmez; yazıp Enter'a bas. Bilgiler diske kaydedilmez.")
    credentials = {
        "username": getpass.getpass("Earthdata kullanıcı adı (gizli): "),
        "password": getpass.getpass("Earthdata parola (gizli): "),
    }
    require(
        all(isinstance(v, str) and 0 < len(v) <= 2048 for v in credentials.values()),
        "Earthdata credentials required",
    )
    read_fd, write_fd = os.pipe()
    command = [
        sys.executable,
        str(PACKAGE / "run_gcp_production.py"),
        "--supervise",
        "--connection",
        str(args.connection.resolve()),
        "--termination",
        args.termination,
        "--auth-fd",
        str(read_fd),
    ] + (["--poweroff"] if args.poweroff else [])
    with (work / "supervisor.log").open("ab") as log:
        proc = subprocess.Popen(
            command,
            pass_fds=(read_fd,),
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            env=environment(),
        )
    os.close(read_fd)
    os.write(write_fd, json_bytes(credentials))
    os.close(write_fd)
    print("Detached production launch requested; PID:", proc.pid)
    print("Progress:", work / "launcher.log")


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except Exception as error:
        # Arbitrary network/parser messages can contain credentials. Never print them.
        print(
            "Production stopped:",
            type(error).__name__,
            safe_guard(error),
            "; scratch/checkpoints retained",
            flush=True,
        )
        if "--queue" in sys.argv:
            progress_path = Path.home() / WORK_NAME / "progress.json"
            if progress_path.exists():
                progress = json.loads(progress_path.read_text())
                progress["status"] = "failed_checkpoints_retained"
                progress["error_type"] = type(error).__name__
                progress["guard"] = safe_guard(error)
                atomic_json(progress_path, progress)
        raise SystemExit(1) from None
