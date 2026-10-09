"""Privacy checker does not disclose detected credentials and scans index content."""

import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/quality/check_git_privacy.py"
SPEC = importlib.util.spec_from_file_location("git_privacy", PATH)
privacy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(privacy)


@pytest.mark.parametrize(
    "name",
    [".env", "outputs/report.json", "data/raw/source.csv", "credentials.json", "private.docx"],
)
def test_private_paths_are_blocked_even_if_git_tracks_them(name):
    assert privacy.findings(name, b"harmless")[0]["rule"] == "private_or_bulk_path"


def test_secret_is_detected_without_printing_value():
    token = b"gh" + b"p_" + b"x" * 36
    results = privacy.findings("config.py", b"first line\n" + token)
    assert results == [{"path": "config.py", "rule": "github_token", "line": 2}]
    assert token.decode() not in str(results)


def test_public_hash_and_template_are_not_credentials():
    assert privacy.findings(".env.example", b"EARTHDATA_PASSWORD=\n") == []
    assert privacy.findings("docs/report.md", b"SHA256 " + b"a" * 64) == []


def test_staged_scan_reads_exact_index_blob(monkeypatch):
    calls = []

    def fake_git(*args):
        calls.append(args)
        if args[0] == "diff":
            return b"config.py\0"
        return b"ya" + b"29." + b"x" * 30

    monkeypatch.setattr(privacy, "git", fake_git)
    report = privacy.scan("staged")
    assert report["status"] == "blocked"
    assert calls[-1] == ("show", ":config.py")
