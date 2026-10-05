"""Independently validate a received day ZIP against its frozen local bundle."""

import argparse
import hashlib
import importlib.util
import json
import math
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "day_worker", Path(__file__).with_name("run_l2_day.py")
)
day = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(day)
require = day.require


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(results, bundle, cloud=True):
    original_root = day.ROOT
    try:
        with tempfile.TemporaryDirectory() as temporary, zipfile.ZipFile(bundle) as archive:
            root = day.ROOT = Path(temporary)
            manifest_bytes = archive.read("day/manifest.json")
            manifest = json.loads(manifest_bytes)
            names = list(manifest["bundle_files"]) + ["day/manifest.json"]
            require(
                len(names) == len(set(archive.namelist())) == len(archive.namelist()),
                "Unexpected bundle members",
            )
            require(set(names) == set(archive.namelist()), "Unexpected bundle member names")
            for name in names:
                target = (root / name).resolve()
                require(target.is_relative_to(root), "Bundle path escapes root")
                data = archive.read(name)
                if name in manifest["bundle_files"]:
                    require(sha(data) == manifest["bundle_files"][name], "Bundle identity differs")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            require(
                day.digest(Path(day.__file__))
                == manifest["bundle_files"]["scripts/cloud/run_l2_day.py"],
                "Local verifier worker differs from bundle",
            )
            for module, name in (
                (day.pilot, "scripts/cloud/run_l2_pilot.py"),
                (day.result_check, "scripts/cloud/verify_l2_pilot_results.py"),
            ):
                require(
                    day.digest(Path(module.__file__)) == manifest["bundle_files"][name],
                    "Local verification helper differs from bundle",
                )
            manifest, manifest_sha = day.manifest_read()
            output = root / "day/results"
            day.restore_results(results, manifest, manifest_sha, output)
            summary = json.loads((output / "day_summary.json").read_text())
            require(summary["status"] == "passed_all_eight_references", "Day unfinished")
            require(
                summary["environment"]
                == ("authenticated_cloud_day" if cloud else "local_rehearsal"),
                "Unexpected execution environment",
            )
            require(
                summary["day"] == manifest["day"] and summary["manifest_sha256"] == manifest_sha,
                "Summary identity differs",
            )
            require(summary["worker_sha256"] == day.digest(Path(day.__file__)), "Worker differs")
            require(
                summary["completed_pairs"] == 8 and summary["negative_label_permitted"] is False,
                "Completion/label mismatch",
            )
            reused = summary["reused_pairs_this_invocation"]
            processed = summary["processed_pairs_this_invocation"]
            require(
                isinstance(reused, int)
                and isinstance(processed, int)
                and 1 <= reused <= 8
                and processed >= 0
                and reused + processed == 8,
                "Resume demonstration missing",
            )
            records = [
                day.checkpoint_read(pair, output, manifest_sha) for pair in manifest["pairs"]
            ]
            require(all(records) and summary["records"] == records, "Checkpoint summary mismatch")
            for pair, record in zip(manifest["pairs"], records, strict=True):
                metrics = record["metrics"]
                sizes = [source["bytes"] for source in pair["sources"]]
                require(metrics["pair_source_bytes"] == sum(sizes), "Source byte count differs")
                require(
                    metrics["downloaded_payload_bytes"] in {0, *sizes, sum(sizes)},
                    "Download metric differs",
                )
                elapsed = metrics["elapsed_seconds"]
                require(
                    isinstance(elapsed, (int, float)) and math.isfinite(elapsed) and elapsed > 0,
                    "Invalid duration",
                )
                if cloud:
                    require(
                        isinstance(metrics["child_peak_rss_bytes"], int)
                        and metrics["child_peak_rss_bytes"] > 0,
                        "Missing memory measurement",
                    )
                before, minimum = (
                    metrics["free_disk_before_bytes"],
                    metrics["minimum_sampled_free_disk_bytes"],
                )
                require(
                    0 < minimum <= before
                    and metrics["sampled_disk_increase_bytes"] == before - minimum
                    and metrics["disk_samples"] >= 2,
                    "Invalid disk measurements",
                )
            source_bytes = sum(s["bytes"] for p in manifest["pairs"] for s in p["sources"])
            require(summary["source_bytes_all_pairs"] == source_bytes, "Total source size differs")
            if cloud:
                require(summary["python"].startswith("3.12."), "Python version differs")
                pins = dict(
                    line.split("==")
                    for line in (root / "scripts/cloud/requirements_l2_pilot.txt")
                    .read_text()
                    .splitlines()
                    if line and not line.startswith("#")
                )
                versions = summary["dependencies"]
                require(
                    set(versions)
                    == {
                        "rasterio",
                        "geopandas",
                        "numpy",
                        "pandas",
                        "shapely",
                        "pyproj",
                        "earthaccess",
                    },
                    "Reported dependency set differs",
                )
                require(
                    all(version == pins[name] for name, version in versions.items()),
                    "Package versions differ",
                )
            return {
                "checked_at_utc": datetime.now(UTC).isoformat(),
                "status": "independent_day_result_verified",
                "environment": summary["environment"],
                "results_zip_sha256": sha(results.read_bytes()),
                "bundle_sha256": sha(bundle.read_bytes()),
                "verifier_sha256": sha(Path(__file__).read_bytes()),
                "completed_pairs": 8,
                "grid_rows_per_pair": 2899,
                "all_audits_and_csv_columns_equal": True,
                "resume_reused_pairs": reused,
                "source_bytes": source_bytes,
                "result_zip_bytes": results.stat().st_size,
                "maximum_child_peak_rss_bytes": max(
                    (
                        r["metrics"]["child_peak_rss_bytes"]
                        for r in records
                        if r["metrics"]["child_peak_rss_bytes"] is not None
                    ),
                    default=None,
                ),
                "maximum_sampled_disk_increase_bytes": max(
                    r["metrics"]["sampled_disk_increase_bytes"] for r in records
                ),
                "elapsed_seconds_across_processed_pairs": sum(
                    r["metrics"]["elapsed_seconds"] for r in records
                ),
                "negative_label_permitted": False,
                "limitations": summary["limitations"],
            }
    finally:
        day.ROOT = original_root


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_zip", type=Path)
    parser.add_argument("--bundle", type=Path, default=ROOT / "outputs/cloud_day/l2_day_bundle.zip")
    parser.add_argument("--local-rehearsal", action="store_true")
    args = parser.parse_args()
    result = verify(args.results_zip, args.bundle, cloud=not args.local_rehearsal)
    destination = (
        ROOT
        / "outputs/reports/observation_coverage"
        / (
            "colab_day_local_rehearsal.json"
            if args.local_rehearsal
            else "colab_day_received_verification.json"
        )
    )
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
