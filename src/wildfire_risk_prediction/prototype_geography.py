"""Lossless vertex display transform for an offline cell-location overview."""

import math

from .feature_join import require


def rings(geometry):
    require(geometry["type"] in ("Polygon", "MultiPolygon"), "Polygon display geometry")
    polygons = (
        [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    )
    return [ring for polygon in polygons for ring in polygon]


def bounds(geometry):
    points = [p for ring in rings(geometry) for p in ring]
    require(
        points
        and all(
            len(p) >= 2
            and math.isfinite(p[0])
            and math.isfinite(p[1])
            and -180 <= p[0] <= 180
            and -90 <= p[1] <= 90
            for p in points
        ),
        "Finite WGS84 display vertices",
    )
    return [
        min(p[0] for p in points),
        min(p[1] for p in points),
        max(p[0] for p in points),
        max(p[1] for p in points),
    ]


def path(geometry, transform):
    pieces = []
    for ring in rings(geometry):
        points = [
            (
                (p[0] - transform["west"]) * transform["x_scale"],
                (transform["north"] - p[1]) * transform["y_scale"],
            )
            for p in ring
        ]
        require(len(points) >= 4 and ring[0] == ring[-1], "Closed polygon ring")
        pieces.append("M" + " L".join(f"{x:.6f},{y:.6f}" for x, y in points) + " Z")
    return " ".join(pieces)


def prepare(grid, aoi, requested_ids):
    require(len(grid["features"]) == 2899, "Existing full 5 km grid")
    source = {f["properties"]["grid_id"]: f for f in grid["features"]}
    require(len(source) == 2899, "Unique unchanged grid IDs")
    geometries = [f["geometry"] for f in aoi["features"]]
    extent = [bounds(g) for g in geometries]
    west, south = min(b[0] for b in extent), min(b[1] for b in extent)
    east, north = max(b[2] for b in extent), max(b[3] for b in extent)
    require(east > west and north > south, "Nonzero overview extent")
    x_scale = 960 / (east - west)
    y_scale = x_scale / math.cos(math.radians((south + north) / 2))
    # The padding keeps the full grid cells at the AOI edge visible.
    transform = {"west": west, "north": north, "x_scale": x_scale, "y_scale": y_scale}
    cells = {}
    for key in sorted(set(requested_ids) & set(source)):
        feature = source[key]
        require(feature["properties"]["cell_size_m"] == 5000, "Existing 5 km cells")
        b = bounds(feature["geometry"])
        cells[key] = {
            "path": path(feature["geometry"], transform),
            "display_bounds": [
                (b[0] - west) * x_scale,
                (north - b[3]) * y_scale,
                (b[2] - west) * x_scale,
                (north - b[1]) * y_scale,
            ],
            "wgs84_bounds": b,
        }
    height = (north - south) * y_scale
    return {
        "version": "research_cell_location_v1",
        "source_crs": "OGC:CRS84",
        "display_transform": transform,
        "study_view_box": [-20, -20, 1000, height + 40],
        "areas": [path(g, transform) for g in geometries],
        "cells": cells,
        "missing_grid_ids": sorted(set(requested_ids) - set(source)),
        "role": "cell_location_navigation_only_not_fire_location_or_risk",
        "geometry_vertices_simplified": False,
    }
