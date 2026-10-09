"""Training-only Landsat NDVI/NDMI pilot with strict past images and recorded QA.

This is a retrospective feasibility check, not a completed daily time series.
Source scene acquisition times are known; their historical publication times
remain unknown. No final-test dates, labels, VM changes or Drive exports.
"""

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from pyproj import CRS

from wildfire_risk_prediction.landscape import validate_past_window

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "LANDSAT/LC08/C02/T1_L2"
VERSION = "landsat_past60_pilot_v1"
PARTS = ROOT / "data/interim/grid_aoi_parts.geojson"
RAW = ROOT / "data/raw/vegetation/landsat_pilot_v1"
OUT = ROOT / "data/interim/vegetation/pilot_v1"
REPORT = ROOT / "outputs/reports/landscape"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def indexed_image(image, ee):
    reflectance = image.select(["SR_B4", "SR_B5", "SR_B6"]).multiply(0.0000275).subtract(0.2)
    red, nir, swir = [reflectance.select(i) for i in (0, 1, 2)]
    valid = (
        image.select("QA_PIXEL")
        .bitwiseAnd(191)
        .eq(0)
        .And(image.select("QA_RADSAT").eq(0))
        .And(reflectance.gte(0).And(reflectance.lte(1)).reduce(ee.Reducer.min()))
        .And(nir.add(red).gt(0))
        .And(nir.add(swir).gt(0))
    )
    # Manual ratios retain the declared reflectance bounds; offsets are essential.
    ndvi = nir.subtract(red).divide(nir.add(red)).rename("ndvi")
    ndmi = nir.subtract(swir).divide(nir.add(swir)).rename("ndmi")
    return ndvi.addBands(ndmi).updateMask(valid).copyProperties(image, ["system:time_start"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2018-08-01")
    parser.add_argument("--cells", type=int, default=32)
    args = parser.parse_args()
    target = validate_past_window(args.date, [])
    if target.year > 2023 or not 4 <= args.cells <= 64:
        parser.error("Pilot uses training dates only and 4–64 cells")
    import ee

    load_dotenv(ROOT / ".env", override=False)
    project = os.getenv("GEE_PROJECT_ID", "").strip()
    if not project:
        raise ValueError("Earth Engine project not configured")
    ee.Initialize(project=project)
    ee.data.setDeadline(180000)
    all_parts = json.loads(PARTS.read_text(encoding="utf-8"))["features"]
    all_parts.sort(key=lambda r: r["properties"]["grid_id"])
    indexes = np.linspace(0, len(all_parts) - 1, args.cells, dtype=int)
    chosen = [all_parts[i] for i in indexes]
    chosen_ids = [r["properties"]["grid_id"] for r in chosen]
    geometry = ee.FeatureCollection(
        [
            ee.Feature(
                ee.Geometry(r["geometry"], proj="EPSG:4326", geodesic=False),
                {"grid_id": r["properties"]["grid_id"]},
            )
            for r in chosen
        ]
    )
    region = geometry.geometry()
    start = (target - timedelta(days=60)).isoformat()
    end = target.isoformat()
    collection = (
        ee.ImageCollection(SOURCE)
        .filterBounds(region)
        .filterDate(start, end)
        .sort("system:time_start")
    )
    sources = (
        collection.reduceColumns(ee.Reducer.toList(2), ["system:index", "system:time_start"])
        .get("list")
        .getInfo()
    )
    if not sources:
        raise ValueError("No past scenes; missing vegetation must not be filled")
    times = [pd.to_datetime(row[1], unit="ms", utc=True).isoformat() for row in sources]
    validate_past_window(target, times)
    indices = collection.map(lambda image: indexed_image(image, ee))
    median = indices.median()
    support = ee.Image.pixelArea().updateMask(median.select("ndvi").mask())
    image = ee.Image.cat(
        [
            support.rename("vegetation_support_m2"),
            median.select("ndvi").multiply(support).rename("ndvi_m2"),
            median.select("ndmi").multiply(support).rename("ndmi_m2"),
            indices.select("ndvi").count().multiply(support).rename("observation_count_m2"),
        ]
    ).toDouble()
    result = image.reduceRegions(
        collection=geometry,
        reducer=ee.Reducer.sum(),
        crs=CRS.from_epsg(6933).to_wkt(version="WKT1_GDAL"),
        scale=30,
        tileScale=4,
    ).getInfo()
    properties = [r["properties"] for r in result["features"]]
    if len(properties) != len(chosen_ids) or {r["grid_id"] for r in properties} != set(chosen_ids):
        raise ValueError("Vegetation pilot keys")
    areas = {r["properties"]["grid_id"]: r["properties"]["aoi_area_km2"] * 1e6 for r in chosen}
    table = []
    for prop in properties:
        area = prop.get("vegetation_support_m2") or 0.0
        if not np.isfinite(area) or area < 0:
            raise ValueError("Vegetation support")
        row = {
            "grid_id": prop["grid_id"],
            "prediction_timestamp_utc": target.isoformat(),
            "vegetation_valid_area_m2": area,
            "aoi_area_m2": areas[prop["grid_id"]],
            "vegetation_support_to_aoi_ratio": area / areas[prop["grid_id"]],
            "source_window_start_utc": start,
            "source_window_end_exclusive_utc": end,
            "available_at": None,
            "usage": "retrospective_candidate_only",
            "processing_version": VERSION,
        }
        for name, integral in [
            ("ndvi_past60_median_mean", "ndvi_m2"),
            ("ndmi_past60_median_mean", "ndmi_m2"),
            ("valid_observation_count_mean", "observation_count_m2"),
        ]:
            value = prop.get(integral)
            if area > 0 and (value is None or not np.isfinite(value)):
                raise ValueError("Vegetation integral missing")
            row[name] = value / area if area else np.nan
        if area and (
            abs(row["ndvi_past60_median_mean"]) > 1 + 1e-7
            or abs(row["ndmi_past60_median_mean"]) > 1 + 1e-7
            or row["valid_observation_count_mean"] < 1 - 1e-7
        ):
            raise ValueError("Vegetation physical bounds")
        table.append(row)
    frame = pd.DataFrame(table).sort_values("grid_id").reset_index(drop=True)
    stem = f"{target.date().isoformat()}_{args.cells}cells"
    raw = {
        "source": SOURCE,
        "version": VERSION,
        "parts_sha256": sha(PARTS),
        "prediction_timestamp_utc": target.isoformat(),
        "grid_ids": chosen_ids,
        "scene_ids": [r[0] for r in sources],
        "scene_acquisition_utc": times,
        "properties": properties,
        "available_at": None,
        "reflectance_scale": 0.0000275,
        "reflectance_offset": -0.2,
        "qa_excluded_bits": [0, 1, 2, 3, 4, 5, 7],
        "qa_radsat": "must be zero",
        "reduction_crs": "EPSG:6933",
        "reduction_scale_m": 30,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
    }
    raw_path = RAW / f"{stem}.json"
    output = OUT / f"{stem}.csv"
    if raw_path.exists() or output.exists():
        raise ValueError("Pilot files already exist; keep original results")
    save(raw_path, raw)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    reread = pd.read_csv(output)
    expected = frame.copy()
    expected["available_at"] = np.nan
    pd.testing.assert_frame_equal(expected, reread, check_dtype=False)
    summary = {
        "status": "past_vegetation_pilot_prepared",
        "cells": len(frame),
        "date": str(target.date()),
        "source_scenes": len(sources),
        "selection": "Evenly spaced sorted grid IDs; no fire labels used",
        "no_supported_vegetation_cells": int(frame.vegetation_valid_area_m2.eq(0).sum()),
        "source_acquisition_latest_utc": max(times),
        "feature_ranges": {
            f: [float(frame[f].min()), float(frame[f].max())]
            for f in ["ndvi_past60_median_mean", "ndmi_past60_median_mean"]
        },
        "raw_sha256": sha(raw_path),
        "table_sha256": sha(output),
        "past_window_verified": True,
        "final_test_accessed": False,
        "daily_time_series_complete": False,
        "historical_availability_verified": False,
        "limits": [
            "Single training date and 32 geographically distributed cells by default",
            "60-day median can lag rapid changes; policy is provisional",
            "No interpolation across unsupported cells; NaN retained",
            "Historical publication times unknown; not operational forecast validation",
            "Grid averages across supported AOI; boundary weights are approximate",
        ],
    }
    save(REPORT / f"vegetation_pilot_{stem}.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
