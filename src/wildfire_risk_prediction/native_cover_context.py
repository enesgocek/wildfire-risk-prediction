"""Bounded native-center support and old-map overlap diagnostics, never fire truth."""

import numpy as np
from pyproj import Transformer
from rasterio.windows import Window
from shapely.geometry import Point, Polygon

from wildfire_risk_prediction.point_cover_context import cover_group


def rounded_coordinate_matches(latitude, longitude, sparse_lat, sparse_lon):
    """Return every five-decimal archive match; callers must preserve ambiguity."""
    lat, lon = np.asarray(sparse_lat, dtype=float), np.asarray(sparse_lon, dtype=float)
    if lat.shape != lon.shape or lat.ndim != 1:
        raise ValueError("Aligned one-dimensional sparse coordinates required")
    if not np.isfinite([latitude, longitude]).all() or abs(latitude) > 90 or abs(longitude) > 180:
        raise ValueError("Valid archive coordinate required")
    return np.flatnonzero(
        (np.abs(lat - latitude) <= 0.000005000001) & (np.abs(lon - longitude) <= 0.000005000001)
    )


def center_patch_polygon(lon, lat, native_row):
    """Approximate four corners using a 3x3 patch wholly inside one 32-line scan."""
    lon, lat = np.asarray(lon, dtype=float), np.asarray(lat, dtype=float)
    if native_row < 0 or int(native_row) != native_row:
        raise ValueError("Nonnegative integer native row required")
    if native_row % 32 in (0, 31):
        raise ValueError("Scan boundary has no same-scan surrounding patch")
    if lon.shape != (3, 3) or lat.shape != (3, 3):
        raise ValueError("Complete 3x3 patch required")
    if not (np.isfinite(lon).all() and np.isfinite(lat).all()):
        raise ValueError("Finite neighboring coordinates required")
    if not ((20 <= lon).all() and (lon <= 40).all() and (30 <= lat).all() and (lat <= 45).all()):
        raise ValueError("Patch outside bounded working envelope")
    x, y = Transformer.from_crs(4326, 6933, always_xy=True).transform(lon, lat)
    centers = np.stack([x, y], axis=-1)
    corners = [
        centers[i : i + 2, j : j + 2].mean(axis=(0, 1)) for i, j in [(0, 0), (0, 1), (1, 1), (1, 0)]
    ]
    polygon = Polygon(corners)
    if not polygon.is_valid or polygon.area <= 0 or np.ptp(corners, axis=0).max() > 10000:
        raise ValueError("Invalid or excessively wide approximate support")
    if not polygon.covers(Point(x[1, 1], y[1, 1])):
        raise ValueError("Approximate support does not cover its native center")
    return polygon


def overlap_reference_map(polygon, dataset):
    """Intersect projected map-cell quadrilaterals with approximate support in EPSG:6933."""
    if dataset.crs is None or dataset.crs.to_epsg() != 3857:
        raise ValueError("Retained EPSG:3857 reference map required")
    if dataset.transform.b != 0 or dataset.transform.d != 0:
        raise ValueError("North-up retained map required")
    if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
        raise ValueError("Nonempty valid support required")
    to_map = Transformer.from_crs(6933, 3857, always_xy=True)
    to_area = Transformer.from_crs(3857, 6933, always_xy=True)
    coords = np.asarray(polygon.exterior.coords)
    mx, my = to_map.transform(coords[:, 0], coords[:, 1])
    top, left = dataset.index(min(mx), max(my))
    bottom, right = dataset.index(max(mx), min(my))
    top, left = max(0, top - 1), max(0, left - 1)
    bottom, right = min(dataset.height - 1, bottom + 1), min(dataset.width - 1, right + 1)
    areas = {}
    if top <= bottom and left <= right:
        values = dataset.read(
            1, window=Window(left, top, right - left + 1, bottom - top + 1), masked=True
        )
        for row, col in np.ndindex(values.shape):
            if np.ma.is_masked(values[row, col]):
                continue
            group = cover_group(int(values[row, col]))
            if group == "unknown_or_unmapped":
                continue
            r, c = row + top, col + left
            corners = [
                (
                    dataset.transform.a * cc + dataset.transform.c,
                    dataset.transform.e * rr + dataset.transform.f,
                )
                for cc, rr in [(c, r), (c + 1, r), (c + 1, r + 1), (c, r + 1)]
            ]
            x, y = to_area.transform(*np.asarray(corners).T)
            overlap = polygon.intersection(Polygon(zip(x, y, strict=True))).area
            areas[group] = areas.get(group, 0.0) + overlap
    mapped = sum(areas.values())
    if mapped > polygon.area + max(1e-5, polygon.area * 1e-8):
        raise ValueError("Reference-map overlap exceeds support")
    forest_shrub = areas.get("forest", 0.0) + areas.get("shrub", 0.0)
    return {
        "approximate_support_area_m2": polygon.area,
        "mapped_reference_area_m2": mapped,
        "unknown_or_outside_reference_area_m2": max(0.0, polygon.area - mapped),
        "forest_shrub_reference_area_m2": forest_shrub,
        "forest_shrub_fraction_of_mapped_area": forest_shrub / mapped if mapped else np.nan,
        "forest_shrub_fraction_of_entire_support": forest_shrub / polygon.area,
        "reference_cover_groups": sorted(k for k, value in areas.items() if value > 1e-6),
    }
