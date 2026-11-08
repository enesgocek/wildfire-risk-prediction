"""Localize a published Salur start marker without treating it as a surveyed point."""

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from shapely.geometry import Point

from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import detection_windows

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset/public_start_geometry_v1/forestry_chamber_2021"
OLD = (
    ROOT
    / "outputs/reports/dataset/manavgat_reported_starts_v1"
    / "20261108T022757Z_358ef972/readback.json"
)
GRID = ROOT / "data/interim/grid_aoi_parts.geojson"
CATALOG = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
PINS = {
    OLD: "cf24f1c2839f3f92942de1d569644e599a84a854b76cb5263cd6e1871e3c7b9e",
    GRID: "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9",
    CATALOG: "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5",
    BASE / "source.pdf": "b5643af14874fd486fedbf82019cdca7428003983f07f8a63f2f308ec2f2dd29",
    BASE / "manavgat_presentation.pdf": (
        "ca7aa12315ff1493d18f244b5806bdb5e5400ce6cc8daeaae9d8a4662fcfa6be"
    ),
    BASE / "gurbuz-02.png": "3a4fa99ccbe8e224baaca6cdba8f8a832afcd652776fc96f40169a05d54e97e7",
    BASE / "imagery_overview.png": (
        "716439b5ec11fb2f17e6a5881bd34a76c35cabd9e554de897fc908f57eacc056"
    ),
    BASE / "imagery_overview.json": (
        "c7bd42c4800e6f4173aae067ef4c0d6aeb667e0746c14a5ebab372e0c6b3d528"
    ),
    BASE / "pre_event_ortho/visual.tif": (
        "1dbcd7837402476f7ed7029550a3ac7cf034a6ea98efc9b12740981ad41f37bd"
    ),
    BASE / "pre_event_ortho/metadata.json": (
        "bc04f228a5acb078705ec02ffd5db62d94e639b10fc8778af3b449cec541ebc2"
    ),
}

# Manual road anchors: slide pixel, 3x overview crop pixel, Sentinel pixel.
# Do not fit to the marker, shoreline (water levels differ), or any fire detection.
ANCHORS = (
    ((941, 238), (308, 308), (273, 440)),
    ((1153, 250), (468, 306), (302, 439)),
    ((1079, 417), (416, 442), (289, 461)),
    ((625, 492), (114, 509), (235, 476)),
    ((727, 208), (160, 286), (243, 435)),
    ((699, 700), (183, 657), (247, 503)),
)
MARKER = (1009, 321, 1)  # Approximate pin tip; slide 2 at 125 dpi.
RADII_M = (50, 100, 250, 500, 1000)
ISTANBUL = ZoneInfo("Europe/Istanbul")
OUTBREAK = datetime(2021, 7, 28, 11, 58, tzinfo=ISTANBUL).astimezone(UTC)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def matched_positions():
    m = read(BASE / "imagery_overview.json")
    extent = m["extent"]
    require(extent["spatialReference"]["latestWkid"] == 3857, "Imagery CRS")
    to_utm = Transformer.from_crs(3857, 32636, always_xy=True)
    overview = []
    for _, (x, y), _ in ANCHORS:
        col, row = 332 + x / 3, 498 + y / 3
        overview.append(
            to_utm.transform(
                extent["xmin"] + col * (extent["xmax"] - extent["xmin"]) / m["width"],
                extent["ymax"] - row * (extent["ymax"] - extent["ymin"]) / m["height"],
            )
        )
    with rasterio.open(BASE / "pre_event_ortho/visual.tif") as src:
        require(src.crs.to_epsg() == 32636 and src.res == (10, 10), "Sentinel crop geometry")
        sentinel = [src.transform * (x, y) for _, _, (x, y) in ANCHORS]
    return {"imagery_overview": np.array(overview), "sentinel_2b_pre_event": np.array(sentinel)}


def marker_fit(positions):
    design = np.c_[[p for p, _, _ in ANCHORS], np.ones(len(ANCHORS))]

    def fit(a, b):
        coeff, _, rank, _ = np.linalg.lstsq(a, b, rcond=None)
        require(rank == 3, "Road anchors must span two dimensions")
        return coeff

    full = fit(design, positions)
    predicted = np.asarray(MARKER) @ full
    omitted_errors, marker_shifts = [], []
    for i in range(len(design)):
        part = fit(np.delete(design, i, axis=0), np.delete(positions, i, axis=0))
        omitted_errors.append(float(np.linalg.norm(design[i] @ part - positions[i])))
        marker_shifts.append(float(np.linalg.norm(np.asarray(MARKER) @ part - predicted)))
    return Point(*predicted), {
        "max_road_residual_m": float(np.linalg.norm(design @ full - positions, axis=1).max()),
        "max_omitted_road_error_m": max(omitted_errors),
        "max_marker_shift_m": max(marker_shifts),
    }


def catalogue_context(lon, lat, rows):
    _, _, distances = GEOD.inv(
        np.full(len(rows), lon),
        np.full(len(rows), lat),
        rows.longitude.to_numpy(float),
        rows.latitude.to_numpy(float),
    )
    data = list(zip(rows.timestamp, distances, strict=True))
    result = {}
    for radius in (500, 1000, 2000, 3000):
        nearby = [(t, d) for t, d in data if d <= radius]
        after = [(t, d) for t, d in nearby if t >= OUTBREAK]
        first = min(after, default=None)
        result[radius] = {
            "before_rows": len(nearby) - len(after),
            "at_or_after_rows": len(after),
            "first_utc": first[0].isoformat() if first else None,
            "first_minutes_after_report": (
                (first[0] - OUTBREAK).total_seconds() / 60 if first else None
            ),
        }
    return result


def main():
    pins = {}
    for path, expected in PINS.items():
        with path.open("rb") as file:
            actual = hashlib.file_digest(file, "sha256").hexdigest()
        require(actual == expected, f"Pinned input differs: {path.name}")
        pins[path.relative_to(ROOT).as_posix()] = actual
    old = read(OLD)["cases"][0]
    require(datetime.fromisoformat(old["reported_start_utc"]) == OUTBREAK, "Prior source clock")
    start, end, boundary = detection_windows(pd.Series([OUTBREAK.isoformat()])).iloc[0]
    require(not boundary and start < OUTBREAK <= end, "Training window only")
    with CATALOG.open(encoding="utf-8-sig", newline="") as file:
        day_keys = {start.date().isoformat(), end.date().isoformat()}
        rows = [r for r in csv.DictReader(file) if r["acq_date"] in day_keys]
    rows = training_detections(pd.DataFrame(rows))
    rows = rows[rows.timestamp.gt(start) & rows.timestamp.le(end)]
    grid = gpd.read_file(GRID).to_crs(32636)
    require(grid.grid_id.is_unique, "Grid keys")
    to_wgs = Transformer.from_crs(32636, 4326, always_xy=True)
    results, positions = {}, []
    for key, matched in matched_positions().items():
        point, fit = marker_fit(matched)
        positions.append(point)
        lon, lat = to_wgs.transform(point.x, point.y)
        cell = grid.loc[grid.geometry.covers(point)]
        require(len(cell) == 1, "Marker estimates must be in a single project cell")
        results[key] = {
            **fit,
            "marker_lon_lat": [lon, lat],
            "center_cell": cell.grid_id.iloc[0],
            "center_distance_to_cell_edge_m": float(cell.boundary.distance(point).iloc[0]),
            "distance_from_prior_map_m": GEOD.inv(lon, lat, *old["approximate_lon_lat"])[2],
            "buffer_cell_counts": {r: int(grid.intersects(point.buffer(r)).sum()) for r in RADII_M},
            "catalogue_context_by_radius_m": catalogue_context(lon, lat, rows),
        }
    receipt = {
        "status": "published_marker_cell_context_only",
        "reported_outbreak_utc": OUTBREAK.isoformat(),
        "window_start_utc": start.isoformat(),
        "window_end_utc": end.isoformat(),
        "anchor_count_per_fit": len(ANCHORS),
        "fit_separation_m": positions[0].distance(positions[1]),
        "estimates": results,
        "input_sha256": pins,
        "original_ignition_coordinate_verified": False,
        "representative_record_coverage_documented": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "target": None,
    }
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = BASE / "salur_marker_v1" / run / "readback.json"
    out.parent.mkdir(parents=True, exist_ok=False)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix())
    print(hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
