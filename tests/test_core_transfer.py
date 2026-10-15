"""Fail closed on bad bytes, low disk, partial writes, redirects and runner timeout."""

import hashlib
import importlib.util
import json
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlunsplit

import pytest

from wildfire_risk_prediction import core_transfer as transfer


def source(data=b"native"):
    return {
        "source_id": "SNPP:2021046.0100|fire",
        "source_day": "2021-02-15",
        "sample_id": "SNPP:2021046.0100",
        "role": "fire",
        "filename": "VNP14IMG.A2021046.0100.002.2024000000000.nc",
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "url": "https://data.lpdaac.earthdatacloud.nasa.gov/path/VNP14IMG.A2021046.0100.002.2024000000000.nc",
        "provider_checksum": {"Algorithm": "MD5", "Value": hashlib.md5(data).hexdigest()},
    }


class Response:
    def __init__(self, record, chunks=(b"na", b"tive"), status=200, headers=None):
        self.status_code, self.url = status, record["url"]
        self.headers = {} if headers is None else headers
        self.chunks = chunks

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def iter_content(self, chunk_size):
        yield from self.chunks


class Session:
    def __init__(self, response):
        self.response, self.calls = response, []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def run(record, cache, response=None, **kwargs):
    session = Session(response or Response(record))
    result = transfer.transfer_one(
        session,
        record,
        cache,
        deadline=kwargs.get("deadline", time.monotonic() + 30),
        cache_limit_bytes=kwargs.get("limit", 10000),
        reserve_bytes=kwargs.get("reserve", 0),
    )
    return session, result


def test_success_writes_only_verified_bytes_and_reuses_without_request(tmp_path):
    r = source()
    session, a = run(r, tmp_path)
    assert a["network_bytes"] == 6 and a["provider_checksum_verified"]
    assert not a["reused"] and (tmp_path / r["filename"]).read_bytes() == b"native"
    assert session.calls[0][1]["allow_redirects"] is False
    assert session.calls[0][1]["headers"] == {"Accept-Encoding": "identity"}
    second, b = run(r, tmp_path)
    assert b["reused"] and b["network_bytes"] == 0 and not second.calls


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/file.nc",
        "http://data.lpdaac.earthdatacloud.nasa.gov/file.nc",
        "https://data.lpdaac.earthdatacloud.nasa.gov:8443/file.nc",
        urlunsplit(
            ("https", "user:password@data.lpdaac.earthdatacloud.nasa.gov", "/file.nc", "", "")
        ),
    ],
)
def test_unapproved_url_never_reaches_session(tmp_path, url):
    r = source()
    r["url"] = url
    s = Session(Response(r))
    with pytest.raises(ValueError):
        transfer.transfer_one(
            s, r, tmp_path, deadline=time.monotonic() + 1, cache_limit_bytes=100, reserve_bytes=0
        )
    assert not s.calls


def test_query_token_is_rejected_before_transfer():
    r = source()
    r["url"] += "?signature=dummy"
    with pytest.raises(ValueError):
        transfer.source_url(r)


@pytest.mark.parametrize("chunks", [(b"short",), (b"native!",), (b"wrong!",)])
def test_truncated_oversized_or_corrupted_bytes_remain_partial(tmp_path, chunks):
    r = source()
    with pytest.raises(ValueError):
        run(r, tmp_path, Response(r, chunks=chunks))
    assert not (tmp_path / r["filename"]).exists()
    assert (tmp_path / (r["filename"] + ".part")).exists()


def test_existing_same_size_corruption_is_not_redownloaded_or_overwritten(tmp_path):
    r = source()
    p = tmp_path / r["filename"]
    p.write_bytes(b"wrong!")
    with pytest.raises(ValueError):
        run(r, tmp_path)
    assert p.read_bytes() == b"wrong!"


def test_partial_is_preserved_and_never_counted_as_reusable(tmp_path):
    r = source()
    p = tmp_path / (r["filename"] + ".part")
    p.write_bytes(b"na")
    with pytest.raises(ValueError):
        run(r, tmp_path)
    assert p.read_bytes() == b"na"


@pytest.mark.parametrize("status", [302, 401, 403, 404, 500])
def test_auth_redirect_and_http_failures_write_no_native_file(tmp_path, status):
    r = source()
    with pytest.raises(ValueError):
        run(r, tmp_path, Response(r, status=status))
    assert not list(tmp_path.iterdir())


def test_header_length_mismatch_fails_before_writing(tmp_path):
    r = source()
    with pytest.raises(ValueError):
        run(r, tmp_path, Response(r, headers={"Content-Length": "9"}))
    assert not list(tmp_path.iterdir())


def test_cache_limit_and_disk_reserve_do_not_start_transfer(tmp_path, monkeypatch):
    r = source()
    with pytest.raises(ValueError):
        run(r, tmp_path, limit=5)
    monkeypatch.setattr(transfer.shutil, "disk_usage", lambda _: SimpleNamespace(free=10))
    with pytest.raises(ValueError):
        run(r, tmp_path, reserve=5)
    assert not list(tmp_path.iterdir())


def test_expired_deadline_does_not_start_transfer(tmp_path):
    with pytest.raises(ValueError):
        run(source(), tmp_path, deadline=time.monotonic() - 1)
    assert not list(tmp_path.iterdir())


def test_provider_checksum_conflict_fails_even_if_historical_sha_matches(tmp_path):
    r = source()
    r["provider_checksum"]["Value"] = "0" * 32
    with pytest.raises(ValueError):
        run(r, tmp_path)
    assert not (tmp_path / r["filename"]).exists()


def runner():
    p = Path(__file__).resolve().parents[1] / "scripts/firms/run_observation_core_pair.py"
    spec = importlib.util.spec_from_file_location("bounded_core_runner_test", p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parent_timeout_uses_hard_cap_and_keeps_token_out_of_arguments_and_files(
    tmp_path, monkeypatch
):
    module = runner()
    monkeypatch.setattr(module.logging, "disable", lambda *_: None)
    monkeypatch.setattr(module, "OUTPUT", tmp_path)
    monkeypatch.setattr(
        module,
        "load_plan",
        lambda _: ({"hard_runtime_seconds": 900}, {"sample_id": "fixed", "bytes": 6}),
    )
    monkeypatch.setattr(module, "digest", lambda _: "a" * 64)
    monkeypatch.setenv("EARTHDATA_TOKEN", "synthetic-test-only")

    def timeout(command, **kwargs):
        assert kwargs["timeout"] == 900 and kwargs["stdout"] == subprocess.DEVNULL
        assert "synthetic-test-only" not in " ".join(command)
        assert "EARTHDATA_PASSWORD" not in kwargs["env"]
        raise subprocess.TimeoutExpired(command, 900)

    monkeypatch.setattr(module.subprocess, "run", timeout)
    assert module.run(tmp_path / "plan.json", False) == 1
    path = next(tmp_path.glob("*/launcher_receipt.json"))
    assert json.loads(path.read_text())["status"] == "hard_timeout_partial_and_lock_retained"
    assert "synthetic-test-only" not in path.read_text()


def test_private_prompt_refuses_non_interactive_input(tmp_path, monkeypatch):
    module = runner()
    monkeypatch.setattr(module.logging, "disable", lambda *_: None)
    monkeypatch.setattr(module, "load_plan", lambda _: ({}, {"sample_id": "fixed", "bytes": 6}))
    monkeypatch.setattr(module.sys.stdin, "isatty", lambda: False)
    with pytest.raises(ValueError, match="interactive terminal"):
        module.run(tmp_path / "plan.json", True)
