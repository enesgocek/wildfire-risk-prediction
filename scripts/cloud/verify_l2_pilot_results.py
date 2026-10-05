"""Independently read a received pilot ZIP without executing or extracting it."""

import argparse
import copy
import hashlib
import io
import json
import math
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE = ROOT / "outputs/cloud_pilot/l2_pilot_isolated_bundle.zip"
SUMMARY = "cloud_pilot_verification.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_received(path, stem):
    names = {SUMMARY, f"{stem}_audit.json", f"{stem}_grid_centers.csv"}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        require(
            len(infos) == len(names) and {item.filename for item in infos} == names,
            "Unexpected, duplicate, or missing result ZIP members",
        )
        require(all(0 < item.file_size < 5_000_000 for item in infos), "Unexpected result size")
        require(archive.testzip() is None, "Result ZIP CRC mismatch")
        return {name: archive.read(name) for name in names}


def normalized_audit(value):
    value = copy.deepcopy(value)
    value.pop("checked_at_utc")
    for source in value["sources"].values():
        source["path"] = source["path"].replace("\\", "/").rsplit("/", 1)[-1]
    return value


def verify(results_path, bundle_path=DEFAULT_BUNDLE):
    with zipfile.ZipFile(bundle_path) as bundle:
        raw_manifest = bundle.read("pilot/manifest.json")
        manifest = json.loads(raw_manifest)
        require(manifest["sample_id"] == "SNPP:2019013.0100", "Wrong pilot reference")
        for name, expected_sha in manifest["bundle_files"].items():
            require(sha(bundle.read(name)) == expected_sha, f"Reference bundle changed: {name}")
        expected_audit = json.loads(bundle.read("pilot/reference/audit.json"))
        expected_csv = bundle.read("pilot/reference/grid_centers.csv")
        worker_sha = sha(bundle.read("scripts/cloud/run_l2_pilot.py"))
    stem = manifest["stem"]
    received = read_received(results_path, stem)
    summary = json.loads(received[SUMMARY])
    actual_audit = json.loads(received[f"{stem}_audit.json"])
    require(summary["status"] == "passed_exact_local_reference_comparison", "Pilot did not pass")
    require(summary["environment"] == "authenticated_cloud_pilot", "This is not a cloud result")
    require(summary["sample_id"] == manifest["sample_id"], "Result sample mismatch")
    require(summary["manifest_sha256"] == sha(raw_manifest), "Result came from a different bundle")
    require(summary["pilot_script_sha256"] == worker_sha, "Result worker identity differs")
    require(
        normalized_audit(actual_audit) == normalized_audit(expected_audit),
        "Cloud audit differs from reference beyond timestamp/path formatting",
    )
    for source in manifest["sources"]:
        actual_source = actual_audit["sources"][source["role"]]
        require(
            actual_source["bytes"] == source["bytes"]
            and actual_source["sha256"] == source["sha256"],
            "Source identity differs",
        )
    expected = pd.read_csv(io.BytesIO(expected_csv)).sort_values("grid_id").reset_index(drop=True)
    actual = pd.read_csv(io.BytesIO(received[f"{stem}_grid_centers.csv"]))
    require(len(actual) == 2899 and actual.grid_id.is_unique, "Grid count/uniqueness differs")
    actual = actual.sort_values("grid_id").reset_index(drop=True)
    pd.testing.assert_frame_equal(actual, expected, check_exact=True)
    require(
        summary["negative_label_permitted"] is False
        and actual_audit["negative_label_permitted"] is False,
        "Negative labels not allowed",
    )
    require(
        actual.negative_label_permitted.eq(False).all()
        and actual.daily_observation_status.eq("unknown").all(),
        "Daily status/labels changed",
    )
    source_bytes = sum(source["bytes"] for source in manifest["sources"])
    require(summary["source_bytes"] == source_bytes, "Source byte total mismatch")
    sizes = [source["bytes"] for source in manifest["sources"]]
    require(
        summary["downloaded_payload_bytes"] in {0, *sizes, source_bytes},
        "Unexpected successful download payload count",
    )
    output_bytes = sum(len(data) for name, data in received.items() if name != SUMMARY)
    require(summary["result_bytes_before_summary"] == output_bytes, "Result byte count differs")
    elapsed = summary["elapsed_seconds"]
    require(
        isinstance(elapsed, (int, float)) and math.isfinite(elapsed) and elapsed > 0,
        "Invalid elapsed time",
    )
    require(summary["python"].startswith("3.12."), "Unsupported cloud Python")
    versions = {}
    for line in (ROOT / "scripts/cloud/requirements_l2_pilot.txt").read_text().splitlines():
        if line and not line.startswith("#"):
            name, version = line.split("==")
            versions[name] = version
    reported_versions = summary["dependencies"]
    require(
        set(reported_versions)
        == {"rasterio", "geopandas", "numpy", "pandas", "shapely", "pyproj", "earthaccess"},
        "Unexpected reported dependency set",
    )
    require(
        all(version == versions[name] for name, version in reported_versions.items()),
        "Cloud package versions differ",
    )
    for key in ("free_disk_before_bytes", "free_disk_after_bytes"):
        require(isinstance(summary[key], int) and summary[key] > 0, "Invalid free disk reading")
    return {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "independent_received_cloud_pilot_verification_passed",
        "verifier_sha256": sha(Path(__file__).read_bytes()),
        "results_zip_sha256": sha(results_path.read_bytes()),
        "bundle_zip_sha256": sha(bundle_path.read_bytes()),
        "member_sha256": {name: sha(data) for name, data in received.items()},
        "sample_id": manifest["sample_id"],
        "grid_rows": len(actual),
        "grid_columns": list(actual.columns),
        "all_grid_columns_exactly_equal": True,
        "full_audit_equal_except_timestamp_and_path_format": True,
        "source_bytes": source_bytes,
        "downloaded_payload_bytes": summary["downloaded_payload_bytes"],
        "elapsed_seconds_excluding_environment_setup": elapsed,
        "result_zip_bytes": results_path.stat().st_size,
        "result_uncompressed_bytes": sum(map(len, received.values())),
        "cloud_python": summary["python"],
        "dependencies": reported_versions,
        "negative_label_permitted": False,
        "limitations": [
            "One fixed training swath, not full-period capacity or footprint validation",
            "Source hashes describe checked cloud inputs; raw inputs are not in result ZIP",
            "Disk readings are before/after; peak RAM/disk was not measured",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_zip", type=Path)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    args = parser.parse_args()
    result = verify(args.results_zip, args.bundle)
    destination = (
        ROOT / "outputs/reports/observation_coverage/colab_pilot_received_verification.json"
    )
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "grid_rows": result["grid_rows"],
                "seconds": result["elapsed_seconds_excluding_environment_setup"],
                "result_zip_bytes": result["result_zip_bytes"],
                "report": str(destination),
            }
        )
    )
