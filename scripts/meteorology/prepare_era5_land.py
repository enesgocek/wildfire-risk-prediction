"""Native ERA5-Land extraction and AOI-area-weighted retrospective features.

Commands are explicit: weights is local; download contacts EE; prepare is local.
No label creation, source-cell interpolation or final-test access.
"""

import argparse
import hashlib
import json
import math
import os
import urllib.request
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from dotenv import load_dotenv
from rasterio.transform import Affine
from shapely.geometry import box
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "data/interim/grid_aoi_parts.geojson"
RAW = ROOT / "data/raw/meteorology/era5_land_daily"
INTERIM = ROOT / "data/interim/meteorology"
REPORTS = ROOT / "outputs/reports/meteorology"
SOURCE = "ECMWF/ERA5_LAND/HOURLY"
VERSION = "era5_land_past_v1"
FEATURES = [
    "temperature_mean_c",
    "temperature_min_c",
    "temperature_max_c",
    "dewpoint_mean_c",
    "wind_speed_mean_ms",
    "wind_speed_max_ms",
    "soil_water_layer_1_mean",
    "rain_24h_raw_mm",
    "rain_72h_raw_mm",
    "rain_168h_raw_mm",
    "rain_336h_raw_mm",
    "rain_negative_hours_24h_mean",
    "rain_negative_hours_336h_mean",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def days(start, end):
    first, stop = date.fromisoformat(start), date.fromisoformat(end)
    if not date(2018, 1, 1) <= first < stop <= date(2025, 1, 1):
        raise ValueError("Only prediction dates in 2018–2024; end is exclusive.")
    while first < stop:
        yield first
        first += timedelta(days=1)


def window(target, hours):
    """Source timestamps [T-hours,T); precipitation ends at T-1h."""
    return target - timedelta(hours=hours), target


def layout(parts):
    west, south, east, north = parts.to_crs(4326).total_bounds
    col0 = math.floor((west + 180.05) / 0.1) - 1
    col1 = math.ceil((east + 180.05) / 0.1) + 1
    row0 = math.floor((90.05 - north) / 0.1) - 1
    row1 = math.ceil((90.05 - south) / 0.1) + 1
    transform = Affine(0.1, 0, -180.05 + col0 * 0.1, 0, -0.1, 90.05 - row0 * 0.1)
    return transform, row1 - row0, col1 - col0


def weights():
    parts = gpd.read_file(PARTS).to_crs(6933).sort_values("grid_id").reset_index(drop=True)
    if len(parts) != 2899 or not parts.grid_id.is_unique:
        raise ValueError("Expected the 2,899 unique pilot AOI parts.")
    if not parts.geometry.is_valid.all() or parts.geometry.is_empty.any():
        raise ValueError("Invalid or empty AOI parts.")
    transform, height, width = layout(parts)
    pixels = []
    for row in range(height):
        for col in range(width):
            left, top = transform * (col, row)
            right, bottom = transform * (col + 1, row + 1)
            pixels.append(box(left, bottom, right, top))
    native = gpd.GeoSeries(pixels, crs=4326).to_crs(6933)
    tree = STRtree(native.array)
    records = []
    for grid_index, geom in enumerate(parts.geometry):
        for pixel_index in tree.query(geom, predicate="intersects"):
            area = geom.intersection(native.iloc[pixel_index]).area
            if area > 0:
                records.append((grid_index, int(pixel_index), area))
    table = pd.DataFrame(records, columns=["grid_index", "pixel_index", "area_m2"])
    summed = table.groupby("grid_index").area_m2.sum().reindex(range(len(parts)), fill_value=0)
    areas = parts.geometry.area.to_numpy()
    if not np.allclose(summed, areas, rtol=1e-7, atol=0.01):
        raise ValueError("Native-pixel overlaps do not cover every AOI part.")
    INTERIM.mkdir(parents=True, exist_ok=True)
    path = INTERIM / "era5_land_area_weights.csv"
    table.to_csv(path, index=False)
    grids = INTERIM / "era5_land_grid_areas.csv"
    pd.DataFrame({"grid_id": parts.grid_id, "area_m2": areas}).to_csv(grids, index=False)
    manifest = {
        "version": VERSION,
        "source": SOURCE,
        "parts_sha256": sha(PARTS),
        "weights_sha256": sha(path),
        "grid_areas_sha256": sha(grids),
        "crs": "EPSG:4326",
        "transform": list(transform)[:6],
        "height": height,
        "width": width,
        "grid_count": len(parts),
        "intersection_count": len(table),
        "calculation_crs": "EPSG:6933",
        "max_area_relative_error": float(np.max(np.abs(summed - areas) / areas)),
        "policy": "AOI-part/native-pixel intersection weights; no nearest-land filling",
    }
    write_json(INTERIM / "era5_land_weights_manifest.json", manifest)
    print(json.dumps(manifest, indent=2))


def read_weights():
    manifest = json.loads((INTERIM / "era5_land_weights_manifest.json").read_text())
    if manifest.get("source") != SOURCE or manifest.get("version") != VERSION:
        raise ValueError("Weights source/version mismatch.")
    if manifest["parts_sha256"] != sha(PARTS):
        raise ValueError("AOI parts changed; rebuild weights.")
    for name, key in [
        ("era5_land_area_weights.csv", "weights_sha256"),
        ("era5_land_grid_areas.csv", "grid_areas_sha256"),
    ]:
        if sha(INTERIM / name) != manifest[key]:
            raise ValueError("Weights changed; rebuild and audit.")
    return manifest


def daily_image(ee, target, projection):
    target_time = datetime.combine(target, datetime.min.time(), tzinfo=UTC)
    long_start, stop = window(target_time, 336)
    recent_start, _ = window(target_time, 24)
    t = ee.Date(stop.isoformat())
    source = ee.ImageCollection(SOURCE).filterDate(long_start.isoformat(), t)
    recent = source.filterDate(recent_start.isoformat(), t)
    counts = ee.Dictionary(
        {
            "long_hours": source.size(),
            "recent_hours": recent.size(),
            "unique_hours": source.aggregate_count_distinct("system:time_start"),
            "first_ms": source.aggregate_min("system:time_start"),
            "last_ms": source.aggregate_max("system:time_start"),
        }
    ).getInfo()
    expected = {
        "long_hours": 336,
        "recent_hours": 24,
        "unique_hours": 336,
        "first_ms": int(long_start.timestamp() * 1000),
        "last_ms": int((stop - timedelta(hours=1)).timestamp() * 1000),
    }
    if counts != expected:
        raise ValueError(f"Incomplete source timestamps for {target}: {counts}")

    def complete(collection, band, expected):
        return collection.select(band).count().eq(expected)

    temperature = recent.select("temperature_2m")
    temp_mask = complete(recent, "temperature_2m", 24)
    images = [
        temperature.mean().subtract(273.15).updateMask(temp_mask),
        temperature.min().subtract(273.15).updateMask(temp_mask),
        temperature.max().subtract(273.15).updateMask(temp_mask),
        recent.select("dewpoint_temperature_2m")
        .mean()
        .subtract(273.15)
        .updateMask(complete(recent, "dewpoint_temperature_2m", 24)),
    ]

    def speed(image):
        return (
            image.select("u_component_of_wind_10m")
            .pow(2)
            .add(image.select("v_component_of_wind_10m").pow(2))
            .sqrt()
            .rename("speed")
            .copyProperties(image, ["system:time_start"])
        )

    wind = recent.map(speed)
    wind_mask = complete(wind, "speed", 24)
    images.extend(
        [
            wind.mean().updateMask(wind_mask),
            wind.max().updateMask(wind_mask),
            recent.select("volumetric_soil_water_layer_1")
            .mean()
            .updateMask(complete(recent, "volumetric_soil_water_layer_1", 24)),
        ]
    )
    for hours in [24, 72, 168, 336]:
        rain = source.filterDate(t.advance(-hours, "hour"), t)
        mask = complete(rain, "total_precipitation_hourly", hours)
        images.append(
            rain.select("total_precipitation_hourly").sum().multiply(1000).updateMask(mask)
        )
    for hours in [24, 336]:
        rain = source.filterDate(t.advance(-hours, "hour"), t)
        negative = rain.map(lambda image: image.select("total_precipitation_hourly").lt(0))
        images.append(
            negative.sum().updateMask(complete(rain, "total_precipitation_hourly", hours))
        )
    return ee.Image.cat(images).rename(FEATURES).setDefaultProjection(projection)


def download(start, end):
    import ee

    requested = list(days(start, end))  # Guard before any remote request.
    manifest = read_weights()
    load_dotenv(ROOT / ".env")
    project = os.environ.get("GEE_PROJECT_ID")
    if not project:
        raise ValueError("GEE_PROJECT_ID is missing from .env.")
    ee.Initialize(project=project)
    original = ee.Image(
        ee.ImageCollection(SOURCE).filterDate("2018-01-01", "2018-01-01T01:00:00").first()
    )
    projection = original.select("temperature_2m").projection()
    info = projection.getInfo()
    if info["crs"] != "EPSG:4326" or not np.allclose(
        info["transform"], [0.1, 0, -180.05, 0, -0.1, 90.05], atol=1e-9, rtol=0
    ):
        raise ValueError("Unexpected native source grid.")
    RAW.mkdir(parents=True, exist_ok=True)
    for target in requested:
        output = RAW / f"{target.isoformat()}.tif"
        metadata = output.with_suffix(".json")
        if output.exists() and metadata.exists():
            verify_archive(output, target, manifest)
            print("Already verified:", target, flush=True)
            continue
        image = daily_image(ee, target, projection).unmask(-9999, False).toFloat()
        url = image.getDownloadURL(
            {
                "crs": manifest["crs"],
                "crs_transform": manifest["transform"],
                "dimensions": [manifest["width"], manifest["height"]],
                "format": "GEO_TIFF",
                "filePerBand": False,
            }
        )
        temporary = output.with_suffix(".part")
        with urllib.request.urlopen(url, timeout=300) as response, temporary.open("wb") as stream:
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
        verify_raster(temporary, manifest)
        temporary.replace(output)
        write_json(
            metadata,
            {
                "source": SOURCE,
                "version": VERSION,
                "prediction_date": target.isoformat(),
                "downloaded_at_utc": datetime.now(UTC).isoformat(),
                "available_at": None,
                "usage": "retrospective_reanalysis_only",
                "source_timestamp_end_exclusive": target.isoformat() + "T00:00:00Z",
                "precipitation_interval_end_utc": (
                    datetime.combine(target, datetime.min.time()) - timedelta(hours=1)
                ).isoformat()
                + "Z",
                "features": FEATURES,
                "weights_manifest": manifest,
                "sha256": sha(output),
            },
        )
        print("Downloaded and verified:", target, flush=True)


def verify_archive(path, target, manifest):
    """Reject a valid file hash paired with the wrong date, schema or source."""
    saved = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    target_time = datetime.combine(target, datetime.min.time(), tzinfo=UTC)
    expected = {
        "source": SOURCE,
        "version": VERSION,
        "prediction_date": target.isoformat(),
        "features": FEATURES,
        "available_at": None,
        "usage": "retrospective_reanalysis_only",
        "source_timestamp_end_exclusive": target.isoformat() + "T00:00:00Z",
        "precipitation_interval_end_utc": (target_time - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "weights_manifest": manifest,
        "sha256": sha(path),
    }
    for key, value in expected.items():
        if key not in saved or saved[key] != value:
            raise ValueError(f"Raster provenance mismatch ({key}): {path.name}")
    verify_raster(path, manifest)


def verify_raster(path, manifest):
    with rasterio.open(path) as src:
        if src.count != len(FEATURES) or src.crs is None or src.crs.to_epsg() != 4326:
            raise ValueError("Unexpected meteorology raster bands or CRS.")
        if (src.height, src.width) != (manifest["height"], manifest["width"]):
            raise ValueError("Unexpected raster dimensions.")
        if not np.allclose(list(src.transform)[:6], manifest["transform"], atol=1e-9, rtol=0):
            raise ValueError("Raster/native grid misalignment.")
        if not np.isfinite(src.read()).all():
            raise ValueError("Non-finite raster values.")


def area_mean(values, grid_index, pixel_index, areas, totals):
    selected = values[pixel_index]
    valid = np.isfinite(selected) & (selected != -9999)
    denominator = np.bincount(grid_index[valid], weights=areas[valid], minlength=len(totals))
    numerator = np.bincount(
        grid_index[valid], weights=selected[valid] * areas[valid], minlength=len(totals)
    )
    mean = np.divide(
        numerator, denominator, out=np.full(len(totals), np.nan), where=denominator > 0
    )
    fraction = denominator / totals
    if np.any(fraction > 1 + 1e-7):
        raise ValueError("Valid-area fraction exceeds 1.")
    return mean, np.minimum(fraction, 1)


def prepare(start, end):
    requested = list(days(start, end))
    manifest = read_weights()
    weights_table = pd.read_csv(INTERIM / "era5_land_area_weights.csv")
    grids = pd.read_csv(INTERIM / "era5_land_grid_areas.csv")
    gi = weights_table.grid_index.to_numpy(dtype=int)
    pi = weights_table.pixel_index.to_numpy(dtype=int)
    areas = weights_table.area_m2.to_numpy()
    totals = grids.area_m2.to_numpy()
    summaries = []
    for target in requested:
        path = RAW / f"{target.isoformat()}.tif"
        verify_archive(path, target, manifest)
        with rasterio.open(path) as src:
            values = src.read().reshape(len(FEATURES), -1)
        table = grids[["grid_id"]].copy()
        table["prediction_timestamp_utc"] = target.isoformat() + "T00:00:00Z"
        table["source_last_timestamp_utc"] = (
            datetime.combine(target, datetime.min.time()) - timedelta(hours=1)
        ).isoformat() + "Z"
        table["available_at"] = None
        table["source_collection"] = SOURCE
        table["processing_version"] = VERSION
        target_time = datetime.combine(target, datetime.min.time(), tzinfo=UTC)
        table["weather_source_window_start_utc"] = window(target_time, 24)[0].isoformat()
        table["weather_source_window_end_exclusive_utc"] = target_time.isoformat()
        table["rain_interval_end_utc"] = (target_time - timedelta(hours=1)).isoformat()
        for hours in [24, 72, 168, 336]:
            table[f"rain_{hours}h_interval_start_exclusive_utc"] = (
                target_time - timedelta(hours=hours + 1)
            ).isoformat()
        for index, feature in enumerate(FEATURES):
            mean, fraction = area_mean(values[index], gi, pi, areas, totals)
            table[feature] = mean
            table[feature + "_valid_area_fraction"] = fraction
        if table.duplicated(["grid_id", "prediction_timestamp_utc"]).any():
            raise ValueError("Duplicate feature keys.")
        output = INTERIM / "daily" / f"{target.isoformat()}.csv"
        output.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(output, index=False)
        summary = {
            "date": target.isoformat(),
            "row_count": len(table),
            "sha256": sha(output),
            "zero_valid_area_by_feature": {f: int(table[f].isna().sum()) for f in FEATURES},
            "minimum_valid_area_fraction_by_feature": {
                f: float(table[f + "_valid_area_fraction"].min()) for f in FEATURES
            },
            "negative_raw_rain_grid_count": {
                f: int(table[f].lt(0).sum()) for f in FEATURES if "raw_mm" in f
            },
        }
        write_json(REPORTS / f"{target.isoformat()}.json", summary)
        summaries.append(summary)
        print("Prepared:", target, "rows:", len(table), flush=True)
    write_json(
        REPORTS / f"preparation_{start}_{end}.json",
        {
            "source": SOURCE,
            "version": VERSION,
            "days": summaries,
            "spatial_policy": "Area-weighted over valid native-pixel/AOI-part intersections",
            "rain_policy": "Raw hourly values preserved; negative-hour counts reported",
            "temporal_policy": "Instantaneous timestamps [T-24h,T); rain (T-hours-1h,T-1h]",
            "area_max_policy": "Spatial mean of pixel-wise temporal maximum, not regional maximum",
            "available_at": None,
            "usage": "retrospective_reanalysis_only",
            "eligibility_threshold": None,
            "final_test_accessed": False,
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["weights", "download", "prepare"])
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--end", default="2018-01-03", help="Exclusive end; at most 2025-01-01")
    args = parser.parse_args()
    if args.command == "weights":
        weights()
    elif args.command == "download":
        download(args.start, args.end)
    else:
        prepare(args.start, args.end)


if __name__ == "__main__":
    main()
