"""Deadline gate and deterministic packaging, without cloud execution."""

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    path = ROOT / "scripts/cloud" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    old = sys.path[:]
    try:
        sys.path.insert(0, str(path.parent))
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old
    return module


runner = load("proof_test", "run_gcp_drive_proof.py")
builder = load("proof_builder_test", "build_gcp_drive_proof.py")
verifier = load("proof_verifier_test", "verify_gcp_drive_proof.py")
NOW = dt.datetime(2026, 10, 6, tzinfo=dt.UTC)


def test_actual_deadline_leaves_stop_reserve():
    assert runner.parse_deadline("2026-10-06T00:20:00Z", NOW) == 900
    assert runner.parse_deadline("2026-10-06T02:00:00Z", NOW) == 1200


@pytest.mark.parametrize(
    "deadline", ["2026-10-06T00:14:59Z", "2026-10-06T02:00:01Z", "2026-10-06T01:00:00", "bad"]
)
def test_deadline_unknown_expired_or_changed_limit_refused(deadline):
    with pytest.raises(ValueError):
        runner.parse_deadline(deadline, NOW)


def test_package_bytes_deterministic():
    assert builder.archive_bytes({"b": b"two", "a": b"one"}) == builder.archive_bytes(
        {"a": b"one", "b": b"two"}
    )


def summary():
    phases = {}
    for kind, pid in (("save", 1), ("restore", 2)):
        phases[kind] = {
            "phase": kind,
            "status": "passed",
            "sample_id": "SNPP:2023197.0018",
            "manifest_sha256": "a" * 64,
            "payload_sha256": "b" * 64,
            "payload_bytes": 10,
            "scientific_readbacks": 1,
            "process_id": pid,
            "filesystem_only": False,
            "negative_label_permitted": False,
            "raw_downloads": 0,
            "existing_completion_reused": kind == "restore",
            "interruption_exercised": kind == "save",
        }
    return {
        "status": "drive_real_pair_persistence_passed",
        "manifest_sha256": "a" * 64,
        "production_months_processed": 0,
        "off_vm_persistence_proven": True,
        "negative_label_permitted": False,
        **phases,
    }


def preparation():
    return {"manifest_sha256": "a" * 64, "payload_sha256": "b" * 64, "payload_bytes": 10}


def test_summary_verification_does_not_claim_independent_remote_download():
    result = verifier.verify(summary(), preparation())
    assert result["remote_payload_independently_downloaded"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("filesystem_only", True),
        ("negative_label_permitted", True),
        ("scientific_readbacks", 0),
        ("process_id", 1),
        ("payload_sha256", "c" * 64),
    ],
)
def test_returned_summary_corruption_rejected(field, value):
    report = summary()
    report["restore"][field] = value
    with pytest.raises(ValueError):
        verifier.verify(report, preparation())


@pytest.fixture
def prepared_package(tmp_path):
    files = {
        name: b"fixture"
        for name in (
            "summer.zip",
            "pair.zip",
            "run_gcp_benchmark.py",
            "verified_job_store.py",
            "drive_job_store.py",
            "run_gcp_drive_proof.py",
        )
    }
    manifest = {
        "protocol": "gcp_drive_real_pair_proof_v1",
        "sample_id": "SNPP:2023197.0018",
        "negative_label_permitted": False,
        "raw_downloads": 0,
        "files": {n: verifier.sha(v) for n, v in files.items()},
    }
    files["proof_manifest.json"] = json.dumps(manifest).encode()
    path = tmp_path / "package.zip"
    path.write_bytes(builder.archive_bytes(files))
    preparation = {
        "package_sha256": verifier.sha(path.read_bytes()),
        "package_bytes": path.stat().st_size,
        "manifest_sha256": verifier.sha(files["proof_manifest.json"]),
        "payload_sha256": verifier.sha(files["pair.zip"]),
        "payload_bytes": len(files["pair.zip"]),
    }
    return path, preparation


def test_prepared_package_readback(prepared_package):
    verifier.verify_package(*prepared_package)


def test_changed_package_rejected_before_summary(prepared_package):
    path, preparation = prepared_package
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="package changed"):
        verifier.verify_package(path, preparation)


def test_wrong_manifest_reference_rejected(prepared_package):
    path, preparation = prepared_package
    preparation["manifest_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="manifest checksum"):
        verifier.verify_package(path, preparation)


def test_wrong_payload_reference_rejected(prepared_package):
    path, preparation = prepared_package
    preparation["payload_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="scientific payload"):
        verifier.verify_package(path, preparation)
