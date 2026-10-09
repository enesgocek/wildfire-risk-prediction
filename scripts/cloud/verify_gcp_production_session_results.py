"""Offline first-session scientific readback. No network, raw processing or VM control."""

import argparse
import concurrent.futures
import hashlib
import importlib
import json
import math
import os
import re
import shutil
import sys
import tarfile
import tempfile
import time
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

from diagnose_gcp_production_manifest import EXPECTED_SCOPE, verify_package

ROOT = Path(__file__).resolve().parents[2]
LIMIT = 500_000_000


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def unpack_snapshot(source, dest):
    """Stream only regular, bounded whitelist members; never tar.extractall."""
    require(0 < source.stat().st_size <= LIMIT, "Snapshot compressed size")
    seen, total = set(), 0
    with tarfile.open(source, "r|gz") as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            require(
                not path.is_absolute()
                and ".." not in path.parts
                and "\\" not in member.name
                and str(path) == member.name,
                "Snapshot path",
            )
            require(member.isfile() or member.isdir(), "Snapshot links/special entries forbidden")
            allowed = (
                member.name == "progress.json"
                or re.fullmatch(r"months/2023-(08|09)/(manifest|month_results)\.zip", member.name)
                or member.name == "months/2023-10/manifest.zip"
                or re.fullmatch(r"months/2023-10/daily_archives/2023-10-\d{2}\.zip", member.name)
                or re.fullmatch(r"days/2023-10-15/inputs/[A-Za-z0-9_.-]+", member.name)
            )
            if member.isdir():
                require(
                    member.name in {"months/2023-10/daily_archives", "days/2023-10-15/inputs"},
                    "Snapshot directory",
                )
                continue
            require(allowed and member.name not in seen, "Unexpected/duplicate snapshot member")
            require(0 < member.size <= 150_000_000, "Snapshot member size")
            seen.add(member.name)
            total += member.size
            require(total <= LIMIT and len(seen) <= 1000, "Snapshot total bound")
            target = dest.joinpath(*path.parts)
            require(target.resolve().is_relative_to(dest.resolve()), "Snapshot destination")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer)
            require(target.stat().st_size == member.size, "Snapshot short read")
    return seen, total


def check_marker(record, day, payload, scope, worker_sha):
    require(record["protocol"] == "verified_job_checkpoint_v1", "Day marker protocol")
    require(record["task_id"] == "day:" + day, "Day marker identity")
    require(
        record["manifest_sha256"] == scope and record["worker_sha256"] == worker_sha,
        "Day marker code/scope",
    )
    require(
        record["negative_label_permitted"] is False
        and record["daily_observation_status"] == "unknown",
        "Day marker policy",
    )
    require(
        record["payload_sha256"] == sha(payload)
        and record["payload_bytes"] == payload.stat().st_size,
        "Nested daily payload SHA/size",
    )
    prefix = f"jobs/{scope}/{hashlib.sha256(('day:' + day).encode()).hexdigest()}"
    require(
        record["payload_key"] == prefix + "/" + record["payload_sha256"] + ".zip",
        "Day marker payload path",
    )


def check_journal(report, pairs, core, compact):
    """Check all daily source journals against independently checked monthly UMMs."""
    expected = {p["sample_id"]: p for p in pairs}
    require(
        len(report["sources"]) == len(expected)
        and {s["sample_id"] for s in report["sources"]} == set(expected),
        "Daily source journal population",
    )
    for saved in report["sources"]:
        pair = expected[saved["sample_id"]]
        audit, estimate = saved["audit"], saved["area_audit"]
        require(
            audit["sample_id"] == pair["sample_id"]
            and audit["negative_label_permitted"] is False
            and estimate["negative_label_permitted"] is False,
            "Source journal identity/policy",
        )
        require(
            set(saved["input_sha256"])
            == {f"{pair['stem']}_{suffix}" for suffix in compact.summer.SUFFIXES}
            and all(re.fullmatch(r"[a-f0-9]{64}", v) for v in saved["input_sha256"].values()),
            "Source journal output population/SHA",
        )
        require(
            estimate["method"] == compact.area.METHOD
            and estimate["sources"]["script_sha256"] == sha(Path(compact.area.__file__))
            and estimate["sources"]["aoi_parts_sha256"]
            == sha(core / "data/interim/grid_aoi_parts.geojson"),
            "Source journal area method/code/geography",
        )
        for name, field in (
            ("scripts/firms/inspect_l2_observation_sample.py", "script_sha256"),
            ("data/aoi/aoi.geojson", "aoi_sha256"),
            ("data/aoi/grid_5km.geojson", "grid_sha256"),
        ):
            require(audit[field] == sha(core / name), "Source journal code/geography")
        for source in pair["sources"]:
            actual = audit["sources"][source["role"]]
            metadata = json.loads((core / pair["metadata"][source["role"]]).read_text())
            entry = metadata["DataGranule"]["ArchiveAndDistributionInformation"][0]
            require(
                actual["bytes"] == source["bytes"]
                and actual["cmr_metadata_sha256"] == source["metadata_sha256"]
                and actual["cmr_checksum"] == entry.get("Checksum")
                and actual["cmr_checksum_verified"] == bool(entry.get("Checksum"))
                and re.fullmatch(r"[a-f0-9]{64}", actual["sha256"]),
                "Source journal CMR lineage",
            )
            interval = actual["cmr_interval"]
            import pandas as pd

            require(
                pd.Timestamp(interval["BeginningDateTime"]) == pd.Timestamp(pair["start_utc"])
                and pd.Timestamp(interval["EndingDateTime"]) == pd.Timestamp(pair["end_utc"]),
                "Source journal interval",
            )
        provenance = estimate["sources"]
        for field, suffix in (
            ("previous_audit_sha256", "audit.json"),
            ("geometry_sha256", "area_estimate.gpkg"),
            ("area_csv_sha256", "area_estimate.csv"),
            ("scan_times_sha256", "scan_times.csv"),
        ):
            require(
                provenance[field] == saved["input_sha256"][f"{pair['stem']}_{suffix}"],
                "Source journal geometry/table SHA references",
            )


def check_day_job(job):
    core, daily, day, pairs, context = job
    support = importlib.import_module("gcp_production_support")
    compact, _ = support.science(core)
    report = compact.validate_day(daily, day, [p["sample_id"] for p in pairs], context)
    check_journal(report, pairs, core, compact)
    return {"day": day, "pairs": len(pairs), "grid_rows": 2899}


def verify(source, package, output, workers=4):
    started, original = time.monotonic(), sha(source)
    spec = verify_package(package)
    sys.path.insert(0, str(package.resolve()))
    support = importlib.import_module("gcp_production_support")
    _, scope, catalogue, sources = support.read_scope(package)
    previous = json.loads(
        (
            ROOT
            / "outputs/gcp_production_diagnosis/session_2026-10-08/session_log_verification.json"
        ).read_text()
    )
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as directory:
        work = Path(directory)
        require(work.resolve().is_relative_to(output.resolve()), "Owned verification scratch")
        snapshot = work / "snapshot"
        snapshot.mkdir()
        names, expanded = unpack_snapshot(source, snapshot)
        progress = json.loads((snapshot / "progress.json").read_text())
        require(
            progress["queue_manifest_sha256"] == scope == EXPECTED_SCOPE
            and progress["status"] == previous["final_progress_status"]
            and progress["pairs_processed_this_invocation"]
            == previous["processed_and_logged_pairs"]
            and progress["pairs_reused_this_invocation"] == 0
            and progress["existing_months"] == previous["existing_completed_months"]
            and progress["negative_label_permitted"] is False
            and progress["daily_observation_status"] == "unknown",
            "Snapshot progress differs from independently checked logs",
        )
        days = progress["days_verified_this_invocation"]
        require(len(days) == 75 and len(set(days)) == 75, "First session day population")
        require(
            dict(Counter(d[:7] for d in days)) == previous["completed_days_by_month"],
            "First session day scope",
        )
        core = work / "science"
        support.template(package, core)
        plans, jobs, receipts, manifests = {}, [], [], []
        expected_names = {"progress.json"}
        for month in ("2023-08", "2023-09", "2023-10"):
            meta_zip = snapshot / "months" / month / "manifest.zip"
            target = core / ("metadata_" + month)
            rows = sources.loc[sources.day.str.startswith(month)]
            plan = support.validate_month(meta_zip, month, rows, catalogue, target)
            month_sha = sha(target / "month.json")
            plans[month] = (plan, month_sha)
            # Pair paths use production_metadata, shared read-only across workers.
            metadata = core / "production_metadata"
            metadata.mkdir(exist_ok=True)
            for path in target.glob("G*.json"):
                dest = metadata / path.name
                require(not dest.exists(), "Duplicate metadata source")
                shutil.copyfile(path, dest)
            expected_names.add(f"months/{month}/manifest.zip")
            manifests.append({"month": month, "sources": len(rows), "sha256": sha(meta_zip)})
            print("Metadata verified:", month, len(rows), flush=True)
            month_days = [d for d in days if d.startswith(month)]
            zip_path = snapshot / "months" / month / "month_results.zip"
            if month in progress["existing_months"]:
                expected_names.add(f"months/{month}/month_results.zip")
                require(month_days == plan["days"], "Completed month missing calendar days")
                with zipfile.ZipFile(zip_path) as archive:
                    required = {"receipt.json", *[d + ".zip" for d in plan["days"]]}
                    require(
                        set(archive.namelist()) == required
                        and len(archive.namelist()) == len(required)
                        and archive.testzip() is None,
                        "Monthly ZIP members/CRC",
                    )
                    require(
                        all(0 < i.file_size <= 150_000_000 for i in archive.infolist())
                        and sum(i.file_size for i in archive.infolist()) <= LIMIT,
                        "Monthly ZIP size bound",
                    )
                    receipt = json.loads(archive.read("receipt.json"))
                    require(
                        receipt["month"] == month
                        and receipt["month_manifest_sha256"] == month_sha
                        and receipt["days"] == plan["days"]
                        and set(receipt["day_records"]) == set(plan["days"])
                        and receipt["unpaired_catalogue_records"]
                        == plan["unpaired_catalogue_records"]
                        and receipt["negative_label_permitted"] is False
                        and receipt["daily_observation_status"] == "unknown",
                        "Monthly receipt lineage/calendar/policy",
                    )
                    for day in month_days:
                        dest = work / (day + ".zip")
                        dest.write_bytes(archive.read(day + ".zip"))
                        check_marker(
                            receipt["day_records"][day],
                            day,
                            dest,
                            scope,
                            spec["files"]["run_gcp_production.py"],
                        )
                receipts.append({"month": month, "days": len(month_days), "sha256": sha(zip_path)})
            for day in month_days:
                pairs = [p for p in plan["pairs"] if p["start_utc"].startswith(day)]
                if month not in progress["existing_months"]:
                    expected_names.add(f"months/{month}/daily_archives/{day}.zip")
                    daily_zip = snapshot / "months" / month / "daily_archives" / (day + ".zip")
                else:
                    daily_zip = work / (day + ".zip")
                dest = work / "days" / day
                dest.mkdir(parents=True)
                with zipfile.ZipFile(daily_zip) as archive:
                    required = {
                        "area.csv",
                        "centers.csv",
                        "scan_grid.csv",
                        "scans.csv",
                        "report.json",
                    }
                    require(
                        set(archive.namelist()) == required
                        and len(archive.namelist()) == 5
                        and archive.testzip() is None,
                        "Daily ZIP member/CRC",
                    )
                    require(
                        all(0 < i.file_size <= 100_000_000 for i in archive.infolist())
                        and sum(i.file_size for i in archive.infolist()) <= 300_000_000,
                        "Daily ZIP size bound",
                    )
                    for name in required:
                        (dest / name).write_bytes(archive.read(name))
                context = {
                    "production_month_manifest_sha256": month_sha,
                    "catalogue_gap_records": [
                        r for r in plan["unpaired_catalogue_records"] if r["day"] == day
                    ],
                }
                jobs.append((core, dest, day, pairs, context))
        checked_days = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
            for result in pool.map(check_day_job, jobs):
                checked_days.append(result)
                print("Independent daily readback passed:", result["day"], flush=True)
        require([r["day"] for r in checked_days] == days, "Daily independent check population")
        _, native = support.science(core)
        plan, month_sha = plans["2023-10"]
        pairs = [p for p in plan["pairs"] if p["start_utc"].startswith("2023-10-15")]
        require(len(pairs) == 10, "Resume-day population")
        inputs = snapshot / "days/2023-10-15/inputs"
        metrics = []
        for pair in pairs:
            for suffix in (*native.SUFFIXES, "checkpoint.json"):
                expected_names.add(f"days/2023-10-15/inputs/{pair['stem']}_{suffix}")
            record = native.checkpoint_read(pair, inputs, month_sha)
            require(record is not None, "Missing saved resume-day checkpoint")
            value = record["metrics"]
            require(
                value["downloaded_payload_bytes"] == sum(s["bytes"] for s in pair["sources"])
                and 0 < value["child_peak_rss_bytes"] < 6 * 2**30
                and math.isfinite(value["elapsed_seconds"])
                and 0 < value["elapsed_seconds"] < 900,
                "Resume-day source/time/memory metrics",
            )
            metrics.append({"sample_id": pair["sample_id"], **value})
            print("Independent saved pair readback passed:", pair["sample_id"], flush=True)
        require(names == expected_names, "Snapshot exact result population")
        require(sha(source) == original, "Received snapshot changed during verification")
        report = {
            "status": "independent_first_session_result_readback_passed",
            "received_sha256": original,
            "received_bytes": source.stat().st_size,
            "expanded_snapshot_bytes": expanded,
            "snapshot_regular_members": len(names),
            "queue_manifest_sha256": scope,
            "metadata_manifests": manifests,
            "completed_months_readback": receipts,
            "independent_day_count": len(checked_days),
            "pairs_in_completed_days": sum(r["pairs"] for r in checked_days),
            "daily_grid_rows": 2899,
            "verified_resume_day": "2023-10-15",
            "verified_saved_resume_pairs": len(metrics),
            "resume_pair_metrics": metrics,
            "negative_label_permitted": False,
            "daily_observation_status": "unknown",
            "raw_downloads": 0,
            "raw_reprocessed": False,
            "live_drive_independently_read_in_this_check": False,
            "completed_day_geometry_union_recomputed": False,
            "resume_pair_geometry_area_checked": True,
            "seconds": time.monotonic() - started,
            "limitations": [
                "Daily numeric/source/temporal checks; full completed-day unions not recomputed",
                "Offline products; remote Drive completion readback is a separate claim",
                "Ten resume-pair metrics from one day; not a whole-period benchmark",
            ],
        }
        (output / "scientific_readback_report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--received",
        type=Path,
        default=ROOT
        / "outputs/gcp_production/received/gcp_production_first_session_results.tar.gz",
    )
    parser.add_argument("--package", type=Path, default=ROOT / "outputs/gcp_production/package")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "outputs/gcp_production_diagnosis/session_2026-10-08/scientific_readback",
    )
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    args = parser.parse_args()
    require(1 <= args.workers <= 4, "Bounded local readback workers")
    result = verify(args.received, args.package, args.out, args.workers)
    print("RESULT", result["status"], "days", result["independent_day_count"])
