"""Bounded full-grid training snapshot with immutable request contracts and checkpoints."""

import argparse
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from pyproj import CRS

from wildfire_risk_prediction.vegetation import (
    AGE_FIELDS,
    SOURCE,
    indexed_image,
    prediction_time,
    summary_row,
    validate_window,
)

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "data/interim/grid_aoi_parts.geojson"
VERSION = "full_grid_vegetation_snapshot_v1"
WINDOWS = (30, 60)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(path)


def batches(features, size):
    if type(size) is not int or not 1 <= size <= 64:
        raise ValueError("Batch size must be 1–64")
    ids = [f["properties"]["grid_id"] for f in features]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Duplicate or empty grid")
    ordered = sorted(features, key=lambda f: f["properties"]["grid_id"])
    return [ordered[i : i + size] for i in range(0, len(ordered), size)]


def contract(target, size):
    prediction_time(target, training_only=True)
    return {
        "version": VERSION,
        "source": SOURCE,
        "target": target,
        "windows": list(WINDOWS),
        "batch_size": size,
        "parts_sha256": sha(PARTS),
        "helper_sha256": sha(ROOT / "src/wildfire_risk_prediction/vegetation.py"),
        "runner_sha256": sha(Path(__file__)),
        "qa_excluded_bits": [0, 1, 2, 3, 4, 5, 7],
        "qa_radsat_zero": True,
        "reflectance_scale": 0.0000275,
        "reflectance_offset": -0.2,
        "crs": "EPSG:6933",
        "scale_m": 30,
        "source_window": "[T-window,T); historical release unknown",
    }


def validate_raw(raw, spec, chosen, days):
    ids = [f["properties"]["grid_id"] for f in chosen]
    if raw["contract"] != spec or raw["grid_ids"] != ids or raw["window_days"] != days:
        raise ValueError("Checkpoint contract changed")
    if raw["available_at"] is not None:
        raise ValueError("Historical availability invented")
    times, scenes = raw["scene_acquisition_utc"], raw["scene_ids"]
    if len(times) != len(scenes) or len(set(scenes)) != len(scenes):
        raise ValueError("Scene identities")
    validate_window(spec["target"], days, times)
    props = raw["properties"]
    if len(props) != len(ids) or {r["grid_id"] for r in props} != set(ids):
        raise ValueError("Response grid coverage")
    areas = {f["properties"]["grid_id"]: f["properties"]["aoi_area_km2"] * 1e6 for f in chosen}
    return [summary_row(r, areas[r["grid_id"]], spec["target"], days) for r in props]


def extract(spec, chosen, days, path):
    if path.exists():
        validate_raw(json.loads(path.read_text()), spec, chosen, days)
        return "reused"
    import ee

    begun = time.monotonic()
    target = prediction_time(spec["target"], training_only=True)
    start, _ = validate_window(target, days, [])
    regions = ee.FeatureCollection(
        [
            ee.Feature(
                ee.Geometry(f["geometry"], proj="EPSG:4326", geodesic=False),
                {"grid_id": f["properties"]["grid_id"]},
            )
            for f in chosen
        ]
    )
    images = (
        ee.ImageCollection(SOURCE)
        .filterBounds(regions.geometry())
        .filterDate(start.isoformat(), target.isoformat())
        .sort("system:time_start")
    )
    scenes = (
        images.reduceColumns(ee.Reducer.toList(2), ["system:index", "system:time_start"])
        .get("list")
        .getInfo()
    )
    times = [pd.to_datetime(r[1], unit="ms", utc=True).isoformat() for r in scenes]
    validate_window(target, days, times)
    if scenes:
        indices = images.map(lambda image: indexed_image(image, ee, target))
        median = indices.median()
        area = ee.Image.pixelArea().updateMask(median.select("ndvi").mask())
        image = ee.Image.cat(
            [
                area.rename("vegetation_support_m2"),
                median.select("ndvi").multiply(area).rename("ndvi_m2"),
                median.select("ndmi").multiply(area).rename("ndmi_m2"),
                indices.select("ndvi").count().multiply(area).rename("observation_count_m2"),
                indices.select("age_days").min().multiply(area).rename("latest_age_days_m2"),
                median.select("age_days").multiply(area).rename("median_age_days_m2"),
            ]
        ).toDouble()
        properties = [
            f["properties"]
            for f in image.reduceRegions(
                collection=regions,
                reducer=ee.Reducer.sum(),
                crs=CRS.from_epsg(6933).to_wkt(version="WKT1_GDAL"),
                scale=30,
                tileScale=4,
            ).getInfo()["features"]
        ]
    else:
        properties = [{"grid_id": f["properties"]["grid_id"]} for f in chosen]
    raw = {
        "contract": spec,
        "grid_ids": [f["properties"]["grid_id"] for f in chosen],
        "window_days": days,
        "scene_ids": [r[0] for r in scenes],
        "scene_acquisition_utc": times,
        "properties": properties,
        "available_at": None,
        "elapsed_seconds": time.monotonic() - begun,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
    }
    validate_raw(raw, spec, chosen, days)
    save(path, raw)
    return "saved"


def prepare(spec, requests, output, report, wall_seconds):
    rows, fingerprints, request_seconds = [], {}, []
    for days, chosen, path in requests:
        raw = json.loads(path.read_text())
        table = pd.DataFrame(validate_raw(raw, spec, chosen, days))
        table["source_acquisition_latest_utc"] = max(raw["scene_acquisition_utc"], default=None)
        table["source_batch"] = path.name
        rows.append(table)
        fingerprints[path.relative_to(ROOT).as_posix()] = sha(path)
        request_seconds.append(raw["elapsed_seconds"])
    combined = pd.concat(rows, ignore_index=True).sort_values(["window_days", "grid_id"])
    if len(combined) != 5798 or combined.duplicated(["grid_id", "window_days"]).any():
        raise ValueError("Full-grid snapshot keys")
    output.mkdir(parents=True, exist_ok=True)
    table_path = output / "snapshots.csv"
    combined.to_csv(table_path, index=False)
    pd.testing.assert_frame_equal(
        combined.reset_index(drop=True).where(combined.notna(), np.nan),
        pd.read_csv(table_path),
        check_dtype=False,
    )
    summaries = []
    for days, table in combined.groupby("window_days"):
        present = table.valid_area_m2.gt(0)
        summaries.append(
            {
                "window_days": int(days),
                "cells": len(table),
                "no_support_cells": int((~present).sum()),
                "ratio_at_least_90pct_cells": int(table.support_to_aoi_ratio.ge(0.9).sum()),
                "support_ratio_median": float(table.support_to_aoi_ratio.median()),
                "pixel_median_age_median_days": float(table.loc[present, AGE_FIELDS[1]].median())
                if present.any()
                else None,
            }
        )
    manifest = {
        "contract": spec,
        "raw_sha256": fingerprints,
        "table": table_path.relative_to(ROOT).as_posix(),
        "table_sha256": sha(table_path),
        "rows": len(combined),
        "final_test_accessed": False,
        "historical_availability_verified": False,
    }
    save(output / "manifest.json", manifest)
    result = {
        "status": "full_grid_snapshot_prepared",
        "target": spec["target"],
        "manifest_sha256": sha(output / "manifest.json"),
        "summaries": summaries,
        "request_count": len(requests),
        "invocation_wall_seconds": wall_seconds,
        "original_request_seconds_range": [min(request_seconds), max(request_seconds)],
        "raw_bytes": sum(path.stat().st_size for _, _, path in requests),
        "table_bytes": table_path.stat().st_size,
        "daily_series_complete": False,
        "limits": [
            "Single training cutoff; not a monthly/daily series or model-quality result",
            "Historical release unknown; retrospective candidates only",
            "Shared EE resources/cache affect timing; not a cold full-period ETA",
            "Support includes water/QA/reflectance exclusions; 90pct is diagnostic only",
        ],
    }
    save(report / "preparation.json", result)
    print(json.dumps(result, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["download", "prepare"])
    parser.add_argument("--date", default="2018-08-01")
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    target = prediction_time(args.date, training_only=True).date().isoformat()
    features = json.loads(PARTS.read_text())["features"]
    if len(features) != 2899:
        raise ValueError("Unexpected full project grid")
    groups = batches(features, args.batch_size)
    spec = contract(target, args.batch_size)
    name = f"{target}_b{args.batch_size}"
    raw_root = ROOT / "data/raw/vegetation/full_grid_v1" / name
    output = ROOT / "data/interim/vegetation/full_grid_v1" / name
    report = ROOT / "outputs/reports/landscape/full_grid_v1" / name
    requests = [
        (days, group, raw_root / f"{days}days_batch_{n:03d}.json")
        for days in WINDOWS
        for n, group in enumerate(groups)
    ]
    begun = time.monotonic()
    if args.command == "download":
        import ee

        load_dotenv(ROOT / ".env", override=False)
        project = os.getenv("GEE_PROJECT_ID", "").strip()
        if not project:
            raise ValueError("Earth Engine project missing")
        ee.Initialize(project=project)
        ee.data.setDeadline(180000)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {
                pool.submit(extract, spec, group, days, path): path
                for days, group, path in requests
            }
            for n, future in enumerate(as_completed(futures), 1):
                print(
                    f"Full-grid {future.result()} {n}/{len(requests)}: {futures[future].name}",
                    flush=True,
                )
    prepare(spec, requests, output, report, time.monotonic() - begun)


if __name__ == "__main__":
    main()
