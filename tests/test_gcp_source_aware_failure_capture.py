"""Read-only continuation capture, pinned identity and credential exclusion checks."""

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


capture = load("continuation_capture", ROOT / "scripts/cloud/collect_gcp_source_aware_failure.py")
previous = load("original_capture_test", ROOT / "tests/test_gcp_failure_collection.py")
NEEDS_NATIVE = pytest.mark.skipif(
    not (
        ROOT / "outputs/gcp_production/received/gcp_production_first_session_results.tar.gz"
    ).is_file()
    or not (previous.CONTROLLER / "acceleration_manifest.json").is_file(),
    reason="Ignored pinned/native fixtures are unavailable",
)


def fields():
    return {
        "continuation_phase": "remaining_months",
        "continuation_wrapper_sha256": capture.WRAPPER,
        "source_block_registry_sha256": capture.REGISTRY,
        "blocked_pairs": capture.BLOCKED,
        "deferred_days": ["2023-12-31"],
        "deferred_months": ["2023-12"],
        "full_training_complete": False,
        "actual_vm_termination_timestamp": "2026-10-09T18:39:24.369866Z",
    }


@pytest.fixture
def evidence(tmp_path):
    work, task, pair, target = previous.capture.__wrapped__(tmp_path)
    state = json.loads((work / "progress.json").read_text()) | fields()
    for name in ("progress.json", "acceleration_run_summary.json", "continuation_summary.json"):
        (work / name).write_text(json.dumps(state))
    (tmp_path / "run_gcp_source_aware_continuation.py").write_bytes(
        (ROOT / "scripts/cloud/run_gcp_source_aware_continuation.py").read_bytes()
    )
    (tmp_path / "source_blocks.json").write_bytes(
        (ROOT / "configs/gcp_source_blocks_2026-10-09.json").read_bytes()
    )
    (tmp_path / "gcp_source_aware_launcher.log").write_text(
        "SECRET_NEW_LOG\nDAY COMMITTED 2023-10-01\n"
        "Continuation stopped: RuntimeError ; safe child diagnostics retained\n"
    )
    return work, task, pair, target


@NEEDS_NATIVE
def test_capture_preserves_tasks_uses_correct_log_and_excludes_secrets(evidence, monkeypatch):
    work, task, pair, target = evidence
    failure = task / "continuation_failure.json"
    failure.write_text(
        json.dumps(
            {
                "sample_id": pair["sample_id"],
                "child_kind": "pair",
                "error_type": "ValueError",
                "guard": "SECRET_ERROR",
                "unknown": "SECRET_EXTRA",
            }
        )
    )
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in work.rglob("*") if p.is_file()}
    read = Path.read_bytes

    def guarded(path):
        assert "raw" not in path.parts and ".config" not in path.parts
        return read(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    report = capture.collect(work, previous.ORIGINAL, previous.CONTROLLER, target)
    assert report["protocol"] == "gcp_source_aware_failure_evidence_v1"
    assert report["network_requests"] == report["production_writes"] == 0
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        for name, digest in report["files"].items():
            data = archive.read(name)
            assert hashlib.sha256(data).hexdigest() == digest
            assert b"SECRET_" not in data and b"RAW_BYTES_MUST_NOT_BE_READ" not in data
        diag = json.loads(archive.read(f"tasks/{task.name}/continuation_failure.json"))
        assert diag["guard"] == "CLASS_ONLY"
        progress = json.loads(archive.read("progress.json"))
        assert progress["deferred_days"] == ["2023-12-31"]
        assert b"Continuation stopped:" in archive.read("launcher_filtered.log")
    after = {p: hashlib.sha256(read(p)).hexdigest() for p in work.rglob("*") if p.is_file()}
    assert before == after


@NEEDS_NATIVE
@pytest.mark.parametrize(
    "fault,label",
    [
        ("wrapper", "Pinned continuation wrapper"),
        ("registry", "Pinned source registry"),
        ("snapshot", "Continuation snapshot differs"),
        ("overwrite", "Export already exists"),
        ("byte_bound", "Diagnostic total byte bound"),
    ],
)
def test_refuses_changed_identity_overwrite_or_snapshot(evidence, monkeypatch, fault, label):
    work, _, _, target = evidence
    if fault == "wrapper":
        (work.parent / "run_gcp_source_aware_continuation.py").write_text("changed")
    elif fault == "registry":
        (work.parent / "source_blocks.json").write_text("changed")
    elif fault == "snapshot":
        path = work / "continuation_summary.json"
        state = json.loads(path.read_text())
        state["pairs_processed_this_invocation"] += 1
        path.write_text(json.dumps(state))
    elif fault == "overwrite":
        target.write_bytes(b"KEEP")
    else:
        monkeypatch.setattr(capture, "MAX_TOTAL", 1)
    with pytest.raises(capture.CollectionCheck, match=label):
        capture.collect(work, previous.ORIGINAL, previous.CONTROLLER, target)
    assert not target.exists() or target.read_bytes() == b"KEEP"
    assert not target.with_suffix(".pending").exists()


def valid_state():
    return {
        "status": "failed_checkpoints_retained",
        "queue_manifest_sha256": capture.SCOPE,
        "controller_manifest_sha256": capture.CONTROLLER,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "error_type": "RuntimeError",
        "failed_phase": "pair_publication",
        "failed_month": "2022-11",
        "existing_months": ["2022-12"],
        "days_verified_this_invocation": ["2022-11-01"],
        "pairs_processed_this_invocation": 1989,
        "pairs_reused_this_invocation": 10,
    } | fields()


@pytest.mark.parametrize(
    "field,value",
    [
        ("days_verified_this_invocation", ["2022-11-31"]),
        ("days_verified_this_invocation", ["2025-01-01"]),
        ("full_training_complete", True),
        ("blocked_pairs", ["N20:2022310.2330"]),
        ("negative_label_permitted", True),
    ],
)
def test_production_scope_and_deferred_state_are_not_relaxed(field, value):
    state = valid_state()
    state[field] = value
    with pytest.raises(ValueError):
        capture.state(json.dumps(state).encode())


def test_guard_filter_ignores_free_form_strings():
    labels = capture.literal_guards(b'require(ok, "Pinned guard")\nprint("SECRET")')
    assert labels == {"Pinned guard"}
