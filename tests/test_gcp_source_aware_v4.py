"""Thirteen-hour continuation rejects unsafe deadlines and unreviewed migration."""

import ast
import hashlib
import importlib.util
import json
import tarfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v4.py"
spec = importlib.util.spec_from_file_location("continuation_v4_tests", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
NOW = datetime(2026, 10, 10, 20, tzinfo=UTC)
ARCHIVE = ROOT / (
    "outputs/gcp_acceleration/source_aware_v3_2026-10-10/received/"
    "gcp_v3_session_20261010T194058Z_logs.tar.gz"
)


@pytest.mark.parametrize("seconds", [4200, 28800, 46800, 46860])
def test_real_deadline_retains_five_minute_stop_reserve(seconds):
    finish = NOW + timedelta(seconds=seconds)
    assert module.runtime_seconds(finish.isoformat(), NOW) == seconds - 300


@pytest.mark.parametrize("seconds", [-1, 0, 4199, 46861, 86400])
def test_past_short_and_overlong_deadlines_are_refused(seconds):
    with pytest.raises(ValueError, match="thirteen hours"):
        module.runtime_seconds((NOW + timedelta(seconds=seconds)).isoformat(), NOW)


def test_timezone_and_trial_cutoff_remain_mandatory():
    with pytest.raises(ValueError, match="timezone"):
        module.runtime_seconds("2026-10-11T09:00:00", NOW)
    with pytest.raises(ValueError, match="Trial cutoff"):
        module.runtime_seconds("2026-10-24T00:00:00Z", datetime(2026, 10, 23, 12, tzinfo=UTC))
    assert module.runtime_seconds("2026-10-11T12:00:00+03:00", NOW) == 46500


def test_science_children_shutdown_and_checkpoint_logic_match_frozen_v3():
    def functions(path):
        return {
            node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(path.read_text(encoding="utf-8")).body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        }

    old = functions(ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v3.py")
    new = functions(SOURCE)
    assert set(new) == set(old) | {"runtime_seconds", "reviewed_resume"}
    for name in set(old) - {"prepare_reviewed_failures", "main"}:
        assert old[name] == new[name], name


@pytest.mark.skipif(not ARCHIVE.is_file(), reason="Ignored accepted V3 fixture unavailable")
def test_exact_accepted_v3_final_migrates_and_changed_bytes_fail(tmp_path):
    with tarfile.open(ARCHIVE) as archive:
        raw = archive.extractfile("progress.json").read()
        for name in ("acceleration_run_summary.json", "continuation_summary.json"):
            (tmp_path / name).write_bytes(archive.extractfile(name).read())
    state = json.loads(raw)
    helper = SimpleNamespace(
        sha=lambda value: hashlib.sha256(value).hexdigest(),
        read=lambda path, root, limit: path.read_bytes(),
    )
    assert module.reviewed_resume(raw, state, tmp_path, helper)
    assert not module.reviewed_resume(raw + b" ", state, tmp_path, helper)
    assert not module.reviewed_resume(
        raw, {**state, "status": "failed_checkpoints_retained"}, tmp_path, helper
    )
    (tmp_path / "continuation_summary.json").write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="Accepted V3 final"):
        module.reviewed_resume(raw, state, tmp_path, helper)


def test_unknown_wrapper_cannot_bypass_migration_review(tmp_path):
    state = {"continuation_wrapper_sha256": "unreviewed", "status": "paused_at_runtime_reserve"}
    assert not module.reviewed_resume(b"{}", state, tmp_path, SimpleNamespace())


@pytest.mark.parametrize(
    "name",
    [
        "test_registry_cannot_defer_an_arbitrary_day_or_pair",
        "test_unaffected_pipeline_and_runtime_reserve_result_remain_unchanged",
        "test_two_phase_live_and_final_counts_do_not_double_count",
        "test_failure_restores_wrappers_and_keeps_registry_and_last_valid_progress",
        "test_reserve_before_december_completion_does_not_start_remaining_months",
        "test_safe_child_error_never_logs_external_text",
        "test_all_processable_months_are_not_all_training_months",
    ],
)
def test_v4_preserves_scientific_scheduling_and_error_behaviour(name, tmp_path, monkeypatch):
    helper_spec = importlib.util.spec_from_file_location(
        "v4_scheduling_helpers", ROOT / "tests/test_gcp_source_aware_continuation.py"
    )
    helper = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helper)
    monkeypatch.setattr(helper, "module", module)
    method = getattr(helper, name)
    if name == "test_all_processable_months_are_not_all_training_months":
        method()
    else:
        method(tmp_path)
