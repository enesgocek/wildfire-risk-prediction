"""Test the VM pilot package boundary, readback and private environment handling."""

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location(
    "gcp_portability", ROOT / "scripts/cloud/run_gcp_portability.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_inherited_credentials_and_python_overrides_are_removed(monkeypatch):
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "EARTHDATA_USERNAME",
        "EARTHDATA_PASSWORD",
        "EARTHDATA_TOKEN",
    ):
        monkeypatch.setenv(name, "private-value")
    result = runner.clean_environment()
    assert not any(
        name in result
        for name in (
            "PYTHONPATH",
            "PYTHONHOME",
            "EARTHDATA_USERNAME",
            "EARTHDATA_PASSWORD",
            "EARTHDATA_TOKEN",
        )
    )
    assert result["PYTHONNOUSERSITE"] == "1"


def test_frozen_package_hash_checked_before_extraction(tmp_path):
    payload = tmp_path / "bad.zip"
    payload.write_bytes(b"not a trusted ZIP")
    destination = tmp_path / "native"
    with pytest.raises(ValueError, match="identity"):
        runner.unpack(payload, destination)
    assert not destination.exists()


@pytest.fixture
def results(tmp_path):
    output = tmp_path / "results"
    output.mkdir()
    summary = {
        "status": "passed_exact_local_reference_comparison",
        "sample_id": runner.SOURCE_ID,
        "manifest_sha256": "a" * 64,
        "negative_label_permitted": False,
    }
    for name in runner.RESULT_NAMES:
        (output / name).write_text(
            json.dumps(summary) if name.endswith("verification.json") else "verified data",
            encoding="utf-8",
        )
    return output, tmp_path / "export/result.zip"


def test_result_zip_contains_only_three_verified_products(results):
    output, target = results
    runner.export_results(output, target, "a" * 64)
    with zipfile.ZipFile(target) as archive:
        assert set(archive.namelist()) == runner.RESULT_NAMES
        assert archive.testzip() is None
        for name in runner.RESULT_NAMES:
            assert archive.read(name) == (output / name).read_bytes()


@pytest.mark.parametrize(
    "key,value",
    [
        ("status", "partial"),
        ("sample_id", "N20:other"),
        ("manifest_sha256", "b" * 64),
        ("negative_label_permitted", True),
    ],
)
def test_wrong_or_incomplete_result_never_published(results, key, value):
    output, target = results
    p = output / "cloud_pilot_verification.json"
    summary = json.loads(p.read_text())
    summary[key] = value
    p.write_text(json.dumps(summary))
    with pytest.raises(ValueError):
        runner.export_results(output, target, "a" * 64)
    assert not target.exists()


def test_unexpected_output_is_not_exported(results):
    output, target = results
    (output / "unexpected.txt").write_text("extra")
    with pytest.raises(ValueError, match="members"):
        runner.export_results(output, target, "a" * 64)
    assert not target.exists()


def test_resume_does_not_clear_or_remove_other_files(results):
    output, target = results
    runner.export_results(output, target, "a" * 64)
    sibling = target.parent / "other-project.txt"
    sibling.write_text("preserved")
    runner.export_results(output, target, "a" * 64)
    assert sibling.read_text() == "preserved"
    assert not list(target.parent.glob("*.pending"))


def test_local_rehearsal_keeps_original_sources_intact(tmp_path):
    original = tmp_path / "original"
    original.mkdir()
    source = original / "source.nc"
    source.write_bytes(b"fixed source")
    manifest = {
        "sources": [
            {
                "filename": source.name,
                "bytes": source.stat().st_size,
                "sha256": runner.digest(source),
            }
        ]
    }
    target = tmp_path / "job/native/raw"
    runner.link_local_sources(manifest, original, target)
    assert (target / source.name).samefile(source)
    assert source.read_bytes() == b"fixed source"
    runner.link_local_sources(manifest, original, target)


def test_modified_local_source_rejected_before_linking(tmp_path):
    original = tmp_path / "original"
    original.mkdir()
    (original / "source.nc").write_bytes(b"wrong")
    target = tmp_path / "job/native/raw"
    manifest = {"sources": [{"filename": "source.nc", "bytes": 100, "sha256": "a" * 64}]}
    with pytest.raises(ValueError, match="source changed"):
        runner.link_local_sources(manifest, original, target)
    assert not (target / "source.nc").exists()
