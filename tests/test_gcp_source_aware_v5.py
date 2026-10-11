"""Reviewed failure rearm, bounded retries, unchanged science and 18-hour cutoff."""

import ast
import hashlib
import importlib
import json
import sys
import tarfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
module = importlib.import_module("run_gcp_source_aware_continuation_v5")
verifier = importlib.import_module("verify_gcp_v4_failure")

ARCHIVE = ROOT / (
    "outputs/gcp_acceleration/source_aware_v4_13h_2026-10-10/received/"
    "gcp_v4_failure_20261011T150511Z.tar.gz"
)
NOW = datetime(2026, 10, 11, 15, tzinfo=UTC)


@pytest.mark.parametrize("seconds", [4200, 46800, 64800, 64860])
def test_eighteen_hour_deadline_and_stop_reserve(seconds):
    assert (
        module.runtime_seconds((NOW + timedelta(seconds=seconds)).isoformat(), NOW) == seconds - 300
    )


@pytest.mark.parametrize("seconds", [-1, 4199, 64861, 86400])
def test_unsafe_deadlines_fail(seconds):
    with pytest.raises(ValueError):
        module.runtime_seconds((NOW + timedelta(seconds=seconds)).isoformat(), NOW)


def test_trial_and_timezone_fail_closed():
    with pytest.raises(ValueError, match="timezone"):
        module.runtime_seconds("2026-10-12T09:00:00", NOW)
    with pytest.raises(ValueError, match="Trial cutoff"):
        module.runtime_seconds("2026-10-24T00:00:00Z", datetime(2026, 10, 23, 12, tzinfo=UTC))


def test_science_shutdown_and_existing_checkpoint_logic_are_unchanged():
    def functions(path):
        return {
            n.name: ast.dump(n, include_attributes=False)
            for n in ast.parse(path.read_text(encoding="utf-8")).body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef))
        }

    old = functions(ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v4.py")
    new = functions(Path(module.__file__))
    changed = {
        "runtime_seconds",
        "reviewed_resume",
        "prepare_reviewed_failures",
        "diagnostic_launcher",
        "main",
    }
    for name in set(old) - changed:
        assert old[name] == new[name], name
    # The previous launcher's actual subprocess/kill/cleanup body is retained.
    original = old["diagnostic_launcher"].replace(
        "name='diagnostic_launcher'", "name='diagnostic_launcher_once'", 1
    )
    assert new["diagnostic_launcher_once"] == original
    original = old["prepare_reviewed_failures"].replace(
        "name='prepare_reviewed_failures'", "name='prepare_legacy_failures'", 1
    )
    assert new["prepare_legacy_failures"] == original


@pytest.fixture
def reviewed(tmp_path):
    if not ARCHIVE.is_file():
        pytest.skip("Ignored reviewed archive unavailable")
    files = verifier.contents(ARCHIVE)
    for name, data in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    control = SimpleNamespace(PRODUCTION=tmp_path, atomic=lambda p, v: p.write_text(json.dumps(v)))
    return control, files


def test_reviewed_rearm_is_dry_then_byte_preserving_and_idempotent(reviewed):
    control, files = reviewed
    before = {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}
    module.prepare_reviewed_failures(control, False)
    assert all((control.PRODUCTION / n).read_bytes() == files[n] for n in files)
    module.prepare_reviewed_failures(control, True)
    module.prepare_reviewed_failures(control, True)
    for name, checksum in module.V4_DIAGNOSTICS.items():
        source = control.PRODUCTION / name
        archive = (
            control.PRODUCTION / "diagnostics/reviewed_v4_timeout" / (source.parent.name + ".json")
        )
        assert not source.exists()
        assert module.sha(archive) == checksum == before[name]
    for name in verifier.BASE:
        assert (control.PRODUCTION / name).read_bytes() == files[name]


@pytest.mark.parametrize("mutation", ["diagnostic", "summary", "extra"])
def test_changed_or_unreviewed_diagnostics_are_not_rearmed(reviewed, mutation):
    control, files = reviewed
    if mutation == "diagnostic":
        (control.PRODUCTION / next(iter(module.V4_DIAGNOSTICS))).write_text("{}")
    elif mutation == "summary":
        (control.PRODUCTION / "continuation_summary.json").write_bytes(
            files["progress.json"] + b" "
        )
    else:
        extra = control.PRODUCTION / "months/2020-07/extra/continuation_failure.json"
        extra.parent.mkdir()
        extra.write_text("{}")
    with pytest.raises(ValueError):
        module.prepare_reviewed_failures(control, True)
    assert not (control.PRODUCTION / "diagnostics/reviewed_v4_timeout").exists()


def timeout_file(root, identity="N20:2020183.0918", error="ReadTimeout"):
    value = {
        "sample_id": identity,
        "child_kind": "pair",
        "error_type": error,
        "guard": "CLASS_ONLY",
        "safe_error": "UNCLASSIFIED_ERROR",
    }
    (root / "continuation_failure.json").write_text(json.dumps(value))


@pytest.mark.parametrize(
    "kind,error,identity",
    [
        ("pair", "ValueError", "N20:2020183.0918"),
        ("pair", "HTTPError", "N20:2020183.0918"),
        ("pair", "RuntimeError", "N20:2020183.0918"),
        ("day", "ReadTimeout", "N20:2020183.0918"),
        ("pair", "ReadTimeout", "wrong"),
    ],
)
def test_scientific_auth_http_and_wrong_identity_are_never_retried(tmp_path, kind, error, identity):
    timeout_file(tmp_path, error=error)
    assert not module.retryable_failure(tmp_path, kind, identity)


def retry_fixture(tmp_path, monkeypatch, success_on=3, failed=False, deadline=10000):
    clock, calls = [0.0], []
    task = tmp_path / "task"
    task.mkdir()
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        module.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds)
    )

    def once(*args):
        assert not (task / "continuation_failure.json").exists()
        calls.append(True)
        if len(calls) < success_on:
            timeout_file(task)
            raise RuntimeError("external sensitive text must not be logged")
        return 1

    monkeypatch.setattr(module, "diagnostic_launcher_once", lambda *a: once)
    launch = module.diagnostic_launcher(
        SimpleNamespace(PRODUCTION=tmp_path), SimpleNamespace(CHILD_LIMIT=900), None
    )
    values = (
        None,
        "pair",
        task,
        None,
        "N20:2020183.0918",
        None,
        deadline,
        SimpleNamespace(failed=failed),
    )
    return launch, values, calls, clock


def test_success_after_two_timeouts_retains_diagnostics_and_backoff(tmp_path, monkeypatch, capsys):
    launch, values, calls, clock = retry_fixture(tmp_path, monkeypatch)
    assert launch(*values) == 90
    assert len(calls) == 3
    assert len(list((tmp_path / "diagnostics/transient_read_timeout").rglob("*.json"))) == 2
    assert not (values[2] / "continuation_failure.json").exists()
    values[2].rmdir()
    assert len(list((tmp_path / "diagnostics/transient_read_timeout").rglob("*.json"))) == 2
    assert "sensitive" not in capsys.readouterr().out


def test_persistent_timeout_stops_after_three_attempts(tmp_path, monkeypatch):
    launch, values, calls, clock = retry_fixture(tmp_path, monkeypatch, success_on=99)
    with pytest.raises(RuntimeError):
        launch(*values)
    assert len(calls) == 3
    assert (values[2] / "continuation_failure.json").is_file()


@pytest.mark.parametrize("failed,deadline", [(True, 10000), (False, 2130)])
def test_deadline_and_resource_failures_never_rearm(tmp_path, monkeypatch, failed, deadline):
    launch, values, calls, clock = retry_fixture(tmp_path, monkeypatch, 99, failed, deadline)
    with pytest.raises(RuntimeError):
        launch(*values)
    assert len(calls) == 1 and clock[0] == 0
    assert (values[2] / "continuation_failure.json").exists()


def test_retry_rejects_extra_fields_and_preserves_original_error(tmp_path):
    timeout_file(tmp_path)
    path = tmp_path / "continuation_failure.json"
    value = json.loads(path.read_bytes())
    value["unexpected"] = "external text"
    path.write_text(json.dumps(value))
    assert not module.retryable_failure(tmp_path, "pair", value["sample_id"])


def test_resource_guard_during_backoff_preserves_current_failure(tmp_path, monkeypatch):
    launch, values, calls, clock = retry_fixture(tmp_path, monkeypatch, success_on=99)
    sampler = values[-1]

    def sleep(seconds):
        clock[0] += seconds
        sampler.failed = True

    monkeypatch.setattr(module.time, "sleep", sleep)
    with pytest.raises(ValueError, match="Retry resource/deadline guard"):
        launch(*values)
    assert len(calls) == 1
    assert (values[2] / "continuation_failure.json").exists()
    assert not (tmp_path / "diagnostics/transient_read_timeout").exists()


@pytest.mark.parametrize("error", [TimeoutError, KeyboardInterrupt])
def test_watchdog_and_cancellation_are_never_retried(tmp_path, monkeypatch, error):
    calls = []

    def once(*args):
        calls.append(True)
        raise error()

    monkeypatch.setattr(module, "diagnostic_launcher_once", lambda *a: once)
    launch = module.diagnostic_launcher(None, SimpleNamespace(CHILD_LIMIT=900), None)
    with pytest.raises(error):
        launch(
            None,
            "pair",
            tmp_path,
            None,
            "N20:2020183.0918",
            None,
            10000,
            SimpleNamespace(failed=False),
        )
    assert len(calls) == 1


def test_unreviewed_v4_state_cannot_migrate(tmp_path):
    helper = SimpleNamespace(sha=lambda b: hashlib.sha256(b).hexdigest())
    assert not module.reviewed_resume(
        b"{}", {"continuation_wrapper_sha256": module.V4_WRAPPER_SHA}, tmp_path, helper
    )


def test_real_archive_catalogue_and_telemetry(tmp_path):
    if not ARCHIVE.is_file():
        pytest.skip("Ignored reviewed archive unavailable")
    r = verifier.verify(ARCHIVE, tmp_path / "readback.json")
    assert len(r["final_state"]["existing_months"]) == 40
    assert r["log_catalogue"]["new_pair_lines"] == 3020
    assert not r["telemetry"]["sampled_reserve_breach"]
    assert not r["scientific_product_readback"] and r["network_requests"] == 0


@pytest.mark.parametrize(
    "name,type_",
    [
        (".. /progress.json", tarfile.REGTYPE),
        ("progress.json", tarfile.SYMTYPE),
        ("private_connection.json", tarfile.REGTYPE),
    ],
)
def test_archive_rejects_unknown_paths_and_links(tmp_path, name, type_):
    import io

    p = tmp_path / "bad.tar.gz"
    with tarfile.open(p, "w:gz") as t:
        m = tarfile.TarInfo(name)
        m.type = type_
        m.size = 1
        t.addfile(m, io.BytesIO(b"x"))
    with pytest.raises(ValueError, match="boundary"):
        verifier.contents(p)
