"""Persist actual Node integration checks for an independently audited offline prototype."""

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    folder, audit = args.prototype.resolve(), args.audit.resolve()
    require(
        folder.parent == (BASE / "historical_research_prototype_v1").resolve()
        and audit.parent == (BASE / "historical_research_prototype_audit_v1").resolve(),
        "Workspace local prototype and separate audit",
    )
    ar = json.loads((audit / "readback.json").read_bytes())
    require(
        ar["prototype"] == folder.relative_to(ROOT).as_posix()
        and ar["memberships_verified"] == 8956
        and ar["score_values_verified"] == 241812,
        "Full audited prototype payload",
    )
    pins = {ROOT / p: sha for p, sha in ar["input_sha256"].items()}
    pins[audit / "readback.json"] = digest(audit / "readback.json")
    test = ROOT / "tests/js/research_prototype.test.cjs"
    pins[test] = digest(test)
    require(
        all(digest(p) == sha for p, sha in pins.items()), "Current audited files and test source"
    )
    node = shutil.which("node")
    require(node is not None, "Existing Node installation only")
    result = subprocess.run(
        [node, "--test", "--test-reporter=tap", str(test)],
        cwd=ROOT,
        env=os.environ | {"RESEARCH_PAYLOAD_PATH": str(folder / "review_data.js")},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    require(
        result.returncode == 0
        and re.search(r"# tests 7\b", result.stdout)
        and re.search(r"# pass 7\b", result.stdout)
        and re.search(r"# fail 0\b", result.stdout),
        "Seven actual logic and frozen-payload tests passed",
    )
    out = (
        BASE
        / "historical_research_prototype_logic_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    (out / "node_tests.tap").write_text(result.stdout, encoding="utf-8")
    require(
        all(digest(p) == sha for p, sha in pins.items()),
        "Prototype unchanged through integration checks",
    )
    body = {
        "status": "audited_offline_prototype_logic_and_actual_payload_checks_complete",
        "prototype": folder.relative_to(ROOT).as_posix(),
        "actual_Node_tests_passed": 7,
        "browser_render_or_manual_usability_verified": False,
        "verification_limit": "source_data_static_DOM_and_Node_logic_checked_not_an_actual_browser",
        "new_model_or_prediction_calls": 0,
        "fire_risk_validated": False,
        "final_merge_performed": False,
        "producer_sha256": digest(Path(__file__)),
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "artifact_sha256": {"node_tests.tap": digest(out / "node_tests.tap")},
    }
    path = out / "readback.json"
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)


if __name__ == "__main__":
    main()
