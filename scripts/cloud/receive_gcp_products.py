"""Read-only Drive delivery of compact training products; never runs cloud science."""

import argparse
import hashlib
import json
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

from diagnose_gcp_production_manifest import verify_package
from drive_job_store import require
from production_drive_store import ProductionDriveStore
from verify_gcp_v7_session_logs import DEFERRED, PARTIAL_DAYS, ROOT, SCOPE, strict_json

MAX_DELIVERY = 4 * 2**30
MIN_FREE = 10 * 2**30


def digest(data):
    return hashlib.sha256(data).hexdigest()


def tasks_for(spec, months=None):
    selected = set(spec["months"]) if months is None else set(months)
    require(selected and selected <= set(spec["months"]), "Production training months only")
    tasks = ["manifest:" + m for m in selected]
    tasks += ["month:" + m for m in selected if m not in {d[:7] for d in DEFERRED}]
    tasks += ["day:" + d for d in PARTIAL_DAYS if d[:7] in selected]
    return sorted(tasks)


def prefix(task):
    return f"jobs/{SCOPE}/{digest(task.encode())}"


def marker(data, task, worker):
    require(data is not None and 0 < len(data) < 65536, "Missing/bounded completion")
    value = strict_json(data)
    require(
        set(value)
        == {
            "protocol",
            "task_id",
            "manifest_sha256",
            "worker_sha256",
            "payload_sha256",
            "payload_bytes",
            "payload_key",
            "negative_label_permitted",
            "daily_observation_status",
        },
        "Completion field population",
    )
    require(
        value["protocol"] == "verified_job_checkpoint_v1"
        and value["task_id"] == task
        and value["manifest_sha256"] == SCOPE
        and value["worker_sha256"] == worker
        and value["negative_label_permitted"] is False
        and value["daily_observation_status"] == "unknown",
        "Completion identity/policy",
    )
    checksum = value["payload_sha256"]
    require(
        isinstance(checksum, str)
        and len(checksum) == 64
        and all(c in "0123456789abcdef" for c in checksum),
        "Payload checksum",
    )
    require(
        type(value["payload_bytes"]) is int and 0 < value["payload_bytes"] < 150_000_000,
        "Payload size",
    )
    require(value["payload_key"] == prefix(task) + "/" + checksum + ".zip", "Payload key")
    return value


def local_folder(root, task):
    kind, value = task.split(":")
    require(kind in {"manifest", "month", "day"}, "Task role")
    # Tasks come exclusively from the pinned training catalogue.
    require(value and all(c in "0123456789-" for c in value), "Task calendar path")
    target = root / "products" / kind / value
    require(
        target.resolve().is_relative_to(root.resolve()) and not target.is_symlink(),
        "Delivery path boundary",
    )
    return target


def preserve(path, data):
    require(not path.is_symlink(), "Delivery symlink")
    if path.exists():
        require(path.read_bytes() == data, "Immutable delivery collision")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def progress(root, phase, completed, total):
    value = {
        "phase": phase,
        "completed": completed,
        "total": total,
        "updated_at_utc": datetime.now(UTC).isoformat(),
        "cloud_writes": 0,
    }
    pending = root / "receive_progress.pending"
    pending.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    pending.replace(root / "receive_progress.json")


def receive(connection, root, months=None, workers=4):
    require(
        root.resolve().is_relative_to((ROOT / "outputs/gcp_delivery").resolve())
        and not root.is_symlink(),
        "Delivery workspace boundary",
    )
    require(1 <= workers <= 4, "Bounded delivery workers")
    spec = verify_package(ROOT / "outputs/gcp_production/package")
    tasks = tasks_for(spec, months)
    worker = spec["files"]["run_gcp_production.py"]
    root.mkdir(parents=True, exist_ok=True)
    require(shutil.disk_usage(root).free >= MIN_FREE, "Local disk reserve")
    lock = root / "receive.lock"
    with lock.open("x", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid()}, stream)
    started = time.monotonic()
    try:

        def fetch_marker(task):
            require(not (root / "PAUSE").exists(), "Delivery pause requested")
            backend = ProductionDriveStore.from_file(connection)
            data = backend.get(prefix(task) + "/completed.json")
            record = marker(data, task, worker)
            preserve(local_folder(root, task) / "completed.json", data)
            return task, record

        records = {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(fetch_marker, task) for task in tasks]
            for future in as_completed(futures):
                task, record = future.result()
                records[task] = record
                progress(root, "markers", len(records), len(tasks))
                if len(records) % 10 == 0:
                    print("Completion checked", len(records), "/", len(tasks), flush=True)
        total_bytes = sum(r["payload_bytes"] for r in records.values())
        require(total_bytes <= MAX_DELIVERY, "Compact delivery byte budget")
        require(shutil.disk_usage(root).free >= MIN_FREE + total_bytes, "Delivery disk budget")
        print("Verified delivery bytes", total_bytes, flush=True)

        def fetch_payload(task):
            require(not (root / "PAUSE").exists(), "Delivery pause requested")
            require(shutil.disk_usage(root).free >= MIN_FREE, "Local disk reserve")
            record = records[task]
            target = local_folder(root, task) / "payload.zip"
            require(not target.is_symlink(), "Payload symlink")
            reused = target.exists()
            if reused:
                data = target.read_bytes()
            else:
                data = ProductionDriveStore.from_file(connection).get(record["payload_key"])
            require(
                data is not None
                and len(data) == record["payload_bytes"]
                and digest(data) == record["payload_sha256"],
                "Delivered payload size/SHA",
            )
            preserve(target, data)
            return {
                "task_id": task,
                "bytes": len(data),
                "sha256": digest(data),
                "local_reused": reused,
                "live_payload_read": not reused,
            }

        received = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(fetch_payload, task) for task in tasks]
            for future in as_completed(futures):
                received.append(future.result())
                progress(root, "payloads", len(received), len(tasks))
                if len(received) % 10 == 0:
                    print("Payload received", len(received), "/", len(tasks), flush=True)
        report = {
            "status": "compact_delivery_bytes_verified",
            "recorded_at_utc": datetime.now(UTC).isoformat(),
            "scope_sha256": SCOPE,
            "tasks": sorted(received, key=lambda r: r["task_id"]),
            "total_bytes": total_bytes,
            "seconds": time.monotonic() - started,
            "cloud_writes": 0,
            "raw_source_downloads": 0,
            "scientific_validation": False,
            "july_reference_included": False,
            "limitation": (
                "Completion/payload byte delivery only; native scientific readback is separate."
            ),
        }
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        preserve(
            root / f"receive_final_{stamp}.json", (json.dumps(report, indent=2) + "\n").encode()
        )
        progress(root, "complete", len(received), len(tasks))
        print("DELIVERY COMPLETE", len(received), "tasks", total_bytes, "bytes", flush=True)
        return report
    finally:
        # Only this invocation's lock is removed, never a pre-existing stale lock.
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connection", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--months", nargs="+")
    args = parser.parse_args()
    receive(args.connection, args.out, args.months)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Delivery stopped:", type(error).__name__, "; no external text logged", flush=True)
        raise SystemExit(1) from None
