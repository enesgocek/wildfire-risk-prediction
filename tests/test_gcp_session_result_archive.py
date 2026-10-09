"""Reject unsafe session archives and altered nested completion records."""

import importlib.util
import io
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
spec = importlib.util.spec_from_file_location(
    "session_result_reader", ROOT / "scripts/cloud/verify_gcp_production_session_results.py"
)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def archive(path, members):
    with tarfile.open(path, "w:gz") as target:
        for name, data, kind in members:
            member = tarfile.TarInfo(name)
            if kind == "link":
                member.type = tarfile.SYMTYPE
                member.linkname = "../private.json"
                target.addfile(member)
            else:
                member.size = len(data)
                target.addfile(member, io.BytesIO(data))


@pytest.mark.parametrize(
    "name,kind",
    [
        ("../private.json", "file"),
        ("/private.json", "file"),
        ("months/2023-08/manifest.zip", "link"),
        ("private_connection.json", "file"),
        ("months/2024-01/manifest.zip", "file"),
    ],
)
def test_unsafe_or_out_of_scope_member_refused(tmp_path, name, kind):
    source = tmp_path / "snapshot.tar.gz"
    archive(source, [(name, b"private", kind)])
    with pytest.raises(ValueError):
        reader.unpack_snapshot(source, tmp_path / "unpacked")
    assert not (tmp_path / "private.json").exists()


def test_duplicate_payload_refused(tmp_path):
    source = tmp_path / "snapshot.tar.gz"
    archive(source, [("progress.json", b"{}", "file")] * 2)
    with pytest.raises(ValueError, match="duplicate"):
        reader.unpack_snapshot(source, tmp_path / "unpacked")


def test_changed_nested_day_bytes_cannot_pass_completion(tmp_path):
    payload = tmp_path / "day.zip"
    payload.write_bytes(b"saved bytes")
    scope, worker = "a" * 64, "b" * 64
    digest = reader.sha(payload)
    task = "day:2023-08-01"
    import hashlib

    record = {
        "protocol": "verified_job_checkpoint_v1",
        "task_id": task,
        "manifest_sha256": scope,
        "worker_sha256": worker,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "payload_sha256": digest,
        "payload_bytes": payload.stat().st_size,
        "payload_key": f"jobs/{scope}/{hashlib.sha256(task.encode()).hexdigest()}/{digest}.zip",
    }
    reader.check_marker(record, "2023-08-01", payload, scope, worker)
    payload.write_bytes(b"other bytes")
    with pytest.raises(ValueError, match="SHA/size"):
        reader.check_marker(record, "2023-08-01", payload, scope, worker)
