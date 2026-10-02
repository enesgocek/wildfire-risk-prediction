"""Read-only local data audit; writes only its report, never downloads or prepares data.

The weather range must already be prepared. Files outside that range are not read,
so a simultaneous download into other dates is unaffected. This audit establishes
structural integrity, not fire-label truth or operational feature availability.
"""

import argparse
import hashlib
import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Transformer

from wildfire_risk_prediction.config import load_config

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "meteorology", ROOT / "scripts/meteorology/prepare_era5_land.py"
)
met = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(met)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def check_geography():
    manifest = read_json("data/aoi/manifest.json")
    for name, relative in [
        ("aoi", "data/aoi/aoi.geojson"),
        ("grid", "data/aoi/grid_5km.geojson"),
        ("candidates", "data/interim/grid_5km_candidates.geojson"),
    ]:
        require(sha(ROOT / relative) == manifest[name + "_sha256"], f"{name}: hash mismatch")
    aoi = gpd.read_file(ROOT / "data/aoi/aoi.geojson").to_crs(6933)
    grid = gpd.read_file(ROOT / "data/aoi/grid_5km.geojson").to_crs(6933)
    parts = gpd.read_file(ROOT / "data/interim/grid_aoi_parts.geojson").to_crs(6933)
    for frame in [aoi, grid, parts]:
        require(frame.geometry.is_valid.all() and not frame.geometry.is_empty.any(), "Geometry")
    for frame in [grid, parts]:
        require(len(frame) == 2899 and frame.grid_id.is_unique, "Grid IDs/count")
    require(set(grid.grid_id) == set(parts.grid_id), "Grid/parts key mismatch")
    require(np.allclose(grid.area, 25_000_000, rtol=1e-7), "Full cell area")
    union = shapely.union_all(aoi.geometry.array)
    expected = grid.set_index("grid_id").geometry.intersection(union)
    actual = parts.set_index("grid_id").geometry.reindex(expected.index)
    require((expected.symmetric_difference(actual).area < 0.1).all(), "AOI intersections")
    require(abs(parts.area.sum() - union.area) < 1, "AOI coverage")
    require(np.allclose(parts.area / 1e6, parts.aoi_area_km2, atol=1e-5), "Stored AOI areas")
    return {"grid_count": len(grid), "aoi_area_km2": union.area / 1e6}


def check_firms():
    aoi = shapely.union_all(gpd.read_file(ROOT / "data/aoi/aoi.geojson").geometry.array)
    grid_ids = set(gpd.read_file(ROOT / "data/aoi/grid_5km.geojson").grid_id)
    transform = Transformer.from_crs(4326, 6933, always_xy=True)
    manifest = read_json("outputs/reports/firms_combined_candidates.json")
    combined = pd.read_csv(
        ROOT / "data/interim/firms_combined_candidates_2018_2024.csv", dtype="string"
    )
    require(combined.detection_id.is_unique, "Combined duplicate detection IDs")
    expected_frames = []
    for source in manifest["sources"]:
        n20 = source["sensor"] == "N20"
        prefix = "firms_noaa20" if n20 else "firms"
        pilot_path = ROOT / f"data/interim/{prefix}_pilot_2018_2024.csv"
        raw_name = "fire_archive_J1V-C2_815590.csv" if n20 else "fire_archive_SV-C2_815579.csv"
        raw_path = ROOT / "data/raw/firms" / source["request_id"] / raw_name
        prep = read_json(f"outputs/reports/{prefix}_pilot_preparation.json")
        require(sha(raw_path) == prep["source_sha256"], "FIRMS raw hash")
        for key, relative in [("aoi", "aoi.geojson"), ("grid", "grid_5km.geojson")]:
            require(sha(ROOT / "data/aoi" / relative) == prep[key + "_sha256"], "FIRMS geo hash")
        require(sha(ROOT / source["file"]) == source["sha256"], "Candidate hash")
        raw = pd.read_csv(raw_path, dtype="string")
        require(not raw.duplicated().any(), "Exact duplicate source rows")
        require(raw.satellite.eq(source["sensor"]).all(), "Source sensor")
        times = pd.to_datetime(
            raw.acq_date + " " + raw.acq_time.str.zfill(4),
            format="%Y-%m-%d %H%M",
            utc=True,
            errors="raise",
        )
        lower = pd.Timestamp("2018-04-01" if n20 else "2018-01-01", tz="UTC")
        require(
            times.ge(lower).all() and times.lt(pd.Timestamp("2025-01-01", tz="UTC")).all(),
            "FIRMS source period",
        )
        lon = pd.to_numeric(raw.longitude, errors="raise").to_numpy(float)
        lat = pd.to_numeric(raw.latitude, errors="raise").to_numpy(float)
        require(
            np.isfinite(lon).all()
            and np.isfinite(lat).all()
            and (np.abs(lon) <= 180).all()
            and (np.abs(lat) <= 90).all(),
            "Coordinates",
        )
        selected = np.flatnonzero(shapely.covers(aoi, shapely.points(lon, lat)))
        pilot = pd.read_csv(pilot_path, dtype="string")
        np.testing.assert_array_equal(pd.to_numeric(pilot.source_record_number), selected + 1)
        pd.testing.assert_frame_equal(
            pilot[list(raw.columns)].reset_index(drop=True),
            raw.iloc[selected].reset_index(drop=True),
        )
        require(len(pilot) == prep["pilot_detection_count"], "Pilot count")
        require(pilot.grid_id.isin(grid_ids).all(), "Unknown FIRMS grid")
        x, y = transform.transform(lon[selected], lat[selected])
        assigned = [
            f"E6933_5K_V1_C{int(c)}_R{int(r)}"
            for c, r in zip(np.floor(x / 5000), np.floor(y / 5000), strict=True)
        ]
        require(pilot.grid_id.tolist() == assigned, "FIRMS coordinate/grid assignment")
        np.testing.assert_array_equal(
            pd.to_datetime(pilot.detection_timestamp_utc, utc=True), times.iloc[selected]
        )
        candidates = pd.read_csv(ROOT / source["file"], dtype="string")
        expected = pilot.loc[pilot.type.eq("0") & pilot.confidence.isin(["n", "h"])]
        pd.testing.assert_frame_equal(
            candidates[list(pilot.columns)].reset_index(drop=True), expected.reset_index(drop=True)
        )
        candidates["source_sensor"] = source["sensor"]
        candidates["source_request_id"] = source["request_id"]
        candidates["detection_id"] = (
            source["sensor"] + "_" + source["request_id"] + "_" + candidates.source_record_number
        )
        expected_frames.append(candidates)
    expected = (
        pd.concat(expected_frames, ignore_index=True).astype("string").sort_values("detection_id")
    )
    pd.testing.assert_frame_equal(
        combined.sort_values("detection_id").reset_index(drop=True),
        expected[combined.columns].reset_index(drop=True),
    )
    require(len(combined) == manifest["combined_candidate_count"], "Combined count")
    train_ids = set(
        combined.loc[
            pd.to_datetime(combined.detection_timestamp_utc, utc=True).dt.year.le(2023),
            "detection_id",
        ]
    )
    grouping = read_json("outputs/reports/event_grouping_sensitivity.json")
    require(
        sha(ROOT / "data/interim/firms_combined_candidates_2018_2024.csv")
        == grouping["source_sha256"],
        "Grouping provenance",
    )
    for scenario in grouping["scenarios"]:
        folder = ROOT / "data/interim/event_grouping"
        assignment = pd.read_csv(folder / (scenario["scenario"] + "_assignments.csv"))
        clusters = pd.read_csv(folder / (scenario["scenario"] + "_clusters.csv"))
        require(
            assignment.detection_id.is_unique and set(assignment.detection_id) == train_ids,
            "Grouping must cover training only, exactly once",
        )
        counts = assignment.groupby("cluster_id").size().sort_index()
        pd.testing.assert_series_equal(
            counts, clusters.set_index("cluster_id").detection_count.sort_index(), check_names=False
        )
    return {
        "candidate_detections": len(combined),
        "training_candidates": len(train_ids),
        "grouping_scenarios_checked": len(grouping["scenarios"]),
        "labels_final": False,
    }


def check_landcover_modis():
    lc = pd.read_csv(ROOT / "data/interim/grid_landcover_2017.csv")
    grid = gpd.read_file(ROOT / "data/interim/grid_aoi_parts.geojson")
    require(lc.grid_id.is_unique and set(lc.grid_id) == set(grid.grid_id), "Landcover keys")
    fractions = lc.filter(regex=r"^lc_\d+_fraction$")
    require(np.isfinite(fractions).all().all(), "Nonfinite landcover")
    require(((fractions >= -1e-10) & (fractions <= 1 + 1e-10)).all().all(), "LC bounds")
    require(np.allclose(fractions.sum(axis=1), 1, atol=1e-6), "LC fractions sum")
    require(
        np.allclose(
            lc.natural_vegetation_fraction,
            lc.forest_fraction + lc.shrub_fraction + lc.herbaceous_fraction,
        ),
        "Natural vegetation composition",
    )
    report = read_json("outputs/reports/landcover_fractions.json")
    require(
        sha(ROOT / "data/raw/landcover/landcover_copernicus_2017.tif") == report["source_sha256"],
        "Landcover source hash",
    )
    require(abs(lc.covered_area_km2.sum() - grid.aoi_area_km2.sum()) < 0.01, "LC area")
    samples = read_json("outputs/reports/burned_area_samples_preparation.json")
    for sample in samples:
        for role in ["source", "output"]:
            require(sha(ROOT / sample[role]) == sample[role + "_sha256"], "MODIS hash")
        with (
            rasterio.open(ROOT / sample["source"]) as raw,
            rasterio.open(ROOT / sample["output"]) as prepared,
        ):
            require(raw.transform == prepared.transform, "MODIS grid changed")
            require(np.array_equal(raw.read(), prepared.read()), "MODIS values changed")
            require(
                prepared.crs
                == rasterio.crs.CRS.from_string("+proj=sinu +R=6371007.181 +units=m +no_defs"),
                "MODIS sphere",
            )
    hdf = read_json("outputs/reports/modis_native_hdf_comparison.json")
    require(sha(ROOT / hdf["source_file"]) == hdf["source_sha256"], "Native HDF hash")
    return {
        "landcover_grids": len(lc),
        "modis_raster_pairs": len(samples),
        "native_hdf_hash_verified": True,
        "limit": "Landcover statistics checked; full pixel extraction not rerun.",
    }


def check_weather(start, end):
    requested = list(met.days(start, end))
    manifest = met.read_weights()
    weights = pd.read_csv(met.INTERIM / "era5_land_area_weights.csv")
    grids = pd.read_csv(met.INTERIM / "era5_land_grid_areas.csv")
    gi, pi = weights.grid_index.to_numpy(int), weights.pixel_index.to_numpy(int)
    areas, totals = weights.area_m2.to_numpy(), grids.area_m2.to_numpy()
    summaries = []
    for day in requested:
        path = met.RAW / f"{day}.tif"
        met.verify_archive(path, day, manifest)
        output = met.INTERIM / "daily" / f"{day}.csv"
        summary = read_json(f"outputs/reports/meteorology/{day}.json")
        require(sha(output) == summary["sha256"], f"{day}: CSV hash")
        df = pd.read_csv(output)
        require(df.grid_id.equals(grids.grid_id) and df.grid_id.is_unique, f"{day}: grid keys")
        require(len(df) == summary["row_count"] and summary["date"] == str(day), "Daily report")
        require(
            df.source_collection.eq(met.SOURCE).all()
            and df.processing_version.eq(met.VERSION).all(),
            "CSV provenance",
        )
        require(df.available_at.isna().all(), "Unverified availability claim")
        t = pd.Timestamp(datetime.combine(day, datetime.min.time(), tzinfo=UTC))
        expected = {
            "prediction_timestamp_utc": t,
            "source_last_timestamp_utc": t - timedelta(hours=1),
            "weather_source_window_start_utc": t - timedelta(hours=24),
            "weather_source_window_end_exclusive_utc": t,
            "rain_interval_end_utc": t - timedelta(hours=1),
        }
        expected.update(
            {
                f"rain_{h}h_interval_start_exclusive_utc": t - timedelta(hours=h + 1)
                for h in [24, 72, 168, 336]
            }
        )
        for column, timestamp in expected.items():
            require(pd.to_datetime(df[column], utc=True).eq(timestamp).all(), f"{day}: {column}")
        with rasterio.open(path) as src:
            values = src.read().reshape(len(met.FEATURES), -1)
        for i, feature in enumerate(met.FEATURES):
            value, coverage = met.area_mean(values[i], gi, pi, areas, totals)
            np.testing.assert_allclose(df[feature], value, rtol=1e-12, atol=1e-12, equal_nan=True)
            actual_coverage = df[feature + "_valid_area_fraction"]
            np.testing.assert_allclose(actual_coverage, coverage, rtol=0, atol=1e-12)
            require(np.array_equal(df[feature].isna(), actual_coverage.eq(0)), "NaN/coverage")
            require(
                int(df[feature].isna().sum()) == summary["zero_valid_area_by_feature"][feature],
                "Missing-area report mismatch",
            )
        fraction = df.temperature_mean_c_valid_area_fraction
        summaries.append(
            {
                "date": str(day),
                "rows": len(df),
                "csv_sha256": sha(output),
                "full_temperature_coverage": int(np.isclose(fraction, 1, rtol=0, atol=1e-9).sum()),
                "zero_temperature_coverage": int(fraction.eq(0).sum()),
                "missing_any_feature": int(df[met.FEATURES].isna().any(axis=1).sum()),
                "negative_rain_24h": int(df.rain_24h_raw_mm.lt(0).sum()),
            }
        )
    return {
        "start": start,
        "end_exclusive": end,
        "days": summaries,
        "total_rows": sum(d["rows"] for d in summaries),
        "limit": "Spatial recomputation; hourly source aggregation not independently rerun.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weather-start", default="2018-01-01")
    parser.add_argument("--weather-end", default="2018-02-01")
    args = parser.parse_args()
    list(met.days(args.weather_start, args.weather_end))  # Guard before data reads.
    load_config(ROOT / "configs/project.yaml")
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "checks": {},
        "errors": {},
        "model_ready": False,
        "final_test_data_read": False,
        "open_gates": [
            "FIRMS Type provenance and event rules",
            "Negative-label observation coverage",
            "Missing/partial weather and negative rain policy",
            "Historical feature availability and vegetation source",
            "Labels, splits and end-to-end leakage tests not implemented",
        ],
    }
    checks = {
        "geography": check_geography,
        "firms": check_firms,
        "landcover_modis": check_landcover_modis,
        "meteorology": lambda: check_weather(args.weather_start, args.weather_end),
    }
    for name, action in checks.items():
        try:
            report["checks"][name] = action()
            print(f"PASS: {name}", flush=True)
        except (ValueError, AssertionError, OSError, KeyError) as error:
            report["errors"][name] = f"{type(error).__name__}: {error}"
            print(f"FAIL: {name}: {error}", flush=True)
    report["status"] = "failed" if report["errors"] else "passed_with_open_gates"
    report["code_sha256"] = {
        str(p.relative_to(ROOT)): sha(p)
        for folder in ["scripts", "src", "tests"]
        for p in sorted((ROOT / folder).rglob("*"))
        if p.suffix in {".py", ".js", ".ps1"}
    }
    output = (
        ROOT
        / "outputs/reports/quality"
        / (f"project_audit_{args.weather_start}_{args.weather_end}.json")
    )
    met.write_json(output, report)
    print(f"Report: {output}")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
