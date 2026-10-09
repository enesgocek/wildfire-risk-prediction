"""A received probe must bind to the exact accepted local scientific payloads."""

import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
reader = importlib.import_module("verify_gcp_publication_probe")
BASE = ROOT / "outputs/gcp_acceleration/continuation_failure_2026-10-09/received"
PROBE = BASE / "gcp_continuation_publication_probe_2026-10-09.json"
ARCHIVE = BASE / "gcp_source_aware_failure_2026-10-09.zip"
pytestmark = pytest.mark.skipif(
    not PROBE.is_file() or not ARCHIVE.is_file(), reason="Ignored received fixtures unavailable"
)


def test_received_probe_binds_to_all_19_real_payloads():
    report = reader.verify(PROBE, ARCHIVE)
    assert report["status"] == "probe_capture_crosscheck_passed"
    assert report["pair_states"] == {"not_published": 19}
    assert report["historical_exception_identified"] is False


@pytest.mark.parametrize("fault", ["digest", "duplicate", "manifest", "writes"])
def test_tampered_probe_is_rejected_before_acceptance(tmp_path, fault):
    value = json.loads(PROBE.read_text())
    if fault == "digest":
        value["pairs"][0]["local_sha256"] = "a" * 64
    elif fault == "duplicate":
        value["pairs"][1] = value["pairs"][0]
    elif fault == "manifest":
        value["manifest_readback"]["local_sha256"] = "a" * 64
    else:
        value["drive_object_writes"] = 1
    path = tmp_path / "probe.json"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        reader.verify(path, ARCHIVE)
