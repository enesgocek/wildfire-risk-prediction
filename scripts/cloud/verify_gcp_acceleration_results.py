"""Independent matched scientific readback and a pinned production readiness gate."""

import argparse
import csv
import io
import json
import math
import shutil
import statistics
import sys
import tempfile
import zipfile
from pathlib import Path

from build_gcp_tuning_bundle import ORIGINAL_SCOPE, ROOT, encoded, sha
from diagnose_gcp_production_manifest import verify_package
from verify_gcp_production_session_results import check_day_job
from verify_gcp_tuning_results import compare_tables, marker, members, require


def verify(source, package, output):
    require(0 < source.stat().st_size < 150_000_000, "Acceleration archive bound")
    with zipfile.ZipFile(package) as prepared:
        manifest_bytes = prepared.read("acceleration_manifest.json")
        spec = json.loads(manifest_bytes)
        require(
            spec["protocol"] == "gcp_acceleration_controller_v1"
            and spec["training_scope_sha256"] == ORIGINAL_SCOPE
            and spec["negative_label_permitted"] is False
            and spec["daily_observation_status"] == "unknown",
            "Prepared controller scope/policy",
        )
        members(prepared, {"acceleration_manifest.json", *spec["files"]}, 10_000_000)
        require(len(prepared.namelist()) == 9, "Prepared controller population")
        for name, checksum in spec["files"].items():
            require(sha(prepared.read(name)) == checksum, "Acceleration package SHA")
        plan_bytes, metadata_bytes = (
            prepared.read("proof_plan.json"),
            prepared.read("month_manifest.zip"),
        )
    scope, worker = sha(manifest_bytes), spec["files"]["run_gcp_acceleration.py"]
    allowed_profiles = {
        8: [
            ("baseline_before", 8),
            ("pipeline_eight", 8),
            ("pipeline_scaled", 6),
            ("baseline_after", 8),
        ],
        16: [
            ("baseline_before", 8),
            ("pipeline_eight", 8),
            ("pipeline_scaled", 12),
            ("baseline_after", 8),
        ],
        32: [
            ("baseline_before", 8),
            ("pipeline_eight", 8),
            ("pipeline_scaled", 24),
            ("baseline_after", 8),
        ],
    }
    with zipfile.ZipFile(source) as archive:
        essential = {
            "acceleration_manifest.json",
            "proof_plan.json",
            "month_manifest.zip",
            "result_summary.json",
            "resource_samples.csv",
        }
        allowed = essential | {
            f"{label}/{name}"
            for label, _ in allowed_profiles[32]
            for name in ["arm_summary.json", *[d + ".zip" for d in spec["proof_days"]]]
        }
        members(archive, allowed, 300_000_000)
        require(essential <= set(archive.namelist()), "Proof essentials")
        for name, value in (
            ("acceleration_manifest.json", manifest_bytes),
            ("proof_plan.json", plan_bytes),
            ("month_manifest.zip", metadata_bytes),
        ):
            require(archive.read(name) == value, "Proof source changed")
        summary = json.loads(archive.read("result_summary.json"))
        require(
            summary["controller_manifest_sha256"] == scope
            and summary["original_scope_sha256"] == spec["training_scope_sha256"]
            and summary["negative_label_permitted"] is False
            and summary["daily_observation_status"] == "unknown"
            and summary["production_months_added"] == 0,
            "Proof scope/policy",
        )
        require(
            summary["status"] == "all_profiles_completed"
            and summary["production_progress_unchanged"] is True
            and summary["resource_guard_hit"] is False,
            "Complete proof required; partial has no gate",
        )
        require(summary["cpus"] in allowed_profiles, "Measured CPU count")
        arms = summary["arms"]
        require(
            [(a["arm"], a["workers"]) for a in arms] == allowed_profiles[summary["cpus"]]
            and set(archive.namelist()) == allowed,
            "Profile population",
        )
        rows = list(csv.DictReader(io.StringIO(archive.read("resource_samples.csv").decode())))
        resources = {}
        original = ROOT / "outputs/gcp_production/package"
        verify_package(original)
        sys.path.insert(0, str(original.resolve()))
        import gcp_production_support as support

        approved = json.loads(plan_bytes)
        output.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output) as directory:
            work = Path(directory)
            manifest = work / "manifest.zip"
            manifest.write_bytes(metadata_bytes)
            _, _, catalogue, sources = support.read_scope(original)
            meta = work / "metadata"
            plan = support.validate_month(
                manifest,
                "2023-10",
                sources.loc[sources.day.str.startswith("2023-10")],
                catalogue,
                meta,
            )
            require(
                sha((meta / "month.json").read_bytes()) == spec["month_manifest_sha256"],
                "Proof scientific month",
            )
            core = work / "core"
            support.template(original, core)
            (core / "production_metadata").mkdir()
            for path in meta.glob("G*.json"):
                shutil.copy2(path, core / "production_metadata" / path.name)
            selected = {
                p["sample_id"]: p for p in plan["pairs"] if p["sample_id"] in approved["sample_ids"]
            }
            for arm in arms:
                label = arm["arm"]
                require(
                    json.loads(archive.read(f"{label}/arm_summary.json")) == arm,
                    "Profile summary bytes",
                )
                require(
                    arm["pair_count"] == 28
                    and arm["day_count"] == 3
                    and len(arm["pairs"]) == 28
                    and {p["sample_id"] for p in arm["pairs"]} == set(selected)
                    and len(arm["days"]) == 3
                    and {d["day"] for d in arm["days"]} == set(approved["days"]),
                    "Matched pair/day set",
                )
                require(
                    math.isfinite(arm["wall_seconds"]) and arm["wall_seconds"] > 0, "Profile clock"
                )
                expected_reducers = (
                    {8: 1, 16: 2, 32: 4}[summary["cpus"]] if label == "pipeline_scaled" else 1
                )
                require(
                    arm.get("daily_workers", 1) == expected_reducers,
                    "Daily worker profile population",
                )
                telemetry = [r for r in rows if r["arm"] == label and r["cpu_busy_pct"]]
                require(len(telemetry) >= 5, "Telemetry absent")
                for row in telemetry:
                    require(
                        all(
                            math.isfinite(float(v))
                            for k, v in row.items()
                            if k not in ("arm", "phase")
                        ),
                        "Telemetry numeric values",
                    )
                    require(
                        all(
                            0 <= float(row[key]) <= 100
                            for key in ("cpu_busy_pct", "cpu_iowait_pct", "cpu_steal_pct")
                        ),
                        "CPU telemetry range",
                    )
                    require(
                        float(row["mem_available_bytes"]) >= 4 * 2**30
                        and float(row["disk_free_bytes"]) >= 4 * 2**30,
                        "Telemetry resource reserve",
                    )
                resources[label] = {
                    "samples": len(telemetry),
                    "mean_cpu_busy_pct": statistics.mean(
                        float(r["cpu_busy_pct"]) for r in telemetry
                    ),
                    "peak_cpu_busy_pct": max(float(r["cpu_busy_pct"]) for r in telemetry),
                    "peak_process_tree_rss_bytes": max(
                        float(r["process_tree_rss_bytes"]) for r in telemetry
                    ),
                    "min_mem_available_bytes": min(
                        float(r["mem_available_bytes"]) for r in telemetry
                    ),
                    "min_disk_free_bytes": min(float(r["disk_free_bytes"]) for r in telemetry),
                }
                for record in arm["pairs"]:
                    pair = selected[record["sample_id"]]
                    require(
                        record["metrics"]["downloaded_payload_bytes"]
                        == sum(s["bytes"] for s in pair["sources"]),
                        "Cold processing evidence",
                    )
                    marker(record["completion"], label + ":" + record["sample_id"], scope, worker)
                for record in arm["days"]:
                    day = record["day"]
                    data = archive.read(f"{label}/{day}.zip")
                    marker(record["completion"], label + ":day:" + day, scope, worker, data)
                    target = work / label / day
                    target.mkdir(parents=True)
                    names = {"area.csv", "centers.csv", "scan_grid.csv", "scans.csv", "report.json"}
                    with zipfile.ZipFile(io.BytesIO(data)) as daily:
                        members(daily, names, 20_000_000)
                        require(set(daily.namelist()) == names, "Daily payload population")
                        for name in names:
                            (target / name).write_bytes(daily.read(name))
                    pairs = [p for p in selected.values() if p["start_utc"].startswith(day)]
                    context = {
                        "production_month_manifest_sha256": spec["month_manifest_sha256"],
                        "catalogue_gap_records": [
                            r for r in plan["unpaired_catalogue_records"] if r["day"] == day
                        ],
                    }
                    check_day_job((core, target, day, pairs, context))
                    journal = json.loads((target / "report.json").read_text())
                    for saved in journal["sources"]:
                        pair = selected[saved["sample_id"]]
                        reference = approved["references"][saved["sample_id"]]
                        require(
                            all(
                                saved["audit"]["sources"][role]["sha256"] == checksum
                                for role, checksum in reference["source_sha256"].items()
                            ),
                            "Matched raw source",
                        )
                        require(
                            all(
                                saved["input_sha256"][f"{pair['stem']}_{suffix}"] == checksum
                                for suffix, checksum in reference["exact_csv_sha256"].items()
                            ),
                            "Matched native counts/scans",
                        )
                    if label != "baseline_before":
                        compare_tables(target, work / "baseline_before" / day)
        ratio = arms[-1]["wall_seconds"] / arms[0]["wall_seconds"]
        baseline = statistics.mean([arms[0]["wall_seconds"], arms[-1]["wall_seconds"]])
        stable = 0.8 <= ratio <= 1.25
        candidates = [
            a
            for a in arms[1:3]
            if a["workers"] + a["daily_workers"] + 1 <= summary["cpus"]
            and min(arms[0]["wall_seconds"], arms[-1]["wall_seconds"]) / a["wall_seconds"] >= 1.15
        ]
        require(stable and candidates, "Unstable baseline or no reliable acceleration candidate")
        best = min(candidates, key=lambda a: a["wall_seconds"])
        best = min(
            (a for a in candidates if a["wall_seconds"] <= best["wall_seconds"] * 1.05),
            key=lambda a: a["workers"],
        )
        old = json.loads((ROOT / "outputs/gcp_tuning/readback/comparison.json").read_text())[1]
        gate = {
            "protocol": "gcp_acceleration_ready_v1",
            "status": "independent_acceleration_readback_passed",
            "controller_manifest_sha256": scope,
            "proof_archive_sha256": sha(source.read_bytes()),
            "cpus": summary["cpus"],
            "pair_slots": best["workers"],
            "daily_slots": best["daily_workers"],
            "selected_profile": best["arm"],
            "baseline_stable": stable,
            "baseline_repeat_ratio": ratio,
            "speedup_vs_same_hardware_baseline": baseline / best["wall_seconds"],
            "speedup_vs_prior_e2_eight": old["wall_seconds"] / best["wall_seconds"],
            "verified_daily_payloads": 12,
            "resource_readback": resources,
            "raw_download_bytes": spec["raw_bytes_four_profiles"],
            "negative_label_permitted": False,
            "daily_observation_status": "unknown",
            "limits": "Three fixed days; no all-year speed guarantee",
        }
    destination = output / "production_readiness.json"
    destination.write_bytes(encoded(gate))
    result = {**gate, "gate_file": str(destination), "gate_sha256": sha(destination.read_bytes())}
    (output / "acceleration_readback.json").write_bytes(encoded(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--package",
        type=Path,
        default=ROOT / "outputs/gcp_acceleration/wildfire_gcp_acceleration.zip",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/gcp_acceleration/readback")
    args = parser.parse_args()
    print(json.dumps(verify(args.source, args.package, args.output), indent=2))
