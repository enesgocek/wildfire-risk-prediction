"""Only enum diagnostics, verified original code and deliberate metadata publication."""

import importlib.util
import io
import json
import sys
import types
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "production_manifest_doctor", ROOT / "scripts/cloud/diagnose_gcp_production_manifest.py"
)
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 503])
def test_exact_safe_transport_status(status):
    assert doctor.safe_error(RuntimeError(f"Drive HTTP {status}; no secrets logged")) == (
        f"GOOGLE_HTTP_{status}"
    )


@pytest.mark.parametrize(
    "secret",
    [
        "refresh_token=secret",
        '{"access_token":"secret"}',
        "Drive HTTP 403; private message",
        "https://example.invalid/?code=secret",
        "File name confidential",
    ],
)
def test_arbitrary_messages_do_not_enter_output(secret, capsys):
    def fail():
        raise RuntimeError(secret)

    with pytest.raises(SystemExit):
        doctor.stage("checked_stage", fail)
    assert capsys.readouterr().out == "FAIL checked_stage: RuntimeError\n"


def test_http_reasons_are_whitelisted_not_response_messages():
    body = {
        "error": {
            "message": "private filename and refresh_token=secret",
            "errors": [
                {"reason": "storageQuotaExceeded"},
                {"reason": "refresh_token=secret"},
            ],
        }
    }
    assert doctor.http_summary(json.dumps(body).encode()) == "storageQuotaExceeded"
    for bad in (b"private token", b"x" * 65537, b'{"error":{"errors":null}}'):
        assert doctor.http_summary(bad) == "UNCLASSIFIED"


def test_wrapper_keeps_original_failure_and_hides_ids_urls(capsys):
    url = "https://www.googleapis.com/upload/drive/v3/files?private=secret"
    body = b'{"error":{"message":"secret","errors":[{"reason":"rateLimitExceeded"}]}}'
    error = urllib.error.HTTPError(url, 403, "private secret", {}, io.BytesIO(body))

    def broken(request, timeout):
        assert timeout == 45
        raise error

    with pytest.raises(urllib.error.HTTPError) as got:
        doctor.diagnostic_opener(broken)(urllib.request.Request(url), timeout=45)
    assert got.value is error
    assert capsys.readouterr().out == "HTTP_DIAGNOSTIC UPLOAD 403 rateLimitExceeded\n"


def test_original_package_is_verified_before_import_or_connection():
    actual = ROOT / "outputs/gcp_production/package"
    assert doctor.verify_package(actual)["months"][0] == "2023-08"


def test_changed_manifest_cannot_run(tmp_path):
    (tmp_path / "production_manifest.json").write_text('{"private":"secret"}')
    with pytest.raises(ValueError, match="Expected original"):
        doctor.verify_package(tmp_path)


@pytest.mark.parametrize(
    "url,role",
    [
        ("https://oauth2.googleapis.com/token", "OAUTH"),
        ("https://www.googleapis.com/drive/v3/files/generateIds?count=1", "ID_ALLOCATION"),
        ("https://www.googleapis.com/drive/v3/files/private?alt=media", "DOWNLOAD"),
        ("https://www.googleapis.com/drive/v3/files?q=private", "LIST"),
        ("https://www.googleapis.com/drive/v3/files/private?fields=mimeType", "FILE_METADATA"),
    ],
)
def test_request_role_does_not_include_private_identifier(url, role):
    assert doctor.request_role(url) == role


@pytest.fixture
def run_fixture(tmp_path, monkeypatch):
    import pandas as pd

    sys.path.insert(0, str(ROOT / "scripts/cloud"))
    import verified_job_store as protocol

    payload = tmp_path / "months/2023-08/manifest.zip"
    payload.parent.mkdir(parents=True)
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("month.json", '{"checked_metadata":true}')
    progress = {
        "queue_manifest_sha256": doctor.EXPECTED_SCOPE,
        "status": "failed_checkpoints_retained",
        "pairs_processed_this_invocation": 0,
        "pairs_reused_this_invocation": 0,
        "days_verified_this_invocation": [],
    }
    (tmp_path / "progress.json").write_text(json.dumps(progress))
    calls = []

    class MemoryBackend(protocol.RehearsalFileStore):
        def create(self, key, data):
            calls.append("write")
            super().create(key, data)

    backend = MemoryBackend(tmp_path / "remote_fixture")
    backend.folder_id = "private_folder_id"
    backend.api = types.SimpleNamespace(
        opener=lambda *_: None,
        token=lambda: calls.append("token"),
        request=lambda path: (
            b'{"storageQuota":{"limit":"400000000000","usage":"31670000000"}}'
            if path.startswith("/about?")
            else b'{"mimeType":"application/vnd.google-apps.folder","trashed":false}'
        ),
    )
    spec = {"months": ["2023-08"], "files": {"run_gcp_production.py": "a" * 64}}
    rows = pd.DataFrame([{"day": "2023-08-01"}])

    def validate(path, *_):
        calls.append("science")
        with zipfile.ZipFile(path) as archive:
            assert json.loads(archive.read("month.json")) == {"checked_metadata": True}

    support = types.SimpleNamespace(
        read_scope=lambda *_: (spec, doctor.EXPECTED_SCOPE, None, rows),
        validate_month=validate,
        month_names=lambda *_: {"month.json"},
    )
    drive = types.SimpleNamespace(
        ProductionDriveStore=types.SimpleNamespace(from_file=lambda *_: backend)
    )
    monkeypatch.setattr(doctor, "verify_package", lambda *_: spec)
    monkeypatch.setattr(doctor, "load_modules", lambda *_: (support, drive, protocol))
    return tmp_path, calls, payload


def test_read_only_default_does_not_publish(run_fixture, capsys):
    work, calls, _ = run_fixture
    doctor.diagnose(work, work / "private.json", work)
    assert "write" not in calls
    assert calls[0] == "science"
    assert "READ_ONLY_COMPLETE" in capsys.readouterr().out


def test_explicit_publish_has_verified_completion_and_rerun_no_write(run_fixture, capsys):
    work, calls, _ = run_fixture
    doctor.diagnose(work, work / "private.json", work, publish=True)
    assert calls.count("write") == 2  # Payload first, completion after independent readback.
    assert calls.count("science") >= 4
    assert "MANIFEST_READY published" in capsys.readouterr().out
    doctor.diagnose(work, work / "private.json", work, publish=True)
    assert calls.count("write") == 2
    assert "existing verified completion" in capsys.readouterr().out


def test_bad_science_blocks_even_authentication(run_fixture, capsys):
    work, calls, payload = run_fixture
    payload.write_bytes(b"broken ZIP")
    with pytest.raises(SystemExit):
        doctor.diagnose(work, work / "private.json", work, publish=True)
    assert "token" not in calls and "write" not in calls
    assert "FAIL local_manifest_scientific_check" in capsys.readouterr().out


def test_changed_failure_scope_cannot_publish(run_fixture, capsys):
    work, calls, _ = run_fixture
    progress = json.loads((work / "progress.json").read_text())
    progress["pairs_processed_this_invocation"] = 1
    (work / "progress.json").write_text(json.dumps(progress))
    with pytest.raises(SystemExit):
        doctor.diagnose(work, work / "private.json", work, publish=True)
    assert "write" not in calls
    assert "FAIL first_failure_scope" in capsys.readouterr().out


def test_quota_output_contains_only_numeric_values():
    data = (
        b'{"storageQuota":{"limit":"400000000000","usage":"31670000000"},'
        b'"user":{"emailAddress":"private"}}'
    )
    assert doctor.quota_values(data) == {"limit": 400000000000, "usage": 31670000000}
    assert doctor.quota_values(b'{"storageQuota":{"usage":"0"}}') == {"limit": None, "usage": 0}
    with pytest.raises(ValueError, match="Quota"):
        doctor.quota_values(b'{"storageQuota":{"limit":"refresh_token=private","usage":"0"}}')


def test_expired_plan_quota_blocks_publication(run_fixture, capsys):
    work, calls, _ = run_fixture
    _, drive, _ = doctor.load_modules(work)
    backend = drive.ProductionDriveStore.from_file(work)
    original = backend.api.request
    backend.api.request = lambda path: (
        b'{"storageQuota":{"limit":"15000000000","usage":"31670000000"}}'
        if path.startswith("/about?")
        else original(path)
    )
    with pytest.raises(SystemExit):
        doctor.diagnose(work, work / "private.json", work, publish=True)
    assert "write" not in calls
    output = capsys.readouterr().out
    assert "DRIVE_FREE_GB -16.67" in output
    assert "FAIL metadata_storage_capacity" in output
