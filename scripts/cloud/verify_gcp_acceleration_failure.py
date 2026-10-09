"""Offline, bounded forensic readback; no network, raw downloads or cloud changes."""

import argparse
import csv
import io
import json
import math
import re
import sys
import tempfile
import zipfile
from pathlib import Path

import collect_gcp_acceleration_failure as capture
from diagnose_gcp_production_manifest import verify_package

ROOT = Path(__file__).resolve().parents[2]


def require(ok, label):
    if not ok:
        raise ValueError(label)


def archive_contents(source):
    require(0 < source.stat().st_size < capture.MAX_TOTAL, "Archive byte bound")
    with zipfile.ZipFile(source) as archive:
        infos = archive.infolist()
        names = archive.namelist()
        require(len(names) <= 2000 and len(names) == len(set(names)), "Archive member count")
        require(sum(i.file_size for i in infos) < capture.MAX_TOTAL, "Expanded byte bound")
        require(archive.testzip() is None, "Archive CRC")
        require(
            all(
                name
                in {
                    "capture_manifest.json",
                    "progress.json",
                    "original_manifest.json",
                    "controller_manifest.json",
                    "manifest.zip",
                    "resource_samples.csv",
                    "launcher_filtered.log",
                }
                or re.fullmatch(
                    r"tasks/[a-f0-9]{64}/(?:pair.zip|task_metrics.json|native/[A-Za-z0-9_.]+)", name
                )
                or re.fullmatch(r"days/20\d{2}-\d{2}-\d{2}.zip", name)
                for name in names
            ),
            "Archive member boundary",
        )
        report = json.loads(archive.read("capture_manifest.json"))
        require(
            report["protocol"] == "gcp_acceleration_failure_evidence_v1"
            and report["credentials_read"] is False
            and report["source_raw_files_included"] is False
            and report["network_requests"] == report["production_writes"] == 0,
            "Capture protocol",
        )
        require(set(names) == {"capture_manifest.json", *report["files"]}, "Capture population")
        data = {name: archive.read(name) for name in report["files"]}
        require(
            all(capture.sha(value) == report["files"][name] for name, value in data.items()),
            "Capture content SHA",
        )
    require(
        capture.sha(data["original_manifest.json"]) == capture.SCOPE
        and capture.sha(data["controller_manifest.json"]) == capture.CONTROLLER,
        "Frozen package identities",
    )
    return report, data


def telemetry(data):
    rows = list(csv.DictReader(io.StringIO(data.decode())))
    require(0 < len(rows) < 20000, "Telemetry population")
    require(
        all(
            all(
                value == "" or math.isfinite(float(value)) and float(value) >= 0
                for key, value in row.items()
                if key not in {"arm", "phase"}
            )
            and (row["cpu_busy_pct"] == "" or 0 <= float(row["cpu_busy_pct"]) <= 100)
            for row in rows
        ),
        "Telemetry numbers",
    )
    return {
        "samples": len(rows),
        "last_sample_seconds": float(rows[-1]["seconds"]),
        "min_disk_free_bytes": min(int(r["disk_free_bytes"]) for r in rows),
        "min_mem_available_bytes": min(int(r["mem_available_bytes"]) for r in rows),
        "peak_process_tree_rss_bytes": max(int(r["process_tree_rss_bytes"]) for r in rows),
        "sampled_reserve_breach": any(
            int(r["disk_free_bytes"]) < 4 * 2**30 or int(r["mem_available_bytes"]) < 4 * 2**30
            for r in rows
        ),
        "limitation": "Sampled reserves do not prove every instant or child address-space limit",
    }


def verify(source, output):
    report, data = archive_contents(source)
    saved = capture.state(data["progress.json"])
    require(report["failed_month"] == saved["failed_month"], "Failed month identity")
    original = ROOT / "outputs/gcp_production/package"
    verify_package(original)
    sys.path.insert(0, str(original))
    import gcp_production_support as support
    import run_gcp_production as runner

    output.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        work = Path(temporary)
        manifest = work / "manifest.zip"
        manifest.write_bytes(data["manifest.zip"])
        _, _, catalogue, sources = support.read_scope(original)
        meta = work / "metadata"
        month = saved["failed_month"]
        plan = support.validate_month(
            manifest, month, sources.loc[sources.day.str.startswith(month)], catalogue, meta
        )
        core = work / "science"
        support.template(original, core)
        runner.ensure_root(core, core, meta, plan["pairs"])
        _, native = support.science(core)
        month_sha = capture.sha((meta / "month.json").read_bytes())
        pairs = {p["sample_id"]: p for p in plan["pairs"]}
        for item in report["task_inventory"]:
            identity = item["sample_id"]
            require(identity in pairs, "Retained pair scope")
            pair = pairs[identity]
            name = "tasks/" + capture.sha(identity.encode()) + "/pair.zip"
            row = {
                "sample_id": identity,
                "pair_zip_present": item["pair_zip_present"],
                "raw_sizes_match": all(
                    s["present"] and s["actual_bytes"] == s["expected_bytes"]
                    for s in item["raw_sources"]
                ),
                "native_outputs": item["native_outputs"],
            }
            if item["pair_zip_present"]:
                payload = work / "pair.zip"
                payload.write_bytes(data[name])
                try:
                    native.restore_pair(payload, pair, month_sha, core / "inputs")
                    row["full_native_readback"] = "passed"
                except Exception as error:
                    row["full_native_readback"] = "failed"
                    row["error_type"] = type(error).__name__
                    # Offline inputs contain only public scientific products. Bound
                    # error detail to code guard strings; do not print raw traces.
                    row["guard"] = (
                        str(error)[:160] if isinstance(error, ValueError) else "CLASS_ONLY"
                    )
                print(identity, row["full_native_readback"], flush=True)
            results.append(row)
        value = {
            "protocol": "gcp_acceleration_failure_readback_v1",
            "archive_sha256": capture.sha(source.read_bytes()),
            "archive_bytes": source.stat().st_size,
            "month_manifest_sha256": month_sha,
            "month_scientific_readback": "passed",
            "failed_state": saved,
            "resources": telemetry(data["resource_samples.csv"]),
            "tasks": results,
            "retained_days": report["day_inventory"],
            "exact_original_exception_identified": False,
            "network_requests": 0,
            "VM_modified": False,
            "complete_months_independently_verified_by_this_archive": [],
        }
    (output / "failure_readback.json").write_text(json.dumps(value, indent=2) + "\n")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = verify(args.source, args.output)
    print("Retained ZIPs checked:", sum(t["pair_zip_present"] for t in value["tasks"]))


if __name__ == "__main__":
    main()
