"""V2 snapshot rejects identity changes and excludes credentials/raw/error text."""

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "v2_snapshot", ROOT / "scripts/cloud/collect_gcp_v2_failure_snapshot.py"
)
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


def state():
    return {
        "status": "failed_checkpoints_retained",
        "failed_month": "2022-09",
        "failed_phase": "pair_publication",
        "error_type": "RuntimeError",
        "queue_manifest_sha256": snapshot.SCOPE,
        "controller_manifest_sha256": snapshot.CONTROLLER,
        "continuation_wrapper_sha256": snapshot.WRAPPER,
        "source_block_registry_sha256": snapshot.REGISTRY,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "continuation_phase": "remaining_months",
        "full_training_complete": False,
        "blocked_pairs": ["SNPP:2023365.0106", "SNPP:2023365.1048"],
        "deferred_days": ["2023-12-31"],
        "deferred_months": ["2023-12"],
        "existing_months": ["2022-10", "2022-11", "2023-07"],
        "days_verified_this_invocation": ["2022-09-01"],
        "pairs_processed_this_invocation": 510,
        "pairs_reused_this_invocation": 15,
        "unknown": "SECRET_STATE",
    }


@pytest.fixture
def home(tmp_path, monkeypatch):
    for package_name, manifest_name, constant in (
        ("wildfire-gcp-production-package", "production_manifest.json", "SCOPE"),
        ("wildfire-gcp-acceleration-package", "acceleration_manifest.json", "CONTROLLER"),
    ):
        package = tmp_path / package_name
        package.mkdir()
        content = b'require(ok, "Pinned public guard")\n'
        (package / "guard.py").write_bytes(content)
        manifest = json.dumps({"files": {"guard.py": snapshot.sha(content)}}).encode()
        (package / manifest_name).write_bytes(manifest)
        monkeypatch.setattr(snapshot, constant, snapshot.sha(manifest))
    wrapper = b'require(ok, "Wrapper guard")\n'
    (tmp_path / "run_gcp_source_aware_continuation_v2.py").write_bytes(wrapper)
    monkeypatch.setattr(snapshot, "WRAPPER", snapshot.sha(wrapper))
    registry = b'{"blocked": "test"}'
    (tmp_path / "source_blocks.json").write_bytes(registry)
    monkeypatch.setattr(snapshot, "REGISTRY", snapshot.sha(registry))
    work = tmp_path / "wildfire-gcp-production-v1"
    meta = work / "months/2022-09/metadata"
    meta.mkdir(parents=True)
    sources = [
        {"role": role, "filename": name, "bytes": 250}
        for role, name in (
            ("fire", "VNP14IMG.A2022252.2230.002.2022253123456.nc"),
            ("geolocation", "VNP03IMG.A2022252.2230.002.2022253123456.nc"),
        )
    ]
    pair = {"sample_id": snapshot.FOCUS, "stem": "l2_sample_2022252.2230", "sources": sources}
    (meta / "month.json").write_text(
        json.dumps({"month": "2022-09", "negative_label_permitted": False, "pairs": [pair]})
    )
    task = meta.parent / "accelerated_run/tasks" / snapshot.sha(snapshot.FOCUS.encode())
    raw = task / "summer/raw" / pair["stem"]
    raw.mkdir(parents=True)
    for source in sources:
        (raw / source["filename"]).write_bytes(b"RAW_MUST_NOT_BE_READ")
    results = task / "summer/results"
    results.mkdir()
    (results / (pair["stem"] + "_audit.json")).write_text("OUTPUT_MUST_NOT_BE_READ")
    (results / (pair["stem"] + "_SECRET_SUFFIX.txt")).write_text("SECRET_RESULT")
    (task / "continuation_failure.json").write_text(
        json.dumps(
            {
                "sample_id": snapshot.FOCUS,
                "child_kind": "pair",
                "error_type": "ValueError",
                "guard": "SECRET_GUARD",
                "safe_error": "SECRET_ERROR",
                "traceback": "SECRET_TRACE",
            }
        )
    )
    diagnostics = work / "diagnostics"
    diagnostics.mkdir()
    (diagnostics / "parent_failure_v2_20261009T231000123456Z.json").write_text(
        json.dumps(
            {
                "protocol": "continuation_parent_failure_v2",
                "error": "GOOGLE_HTTP_503",
                "guard": "Pinned public guard",
                "last_recorded_month": "2022-09",
                "last_recorded_stage": "pair_publication",
                "unknown": "SECRET_PARENT",
            }
        )
    )
    for name in ("progress.json", "acceleration_run_summary.json", "continuation_summary.json"):
        (work / name).write_text(json.dumps(state()))
    (work / "resource_samples.csv").write_text(
        "seconds,disk_free_bytes,mem_available_bytes,process_tree_rss_bytes,private\n"
        "0,9999999999,11111111111,222222,SECRET_CSV\n"
        "8820.1,5555555555,9999999999,999999,SECRET_CSV\n"
    )
    (work / "job.lock").write_text("1")
    private = tmp_path / ".config/wildfire/drive_connection.json"
    private.parent.mkdir(parents=True)
    private.write_text("SECRET_TOKEN")
    return tmp_path


def test_actual_collection_is_read_only_and_drops_unknown_fields(home, monkeypatch):
    original_read = Path.read_bytes
    before = {p: snapshot.sha(original_read(p)) for p in home.rglob("*") if p.is_file()}

    def guarded(path):
        assert "raw" not in path.parts and ".config" not in path.parts
        assert not path.name.endswith("_audit.json")
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    report = snapshot.collect(home)
    assert report["focus_sample"] == snapshot.FOCUS
    assert report["child_failures"][0]["error_type"] == "ValueError"
    assert report["child_failures"][0]["guard"] == "CLASS_ONLY"
    assert report["parent_failures"][0]["error_type"] == "GOOGLE_HTTP_503"
    assert report["resources"]["min_disk_free_bytes"] == 5555555555
    assert report["resources"]["peak_process_tree_rss_bytes"] == 999999
    assert len(report["focus_raw_inventory"]) == 2
    assert report["focus_output_inventory"] == [{"suffix": "audit.json", "bytes": 23}]
    assert report["network_requests"] == report["production_writes"] == 0
    assert report["credentials_read"] is report["raw_files_read"] is False
    assert "SECRET" not in json.dumps(report) and "MUST_NOT" not in json.dumps(report)
    after = {p: snapshot.sha(original_read(p)) for p in home.rglob("*") if p.is_file()}
    assert before == after


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "running"),
        ("failed_month", "2023-12"),
        ("continuation_wrapper_sha256", "V1"),
        ("negative_label_permitted", True),
        ("full_training_complete", True),
        ("deferred_days", []),
        ("days_verified_this_invocation", ["2022-09-31"]),
        ("existing_months", ["2025-01"]),
        ("pairs_processed_this_invocation", -1),
    ],
)
def test_scope_and_bad_calendar_fail_closed(field, value):
    value_state = state()
    value_state[field] = value
    with pytest.raises(ValueError):
        snapshot.progress(json.dumps(value_state).encode())


@pytest.mark.parametrize("fault", ["wrapper", "registry", "package", "snapshot", "task"])
def test_changed_evidence_is_rejected_without_any_output(home, fault):
    work = home / "wildfire-gcp-production-v1"
    if fault == "wrapper":
        (home / "run_gcp_source_aware_continuation_v2.py").write_text("changed")
    elif fault == "registry":
        (home / "source_blocks.json").write_text("changed")
    elif fault == "package":
        (home / "wildfire-gcp-production-package/guard.py").write_text("changed")
    elif fault == "snapshot":
        value = state()
        value["pairs_processed_this_invocation"] += 1
        (work / "continuation_summary.json").write_text(json.dumps(value))
    else:
        (work / "months/2022-09/accelerated_run/tasks/foreign").mkdir()
    with pytest.raises(snapshot.SnapshotCheck):
        snapshot.collect(home)
    assert not list(home.glob("gcp_v2_failure_snapshot_*.json"))


def test_safe_failure_keeps_exit_code_but_never_arbitrary_error_text():
    report = snapshot.failure(
        {
            "error_type": "RuntimeError",
            "exit_code": -9,
            "termination_kind": "nonzero_exit_without_python_diagnostic",
            "guard": ["SECRET"],
            "safe_error": "https://private/token",
        },
        {"CLASS_ONLY"},
    )
    assert report["exit_code"] == -9
    assert report["safe_error"] == "UNCLASSIFIED_ERROR"
    assert report["guard"] == "CLASS_ONLY"
    assert "SECRET" not in json.dumps(report) and "private" not in json.dumps(report)


@pytest.mark.parametrize("value", ["nan", "-1", "SECRET_TOKEN"])
def test_resource_free_form_or_nonfinite_values_rejected(value):
    data = (
        f"seconds,disk_free_bytes,mem_available_bytes,process_tree_rss_bytes\n1,{value},2,3\n"
    ).encode()
    with pytest.raises(ValueError):
        snapshot.telemetry(data)


def test_running_job_lock_prevents_snapshot_before_any_evidence_read(home, monkeypatch):
    def refused(fd, flags):
        assert flags == 5
        raise BlockingIOError("locked")

    monkeypatch.setitem(sys.modules, "fcntl", SimpleNamespace(LOCK_SH=1, LOCK_NB=4, flock=refused))
    with pytest.raises(BlockingIOError):
        with snapshot.stopped_lock(home / "wildfire-gcp-production-v1"):
            raise AssertionError("Live job was entered")
