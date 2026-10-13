"""Rearm evidence is bounded, sanitized, immutable and rejects unreviewed failures."""

import importlib.util
import json
from pathlib import Path

import pytest
from test_gcp_v6_geolocation_snapshot import home as snapshot_home
from test_gcp_v6_geolocation_snapshot import module as helper

ROOT = Path(__file__).resolve().parents[1]
home = snapshot_home
spec = importlib.util.spec_from_file_location(
    "v6_resume_snapshot", ROOT / "scripts/cloud/collect_gcp_v6_resume_snapshot.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def reviewed(home, monkeypatch):
    work = home / "wildfire-gcp-production-v1"
    plan_path = work / "months/2018-06/metadata/month.json"
    plan = json.loads(plan_path.read_bytes())
    for identity in (*module.CANCELLED, "SNPP:2018166.0000"):
        pair = dict(plan["pairs"][0], sample_id=identity)
        plan["pairs"].append(pair)
        root = work / "months/2018-06/accelerated_run/tasks" / helper.sha(identity.encode())
        root.mkdir()
        if identity in module.CANCELLED:
            (root / "continuation_failure.json").write_text(
                json.dumps(
                    {
                        "sample_id": identity,
                        "child_kind": "pair",
                        "error_type": "RuntimeError",
                        "guard": "CLASS_ONLY",
                        "exit_code": -9,
                        "termination_kind": "nonzero_exit_without_python_diagnostic",
                        "private_extra": "do not export this",
                    }
                ),
                encoding="utf-8",
            )
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    parents = work / "diagnostics"
    parents.mkdir()
    (parents / "parent_failure_v3_20261013T030000Z.json").write_text(
        json.dumps(
            {
                "protocol": "continuation_parent_failure_v3",
                "continuation_phase": "remaining_months",
                "error": "RuntimeError",
                "guard": "CLASS_ONLY",
                "last_recorded_month": "2018-06",
                "last_recorded_stage": "pair_publication",
                "private_extra": "do not export this",
            }
        ),
        encoding="utf-8",
    )
    payload = (
        work
        / "months/2018-06/accelerated_run/tasks"
        / helper.sha(helper.FOCUS[0].encode())
        / "pair.zip"
    )
    payload.write_bytes(b"synthetic public payload")
    proof = helper.snapshot(home)
    monkeypatch.setattr(module, "PLAN_SHA", proof["month_plan_sha256"])
    return home, proof, payload


def cancelled_path(home):
    return (
        home
        / "wildfire-gcp-production-v1/months/2018-06/accelerated_run/tasks"
        / helper.sha(module.CANCELLED[0].encode())
        / "continuation_failure.json"
    )


def test_snapshot_sanitizes_and_preserves_every_existing_byte(reviewed, monkeypatch):
    home, proof, payload = reviewed
    before = {p: helper.sha(p.read_bytes()) for p in home.rglob("*") if p.is_file()}
    original = Path.read_bytes

    def read(path):
        assert "raw" not in path.parts and ".config" not in path.parts
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    result = module.collect(home, helper, proof)
    assert len(result["child_diagnostics"]) == 18 and len(result["parent_diagnostics"]) == 1
    assert result["retained_pair_zips"][0]["sha256"] == helper.sha(payload.read_bytes())
    assert result["production_writes"] == result["network_requests"] == 0
    assert not result["scientific_product_readback"]
    assert "do not export this" not in json.dumps(result)
    monkeypatch.setattr(Path, "read_bytes", original)
    assert before == {p: helper.sha(p.read_bytes()) for p in home.rglob("*") if p.is_file()}


def test_cancelled_child_with_different_error_is_rejected(reviewed):
    home, proof, _ = reviewed
    path = cancelled_path(home)
    value = json.loads(path.read_bytes())
    value["exit_code"] = 1
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Reviewed cancelled child"):
        module.collect(home, helper, proof)


def test_additional_unreviewed_child_is_rejected(reviewed):
    home, proof, _ = reviewed
    root = (
        home
        / "wildfire-gcp-production-v1/months/2018-06/accelerated_run/tasks"
        / helper.sha(b"SNPP:2018166.0000")
    )
    (root / "continuation_failure.json").write_text("{}")
    with pytest.raises(ValueError, match="Unreviewed child failure"):
        module.collect(home, helper, proof)


def test_changed_prior_proof_is_rejected(reviewed):
    home, proof, _ = reviewed
    proof["protected_file_sha256"]["source_blocks.json"] = "0" * 64
    with pytest.raises(ValueError, match="Same previously reviewed"):
        module.collect(home, helper, proof)


def test_payload_change_during_hashing_is_rejected(reviewed, monkeypatch):
    home, proof, payload = reviewed
    original = Path.read_bytes
    count = 0

    def changed(path):
        nonlocal count
        raw = original(path)
        if path == payload:
            count += 1
            if count == 1:
                path.write_bytes(raw + b"changed")
        return raw

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(ValueError, match="Protected resume evidence changed"):
        module.collect(home, helper, proof)


def test_unreviewed_parent_is_rejected(reviewed):
    home, proof, _ = reviewed
    path = next((home / "wildfire-gcp-production-v1/diagnostics").glob("parent_failure_v3_*.json"))
    value = json.loads(path.read_bytes())
    value["error"] = "GOOGLE_HTTP_404"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Reviewed parent diagnostic"):
        module.collect(home, helper, proof)
