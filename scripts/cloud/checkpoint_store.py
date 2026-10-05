"""Persist immutable, validated day ZIPs; publish a completion record last."""

import json
import re
import shutil
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

PROTOCOL = "validated_zip_v1"
NAME = re.compile(r"checkpoint_([1-8])_([a-f0-9]{64})\.commit\.json")


def validate_snapshot(day, payload, manifest, manifest_sha):
    with tempfile.TemporaryDirectory(dir=day.ROOT) as temporary:
        output = Path(temporary) / "results"
        day.restore_results(payload, manifest, manifest_sha, output)
        summary = json.loads((output / "day_summary.json").read_text())
        records = [day.checkpoint_read(p, output, manifest_sha) for p in manifest["pairs"]]
        records = [record for record in records if record is not None]
        count = len(records)
        day.require(
            1 <= count <= 8 and summary["completed_pairs"] == count, "Snapshot count differs"
        )
        day.require(
            summary["manifest_sha256"] == manifest_sha
            and summary["worker_sha256"] == day.digest(Path(day.__file__)),
            "Snapshot code/manifest differs",
        )
        day.require(
            summary["records"] == records and summary["negative_label_permitted"] is False,
            "Snapshot records/labels differ",
        )
        expected_status = "passed_all_eight_references" if count == 8 else "checkpointed_partial"
        day.require(
            summary["status"] == expected_status and summary["day"] == manifest["day"],
            "Snapshot status/day differs",
        )
        return count


def copy_verified(day, source, destination, expected_sha):
    """Never move the local source or overwrite an immutable saved version."""
    day.require(source.is_file() and day.digest(source) == expected_sha, "Input changed")
    if destination.exists():
        day.require(day.digest(destination) == expected_sha, "Existing saved payload changed")
        return
    pending = destination.with_name(destination.name + f".{uuid.uuid4().hex}.pending")
    with source.open("rb") as reader, pending.open("xb") as writer:
        shutil.copyfileobj(reader, writer)
        writer.flush()
    day.require(
        day.digest(pending) == expected_sha and day.digest(source) == expected_sha,
        "Copy readback differs",
    )
    # Drive/FUSE rename is not assumed to be a server-side atomic transaction.
    pending.rename(destination)
    day.require(day.digest(destination) == expected_sha, "Saved payload readback differs")


def save_snapshot(day, source, store_root, manifest, manifest_sha):
    count = validate_snapshot(day, source, manifest, manifest_sha)
    checksum = day.digest(source)
    folder = store_root.resolve() / manifest_sha
    day.require(folder.resolve().is_relative_to(store_root.resolve()), "Store path escapes root")
    folder.mkdir(parents=True, exist_ok=True)
    basename = f"checkpoint_{count}_{checksum}"
    payload = folder / (basename + ".zip")
    day.require(payload.resolve().is_relative_to(folder.resolve()), "Payload path escapes job")
    copy_verified(day, source, payload, checksum)
    day.require(
        validate_snapshot(day, payload, manifest, manifest_sha) == count, "Saved snapshot differs"
    )
    expected = {
        "protocol": PROTOCOL,
        "manifest_sha256": manifest_sha,
        "worker_sha256": day.digest(Path(day.__file__)),
        "payload_sha256": checksum,
        "payload_bytes": source.stat().st_size,
        "completed_pairs": count,
        "payload_name": payload.name,
    }
    marker = folder / (basename + ".commit.json")
    day.require(marker.resolve().is_relative_to(folder.resolve()), "Commit path escapes job")
    if marker.exists():
        value = json.loads(marker.read_text())
        day.require(
            all(value.get(key) == item for key, item in expected.items()),
            "Existing completion record differs",
        )
    else:
        value = {**expected, "saved_at_utc": datetime.now(UTC).isoformat()}
        pending = marker.with_name(marker.name + f".{uuid.uuid4().hex}.pending")
        pending.write_text(json.dumps(value, indent=2), encoding="utf-8")
        day.require(json.loads(pending.read_text()) == value, "Completion record readback failed")
        pending.rename(marker)
    day.require(json.loads(marker.read_text()) == value, "Published completion record differs")
    return {**value, "store_payload": str(payload), "store_commit": str(marker)}


def latest_snapshot(day, store_root, manifest, manifest_sha):
    folder = store_root.resolve() / manifest_sha
    day.require(folder.resolve().is_relative_to(store_root.resolve()), "Store path escapes root")
    if not folder.exists():
        return None
    candidates = []
    # Only this job's completion records are read; pending files are never eligible.
    for marker in folder.glob("*.commit.json"):
        match = NAME.fullmatch(marker.name)
        day.require(
            match is not None and marker.resolve().is_relative_to(folder.resolve()),
            "Unexpected completion record path",
        )
        record = json.loads(marker.read_text())
        checksum = match[2]
        count = int(match[1])
        expected_name = f"checkpoint_{count}_{checksum}.zip"
        day.require(
            record["protocol"] == PROTOCOL
            and record["manifest_sha256"] == manifest_sha
            and record["worker_sha256"] == day.digest(Path(day.__file__))
            and record["payload_name"] == expected_name
            and record["payload_sha256"] == checksum
            and record["completed_pairs"] == count,
            "Completion record identity differs",
        )
        payload = folder / expected_name
        day.require(payload.resolve().is_relative_to(folder.resolve()), "Saved path escapes root")
        day.require(
            payload.stat().st_size == record["payload_bytes"] and day.digest(payload) == checksum,
            "Saved snapshot corrupted",
        )
        day.require(
            validate_snapshot(day, payload, manifest, manifest_sha) == count,
            "Completion count differs",
        )
        saved = datetime.fromisoformat(record["saved_at_utc"])
        day.require(saved.tzinfo is not None, "Missing completion timezone")
        candidates.append((count, saved, payload))
    return max(candidates, key=lambda value: (value[0], value[1]))[2] if candidates else None


def attach_store(day, store_root, manifest, manifest_sha):
    original_export = day.export_results

    def export_and_persist(*args):
        original_export(*args)
        record = save_snapshot(
            day, day.ROOT / "l2_day_results.zip", store_root, manifest, manifest_sha
        )
        print(
            f"Saved and read back persistent checkpoint: {record['completed_pairs']}/8", flush=True
        )

    day.export_results = export_and_persist
    return original_export
