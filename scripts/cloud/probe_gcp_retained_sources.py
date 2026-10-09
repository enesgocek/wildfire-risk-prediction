"""Bounded isolated replay of retained local sources; no login, download or publication.

Uses pinned frozen science. Writes only to a separate diagnosis directory.
Never starts the production queue or shuts down/restarts a VM.
"""

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

COLLECTOR_SHA = "0afd6e7618ec7d1d32da7d43458429faf4b0a951876e69d5e993215dfb648f31"
NAME = "gcp_acceleration_local_probe_2026-10-09"
MAX_SECONDS = 900
MONTH_SHA = "7f44606b19aab60fe75392f8df7e6951143892caf94e58eb6b23b2bfc5f19685"


class ProbeCheck(ValueError):
    """Only constant labels supplied by this diagnostic are printable."""


def require(ok, label):
    if not ok:
        raise ProbeCheck(label)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def helper(home):
    path = home / "collect_gcp_acceleration_failure.py"
    require(not path.is_symlink() and digest(path) == COLLECTOR_SHA, "Pinned diagnostic helper")
    spec = importlib.util.spec_from_file_location("checked_capture", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def error_summary(error, roots):
    """Public labels from pinned source only; no external error text or frame locals."""
    labels = set()
    for root in roots:
        manifest = root / "production_manifest.json"
        if manifest.is_file():
            names = json.loads(manifest.read_bytes())["files"]
        else:
            names = {
                **json.loads((root / "summer/manifest.json").read_bytes())["bundle_files"],
                "scripts/cloud/l2_daily_compact.py": "",
            }
        for name in names:
            if not name.endswith(".py"):
                continue
            path = root / name
            require(
                not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
                "Guard source boundary",
            )
            # Never scan unrelated files or frame locals for error text.
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call) and len(node.args) > 1:
                    fn = node.func
                    if (isinstance(fn, ast.Name) and fn.id == "require") or (
                        isinstance(fn, ast.Attribute) and fn.attr == "require"
                    ):
                        value = node.args[1]
                        if isinstance(value, ast.Constant) and isinstance(value.value, str):
                            labels.add(value.value)
    value = error.args[0] if len(error.args) == 1 else None
    frames = []
    tb = error.__traceback__
    while tb:
        path = Path(tb.tb_frame.f_code.co_filename).resolve()
        for root in roots:
            if path.is_relative_to(root.resolve()):
                frames.append(
                    {
                        "file": str(path.relative_to(root.resolve())).replace("\\", "/"),
                        "line": tb.tb_lineno,
                        "function": tb.tb_frame.f_code.co_name,
                    }
                )
                break
        tb = tb.tb_next
    return {
        "error_type": type(error).__name__,
        "guard": value
        if isinstance(value, str) and (value in labels or isinstance(error, ProbeCheck))
        else "CLASS_ONLY",
        "frames": frames[-6:],
    }


def block_network():
    def audit(event, _args):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.bind"}:
            raise RuntimeError("Diagnostic network forbidden")

    sys.addaudithook(audit)


def scientific_probe(runner, root, pair, output):
    """Existing raw source paths stay inside the frozen task clone."""
    _, native = runner.science(root)
    native.OUTPUT = output
    raw = root / "summer/raw" / pair["stem"]
    for source in pair["sources"]:
        path = raw / source["filename"]
        require(
            not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
            "Local raw boundary",
        )
        require(path.is_file() and path.stat().st_size == source["bytes"], "Local raw size")
        native.source_check(pair, source, path)
    native.child_audit(pair, raw)
    native.compare_pair(pair, output)


def child(home, identity):
    capture = helper(home)
    original = home / "wildfire-gcp-production-package"
    controller = home / "wildfire-gcp-acceleration-package"
    capture.pinned(original, "production_manifest.json", capture.SCOPE)
    capture.pinned(controller, "acceleration_manifest.json", capture.CONTROLLER)
    work = home / "wildfire-gcp-production-v1"
    saved = capture.state(capture.read(work / "progress.json", work, 65536))
    month = work / "months" / saved["failed_month"]
    plan_data = capture.read(month / "metadata/month.json", work, 2_000_000)
    require(
        saved["failed_month"] == "2023-12" and hashlib.sha256(plan_data).hexdigest() == MONTH_SHA,
        "Pinned December metadata plan",
    )
    plan = json.loads(plan_data)
    pairs = [p for p in plan["pairs"] if p["sample_id"] == identity]
    require(len(pairs) == 1, "Local pair identity")
    root = month / "accelerated_run/tasks" / hashlib.sha256(identity.encode()).hexdigest()
    require(
        root.is_dir() and not root.is_symlink() and not (root / "pair.zip").exists(),
        "Partial local task only",
    )
    output = home / NAME / "replay" / root.name
    require(not output.exists() and not output.is_symlink(), "Fresh isolated replay")
    output.mkdir(parents=True)
    sys.path.insert(0, str(original))
    import run_gcp_production as runner

    # Same address-space bound as frozen pair children; one worker, one BLAS thread.
    if os.name == "posix":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (6 * 2**30, 6 * 2**30))
    block_network()
    started = time.monotonic()
    value = {"sample_id": identity, "status": "local_science_passed"}
    try:
        with (
            open(os.devnull, "w") as quiet,
            contextlib.redirect_stdout(quiet),
            contextlib.redirect_stderr(quiet),
        ):
            scientific_probe(runner, root, pairs[0], output)
    except Exception as error:
        value.update(status="local_failure_reproduced", **error_summary(error, [original, root]))
    value["seconds"] = time.monotonic() - started
    (home / NAME / (root.name + ".json")).write_text(json.dumps(value, sort_keys=True))


def worker(home):
    capture = helper(home)
    original = home / "wildfire-gcp-production-package"
    controller = home / "wildfire-gcp-acceleration-package"
    work = home / "wildfire-gcp-production-v1"
    output = home / NAME
    require(not output.exists() and not output.is_symlink(), "Probe directory already exists")
    output.mkdir(mode=0o700)
    rows = []
    with capture.lock(work):
        capture.pinned(original, "production_manifest.json", capture.SCOPE)
        capture.pinned(controller, "acceleration_manifest.json", capture.CONTROLLER)
        state = capture.state(capture.read(work / "progress.json", work, 65536))
        month = work / "months" / state["failed_month"]
        plan_data = capture.read(month / "metadata/month.json", work, 2_000_000)
        require(
            state["failed_month"] == "2023-12"
            and hashlib.sha256(plan_data).hexdigest() == MONTH_SHA,
            "Pinned December metadata plan",
        )
        plan = json.loads(plan_data)
        pairs = {hashlib.sha256(p["sample_id"].encode()).hexdigest(): p for p in plan["pairs"]}
        tasks = [
            p for p in (month / "accelerated_run/tasks").iterdir() if not (p / "pair.zip").exists()
        ]
        require(
            0 < len(tasks) <= 24 and all(not p.is_symlink() and p.name in pairs for p in tasks),
            "Retained partial task population",
        )
        # Fewest outputs first: early source checks are cheaper than later geometry.
        tasks.sort(key=lambda p: (len(list((p / "summer/results").glob("*"))), p.name))
        deadline = time.monotonic() + MAX_SECONDS
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("EARTHDATA_") and k not in {"PYTHONPATH", "PYTHONHOME"}
        }
        env.update(
            PYTHONNOUSERSITE="1",
            PYTHONDONTWRITEBYTECODE="1",
            OMP_NUM_THREADS="1",
            OPENBLAS_NUM_THREADS="1",
            MKL_NUM_THREADS="1",
            GDAL_NUM_THREADS="1",
        )
        for task in tasks:
            remaining = deadline - time.monotonic()
            if remaining < 30:
                break
            require(shutil.disk_usage(home).free > 4 * 2**30, "Probe disk reserve")
            identity = pairs[task.name]["sample_id"]
            print("LOCAL CHECK", identity, flush=True)
            try:
                result = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()), "--child", identity],
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=min(180, remaining),
                )
                path = output / (task.name + ".json")
                if result.returncode != 0 or not path.is_file():
                    rows.append(
                        {
                            "sample_id": identity,
                            "status": "probe_child_failed",
                            "returncode": result.returncode,
                        }
                    )
                    break
                record = json.loads(path.read_bytes())
                rows.append(record)
                print(
                    "LOCAL RESULT", identity, record["status"], record.get("guard", ""), flush=True
                )
                if record["status"] != "local_science_passed":
                    break
            except subprocess.TimeoutExpired:
                rows.append({"sample_id": identity, "status": "diagnostic_time_limit"})
                break
        report = {
            "protocol": "gcp_retained_source_probe_v1",
            "diagnostic_sha256": digest(Path(__file__).resolve()),
            "collector_sha256": COLLECTOR_SHA,
            "original_manifest_sha256": capture.SCOPE,
            "controller_manifest_sha256": capture.CONTROLLER,
            "month_plan_sha256": MONTH_SHA,
            "results": rows,
            "planned_pairs": len(tasks),
            "max_seconds": MAX_SECONDS,
            "raw_downloads": 0,
            "production_writes": 0,
            "credentials_read": False,
            "network_requests": 0,
            "remaining_pairs": len(tasks) - len(rows),
            "original_exception_automatically_proven": False,
        }
        target = home / (NAME + ".zip")
        require(not target.exists(), "Probe export already exists")
        with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("probe_summary.json", json.dumps(report, sort_keys=True))
    print("Download:", target, flush=True)
    print("Stop VM after downloading; this probe does not shut it down.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--child")
    args = parser.parse_args()
    home = Path.home()
    if args.child:
        require(re.fullmatch(r"(?:SNPP|N20):\d{7}\.\d{4}", args.child), "Probe sample identity")
        child(home, args.child)
    elif args.worker:
        worker(home)
    else:
        helper(home)
        require(not (home / NAME).exists(), "Probe directory already exists")
        log = home / "gcp_local_probe_launcher.log"
        with log.open("x") as stream:
            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--worker"],
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=stream,
                start_new_session=True,
            )
        print("Detached local probe PID:", process.pid)
        print("Check:", log)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    os.umask(0o077)
    try:
        main()
    except ProbeCheck as error:
        print("Probe check failed:", str(error), flush=True)
        raise SystemExit(1) from None
    except Exception as error:
        print("Probe stopped:", type(error).__name__, "; no external error text logged", flush=True)
        raise SystemExit(1) from None
