"""Private VM replacement stays confined and checks access before changing old bytes."""

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
m = importlib.import_module("install_renewed_drive_connection")
SCOPE = "https://www.googleapis.com/auth/drive.file"


@pytest.fixture
def private(tmp_path):
    old = dict(
        client_id="fixture.apps.googleusercontent.com",
        client_secret="fixture",
        refresh_token="fixture-old",
        scope=SCOPE,
        folder_id="fixture_folder_id",
    )
    new = {**old, "refresh_token": "fixture-new"}
    source = tmp_path / "drive_connection.json"
    target = tmp_path / ".config/wildfire/drive_connection.json"
    target.parent.mkdir(parents=True)
    source.write_text(json.dumps(new), encoding="utf-8")
    target.write_text(json.dumps(old), encoding="utf-8")
    folder = dict(
        id=new["folder_id"],
        mimeType="application/vnd.google-apps.folder",
        trashed=False,
        capabilities={"canAddChildren": True},
    )
    calls = []

    class API:
        def __init__(self, connection):
            assert connection == json.loads(source.read_bytes())

        def token(self):
            calls.append("token")
            return "fixture-access"

        def request(self, path):
            calls.append("GET")
            return json.dumps(folder).encode()

    return tmp_path, source, target, folder, API, calls


def test_only_private_file_is_replaced_after_token_and_folder_checks(private, capsys):
    home, source, target, _, api, calls = private
    raw = source.read_bytes()
    sentinel = home / "scientific_zip.fixture"
    sentinel.write_bytes(b"unchanged")
    m.install(home, api, SCOPE)
    assert (
        target.read_bytes() == raw and not source.exists() and sentinel.read_bytes() == b"unchanged"
    )
    assert calls == ["token", "GET"]
    assert capsys.readouterr().out == (
        "PASS same_client_scope_folder\n"
        "PASS renewed_token_and_existing_folder\nPASS private_connection_installed\n"
    )


@pytest.mark.parametrize(
    "change",
    ["client_id", "client_secret", "folder_id", "scope", "extra", "folder_denied", "trashed"],
)
def test_changed_identity_or_access_keeps_both_private_files(private, change):
    home, source, target, folder, api, calls = private
    data = json.loads(source.read_bytes())
    if change in ("client_id", "client_secret", "folder_id", "scope"):
        data[change] = "different-fixture"
    elif change == "extra":
        data["extra"] = "not allowed"
    elif change == "folder_denied":
        folder["capabilities"]["canAddChildren"] = False
    else:
        folder["trashed"] = True
    source.write_text(json.dumps(data), encoding="utf-8")
    before = source.read_bytes(), target.read_bytes()
    with pytest.raises(ValueError):
        m.install(home, api, SCOPE)
    assert (source.read_bytes(), target.read_bytes()) == before
    if change not in ("folder_denied", "trashed"):
        assert calls == []


def test_oauth_rejection_does_not_overwrite_old_token(private):
    home, source, target, _, api, _ = private
    before = source.read_bytes(), target.read_bytes()

    class Broken(api):
        def token(self):
            raise RuntimeError("Drive HTTP 400; no secrets logged")

    with pytest.raises(RuntimeError):
        m.install(home, Broken, SCOPE)
    assert (source.read_bytes(), target.read_bytes()) == before


def test_concurrent_private_file_change_is_not_overwritten(private):
    home, source, target, _, api, _ = private

    class Changed(api):
        def request(self, path):
            target.write_bytes(target.read_bytes() + b" ")
            return super().request(path)

    with pytest.raises(ValueError, match="changed during checks"):
        m.install(home, Changed, SCOPE)
    assert source.exists() and target.read_bytes().endswith(b" ")
