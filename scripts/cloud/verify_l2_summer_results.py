"""Local readback of the bounded summer ZIP; no NASA/Drive login or raw downloads."""

import argparse
import importlib.util
import json
import math
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "summer_local_verify", Path(__file__).with_name("run_l2_summer.py")
)
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)
require, digest = worker.require, worker.digest


def verify(results, bundle):
    preparation = json.loads((ROOT / "outputs/cloud_summer/preparation.json").read_text())
    require(digest(bundle) == preparation["bundle_sha256"], "Frozen bundle differs")
    original_root = worker.ROOT
    try:
        with tempfile.TemporaryDirectory() as directory, zipfile.ZipFile(bundle) as archive:
            root = worker.ROOT = Path(directory)
            manifest = json.loads(archive.read("summer/manifest.json"))
            expected = set(manifest["bundle_files"]) | {"summer/manifest.json"}
            require(
                set(archive.namelist()) == expected and len(archive.namelist()) == len(expected),
                "Unexpected bundle members",
            )
            require(archive.testzip() is None, "Bundle CRC")
            for name in expected:
                target = (root / name).resolve()
                require(target.is_relative_to(root), "Bundle path escapes root")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))
                if name in manifest["bundle_files"]:
                    require(
                        digest(target) == manifest["bundle_files"][name], "Bundle content differs"
                    )
                    if name.startswith("scripts/"):
                        require(
                            digest(ROOT / name) == digest(target), "Local code changed since bundle"
                        )
            manifest, manifest_sha = worker.manifest_read()
            output = root / "summer/results"
            output.mkdir(parents=True)
            allowed = {"summer_summary.json"}
            for pair in manifest["pairs"]:
                allowed.update(f"{pair['stem']}_{s}" for s in (*worker.SUFFIXES, "checkpoint.json"))
            with zipfile.ZipFile(results) as result:
                infos = result.infolist()
                names = [i.filename for i in infos]
                require(
                    set(names) == allowed and len(names) == len(allowed),
                    "Incomplete/unexpected result ZIP",
                )
                require(
                    all(0 < i.file_size < 150_000_000 for i in infos)
                    and sum(i.file_size for i in infos) < 750_000_000,
                    "Result size bounds",
                )
                require(result.testzip() is None, "Result CRC")
                for name in names:
                    (output / name).write_bytes(result.read(name))
            summary = json.loads((output / "summer_summary.json").read_text())
            require(
                summary["status"] == "complete_native_diagnostics"
                and summary["day"] == "2023-07-16"
                and summary["completed_pairs"] == 6,
                "Summer day incomplete",
            )
            require(
                summary["manifest_sha256"] == manifest_sha
                and summary["worker_sha256"] == digest(Path(worker.__file__)),
                "Summary identity",
            )
            require(
                summary["negative_label_permitted"] is False
                and summary["daily_observation_status"] == "unknown"
                and summary["golden_raw_reference_available"] is False,
                "Incorrect verification claim",
            )
            require(summary["python"].startswith("3.12."), "Python version")
            pins = dict(
                line.split("==")
                for line in (root / "scripts/cloud/requirements_l2_pilot.txt")
                .read_text()
                .splitlines()
                if line and not line.startswith("#")
            )
            require(
                set(summary["dependencies"])
                == {"rasterio", "geopandas", "numpy", "pandas", "shapely", "pyproj"}
                and all(pins[n] == v for n, v in summary["dependencies"].items()),
                "Package versions",
            )
            records = [
                worker.checkpoint_read(pair, output, manifest_sha) for pair in manifest["pairs"]
            ]
            require(all(records) and records == summary["records"], "Checkpoint summary differs")
            total_bytes = 0
            for pair, record in zip(manifest["pairs"], records, strict=True):
                metrics = record["metrics"]
                sizes = [s["bytes"] for s in pair["sources"]]
                require(metrics["pair_source_bytes"] == sum(sizes), "Source size metric")
                require(
                    metrics["downloaded_payload_bytes"] in {0, *sizes, sum(sizes)},
                    "Transfer metric",
                )
                require(
                    math.isfinite(metrics["elapsed_seconds"]) and metrics["elapsed_seconds"] > 0,
                    "Duration metric",
                )
                require(
                    metrics["child_peak_rss_bytes"] > 0
                    and metrics["sampled_disk_increase_bytes"] >= 0,
                    "Resource metrics",
                )
                total_bytes += sum(sizes)
            require(total_bytes == preparation["source_bytes"], "Total bytes")
            return {
                "checked_at_utc": datetime.now(UTC).isoformat(),
                "status": "independent_summer_result_readback_passed",
                "completed_pairs": 6,
                "results_zip_sha256": digest(results),
                "bundle_sha256": digest(bundle),
                "verifier_sha256": digest(Path(__file__)),
                "source_bytes": total_bytes,
                "seconds_sum": sum(r["metrics"]["elapsed_seconds"] for r in records),
                "maximum_child_rss_bytes": max(
                    r["metrics"]["child_peak_rss_bytes"] for r in records
                ),
                "golden_raw_reference_available": False,
                "negative_label_permitted": False,
                "limits": [
                    "No local summer raw reference; native/CMR/invariant readback only",
                    "Approximate geometry and scan envelopes; not physical continuous coverage",
                    "Drive remount is performed by the notebook; raw satellite files are absent",
                ],
            }
    finally:
        worker.ROOT = original_root


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument(
        "--bundle", type=Path, default=ROOT / "outputs/cloud_summer/l2_summer_B_bundle.zip"
    )
    args = parser.parse_args()
    result = verify(args.results, args.bundle)
    target = ROOT / "outputs/reports/observation_coverage/colab_summer_received_verification.json"
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {target}")
