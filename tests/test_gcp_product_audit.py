"""Reject altered delivery bytes and ambiguous nested compact archives offline."""

import importlib
import io
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/cloud"))
m = importlib.import_module("audit_gcp_products")


def zip_bytes(names):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name in names:
            archive.writestr(name, b"bounded")
    return stream.getvalue()


@pytest.mark.parametrize("names", [["../outside"], ["report.json", "report.json"], ["unexpected"]])
def test_unexpected_or_duplicate_zip_members(names):
    with pytest.raises(ValueError):
        m.flat_zip(zip_bytes(names), {"report.json"})


def test_exact_zip_members():
    assert m.flat_zip(zip_bytes(["report.json"]), {"report.json"}) == {"report.json": b"bounded"}


def test_changed_local_payload_rejected(tmp_path, monkeypatch):
    folder = tmp_path / "task"
    folder.mkdir()
    (folder / "completed.json").write_bytes(b"private schema handled by marker helper")
    (folder / "payload.zip").write_bytes(b"changed")
    monkeypatch.setattr(m, "local_folder", lambda *_: folder)
    monkeypatch.setattr(m, "marker", lambda *_: {"payload_bytes": 8, "payload_sha256": "0" * 64})
    with pytest.raises(ValueError, match="Delivered file changed"):
        m.checked_local(tmp_path, "day:2018-01-01", "a" * 64)


def test_offline_month_blocks_network(tmp_path, monkeypatch):
    def attempts_network(*_):
        import socket

        socket.create_connection(("example.com", 443))

    monkeypatch.setattr(m, "month_audit_offline", attempts_network)
    with pytest.raises(RuntimeError, match="Offline connection boundary"):
        m.month_audit(tmp_path, tmp_path, "2018-01")


def test_expired_deadline_prevents_scientific_work(tmp_path):
    with pytest.raises(TimeoutError, match="Audit runtime limit"):
        m.month_audit(tmp_path, tmp_path, "2018-01", deadline=-1)
    assert not list(tmp_path.iterdir())
