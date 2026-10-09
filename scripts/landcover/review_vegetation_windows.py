"""Seasonal paired 16/30/60-day vegetation checks with safe checkpoint reuse."""

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
    VERSION,
    WINDOWS,
    indexed_image,
    prediction_time,
    summary_row,
    validate_window,
)

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "data/interim/grid_aoi_parts.geojson"
RAW = ROOT / "data/raw/vegetation/seasonal_v1"
OUT = ROOT / "data/interim/vegetation/seasonal_v1"
REPORT = ROOT / "outputs/reports/landscape/seasonal_v1"
DATES = ["2018-02-01", "2018-05-01", "2018-08-01", "2018-11-01"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )
    temp.replace(path)


def selection(cells):
    all_parts = json.loads(PARTS.read_text(encoding="utf-8"))["features"]
    ids = [f["properties"]["grid_id"] for f in all_parts]
    if len(ids) != 2899 or len(set(ids)) != 2899:
        raise ValueError("Unexpected project grid identities")
    all_parts.sort(key=lambda f: f["properties"]["grid_id"])
    return [all_parts[i] for i in np.linspace(0, len(all_parts) - 1, cells, dtype=int)]


def contract(chosen):
    return {
        "version": VERSION,
        "source": SOURCE,
        "parts_sha256": sha(PARTS),
        "grid_ids": [r["properties"]["grid_id"] for r in chosen],
        "selection": "Evenly spaced sorted grid IDs, matched across dates/windows",
        "source_window": "[T-window,T); acquisition-time only, release time unknown",
        "qa_excluded_bits": [0, 1, 2, 3, 4, 5, 7],
        "qa_radsat_zero": True,
        "reflectance_scale": 0.0000275,
        "reflectance_offset": -0.2,
        "crs": "EPSG:6933",
        "scale_m": 30,
        "helper_sha256": sha(ROOT / "src/wildfire_risk_prediction/vegetation.py"),
    }


def stem(target, days, cells):
    return f"{target}_{days}days_{cells}cells"


def extract(target, days, chosen, spec):
    import ee

    t = prediction_time(target, training_only=True)
    start, _ = validate_window(t, days, [])
    key = stem(target, days, len(chosen))
    path = RAW / f"{key}.json"
    if path.exists():
        raw = json.loads(path.read_text())
        if raw["contract"] != spec or raw["date"] != target or raw["window_days"] != days:
            raise ValueError("Cached vegetation request changed")
        return key, "reused"
    begun = time.monotonic()
    regions = ee.FeatureCollection(
        [
            ee.Feature(
                ee.Geometry(r["geometry"], proj="EPSG:4326", geodesic=False),
                {"grid_id": r["properties"]["grid_id"]},
            )
            for r in chosen
        ]
    )
    images = (
        ee.ImageCollection(SOURCE)
        .filterBounds(regions.geometry())
        .filterDate(start.isoformat(), t.isoformat())
        .sort("system:time_start")
    )
    scenes = (
        images.reduceColumns(ee.Reducer.toList(2), ["system:index", "system:time_start"])
        .get("list")
        .getInfo()
    )
    times = [pd.to_datetime(r[1], unit="ms", utc=True).isoformat() for r in scenes]
    validate_window(t, days, times)
    if scenes:
        indices = images.map(lambda image: indexed_image(image, ee, t))
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
            r["properties"]
            for r in image.reduceRegions(
                collection=regions,
                reducer=ee.Reducer.sum(),
                crs=CRS.from_epsg(6933).to_wkt(version="WKT1_GDAL"),
                scale=30,
                tileScale=4,
            ).getInfo()["features"]
        ]
    else:
        properties = [{"grid_id": r["properties"]["grid_id"]} for r in chosen]
    if len(properties) != len(chosen) or {r["grid_id"] for r in properties} != set(
        spec["grid_ids"]
    ):
        raise ValueError("Vegetation response identities")
    areas = {r["properties"]["grid_id"]: r["properties"]["aoi_area_km2"] * 1e6 for r in chosen}
    for row in properties:
        summary_row(row, areas[row["grid_id"]], t, days)
    raw = {
        "contract": spec,
        "date": target,
        "window_days": days,
        "scene_ids": [r[0] for r in scenes],
        "scene_acquisition_utc": times,
        "properties": properties,
        "available_at": None,
        "elapsed_seconds": time.monotonic() - begun,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
    }
    save(path, raw)
    return key, "saved"


def prepare(args, chosen, spec):
    tables, summaries = [], []
    fingerprints = {}
    areas = {r["properties"]["grid_id"]: r["properties"]["aoi_area_km2"] * 1e6 for r in chosen}
    for target in args.dates:
        for days in WINDOWS:
            key = stem(target, days, len(chosen))
            path = RAW / f"{key}.json"
            raw = json.loads(path.read_text())
            if raw["contract"] != spec or raw["date"] != target or raw["window_days"] != days:
                raise ValueError("Vegetation source contract")
            validate_window(target, days, raw["scene_acquisition_utc"])
            if len(raw["properties"]) != len(chosen) or {
                r["grid_id"] for r in raw["properties"]
            } != set(spec["grid_ids"]):
                raise ValueError("Vegetation raw coverage")
            table = pd.DataFrame(
                [summary_row(r, areas[r["grid_id"]], target, days) for r in raw["properties"]]
            )
            table["source_acquisition_latest_utc"] = max(raw["scene_acquisition_utc"], default=None)
            table = table.sort_values("grid_id").reset_index(drop=True)
            tables.append(table)
            supported = table.valid_area_m2.gt(0)
            summaries.append(
                {
                    "date": target,
                    "window_days": days,
                    "cells": len(table),
                    "no_support_cells": int((~supported).sum()),
                    "ratio_at_least_90pct_cells": int((table.support_to_aoi_ratio >= 0.9).sum()),
                    "support_ratio_p10": float(table.support_to_aoi_ratio.quantile(0.1)),
                    "support_ratio_median": float(table.support_to_aoi_ratio.median()),
                    "latest_age_median_days": float(table.loc[supported, AGE_FIELDS[0]].median())
                    if supported.any()
                    else None,
                    "median_age_median_days": float(table.loc[supported, AGE_FIELDS[1]].median())
                    if supported.any()
                    else None,
                    "wall_seconds_measured": raw["elapsed_seconds"],
                    "source_scenes": len(raw["scene_ids"]),
                }
            )
            fingerprints[path.name] = sha(path)
    combined = pd.concat(tables, ignore_index=True)
    if combined.duplicated(["grid_id", "snapshot_cutoff_utc", "window_days"]).any():
        raise ValueError("Duplicate seasonal observations")
    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / f"snapshots_{len(chosen)}cells.csv"
    expected = combined.copy()
    expected["available_at"] = np.nan
    combined.to_csv(output, index=False)
    pd.testing.assert_frame_equal(expected, pd.read_csv(output), check_dtype=False)
    manifest = {
        "contract": spec,
        "dates": args.dates,
        "windows": list(WINDOWS),
        "raw_sha256": fingerprints,
        "table_sha256": sha(output),
        "table": output.relative_to(ROOT).as_posix(),
        "rows": len(combined),
        "final_test_accessed": False,
        "historical_availability_verified": False,
    }
    save(OUT / f"manifest_{len(chosen)}cells.json", manifest)
    summary = {
        "status": "seasonal_windows_prepared",
        "comparisons": summaries,
        "matched_cells": len(chosen),
        "snapshot_rows": len(combined),
        "manifest_sha256": sha(OUT / f"manifest_{len(chosen)}cells.json"),
        "limits": [
            "Training-only matched spatial sample, no model performance inference",
            "Support ratio includes water/QA/reflectance exclusions, not cloud rate alone",
            "Different windows summarize different pixel-time populations",
            "Fixed order and EE caching/shared resources affect measured wall times",
            "Historical release times unknown; no final test or fire labels",
        ],
    }
    save(REPORT / f"review_{len(chosen)}cells.json", summary)
    pd.DataFrame(summaries).to_csv(REPORT / f"comparisons_{len(chosen)}cells.csv", index=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["download", "prepare"])
    parser.add_argument("--cells", type=int, default=32)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--dates", nargs="+", default=DATES)
    args = parser.parse_args()
    if not 4 <= args.cells <= 64 or not 1 <= args.workers <= 2:
        parser.error("Use 4–64 cells and 1–2 workers")
    if len(set(args.dates)) != len(args.dates):
        parser.error("Duplicate review dates")
    for target in args.dates:
        prediction_time(target, training_only=True)
    chosen = selection(args.cells)
    spec = contract(chosen)
    if args.command == "prepare":
        prepare(args, chosen, spec)
        return
    import ee

    load_dotenv(ROOT / ".env", override=False)
    project = os.getenv("GEE_PROJECT_ID", "").strip()
    if not project:
        raise ValueError("Earth Engine project missing")
    ee.Initialize(project=project)
    ee.data.setDeadline(180000)
    requests = [(target, days) for target in args.dates for days in WINDOWS]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(extract, target, days, chosen, spec) for target, days in requests]
        for n, future in enumerate(as_completed(futures), 1):
            key, status = future.result()
            print(f"Seasonal {status} {n}/{len(requests)}: {key}", flush=True)


if __name__ == "__main__":
    main()
