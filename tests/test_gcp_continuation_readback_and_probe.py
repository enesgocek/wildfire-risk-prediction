"""Actual local evidence and strictly read-only publication diagnostics."""

import hashlib
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
reader = importlib.import_module("verify_gcp_source_aware_failure")
probe = importlib.import_module("diagnose_gcp_continuation_publication")
capture = importlib.import_module("collect_gcp_source_aware_failure")
SOURCE = ROOT / (
    "outputs/gcp_acceleration/continuation_failure_2026-10-09/received/"
    "gcp_source_aware_failure_2026-10-09.zip"
)


@pytest.mark.skipif(not SOURCE.is_file(), reason="Ignored received evidence unavailable")
def test_actual_capture_integrity_resources_and_source_policy():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
        "74273df994a005372be4c3916c569a8670fde801d1816e60bed78b6a0841d260"
    )
    report, data = reader.archive_contents(SOURCE)
    state = capture.state(data["progress.json"])
    assert state["failed_month"] == "2022-11" and state["pairs_processed_this_invocation"] == 1989
    assert len(report["task_inventory"]) == 29
    assert sum(t["pair_zip_present"] for t in report["task_inventory"]) == 19
    resources = reader.telemetry(data["resource_samples.csv"])
    assert resources["samples"] == 12018 and resources["sampled_reserve_breach"] is False
    assert resources["min_disk_free_bytes"] == 13865873408
    assert resources["min_mem_available_bytes"] == 119776571392


def test_api_guard_forbids_all_drive_object_mutations():
    calls = []
    api = SimpleNamespace(request=lambda *a, **k: calls.append((a, k)) or b"ok")
    probe.readonly_requests(api)
    assert api.request("/files?fields=id") == b"ok"
    for method in ("POST", "PATCH", "PUT", "DELETE"):
        with pytest.raises(ValueError, match="Probe write forbidden"):
            api.request("/files", method=method)
    with pytest.raises(ValueError):
        api.request("/files", data=b"data")
    with pytest.raises(ValueError):
        api.request("/files", upload=True)
    assert len(calls) == 1


def fixture_objects(state):
    scope, worker, identity, local = "a" * 64, "b" * 64, "SNPP:2022314.1048", b"local-science"
    prefix = f"jobs/{scope}/{capture.sha(identity.encode())}"
    key = f"{prefix}/{capture.sha(local)}.zip"
    marker = {
        "protocol": "verified_job_checkpoint_v1",
        "task_id": identity,
        "manifest_sha256": scope,
        "worker_sha256": worker,
        "payload_sha256": capture.sha(local),
        "payload_bytes": len(local),
        "payload_key": key,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
    }
    objects = {}
    if state != "not_published":
        objects[key] = local
    if state == "completed_matches_local":
        objects[prefix + "/completed.json"] = json.dumps(marker).encode()
    return scope, worker, identity, local, objects, prefix, key


@pytest.mark.parametrize(
    "state", ["not_published", "payload_without_completion", "completed_matches_local"]
)
def test_probe_distinguishes_missing_orphan_and_completed_without_writes(state):
    scope, worker, identity, local, objects, _, _ = fixture_objects(state)
    before = objects.copy()
    result = probe.probe_pairs(
        SimpleNamespace(get=objects.get),
        [(identity, local)],
        scope,
        worker,
        capture.sha,
        lambda name, action: action(),
    )
    assert result[0]["state"] == state and objects == before


@pytest.mark.parametrize("fault", ["payload", "marker", "missing_payload"])
def test_existing_corrupt_objects_are_rejected_without_repair(fault):
    scope, worker, identity, local, objects, prefix, key = fixture_objects(
        "completed_matches_local"
    )
    if fault == "payload":
        objects[key] = b"changed"
    elif fault == "marker":
        m = json.loads(objects[prefix + "/completed.json"])
        m["negative_label_permitted"] = True
        objects[prefix + "/completed.json"] = json.dumps(m).encode()
    else:
        objects.pop(key)
    before = objects.copy()
    with pytest.raises(ValueError):
        probe.probe_pairs(
            SimpleNamespace(get=objects.get),
            [(identity, local)],
            scope,
            worker,
            capture.sha,
            lambda name, action: action(),
        )
    assert objects == before


def test_changed_dependency_rejected_before_module_execution(tmp_path):
    (tmp_path / "helper.py").write_text("raise AssertionError('MUST_NOT_LOAD')")
    with pytest.raises(ValueError, match="Diagnostic helper hash"):
        probe.helper(tmp_path, "helper.py", "a" * 64)


def test_safe_error_redacts_external_response_and_retains_http_code_only():
    diagnostic = importlib.import_module("diagnose_gcp_production_manifest")
    assert (
        diagnostic.safe_error(RuntimeError("Drive HTTP 503; no secrets logged"))
        == "GOOGLE_HTTP_503"
    )
    assert diagnostic.safe_error(RuntimeError("SECRET_TOKEN_RESPONSE")) == "RuntimeError"
