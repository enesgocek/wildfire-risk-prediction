"""Independent local readback of compact month results; raw/remote Drive unclaimed."""

import argparse
import hashlib
import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "month_verify_worker", Path(__file__).with_name("run_l2_month.py")
)
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)
require, digest = worker.require, worker.digest


def check_sources(report, pairs, manifest_sha, metadata):
    expected = {p["sample_id"]: p for p in pairs}
    require(len(report["sources"]) == len(expected), "Daily source count")
    require({s["sample_id"] for s in report["sources"]} == set(expected), "Daily source identities")
    for saved in report["sources"]:
        pair = expected[saved["sample_id"]]
        audit, estimate = saved["audit"], saved["area_audit"]
        require(
            audit["sample_id"] == pair["sample_id"] and audit["negative_label_permitted"] is False,
            "Native audit policy/identity",
        )
        require(
            estimate["negative_label_permitted"] is False
            and estimate["method"] == worker.compact.area.METHOD,
            "Area audit policy/method",
        )
        require(
            set(saved["input_sha256"]) == {f"{pair['stem']}_{s}" for s in worker.summer.SUFFIXES},
            "Pair journal output references",
        )
        require(
            all(
                len(s) == 64 and all(c in "0123456789abcdef" for c in s)
                for s in saved["input_sha256"].values()
            ),
            "Invalid journal output SHA",
        )
        for name, field in (
            ("scripts/firms/inspect_l2_observation_sample.py", "script_sha256"),
            ("data/aoi/aoi.geojson", "aoi_sha256"),
            ("data/aoi/grid_5km.geojson", "grid_sha256"),
        ):
            require(audit[field] == digest(ROOT / name), "Native code/geography differs")
        for source in pair["sources"]:
            native = audit["sources"][source["role"]]
            entry = metadata[pair["metadata"][source["role"]]]["DataGranule"][
                "ArchiveAndDistributionInformation"
            ][0]
            require(
                native["cmr_checksum"] == entry.get("Checksum")
                and native["cmr_checksum_verified"] == bool(entry.get("Checksum")),
                "Native CMR checksum status differs",
            )
            require(
                native["bytes"] == source["bytes"]
                and native["cmr_metadata_sha256"] == source["metadata_sha256"],
                "Native source metadata differs",
            )
            require(len(native["sha256"]) == 64, "Native SHA absent")
            interval = native["cmr_interval"]
            require(
                pd.Timestamp(interval["BeginningDateTime"]) == pd.Timestamp(pair["start_utc"])
                and pd.Timestamp(interval["EndingDateTime"]) == pd.Timestamp(pair["end_utc"]),
                "Source interval changed",
            )
        provenance = estimate["sources"]
        require(
            provenance["script_sha256"] == digest(Path(worker.compact.area.__file__))
            and provenance["previous_audit_sha256"]
            == saved["input_sha256"][f"{pair['stem']}_audit.json"],
            "Area journal lineage",
        )
        for field, suffix in (
            ("geometry_sha256", "area_estimate.gpkg"),
            ("area_csv_sha256", "area_estimate.csv"),
            ("scan_times_sha256", "scan_times.csv"),
        ):
            require(
                provenance[field] == saved["input_sha256"][f"{pair['stem']}_{suffix}"],
                "Area journal reference",
            )
    require(report["context"] == worker.context(manifest_sha, report["day"]), "Day context")


def verify(received, allow_partial=False):
    prepared_path = ROOT / "outputs/cloud_month/preparation.json"
    preparation = json.loads(prepared_path.read_text())
    bundle = Path(preparation["bundle"])
    require(digest(bundle) == preparation["bundle_sha256"], "Prepared bundle changed")
    with zipfile.ZipFile(bundle) as archive:
        require(archive.testzip() is None, "Prepared bundle CRC")
        manifest_data = archive.read("month/manifest.json")
        manifest = json.loads(manifest_data)
        b = json.loads(archive.read("month/bootstrap_manifest.json"))
        metadata = {
            name: json.loads(archive.read(name))
            for name in manifest["bundle_files"]
            if name.startswith(("month/metadata/", "summer/metadata/"))
        }
        for name, checksum in manifest["bundle_files"].items():
            require(
                hashlib.sha256(archive.read(name)).hexdigest() == checksum, "Bundle member changed"
            )
            if name.startswith(("scripts/", "data/")):
                require(digest(ROOT / name) == checksum, "Local code/geography changed")
    manifest_sha = hashlib.sha256(manifest_data).hexdigest()
    all_pairs = [*manifest["pairs"], *b["pairs"]]
    require(
        len(all_pairs) == 270 and len({p["sample_id"] for p in all_pairs}) == 270,
        "Month pair scope",
    )
    before = digest(received)
    with tempfile.TemporaryDirectory(dir=ROOT / "outputs/cloud_month") as directory:
        output = Path(directory)
        with zipfile.ZipFile(received) as archive:
            infos = archive.infolist()
            names = [i.filename for i in infos]
            require(len(names) == len(set(names)), "Duplicate result member")
            require(archive.testzip() is None, "Result CRC")
            summary = json.loads(archive.read("month_summary.json"))
            records = summary["daily_commits"]
            days = [r["day"] for r in records]
            require(len(days) == len(set(days)) and set(days) <= set(worker.DAYS), "Result days")
            complete = set(days) == set(worker.DAYS)
            require(
                complete or allow_partial, "Month incomplete; use --allow-partial for diagnostics"
            )
            require(
                bool(days)
                and summary["completed_days"] == len(days)
                and summary["status"] == ("complete_month_diagnostics" if complete else "partial"),
                "Completion status",
            )
            require(
                summary["scope"] == "2023-07"
                and summary["manifest_sha256"] == manifest_sha
                and summary["worker_sha256"] == digest(Path(worker.__file__))
                and summary["new_source_bytes"] == 48_301_330_714
                and summary["days_expected"] == 31
                and summary["new_pairs_expected"] == 264,
                "Monthly source/version scope",
            )
            require(
                summary["negative_label_permitted"] is False
                and summary["daily_observation_status"] == "unknown"
                and summary["bootstrap_not_redownloaded"] is True,
                "Summary policy",
            )
            expected = {"month_summary.json"} | {
                f"{d}/{n}" for d in days for n in worker.compact.NAMES
            }
            require(set(names) == expected, "Unexpected monthly ZIP member")
            require(
                all(0 < i.file_size < 100_000_000 for i in infos)
                and sum(i.file_size for i in infos) < 1_000_000_000,
                "Month ZIP size",
            )
            for name in names:
                target = output / name
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(archive.read(name))
        for record in records:
            day = record["day"]
            pairs = [p for p in all_pairs if p["start_utc"].startswith(day)]
            require(
                record["protocol"] == "month_daily_v1"
                and record["day"] == day
                and record["manifest_sha256"] == manifest_sha
                and record["worker_sha256"] == digest(Path(worker.__file__))
                and record["negative_label_permitted"] is False
                and set(record["pair_ids"]) == {p["sample_id"] for p in pairs},
                "Day commit identity",
            )
            report = worker.compact.validate_day(
                output / day,
                day,
                [p["sample_id"] for p in pairs],
                worker.context(manifest_sha, day),
            )
            check_sources(report, pairs, manifest_sha, metadata)
            print(f"Independent compact readback passed: {day}", flush=True)
    require(digest(received) == before, "Received ZIP changed during readback")
    return {
        "status": "independent_month_compact_readback_passed"
        if complete
        else "partial_compact_readback_passed",
        "completed_days": len(days),
        "complete_month": complete,
        "received_sha256": before,
        "received_bytes": received.stat().st_size,
        "manifest_sha256": manifest_sha,
        "negative_label_permitted": False,
        "raw_reprocessed": False,
        "remote_drive_independently_verified": False,
        "geometry_union_recomputed_from_pair_journals": False,
        "limitations": (
            "Compact numeric/source/time readback; full geometry lives in Drive pair journals"
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("received", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT
        / "outputs/reports/observation_coverage/colab_month_received_verification.json",
    )
    args = parser.parse_args()
    result = verify(args.received, args.allow_partial)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    worker.atomic_json(args.report, result)
    print(json.dumps(result, indent=2))
