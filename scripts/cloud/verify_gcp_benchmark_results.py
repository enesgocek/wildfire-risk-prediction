"""Independent local readback of both GCP arms and the prior Colab products.

No network, cloud commands, raw processing, or execution of received ZIP code.
The existing scientific verifier is imported from the local repository only.
"""

import argparse
import copy
import hashlib
import importlib.util
import io
import json
import math
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_SHA = "61ef861ffe461e60de45856b43cb1111d5ed80f5f9b8ac2f6aeb4bf98af783bb"
SUMMER_SHA = "0a90b93be0ed31fa468b6ecef61851612bcd255e34caf3ccdb6adf2d6d425f7e"
SUMMARY = "gcp_benchmark_summary.json"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_received(path):
    with zipfile.ZipFile(path) as archive:
        names = {SUMMARY, "workers_1.zip", "workers_2.zip"}
        infos = archive.infolist()
        require(len(infos) == 3 and {i.filename for i in infos} == names, "Outer ZIP members")
        require(all(0 < i.file_size < 30_000_000 for i in infos), "Outer ZIP size bounds")
        require(archive.testzip() is None, "Outer ZIP CRC")
        return {n: archive.read(n) for n in names}


def validate_summary(summary, spec, received):
    require(summary["status"] == "gcp_two_arm_benchmark_completed", "Benchmark incomplete")
    require(summary["negative_label_permitted"] is False, "Labels forbidden")
    require(summary["full_years_processed"] is False, "Scope changed")
    arms = summary["arms"]
    require(len(arms) == 2 and [a["workers"] for a in arms] == [1, 2], "Arm scope/order")
    for arm in arms:
        data = received[f"workers_{arm['workers']}.zip"]
        require(arm["result_zip_sha256"] == sha(data), "Arm ZIP SHA")
        require(arm["result_zip_bytes"] == len(data), "Arm ZIP byte count")
        require(arm["completed_pairs"] == 6, "Incomplete six pairs")
        require(
            arm["downloaded_payload_bytes"] == spec["source_bytes_per_arm"], "Cold source total"
        )
        seconds = arm["cold_pair_wall_seconds"]
        require(
            type(seconds) in (int, float) and math.isfinite(seconds) and seconds > 0, "Wall time"
        )
        rss = arm["maximum_child_peak_rss_bytes"]
        require(type(rss) is int and rss > 0, "Child RSS")
    ratio = arms[0]["cold_pair_wall_seconds"] / arms[1]["cold_pair_wall_seconds"]
    require(
        math.isclose(summary["speedup_two_vs_one"], ratio, rel_tol=1e-12), "Speed ratio changed"
    )
    require(summary["cold_source_bytes_total"] == 2 * spec["source_bytes_per_arm"], "Total payload")
    return ratio


def normalized_audit(value):
    value = copy.deepcopy(value)
    value.pop("checked_at_utc")
    for source in value["sources"].values():
        source["path"] = source["path"].replace("\\", "/").rsplit("/", 1)[-1]
    return value


def compare_area_tables(actual, reference, exact=False):
    require(list(actual.columns) == list(reference.columns), "Area schema differs")
    differences = []
    for column in actual.columns:
        tolerance = 0
        if not exact and column.endswith("_m2"):
            tolerance = 1e-4
        elif not exact and column.endswith("fraction_estimate"):
            tolerance = 1e-12
        pd.testing.assert_series_equal(
            actual[column], reference[column], check_exact=tolerance == 0, rtol=0, atol=tolerance
        )
        if tolerance and not actual[column].equals(reference[column]):
            delta = np.abs(actual[column].to_numpy() - reference[column].to_numpy())
            differences.append(
                {
                    "column": column,
                    "different_rows": int((delta > 0).sum()),
                    "max_absolute_difference": float(np.nanmax(delta)),
                    "absolute_tolerance": tolerance,
                }
            )
    return differences


def compare_products(actual, reference, manifest, spec, groups, temporary, exact=False):
    cells = geometry_rows = 0
    coordinate_tolerance = 0 if exact else 1e-8
    area_differences, geometry_differences = [], []
    for pair in manifest["pairs"]:
        stem, sample_id = pair["stem"], pair["sample_id"]
        audit_name = f"{stem}_audit.json"
        audit = json.loads(actual.read(audit_name))
        prior = json.loads(reference.read(audit_name))
        require(normalized_audit(audit) == normalized_audit(prior), "Full audit differs from Colab")
        for role, expected in spec["source_sha256"][sample_id].items():
            require(audit["sources"][role]["sha256"] == expected, "Native source identity changed")
        for suffix, expected in spec["exact_csv_sha256"][sample_id].items():
            name = f"{stem}_{suffix}"
            require(sha(actual.read(name)) == sha(reference.read(name)) == expected, "CSV differs")
        csv_name = f"{stem}_area_estimate.csv"
        a = (
            pd.read_csv(io.BytesIO(actual.read(csv_name)))
            .sort_values("grid_id")
            .reset_index(drop=True)
        )
        b = (
            pd.read_csv(io.BytesIO(reference.read(csv_name)))
            .sort_values("grid_id")
            .reset_index(drop=True)
        )
        differences = compare_area_tables(a, b, exact)
        area_differences.extend({"sample_id": sample_id, **d} for d in differences)
        cells += len(a)
        geometry_name = f"{stem}_area_estimate.gpkg"
        paths = [temporary / f"{prefix}_{stem}.gpkg" for prefix in ("actual", "prior")]
        for path, archive in zip(paths, (actual, reference), strict=True):
            path.write_bytes(archive.read(geometry_name))
        for group in groups:
            frames = [
                gpd.read_file(path, layer=group).sort_values("grid_id").reset_index(drop=True)
                for path in paths
            ]
            require(frames[0].crs == frames[1].crs, "Geometry CRS differs")
            compare_area_tables(
                pd.DataFrame(frames[0].drop(columns="geometry")),
                pd.DataFrame(frames[1].drop(columns="geometry")),
                exact,
            )
            left, right = frames[0].geometry.array, frames[1].geometry.array
            if exact:
                require(
                    shapely.equals_exact(left, right, tolerance=0, normalize=True).all(),
                    "Geometry coordinates differ between arms",
                )
            changed = ~shapely.equals_exact(left, right, tolerance=0, normalize=True)
            if changed.any():
                distance = shapely.hausdorff_distance(left[changed], right[changed])
                symmetric_area = shapely.area(
                    shapely.symmetric_difference(left[changed], right[changed])
                )
                require(
                    np.isfinite(distance).all() and np.isfinite(symmetric_area).all(),
                    "Geometry distance",
                )
                require((distance <= coordinate_tolerance).all(), "Geometry distance too large")
                require((symmetric_area <= (0 if exact else 1e-4)).all(), "Geometry area too large")
                geometry_differences.append(
                    {
                        "sample_id": sample_id,
                        "group": group,
                        "nonexact_rows": int(changed.sum()),
                        "different_coordinate_count_rows": int(
                            (
                                shapely.get_num_coordinates(left[changed])
                                != shapely.get_num_coordinates(right[changed])
                            ).sum()
                        ),
                        "max_hausdorff_coordinate_m": float(distance.max()),
                        "max_symmetric_difference_m2": float(symmetric_area.max()),
                    }
                )
            geometry_rows += len(frames[0])
    return {
        "area_table_rows_compared": cells,
        "geometry_rows_compared": geometry_rows,
        "geometry_groups": list(groups),
        "geometry_coordinate_tolerance": coordinate_tolerance,
        "all_four_native_csv_bytes_match_colab": True,
        "full_audit_equal_except_timestamp_path": True,
        "all_area_columns_within_tolerance": True,
        "all_saved_geometry_boundaries_within_tolerance": True,
        "area_tables_exactly_equal": not area_differences,
        "geometry_coordinates_exactly_equal": not geometry_differences,
        "area_roundoff_differences": area_differences,
        "geometry_roundoff_differences": geometry_differences,
    }


def verify(results):
    package = ROOT / "outputs/gcp_benchmark/wildfire_gcp_benchmark.zip"
    bundle = ROOT / "outputs/cloud_summer/l2_summer_B_bundle.zip"
    reference = ROOT / "outputs/cloud_summer/received/l2_summer_results.zip"
    require(sha(package.read_bytes()) == PACKAGE_SHA, "GCP package changed")
    require(sha(bundle.read_bytes()) == SUMMER_SHA, "Frozen science bundle changed")
    with zipfile.ZipFile(package) as archive:
        raw_spec = archive.read("benchmark_manifest.json")
        spec = json.loads(raw_spec)
        require(archive.testzip() is None, "Package CRC")
        require(spec["protocol"] == "gcp_summer_two_arm_v1" and spec["arms"] == [1, 2], "Protocol")
        require(spec["negative_label_permitted"] is False, "Package labels forbidden")
        for name, checksum in spec["files"].items():
            require(sha(archive.read(name)) == checksum, "Package member changed")
    require(
        sha(reference.read_bytes()) == spec["colab_results_sha256"], "Prior Colab proof changed"
    )
    received = read_received(results)
    summary = json.loads(received[SUMMARY])
    require(summary["package_manifest_sha256"] == sha(raw_spec), "Wrong GCP package identity")
    ratio = validate_summary(summary, spec, received)
    verifier_path = ROOT / "scripts/cloud/verify_l2_summer_results.py"
    module_spec = importlib.util.spec_from_file_location("gcp_native_readback", verifier_path)
    native = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(native)
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("summer/manifest.json"))
    arm_reports = []
    with tempfile.TemporaryDirectory(dir=ROOT / "outputs/gcp_benchmark") as directory:
        temporary = Path(directory)
        with zipfile.ZipFile(reference) as prior:
            require(prior.testzip() is None, "Reference CRC")
            for arm in summary["arms"]:
                path = temporary / f"workers_{arm['workers']}.zip"
                path.write_bytes(received[path.name])
                readback = native.verify(path, bundle)
                # Legacy wording about a Colab notebook is not a GCP storage claim.
                readback["limits"] = [s for s in readback["limits"] if "Drive remount" not in s]
                with zipfile.ZipFile(path) as actual:
                    native_summary = json.loads(actual.read("summer_summary.json"))
                    require(
                        native_summary["processed_this_invocation"] == 6
                        and native_summary["reused_this_invocation"] == 0,
                        "Cached arm",
                    )
                    for record in native_summary["records"]:
                        metrics = record["metrics"]
                        require(
                            metrics["downloaded_payload_bytes"] == metrics["pair_source_bytes"],
                            "Warm pair",
                        )
                        require(
                            metrics["disk_sampling_enabled"] is False
                            and metrics["sampled_disk_increase_bytes"] == 0,
                            "Disk claim changed",
                        )
                    require(
                        readback["maximum_child_rss_bytes"] == arm["maximum_child_peak_rss_bytes"],
                        "RSS summary differs",
                    )
                    require(
                        arm["cold_pair_wall_seconds"] + 1e-6
                        >= readback["seconds_sum"] / arm["workers"],
                        "Impossible timing",
                    )
                    comparison = compare_products(
                        actual, prior, manifest, spec, native.worker.area.GROUPS, temporary
                    )
                arm_reports.append(
                    {
                        "workers": arm["workers"],
                        "native_readback": readback,
                        "colab_comparison": comparison,
                    }
                )
            with (
                zipfile.ZipFile(io.BytesIO(received["workers_1.zip"])) as first,
                zipfile.ZipFile(io.BytesIO(received["workers_2.zip"])) as second,
            ):
                cross_arm = compare_products(
                    second, first, manifest, spec, native.worker.area.GROUPS, temporary, exact=True
                )
    return {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "independent_gcp_two_arm_readback_passed",
        "verifier_sha256": sha(Path(__file__).read_bytes()),
        "result_zip_sha256": sha(results.read_bytes()),
        "result_zip_bytes": results.stat().st_size,
        "package_sha256": PACKAGE_SHA,
        "package_manifest_sha256": sha(raw_spec),
        "summary": summary,
        "arms": arm_reports,
        "speedup_two_vs_one": ratio,
        "duration_reduction_fraction": 1 - 1 / ratio,
        "both_arms_match_same_colab_reference": True,
        "cross_arm_exact_comparison": cross_arm,
        "negative_label_permitted": False,
        "full_years_processed": False,
        "raw_reprocessed_locally": False,
        "vm_state_checked_remotely": False,
        "limits": [
            "One six-pair benchmark; fixed-order network/cache effects are unresolved",
            "Saved approximate geometry compared; physical footprints not validated",
            "Source SHA comes from cloud diagnostics; raw sources are absent locally",
            "Child RSS is not simultaneous VM memory; disk peak not sampled",
            "No API read of VM state, billing costs, or disk inventory",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    report = verify(args.results)
    output = ROOT / "outputs/reports/observation_coverage/gcp_benchmark_received_verification.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "speedup": report["speedup_two_vs_one"],
                "reduction_percent": 100 * report["duration_reduction_fraction"],
                "report": str(output),
            },
            indent=2,
        )
    )
