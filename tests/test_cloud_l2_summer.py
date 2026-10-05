"""Approved scope, untrusted ZIPs, persistence-before-cleanup and restart behavior."""

import ast
import copy
import importlib.util
import json
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/cloud" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


worker = load("summer_test", "run_l2_summer.py")
builder = load("summer_builder_test", "build_l2_summer_bundle.py")


def test_notebook_clean_cpu_environment_and_one_sequential_job():
    notebook = builder.notebook("a" * 64)
    source = "\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            ast.parse("".join(cell["source"]))
            assert cell["outputs"] == [] and cell["execution_count"] is None
    assert "getpass.getpass" in source and "auth_env.clear()" in source
    assert "--verify-only" in source and "flush_and_unmount" in source
    assert "subprocess.run(command, check=True, env=auth_env)" in source
    assert "system_site_packages=False" in source
    assert "a" * 64 in source


def metadata_example():
    row = SimpleNamespace(
        filename="VJ103IMG.A2023197.0106.021.2023197073337.nc",
        product="VJ103IMG",
        start_utc="2023-07-16T01:06:00Z",
        end_utc="2023-07-16T01:12:00Z",
        data_url="https://example/file.nc",
        catalogue_size_bytes_estimate=1234.0,
    )
    metadata = {
        "GranuleUR": "LAADS:12345",
        "DataGranule": {
            "Identifiers": [{"IdentifierType": "ProducerGranuleId", "Identifier": row.filename}],
            "ArchiveAndDistributionInformation": [{"SizeInBytes": 1234}],
        },
        "CollectionReference": {"ShortName": "VJ103IMG", "Version": "2.1"},
        "TemporalExtent": {
            "RangeDateTime": {"BeginningDateTime": row.start_utc, "EndingDateTime": row.end_utc}
        },
        "RelatedUrls": [{"URL": row.data_url}],
    }
    return row, metadata


def test_laads_internal_ur_uses_producer_identifier_instead():
    row, metadata = metadata_example()
    assert builder.source_metadata(row, metadata) == 1234


@pytest.mark.parametrize("field", ["identity", "size", "version", "url", "time"])
def test_metadata_mismatch_rejected(field):
    row, metadata = metadata_example()
    if field == "identity":
        metadata["DataGranule"]["Identifiers"][0]["Identifier"] = "other.nc"
    elif field == "size":
        metadata["DataGranule"]["ArchiveAndDistributionInformation"][0]["SizeInBytes"] += 2
    elif field == "version":
        metadata["CollectionReference"]["Version"] = "1"
    elif field == "url":
        metadata["RelatedUrls"] = []
    else:
        metadata["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"] = "2024-01-01T00:00Z"
    with pytest.raises(ValueError):
        builder.source_metadata(row, metadata)


@pytest.fixture
def example(monkeypatch, tmp_path):
    monkeypatch.setattr(worker, "ROOT", tmp_path)
    output = tmp_path / "summer/results"
    output.mkdir(parents=True)
    monkeypatch.setattr(worker, "OUTPUT", output)
    monkeypatch.setattr(worker, "compare_pair", lambda pair, output: None)
    pair = {
        "stem": "l2_sample_2023197.0018",
        "sample_id": "SNPP:2023197.0018",
        "sources": [
            {"role": "fire", "filename": "fire.nc", "bytes": 4},
            {"role": "geolocation", "filename": "geo.nc", "bytes": 3},
        ],
    }
    for suffix in worker.SUFFIXES:
        (output / f"{pair['stem']}_{suffix}").write_text(suffix)
    record = {
        "manifest_sha256": "a" * 64,
        "worker_sha256": worker.digest(Path(worker.__file__)),
        "sample_id": pair["sample_id"],
        "outputs": {
            f"{pair['stem']}_{suffix}": worker.digest(output / f"{pair['stem']}_{suffix}")
            for suffix in worker.SUFFIXES
        },
        "metrics": {},
    }
    worker.atomic_json(output / f"{pair['stem']}_checkpoint.json", record)
    return pair, record, tmp_path / "store"


def test_save_and_new_session_restore_without_source_files(example, monkeypatch):
    pair, record, store = example
    saved = worker.save_pair(pair, store, "a" * 64)
    folder = store / ("a" * 64)
    assert (folder / saved["payload_name"]).is_file()
    fresh = worker.ROOT / "fresh"
    monkeypatch.setattr(worker, "OUTPUT", fresh)
    assert worker.restore_store(pair, store, "a" * 64)
    assert worker.checkpoint_read(pair, fresh, "a" * 64) == record


@pytest.mark.parametrize("change", ["payload", "manifest", "worker", "name", "count"])
def test_committed_storage_corruption_cannot_be_reused(example, change):
    pair, _, store = example
    saved = worker.save_pair(pair, store, "a" * 64)
    folder = store / ("a" * 64)
    marker = next(folder.glob("*.commit.json"))
    content = json.loads(marker.read_text())
    if change == "payload":
        (folder / saved["payload_name"]).write_bytes(b"corrupted")
    else:
        field = {
            "manifest": "manifest_sha256",
            "worker": "worker_sha256",
            "name": "payload_name",
            "count": "sample_id",
        }[change]
        content[field] = "different"
        marker.write_text(json.dumps(content))
    with pytest.raises(ValueError):
        worker.restore_store(pair, store, "a" * 64)


def test_orphaned_zip_without_commit_is_not_a_completed_pair(example):
    pair, _, store = example
    worker.save_pair(pair, store, "a" * 64)
    next((store / ("a" * 64)).glob("*.commit.json")).unlink()
    assert worker.restore_store(pair, store, "a" * 64) is False


def test_unexpected_zip_member_is_rejected_before_extraction(example):
    pair, _, _ = example
    payload = worker.ROOT / "bad.zip"
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("../escape.txt", "bad")
    with pytest.raises(ValueError, match="Unexpected"):
        worker.restore_pair(payload, pair, "a" * 64, worker.ROOT / "fresh")
    assert not (worker.ROOT.parent / "escape.txt").exists()


def test_changed_checkpoint_output_stops_reuse(example):
    pair, _, _ = example
    (worker.OUTPUT / f"{pair['stem']}_grid_centers.csv").write_text("changed")
    with pytest.raises(ValueError, match="output changed"):
        worker.checkpoint_read(pair, worker.OUTPUT, "a" * 64)


def test_cleanup_rejects_source_outside_scratch(example):
    pair, _, _ = example
    original = worker.ROOT / "original"
    original.mkdir()
    (original / "fire.nc").write_bytes(b"fire")
    with pytest.raises(ValueError, match="outside summer scratch"):
        worker.cleanup_pair(pair, original)
    assert (original / "fire.nc").read_bytes() == b"fire"


def test_failed_drive_save_keeps_raw_then_restart_saves_without_redownload(example, monkeypatch):
    pair, _, store = example
    manifest = {"pairs": [pair]}
    monkeypatch.setattr(worker, "manifest_read", lambda: (manifest, "a" * 64))
    monkeypatch.setattr(worker, "validate_store_root", lambda path: None)
    raw = worker.ROOT / "summer/raw" / pair["stem"]
    raw.mkdir(parents=True)
    for source in pair["sources"]:
        (raw / source["filename"]).write_bytes(source["role"].encode())
    saved_audit = {
        "sources": {
            s["role"]: {"sha256": worker.digest(raw / s["filename"])} for s in pair["sources"]
        }
    }
    (worker.OUTPUT / f"{pair['stem']}_audit.json").write_text(json.dumps(saved_audit))
    cp = worker.OUTPUT / f"{pair['stem']}_checkpoint.json"
    record = json.loads(cp.read_text())
    record["outputs"][f"{pair['stem']}_audit.json"] = worker.digest(
        worker.OUTPUT / f"{pair['stem']}_audit.json"
    )
    worker.atomic_json(cp, record)
    original_save = worker.save_pair

    def failed_save(*args):
        raise OSError("Drive full")

    monkeypatch.setattr(worker, "save_pair", failed_save)
    with pytest.raises(OSError, match="Drive full"):
        worker.run(store)
    assert (raw / "fire.nc").exists()
    monkeypatch.setattr(worker, "save_pair", original_save)
    monkeypatch.setattr(worker, "download_pair", lambda *args: pytest.fail("Redownload forbidden"))
    worker.run(store)
    assert not (raw / "fire.nc").exists()
    assert worker.restore_store(pair, store, "a" * 64)


def test_wrong_store_path_rejected():
    with pytest.raises(ValueError, match="Mount selected"):
        worker.validate_store_root(Path("unrelated"))


def test_unapproved_day_rejected_before_native_files(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "ROOT", tmp_path)
    directory = tmp_path / "summer"
    directory.mkdir()
    manifest = {"day": "2024-07-16", "option": "B_one_day"}
    (directory / "manifest.json").write_text(json.dumps(copy.deepcopy(manifest)))
    with pytest.raises(ValueError, match="Unapproved scope"):
        worker.manifest_read()
