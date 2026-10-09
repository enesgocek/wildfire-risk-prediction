"""Offline evidence collection against real pinned packages and native products."""

import hashlib
import importlib.util
import json
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "failure_collection", ROOT / "scripts/cloud/collect_gcp_acceleration_failure.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ORIGINAL = ROOT / "outputs/gcp_production/package"
CONTROLLER = ROOT / "outputs/gcp_acceleration/package"


@pytest.fixture
def capture(tmp_path):
    work = tmp_path / "wildfire-gcp-production-v1"
    meta = work / "months/2023-10/metadata"
    meta.mkdir(parents=True)
    (meta.parent / "manifest.zip").write_bytes((CONTROLLER / "month_manifest.zip").read_bytes())
    with zipfile.ZipFile(CONTROLLER / "month_manifest.zip") as archive:
        for name in archive.namelist():
            assert Path(name).name == name
            (meta / name).write_bytes(archive.read(name))
    plan = json.loads((meta / "month.json").read_bytes())
    pair = next(p for p in plan["pairs"] if p["start_utc"].startswith("2023-10-15"))
    task = (
        work
        / "months/2023-10/accelerated_run/tasks"
        / hashlib.sha256(pair["sample_id"].encode()).hexdigest()
    )
    task.mkdir(parents=True)
    fixture = ROOT / "outputs/gcp_production/received/gcp_production_first_session_results.tar.gz"
    with tarfile.open(fixture) as archive, zipfile.ZipFile(task / "pair.zip", "w") as out:
        found = 0
        for member in archive.getmembers():
            name = Path(member.name).name
            if "/inputs/" in member.name and name.startswith(pair["stem"] + "_"):
                out.writestr(name, archive.extractfile(member).read())
                found += 1
        assert found == 10
    raw = task / "summer/raw" / pair["stem"]
    raw.mkdir(parents=True)
    for source in pair["sources"]:
        (raw / source["filename"]).write_bytes(b"RAW_BYTES_MUST_NOT_BE_READ")
    value = {
        "status": "failed_checkpoints_retained",
        "queue_manifest_sha256": module.SCOPE,
        "controller_manifest_sha256": module.CONTROLLER,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "error_type": "ValueError",
        "failed_phase": "pair_publication",
        "failed_month": "2023-10",
        "existing_months": ["2023-07", "2023-08", "2023-09"],
        "days_verified_this_invocation": ["2023-10-01"],
        "pairs_processed_this_invocation": 7,
        "pairs_reused_this_invocation": 10,
        "extra": "SECRET_EXTRA_VALUE",
    }
    for name in ("progress.json", "acceleration_run_summary.json"):
        (work / name).write_text(json.dumps(value))
    (tmp_path / "gcp_acceleration_launcher.log").write_text(
        "SECRET_LOG_VALUE\nDAY COMMITTED 2023-10-01\nGuest poweroff requested: True\n"
    )
    private = tmp_path / ".config/wildfire/drive_connection.json"
    private.parent.mkdir(parents=True)
    private.write_text("SECRET_CONNECTION_VALUE")
    (work / "job.lock").write_text("1")
    return work, task, pair, tmp_path / "evidence.zip"


def test_real_native_capture_preserves_hashes_and_never_reads_raw_or_credentials(
    capture, monkeypatch
):
    work, task, _, target = capture
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in work.rglob("*") if p.is_file()}
    read_bytes = Path.read_bytes

    def guarded(path):
        assert "raw" not in path.parts and ".config" not in path.parts
        return read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    report = module.collect(work, ORIGINAL, CONTROLLER, target)
    assert len(report["task_inventory"]) == 1
    assert report["network_requests"] == report["production_writes"] == 0
    assert report["credentials_read"] is report["source_raw_files_included"] is False
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert archive.read("manifest.zip") == read_bytes(CONTROLLER / "month_manifest.zip")
        assert archive.read("tasks/" + task.name + "/pair.zip") == read_bytes(task / "pair.zip")
        for name, checksum in report["files"].items():
            data = archive.read(name)
            assert hashlib.sha256(data).hexdigest() == checksum
            assert b"SECRET_" not in data and b"RAW_BYTES_MUST_NOT_BE_READ" not in data
        assert archive.read("launcher_filtered.log") == (
            b"DAY COMMITTED 2023-10-01\nGuest poweroff requested: True\n"
        )
    after = {p: hashlib.sha256(read_bytes(p)).hexdigest() for p in work.rglob("*") if p.is_file()}
    assert before == after


def test_partial_native_output_is_collected_without_pair_zip(capture):
    work, task, pair, target = capture
    native = task / "summer/results"
    native.mkdir(parents=True)
    with zipfile.ZipFile(task / "pair.zip") as archive:
        name = pair["stem"] + "_audit.json"
        data = archive.read(name)
    (task / "pair.zip").unlink()  # Fixture setup only; collector never removes production files.
    (native / name).write_bytes(data)
    report = module.collect(work, ORIGINAL, CONTROLLER, target)
    assert report["task_inventory"][0]["native_outputs"] == ["audit.json"]
    with zipfile.ZipFile(target) as archive:
        assert archive.read("tasks/" + task.name + "/native/" + name) == data


@pytest.mark.parametrize("fault", ["foreign_task", "different_snapshot", "overwrite", "byte_bound"])
def test_fail_closed_before_export(capture, monkeypatch, fault):
    work, task, _, target = capture
    if fault == "foreign_task":
        (task.parent / "foreign").mkdir()
    elif fault == "different_snapshot":
        path = work / "progress.json"
        value = json.loads(path.read_bytes())
        value["pairs_processed_this_invocation"] += 1
        path.write_text(json.dumps(value))
    elif fault == "overwrite":
        target.write_bytes(b"KEEP")
    else:
        monkeypatch.setattr(module, "MAX_TOTAL", 1)
    expected = {
        "foreign_task": "Retained task boundary",
        "different_snapshot": "Failure snapshots differ",
        "overwrite": "Export already exists",
        "byte_bound": "Diagnostic total byte bound",
    }[fault]
    with pytest.raises(module.CollectionCheck, match=expected):
        module.collect(work, ORIGINAL, CONTROLLER, target)
    assert not target.exists() or target.read_bytes() == b"KEEP"
    assert not target.with_suffix(".pending").exists()


def test_changed_pinned_controller_is_rejected(capture, tmp_path):
    work, _, _, target = capture
    changed = tmp_path / "changed"
    changed.mkdir()
    (changed / "acceleration_manifest.json").write_bytes(b"{}")
    with pytest.raises(module.CollectionCheck, match="Pinned manifest SHA"):
        module.collect(work, ORIGINAL, changed, target)
    assert not target.exists()


def test_source_symlink_rejected_without_reading_destination(capture, tmp_path):
    work, task, _, target = capture
    saved = tmp_path / "outside.zip"
    saved.write_bytes((task / "pair.zip").read_bytes())
    (task / "pair.zip").unlink()
    try:
        (task / "pair.zip").symlink_to(saved)
    except OSError:
        pytest.skip("Windows session does not permit symlink creation")
    with pytest.raises(module.CollectionCheck):
        module.collect(work, ORIGINAL, CONTROLLER, target)
    assert not target.exists()
