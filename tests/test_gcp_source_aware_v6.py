"""Reviewed Drive failure migration, metadata-only retries and frozen science guards."""

import ast
import hashlib
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
module = importlib.import_module("run_gcp_source_aware_continuation_v6")
reader = importlib.import_module("verify_gcp_v5_failure")
ARCHIVE = ROOT / "outputs/gcp_acceleration/received/gcp_v5_failure_20261011T234521Z.tar.gz"
PROBE = ROOT / "outputs/gcp_acceleration/received" / module.V5_PROBE_NAME


def test_science_shutdown_and_v5_child_retries_are_unchanged():
    def functions(path):
        return {
            node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(path.read_text(encoding="utf-8")).body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        }

    old = functions(ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v5.py")
    new = functions(Path(module.__file__))
    for name in set(old) - {"prepare_reviewed_failures", "instrument_backend", "main"}:
        assert old[name] == new[name], name
    renamed = old["prepare_reviewed_failures"].replace(
        "name='prepare_reviewed_failures'", "name='prepare_v4_failures'", 1
    )
    assert new["prepare_v4_failures"] == renamed


@pytest.mark.skipif(not PROBE.exists(), reason="Ignored real Drive probe unavailable")
def test_actual_probe_identity_and_coverage():
    assert module.sha(PROBE) == module.V5_PROBE_SHA
    value = json.loads(PROBE.read_bytes())
    assert value["protected_files_unchanged"] is True
    assert value["production_writes"] == value["drive_object_writes"] == 0
    assert len(value["pairs"]) == value["retained_candidates"] == 31
    assert sum(r["local_bytes"] for r in value["pairs"]) == value["retained_bytes"] == 81521503
    assert sum(r["state"] == "not_published" for r in value["pairs"]) == 30
    assert sum(r["state"] == "payload_without_completion" for r in value["pairs"]) == 1
    assert value["child_diagnostics"] == []


@pytest.fixture
def reviewed(tmp_path, monkeypatch):
    if not ARCHIVE.exists() or not PROBE.exists():
        pytest.skip("Ignored reviewed evidence unavailable")
    home, work = tmp_path, tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    files = reader.contents(ARCHIVE)
    for name in ("progress.json", "acceleration_run_summary.json", "continuation_summary.json"):
        (work / name).write_bytes(files[name])
    # Actual final bytes, synthetic retained payloads with an explicitly patched test probe pin.
    value = json.loads(PROBE.read_bytes())
    for n, row in enumerate(value["pairs"]):
        root = (
            work
            / "months/2020-07/accelerated_run/tasks"
            / hashlib.sha256(row["sample_id"].encode()).hexdigest()
        )
        root.mkdir(parents=True)
        path = root / "pair.zip"
        path.write_bytes(f"fixture-{n}".encode())
        row["local_bytes"] = path.stat().st_size
        row["local_sha256"] = module.sha(path)
    parent = work / value["parent_diagnostic"]["path"]
    parent.parent.mkdir(parents=True)
    parent.write_bytes(b"fixture parent diagnostic")
    value["parent_diagnostic"]["sha256"] = module.sha(parent)
    probe = home / module.V5_PROBE_NAME
    probe.write_text(json.dumps(value))
    monkeypatch.setattr(module, "V5_PROBE_SHA", module.sha(probe))
    control = SimpleNamespace(PRODUCTION=work)
    return control, value, probe


def test_exact_reviewed_state_rearms_dry_then_preserves_evidence_idempotently(reviewed):
    control, value, probe = reviewed
    before = {p: p.read_bytes() for p in control.PRODUCTION.rglob("*") if p.is_file()}
    module.prepare_reviewed_failures(control, False)
    assert before == {p: p.read_bytes() for p in control.PRODUCTION.rglob("*") if p.is_file()}
    module.prepare_reviewed_failures(control, True)
    module.prepare_reviewed_failures(control, True)
    assert all(path.read_bytes() == data for path, data in before.items())
    archived = control.PRODUCTION / "diagnostics/reviewed_v5_drive"
    assert len(list(archived.iterdir())) == 5
    assert (archived / probe.name).read_bytes() == probe.read_bytes()
    assert (archived / "progress.json").read_bytes() == before[control.PRODUCTION / "progress.json"]


@pytest.mark.parametrize("change", ["summary", "probe", "parent", "payload", "extra_failure"])
def test_changed_inputs_cannot_rearm_or_modify_production(reviewed, change):
    control, value, probe = reviewed
    if change == "summary":
        (control.PRODUCTION / "continuation_summary.json").write_bytes(b"{}")
    elif change == "probe":
        probe.write_bytes(probe.read_bytes() + b" ")
    elif change == "parent":
        (control.PRODUCTION / value["parent_diagnostic"]["path"]).write_bytes(b"changed")
    elif change == "payload":
        next((control.PRODUCTION / "months/2020-07").rglob("pair.zip")).write_bytes(b"changed")
    else:
        (control.PRODUCTION / "months/2020-07/continuation_failure.json").write_bytes(b"{}")
    with pytest.raises(ValueError):
        module.prepare_reviewed_failures(control, True)
    assert not (control.PRODUCTION / "diagnostics/reviewed_v5_drive").exists()


def retry_api(monkeypatch, error=404, succeed_on=2, failed=False, deadline=10000):
    clock, calls = [0.0], []
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(module.time, "sleep", lambda n: clock.__setitem__(0, clock[0] + n))

    def original(*args, **kwargs):
        calls.append((args, kwargs))
        if len(calls) < succeed_on:
            raise RuntimeError(f"Drive HTTP {error}; no secrets logged")
        return b"verified metadata"

    api = SimpleNamespace(request=original)
    sampler = SimpleNamespace(failed=failed)
    module.metadata_retry_requests(api, deadline, sampler)
    return api, calls, clock, sampler


def test_metadata_404_retries_same_id_and_arguments_with_bounded_backoff(monkeypatch, capsys):
    api, calls, clock, _ = retry_api(monkeypatch, succeed_on=4)
    assert api.request("/files/private_id?fields=id,name,size") == b"verified metadata"
    assert len(calls) == 4 and clock[0] == 17
    assert all(call == calls[0] for call in calls)
    assert capsys.readouterr().out == (
        "DRIVE_METADATA_RETRY 1 HTTP_404\nDRIVE_METADATA_RETRY 2 HTTP_404\n"
        "DRIVE_METADATA_RETRY 3 HTTP_404\n"
    )


def test_persistent_missing_metadata_still_fails_closed(monkeypatch):
    api, calls, clock, _ = retry_api(monkeypatch, succeed_on=99)
    with pytest.raises(RuntimeError, match="Drive HTTP 404"):
        api.request("/files/private_id?fields=id")
    assert len(calls) == 4 and clock[0] == 17


@pytest.mark.parametrize(
    "path,kwargs",
    [
        ("/files/private_id?alt=media", {}),
        ("/files?fields=id", {"method": "POST"}),
        ("/files/private_id?fields=id", {"method": "DELETE"}),
        (
            "/files?uploadType=multipart&fields=id",
            {"method": "POST", "upload": True, "data": b"ZIP"},
        ),
        ("/files/generateIds?count=1&space=drive", {}),
        ("/files?q=name", {}),
    ],
)
def test_upload_create_delete_media_listing_and_id_generation_never_retried(
    monkeypatch, path, kwargs
):
    api, calls, _, _ = retry_api(monkeypatch, succeed_on=99)
    with pytest.raises(RuntimeError):
        api.request(path, **kwargs)
    assert len(calls) == 1


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500, 503])
def test_other_http_errors_not_retried_by_new_layer(monkeypatch, status):
    api, calls, _, _ = retry_api(monkeypatch, error=status, succeed_on=99)
    with pytest.raises(RuntimeError):
        api.request("/files/private_id?fields=id")
    assert len(calls) == 1


@pytest.mark.parametrize("failed,deadline", [(True, 10000), (False, 1502)])
def test_retry_respects_sampler_and_publication_reserve(monkeypatch, failed, deadline):
    api, calls, clock, _ = retry_api(monkeypatch, succeed_on=99, failed=failed, deadline=deadline)
    with pytest.raises(ValueError, match="Drive retry resource/deadline guard"):
        api.request("/files/private_id?fields=id")
    assert len(calls) == 1 and clock[0] == 0


def test_resource_failure_during_backoff_prevents_next_get(monkeypatch):
    api, calls, clock, sampler = retry_api(monkeypatch, succeed_on=99)

    def sleep(n):
        clock[0] += n
        sampler.failed = True

    monkeypatch.setattr(module.time, "sleep", sleep)
    with pytest.raises(ValueError, match="Drive retry resource/deadline guard"):
        api.request("/files/private_id?fields=id")
    assert len(calls) == 1


def test_resource_failure_on_final_backoff_tick_also_prevents_next_get(monkeypatch):
    api, calls, clock, sampler = retry_api(monkeypatch, succeed_on=99)

    def sleep(n):
        clock[0] += n
        if clock[0] >= 2:
            sampler.failed = True

    monkeypatch.setattr(module.time, "sleep", sleep)
    with pytest.raises(ValueError, match="Drive retry resource/deadline guard"):
        api.request("/files/private_id?fields=id")
    assert len(calls) == 1


def test_uncertain_upload_uses_one_generated_id_and_one_post_even_with_metadata_retries(
    monkeypatch,
):
    from drive_job_store import SCOPE, DriveAPI

    clock, calls, reads = [0.0], [], [0]
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(module.time, "sleep", lambda n: clock.__setitem__(0, clock[0] + n))
    api = DriveAPI(
        {
            "scope": SCOPE,
            "client_id": "hidden",
            "client_secret": "hidden",
            "refresh_token": "hidden",
        }
    )

    def request(path, method="GET", **kwargs):
        calls.append((path, method))
        if path.startswith("/files/generateIds"):
            return b'{"ids":["fixed_id_123"]}'
        if method == "POST":
            raise RuntimeError("Drive transport failed; checkpoint retained")
        assert path == "/files/fixed_id_123?fields=id"
        reads[0] += 1
        if reads[0] < 4:
            raise RuntimeError("Drive HTTP 404; no secrets logged")
        return b'{"id":"fixed_id_123"}'

    api.request = request
    module.metadata_retry_requests(api, 10000, SimpleNamespace(failed=False))
    assert api.create_file({"name": "object"}, b"verified payload") == "fixed_id_123"
    assert sum(method == "POST" for _, method in calls) == 1
    assert sum(path.startswith("/files/generateIds") for path, _ in calls) == 1
    assert reads[0] == 4


@pytest.mark.parametrize("error", [RuntimeError("sensitive external text"), KeyboardInterrupt()])
def test_arbitrary_error_and_user_cancellation_do_not_retry(monkeypatch, error, capsys):
    calls = []

    def request(*args, **kwargs):
        calls.append(True)
        raise error

    api = SimpleNamespace(request=request)
    module.metadata_retry_requests(api, 10000, SimpleNamespace(failed=False))
    with pytest.raises(type(error)):
        api.request("/files/private_id?fields=id")
    assert len(calls) == 1
    assert capsys.readouterr().out == ""
