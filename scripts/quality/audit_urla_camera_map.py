"""Measure the visible map overlay in a public Urla camera incident screenshot."""

import csv
import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import geopandas as gpd
import numpy as np
import pandas as pd
from audit_open_municipal_reference import BASE, ROOT, SPATIAL_SOURCES, URLA_DAY
from PIL import Image
from pyproj import Transformer
from scipy.signal import fftconvolve
from shapely.geometry import Point, Polygon
from shapely.ops import transform

from wildfire_risk_prediction.event_review import training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

MEDIA = BASE / "urla_media_review"
SCREEN = MEDIA / "09062022_2152_0.jpg"
ORTHO = MEDIA / "imagery_overview.png"
EXTENT = MEDIA / "imagery_overview.json"
PINS = {
    **SPATIAL_SOURCES,
    SCREEN: "0a705d59e3ee50191bb57d91dbafca2812d899da0ffff7a0a128442b4f5551e3",
    ORTHO: "b1ca9fff191a9ef06ee9a8e4b02bbf147ae9a2ae95ded668ea0d8e4f290fb2a7",
    EXTENT: "e66cbc2ee22c8b84abbe6f1d23376a96328316d6fe299f1173eed8eda0a56825",
}
TEMPLATE = (3, 111, 525, 773)
MAP_RECTANGLE = ((1, 108), (527, 108), (527, 778), (1, 778))
RED_AREA = ((1, 242), (264, 440), (64, 778), (1, 778))


def registrations(overview):
    with Image.open(SCREEN) as source:
        template = source.convert("RGB").crop(TEMPLATE).resize((261, 331))
    r, g, _ = np.array(template, dtype=float).transpose((2, 0, 1))
    x, y = np.meshgrid(np.arange(261), np.arange(331))
    red_region = (x < 137) & (y > 55) & (y > 0.68 * x + 50) & (y < -1.36 * x + 342)
    mask = ((r - g < 22) & (g > 23) & (g < 220) & ~red_region).astype(float)
    g = (g - (g * mask).sum() / mask.sum()) * mask
    template_energy = (g * g).sum()
    scores = []
    for scale in np.arange(0.49, 0.76, 0.004):
        size = tuple(round(n * scale / 2) for n in overview.size)
        grid = np.array(overview.resize(size), dtype=float)[:, :, 1]
        if any(a < b for a, b in zip(grid.shape, g.shape, strict=True)):
            continue
        numerator = fftconvolve(grid, g[::-1, ::-1], mode="valid")
        masked_sum = fftconvolve(grid, mask[::-1, ::-1], mode="valid")
        sum_squares = fftconvolve(grid**2, mask[::-1, ::-1], mode="valid")
        variance = sum_squares - masked_sum**2 / mask.sum()
        ncc = numerator / np.sqrt(np.maximum(1e-8, variance * template_energy))
        dy, dx = np.unravel_index(ncc.argmax(), ncc.shape)
        scores.append((float(ncc[dy, dx]), float(scale), int(dx * 2), int(dy * 2)))
    return sorted(scores, reverse=True)[:3]


def scenario(registration, metadata, neighborhood, cells, witnesses):
    score, scale, dx, dy = registration
    extent = metadata["extent"]
    width, height = (round(metadata[key] * scale) for key in ("width", "height"))
    to_metric = Transformer.from_crs(3857, 6933, always_xy=True)

    def point(pixel):
        col = (pixel[0] - TEMPLATE[0] + dx) / width
        row = (pixel[1] - TEMPLATE[1] + dy) / height
        return to_metric.transform(
            extent["xmin"] + col * (extent["xmax"] - extent["xmin"]),
            extent["ymax"] - row * (extent["ymax"] - extent["ymin"]),
        )

    visible = Polygon(map(point, MAP_RECTANGLE))
    red = Polygon(map(point, RED_AREA))
    unseen = neighborhood.difference(visible)
    overlaps = []
    for margin in (0, 100, 250, 500):
        in_view = neighborhood.intersection(visible).intersection(red.buffer(margin))
        conservative = in_view.union(unseen)
        overlaps.append(
            {
                "overlay_margin_project_m": margin,
                "visible_overlap_km2": in_view.area / 1e6,
                "visible_overlap_cells": int(cells.intersection(in_view).area.gt(0).sum()),
                "cells_retaining_unseen_area": int(
                    cells.intersection(conservative).area.gt(0).sum()
                ),
                "visible_overlap_catalogue_centers": sum(in_view.covers(p) for p in witnesses),
            }
        )
    return {
        "image_correlation": score,
        "scale": scale,
        "template_offset_px": [dx, dy],
        "neighborhood_area_outside_view_km2": unseen.area / 1e6,
        "neighborhood_area_km2": neighborhood.area / 1e6,
        "overlay_scenarios": overlaps,
    }


def main():
    for path, expected in PINS.items():
        with path.open("rb") as handle:
            require(hashlib.file_digest(handle, "sha256").hexdigest() == expected, path.name)
    boundary, _, grid, catalog = SPATIAL_SOURCES
    raw = json.loads(boundary.read_bytes())
    (feature,) = raw["features"]
    (ring,) = feature["geometry"]["rings"]
    require(raw["spatialReference"]["wkid"] == 4326, "Neighborhood CRS")
    to_metric = Transformer.from_crs(4326, 6933, always_xy=True)
    neighborhood = transform(to_metric.transform, Polygon(ring))
    cells = gpd.read_file(grid).to_crs(6933).geometry
    cells = cells[cells.intersects(neighborhood)]
    start = pd.Timestamp(URLA_DAY.isoformat(), tz="UTC")
    end = pd.Timestamp((URLA_DAY + timedelta(days=1)).isoformat(), tz="UTC")
    prefixes = (start.date().isoformat(), end.date().isoformat())
    with catalog.open(encoding="utf-8-sig", newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["detection_timestamp_utc"].startswith(prefixes)
        ]
    detections = training_detections(pd.DataFrame(rows))
    detections = detections[detections.timestamp.gt(start) & detections.timestamp.le(end)]
    points = [
        Point(*to_metric.transform(x, y))
        for x, y in zip(detections.longitude, detections.latitude, strict=True)
    ]
    witnesses = [p for p in points if neighborhood.covers(p)]
    metadata = json.loads(EXTENT.read_bytes())
    require(metadata["extent"]["spatialReference"]["latestWkid"] == 3857, "Reference CRS")
    with Image.open(ORTHO) as image:
        require(image.size == (metadata["width"], metadata["height"]), "Reference dimensions")
        fits = registrations(image.convert("RGB"))
    result = {
        "scope": "visible_camera_map_overlay_only",
        "input_sha256": {
            path.relative_to(ROOT).as_posix(): digest for path, digest in PINS.items()
        },
        "panel_time_display": "14:59:03",
        "camera_image_time_display": "2022-06-09 15:01:25",
        "neighborhood_catalogue_centers": len(witnesses),
        "registrations": [scenario(fit, metadata, neighborhood, cells, witnesses) for fit in fits],
        "target_admission": specification(),
    }
    out = MEDIA / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    out.mkdir(exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Output roundtrip")
    print(path.relative_to(ROOT).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
