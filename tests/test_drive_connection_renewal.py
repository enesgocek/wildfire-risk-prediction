"""Renew the same private connection; failed checks must preserve previous bytes."""

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
m = importlib.import_module("connect_drive")


@pytest.fixture
def renewal(tmp_path, monkeypatch):
    target = tmp_path / "private" / "drive_connection.json"
    target.parent.mkdir()
    previous = dict(
        client_id="fixture.apps.googleusercontent.com",
        client_secret="fixture",
        refresh_token="fixture-old",
        scope=m.SCOPE,
        folder_id="fixture_folder_id",
    )
    target.write_text(json.dumps(previous), encoding="utf-8")
    before = target.read_bytes()
    returned = {**previous, "refresh_token": "fixture-new"}
    returned.pop("folder_id")
    folder = dict(
        id=previous["folder_id"],
        mimeType="application/vnd.google-apps.folder",
        trashed=False,
        capabilities={"canAddChildren": True},
    )
    calls = []

    class API:
        def __init__(self, value):
            assert value["folder_id"] == previous["folder_id"]

        def request(self, path):
            calls.append(("GET", path))
            return json.dumps(folder).encode()

        def create_file(self, *args):
            raise AssertionError("Renewal cannot create any Drive object")

    monkeypatch.setattr(m, "DriveAPI", API)
    monkeypatch.setattr(m, "authorize", lambda value: dict(returned))
    monkeypatch.setattr(
        m, "os", SimpleNamespace(name="nt", environ={"LOCALAPPDATA": str(tmp_path / "shadow")})
    )
    monkeypatch.setattr(sys, "argv", ["connect_drive.py", "--renew", "--connection", str(target)])
    return target, previous, before, returned, folder, calls


def test_renewal_uses_explicit_private_path_and_preserves_folder_client_scope(renewal, capsys):
    target, previous, _, _, _, calls = renewal
    m.main()
    result = json.loads(target.read_bytes())
    assert result == {**previous, "refresh_token": "fixture-new"}
    assert calls == [
        (
            "GET",
            f"/files/{previous['folder_id']}?fields=id,mimeType,trashed,capabilities(canAddChildren)",
        )
    ]
    assert not target.with_suffix(".pending").exists()
    output = capsys.readouterr().out
    for value in (
        "fixture-old",
        "fixture-new",
        "fixture.apps.googleusercontent.com",
        "fixture_folder_id",
    ):
        assert value not in output


@pytest.mark.parametrize(
    "change", ["folder_id", "trashed", "mime", "write_permission", "client", "secret", "scope"]
)
def test_failed_identity_access_checks_leave_old_connection_unchanged(renewal, change):
    target, _, before, returned, folder, _ = renewal
    if change == "folder_id":
        folder["id"] = "different_folder"
    elif change == "trashed":
        folder["trashed"] = True
    elif change == "mime":
        folder["mimeType"] = "application/zip"
    elif change == "write_permission":
        folder["capabilities"]["canAddChildren"] = False
    elif change == "client":
        returned["client_id"] = "different.apps.googleusercontent.com"
    elif change == "secret":
        returned["client_secret"] = "different-fixture"
    else:
        returned["scope"] = "wrong-scope"
    with pytest.raises(ValueError):
        m.main()
    assert target.read_bytes() == before and not target.with_suffix(".pending").exists()


def test_callback_failure_and_pending_collision_preserve_old_connection(renewal, monkeypatch):
    target, _, before, returned, _, _ = renewal

    def fail(value):
        raise RuntimeError("Authorization unavailable")

    monkeypatch.setattr(m, "authorize", fail)
    with pytest.raises(RuntimeError):
        m.main()
    assert target.read_bytes() == before
    monkeypatch.setattr(m, "authorize", lambda value: dict(returned))
    pending = target.with_suffix(".pending")
    pending.write_bytes(b"existing pending fixture")
    with pytest.raises(FileExistsError):
        m.main()
    assert target.read_bytes() == before and pending.read_bytes() == b"existing pending fixture"


def test_explicit_path_cannot_create_new_connection(renewal, monkeypatch):
    target, _, before, _, _, _ = renewal
    monkeypatch.setattr(sys, "argv", ["connect_drive.py", "--connection", str(target)])
    with pytest.raises(ValueError, match="renewal-only"):
        m.main()
    assert target.read_bytes() == before


@pytest.mark.parametrize(
    "message,label",
    [
        ("Browser authorization timed out; rerun locally", "BROWSER_TIMEOUT"),
        ("Browser could not open", "BROWSER_NOT_OPENED"),
        ("Renewed authorization must access the existing folder", "EXISTING_FOLDER_ACCESS_FAILED"),
        ("Drive HTTP 400; no secrets logged", "OAUTH_OR_DRIVE_HTTP_400"),
        ("arbitrary private response contents", "UNCLASSIFIED"),
    ],
)
def test_failure_classification_never_returns_arbitrary_message(message, label):
    assert m.safe_failure(RuntimeError(message)) == label
