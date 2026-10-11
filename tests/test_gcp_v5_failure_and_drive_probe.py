"""V5 failure evidence boundaries and read-only checkpoint diagnosis."""

import importlib
import io
import json
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
reader = importlib.import_module("verify_gcp_v5_failure")
probe = importlib.import_module("diagnose_gcp_v5_drive_publication")
SOURCE = ROOT / "outputs/gcp_acceleration/received/gcp_v5_failure_20261011T234521Z.tar.gz"


@pytest.mark.skipif(not SOURCE.exists(), reason="Ignored real V5 archive unavailable")
def test_actual_v5_final_catalogue_and_resources(tmp_path):
    result = reader.verify(SOURCE, tmp_path / "readback.json")
    assert result["received_sha256"] == (
        "e7a08fcb89397ffe71eb288540741f6e04c230ef0f05dcdc8f5e9a2c8bb77fc1"
    )
    assert len(result["final_state"]["existing_months"]) == 40
    assert result["log_catalogue"]["new_pair_lines"] == 156
    assert result["log_catalogue"]["day_commit_lines"] == 17
    assert result["log_catalogue"]["pending_days"] == {
        "2020-07-18": {"saved_pair_lines": 5, "nominal_pairs": 8, "daily_committed": False}
    }
    assert len(result["log_catalogue"]["days_only_in_state"]) == 30
    assert result["telemetry"]["sampled_reserve_breach"] is False
    assert result["historical_file_or_call_site_identified"] is False
    assert result["live_drive_readback"] is False
    with pytest.raises(ValueError, match="Report collision"):
        reader.verify(SOURCE, tmp_path / "readback.json")


@pytest.mark.parametrize("name", ["../progress.json", "/progress.json", ".env", "unknown.json"])
def test_tar_unapproved_members_rejected_before_extraction(tmp_path, name):
    source = tmp_path / "bad.tar.gz"
    with tarfile.open(source, "w:gz") as archive:
        member = tarfile.TarInfo(name)
        member.size = 2
        archive.addfile(member, io.BytesIO(b"{}"))
    with pytest.raises(ValueError, match="Archive boundary"):
        reader.contents(source)
    assert not (tmp_path / "progress.json").exists()


@pytest.mark.parametrize("kind", [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.DIRTYPE])
def test_tar_links_and_directories_rejected(tmp_path, kind):
    source = tmp_path / "bad.tar.gz"
    with tarfile.open(source, "w:gz") as archive:
        member = tarfile.TarInfo("progress.json")
        member.type = kind
        member.linkname = "secret"
        archive.addfile(member)
    with pytest.raises(ValueError, match="Archive boundary"):
        reader.contents(source)


@pytest.mark.skipif(not SOURCE.exists(), reason="Ignored real V5 archive unavailable")
def test_changed_final_bytes_fail_before_acceptance():
    files = reader.contents(SOURCE)
    files["continuation_summary.json"] += b" "
    with pytest.raises(ValueError, match="Reviewed V5 final bytes"):
        reader.final_state(files)


def test_readonly_boundary_blocks_every_drive_mutation():
    calls = []
    api = SimpleNamespace(request=lambda *a, **kw: calls.append((a, kw)))
    probe.readonly_requests(api)
    api.request("/about")
    assert len(calls) == 1
    for kwargs in (
        {"method": "POST"},
        {"method": "PATCH"},
        {"method": "DELETE"},
        {"data": b"write"},
        {"upload": True},
    ):
        with pytest.raises(ValueError, match="Probe write forbidden"):
            api.request("/files", **kwargs)
    assert len(calls) == 1


def record(identity, local, worker):
    digest = probe.sha(local)
    return {
        "protocol": "verified_job_checkpoint_v1",
        "task_id": identity,
        "manifest_sha256": probe.SCOPE,
        "worker_sha256": worker,
        "payload_sha256": digest,
        "payload_bytes": len(local),
        "payload_key": f"jobs/{probe.SCOPE}/{probe.sha(identity.encode())}/{digest}.zip",
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
    }


@pytest.mark.parametrize(
    "state", ["completed_matches_local", "payload_without_completion", "not_published"]
)
def test_diagnosis_distinguishes_orphan_from_completion_without_writes(state):
    identity, local, worker = "SNPP:2020200.0012", b"payload", "0" * 64
    marker = (
        json.dumps(record(identity, local, worker)).encode()
        if state.startswith("completed")
        else None
    )
    remote = None if state == "not_published" else local
    calls = []

    def get(key):
        calls.append(key)
        return marker if key.endswith("completed.json") else remote

    backend = SimpleNamespace(get=get)
    result = probe.check_pair(backend, identity, local, worker, lambda _, fn: fn())
    assert result["state"] == state and len(calls) == 2


@pytest.mark.parametrize(
    "change",
    [
        {"negative_label_permitted": True},
        {"daily_observation_status": "clear"},
        {"payload_key": "elsewhere"},
        {"payload_sha256": "0" * 64},
        {"worker_sha256": "other"},
        {"extra": "secret"},
    ],
)
def test_wrong_marker_fails_before_payload_read(change):
    identity, local, worker = "SNPP:2020200.0012", b"payload", "0" * 64
    marker = json.dumps({**record(identity, local, worker), **change}).encode()
    calls = []

    def get(key):
        calls.append(key)
        return marker

    with pytest.raises(ValueError, match="Completion differs"):
        probe.check_pair(SimpleNamespace(get=get), identity, local, worker, lambda _, fn: fn())
    assert len(calls) == 1


@pytest.mark.parametrize("remote", [None, b"changed"])
def test_completed_missing_or_changed_payload_is_not_accepted(remote):
    identity, local, worker = "SNPP:2020200.0012", b"payload", "0" * 64
    marker = json.dumps(record(identity, local, worker)).encode()
    backend = SimpleNamespace(get=lambda key: marker if key.endswith("completed.json") else remote)
    with pytest.raises(ValueError):
        probe.check_pair(backend, identity, local, worker, lambda _, fn: fn())


def test_probe_does_not_mask_or_retry_404():
    calls = []

    def get(key):
        calls.append(key)
        raise RuntimeError("Drive HTTP 404; no secrets logged")

    with pytest.raises(RuntimeError, match="Drive HTTP 404"):
        probe.check_pair(
            SimpleNamespace(get=get), "SNPP:2020200.0012", b"data", "0" * 64, lambda _, fn: fn()
        )
    assert len(calls) == 1


def test_changed_helper_is_not_imported(tmp_path):
    (tmp_path / "diagnose_gcp_production_manifest.py").write_text("raise AssertionError('secret')")
    with pytest.raises(ValueError, match="Pinned HTTP helper"):
        probe.checked_helper(tmp_path)


def test_retained_inventory_preserves_files_and_drops_unreviewed_exception_text(tmp_path):
    work, original = tmp_path / "work", tmp_path / "original"
    original.mkdir()
    identity = "SNPP:2020200.0012"
    (original / "pairs.csv").write_text(
        "sensor,pair_key,day,pair_status\nSNPP,2020200.0012,2020-07-18,nominal_unique_pair\n"
    )
    meta = work / "months/2020-07/metadata"
    meta.mkdir(parents=True)
    (meta / "month.json").write_text(
        json.dumps(
            {
                "month": "2020-07",
                "negative_label_permitted": False,
                "pairs": [{"sample_id": identity}],
            }
        )
    )
    root = work / "months/2020-07/accelerated_run/tasks" / probe.sha(identity.encode())
    root.mkdir(parents=True)
    (root / "pair.zip").write_bytes(b"retained")
    failure = root / "continuation_failure.json"
    failure.write_text(json.dumps({"sample_id": identity, "guard": "PRIVATE_EXCEPTION_TEXT"}))
    before = {p: p.read_bytes() for p in work.rglob("*") if p.is_file()}
    candidates, protected, diagnostics = probe.retained_pairs(work, original)
    assert candidates == [(identity, b"retained")]
    assert len(protected) == 2
    assert diagnostics[0]["reviewed_schema"] == "OTHER_UNREVIEWED"
    assert "PRIVATE_EXCEPTION_TEXT" not in json.dumps(diagnostics)
    assert before == {p: p.read_bytes() for p in work.rglob("*") if p.is_file()}
    (meta / "month.json").write_text(
        json.dumps(
            {
                "month": "2020-07",
                "negative_label_permitted": False,
                "pairs": [{"sample_id": "SNPP:2020201.0012"}],
            }
        )
    )
    with pytest.raises(ValueError, match="Frozen July pair population"):
        probe.retained_pairs(work, original)


def test_parent_diagnostic_accepts_exact_schema_and_refuses_free_form_fields(tmp_path):
    folder = tmp_path / "diagnostics"
    folder.mkdir()
    path = folder / "parent_failure_v3_20261011T215249123456Z.json"
    value = {
        "protocol": "continuation_parent_failure_v3",
        "continuation_phase": "remaining_months",
        "error": "GOOGLE_HTTP_404",
        "guard": "CLASS_ONLY",
        "last_recorded_month": "2020-07",
        "last_recorded_stage": "pair_publication",
        "recorded_at_utc": "2026-10-11T21:52:49.123456+00:00",
    }
    path.write_text(json.dumps(value))
    result, protected = probe.parent_diagnostic(tmp_path)
    assert result["sha256"] == probe.sha(path.read_bytes())
    assert protected == {path: result["sha256"]}
    path.write_text(json.dumps({**value, "message": "PRIVATE_EXCEPTION_TEXT"}))
    with pytest.raises(ValueError, match="Parent schema"):
        probe.parent_diagnostic(tmp_path)
