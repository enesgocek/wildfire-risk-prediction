"""Offline spatial/time diagnostics of the accepted first core pair; no labels."""

import argparse
import importlib.util
import json
import socket
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import shapely

from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/reports/dataset/observation_core_spatial_v1"
NATIVE = ROOT / "outputs/reports/dataset/observation_core_native_v1/20261015T104742Z_295e4bc3"
NATIVE_SHA = "2da1534f3a0e57a8c736ea37199fc2158ba3f329f1862b96c2d5cf87788c05f3"
PLAN = ROOT / "outputs/reports/dataset/observation_core_transfer_v1/20261015T104255Z_9750c1c4"
PROTECTED = ROOT / (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)
LIMIT_SECONDS = 1800


def load_script(name):
    path = ROOT / "scripts/firms" / name
    spec = importlib.util.spec_from_file_location("spatial_core_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    require(not path.exists(), "No accepted result overwrite")
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def accepted_parent(folder, expected_sha):
    report = folder / "native_probe.json"
    require(digest(report) == expected_sha, "Pinned native receipt")
    value = json.loads(report.read_text(encoding="utf-8"))
    completion = json.loads((folder / "completion_readback.json").read_text(encoding="utf-8"))
    launcher = json.loads((folder / "launcher_receipt.json").read_text(encoding="utf-8"))
    require(completion["report_sha256"] == expected_sha, "Native completion hash")
    require(
        value["status"] == "one_pair_bytes_and_headers_passed"
        and value["sample_id"] == "SNPP:2018045.0000"
        and launcher["status"] == "child_completed"
        and launcher["plan_sha256"] == value["plan_sha256"]
        and value["negative_label_permitted"] is False
        and value["daily_observation_status"] == "unknown"
        and value["labels_created"] is False,
        "Accepted training-only native parent",
    )
    return value


def read_table(path, original):
    table = pd.read_csv(path, dtype={"pair_key": str, "grid_id": str, "sensor": str})
    require(list(table.columns) == list(original.columns), "CSV columns")
    require(len(table) == len(original), "CSV rows")
    for name in original.columns:
        expected = original[name]
        actual = table[name]
        if pd.api.types.is_numeric_dtype(expected):
            require(np.allclose(actual, expected, rtol=1e-12, atol=1e-7), "CSV numeric values")
        else:
            require(
                actual.fillna("").astype(str).equals(expected.fillna("").astype(str)),
                "CSV text values",
            )
    return table


def verify_geometry(path, table, parts, groups):
    expected = table.set_index("grid_id").loc[parts.grid_id]
    for group in groups:
        frame = gpd.read_file(path, layer=group)
        require(frame.crs.to_epsg() == 6933, "Geometry projection")
        require(
            frame.grid_id.is_unique and set(frame.grid_id) == set(parts.grid_id), "Geometry keys"
        )
        geometries = frame.set_index("grid_id").loc[parts.grid_id].geometry.to_numpy()
        require(shapely.is_valid(geometries).all(), "Valid saved geometry")
        areas = shapely.area(geometries)
        require(
            np.allclose(areas, expected[f"{group}_area_estimate_m2"], rtol=1e-8, atol=0.05),
            "Geometry/CSV areas",
        )
        outside = shapely.area(shapely.difference(geometries, parts.geometry.to_numpy()))
        require(
            (outside <= np.maximum(0.05, parts.geometry.area.to_numpy() * 1e-8)).all(),
            "Geometry stays inside AOI parts",
        )


def deny(*args, **kwargs):
    raise RuntimeError("Offline core spatial review")


def worker(out):
    require(out.resolve().parent == OUTPUT.resolve() and out.is_dir(), "Fresh project output")
    require(not list(out.glob("l2_*")), "Fresh spatial artifacts")
    socket.socket.connect = deny
    socket.create_connection = deny
    pyproj.network.set_network_enabled(False)
    pins = {}

    def retain(path, expected=None):
        path = path.resolve()
        require(
            path.is_relative_to(ROOT) and path.is_file() and not path.is_symlink(),
            "Regular project input",
        )
        value = digest(path)
        require(expected is None or expected == value, "Pinned spatial input")
        pins[path.relative_to(ROOT).as_posix()] = value
        return path

    def phase(name):
        print("LOCAL SPATIAL PHASE " + name, flush=True)

    phase("verify_parent_and_inputs")
    parent = accepted_parent(NATIVE, NATIVE_SHA)
    native = load_script("run_observation_core_pair.py")
    plan_path = retain(PLAN / "native_plan.json", parent["plan_sha256"])
    plan, pair = native.load_plan(plan_path)
    for name, expected in plan["input_sha256"].items():
        retain(ROOT / name, expected)
    for name in ("native_probe.json", "completion_readback.json", "launcher_receipt.json"):
        retain(NATIVE / name)
    for name in ("readback.json", "completion_readback.json"):
        retain(PLAN / name)
    protected = json.loads(retain(PROTECTED).read_text(encoding="utf-8"))
    require(len(protected) == 22, "Frozen production input inventory")
    for name, expected in protected.items():
        retain(ROOT / name, expected)
    cache = ROOT / parent["cache_directory"]
    require(
        cache.resolve() == ROOT / "data/raw/observation_core_v1" / digest(plan_path)[:16],
        "Accepted dedicated cache",
    )
    require(not (cache / "writer.lock").exists(), "No active cache writer")
    metadata = {}
    for source in pair["sources"]:
        check_file(cache / source["filename"], source)
        retain(cache / source["filename"], source["sha256"])
        metadata[source["role"]] = out / (source["role"] + "_cmr.json")
        write_json(metadata[source["role"]], source["metadata"])
    timing = load_script("audit_l2_observation_timing.py")
    area, audit = timing.area, timing.audit
    # Separate module instances and a new nonce directory preserve every old artifact/code pin.
    for module in (timing, timing.combine, area, audit):
        retain(Path(module.__file__))
        module.OUTPUT = out
    retain(Path(__file__))
    for name in (
        "data/aoi/aoi.geojson",
        "data/aoi/grid_5km.geojson",
        "data/interim/grid_aoi_parts.geojson",
    ):
        retain(ROOT / name)
    phase("native_pixel_centers_and_sparse_orientation")
    audit.inspect(cache, metadata["fire"], metadata["geolocation"])
    sensor, key = pair["sample_id"].split(":")
    stem = audit.sample_stem(sensor, key)
    center_report = json.loads((out / f"{stem}_audit.json").read_text(encoding="utf-8"))
    phase("scan_interior_approximate_area")
    parts_path, parts = area.load_parts()
    area_report, _ = area.estimate(sensor, key, parts_path, parts)
    phase("native_scan_time_quality_reconciliation")
    aoi = gpd.read_file(ROOT / "data/aoi/aoi.geojson").to_crs(4326).geometry.union_all()
    shapely.prepare(aoi)
    ids = set(parts.grid_id)
    centers, scans, provenance, begin = timing.source_scans(
        sensor, key, aoi, pyproj.Transformer.from_crs(4326, 6933, always_xy=True), ids
    )
    require(
        not centers.duplicated(["sensor", "pair_key", "scan_index", "grid_id"]).any(),
        "Unique scan/grid rows",
    )
    grid = timing.summarize_grid(centers, ids, begin)
    for name, table in (("scan_grid", centers), ("all_scans", scans), ("grid_time", grid)):
        path = out / f"{name}.csv"
        table.to_csv(path, index=False)
        read_table(path, table)
    phase("saved_geometry_and_input_readback")
    areas = pd.read_csv(out / f"{stem}_area_estimate.csv")
    require(areas.grid_id.is_unique and set(areas.grid_id) == ids, "All AOI parts retained")
    require(
        areas.daily_observation_status.eq("unknown").all()
        and areas.negative_label_permitted.eq(False).all(),
        "Closed spatial rows",
    )
    verify_geometry(out / f"{stem}_area_estimate.gpkg", areas, parts, area.GROUPS)
    require(set(grid.grid_id) == ids and grid.grid_id.is_unique, "All timing grid keys")
    require(
        int(grid.pixel_center_count.sum()) == center_report["spatial_counts"]["pilot_centers"],
        "Grid/scan/center conservation",
    )
    require(
        all(digest(ROOT / name) == expected for name, expected in pins.items()),
        "Spatial input closure",
    )
    artifacts = {
        p.name: digest(p)
        for p in sorted(out.iterdir())
        if p.is_file() and p.suffix in {".json", ".csv", ".gpkg"}
    }
    result = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "one_pair_spatial_time_diagnostics_passed_not_daily_acceptance",
        "sample_id": pair["sample_id"],
        "native_parent_sha256": NATIVE_SHA,
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "grid_count": len(grid),
        "scan_count": len(scans),
        "scan_grid_rows": len(centers),
        "spatial_counts": center_report["spatial_counts"],
        "sparse_fire_count": center_report["sparse_fire_count"],
        "native_orientation_verified_against_all_sparse_fires": center_report[
            "native_orientation_verified_against_all_sparse_fires"
        ],
        "pilot_class_counts": center_report["pilot_class_counts"],
        "pilot_qa_counts": center_report["pilot_qa_counts"],
        "grids_with_pixel_centers": center_report["grids_with_pixel_centers"],
        "grids_with_nominal_land_centers": int(grid.land_nominal_input_no_residual.gt(0).sum()),
        "area_estimate_km2": area_report["area_estimate_km2"],
        "area_method": area.METHOD,
        "scan_quality_histogram": {
            str(k): v for k, v in area_report["scan_quality_histogram"].items()
        },
        "sensor_mode_histogram": {
            str(k): v for k, v in area_report["sensor_mode_histogram"].items()
        },
        "day_window_status_histogram": scans.day_window_status.value_counts().to_dict(),
        "native_scan_provenance": provenance,
        "network_bytes": 0,
        "cloud_jobs_started": 0,
        "labels_created": False,
        "model_ready": False,
        "full_spatial_pilot_complete": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "limitations": [
            "One six-minute training swath, not a complete cell-day or the 156-unit pilot",
            "Pixel centers are counts, not areas; zero centers is not proven absence",
            "Area uses approximate scan-interior midpoint polygons, not official footprints",
            "Scan envelopes are not per-pixel exact times or continuous observation",
            "AOI parts include all registered cells, not a final vegetation eligibility mask",
            "Class areas may overlap across scans and must not be added as disjoint fractions",
            "No negative-label threshold, calibration, model or final merge accepted",
        ],
    }
    write_json(out / "readback.json", result)
    require(
        json.loads((out / "readback.json").read_text(encoding="utf-8")) == result,
        "Spatial report readback",
    )
    write_json(
        out / "completion_readback.json",
        {"status": "passed", "report_sha256": digest(out / "readback.json")},
    )
    phase("complete_no_labels")


def run():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    out = OUTPUT / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    out.mkdir()
    start = time.monotonic()
    status = "failed_outputs_retained"
    print("Sonuc klasoru: " + out.relative_to(ROOT).as_posix(), flush=True)
    try:
        with (out / "worker.log").open("x", encoding="utf-8") as log:
            child = subprocess.run(
                [sys.executable, str(Path(__file__)), "--worker", str(out)],
                cwd=ROOT,
                stdout=log,
                stderr=log,
                timeout=LIMIT_SECONDS,
                check=False,
            )
        status = "child_completed" if child.returncode == 0 else "failed_outputs_retained"
    except subprocess.TimeoutExpired:
        status = "paused_at_local_runtime_limit_outputs_retained"
    finally:
        write_json(
            out / "launcher_receipt.json",
            {
                "status": status,
                "hard_runtime_seconds": LIMIT_SECONDS,
                "elapsed_seconds": round(time.monotonic() - start, 3),
                "network_permitted": False,
                "cloud_jobs_started": 0,
            },
        )
    print(status, flush=True)
    return 0 if status == "child_completed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
    else:
        sys.exit(run())
