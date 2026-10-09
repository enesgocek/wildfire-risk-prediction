"""Explicit Earth Engine terrain extraction and retrospective local assembly.

No VM changes, Drive export, habitat selection or fire labels. Cached raw
region integrals are preserved; table preparation runs without network access.
"""

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

from wildfire_risk_prediction.landscape import (
    COVER_FEATURES,
    TERRAIN_FEATURES,
    VERSION,
    terrain_summary,
    validate_cover,
)

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "data/interim/grid_aoi_parts.geojson"
GRID = ROOT / "data/aoi/grid_5km.geojson"
COVER = ROOT / "data/interim/grid_landcover_2017.csv"
COVER_RASTER = ROOT / "data/raw/landcover/landcover_copernicus_2017.tif"
RAW = ROOT / "data/raw/terrain/srtm_v1"
OUT = ROOT / "data/interim/landscape/v1"
REPORT = ROOT / "outputs/reports/landscape"
SOURCE = "USGS/SRTMGL1_003"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    temp.replace(path)


def features():
    value = json.loads(PARTS.read_text(encoding="utf-8"))["features"]
    value.sort(key=lambda f: f["properties"]["grid_id"])
    ids = [f["properties"]["grid_id"] for f in value]
    expected = {
        f["properties"]["grid_id"] for f in json.loads(GRID.read_text(encoding="utf-8"))["features"]
    }
    if len(ids) != 2899 or len(set(ids)) != 2899 or set(ids) != expected:
        raise ValueError("Pilot grid identities")
    return value


def source_contract(projection):
    return {
        "source": SOURCE,
        "version": VERSION,
        "parts_sha256": sha(PARTS),
        "grid_sha256": sha(GRID),
        "projection": projection,
        "terrain_operator": "ee.Terrain.products before geometry clipping",
        "aspect_policy": "cos/sin means; slope>0 only; no degree averaging",
        "reduction": "native CRS/transform; pixelArea integrals; EE fractional boundary weights",
        "availability": "retrospective; original historical available_at unknown",
    }


def terrain_image(ee):
    dem = ee.Image(SOURCE).select("elevation")
    terrain = ee.Terrain.products(dem)
    elevation, slope, aspect = [terrain.select(k) for k in ("elevation", "slope", "aspect")]
    mask = elevation.mask().And(slope.mask()).And(aspect.mask())
    area = ee.Image.pixelArea().updateMask(mask)
    nonflat = slope.gt(0)
    radians = aspect.multiply(np.pi / 180)
    bands = [
        area.rename("support_m2"),
        elevation.multiply(area).rename("elevation_m_m2"),
        elevation.pow(2).multiply(area).rename("elevation2_m2_m2"),
        slope.multiply(area).rename("slope_deg_m2"),
        area.updateMask(nonflat).rename("aspect_support_m2"),
        radians.cos().multiply(area).updateMask(nonflat).rename("northness_m2"),
        radians.sin().multiply(area).updateMask(nonflat).rename("eastness_m2"),
    ]
    return ee.Image.cat(bands).toDouble(), dem.projection().getInfo()


def download(args):
    import ee

    load_dotenv(ROOT / ".env", override=False)
    project = os.getenv("GEE_PROJECT_ID", "").strip()
    if not project:
        raise ValueError("Earth Engine project not configured")
    ee.Initialize(project=project)
    ee.data.setDeadline(180000)
    image, projection = terrain_image(ee)
    contract = source_contract(projection)
    RAW.mkdir(parents=True, exist_ok=True)
    meta = RAW / "source.json"
    if meta.exists() and json.loads(meta.read_text()) != contract:
        raise ValueError("Source/grid contract changed; use a new version")
    save_json(meta, contract)
    rows = features()
    chunks = [rows[i : i + args.batch_size] for i in range(0, len(rows), args.batch_size)]
    if args.limit_batches:
        chunks = chunks[: args.limit_batches]

    def get_chunk(chunk):
        ids = [r["properties"]["grid_id"] for r in chunk]
        key = hashlib.sha256("\n".join(ids).encode()).hexdigest()[:16]
        path = RAW / f"batch_{key}.json"
        if path.exists():
            cached = json.loads(path.read_text())
            if cached["contract"] != contract or cached["grid_ids"] != ids:
                raise ValueError("Cached terrain contract")
            return len(ids), "reused"
        collection = ee.FeatureCollection(
            [
                ee.Feature(
                    ee.Geometry(r["geometry"], proj="EPSG:4326", geodesic=False),
                    {"grid_id": r["properties"]["grid_id"]},
                )
                for r in chunk
            ]
        )
        for attempt in range(3):
            try:
                result = image.reduceRegions(
                    collection=collection,
                    reducer=ee.Reducer.sum(),
                    crs=projection["crs"],
                    crsTransform=projection["transform"],
                    tileScale=4,
                ).getInfo()
                break
            except Exception:
                if attempt == 2:
                    raise RuntimeError(
                        "Terrain request failed; verified batches retained"
                    ) from None
                time.sleep(2**attempt)
        properties = [r["properties"] for r in result["features"]]
        if len(properties) != len(ids) or {r["grid_id"] for r in properties} != set(ids):
            raise ValueError("Terrain response keys")
        for row in properties:
            terrain_summary(row)
        save_json(
            path,
            {
                "contract": contract,
                "grid_ids": ids,
                "properties": properties,
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
            },
        )
        return len(ids), "saved"

    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(get_chunk, chunk) for chunk in chunks]):
            count, status = future.result()
            completed += count
            print(f"Terrain {status}: {completed}/{sum(map(len, chunks))}", flush=True)


def prepare():
    rows = features()
    ids = [r["properties"]["grid_id"] for r in rows]
    cover_report = json.loads((ROOT / "outputs/reports/landcover_fractions.json").read_text())
    if sha(COVER_RASTER) != cover_report["source_sha256"]:
        raise ValueError("Landcover source changed")
    cover = validate_cover(pd.read_csv(COVER), ids).set_index("grid_id").loc[ids].reset_index()
    contract = json.loads((RAW / "source.json").read_text())
    if contract != source_contract(contract["projection"]):
        raise ValueError("Terrain source changed")
    data = {}
    raw_hashes = {}
    for path in sorted(RAW.glob("batch_*.json")):
        batch = json.loads(path.read_text())
        if batch["contract"] != contract:
            raise ValueError("Terrain batch source")
        if len(batch["properties"]) != len(batch["grid_ids"]) or {
            p["grid_id"] for p in batch["properties"]
        } != set(batch["grid_ids"]):
            raise ValueError("Terrain batch keys")
        for p in batch["properties"]:
            if p["grid_id"] in data and p != data[p["grid_id"]]:
                raise ValueError("Conflicting terrain batches")
            data[p["grid_id"]] = p
        raw_hashes[path.name] = sha(path)
    if set(data) != set(ids):
        raise ValueError(f"Incomplete terrain: {len(data)}/{len(ids)}; no final table written")
    terrain = pd.DataFrame([{"grid_id": key, **terrain_summary(data[key])} for key in ids])
    areas = pd.DataFrame(
        [
            {
                "grid_id": r["properties"]["grid_id"],
                "aoi_area_m2": r["properties"]["aoi_area_km2"] * 1e6,
            }
            for r in rows
        ]
    )
    table = cover.merge(terrain, on="grid_id", validate="one_to_one").merge(
        areas, on="grid_id", validate="one_to_one"
    )
    table["terrain_support_to_aoi_ratio"] = table.terrain_valid_area_m2 / table.aoi_area_m2
    # Keep raw ratios: EE boundary quantization and different area models can exceed one.
    table["terrain_support_close_to_aoi"] = table.terrain_support_to_aoi_ratio.between(0.99, 1.01)
    table["processing_version"] = VERSION
    table["historical_available_at"] = None
    table["usage"] = "retrospective_candidate_features_only"
    table["landcover_suitability_decided"] = False
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "grid_static.csv"
    table.to_csv(path, index=False)
    saved = pd.read_csv(path)
    pd.testing.assert_frame_equal(
        table[COVER_FEATURES + TERRAIN_FEATURES],
        saved[COVER_FEATURES + TERRAIN_FEATURES],
        check_dtype=False,
    )
    manifest = {
        "version": VERSION,
        "grid_count": len(table),
        "grid_sha256": sha(GRID),
        "parts_sha256": sha(PARTS),
        "landcover_source_sha256": sha(COVER_RASTER),
        "landcover_table_sha256": sha(COVER),
        "terrain_contract": contract,
        "terrain_batch_sha256": raw_hashes,
        "table_sha256": sha(path),
        "table": path.relative_to(ROOT).as_posix(),
        "model_candidate_features": COVER_FEATURES + TERRAIN_FEATURES,
        "landcover_reference_year": 2017,
        "final_test_accessed": False,
        "labels_created": False,
        "historical_availability_verified": False,
        "habitat_eligibility_decided": False,
    }
    save_json(OUT / "manifest.json", manifest)
    summary = {
        "status": "static_candidates_prepared",
        "grid_count": len(table),
        "terrain_no_support": int(table.terrain_valid_area_m2.eq(0).sum()),
        "terrain_support_not_close_to_aoi": int((~table.terrain_support_close_to_aoi).sum()),
        "aspect_no_support": int(table.aspect_valid_area_m2.eq(0).sum()),
        "terrain_support_ratio_range": [
            float(table.terrain_support_to_aoi_ratio.min()),
            float(table.terrain_support_to_aoi_ratio.max()),
        ],
        "feature_ranges": {
            f: [float(table[f].min()), float(table[f].max())]
            for f in COVER_FEATURES + TERRAIN_FEATURES
        },
        "manifest_sha256": sha(OUT / "manifest.json"),
        "limits": [
            "Retrospective candidate features; historical release times unknown",
            "2017 landcover is frozen and may become stale",
            "EE area weights quantize boundary overlaps; small slivers need review",
            "No fire labels or habitat thresholds; dynamic NDVI/NDMI separate",
        ],
    }
    save_json(REPORT / "static_preparation.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["download-terrain", "prepare"])
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--limit-batches", type=int, default=0)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 64 or not 1 <= args.workers <= 4 or args.limit_batches < 0:
        parser.error("Use batches 1–64 and workers 1–4")
    download(args) if args.command == "download-terrain" else prepare()


if __name__ == "__main__":
    main()
