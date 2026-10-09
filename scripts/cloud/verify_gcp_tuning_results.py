"""Offline tuning readback; recommendation requires all four arms and stable baselines."""

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import sys
import tempfile
import zipfile
from pathlib import Path

from build_gcp_tuning_bundle import ARMS, DAYS, ROOT, sha
from diagnose_gcp_production_manifest import verify_package
from verify_gcp_production_session_results import check_day_job


def require(ok, label):
    if not ok:
        raise ValueError(label)


def finite(value, label):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, label)
    return value


def members(archive, allowed, total_limit):
    rows = archive.infolist()
    require(len(rows) == len({i.filename for i in rows}), "Duplicate ZIP member")
    require(set(i.filename for i in rows) <= allowed, "Unexpected ZIP member")
    require(
        all(0 < i.file_size <= 150_000_000 and not i.is_dir() for i in rows)
        and sum(i.file_size for i in rows) < total_limit,
        "ZIP size bound",
    )
    require(archive.testzip() is None, "ZIP CRC")


def marker(record, task, scope, worker, payload=None):
    require(
        set(record)
        == {
            "protocol",
            "task_id",
            "manifest_sha256",
            "worker_sha256",
            "payload_sha256",
            "payload_bytes",
            "payload_key",
            "negative_label_permitted",
            "daily_observation_status",
        },
        "Completion schema",
    )
    require(
        record["protocol"] == "verified_job_checkpoint_v1"
        and record["task_id"] == task
        and record["manifest_sha256"] == scope
        and record["worker_sha256"] == worker
        and record["negative_label_permitted"] is False
        and record["daily_observation_status"] == "unknown",
        "Completion identity/policy",
    )
    import re

    checksum = record["payload_sha256"]
    require(isinstance(checksum, str) and re.fullmatch(r"[a-f0-9]{64}", checksum), "Completion SHA")
    prefix = f"jobs/{scope}/{hashlib.sha256(task.encode()).hexdigest()}"
    require(record["payload_key"] == f"{prefix}/{checksum}.zip", "Completion payload path")
    require(
        type(record["payload_bytes"]) is int and 0 < record["payload_bytes"] < 150_000_000,
        "Completion payload bytes",
    )
    if payload is not None:
        require(
            sha(payload) == checksum and len(payload) == record["payload_bytes"],
            "Daily payload readback",
        )


def decision(arms, rows):
    """Speed, repeatability and reserves matter; higher RAM/CPU alone is not success."""
    require([(a["arm"], a["workers"]) for a in arms] == [tuple(a) for a in ARMS], "Profile order")
    resource_readback = {}
    for arm in arms:
        finite(arm["wall_seconds"], "Profile timing")
        require(
            arm["wall_seconds"] > 0 and arm["pair_count"] == 28 and arm["day_count"] == 3,
            "Complete matched profile",
        )
        samples = [r for r in rows if r["arm"] == arm["arm"] and r["cpu_busy_pct"] != ""]
        require(len(samples) >= 5, "Insufficient resource samples")
        for row in samples:
            require(
                all(math.isfinite(float(row[key])) for key in row if key not in ("arm", "phase")),
                "Invalid telemetry value",
            )
            require(
                0 <= float(row["cpu_busy_pct"]) <= 100 and float(row["cpu_iowait_pct"]) >= 0,
                "CPU telemetry range",
            )
            require(
                float(row["mem_available_bytes"]) >= 4 * 2**30
                and float(row["disk_free_bytes"]) >= 4 * 2**30,
                "Resource reserve breached",
            )
        resource_readback[arm["arm"]] = {
            "samples": len(samples),
            "mean_cpu_busy_pct": statistics.mean(float(r["cpu_busy_pct"]) for r in samples),
            "mean_cpu_iowait_pct": statistics.mean(float(r["cpu_iowait_pct"]) for r in samples),
            "mean_cpu_steal_pct": statistics.mean(float(r["cpu_steal_pct"]) for r in samples),
            "peak_sampled_process_tree_rss_bytes": max(
                float(r["process_tree_rss_bytes"]) for r in samples
            ),
            "min_mem_available_bytes": min(float(r["mem_available_bytes"]) for r in samples),
            "min_disk_free_bytes": min(float(r["disk_free_bytes"]) for r in samples),
        }
    baseline = statistics.mean([arms[0]["wall_seconds"], arms[-1]["wall_seconds"]])
    ratio = arms[-1]["wall_seconds"] / arms[0]["wall_seconds"]
    stable = 0.8 <= ratio <= 1.25
    speedups = {a["arm"]: baseline / a["wall_seconds"] for a in arms[1:3]}
    candidates = [
        a
        for a in arms[1:3]
        if stable
        and max(arms[0]["wall_seconds"], arms[-1]["wall_seconds"]) / a["wall_seconds"] >= 1.15
        and min(arms[0]["wall_seconds"], arms[-1]["wall_seconds"]) / a["wall_seconds"] >= 1.15
    ]
    best = min(candidates, key=lambda a: a["wall_seconds"], default=None)
    # Prefer fewer workers when the difference is within 5% of the best measured result.
    if best:
        best = min(
            (a for a in candidates if a["wall_seconds"] <= best["wall_seconds"] * 1.05),
            key=lambda a: a["workers"],
        )
    return {
        "baseline_repeat_ratio": ratio,
        "baseline_stable": stable,
        "speedup_vs_mean_four": speedups,
        "candidate_workers_for_next_validated_runner": best["workers"] if best else None,
        "deployment_automatic": False,
        "resource_readback": resource_readback,
        "interpretation": "candidate_needs_production_runner_validation"
        if best
        else "no_reliable_gain_or_unstable_baseline",
    }


def compare_tables(current, baseline):
    import pandas as pd

    for name in ("area.csv", "centers.csv", "scan_grid.csv", "scans.csv"):
        actual, expected = pd.read_csv(current / name), pd.read_csv(baseline / name)
        try:
            pd.testing.assert_frame_equal(
                actual, expected, check_exact=False, rtol=1e-10, atol=1e-4, check_dtype=False
            )
        except AssertionError:
            raise ValueError("Daily tables differ across tuning profiles") from None


def verify(source, package, output):
    require(0 < source.stat().st_size < 150_000_000, "Result archive size")
    with zipfile.ZipFile(package) as prepared:
        manifest_bytes = prepared.read("tuning_manifest.json")
        spec = json.loads(manifest_bytes)
        for name, expected in spec["files"].items():
            require(sha(prepared.read(name)) == expected, "Prepared package SHA")
        plan_bytes = prepared.read("tuning_plan.json")
        metadata_bytes = prepared.read("month_manifest.zip")
    scope, worker = sha(manifest_bytes), spec["files"]["run_gcp_tuning.py"]
    allowed = {
        "result_summary.json",
        "resource_samples.csv",
        "tuning_manifest.json",
        "tuning_plan.json",
        "month_manifest.zip",
    }
    allowed |= {
        f"{arm}/{name}"
        for arm, _ in ARMS
        for name in ["arm_summary.json", *(day + ".zip" for day in DAYS)]
    }
    with zipfile.ZipFile(source) as archive:
        members(archive, allowed, 300_000_000)
        require(all(n in archive.namelist() for n in allowed if "/" not in n), "Result essentials")
        for name, expected in (
            ("tuning_manifest.json", manifest_bytes),
            ("tuning_plan.json", plan_bytes),
            ("month_manifest.zip", metadata_bytes),
        ):
            require(archive.read(name) == expected, "Result scope changed")
        summary = json.loads(archive.read("result_summary.json"))
        require(
            summary["tuning_scope_sha256"] == scope
            and summary["original_production_scope_sha256"]
            == spec["original_production_scope_sha256"]
            and summary["negative_label_permitted"] is False
            and summary["daily_observation_status"] == "unknown"
            and summary["production_months_added"] == 0,
            "Result scope/policy",
        )
        if summary["status"] != "all_profiles_completed":
            result = {
                "status": "partial_test_no_speed_recommendation",
                "completed_profiles": [a["arm"] for a in summary["arms"]],
            }
        else:
            require(set(archive.namelist()) == allowed, "Full profile result population")
            require(
                summary["production_progress_unchanged"] is True
                and summary["peak_sampled_resource_limit_hit"] is False,
                "Production/resource guard",
            )
            rows = list(csv.DictReader(io.StringIO(archive.read("resource_samples.csv").decode())))
            result = decision(summary["arms"], rows)
            original = ROOT / "outputs/gcp_production/package"
            verify_package(original)
            sys.path.insert(0, str(original.resolve()))
            import gcp_production_support as support

            _, _, catalogue, sources = support.read_scope(original)
            output.mkdir(parents=True, exist_ok=True)
            approved = json.loads(plan_bytes)
            with tempfile.TemporaryDirectory(dir=output) as directory:
                work = Path(directory)
                manifest = work / "manifest.zip"
                manifest.write_bytes(metadata_bytes)
                meta = work / "metadata"
                month = support.validate_month(
                    manifest,
                    "2023-10",
                    sources.loc[sources.day.str.startswith("2023-10")],
                    catalogue,
                    meta,
                )
                require(
                    sha((meta / "month.json").read_bytes())
                    == spec["production_month_manifest_sha256"],
                    "Scientific month SHA",
                )
                core = work / "core"
                support.template(original, core)
                target_metadata = core / "production_metadata"
                target_metadata.mkdir()
                import shutil

                for path in meta.glob("G*.json"):
                    shutil.copy2(path, target_metadata / path.name)
                selected = {
                    p["sample_id"]: p
                    for p in month["pairs"]
                    if p["sample_id"] in approved["sample_ids"]
                }
                expected_bytes = 0
                for arm in summary["arms"]:
                    label = arm["arm"]
                    require(
                        json.loads(archive.read(f"{label}/arm_summary.json")) == arm,
                        "Arm summary mismatch",
                    )
                    require(
                        len(arm["pairs"]) == 28
                        and {p["sample_id"] for p in arm["pairs"]} == set(selected),
                        "Profile pair population",
                    )
                    for saved in arm["pairs"]:
                        pair = selected[saved["sample_id"]]
                        expected = sum(s["bytes"] for s in pair["sources"])
                        require(
                            saved["metrics"]["downloaded_payload_bytes"] == expected,
                            "Cold pair evidence",
                        )
                        finite(saved["child_wall_seconds"], "Child timing")
                        finite(saved["metrics"]["elapsed_seconds"], "Science timing")
                        expected_bytes += expected
                        marker(saved["completion"], label + ":" + saved["sample_id"], scope, worker)
                    require(
                        {d["day"] for d in arm["days"]} == set(DAYS) and len(arm["days"]) == 3,
                        "Profile day population",
                    )
                    for day in arm["days"]:
                        value = day["day"]
                        payload = archive.read(f"{label}/{value}.zip")
                        marker(day["completion"], label + ":day:" + value, scope, worker, payload)
                        target = work / label / value
                        target.mkdir(parents=True)
                        with zipfile.ZipFile(io.BytesIO(payload)) as daily:
                            names = {
                                "area.csv",
                                "centers.csv",
                                "scan_grid.csv",
                                "scans.csv",
                                "report.json",
                            }
                            members(daily, names, 20_000_000)
                            require(set(daily.namelist()) == names, "Daily file population")
                            for name in names:
                                (target / name).write_bytes(daily.read(name))
                        pairs = [p for p in selected.values() if p["start_utc"].startswith(value)]
                        context = {
                            "production_month_manifest_sha256": spec[
                                "production_month_manifest_sha256"
                            ],
                            "catalogue_gap_records": [
                                r for r in month["unpaired_catalogue_records"] if r["day"] == value
                            ],
                        }
                        check_day_job((core, target, value, pairs, context))
                        journal = json.loads((target / "report.json").read_text())
                        for entry in journal["sources"]:
                            pair = selected[entry["sample_id"]]
                            reference = approved["references"][entry["sample_id"]]
                            require(
                                all(
                                    entry["audit"]["sources"][role]["sha256"] == expected
                                    for role, expected in reference["source_sha256"].items()
                                ),
                                "Raw source reference",
                            )
                            require(
                                all(
                                    entry["input_sha256"][f"{pair['stem']}_{suffix}"] == expected
                                    for suffix, expected in reference["exact_csv_sha256"].items()
                                ),
                                "CSV reference",
                            )
                        if label != "four_before":
                            compare_tables(target, work / "four_before" / value)
                require(
                    expected_bytes
                    == summary["raw_downloaded_bytes"]
                    == spec["nominal_raw_download_bytes"],
                    "Cold download total",
                )
            result.update(
                status="independent_matched_tuning_readback_passed",
                validated_daily_payloads=12,
                raw_reprocessed_locally=False,
                live_drive_readback_in_this_check=False,
            )
    output.mkdir(parents=True, exist_ok=True)
    result.update(received_sha256=sha(source.read_bytes()), tuning_scope_sha256=scope)
    (output / "tuning_readback.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--package", type=Path, default=ROOT / "outputs/gcp_tuning/wildfire_gcp_tuning.zip"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/gcp_tuning/readback")
    arguments = parser.parse_args()
    print(json.dumps(verify(arguments.source, arguments.package, arguments.output), indent=2))
