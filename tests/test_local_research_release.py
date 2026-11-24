"""Container integrity must fail on missing, changed or extra members."""

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/quality/verify_local_research_release.py"
SPEC = importlib.util.spec_from_file_location("local_release_verifier", SCRIPT)
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def sample(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    data = package / "data.txt"
    data.write_text("unknown target\n", encoding="utf-8")
    manifest = package / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "files": {
                    "data.txt": {
                        "sha256": verifier.sha256(data),
                        "bytes": data.stat().st_size,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    with zipfile.ZipFile(tmp_path / "research_release.zip", "w") as archive:
        for path in (data, manifest):
            archive.write(path, path.name)
    receipt = {
        "manifest_sha256": verifier.sha256(manifest),
        "zip_sha256": verifier.sha256(tmp_path / "research_release.zip"),
    }
    (tmp_path / "readback.json").write_text(json.dumps(receipt), encoding="utf-8")
    return tmp_path


def test_release_passes_and_changed_csv_fails(tmp_path):
    release = sample(tmp_path)
    assert verifier.verify(release)["files_including_manifest"] == 2
    (release / "package/data.txt").write_text("changed target\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Package byte"):
        verifier.verify(release)


def test_zip_extra_member_rejected_even_if_outer_hash_updated(tmp_path):
    release = sample(tmp_path)
    archive = release / "research_release.zip"
    with zipfile.ZipFile(archive, "a") as zipped:
        zipped.writestr("../escape.txt", "extra")
    receipt = json.loads((release / "readback.json").read_bytes())
    receipt["zip_sha256"] = verifier.sha256(archive)
    (release / "readback.json").write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="ZIP inventory"):
        verifier.verify(release)


def test_missing_file_and_changed_container_rejected(tmp_path):
    release = sample(tmp_path)
    (release / "package/data.txt").unlink()
    with pytest.raises(ValueError, match="inventory"):
        verifier.verify(release)
    with (release / "research_release.zip").open("ab") as stream:
        stream.write(b"unexpected")
    with pytest.raises(ValueError, match="container hash"):
        verifier.verify(release)
