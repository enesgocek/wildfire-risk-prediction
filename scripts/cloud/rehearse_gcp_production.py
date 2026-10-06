"""Offline six-real-pair recovery and daily union rehearsal. No cloud or raw requests."""

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import gcp_production_support as support
import pandas as pd
import run_gcp_production as runner
from verified_job_store import RehearsalFileStore, VerifiedJobStore, require

ROOT = Path(__file__).resolve().parents[2]


def child(root, payload, plan, sample):
    value = json.loads(plan.read_text())
    pair = next(p for p in value["pairs"] if p["sample_id"] == sample)
    native, check = runner.pair_checker(root, pair, support.digest(plan), root / "inputs")
    check(payload)
    require(
        native.checkpoint_read(pair, root / "inputs", support.digest(plan)) is not None,
        "Parallel restore",
    )


def rehearse(package):
    spec, scope_sha, _, _ = support.read_scope(package)
    out = ROOT / "outputs/gcp_production_rehearsal"
    out.mkdir(exist_ok=True)
    received = ROOT / "outputs/cloud_summer/received/l2_summer_results.zip"
    old_day = ROOT / "outputs/cloud_month/received/l2_month_2023_07_results.zip"
    identities = {str(p): support.digest(p) for p in (received, old_day)}
    started = time.monotonic()
    with tempfile.TemporaryDirectory(dir=out) as temporary:
        work = Path(temporary)
        core = work / "core"
        support.template(package, core)
        old = json.loads((core / "summer/manifest.json").read_text())
        plan = {"pairs": old["pairs"], "unpaired_catalogue_records": []}
        plan_path = work / "month.json"
        support.atomic_json(plan_path, plan)
        month_sha = support.digest(plan_path)
        dayroot = work / "day"
        shutil.copytree(core, dayroot)
        backend = RehearsalFileStore(work / "separate_store")
        store = VerifiedJobStore(
            backend, scope_sha, spec["files"]["run_gcp_production.py"], 100_000_000
        )
        payloads, records = {}, {}
        checks = 0
        with zipfile.ZipFile(received) as archive:
            for pair in plan["pairs"]:
                native, actual_check = runner.pair_checker(
                    dayroot, pair, month_sha, dayroot / "inputs"
                )
                names = runner.pair_names(pair, native)
                path = work / (pair["stem"] + ".zip")
                with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as target:
                    for name in sorted(names):
                        data = archive.read(name)
                        if name.endswith("_checkpoint.json"):
                            record = json.loads(data)
                            # Change enclosing lineage only; preserve all nine science products.
                            record["manifest_sha256"] = month_sha
                            data = support.json_bytes(record)
                        target.writestr(name, data)

                def check(path, actual_check=actual_check):
                    nonlocal checks
                    actual_check(path)
                    checks += 1

                if not payloads:
                    original = backend.create

                    def interrupted(key, data, original=original):
                        if key.endswith("completed.json"):
                            raise OSError("Injected before completion marker")
                        return original(key, data)

                    backend.create = interrupted
                    try:
                        store.save(pair["sample_id"], path, names, check)
                        raise AssertionError("Interruption missing")
                    except OSError:
                        pass
                    require(
                        store.restore(pair["sample_id"], names, check) is None,
                        "Orphan must not complete",
                    )
                    backend.create = original
                    store = VerifiedJobStore(backend, scope_sha, store.worker_sha, 100_000_000)
                records[pair["sample_id"]] = store.save(pair["sample_id"], path, names, check)
                payloads[pair["sample_id"]] = path
                print("Rehearsal pair committed:", pair["sample_id"], flush=True)

        # Four isolated Python processes exercise real scientific restore; no download speed claim.
        def parallel_restore(pair):
            target = work / ("isolated_" + hashlib.sha256(pair["sample_id"].encode()).hexdigest())
            shutil.copytree(core, target)
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__)),
                    "--child-root",
                    str(target),
                    "--payload",
                    str(payloads[pair["sample_id"]]),
                    "--plan",
                    str(plan_path),
                    "--sample",
                    pair["sample_id"],
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )
            require(
                result.returncode == 0,
                "Isolated real scientific restore failed: " + result.stderr[-1000:],
            )
            return True

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            restored = list(pool.map(parallel_restore, plan["pairs"]))
        print("Six isolated process restores passed", flush=True)
        args = argparse.Namespace(root=dayroot, plan=plan_path, day="2023-07-16")
        runner.child_day(args)
        lineage = {"production_month_manifest_sha256": month_sha, "catalogue_gap_records": []}
        compact, _ = support.science(dayroot)
        restored_report = runner.restore_daily(
            dayroot / "day.zip", dayroot, args.day, plan["pairs"], lineage
        )
        compared, numeric_differences = [], {}
        with zipfile.ZipFile(old_day) as archive:
            for name in compact.NAMES[:-1]:
                known = work / ("known_" + name)
                known.write_bytes(archive.read(args.day + "/" + name))
                left = pd.read_csv(known, dtype={"pair_key": str})
                right = pd.read_csv(dayroot / "daily" / name, dtype={"pair_key": str})
                keys = (
                    ["grid_id"]
                    if name in {"area.csv", "centers.csv"}
                    else ["sensor", "pair_key", "scan_index"]
                    + (["grid_id"] if name == "scan_grid.csv" else [])
                )
                left = left.sort_values(keys).reset_index(drop=True)
                right = right.sort_values(keys).reset_index(drop=True)
                require(
                    list(left.columns) == list(right.columns) and len(left) == len(right),
                    "Daily table dimensions",
                )
                deltas = {}
                for column in left.columns:
                    if name == "area.csv" and pd.api.types.is_float_dtype(left[column]):
                        tolerance = 1e-4 if column.endswith("_m2") else 1e-12
                        pd.testing.assert_series_equal(
                            left[column],
                            right[column],
                            check_exact=False,
                            rtol=1e-10,
                            atol=tolerance,
                        )
                        deltas[column] = float((left[column] - right[column]).abs().max())
                    else:
                        pd.testing.assert_series_equal(
                            left[column], right[column], check_exact=True
                        )
                numeric_differences[name] = deltas
                compared.append(name)
        daily_checks = 0

        def daily_check(path):
            nonlocal daily_checks
            runner.restore_daily(path, dayroot, args.day, plan["pairs"], lineage)
            daily_checks += 1

        day_record = store.save(
            "day:" + args.day, dayroot / "day.zip", set(compact.NAMES), daily_check
        )
        restarted = VerifiedJobStore(backend, scope_sha, store.worker_sha, 100_000_000)
        require(
            restarted.restore("day:" + args.day, set(compact.NAMES), daily_check) == day_record,
            "Committed daily restore",
        )
        # Membership and changed lineage must fail before being accepted as a day.
        rejected = False
        try:
            runner.restore_daily(
                dayroot / "day.zip", dayroot, args.day, plan["pairs"][:-1], lineage
            )
        except ValueError:
            rejected = True
        require(rejected, "Missing nominal pair must be rejected")
        require(
            all(support.digest(Path(p)) == checksum for p, checksum in identities.items()),
            "Old received archives changed",
        )
        report = {
            "status": "offline_six_real_pairs_and_daily_union_passed",
            "queue_manifest_sha256": scope_sha,
            "pairs": len(records),
            "pair_scientific_readbacks": checks,
            "isolated_process_restores": sum(restored),
            "parallel_process_limit": 4,
            "daily_scientific_readbacks": daily_checks,
            "daily_tables_compared": compared,
            "non_area_columns_exact": True,
            "area_max_absolute_differences": numeric_differences["area.csv"],
            "area_tolerance_m2": 0.0001,
            "area_fraction_tolerance": 1e-12,
            "area_fraction_relative_tolerance": 1e-10,
            "day": args.day,
            "grid_rows": restored_report.get("grid_rows", 2899),
            "interruption_before_marker": True,
            "uncommitted_not_reused": True,
            "incomplete_pair_set_rejected": True,
            "old_archives_unchanged": True,
            "raw_downloads": 0,
            "four_worker_raw_speedup_proven": False,
            "live_drive_or_vm_access": False,
            "negative_label_permitted": False,
            "seconds": time.monotonic() - started,
        }
        support.atomic_json(out / "report.json", report)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path)
    parser.add_argument("--child-root", type=Path)
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--sample")
    args = parser.parse_args()
    if args.child_root:
        child(args.child_root, args.payload, args.plan, args.sample)
    else:
        rehearse(args.package)
