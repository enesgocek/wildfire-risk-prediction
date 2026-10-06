"""Small real-product persistence gate, not a new production month.

Detached supervisor owns a bounded child process group; no NASA login/download.
Save and restore run in distinct Python processes and fresh science directories.
"""

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from drive_job_store import DriveJobStore
from verified_job_store import RehearsalFileStore, VerifiedJobStore, require

PACKAGE = Path(__file__).resolve().parent
WORK_NAME = "wildfire-gcp-drive-proof-v2"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spec_read():
    spec = json.loads((PACKAGE / "proof_manifest.json").read_text())
    require(spec["protocol"] == "gcp_drive_real_pair_proof_v1", "Proof protocol")
    require(spec["negative_label_permitted"] is False, "Proof label policy")
    require(spec["raw_downloads"] == 0, "Proof scope")
    expected = {
        "summer.zip",
        "pair.zip",
        "run_gcp_benchmark.py",
        "verified_job_store.py",
        "drive_job_store.py",
        "run_gcp_drive_proof.py",
        "diagnose_gcp_drive_proof.py",
    }
    require(set(spec["files"]) == expected, "Proof file set")
    for name, checksum in spec["files"].items():
        require(digest(PACKAGE / name) == checksum, "Proof package changed")
    return spec


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def phase(kind, work, connection=None, local_store=None):
    spec = spec_read()
    native = load("proof_unpack", PACKAGE / "run_gcp_benchmark.py")
    checks = 0
    work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work) as directory:
        fresh = Path(directory)
        native.unpack(PACKAGE / "summer.zip", fresh / "native")
        science = native.load_summer(fresh / "native")
        manifest, manifest_sha = science.manifest_read()
        selected = [p for p in manifest["pairs"] if p["sample_id"] == spec["sample_id"]]
        require(len(selected) == 1, "Proof pair identity")
        pair = selected[0]
        names = {f"{pair['stem']}_{s}" for s in (*science.SUFFIXES, "checkpoint.json")}

        def scientific_check(path):
            nonlocal checks
            with tempfile.TemporaryDirectory(dir=fresh) as target:
                out = Path(target) / "products"
                science.restore_pair(path, pair, manifest_sha, out)
                require(science.checkpoint_read(pair, out, manifest_sha), "Science checkpoint")
            checks += 1

        backend = (
            RehearsalFileStore(local_store)
            if local_store is not None
            else DriveJobStore.from_file(connection)
        )
        job = VerifiedJobStore(
            backend,
            digest(PACKAGE / "proof_manifest.json"),
            spec["files"]["verified_job_store.py"],
            20_000_000,
        )
        task = pair["sample_id"]
        existing = job.restore(task, names, scientific_check)
        interrupted = False
        if kind == "save" and existing is None:
            create = backend.create

            def fail_before_marker(key, data):
                if key.endswith("completed.json"):
                    raise InterruptedError("Deliberate proof interruption")
                return create(key, data)

            backend.create = fail_before_marker
            try:
                job.save(task, PACKAGE / "pair.zip", names, scientific_check)
            except InterruptedError:
                interrupted = True
            finally:
                backend.create = create
            require(interrupted, "Interruption not exercised")
            require(job.restore(task, names, scientific_check) is None, "Orphan counted complete")
            record = job.save(task, PACKAGE / "pair.zip", names, scientific_check)
        else:
            require(existing is not None, "Saved completion missing")
            record = existing
        require(record["payload_sha256"] == spec["files"]["pair.zip"], "Proof product changed")
    report = {
        "phase": kind,
        "status": "passed",
        "sample_id": task,
        "manifest_sha256": digest(PACKAGE / "proof_manifest.json"),
        "payload_sha256": record["payload_sha256"],
        "payload_bytes": record["payload_bytes"],
        "scientific_readbacks": checks,
        "interruption_exercised": interrupted,
        "existing_completion_reused": existing is not None,
        "process_id": os.getpid(),
        "filesystem_only": local_store is not None,
        "negative_label_permitted": False,
        "raw_downloads": 0,
    }
    (work / f"{kind}.json").write_text(json.dumps(report, indent=2) + "\n")


def parse_deadline(value, now=None):
    now = now or dt.datetime.now(dt.UTC)
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "terminationTimestamp requires timezone")
    remaining = (parsed - now).total_seconds()
    require(900 < remaining <= 7200, "Actual VM deadline must leave 15 minutes to 2 hours")
    # Leave five minutes before Google's stop; proof itself never runs >20 min.
    return min(1200, remaining - 300)


def supervise(args):
    import fcntl

    work = Path.home() / WORK_NAME
    work.mkdir(mode=0o700, exist_ok=True)
    with (work / "job.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        seconds = parse_deadline(args.termination)
        stop_at = time.monotonic() + seconds
        for kind in ("save", "restore"):
            command = [
                sys.executable,
                str(PACKAGE / "run_gcp_drive_proof.py"),
                "--phase",
                kind,
                "--work",
                str(work / kind),
                "--connection",
                str(args.connection),
            ]
            with (work / "private-worker.log").open("ab") as log:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=log,
                    start_new_session=True,
                )
                try:
                    code = process.wait(timeout=max(1, stop_at - time.monotonic()))
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    raise RuntimeError("Proof time bound reached; saved files preserved") from None
                require(code == 0, "Proof phase failed; inspect safe summary")
        saved = json.loads((work / "save/save.json").read_text())
        restored = json.loads((work / "restore/restore.json").read_text())
        require(saved["process_id"] != restored["process_id"], "Distinct restore process")
        require(restored["existing_completion_reused"], "Restore did not use completion")
        summary = {
            "status": "drive_real_pair_persistence_passed",
            "manifest_sha256": digest(PACKAGE / "proof_manifest.json"),
            "save": saved,
            "restore": restored,
            "off_vm_persistence_proven": True,
            "production_months_processed": 0,
            "negative_label_permitted": False,
            "actual_vm_termination_timestamp": args.termination,
        }
        (work / "drive_proof_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print("Passed. Download:", work / "drive_proof_summary.json", flush=True)
        print(
            "Apply Stop in Compute Engine after downloading. This script does not change VM state."
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("save", "restore"))
    parser.add_argument("--work", type=Path)
    parser.add_argument("--local-store", type=Path)
    parser.add_argument("--connection", type=Path)
    parser.add_argument("--termination")
    parser.add_argument("--supervise", action="store_true")
    args = parser.parse_args()
    spec = spec_read()
    from diagnose_gcp_drive_proof import add_safe_check_messages

    for filename in spec["files"]:
        if filename.endswith(".py"):
            add_safe_check_messages((PACKAGE / filename).read_text())
    if args.phase:
        require(args.work is not None, "Phase work path")
        require((args.local_store is None) != (args.connection is None), "Select one backend")
        phase(args.phase, args.work, args.connection, args.local_store)
        return
    require(os.name == "posix", "Launch on the Ubuntu VM")
    require(args.connection is not None and args.termination, "Connection and actual VM deadline")
    DriveJobStore.from_file(args.connection)  # permission/config preflight, no API call
    parse_deadline(args.termination)
    if args.supervise:
        supervise(args)
        return
    work = Path.home() / WORK_NAME
    work.mkdir(mode=0o700, exist_ok=True)
    with (work / "launcher.log").open("ab") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--supervise",
                "--connection",
                str(args.connection.resolve()),
                "--termination",
                args.termination,
            ],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    print("Detached launch requested; PID:", process.pid)
    print("Check progress:", work / "launcher.log")


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except Exception as error:
        # Only literal validation labels from the verified code and exact
        # transport HTTP status codes are public; arbitrary exceptions aren't.
        from diagnose_gcp_drive_proof import safe_error

        print(
            "Proof failed:",
            safe_error(error),
            "No credentials logged; files retained.",
            flush=True,
        )
        raise SystemExit(1) from None
