"""Drive adapter failure semantics; no real account or network access."""

import importlib.util
import json
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "drive_store_test", ROOT / "scripts/cloud/drive_job_store.py"
)
drive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drive)
KEY = "jobs/" + "a" * 64 + "/" + "b" * 64 + "/" + "c" * 64 + ".zip"


class FakeAPI:
    def __init__(self):
        self.files, self.data, self.writes = [], {}, 0

    def listing(self, query):
        assert "trashed = false" in query and "in parents" in query
        return self.files

    def create_file(self, metadata, data):
        identity = f"object{self.writes}"
        self.writes += 1
        self.files.append({**metadata, "id": identity, "size": str(len(data))})
        self.data[identity] = data
        return identity

    def request(self, path):
        assert path.endswith("?alt=media")
        return self.data[path.split("/")[2].split("?")[0]]


@pytest.fixture
def backend():
    return drive.DriveJobStore(FakeAPI(), "folder_1234567890")


def test_long_checkpoint_key_and_idempotent_write(backend):
    assert backend.get(KEY) is None
    backend.create(KEY, b"science")
    backend.create(KEY, b"science")
    assert backend.api.writes == 1
    assert backend.get(KEY) == b"science"
    assert backend.used_bytes("jobs/" + "a" * 64) == 7
    assert backend.used_bytes("jobs/" + "d" * 64) == 0
    assert all(len(v) <= 124 for v in backend.api.files[0]["appProperties"].values())


def test_changed_object_never_overwritten(backend):
    backend.create(KEY, b"original")
    with pytest.raises(ValueError, match="collision"):
        backend.create(KEY, b"changed")
    assert backend.api.writes == 1


def test_duplicate_ids_fail_closed(backend):
    backend.create(KEY, b"science")
    backend.api.files.append({**backend.api.files[0], "id": "another"})
    with pytest.raises(ValueError, match="Duplicate"):
        backend.get(KEY)


def test_unknown_foreign_object_blocks_budget_and_reads(backend):
    backend.api.files.append({"id": "unexpected", "name": "unknown", "size": "1"})
    with pytest.raises(ValueError, match="Foreign"):
        backend.get(KEY)


@pytest.mark.parametrize("size", ["-10", "0", "nan", 2, True, "150000001"])
def test_invalid_size_cannot_reduce_storage_budget(backend, size):
    backend.create(KEY, b"science")
    backend.api.files[0]["size"] = size
    with pytest.raises(ValueError, match="metadata"):
        backend.used_bytes("jobs/" + "a" * 64)


def test_listing_error_is_not_a_missing_object(backend):
    def broken(query):
        raise RuntimeError("service unavailable")

    backend.api.listing = broken
    with pytest.raises(RuntimeError):
        backend.get(KEY)


def test_readback_size_mismatch(backend):
    backend.create(KEY, b"science")
    backend.api.data["object0"] = b"bad"
    with pytest.raises(ValueError, match="size"):
        backend.get(KEY)


@pytest.mark.parametrize("mime", sorted(drive.PAYLOAD_MIMES))
def test_drive_reports_zip_content_type_without_changing_payload(backend, mime):
    backend.create(KEY, b"science")
    backend.api.files[0]["mimeType"] = mime
    assert backend.get(KEY) == b"science"
    backend.create(KEY, b"science")
    assert backend.api.writes == 1


@pytest.mark.parametrize("mime", sorted(drive.MARKER_MIMES))
def test_json_completion_content_type(backend, mime):
    key = "jobs/" + "a" * 64 + "/" + "b" * 64 + "/completed.json"
    backend.create(key, b'{"done":true}')
    backend.api.files[0]["mimeType"] = mime
    assert backend.get(key) == b'{"done":true}'


@pytest.mark.parametrize(
    "mime",
    [
        "application/vnd.google-apps.document",
        "application/vnd.google-apps.shortcut",
        "text/html",
        "image/png",
    ],
)
def test_unexpected_or_google_editor_types_rejected(backend, mime):
    backend.create(KEY, b"science")
    backend.api.files[0]["mimeType"] = mime
    with pytest.raises(ValueError, match="type"):
        backend.get(KEY)


def test_zip_type_cannot_be_used_as_completion_marker(backend):
    key = "jobs/" + "a" * 64 + "/" + "b" * 64 + "/completed.json"
    backend.create(key, b'{"done":true}')
    backend.api.files[0]["mimeType"] = "application/zip"
    with pytest.raises(ValueError, match="role"):
        backend.get(key)


def test_recognized_mime_still_rejects_changed_bytes(backend):
    backend.create(KEY, b"science")
    backend.api.files[0]["mimeType"] = "application/zip"
    backend.api.data["object0"] = b"changed"
    with pytest.raises(ValueError, match="collision"):
        backend.create(KEY, b"science")


@pytest.mark.parametrize("key", ["/absolute", "../bad", "jobs//bad", "jobs/../bad", "a\\b"])
def test_invalid_keys(backend, key):
    with pytest.raises(ValueError):
        backend.create(key, b"x")


def connection():
    return {
        "scope": drive.SCOPE,
        "client_id": "client",
        "client_secret": "private",
        "refresh_token": "hidden",
    }


def test_transport_has_finite_retries_and_redacts_error():
    calls, delays = [], []

    def broken(request, timeout):
        calls.append(timeout)
        raise urllib.error.HTTPError(request.full_url, 503, "secret response", {}, None)

    api = drive.DriveAPI(connection(), opener=broken, sleep=delays.append)
    with pytest.raises(RuntimeError, match="HTTP 503") as error:
        api.wire(drive.API + "/files", "GET", retry=True)
    assert calls == [45, 45, 45] and delays == [2, 4]
    assert "secret" not in str(error.value).replace("secrets", "")


def test_nonretryable_auth_failure_not_retried():
    calls = []

    def denied(request, timeout):
        calls.append(True)
        raise urllib.error.HTTPError(request.full_url, 401, "refresh_token", {}, None)

    api = drive.DriveAPI(connection(), opener=denied)
    with pytest.raises(RuntimeError, match="HTTP 401"):
        api.wire(drive.API + "/files", "GET", retry=True)
    assert len(calls) == 1


def test_full_drive_scope_refused():
    with pytest.raises(ValueError, match="scope"):
        drive.DriveAPI({**connection(), "scope": "https://www.googleapis.com/auth/drive"})


def test_redirect_refused_before_credentials_forwarded():
    with pytest.raises(RuntimeError, match="redirect"):
        drive.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.example")


def test_plaintext_endpoint_refused_before_credentials_sent():
    api = drive.DriveAPI(connection())
    with pytest.raises(ValueError, match="endpoint"):
        api.wire("http://www.googleapis.com/drive/v3/files", "GET")


def test_incomplete_listing_refused():
    api = drive.DriveAPI(connection())
    api.request = lambda path: json.dumps({"incompleteSearch": True, "files": []}).encode()
    with pytest.raises(ValueError, match="Incomplete"):
        api.listing("query")
