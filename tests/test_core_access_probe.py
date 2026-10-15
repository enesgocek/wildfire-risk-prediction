"""Header evidence must use live requests, preserve scope and never leak redirect secrets."""

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


def module():
    spec = importlib.util.spec_from_file_location(
        "test_access_probe",
        Path(__file__).resolve().parents[1] / "scripts/firms/probe_observation_core_access.py",
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def source():
    name = "VNP14IMG.A2021046.0100.002.2024000000000.nc"
    return {
        "source_id": "SNPP:2021046.0100|fire",
        "sample_id": "SNPP:2021046.0100",
        "source_day": "2021-02-15",
        "role": "fire",
        "filename": name,
        "bytes": 6,
        "sha256": "a" * 64,
        "url": "https://data.lpdaac.earthdatacloud.nasa.gov/path/" + name,
    }


class Response:
    def __init__(self, status=303, location=None, length="6"):
        self.url = source()["url"]
        self.status_code = status
        self.headers = {
            "Content-Length": length,
            "Location": location
            or self.url.split("/path/")[0] + "/error?error=invalid_token&token=synthetic-private",
        }
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True

    @property
    def content(self):
        raise AssertionError("Body must not be read")

    def iter_content(self, *_):
        raise AssertionError("Body must not be read")


class Session:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_provider_error_is_classified_without_capturing_private_query():
    m = module()
    r = Response()
    session = Session(r)
    result = m.inspect_source(session, source())
    assert result["redirect"]["path_kind"] == "provider_error"
    assert result["redirect"]["oauth_error_code"] == "invalid_token"
    assert result["exact_signed_object"] is False
    assert "synthetic-private" not in json.dumps(result)
    assert len(session.calls) == 1 and session.calls[0][1]["allow_redirects"] is False
    assert session.calls[0][1]["stream"] is True and r.closed


def test_unknown_host_and_path_are_never_serialized():
    m = module()
    result = m.redirect_summary(
        "https://synthetic-private.example/private-path?error=private-error", source()["url"]
    )
    assert (
        result["public_host"] == result["path_kind"] == result["oauth_error_code"] == "unclassified"
    )
    assert "private" not in json.dumps(result)


def test_direct_length_mismatch_is_evidence_not_content_success():
    result = module().inspect_source(Session(Response(status=200, length="7")), source())
    assert result["status"] == "direct_headers_only"
    assert result["content_length_matches"] is False and result["body_bytes_read"] == 0


def test_altered_origin_is_rejected_and_body_closed():
    r = Response(status=200)
    r.url = "https://synthetic-private.example/"
    result = module().inspect_source(Session(r), source())
    assert result["status"] == "request_failed" and result["safe_code"] == "origin_response_url"
    assert "synthetic-private" not in json.dumps(result) and r.closed


def test_network_exception_text_is_not_recorded():
    class Broken:
        def get(self, *_args, **_kwargs):
            raise ValueError("synthetic-private-token")

    result = module().inspect_source(Broken(), source())
    assert result["safe_code"] == "unclassified" and "synthetic-private" not in json.dumps(result)


def test_cached_data_never_replaces_the_two_header_requests():
    m = module()
    session = Session(Response(status=200))
    m.inspect_source(session, source())
    m.inspect_source(session, source())
    assert len(session.calls) == 2  # Header probe does not read the raw cache at all.


def test_parent_timeout_keeps_secrets_out_of_command_and_receipt(tmp_path, monkeypatch):
    m = module()
    monkeypatch.setattr(m.logging, "disable", lambda *_: None)
    fake = SimpleNamespace(
        latest_plan=lambda: tmp_path / "native_plan.json",
        load_plan=lambda _: ({}, {"sample_id": "fixed"}),
        write_json=lambda p, d: p.write_text(json.dumps(d), encoding="utf-8"),
    )
    monkeypatch.setattr(m, "runner", lambda: fake)
    monkeypatch.setattr(m, "OUTPUT", tmp_path / "out")
    monkeypatch.setattr(m, "digest", lambda _: "a" * 64)
    monkeypatch.setattr(m, "private_token", lambda: "synthetic-private-token")
    monkeypatch.setenv("EARTHDATA_PASSWORD", "synthetic-private-password")

    def timeout(command, **kwargs):
        assert "synthetic-private" not in " ".join(command)
        assert "EARTHDATA_PASSWORD" not in kwargs["env"]
        assert kwargs["timeout"] == 120 and kwargs["stdout"] == subprocess.DEVNULL
        raise subprocess.TimeoutExpired(command, 120)

    monkeypatch.setattr(m.subprocess, "run", timeout)
    assert m.run() == 1
    receipt = next((tmp_path / "out").glob("*/launcher_receipt.json")).read_text()
    assert "synthetic-private" not in receipt and json.loads(receipt)["status"] == "hard_timeout"


def test_private_login_refuses_noninteractive_input(monkeypatch):
    m = module()
    monkeypatch.setattr(m.sys.stdin, "isatty", lambda: False)
    with pytest.raises(ValueError, match="interactive"):
        m.private_token()


def test_real_requests_session_never_consumes_redirect_body():
    import requests

    class Raw:
        def read(self, *_args, **_kwargs):
            raise AssertionError("Redirect body must not be consumed by Requests")

        def stream(self, *_args, **_kwargs):
            raise AssertionError("Redirect body must not be streamed by Requests")

        def close(self):
            pass

        def release_conn(self):
            pass

    class Adapter(requests.adapters.BaseAdapter):
        def send(self, request, **kwargs):
            assert kwargs["stream"] is True
            r = requests.Response()
            r.status_code = 303
            r.url = request.url
            r.request = request
            r.headers["Location"] = "https://synthetic-private.example/?token=private"
            r.raw = Raw()
            return r

        def close(self):
            pass

    m = module()
    with m.header_session() as session:
        session.trust_env = False
        session.mount("https://", Adapter())
        result = m.inspect_source(session, source())
    assert result["status"] == "redirect_headers_only" and result["body_bytes_read"] == 0
    assert "private" not in json.dumps(result)
