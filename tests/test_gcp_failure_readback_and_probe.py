"""Actual evidence hashes plus diagnostic isolation and credential-free failure logging."""

import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
reader = importlib.import_module("verify_gcp_acceleration_failure")
probe = importlib.import_module("probe_gcp_retained_sources")
SOURCE = ROOT / "outputs/gcp_acceleration/received/gcp_acceleration_failure_2026-10-09.zip"


def test_actual_evidence_integrity_and_resource_readback():
    report, data = reader.archive_contents(SOURCE)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
        "f157cf60b334d4e815948721670f959ad49f2a350b3b7ff4c090eed07c39db27"
    )
    assert len(report["task_inventory"]) == 34
    assert sum(t["pair_zip_present"] for t in report["task_inventory"]) == 20
    resource = reader.telemetry(data["resource_samples.csv"])
    assert resource["samples"] == 3862
    assert resource["sampled_reserve_breach"] is False
    assert resource["min_disk_free_bytes"] == 16487358464


def test_guard_whitelist_does_not_copy_external_error_text_or_unlisted_source(tmp_path):
    (tmp_path / "production_manifest.json").write_text(json.dumps({"files": {"checked.py": ""}}))
    (tmp_path / "checked.py").write_text('require(False, "Known scientific check")')
    (tmp_path / "unlisted.py").write_text('require(False, "SECRET_CONNECTION_VALUE")')
    assert probe.error_summary(ValueError("Known scientific check"), [tmp_path])["guard"] == (
        "Known scientific check"
    )
    result = probe.error_summary(ValueError("SECRET_CONNECTION_VALUE"), [tmp_path])
    assert result["guard"] == "CLASS_ONLY" and "SECRET" not in json.dumps(result)


def setup_science(tmp_path):
    root, output = tmp_path / "original", tmp_path / "isolated"
    raw = root / "summer/raw/l2_sample_2023365.0106"
    raw.mkdir(parents=True)
    output.mkdir()
    (raw / "source.nc").write_bytes(b"local source")
    pair = {"stem": raw.name, "sources": [{"filename": "source.nc", "bytes": 12}]}
    return root, output, pair


def test_probe_checks_existing_raw_and_writes_only_isolated_outputs(tmp_path):
    root, output, pair = setup_science(tmp_path)
    calls = []

    def source_check(_pair, _source, path):
        assert path.read_bytes() == b"local source"
        calls.append("source")

    def audit(_pair, raw):
        assert raw.is_relative_to(root)
        assert native.OUTPUT == output
        (native.OUTPUT / "diagnostic.json").write_text("{}")
        calls.append("audit")

    def compare(_pair, path):
        assert path == output and (path / "diagnostic.json").read_text() == "{}"
        calls.append("compare")

    native = SimpleNamespace(source_check=source_check, child_audit=audit, compare_pair=compare)
    runner = SimpleNamespace(science=lambda path: (None, native))
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    probe.scientific_probe(runner, root, pair, output)
    assert calls == ["source", "audit", "compare"]
    assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_source_failure_is_not_suppressed_or_followed_by_scientific_processing(tmp_path):
    root, output, pair = setup_science(tmp_path)

    def bad(*_):
        raise ValueError("CMR checksum differs")

    def forbidden(*_):
        pytest.fail("Invalid source must not reach science")

    runner = SimpleNamespace(
        science=lambda path: (
            None,
            SimpleNamespace(source_check=bad, child_audit=forbidden, compare_pair=forbidden),
        )
    )
    with pytest.raises(ValueError, match="CMR checksum differs"):
        probe.scientific_probe(runner, root, pair, output)
    assert not list(output.iterdir())


def test_no_network_audit_hook_blocks_connection_before_any_request():
    script = (
        "import sys,socket;sys.path.insert(0,'scripts/cloud');"
        "import probe_gcp_retained_sources as p;p.block_network();"
        "socket.create_connection(('127.0.0.1',9))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True, timeout=10
    )
    assert result.returncode != 0 and "Diagnostic network forbidden" in result.stderr


def test_changed_helper_is_rejected_before_loading(tmp_path):
    (tmp_path / "collect_gcp_acceleration_failure.py").write_text("raise AssertionError('LOAD')")
    with pytest.raises(probe.ProbeCheck, match="Pinned diagnostic helper"):
        probe.helper(tmp_path)
