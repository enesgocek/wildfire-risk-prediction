"""Candidate execution resumes without redownloading; failure retains completed references."""

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from wildfire_risk_prediction import dataset_batch as batch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/quality/prepare_dataset.py"
spec = importlib.util.spec_from_file_location("dataset_preparation_cli_test", SCRIPT)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)
METHODS = {"src/method.py": "d" * 64}


def reference(month="2018-01"):
    from wildfire_risk_prediction.feature_month import calendar_days

    return {
        "month": month,
        "path": f"outputs/reports/dataset/feature_month_v1/job_{month}/readback.json",
        "sha256": "a" * 64,
        "manifest_sha256": "b" * 64,
        "rows": len(calendar_days(month)) * batch.GRID_COUNT,
    }


def source():
    return {
        "month": "2018-02",
        "readback": "outputs/reports/landscape/month_v1/2018-02/accepted.json",
        "readback_sha256": "a" * 64,
        "manifest_sha256": "b" * 64,
        "daily_table_sha256": "c" * 64,
        "daily_rows": 162344,
    }


@pytest.fixture
def execution(tmp_path, monkeypatch):
    value = batch.build_plan([source()], [reference()], METHODS)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "fingerprints", lambda: METHODS)
    monkeypatch.setattr(cli, "read_record", lambda *args: (value, "e" * 64))
    monkeypatch.setattr(cli.shutil, "disk_usage", lambda _: SimpleNamespace(free=100 * 2**30))
    monkeypatch.setattr(cli, "audit_candidate", lambda ref, *args: ref)
    return value, tmp_path


def result(folder):
    return json.loads((folder / "progress.json").read_text(encoding="utf-8"))


def test_reuse_only_never_calls_builder_or_discards_ready_report(execution, monkeypatch):
    monkeypatch.setattr(cli.subprocess, "run", lambda *a, **k: pytest.fail("Builder forbidden"))
    folder = cli.execute("plan.json", "e" * 64, ["2018-01"], 1)
    value = result(folder)
    assert value["status"] == "completed_selected_candidate_months"
    assert value["reports"] == [reference()]
    assert value["actions"] == [{"month": "2018-01", "action": "verified_reused"}]
    assert value["candidate_calendar_complete"] is False and value["model_ready"] is False
    assert not (execution[1] / "outputs/cache/dataset_candidate_batch.lock").exists()


def test_missing_build_request_retains_previous_complete_result(execution):
    folder = cli.execute("plan.json", "e" * 64, ["2018-01", "2018-02"], 1)
    value = result(folder)
    assert value["status"] == "stopped_awaiting_source_or_build_request"
    assert value["blocked_month"] == "2018-02" and value["reports"] == [reference()]


def test_builder_error_retains_prior_results_and_does_not_write_external_error_text(
    execution,
    monkeypatch,
):
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=1, stderr="untrusted private server text", stdout=""
        ),
    )
    folder = cli.execute("plan.json", "e" * 64, ["2018-01", "2018-02"], 1, True)
    value = result(folder)
    assert value["status"] == "failed_results_retained" and value["reports"] == [reference()]
    assert value["error_type"] == "ValueError"
    assert "private server text" not in (folder / "progress.json").read_text()


def test_child_timeout_retains_previous_month_and_never_admits_partial_output(
    execution, monkeypatch
):
    def expired(*args, **kwargs):
        assert kwargs["timeout"] > 0
        raise subprocess.TimeoutExpired("bounded-month-child", kwargs["timeout"])

    monkeypatch.setattr(cli.subprocess, "run", expired)
    folder = cli.execute("plan.json", "e" * 64, ["2018-01", "2018-02"], 1, True)
    value = result(folder)
    assert value["status"] == "stopped_time_budget_results_retained"
    assert value["error_type"] == "TimeoutExpired" and value["reports"] == [reference()]


@pytest.mark.parametrize("months", [["2024-01"], ["2025-01"], ["2018-01", "2018-01"]])
def test_invalid_scope_or_duplicate_selection_before_plan_read(monkeypatch, months):
    monkeypatch.setattr(cli, "read_record", lambda *a: pytest.fail("Plan must not be read"))
    with pytest.raises(ValueError):
        cli.execute("plan.json", "e" * 64, months, 1)


def test_changed_method_identity_prevents_all_csv_and_output_work(execution, monkeypatch):
    monkeypatch.setattr(cli, "fingerprints", lambda: {"src/method.py": "f" * 64})
    monkeypatch.setattr(cli, "new_directory", lambda *a: pytest.fail("Output must not be opened"))
    with pytest.raises(ValueError, match="methods changed"):
        cli.execute("plan.json", "e" * 64, ["2018-01"], 1)


def test_resume_index_keeps_registered_months_outside_latest_selected_batch(monkeypatch):
    plan = batch.build_plan([], [reference("2018-01"), reference("2018-08")], METHODS)
    index = {
        "version": batch.INDEX_VERSION,
        "plan": "plan.json",
        "plan_sha256": "e" * 64,
        "reports": [reference("2018-02")],
        "labels_created": False,
        "model_ready": False,
        "final_test_accessed": False,
    }
    monkeypatch.setattr(
        cli, "read_record", lambda name, *a: (index if name == "index.json" else plan, "e" * 64)
    )
    refs, _ = cli.index_references("index.json", "e" * 64)
    assert [r["month"] for r in refs] == ["2018-01", "2018-02", "2018-08"]


def test_existing_writer_lock_prevents_parallel_candidate_writer(execution, monkeypatch):
    root = execution[1]
    path = root / "outputs/cache/dataset_candidate_batch.lock"
    path.parent.mkdir(parents=True)
    path.write_text("retained-lock")
    monkeypatch.setattr(cli, "audit_candidate", lambda *a: pytest.fail("Second writer forbidden"))
    with pytest.raises(FileExistsError):
        cli.execute("plan.json", "e" * 64, ["2018-01"], 1)
    assert path.read_text() == "retained-lock"


def test_final_test_reference_rejected_before_any_candidate_csv(monkeypatch):
    held_out = dict(reference(), month="2025-01")
    monkeypatch.setattr(cli, "index_references", lambda *a: ([reference(), held_out], "e" * 64))
    monkeypatch.setattr(cli, "audit_candidate", lambda *a: pytest.fail("CSV must not be read"))
    with pytest.raises(ValueError):
        cli.audit("index.json", "e" * 64)


def test_all_ready_selects_references_only_and_stops_before_implicit_build(execution):
    folder = cli.execute("plan.json", "e" * 64, None, 1)
    value = result(folder)
    assert value["selected_months"] == ["2018-01", "2018-02"]
    assert value["reports"] == [reference()] and value["blocked_month"] == "2018-02"


def test_complete_calendar_requirement_rejects_sparse_index_before_csv(monkeypatch):
    monkeypatch.setattr(cli, "index_references", lambda *a: ([reference()], "e" * 64))
    monkeypatch.setattr(cli, "audit_candidate", lambda *a: pytest.fail("Sparse final inventory"))
    with pytest.raises(ValueError, match="Complete training calendar"):
        cli.audit("index.json", "e" * 64, require_complete=True)


def test_disk_reserve_stop_precedes_any_candidate_read(execution, monkeypatch):
    monkeypatch.setattr(cli.shutil, "disk_usage", lambda _: SimpleNamespace(free=9 * 2**30))
    monkeypatch.setattr(
        cli, "audit_candidate", lambda *a: pytest.fail("Reserve failed before reads")
    )
    folder = cli.execute("plan.json", "e" * 64, ["2018-01"], 1)
    assert result(folder)["status"] == "stopped_disk_reserve_results_retained"
    assert result(folder)["reports"] == []


def test_insufficient_child_time_is_a_controlled_pause_without_builder(execution, monkeypatch):
    monkeypatch.setattr(cli.subprocess, "run", lambda *a, **k: pytest.fail("Child not admitted"))
    folder = cli.execute("plan.json", "e" * 64, ["2018-02"], 1 / 60, True)
    assert result(folder)["status"] == "stopped_time_budget_results_retained"


@pytest.mark.parametrize("post_audit_timeout", [False, True])
def test_completed_child_receipt_survives_parent_pause_for_next_resume(
    execution,
    monkeypatch,
    post_audit_timeout,
):
    plan = execution[0]
    ref = reference("2018-02")
    report = {"rows": ref["rows"], "manifest_sha256": ref["manifest_sha256"]}
    monkeypatch.setattr(
        cli,
        "read_record",
        lambda path, *a: (plan if path == "plan.json" else report, ref["sha256"]),
    )
    monkeypatch.setattr(cli, "candidate_report", lambda *a: report)
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="Report: " + ref["path"] + "\n"),
    )

    def audit(ref, *args):
        if post_audit_timeout and ref["month"] == "2018-02":
            raise TimeoutError("bounded audit")
        return ref

    monkeypatch.setattr(cli, "audit_candidate", audit)
    folder = cli.execute("plan.json", "e" * 64, ["2018-01", "2018-02"], 1, True)
    value = result(folder)
    assert value["completed_builder_reports"] == [ref]
    if post_audit_timeout:
        assert value["status"] == "stopped_time_budget_results_retained"
        assert value["reports"] == [reference()]
    else:
        assert value["status"] == "completed_selected_candidate_months"
        assert value["reports"] == [reference(), ref]
    monkeypatch.setattr(
        cli, "read_record", lambda path, *a: (value if path == "index.json" else plan, "e" * 64)
    )
    refs, _ = cli.index_references("index.json", "e" * 64)
    assert [r["month"] for r in refs] == ["2018-01", "2018-02"]
