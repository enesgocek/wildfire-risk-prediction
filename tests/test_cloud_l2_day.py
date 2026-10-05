"""Bounded cloud scratch, exact references, and interruption-safe checkpoints."""

import ast
import importlib.util
import json
import shutil
import zipfile
from pathlib import Path

import pandas as pd
import pytest


def load(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).resolve().parents[1] / "scripts/cloud" / filename
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


day = load("day_test", "run_l2_day.py")
builder = load("day_builder_test", "build_l2_day_bundle.py")


@pytest.fixture
def example(monkeypatch, tmp_path):
    monkeypatch.setattr(day, "ROOT", tmp_path)
    manifest = {"day": "2019-01-14", "pairs": []}
    table = pd.DataFrame(
        {
            "grid_id": range(2899),
            "land": [1] * 2899,
            "daily_observation_status": ["unknown"] * 2899,
            "negative_label_permitted": [False] * 2899,
        }
    )
    original = tmp_path / "original"
    original.mkdir()
    for index in range(8):
        stem = f"sample_{index}"
        directory = original / stem
        directory.mkdir()
        sources = []
        audit = {
            "checked_at_utc": "reference",
            "sources": {},
            "negative_label_permitted": False,
            "qa": index,
        }
        for role in ("fire", "geolocation"):
            path = directory / f"{role}.nc"
            path.write_bytes(role.encode())
            source = {
                "role": role,
                "filename": path.name,
                "bytes": path.stat().st_size,
                "sha256": day.digest(path),
            }
            sources.append(source)
            audit["sources"][role] = {
                "path": str(path),
                "bytes": source["bytes"],
                "sha256": source["sha256"],
            }
        reference = tmp_path / "reference"
        reference.mkdir(exist_ok=True)
        (reference / f"{stem}.json").write_text(json.dumps(audit))
        table.to_csv(reference / f"{stem}.csv", index=False)
        manifest["pairs"].append(
            {
                "stem": stem,
                "sample_id": f"SNPP:{index}",
                "sources": sources,
                "local_directory": stem,
                "reference_audit": f"reference/{stem}.json",
                "reference_csv": f"reference/{stem}.csv",
            }
        )
    monkeypatch.setattr(day, "manifest_read", lambda: (manifest, "fixed-manifest"))
    monkeypatch.setattr(day.platform, "system", lambda: "Linux")
    calls = []

    def audit_process(command, **kwargs):
        pair = next(p for p in manifest["pairs"] if p["sample_id"] == command[3])
        calls.append(pair["sample_id"])
        output = tmp_path / "day/results"
        shutil.copyfile(tmp_path / pair["reference_audit"], output / f"{pair['stem']}_audit.json")
        shutil.copyfile(
            tmp_path / pair["reference_csv"], output / f"{pair['stem']}_grid_centers.csv"
        )
        day.atomic_json(output / f"{pair['stem']}_memory.json", {"child_peak_rss_bytes": 123456})

    monkeypatch.setattr(day.subprocess, "run", audit_process)
    return manifest, original, calls


def test_restart_reuses_verified_checkpoint_without_touching_local_sources(example):
    manifest, original, calls = example
    source_sha = {path: day.digest(path) for path in original.rglob("*.nc")}
    day.run(original, stop_after=1)
    assert len(calls) == 1
    day.run(original)
    assert len(calls) == 8 and len(set(calls)) == 8
    summary = json.loads((day.ROOT / "day/results/day_summary.json").read_text())
    assert summary["reused_pairs_this_invocation"] == 1
    assert summary["processed_pairs_this_invocation"] == 7
    assert summary["status"] == "passed_all_eight_references"
    assert source_sha == {path: day.digest(path) for path in source_sha}
    restored = day.ROOT / "restored"
    day.restore_results(day.ROOT / "l2_day_results.zip", manifest, "fixed-manifest", restored)
    assert day.checkpoint_read(manifest["pairs"][0], restored, "fixed-manifest")


@pytest.mark.parametrize("change", ["table", "qa", "manifest", "output_list"])
def test_checkpoint_cannot_hide_changed_results(example, change):
    manifest, original, _ = example
    day.run(original, stop_after=1)
    pair = manifest["pairs"][0]
    output = day.ROOT / "day/results"
    if change == "table":
        path = output / f"{pair['stem']}_grid_centers.csv"
        table = pd.read_csv(path)
        table.loc[0, "land"] = 2
        table.to_csv(path, index=False)
    elif change == "qa":
        path = output / f"{pair['stem']}_audit.json"
        audit = json.loads(path.read_text())
        audit["qa"] = 100
        day.atomic_json(path, audit)
        checkpoint_path = output / f"{pair['stem']}_checkpoint.json"
        record = json.loads(checkpoint_path.read_text())
        record["outputs"][path.name] = day.digest(path)
        day.atomic_json(checkpoint_path, record)
    else:
        path = output / f"{pair['stem']}_checkpoint.json"
        record = json.loads(path.read_text())
        if change == "manifest":
            record["manifest_sha256"] = "other"
        else:
            record["outputs"] = {"../../original/fire.nc": "fake"}
        day.atomic_json(path, record)
    with pytest.raises(ValueError):
        day.run(original)


@pytest.mark.parametrize("case", ["traversal", "uncheckpointed", "missing_csv"])
def test_restore_refuses_untrusted_or_incomplete_zip(example, case):
    manifest, original, _ = example
    day.run(original, stop_after=1)
    result = day.ROOT / "l2_day_results.zip"
    with zipfile.ZipFile(result) as archive:
        contents = {name: archive.read(name) for name in archive.namelist()}
    if case == "traversal":
        contents["../bad.py"] = b"untrusted"
    elif case == "uncheckpointed":
        contents.pop("sample_0_checkpoint.json")
    else:
        contents.pop("sample_0_grid_centers.csv")
    altered = day.ROOT / "altered.zip"
    with zipfile.ZipFile(altered, "w") as archive:
        for name, data in contents.items():
            archive.writestr(name, data)
    output = day.ROOT / "restored"
    with pytest.raises((ValueError, FileNotFoundError)):
        day.restore_results(altered, manifest, "fixed-manifest", output)
    assert not output.exists()


def test_cleanup_refuses_original_inputs_and_checks_scratch_hashes(example):
    manifest, original, _ = example
    pair = manifest["pairs"][0]
    with pytest.raises(ValueError, match="outside"):
        day.cleanup_pair(pair, original / pair["local_directory"])
    scratch = day.ROOT / "day/raw" / pair["stem"]
    scratch.mkdir(parents=True)
    source = scratch / pair["sources"][0]["filename"]
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="identity"):
        day.cleanup_pair(pair, scratch)
    assert source.exists()


def test_interrupted_partial_download_retries_only_scratch(example, monkeypatch):
    manifest, original, _ = example
    pair = manifest["pairs"][0]
    directory = day.ROOT / "day/raw" / pair["stem"]
    staging = directory / "staging"
    staging.mkdir(parents=True)
    (staging / "fire.nc").write_bytes(b"incomplete")
    (staging / "geolocation.nc").write_bytes(b"geolocation")
    calls = []

    def download(value, destination, strategy):
        assert strategy == "environment"
        assert not (destination / "fire.nc").exists()
        assert (destination / "geolocation.nc").read_bytes() == b"geolocation"
        calls.append(value)
        (destination / "fire.nc").write_bytes(b"fire")
        return 4

    monkeypatch.setattr(day.pilot, "download_sources", download)
    assert day.download_pair(pair, directory) == 4
    assert len(calls) == 1
    assert day.download_pair(pair, directory) == 0
    day.cleanup_pair(pair, directory)
    assert not list(directory.glob("*.nc"))
    assert len(list(original.rglob("*.nc"))) == 16


def test_day_notebook_keeps_isolation_and_runs_separate_resume_processes():
    notebook = builder.make_notebook("0" * 64)
    codes = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
    for code in codes:
        ast.parse(code)
    assert "system_site_packages=False" in codes[0]
    assert "--stop-after" in codes[2] and codes[2].count("subprocess.run") == 2
    assert "finally:" in codes[2] and "auth_env.clear()" in codes[2]
    assert "--restore-results" in codes[1]


@pytest.mark.parametrize("change", ["valid", "unfinished", "no_resume", "missing_memory", "labels"])
def test_independent_received_day_validation(example, monkeypatch, change):
    manifest, original, _ = example
    day.run(original, stop_after=1)
    day.run(original)
    validator = load("day_validator_test", "verify_l2_day_results.py")
    monkeypatch.setattr(validator, "day", day)
    bundle_files = {
        "scripts/cloud/run_l2_day.py": Path(day.__file__).read_bytes(),
        "scripts/cloud/run_l2_pilot.py": Path(day.pilot.__file__).read_bytes(),
        "scripts/cloud/verify_l2_pilot_results.py": Path(day.result_check.__file__).read_bytes(),
        "scripts/cloud/requirements_l2_pilot.txt": (
            Path(day.__file__).with_name("requirements_l2_pilot.txt").read_bytes()
        ),
    }
    for pair in manifest["pairs"]:
        for field in ("reference_audit", "reference_csv"):
            bundle_files[pair[field]] = (day.ROOT / pair[field]).read_bytes()
    manifest["bundle_files"] = {name: validator.sha(data) for name, data in bundle_files.items()}
    bundle = day.ROOT / "bundle.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        for name, data in bundle_files.items():
            archive.writestr(name, data)
        archive.writestr("day/manifest.json", json.dumps(manifest))
    with zipfile.ZipFile(day.ROOT / "l2_day_results.zip") as archive:
        contents = {name: archive.read(name) for name in archive.namelist()}
    summary = json.loads(contents["day_summary.json"])
    summary["environment"] = "authenticated_cloud_day"
    summary["python"] = "3.12.13"
    pins = dict(
        line.split("==")
        for line in bundle_files["scripts/cloud/requirements_l2_pilot.txt"].decode().splitlines()
        if line and not line.startswith("#")
    )
    summary["dependencies"] = {
        name: pins[name]
        for name in ("rasterio", "geopandas", "numpy", "pandas", "shapely", "pyproj", "earthaccess")
    }
    if change == "unfinished":
        summary["status"] = "checkpointed_partial"
    elif change == "no_resume":
        summary["reused_pairs_this_invocation"] = 0
        summary["processed_pairs_this_invocation"] = 8
    elif change == "labels":
        summary["negative_label_permitted"] = True
    elif change == "missing_memory":
        record = json.loads(contents["sample_0_checkpoint.json"])
        record["metrics"]["child_peak_rss_bytes"] = None
        contents["sample_0_checkpoint.json"] = json.dumps(record).encode()
        summary["records"][0] = record
    contents["day_summary.json"] = json.dumps(summary).encode()
    result = day.ROOT / "received.zip"
    with zipfile.ZipFile(result, "w") as archive:
        for name, data in contents.items():
            archive.writestr(name, data)
    if change == "valid":
        report = validator.verify(result, bundle)
        assert report["completed_pairs"] == 8
        assert report["resume_reused_pairs"] == 1
        assert report["negative_label_permitted"] is False
    else:
        with pytest.raises(ValueError):
            validator.verify(result, bundle)


@pytest.mark.parametrize("changed_audit", [False, True])
def test_cloud_run_keeps_only_one_pair_and_deletes_after_verified_zip(
    example, monkeypatch, changed_audit
):
    manifest, original, calls = example
    monkeypatch.setattr(day.importlib.metadata, "version", lambda _: "fixture")
    downloads = []

    def download(pair, directory):
        assert not list((day.ROOT / "day/raw").rglob("*.nc"))
        directory.mkdir(parents=True, exist_ok=True)
        for source in pair["sources"]:
            shutil.copyfile(
                original / pair["local_directory"] / source["filename"],
                directory / source["filename"],
            )
        downloads.append(pair["sample_id"])
        return sum(source["bytes"] for source in pair["sources"])

    monkeypatch.setattr(day, "download_pair", download)
    cleanup = day.cleanup_pair

    def checked_cleanup(pair, directory):
        output = day.ROOT / "day/results"
        assert day.checkpoint_read(pair, output, "fixed-manifest")
        with zipfile.ZipFile(day.ROOT / "l2_day_results.zip") as archive:
            assert f"{pair['stem']}_checkpoint.json" in archive.namelist()
        cleanup(pair, directory)

    monkeypatch.setattr(day, "cleanup_pair", checked_cleanup)
    if changed_audit:
        audit_process = day.subprocess.run

        def changed(command, **kwargs):
            audit_process(command, **kwargs)
            path = day.ROOT / "day/results/sample_0_audit.json"
            audit = json.loads(path.read_text())
            audit["qa"] = "changed"
            day.atomic_json(path, audit)

        monkeypatch.setattr(day.subprocess, "run", changed)
        with pytest.raises(ValueError, match="Full audit differs"):
            day.run()
        assert len(list((day.ROOT / "day/raw").rglob("*.nc"))) == 2
        assert not (day.ROOT / "l2_day_results.zip").exists()
    else:
        day.run()
        assert len(calls) == len(downloads) == 8
        assert not list((day.ROOT / "day/raw").rglob("*.nc"))
    assert len(list(original.rglob("*.nc"))) == 16
