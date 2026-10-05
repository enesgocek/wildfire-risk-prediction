"""Validate durable publication, readback, interruption handling, and cleanup gating."""

import importlib.util
import json
import shutil
from pathlib import Path

import pytest
from test_cloud_l2_day import day
from test_cloud_l2_day import example as example

SPEC = importlib.util.spec_from_file_location(
    "store_test", Path(__file__).resolve().parents[1] / "scripts/cloud/checkpoint_store.py"
)
store = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(store)


def test_publish_partial_then_full_and_recover_latest_without_overwriting(example):
    manifest, original, _ = example
    folder = day.ROOT / "persistent"
    day.run(original, stop_after=1)
    source = day.ROOT / "l2_day_results.zip"
    first = store.save_snapshot(day, source, folder, manifest, "fixed-manifest")
    first_payload = Path(first["store_payload"])
    first_sha = day.digest(first_payload)
    assert first["completed_pairs"] == 1
    day.run(original)
    full = store.save_snapshot(day, source, folder, manifest, "fixed-manifest")
    again = store.save_snapshot(day, source, folder, manifest, "fixed-manifest")
    assert again == full
    assert day.digest(first_payload) == first_sha
    assert store.latest_snapshot(day, folder, manifest, "fixed-manifest") == Path(
        full["store_payload"]
    )
    recovered = day.ROOT / "recovered"
    day.restore_results(Path(full["store_payload"]), manifest, "fixed-manifest", recovered)
    assert all(day.checkpoint_read(pair, recovered, "fixed-manifest") for pair in manifest["pairs"])
    assert len(list(original.rglob("*.nc"))) == 16


def test_uncommitted_or_partial_files_are_not_recovery_candidates(example):
    manifest, original, _ = example
    day.run(original, stop_after=1)
    folder = day.ROOT / "persistent"
    job = folder / "fixed-manifest"
    job.mkdir(parents=True)
    (job / "unfinished.pending").write_bytes(b"partial")
    shutil.copyfile(day.ROOT / "l2_day_results.zip", job / "orphan.zip")
    assert store.latest_snapshot(day, folder, manifest, "fixed-manifest") is None


@pytest.mark.parametrize("case", ["payload", "manifest", "traversal", "count"])
def test_corrupted_committed_data_stops_recovery(example, case):
    manifest, original, _ = example
    day.run(original, stop_after=1)
    folder = day.ROOT / "persistent"
    saved = store.save_snapshot(
        day, day.ROOT / "l2_day_results.zip", folder, manifest, "fixed-manifest"
    )
    if case == "payload":
        Path(saved["store_payload"]).write_bytes(b"changed")
    else:
        marker = Path(saved["store_commit"])
        record = json.loads(marker.read_text())
        record[
            {
                "manifest": "manifest_sha256",
                "traversal": "payload_name",
                "count": "completed_pairs",
            }[case]
        ] = 8 if case == "count" else "../changed"
        marker.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        store.latest_snapshot(day, folder, manifest, "fixed-manifest")


def test_copy_interruption_keeps_source_and_never_publishes_commit(example, monkeypatch):
    manifest, original, _ = example
    day.run(original, stop_after=1)
    source = day.ROOT / "l2_day_results.zip"
    source_sha = day.digest(source)
    folder = day.ROOT / "persistent"

    def interrupted(reader, writer):
        writer.write(reader.read(10))
        raise OSError("fixture interrupted upload")

    monkeypatch.setattr(store.shutil, "copyfileobj", interrupted)
    with pytest.raises(OSError, match="interrupted"):
        store.save_snapshot(day, source, folder, manifest, "fixed-manifest")
    assert day.digest(source) == source_sha
    assert not list(folder.rglob("*.commit.json"))
    assert store.latest_snapshot(day, folder, manifest, "fixed-manifest") is None


def test_storage_failure_prevents_raw_cleanup_and_preserves_local_checkpoint(example, monkeypatch):
    manifest, original, _ = example
    monkeypatch.setattr(day.importlib.metadata, "version", lambda _: "fixture")

    def download(pair, directory):
        directory.mkdir(parents=True)
        for source in pair["sources"]:
            shutil.copyfile(
                original / pair["local_directory"] / source["filename"],
                directory / source["filename"],
            )
        return sum(s["bytes"] for s in pair["sources"])

    monkeypatch.setattr(day, "download_pair", download)

    def fail(*args):
        raise OSError("fixture quota exceeded")

    monkeypatch.setattr(store, "save_snapshot", fail)
    original_export = store.attach_store(day, day.ROOT / "persistent", manifest, "fixed-manifest")
    try:
        with pytest.raises(OSError, match="quota"):
            day.run()
    finally:
        day.export_results = original_export
    assert len(list((day.ROOT / "day/raw").rglob("*.nc"))) == 2
    assert (day.ROOT / "l2_day_results.zip").exists()
    assert day.checkpoint_read(manifest["pairs"][0], day.ROOT / "day/results", "fixed-manifest")


def test_drive_notebook_uses_existing_results_and_remounts_before_second_readback():
    import ast

    spec = importlib.util.spec_from_file_location(
        "drive_builder_test",
        Path(__file__).resolve().parents[1] / "scripts/cloud/build_l2_drive_bundle.py",
    )
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    codes = [
        "".join(c["source"])
        for c in builder.notebook("0" * 64)["cells"]
        if c["cell_type"] == "code"
    ]
    for code in codes:
        ast.parse(code)
    assert "system_site_packages=False" in codes[0]
    assert "drive.mount" in codes[2]
    assert "flush_and_unmount(timeout_ms=60000)" in codes[3]
    assert "--after-remount" in codes[3]
    assert all("--run-day" not in code and "getpass" not in code for code in codes)


def test_store_scope_rejects_escape_before_creating_directory(example, monkeypatch):
    manifest, original, _ = example
    day.run(original, stop_after=1)
    monkeypatch.setattr(store, "validate_snapshot", lambda *args: 1)
    with pytest.raises(ValueError, match="escapes"):
        store.save_snapshot(
            day, day.ROOT / "l2_day_results.zip", day.ROOT / "persistent", manifest, "../escape"
        )
    assert not (day.ROOT / "escape").exists()
