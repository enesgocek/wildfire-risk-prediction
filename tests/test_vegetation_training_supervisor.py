"""Automatic bounded continuation, cumulative acceptance and stop conditions."""

import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/landcover/run_vegetation_training.py"
SPEC = importlib.util.spec_from_file_location("training_supervisor_test", PATH)
supervisor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(supervisor)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(supervisor, "ROOT", tmp_path)
    monkeypatch.setattr(supervisor.queue, "ROOT", tmp_path)
    monkeypatch.setattr(supervisor, "runtime", lambda: {"sources": "fixed"})
    return tmp_path


def batch_factory(statuses, calls):
    def batch(start, end, **kwargs):
        index = len(calls)
        calls.append(kwargs)
        status, months = statuses[min(index, len(statuses) - 1)]
        directory = supervisor.ROOT / "outputs/reports/landscape/period_v1" / f"batch_{index}"
        report = {
            "status": status,
            "current_month": months[-1] if months else start,
            "verified_months": [
                {"month": month, "manifest_sha256": month + "_unchanged"} for month in months
            ],
        }
        supervisor.queue.save(directory / "progress.json", report)
        kwargs["on_progress"](directory, report)
        return report, directory

    return batch


def test_time_pause_resumes_automatically_and_counts_months_once(workspace, monkeypatch):
    calls = []
    monkeypatch.setattr(
        supervisor.queue,
        "run",
        batch_factory(
            [
                ("paused_time_budget_checkpoints_retained", ["2018-01"]),
                ("selected_training_range_verified", ["2018-01", "2018-02"]),
            ],
            calls,
        ),
    )
    report, _ = supervisor.run("2018-01", "2018-02", job_id="test_auto")
    assert len(calls) == 2
    assert report["status"] == "selected_training_range_verified"
    assert [r["month"] for r in report["verified_months"]] == ["2018-01", "2018-02"]
    assert all(r["max_run_minutes"] <= 240 and r["max_new_months"] == 72 for r in calls)


@pytest.mark.parametrize(
    "status",
    ["failed_checkpoints_retained", "paused_disk_reserve", "interrupted_checkpoints_retained"],
)
def test_error_disk_or_interrupt_is_not_automatically_retried(workspace, monkeypatch, status):
    calls = []
    monkeypatch.setattr(supervisor.queue, "run", batch_factory([(status, [])], calls))
    report, _ = supervisor.run("2018-01", "2018-02", job_id="test_stop")
    assert len(calls) == 1 and report["status"] == status
    assert not (workspace / "outputs/cache/vegetation_training_supervisor.lock").exists()


def test_complete_status_without_all_months_is_rejected(workspace, monkeypatch):
    calls = []
    monkeypatch.setattr(
        supervisor.queue,
        "run",
        batch_factory([("selected_training_range_verified", ["2018-01"])], calls),
    )
    report, _ = supervisor.run("2018-01", "2018-02", job_id="test_incomplete")
    assert report["status"] == "failed_checkpoints_retained"


def test_month_outside_selected_range_is_never_accepted(workspace, monkeypatch):
    calls = []
    monkeypatch.setattr(
        supervisor.queue,
        "run",
        batch_factory([("selected_training_range_verified", ["2025-01"])], calls),
    )
    report, _ = supervisor.run("2018-01", "2018-02", job_id="test_scope")
    assert report["status"] == "failed_checkpoints_retained"
    assert not report["verified_months"]


def test_repeated_pauses_have_finite_batch_budget(workspace, monkeypatch):
    calls = []
    monkeypatch.setattr(supervisor.queue, "run", batch_factory([("paused_time_budget", [])], calls))
    report, _ = supervisor.run("2018-01", "2018-02", max_batches=2, job_id="test_finite")
    assert len(calls) == 2 and report["status"] == "paused_batch_count_budget"


def test_changed_environment_stops_before_next_batch(workspace, monkeypatch):
    calls, state = [], {"sources": "fixed"}
    monkeypatch.setattr(supervisor, "runtime", lambda: state.copy())
    original = batch_factory([("paused_time_budget", ["2018-01"])], calls)

    def batch(*args, **kwargs):
        result = original(*args, **kwargs)
        state["sources"] = "changed"
        return result

    monkeypatch.setattr(supervisor.queue, "run", batch)
    report, _ = supervisor.run("2018-01", "2018-02", job_id="test_drift")
    assert report["status"] == "failed_checkpoints_retained" and len(calls) == 1
    assert len(report["verified_months"]) == 1


def test_changed_accepted_manifest_is_rejected(workspace, monkeypatch):
    calls = []
    original = batch_factory(
        [
            ("paused_time_budget", ["2018-01"]),
            ("selected_training_range_verified", ["2018-01", "2018-02"]),
        ],
        calls,
    )

    def batch(start, end, **kwargs):
        callback = kwargs["on_progress"]

        def changed(directory, report):
            if calls:
                # The first fake batch has now appended its call; alter only the second one.
                if len(calls) == 2:
                    report["verified_months"][0]["manifest_sha256"] = "changed"
            callback(directory, report)

        kwargs["on_progress"] = changed
        return original(start, end, **kwargs)

    monkeypatch.setattr(supervisor.queue, "run", batch)
    report, _ = supervisor.run("2018-01", "2018-02", job_id="test_manifest_drift")
    assert report["status"] == "failed_checkpoints_retained"
    assert report["verified_months"][0]["manifest_sha256"] == "2018-01_unchanged"


def test_overall_deadline_starts_no_more_work(workspace, monkeypatch):
    calls = []
    clock = {"now": 0}
    original = batch_factory([("paused_time_budget", [])], calls)

    def batch(*args, **kwargs):
        result = original(*args, **kwargs)
        clock["now"] = 3600
        return result

    monkeypatch.setattr(supervisor.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(supervisor.queue, "run", batch)
    report, _ = supervisor.run("2018-01", "2018-02", hours=1, job_id="test_deadline")
    assert len(calls) == 1 and report["status"] == "paused_overall_time_budget"


def test_existing_supervisor_record_is_immutable(workspace):
    path = workspace / "outputs/reports/landscape/training_supervisor_v1/test_prior/progress.json"
    path.parent.mkdir(parents=True)
    path.write_text("accepted old record")
    with pytest.raises(ValueError, match="record retained"):
        supervisor.run("2018-01", "2018-02", job_id="test_prior")
    assert path.read_text() == "accepted old record"


def test_existing_supervisor_lock_is_not_removed(workspace):
    path = workspace / "outputs/cache/vegetation_training_supervisor.lock"
    path.parent.mkdir(parents=True)
    path.write_text("another job")
    with pytest.raises(FileExistsError):
        supervisor.run("2018-01", "2018-02", job_id="test_lock")
    assert path.read_text() == "another job"


@pytest.mark.parametrize("end", ["2024-01", "2025-01", "../../.env"])
def test_nontraining_range_rejected_before_manifest_reads(workspace, monkeypatch, end):
    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid scope must not inspect manifests")

    monkeypatch.setattr(Path, "is_file", forbidden)
    with pytest.raises(ValueError):
        supervisor.run("2018-01", end)


@pytest.mark.parametrize(
    "options", [{"hours": float("nan")}, {"batch_minutes": 241}, {"min_free_gib": 0}]
)
def test_invalid_options_start_no_work(workspace, options):
    with pytest.raises(ValueError):
        supervisor.run("2018-01", "2018-02", **options)
    assert not (workspace / "outputs").exists()
