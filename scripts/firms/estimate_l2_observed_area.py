"""Scan-aware approximate area diagnostics. Never an official footprint or label mask.

Corners average four projected neighboring centers within one 32-line scan.
Outer detector rows/columns and invalid neighborhoods are left unreconstructed.
Only the listed local training swaths are processed; no daily inference is made.
"""

import argparse
import importlib.util
import json
import re
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Transformer
from rasterio.windows import Window

SPEC = importlib.util.spec_from_file_location(
    "sample_audit", Path(__file__).with_name("inspect_l2_observation_sample.py")
)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)
ROOT, OUTPUT = audit.ROOT, audit.OUTPUT
METHOD = "scan_interior_center_midpoints_v1_approximate"
GROUPS = ("reconstructed_domain", "nominal_nonfire_land", "cloud")
ROWS_PER_SCAN = 32
# Geometry sanity limit only; not an observation eligibility/label threshold.
MAX_LOCAL_SPAN_M = 10000.0


def interior_corners(x, y):
    """Return quadrilaterals for interior centers, never spanning two scans."""
    x, y = np.asarray(x, dtype="float64"), np.asarray(y, dtype="float64")
    audit.require(x.shape == y.shape and x.ndim == 2, "Coordinate shape mismatch")
    audit.require(x.shape[0] == ROWS_PER_SCAN and x.shape[1] >= 3, "Expected one scan")
    centers = np.stack([x, y], axis=-1)
    midpoints = (centers[:-1, :-1] + centers[:-1, 1:] + centers[1:, :-1] + centers[1:, 1:]) / 4.0
    corners = np.stack(
        [
            midpoints[:-1, :-1],
            midpoints[:-1, 1:],
            midpoints[1:, 1:],
            midpoints[1:, :-1],
        ],
        axis=-2,
    )
    finite = np.isfinite(corners).all(axis=(-1, -2))
    span = np.ptp(corners, axis=-2)
    valid = finite & (span.max(axis=-1) <= MAX_LOCAL_SPAN_M)
    return corners, valid


def tai93_utc(values, leap_seconds):
    values = np.asarray(values, dtype="float64")
    audit.require(np.isfinite(values).all() and (values >= 0).all(), "Invalid scan times")
    audit.require(float(leap_seconds).is_integer() and 0 <= leap_seconds <= 100, "Bad TAI offset")
    return pd.Timestamp("1993-01-01T00:00:00Z") + pd.to_timedelta(values - leap_seconds, unit="s")


def union_clipped(polygons, domain):
    """Never sum overlapping footprints. Empty inputs preserve zero area."""
    if len(polygons) == 0:
        return shapely.GeometryCollection()
    shapes = np.asarray(polygons, dtype=object)
    audit.require(shapely.is_valid(shapes).all(), "Invalid geometry before union")
    result = shapely.intersection(shapely.union_all(shapes), domain)
    audit.require(shapely.is_valid(result), "Invalid union geometry")
    audit.require(result.area <= domain.area + max(1e-5, domain.area * 1e-9), "Area exceeds AOI")
    return result


def parse_key(value):
    match = re.fullmatch(r"(?:(SNPP|N20):)?(\d{7}\.\d{4})", value)
    audit.require(match is not None, "Invalid sensor/sample key")
    sensor, key = match[1] or "SNPP", match[2]
    product = "VNP14IMG" if sensor == "SNPP" else "VJ114IMG"
    audit.product_identity(f"{product}.A{key}.002.2000000000000.nc")
    return sensor, key


def load_parts():
    path = ROOT / "data/interim/grid_aoi_parts.geojson"
    parts = gpd.read_file(path).to_crs(6933).sort_values("grid_id").reset_index(drop=True)
    audit.require(len(parts) == 2899 and parts.grid_id.is_unique, "AOI/grid keys changed")
    audit.require(
        parts.geometry.is_valid.all() and (parts.geometry.area > 0).all(), "Bad AOI parts"
    )
    areas = parts.geometry.area.to_numpy()
    audit.require(
        np.allclose(areas / 1e6, parts.aoi_area_km2, rtol=1e-7, atol=1e-7),
        "Stored AOI areas mismatch",
    )
    return path, parts


def estimate(sensor, key, parts_path, parts):
    stem = audit.sample_stem(sensor, key)
    previous_path = OUTPUT / f"{stem}_audit.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    fire = ROOT / previous["sources"]["fire"]["path"]
    geo = ROOT / previous["sources"]["geolocation"]["path"]
    audit.require(audit.product_identity(fire.name)[:3] == (sensor, "fire", key), "Wrong sample")
    audit.require(previous["sensor"] == sensor and previous["pair_key"] == key, "Wrong audit")
    audit.require(previous["script_sha256"] == audit.digest(Path(audit.__file__)), "Stale audit")
    for field, path in [
        ("aoi_sha256", ROOT / "data/aoi/aoi.geojson"),
        ("grid_sha256", ROOT / "data/aoi/grid_5km.geojson"),
    ]:
        audit.require(previous[field] == audit.digest(path), "Geography changed")
    for source in previous["sources"].values():
        audit.require(audit.digest(ROOT / source["path"]) == source["sha256"], "Source changed")
    regions = parts.geometry.to_numpy()
    tree = shapely.STRtree(regions)
    west, south, east, north = parts.total_bounds
    lonlat_bounds = gpd.GeoSeries([shapely.box(west, south, east, north)], crs=6933)
    lonlat_bounds = lonlat_bounds.to_crs(4326).total_bounds
    projection = Transformer.from_crs(4326, 6933, always_xy=True)
    pieces = {group: [[] for _ in range(len(parts))] for group in GROUPS}
    diagnostics, scan_rows = [], []
    counts = dict(scans_with_reconstructed_aoi_pixels=0, interior_aoi_polygon_count=0)
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask, qa = (audit.layer(stack, fire, n) for n in ("fire_mask", "algorithm_QA"))
        latds, londs = (
            audit.layer(stack, geo, f"geolocation_data/{n}") for n in ("latitude", "longitude")
        )
        audit.validate_pair(fire, geo, mask.tags(), latds.tags())
        audit.require(mask.shape == qa.shape == latds.shape == londs.shape, "Wrong dimensions")
        nscans = mask.height // ROWS_PER_SCAN
        audit.require(mask.height % ROWS_PER_SCAN == 0, "Incomplete scan array")
        scan_data = {
            n: audit.layer(stack, geo, f"scan_line_attributes/{n}").read(1).ravel()
            for n in (
                "scan_start_time",
                "scan_end_time",
                "ev_mid_time",
                "scan_quality",
                "sensor_mode",
            )
        }
        audit.require(all(len(v) == nscans for v in scan_data.values()), "Scan dimension mismatch")
        offset = int(latds.tags()["TAI93_leapseconds"])
        starts, ends, mids = (
            tai93_utc(scan_data[n], offset)
            for n in ("scan_start_time", "scan_end_time", "ev_mid_time")
        )
        audit.require(
            ((ends > starts) & (mids >= starts) & (mids <= ends)).all()
            and (np.diff(scan_data["scan_start_time"]) > 0).all(),
            "Bad scan ordering",
        )
        begin, finish = pd.Timestamp(previous["start_utc"]), pd.Timestamp(previous["end_utc"])
        # Six-minute granules may contain a scan crossing the nominal end.
        audit.require(
            starts.asi8.min() >= begin.value - 2_000_000_000
            and ends.asi8.max() <= finish.value + 2_000_000_000,
            "UTC/TAI conversion mismatch",
        )
        audit.require(
            np.isin(scan_data["sensor_mode"], np.arange(7)).all()
            and (scan_data["scan_quality"] >= 0).all(),
            "Invalid scan flags",
        )
        for scan in range(nscans):
            scan_rows.append(
                {
                    "scan_index": scan,
                    "first_native_row": scan * ROWS_PER_SCAN,
                    "start_utc": starts[scan].isoformat(),
                    "end_utc": ends[scan].isoformat(),
                    "ev_mid_utc": mids[scan].isoformat(),
                    "geolocation_scan_quality": int(scan_data["scan_quality"][scan]),
                    "sensor_mode": int(scan_data["sensor_mode"][scan]),
                    "nominal_granule_boundary_crossed": bool(
                        starts[scan] < begin or ends[scan] > finish
                    ),
                }
            )
            window = Window(0, scan * ROWS_PER_SCAN, mask.width, ROWS_PER_SCAN)
            lon, lat = londs.read(1, window=window), latds.read(1, window=window)
            valid = np.isfinite(lon) & np.isfinite(lat) & (abs(lon) <= 180) & (abs(lat) <= 90)
            # Scan-wide bbox prefilter; it does not discard outside-AOI pixel centers.
            vb_lon, vb_lat = lon[valid], lat[valid]
            if not len(vb_lon) or (
                vb_lon.max() < lonlat_bounds[0]
                or vb_lon.min() > lonlat_bounds[2]
                or vb_lat.max() < lonlat_bounds[1]
                or vb_lat.min() > lonlat_bounds[3]
            ):
                continue
            x, y = projection.transform(np.where(valid, lon, np.nan), np.where(valid, lat, np.nan))
            corners, eligible = interior_corners(x, y)
            bbox_min, bbox_max = np.min(corners, axis=-2), np.max(corners, axis=-2)
            candidate = eligible & (
                (bbox_max[..., 0] >= west)
                & (bbox_min[..., 0] <= east)
                & (bbox_max[..., 1] >= south)
                & (bbox_min[..., 1] <= north)
            )
            if not candidate.any():
                continue
            polygons = shapely.polygons(corners[candidate])
            audit.require(
                shapely.is_valid(polygons).all() and (shapely.area(polygons) > 0).all(),
                "Invalid reconstructed AOI polygons",
            )
            values = mask.read(1, window=window)[1:-1, 1:-1][candidate]
            quality = qa.read(1, window=window)[1:-1, 1:-1][candidate]
            audit.require((values < 10).all(), "Invalid classification")
            flags = {
                "reconstructed_domain": np.ones(len(values), dtype=bool),
                "nominal_nonfire_land": audit.diagnostic_land(values, quality),
                "cloud": values == 4,
            }
            pixel_indices, grid_indices = tree.query(polygons, predicate="intersects")
            if not len(pixel_indices):
                continue
            counts["scans_with_reconstructed_aoi_pixels"] += 1
            counts["interior_aoi_polygon_count"] += len(np.unique(pixel_indices))
            intersections = shapely.intersection(polygons[pixel_indices], regions[grid_indices])
            for group, flag in flags.items():
                keep = flag[pixel_indices] & (shapely.area(intersections) > 0)
                for index in np.unique(grid_indices[keep]):
                    subset = intersections[keep & (grid_indices == index)]
                    pieces[group][index].append(shapely.union_all(subset))
            diagnostics.append(
                {
                    "scan_index": scan,
                    "aoi_polygon_count": int(len(np.unique(pixel_indices))),
                    "scan_quality": int(scan_data["scan_quality"][scan]),
                    "sensor_mode": int(scan_data["sensor_mode"][scan]),
                    "invalid_or_large_neighborhoods_in_scan": int((~eligible).sum()),
                }
            )
    all_unions = {
        group: [union_clipped(p, region) for p, region in zip(items, regions, strict=True)]
        for group, items in pieces.items()
    }
    table, geometries = write_area_output(f"{stem}_area_estimate", parts, all_unions)
    scans_path = OUTPUT / f"{stem}_scan_times.csv"
    pd.DataFrame(scan_rows).to_csv(scans_path, index=False)
    for source in previous["sources"].values():
        audit.require(audit.digest(ROOT / source["path"]) == source["sha256"], "Source changed")
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "sensor": sensor,
        "pair_key": key,
        "method": METHOD,
        "status": "approximate_area_diagnostic_only",
        "scan_count": nscans,
        "tai93_leapseconds_from_product": offset,
        "nominal_granule_boundary_crossing_scans": sum(
            r["nominal_granule_boundary_crossed"] for r in scan_rows
        ),
        "scan_quality_histogram": pd.Series(scan_data["scan_quality"]).value_counts().to_dict(),
        "sensor_mode_histogram": pd.Series(scan_data["sensor_mode"]).value_counts().to_dict(),
        "counts": counts,
        "spatial_scan_diagnostics": diagnostics,
        "area_estimate_km2": {g: float(table[f"{g}_area_estimate_m2"].sum() / 1e6) for g in GROUPS},
        "sources": {
            "previous_audit_sha256": audit.digest(previous_path),
            "aoi_parts_sha256": audit.digest(parts_path),
            "script_sha256": audit.digest(Path(__file__)),
            "area_csv_sha256": audit.digest(OUTPUT / f"{stem}_area_estimate.csv"),
            "geometry_sha256": audit.digest(geometries),
            "scan_times_sha256": audit.digest(scans_path),
        },
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "limitations": [
            "Interpolated center midpoints, not official terrain-corrected pixel corners",
            "No certified lower/upper area bound or exact physical footprint claim",
            "Two detector-edge rows per scan and two outer columns left unreconstructed",
            "Invalid or over-10-km neighborhoods left unreconstructed; no extrapolation",
            "Nonfire-land class 5 only; thermal detections not counted as nonfire land",
            "Cloud and nonfire-land areas can overlap across scans; do not add class areas",
            "Scan quality/mode reported, not a final exclusion policy",
            "Scan start/end do not provide exact per-pixel acquisition seconds",
            "Single listed swath, no full-day or vegetation-specific coverage or labels",
        ],
    }
    destination = OUTPUT / f"{stem}_area_estimate.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {destination}", flush=True)
    return report, all_unions


def write_area_output(stem, parts, unions):
    table = pd.DataFrame({"grid_id": parts.grid_id, "aoi_area_m2": parts.geometry.area})
    frame = parts[["grid_id", "geometry"]].copy()
    geometry_path = OUTPUT / f"{stem}.gpkg"
    for group in GROUPS:
        array = np.asarray(unions[group], dtype=object)
        area = shapely.area(array)
        audit.require((area >= 0).all() and (area <= table.aoi_area_m2 + 0.1).all(), "Area range")
        table[f"{group}_area_estimate_m2"] = area
        table[f"{group}_fraction_estimate"] = area / table.aoi_area_m2
        frame.geometry = array
        frame.to_file(geometry_path, layer=group, driver="GPKG", index=False)
    for group in GROUPS[1:]:
        audit.require(
            (
                table[f"{group}_area_estimate_m2"]
                <= table.reconstructed_domain_area_estimate_m2 + 0.1
            ).all(),
            "Class area outside reconstructed domain",
        )
    table["method"] = METHOD
    table["daily_observation_status"] = "unknown"
    table["negative_label_permitted"] = False
    destination = OUTPUT / f"{stem}.csv"
    table.to_csv(destination, index=False)
    reread = pd.read_csv(destination)
    audit.require(len(reread) == len(parts) and reread.grid_id.is_unique, "Saved keys mismatch")
    audit.require(reread.negative_label_permitted.eq(False).all(), "Saved label permission")
    return table, geometry_path


def main(keys):
    parsed = [parse_key(k) for k in keys]
    audit.require(len(set(parsed)) == len(parsed), "Repeated sample")
    parts_path, parts = load_parts()
    for sensor, key in parsed:
        estimate(sensor, key, parts_path, parts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair-keys", nargs="+", default=["2019013.0100"])
    main(parser.parse_args().pair_keys)
