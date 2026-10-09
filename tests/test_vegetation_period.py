"""Training isolation, verified reuse, source drift, budgets and exclusive queue execution."""

import importlib.util
import shutil
import subprocess
import time
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/landcover/prepare_vegetation_period.py"
SPEC = importlib.util.spec_from_file_location("vegetation_period", PATH)
queue = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(queue)


@pytest.mark.parametrize(
    "start,end",
    [
        ("2018-01", "2024-01"),
        ("2025-01", "2025-12"),
        ("2017-12", "2018-01"),
        ("2018-02", "2018-01"),
        ("2018-8", "2018-09"),
        ("2018-01", "../../.env"),
    ],
)
def test_invalid_scope_rejected_before_file_access(start, end, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid range must not inspect any files")

    monkeypatch.setattr(Path, "is_file", forbidden)
    with pytest.raises(ValueError):
        queue.plan(start, end)


def test_full_training_calendar_includes_leap_day():
    months = queue.months_between("2018-01", "2023-12")
    assert len(months) == 72
    assert sum(len(queue.month_schedule(m)[0]) for m in months) == 2191


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    for name in queue.DEPENDENCIES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("pinned source", encoding="utf-8")
    monkeypatch.setattr(
        queue.shutil, "disk_usage", lambda path: shutil._ntuple_diskusage(100, 10, 20 * queue.GIB)
    )
    return tmp_path


def month_manifest(month):
    path = queue.manifest_path(month)
    queue.save(
        path,
        {
            "month": month,
            "rows": len(queue.month_schedule(month)[0]) * 2899 * 2,
            "table_sha256": "a" * 64,
        },
    )


def fake_children(calls, *, corrupt=False, drift=False):
    def child(arguments, log_path, deadline):
        assert deadline > time.monotonic()
        calls.append(arguments)
        month = arguments[arguments.index("--month") + 1]
        if "download" in arguments:
            month_manifest(month)
            if drift:
                (queue.ROOT / queue.DEPENDENCIES[0]).write_text("changed")
            return
        name = arguments[arguments.index("--report-name") + 1]
        queue.save(
            queue.ROOT / "outputs/reports/landscape/month_v1" / month / name,
            {
                "status": "monthly_daily_readback_passed",
                "month": month,
                "manifest_sha256": "bad" if corrupt else queue.sha(queue.manifest_path(month)),
                "verified_daily_rows": len(queue.month_schedule(month)[0]) * 2899 * 2,
                "final_test_accessed": False,
                "historical_availability_verified": False,
            },
        )

    return child


def test_existing_month_is_verified_not_rebuilt_or_charged_to_new_budget(workspace, monkeypatch):
    month_manifest("2018-08")
    original = queue.manifest_path("2018-08").read_bytes()
    calls = []
    monkeypatch.setattr(queue, "run_child", fake_children(calls))
    report, _ = queue.run("2018-08", "2018-10", max_new_months=1)
    assert report["status"] == "paused_new_month_budget"
    assert report["new_months"] == 1
    assert [r["month"] for r in report["verified_months"]] == ["2018-08", "2018-09"]
    assert queue.manifest_path("2018-08").read_bytes() == original
    assert len(calls) == 3
    assert "download" not in calls[0]
    assert not queue.manifest_path("2018-10").exists()


def test_disk_guard_starts_no_child_and_does_not_delete_existing_data(workspace, monkeypatch):
    month_manifest("2018-08")
    before = queue.manifest_path("2018-08").read_bytes()
    calls = []
    monkeypatch.setattr(queue, "run_child", fake_children(calls))
    monkeypatch.setattr(
        queue.shutil, "disk_usage", lambda path: shutil._ntuple_diskusage(100, 99, 100)
    )
    report, _ = queue.run("2018-08", "2018-09")
    assert report["status"] == "paused_disk_reserve"
    assert not calls and not report["verified_months"]
    assert queue.manifest_path("2018-08").read_bytes() == before


def test_source_drift_stops_before_acceptance(workspace, monkeypatch):
    calls = []
    monkeypatch.setattr(queue, "run_child", fake_children(calls, drift=True))
    report, _ = queue.run("2018-08", "2018-09")
    assert report["status"] == "failed_checkpoints_retained"
    assert not report["verified_months"] and len(calls) == 1
    assert queue.manifest_path("2018-08").is_file()


def test_bad_readback_is_never_accepted(workspace, monkeypatch):
    calls = []
    monkeypatch.setattr(queue, "run_child", fake_children(calls, corrupt=True))
    report, _ = queue.run("2018-08", "2018-09")
    assert report["status"] == "failed_checkpoints_retained"
    assert not report["verified_months"]
    assert not queue.manifest_path("2018-09").exists()


def test_failed_month_retains_files_and_sanitizes_error_text(workspace, monkeypatch):
    def child(*args):
        month_manifest("2018-08")
        raise RuntimeError("sensitive external detail")

    monkeypatch.setattr(queue, "run_child", child)
    report, directory = queue.run("2018-08", "2018-09")
    assert report["status"] == "failed_checkpoints_retained"
    assert queue.manifest_path("2018-08").exists()
    assert not queue.manifest_path("2018-09").exists()
    assert "sensitive" not in (directory / "progress.json").read_text()
    assert not (workspace / "outputs/cache/vegetation_training_queue.lock").exists()


def test_interrupted_run_resumes_by_verifying_completed_month(workspace, monkeypatch):
    def timeout(arguments, log_path, deadline):
        month_manifest("2018-08")
        raise subprocess.TimeoutExpired("hidden command", 1)

    monkeypatch.setattr(queue, "run_child", timeout)
    first, _ = queue.run("2018-08", "2018-08")
    assert first["status"] == "paused_time_budget_checkpoints_retained"
    assert not first["verified_months"]
    calls = []
    monkeypatch.setattr(queue, "run_child", fake_children(calls))
    second, _ = queue.run("2018-08", "2018-08")
    assert second["status"] == "selected_training_range_verified"
    assert len(second["verified_months"]) == 1 and second["new_months"] == 0
    assert len(calls) == 1 and "download" not in calls[0]


def test_existing_lock_is_never_removed_or_bypassed(workspace):
    path = workspace / "outputs/cache/vegetation_training_queue.lock"
    path.parent.mkdir(parents=True)
    path.write_text("another process")
    with pytest.raises(FileExistsError):
        with queue.single_writer():
            pytest.fail("Overlapping writer")
    assert path.read_text() == "another process"


def test_live_callback_cannot_mutate_queue_acceptance(workspace, monkeypatch):
    calls, observed = [], []
    monkeypatch.setattr(queue, "run_child", fake_children(calls))

    def observer(directory, report):
        assert (directory / "progress.json").is_file()
        observed.append(len(report["verified_months"]))
        report["verified_months"].clear()

    report, _ = queue.run("2018-08", "2018-08", on_progress=observer)
    assert observed[-1] == 1
    assert len(report["verified_months"]) == 1


def test_child_is_killed_and_reaped_at_deadline(workspace):
    path = workspace / "private_child.log"
    with pytest.raises(subprocess.TimeoutExpired):
        queue.run_child(["-c", "import time; time.sleep(30)"], path, time.monotonic() + 0.2)
    assert path.is_file()


def test_user_interrupt_is_recorded_and_lock_released(workspace, monkeypatch):
    def interrupted(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(queue, "run_child", interrupted)
    report, _ = queue.run("2018-08", "2018-09")
    assert report["status"] == "interrupted_checkpoints_retained"
    assert not report["verified_months"]
    assert not (workspace / "outputs/cache/vegetation_training_queue.lock").exists()


@pytest.mark.parametrize(
    "options", [{"max_new_months": 0}, {"max_run_minutes": float("nan")}, {"min_free_gib": 0}]
)
def test_invalid_budgets_start_no_run(workspace, options):
    with pytest.raises(ValueError):
        queue.run("2018-08", "2018-09", **options)
    assert not (workspace / "outputs").exists()
