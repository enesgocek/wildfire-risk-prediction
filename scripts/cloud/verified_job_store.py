"""Provider-independent immutable checkpoint protocol; filesystem is rehearsal only.

Publish completion last. Saving validates the caller's scientific payload twice:
before upload and after reading the saved bytes into a new temporary location.
Production Drive/GCS adapters and launcher are separate integration work.
"""

import hashlib
import json
import math
import os
import re
import tempfile
import threading
import zipfile
from pathlib import Path

PROTOCOL = "verified_job_checkpoint_v1"
SHA_PATTERN = re.compile(r"[a-f0-9]{64}")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class RehearsalFileStore:
    """A second local directory does NOT prove off-VM/cloud persistence."""

    def __init__(self, root):
        require(not root.is_symlink(), "Store root symlink")
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, key):
        require(isinstance(key, str) and key and "\\" not in key, "Object key")
        require(
            not key.startswith("/") and all(p not in {"", ".", ".."} for p in key.split("/")),
            "Object key",
        )
        path = self.root.joinpath(*key.split("/"))
        require(
            not path.is_symlink() and path.resolve().is_relative_to(self.root), "Store path escape"
        )
        return path

    def get(self, key):
        path = self.path(key)
        return path.read_bytes() if path.exists() else None

    def create(self, key, data):
        """Exclusive create; collisions never overwrite an existing object."""
        path = self.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            require(path.read_bytes() == data, "Immutable object collision")

    def used_bytes(self, prefix):
        folder = self.path(prefix)
        total = 0
        if folder.exists():
            for path in folder.rglob("*"):
                require(
                    not path.is_symlink() and path.resolve().is_relative_to(self.root),
                    "Store symlink",
                )
                if path.is_file():
                    total += path.stat().st_size
        return total


class VerifiedJobStore:
    def __init__(self, backend, manifest_sha, worker_sha, budget_bytes):
        require(SHA_PATTERN.fullmatch(manifest_sha) is not None, "Manifest SHA")
        require(SHA_PATTERN.fullmatch(worker_sha) is not None, "Worker SHA")
        require(type(budget_bytes) is int and budget_bytes > 0, "Storage budget")
        self.backend = backend
        self.manifest_sha = manifest_sha
        self.worker_sha = worker_sha
        self.budget_bytes = budget_bytes
        # One parent coordinates writes; this is not a distributed multi-VM lock.
        self.lock = threading.RLock()

    def task_prefix(self, task_id):
        require(isinstance(task_id, str) and 0 < len(task_id) < 128, "Task identity")
        return f"jobs/{self.manifest_sha}/{sha(task_id.encode())}"

    def check_zip(self, path, expected_names):
        require(
            expected_names
            and all(Path(n).name == n and "/" not in n and "\\" not in n for n in expected_names),
            "Expected payload members",
        )
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            require(
                len(infos) == len(expected_names)
                and {i.filename for i in infos} == set(expected_names),
                "Payload ZIP members",
            )
            require(
                all(0 < i.file_size < 150_000_000 for i in infos)
                and sum(i.file_size for i in infos) < 300_000_000,
                "Payload size",
            )
            require(archive.testzip() is None, "Payload CRC")

    def materialize_checked(self, data, expected_names, scientific_check):
        require(
            data is not None and 0 < len(data) < 150_000_000, "Saved payload absent or oversized"
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "payload.zip"
            path.write_bytes(data)
            self.check_zip(path, expected_names)
            scientific_check(path)

    def restore(self, task_id, expected_names, scientific_check):
        prefix = self.task_prefix(task_id)
        marker = self.backend.get(prefix + "/completed.json")
        if marker is None:
            # Orphan payloads and partial files never mean that a task completed.
            return None
        require(len(marker) < 65536, "Completion record size")
        record = json.loads(marker)
        require(
            set(record)
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
            "Completion schema",
        )
        require(
            record["protocol"] == PROTOCOL
            and record["task_id"] == task_id
            and record["manifest_sha256"] == self.manifest_sha
            and record["worker_sha256"] == self.worker_sha,
            "Completion identity",
        )
        require(
            record["negative_label_permitted"] is False
            and record["daily_observation_status"] == "unknown",
            "Completion label policy",
        )
        checksum = record["payload_sha256"]
        require(
            isinstance(checksum, str) and SHA_PATTERN.fullmatch(checksum) is not None, "Payload SHA"
        )
        key = prefix + f"/{checksum}.zip"
        require(record["payload_key"] == key, "Payload key escapes task")
        data = self.backend.get(key)
        require(
            data is not None and len(data) == record["payload_bytes"] and sha(data) == checksum,
            "Saved payload changed",
        )
        self.materialize_checked(data, expected_names, scientific_check)
        return record

    def save(self, task_id, payload, expected_names, scientific_check):
        with self.lock:
            data = payload.read_bytes()
            checksum = sha(data)
            prefix = self.task_prefix(task_id)
            existing = self.restore(task_id, expected_names, scientific_check)
            if existing is not None:
                require(
                    existing["payload_sha256"] == checksum, "Completed task must not be replaced"
                )
                return existing
            self.check_zip(payload, expected_names)
            scientific_check(payload)
            key = prefix + f"/{checksum}.zip"
            record = {
                "protocol": PROTOCOL,
                "task_id": task_id,
                "manifest_sha256": self.manifest_sha,
                "worker_sha256": self.worker_sha,
                "payload_sha256": checksum,
                "payload_bytes": len(data),
                "payload_key": key,
                "negative_label_permitted": False,
                "daily_observation_status": "unknown",
            }
            previous = self.backend.get(key)
            require(previous is None or previous == data, "Immutable payload changed")
            addition = (len(data) if previous is None else 0) + len(canonical(record))
            require(
                self.backend.used_bytes(f"jobs/{self.manifest_sha}") + addition
                <= self.budget_bytes,
                "Job storage budget exceeded",
            )
            self.backend.create(key, data)
            readback = self.backend.get(key)
            require(readback == data, "Uploaded payload readback differs")
            self.materialize_checked(readback, expected_names, scientific_check)
            require(payload.read_bytes() == data, "Local payload changed during publish")
            self.backend.create(prefix + "/completed.json", canonical(record))
            require(
                self.restore(task_id, expected_names, scientific_check) == record,
                "Completion readback failed",
            )
            return record


def may_start_task(seconds_remaining, task_timeout=900, publish_reserve=180):
    require(
        type(seconds_remaining) in (int, float)
        and math.isfinite(seconds_remaining)
        and seconds_remaining >= 0,
        "Remaining runtime",
    )
    require(
        type(task_timeout) is int
        and task_timeout > 0
        and type(publish_reserve) is int
        and publish_reserve > 0,
        "Runtime reserves",
    )
    # Nothing new starts unless worst-case task and publish time both fit.
    return seconds_remaining > task_timeout + publish_reserve
