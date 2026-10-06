"""Two-pass readback, interruption, corruption, identity, and time-budget gates."""

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "job_store_test", ROOT / "scripts/cloud/verified_job_store.py"
)
store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(store)


@pytest.fixture
def fixture(tmp_path):
    source = tmp_path / "source.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("counts.csv", "grid_id,count\ng,7\n")
    backend = store.RehearsalFileStore(tmp_path / "saved")
    job = store.VerifiedJobStore(backend, "a" * 64, "b" * 64, 1_000_000)
    calls = []

    def science(path):
        with zipfile.ZipFile(path) as archive:
            assert archive.read("counts.csv") == b"grid_id,count\ng,7\n"
        calls.append(path)

    return source, backend, job, science, calls


def test_saved_object_rechecked_in_fresh_directory_before_marker(fixture):
    source, backend, job, science, calls = fixture
    record = job.save("SNPP:sample", source, {"counts.csv"}, science)
    assert source in calls and any(p != source for p in calls)
    assert record["negative_label_permitted"] is False
    restarted = store.VerifiedJobStore(backend, "a" * 64, "b" * 64, 1_000_000)
    assert restarted.restore("SNPP:sample", {"counts.csv"}, science) == record
    assert job.save("SNPP:sample", source, {"counts.csv"}, science) == record


def test_interruption_after_payload_before_marker_resumes_without_recompute(fixture, monkeypatch):
    source, backend, job, science, _ = fixture
    create = backend.create

    def interrupt(key, data):
        if key.endswith("completed.json"):
            raise OSError("simulated process loss")
        return create(key, data)

    monkeypatch.setattr(backend, "create", interrupt)
    with pytest.raises(OSError):
        job.save("task", source, {"counts.csv"}, science)
    assert job.restore("task", {"counts.csv"}, science) is None
    monkeypatch.setattr(backend, "create", create)
    assert (
        job.save("task", source, {"counts.csv"}, science)["payload_bytes"] == source.stat().st_size
    )


def test_failed_saved_readback_never_publishes_marker(fixture, monkeypatch):
    source, backend, job, science, _ = fixture
    get = backend.get
    monkeypatch.setattr(
        backend,
        "get",
        lambda key: b"corrupt" if key.endswith(".zip") and get(key) is not None else get(key),
    )
    with pytest.raises(ValueError, match="readback"):
        job.save("task", source, {"counts.csv"}, science)
    assert get(job.task_prefix("task") + "/completed.json") is None


def test_marker_without_payload_is_rejected(fixture):
    source, backend, job, science, _ = fixture
    record = job.save("task", source, {"counts.csv"}, science)
    backend.path(record["payload_key"]).unlink()
    with pytest.raises(ValueError, match="Saved payload changed"):
        job.restore("task", {"counts.csv"}, science)


@pytest.mark.parametrize(
    "field,value",
    [
        ("worker_sha256", "c" * 64),
        ("negative_label_permitted", True),
        ("payload_key", "../other.zip"),
        ("daily_observation_status", "observed"),
    ],
)
def test_wrong_marker_identity_or_policy_never_reused(fixture, field, value):
    source, backend, job, science, _ = fixture
    record = job.save("task", source, {"counts.csv"}, science)
    record[field] = value
    backend.path(job.task_prefix("task") + "/completed.json").write_text(json.dumps(record))
    with pytest.raises(ValueError):
        job.restore("task", {"counts.csv"}, science)


def test_storage_budget_rejects_before_upload(fixture):
    source, backend, _, science, _ = fixture
    job = store.VerifiedJobStore(backend, "a" * 64, "b" * 64, 1)
    with pytest.raises(ValueError, match="budget"):
        job.save("task", source, {"counts.csv"}, science)
    assert backend.used_bytes("jobs/" + "a" * 64) == 0


def test_extra_zip_member_cannot_be_marked_complete(fixture):
    source, backend, job, science, _ = fixture
    with zipfile.ZipFile(source, "a") as archive:
        archive.writestr("../outside", "bad")
    with pytest.raises(ValueError, match="members"):
        job.save("task", source, {"counts.csv"}, science)
    assert backend.used_bytes("jobs/" + "a" * 64) == 0


def test_second_scientific_readback_failure_preserves_uncommitted_payload(fixture):
    source, backend, job, _, _ = fixture
    calls = 0

    def check(_):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("saved scientific check failed")

    with pytest.raises(ValueError, match="scientific"):
        job.save("task", source, {"counts.csv"}, check)
    assert backend.get(job.task_prefix("task") + "/completed.json") is None
    assert source.exists()


@pytest.mark.parametrize("key", ["../x", "/absolute", "jobs//x", "jobs/../x", "x\\y"])
def test_store_key_cannot_escape_workspace(fixture, key):
    _, backend, _, _, _ = fixture
    with pytest.raises(ValueError):
        backend.create(key, b"data")


def test_new_task_stops_before_deadline_reserve_is_consumed():
    assert store.may_start_task(1081)
    assert not store.may_start_task(1080)
    assert not store.may_start_task(60)


@pytest.mark.parametrize("remaining", [float("inf"), float("nan"), -1, True])
def test_invalid_deadline_cannot_start_work(remaining):
    with pytest.raises(ValueError, match="Remaining runtime"):
        store.may_start_task(remaining)
