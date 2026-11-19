import copy
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "tested_source_queue", ROOT / "scripts/firms/run_source_review_queue.py"
)
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


def policy():
    return {
        "scope": "seven_frozen_source_rows_download_headers_only",
        "source_sample_sha256": queue.SAMPLE_SHA,
        "workers": 1,
        "download_runtime_seconds": 3600,
        "per_pair_runtime_seconds": 900,
        "stop_on_first_failure": True,
        "automatic_restart": False,
        "raw_eviction_permitted": False,
        "labels_created": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_training_permitted": False,
        "cloud_execution_permitted": False,
        "spatial_or_daily_acceptance_permitted": False,
        "units": [
            {"archive_row": row, "source_day": "2020-01-01", "bytes": 100}
            for row in sorted(queue.ROWS)
        ],
        "total_raw_bytes": 700,
    }


def test_exact_bounded_policy_passes_without_network():
    queue.validate_policy(policy())


@pytest.mark.parametrize(
    "key,value",
    [
        ("workers", 2),
        ("download_runtime_seconds", 7200),
        ("per_pair_runtime_seconds", 1800),
        ("stop_on_first_failure", False),
        ("automatic_restart", True),
        ("raw_eviction_permitted", True),
        ("labels_created", True),
        ("negative_label_permitted", True),
        ("daily_observation_status", "observed"),
        ("model_training_permitted", True),
        ("cloud_execution_permitted", True),
        ("spatial_or_daily_acceptance_permitted", True),
        ("source_sample_sha256", "other"),
        ("total_raw_bytes", 701),
    ],
)
def test_policy_widening_is_rejected(key, value):
    changed = policy()
    changed[key] = value
    with pytest.raises(ValueError):
        queue.validate_policy(changed)


@pytest.mark.parametrize("change", ["replacement", "duplicate", "future", "oversize"])
def test_sample_replacement_future_roles_and_expansion_are_rejected(change):
    changed = policy()
    if change == "replacement":
        changed["units"][0]["archive_row"] = "WF1342"
    elif change == "duplicate":
        changed["units"][0] = copy.deepcopy(changed["units"][1])
    elif change == "future":
        changed["units"][0]["source_day"] = "2023-01-01"
    else:
        changed["units"][0]["bytes"] = 1_500_000_001
        changed["total_raw_bytes"] = sum(u["bytes"] for u in changed["units"])
    with pytest.raises(ValueError):
        queue.validate_policy(changed)


@pytest.mark.parametrize("fail_login", [False, True])
def test_private_login_is_once_nonpersistent_and_environment_restored(monkeypatch, fail_login):
    monkeypatch.setenv("EARTHDATA_USERNAME", "previous-user")
    monkeypatch.setenv("EARTHDATA_PASSWORD", "previous-password")
    monkeypatch.setenv("EARTHDATA_TOKEN", "previous-token")
    calls = []

    def login(**kwargs):
        calls.append(kwargs)
        assert os.environ["EARTHDATA_USERNAME"] == "test-user"
        assert "EARTHDATA_TOKEN" not in os.environ
        if fail_login:
            raise RuntimeError("Do not expose this message")
        return SimpleNamespace(authenticated=True, token={"access_token": "test-only-token"})

    monkeypatch.setitem(sys.modules, "earthaccess", SimpleNamespace(login=login))
    monkeypatch.setattr(queue.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    entries = iter(["test-user", "test-password"])
    monkeypatch.setattr(queue.getpass, "getpass", lambda _: next(entries))
    try:
        with queue.private_token(True):
            assert not fail_login
            assert os.environ["EARTHDATA_TOKEN"] == "test-only-token"
            assert "EARTHDATA_USERNAME" not in os.environ
            assert "EARTHDATA_PASSWORD" not in os.environ
            raise LookupError("Simulated downstream failure")
    except (RuntimeError, LookupError):
        pass
    assert calls == [{"strategy": "environment", "persist": False}]
    assert os.environ["EARTHDATA_USERNAME"] == "previous-user"
    assert os.environ["EARTHDATA_PASSWORD"] == "previous-password"
    assert os.environ["EARTHDATA_TOKEN"] == "previous-token"


def test_failed_pair_stops_queue_and_records_no_secret_message(tmp_path, monkeypatch):
    queue_root = tmp_path / "queue"
    queue_root.mkdir()
    native_root = tmp_path / "native"
    native_root.mkdir()
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}")
    plan = policy()
    calls = []

    def failed_run(path, prompt):
        calls.append(path)
        assert prompt is False
        raise RuntimeError("sensitive test marker")

    runner = SimpleNamespace(OUTPUT=native_root, run=failed_run)
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    monkeypatch.setattr(queue, "BASE", queue_root)
    monkeypatch.setattr(queue, "runner_module", lambda: runner)
    monkeypatch.setattr(queue, "load_plan", lambda *_: plan)
    monkeypatch.setattr(queue, "completed_probe", lambda *_: None)
    monkeypatch.setattr(queue.shutil, "disk_usage", lambda _: SimpleNamespace(free=10**12))
    monkeypatch.setenv("EARTHDATA_TOKEN", "test-only-token")
    for unit in plan["units"]:
        unit["plan"] = "unused.json"
    assert queue.run(plan_path, execute=True) == 1
    assert len(calls) == 1
    report_path = next(queue_root.glob("*/readback.json"))
    text = report_path.read_text()
    report = json.loads(text)
    assert report["status"] == "stopped_outputs_retained"
    assert report["units"] == [] and report["labels_created"] is False
    assert "sensitive test marker" not in text and "test-only-token" not in text


def test_runtime_reserve_does_not_start_another_fifteen_minute_child(tmp_path, monkeypatch):
    queue_root = tmp_path / "queue"
    queue_root.mkdir()
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}")
    plan = policy()
    calls = []
    runner = SimpleNamespace(OUTPUT=tmp_path, run=lambda *_: calls.append(True))
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    monkeypatch.setattr(queue, "BASE", queue_root)
    monkeypatch.setattr(queue, "runner_module", lambda: runner)
    monkeypatch.setattr(queue, "load_plan", lambda *_: plan)
    monkeypatch.setattr(queue, "completed_probe", lambda *_: None)
    monkeypatch.setattr(queue.shutil, "disk_usage", lambda _: SimpleNamespace(free=10**12))
    monkeypatch.setenv("EARTHDATA_TOKEN", "test-only-token")
    ticks = iter([0, 2700])
    monkeypatch.setattr(queue.time, "monotonic", lambda: next(ticks))
    assert queue.run(plan_path, execute=True) == 1
    report = json.loads(next(queue_root.glob("*/readback.json")).read_text())
    assert report["status"] == "paused_at_download_runtime_reserve" and not calls


def test_all_completed_bytes_skip_login_and_network(tmp_path, monkeypatch):
    queue_root = tmp_path / "queue"
    queue_root.mkdir()
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}")
    monkeypatch.setattr(queue, "BASE", queue_root)
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    monkeypatch.setattr(queue, "runner_module", lambda: None)
    monkeypatch.setattr(queue, "load_plan", lambda *_: policy())
    monkeypatch.setattr(queue, "completed_probe", lambda *_: {"probe": "verified", "sha256": "h"})
    monkeypatch.setattr(queue.shutil, "disk_usage", lambda _: SimpleNamespace(free=10**12))
    monkeypatch.setattr(queue, "private_token", lambda *_: pytest.fail("No repeated login"))
    assert queue.run(plan_path, execute=True) == 0
    report = json.loads(next(queue_root.glob("*/readback.json")).read_text())
    assert len(report["units"]) == 7 and report["labels_created"] is False
