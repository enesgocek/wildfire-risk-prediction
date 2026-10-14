"""Deliver bytes through read-only fake storage and reject untrusted completion records."""

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/cloud"))
m = importlib.import_module("receive_gcp_products")
WORKER = "a" * 64


def record(task, payload=b"checked payload"):
    checksum = m.digest(payload)
    return {
        "protocol": "verified_job_checkpoint_v1",
        "task_id": task,
        "manifest_sha256": m.SCOPE,
        "worker_sha256": WORKER,
        "payload_sha256": checksum,
        "payload_bytes": len(payload),
        "payload_key": m.prefix(task) + "/" + checksum + ".zip",
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
    }


def test_training_delivery_population():
    months = [
        f"{y}-{n:02d}"
        for y in range(2018, 2024)
        for n in range(1, 13)
        if f"{y}-{n:02d}" != "2023-07"
    ]
    tasks = m.tasks_for({"months": months})
    assert len(tasks) == len(set(tasks)) == 199
    assert "month:2018-06" not in tasks and "day:2018-06-13" not in tasks
    assert "month:2023-12" not in tasks and "day:2023-12-31" not in tasks
    with pytest.raises(ValueError):
        m.tasks_for({"months": months}, ["2025-01"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("manifest_sha256", "b" * 64),
        ("worker_sha256", "b" * 64),
        ("payload_key", "escape.zip"),
        ("negative_label_permitted", True),
        ("payload_bytes", True),
        ("daily_observation_status", "observed"),
        ("payload_sha256", "not-a-hash"),
    ],
)
def test_bad_marker_rejected(field, value):
    value_record = record("month:2018-01")
    value_record[field] = value
    with pytest.raises(ValueError):
        m.marker(json.dumps(value_record).encode(), "month:2018-01", WORKER)


def test_changed_existing_bytes_preserved(tmp_path):
    p = tmp_path / "accepted.zip"
    p.write_bytes(b"accepted")
    with pytest.raises(ValueError):
        m.preserve(p, b"changed")
    assert p.read_bytes() == b"accepted"


def test_receive_and_resume_without_remote_payload_rewrite(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "ROOT", tmp_path)
    monkeypatch.setattr(m.shutil, "disk_usage", lambda _: SimpleNamespace(free=100 * 2**30))
    spec = {"months": ["2018-01"], "files": {"run_gcp_production.py": WORKER}}
    monkeypatch.setattr(m, "verify_package", lambda _: spec)
    objects = {}
    for task in m.tasks_for(spec):
        r = record(task)
        objects[m.prefix(task) + "/completed.json"] = json.dumps(r).encode()
        objects[r["payload_key"]] = b"checked payload"
    calls = []

    class ReadOnly:
        @classmethod
        def from_file(cls, _):
            return cls()

        def get(self, key):
            calls.append(key)
            return objects.get(key)

    monkeypatch.setattr(m, "ProductionDriveStore", ReadOnly)
    out = tmp_path / "outputs/gcp_delivery/fixture"
    first = m.receive(tmp_path / "private.json", out, workers=1)
    assert len(first["tasks"]) == 2 and first["cloud_writes"] == 0
    assert first["scientific_validation"] is False
    calls.clear()
    second = m.receive(tmp_path / "private.json", out, workers=1)
    assert all(r["local_reused"] for r in second["tasks"])
    assert all(key.endswith("/completed.json") for key in calls)
    (out / "receive.lock").write_text("another writer")
    with pytest.raises(FileExistsError):
        m.receive(tmp_path / "private.json", out, workers=1)
    assert (out / "receive.lock").read_text() == "another writer"
