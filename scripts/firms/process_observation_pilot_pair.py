"""Process one exact training pair for fixed pilot cells into scan-linked geometries."""

import importlib.util
import json
import warnings
from contextlib import ExitStack
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Transformer
from rasterio.windows import Window

from wildfire_risk_prediction.core_pilot import GROUPS, scan_shapes
from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]


def script(name):
    spec = importlib.util.spec_from_file_location(
        "pilot_" + name.replace(".", "_"), ROOT / "scripts/firms" / name
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    require(not path.exists(), "No pilot result overwrite")
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_completed(out, pair, queue_sha):
    report = json.loads((out / "readback.json").read_text(encoding="utf-8"))
    completion = json.loads((out / "completion_readback.json").read_text(encoding="utf-8"))
    require(completion["report_sha256"] == digest(out / "readback.json"), "Pair receipt")
    require(
        report["queue_sha256"] == queue_sha
        and report["sample_id"] == pair["sample_id"]
        and report["negative_label_permitted"] is False,
        "Same closed queue pair",
    )
    for name, expected in report["artifact_sha256"].items():
        require(digest(out / name) == expected, "Pair saved artifact")
    return report


def process(pair, cache, out, parts, queue_sha):
    require(not out.exists(), "New pair result directory")
    out.mkdir(parents=True)
    for source in pair["sources"]:
        check_file(cache / source["filename"], source)
        write_json(out / (source["role"] + "_cmr.json"), source["metadata"])
    timing = script("audit_l2_observation_timing.py")
    area, audit = timing.area, timing.audit
    for module in (timing, timing.combine, area, audit):
        module.OUTPUT = out
    audit.inspect(cache, out / "fire_cmr.json", out / "geolocation_cmr.json")
    sensor, key = pair["sample_id"].split(":")
    aoi = gpd.read_file(ROOT / "data/aoi/aoi.geojson").to_crs(4326).geometry.union_all()
    shapely.prepare(aoi)
    grid_ids = set(gpd.read_file(ROOT / "data/aoi/grid_5km.geojson").grid_id)
    projection = Transformer.from_crs(4326, 6933, always_xy=True)
    area_report, expected = area.estimate(
        sensor, key, ROOT / "data/interim/grid_aoi_parts.geojson", parts
    )
    centers, times, provenance, _ = timing.source_scans(sensor, key, aoi, projection, grid_ids)
    centers = centers.loc[centers.grid_id.isin(parts.grid_id)]
    lookup = centers.set_index(["grid_id", "scan_index"]).to_dict("index")
    scheduled = {r["scan_index"] for r in area_report["spatial_scan_diagnostics"]}
    regions = parts.geometry.to_numpy()
    paths = {s["role"]: cache / s["filename"] for s in pair["sources"]}
    shapes = {g: [] for g in GROUPS}
    rows = []
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask, qa = (audit.layer(stack, paths["fire"], n) for n in ("fire_mask", "algorithm_QA"))
        lon, lat = (
            audit.layer(stack, paths["geolocation"], "geolocation_data/" + n)
            for n in ("longitude", "latitude")
        )
        for scan in range(len(times)):
            local = {g: [shapely.GeometryCollection() for _ in regions] for g in GROUPS}
            if scan in scheduled:
                window = Window(0, scan * 32, mask.width, 32)
                local = scan_shapes(
                    lon.read(1, window=window),
                    lat.read(1, window=window),
                    mask.read(1, window=window),
                    qa.read(1, window=window),
                    regions,
                    projection,
                    area.interior_corners,
                    audit.diagnostic_land,
                )
            for index, grid_id in enumerate(parts.grid_id):
                row = times.iloc[scan].to_dict()
                row["grid_id"], row["scan_id"] = grid_id, pair["sample_id"] + ":" + str(scan)
                row["orbit_id"] = f"{sensor}:{provenance['orbit_number']}"
                row["source_nominal_day"] = pair["source_day"]
                counts = lookup.get((grid_id, scan), {})
                for column in timing.COUNTS:
                    row[column] = int(counts.get(column, 0))
                for group in GROUPS:
                    shapes[group].append(local[group][index])
                    row[group + "_m2"] = float(local[group][index].area)
                row["daily_observation_status"], row["negative_label_permitted"] = "unknown", False
                rows.append(row)
    frame = pd.DataFrame(rows)
    require(not frame.duplicated(["grid_id", "scan_id"]).any(), "Distinct scan/cell rows")
    require(len(frame) == len(parts) * len(times), "Zero-area scans retained")
    tolerance = np.maximum(0.05, shapely.area(regions) * 1e-8)
    for group in GROUPS:
        arr = np.asarray(shapes[group], dtype=object)
        for index, grid_id in enumerate(parts.grid_id):
            actual = shapely.union_all(arr[frame.grid_id.eq(grid_id)])
            require(
                actual.symmetric_difference(expected[group][index]).area <= tolerance[index],
                "Scan geometry/independent granule union",
            )
        geo = gpd.GeoDataFrame(frame[["grid_id", "scan_id"]].copy(), geometry=arr, crs=6933)
        geo.to_file(out / "scan_geometries.gpkg", layer=group, driver="GPKG", index=False)
        saved = gpd.read_file(out / "scan_geometries.gpkg", layer=group)
        require(saved.crs.to_epsg() == 6933 and len(saved) == len(frame), "Saved scan geometry")
        require(
            saved.grid_id.tolist() == frame.grid_id.tolist()
            and saved.scan_id.tolist() == frame.scan_id.tolist(),
            "Saved scan identities",
        )
        require(
            (
                shapely.area(shapely.symmetric_difference(saved.geometry.to_numpy(), arr)) <= 0.05
            ).all(),
            "Saved scan geometry position",
        )
    frame.to_csv(out / "scan_grid.csv", index=False)
    reread = pd.read_csv(out / "scan_grid.csv", dtype={"pair_key": str})
    require(reread.pair_key.eq(key).all() and len(reread) == len(frame), "Scan CSV keys")
    for column in timing.COUNTS + [g + "_m2" for g in GROUPS]:
        require(
            np.allclose(reread[column], frame[column], rtol=1e-10, atol=1e-7),
            "Scan CSV numeric readback",
        )
    require(
        int(frame.pixel_center_count.sum()) == int(centers.pixel_center_count.sum()),
        "Selected cell centers conserved",
    )
    for source in pair["sources"]:
        check_file(cache / source["filename"], source)
    report = {
        "status": "fixed_pilot_pair_scan_geometry_verified_not_daily_acceptance",
        "queue_sha256": queue_sha,
        "sample_id": pair["sample_id"],
        "source_nominal_day": pair["source_day"],
        "grid_ids": parts.grid_id.tolist(),
        "scan_count": len(times),
        "scan_grid_rows": len(frame),
        "raw_source_sha256": {s["filename"]: s["sha256"] for s in pair["sources"]},
        "selected_pixel_center_count": int(frame.pixel_center_count.sum()),
        "artifact_sha256": {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()},
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "labels_created": False,
        "model_ready": False,
    }
    write_json(out / "readback.json", report)
    write_json(
        out / "completion_readback.json",
        {"status": "passed", "report_sha256": digest(out / "readback.json")},
    )
    return read_completed(out, pair, queue_sha)
