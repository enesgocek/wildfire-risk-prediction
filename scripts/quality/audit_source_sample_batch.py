"""Offline native-point review of all seven completed frozen-source downloads."""

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from prepare_marmaris_native_pair import module, write

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
QUEUE = BASE / "source_review_queue_v1/20261119T141303Z_9c1e2156/queue_plan.json"
DOWNLOAD = BASE / "source_review_queue_v1/20261119T173352Z_c8a31d03/readback.json"
FIRST = BASE / "source_sample_point_v1/20261119T140051Z_000dc2bf/readback.json"
PINS = {
    QUEUE: "dc6f2e51af888f7650a6a3652d50286f5c6d3b06becc91590a2929f246f27f01",
    DOWNLOAD: "121eb4daadcb2edcd2e606cb47a5ed6a310925f3e7fbd916d85a98cc1d084ebd",
    FIRST: "9970de0d18f2717c0f72294e35a61938f55af452d034d3f341e2ecc10edc7efa",
}


def verify_result(path, archive_row, plan_path=None, probe_path=None):
    require(
        path.resolve().is_relative_to(BASE / "source_sample_point_v1"), "Contained point result"
    )
    result = json.loads(path.read_text(encoding="utf-8"))
    require(
        result["archive_row"] == archive_row
        and result["scope"] == "one_frozen_source_row_single_swath_diagnostic_only"
        and result["gate"] == specification()
        and result["L_memberships_created"] == 0
        and result["labels_created"] is False
        and result["model_trained"] is False
        and result["final_merge_performed"] is False
        and result["network_used"] is False,
        "Diagnostic-only result with unchanged scientific gates",
    )
    for key in ("input_sha256", "code_sha256"):
        require(all(digest(ROOT / n) == h for n, h in result[key].items()), "Exact point closure")
    for parent in (plan_path, probe_path):
        if parent is not None:
            require(
                result["input_sha256"][parent.relative_to(ROOT).as_posix()] == digest(parent),
                "Exact requested native pair and probe",
            )
    return result


def main():
    require(all(digest(p) == h for p, h in PINS.items()), "Frozen queue, download and first point")
    receipt = json.loads((DOWNLOAD.parent / "completion_readback.json").read_text(encoding="utf-8"))
    require(receipt["report_sha256"] == digest(DOWNLOAD), "Download completion receipt")
    downloaded = json.loads(DOWNLOAD.read_text(encoding="utf-8"))
    queue_runner = module("batch_queue", "scripts/firms/run_source_review_queue.py")
    runner = queue_runner.runner_module()
    queue = queue_runner.load_plan(QUEUE, runner)
    probes = {u["archive_row"]: u for u in downloaded["units"]}
    require(
        downloaded["status"] == "seven_pairs_bytes_headers_complete_not_spatial_acceptance"
        and downloaded["plan_sha256"] == digest(QUEUE)
        and len(probes) == len(downloaded["units"]) == 7
        and set(probes) == queue_runner.ROWS,
        "Seven exact completed source rows",
    )
    for unit in queue["units"]:
        probe = probes[unit["archive_row"]]
        require(digest(ROOT / probe["probe"]) == probe["sha256"], "Pinned download probe")
        require(
            queue_runner.completed_probe(unit, runner)
            == {"probe": probe["probe"], "sha256": probe["sha256"]},
            "Native bytes and completion verified",
        )
    verify_result(FIRST, "WF1206")
    out = (
        BASE
        / "source_sample_batch_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    print("Offline batch:", out.relative_to(ROOT).as_posix(), flush=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("EARTHDATA_")}
    script = ROOT / "scripts/quality/audit_source_sample_point.py"

    def audit(unit):
        row = unit["archive_row"]
        plan_path = ROOT / unit["plan"]
        probe_path = ROOT / probes[row]["probe"]
        # Reuse exact input/code matches; mismatches stop without replacing evidence.
        for path in sorted((BASE / "source_sample_point_v1").glob("*/readback.json"), reverse=True):
            candidate = json.loads(path.read_text(encoding="utf-8"))
            if candidate.get("archive_row") == row:
                verify_result(path, row, plan_path, probe_path)
                return {
                    "archive_row": row,
                    "report": path.relative_to(ROOT).as_posix(),
                    "sha256": digest(path),
                    "reused": True,
                }
        command = [
            sys.executable,
            str(script),
            "--archive-row",
            row,
            "--plan",
            str(plan_path),
            "--probe",
            str(probe_path),
        ]
        child = subprocess.run(
            command,
            env=env,
            capture_output=True,
            timeout=600,
            check=False,
            text=True,
            encoding="utf-8",
        )
        require(child.returncode == 0, "Offline point worker failed; existing outputs retained")
        first_line = child.stdout.splitlines()[0].split()
        require(len(first_line) == 2, "Worker result identity")
        path = ROOT / first_line[0]
        require(digest(path) == first_line[1], "Point worker report bytes")
        verify_result(path, row, plan_path, probe_path)
        return {
            "archive_row": row,
            "report": path.relative_to(ROOT).as_posix(),
            "sha256": digest(path),
            "reused": False,
        }

    results, failures = [], []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(audit, u): u["archive_row"] for u in queue["units"]}
        for future in as_completed(futures):
            row = futures[future]
            try:
                results.append(future.result())
                print("Point reviewed:", row, flush=True)
            except Exception as error:
                failures.append({"archive_row": row, "error_type": type(error).__name__})
                print("Point unresolved:", row, type(error).__name__, flush=True)
            # Mutable progress only; never a scientific acceptance receipt.
            (out / "progress.json").write_text(
                json.dumps({"results": results, "failures": failures}, indent=2), encoding="utf-8"
            )
    result = {
        "status": "seven_point_reviews_complete" if not failures else "incomplete_outputs_retained",
        "results": sorted(results, key=lambda r: r["archive_row"]),
        "failures": failures,
        "first_review": {"report": FIRST.relative_to(ROOT).as_posix(), "sha256": digest(FIRST)},
        "source_rows_retained": 10,
        "metadata_untransportable_rows": ["WF1342", "WF1556"],
        "local_workers": 2,
        "per_worker_timeout_seconds": 600,
        "raw_downloads_started": 0,
        "new_L_memberships": 0,
        "labels_created": False,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    write(out / "readback.json", result)
    write(out / "completion_readback.json", {"report_sha256": digest(out / "readback.json")})
    print("Result:", (out / "readback.json").relative_to(ROOT).as_posix(), flush=True)
    require(not failures, "One or more point reviews incomplete; preserve all source rows")


if __name__ == "__main__":
    main()
