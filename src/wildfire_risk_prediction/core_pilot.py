"""Closed method-pilot bookkeeping and scan-interior geometry, never target labels."""

import numpy as np
import pandas as pd
import shapely

from wildfire_risk_prediction.feature_join import require, training_day
from wildfire_risk_prediction.observation_window import classify_intervals
from wildfire_risk_prediction.scan_support import temporal_repeat_support

GROUPS = ("reconstructed_domain", "nominal_nonfire_land", "cloud")


def source_progress(expected, completed):
    require(len(expected) == len(set(expected)) and bool(expected), "Distinct expected pairs")
    require(len(completed) == len(set(completed)), "Distinct completed pairs")
    require(set(completed) <= set(expected), "Completed pairs belong to fixed scope")
    missing = sorted(set(expected) - set(completed))
    return {
        "expected_pair_count": len(expected),
        "completed_pair_count": len(completed),
        "missing_pair_count": len(missing),
        "missing_pairs": missing,
        "all_planned_pairs_processed": not missing,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
    }


def scan_shapes(lon, lat, mask, qa, regions, transformer, corners, nominal_land):
    """Intersect one 32-line scan with selected AOI parts, retaining empty geometries."""
    require(
        lon.shape == lat.shape == mask.shape == qa.shape and lon.shape[0] == 32,
        "One aligned native scan",
    )
    require(np.isin(mask, np.arange(10)).all(), "Known native classes")
    valid = np.isfinite(lon) & np.isfinite(lat) & (abs(lon) <= 180) & (abs(lat) <= 90)
    x, y = transformer.transform(np.where(valid, lon, np.nan), np.where(valid, lat, np.nan))
    quads, eligible = corners(x, y)
    bounds = shapely.bounds(shapely.union_all(regions))
    lo, hi = np.min(quads, axis=-2), np.max(quads, axis=-2)
    use = eligible & (hi[..., 0] >= bounds[0]) & (lo[..., 0] <= bounds[2])
    use &= (hi[..., 1] >= bounds[1]) & (lo[..., 1] <= bounds[3])
    empty = {g: [shapely.GeometryCollection() for _ in regions] for g in GROUPS}
    if not use.any():
        return empty
    polygons = shapely.polygons(quads[use])
    require(
        shapely.is_valid(polygons).all() and (shapely.area(polygons) > 0).all(),
        "Valid scan-interior polygons",
    )
    values, quality = mask[1:-1, 1:-1][use], qa[1:-1, 1:-1][use]
    classes = {
        GROUPS[0]: np.ones(len(values), dtype=bool),
        GROUPS[1]: nominal_land(values, quality),
        GROUPS[2]: values == 4,
    }
    pix, cell = shapely.STRtree(regions).query(polygons, predicate="intersects")
    if not len(pix):
        return empty
    intersections = shapely.intersection(polygons[pix], regions[cell])
    positive = shapely.area(intersections) > 0
    for group, keep_class in classes.items():
        for index in range(len(regions)):
            keep = positive & (cell == index) & keep_class[pix]
            if keep.any():
                empty[group][index] = shapely.union_all(intersections[keep])
    return empty


def window_geometry(frame, geometries, region, day):
    """Classify actual times and union loaded support; absence of sources stays unknown."""
    training_day(day)
    require(frame.scan_id.is_unique, "Distinct loaded scan identities")
    shapes = np.asarray(geometries, dtype=object)
    require(len(shapes) == len(frame) and shapely.is_valid(shapes).all(), "Aligned scan shapes")
    require(
        (shapely.area(shapely.difference(shapes, region)) <= 0.05).all(),
        "Loaded geometry inside cell",
    )
    classes = classify_intervals(frame, day)
    inside = classes.eq("inside").to_numpy()
    boundary = classes.eq("boundary_unknown").to_numpy()
    admitted = shapely.union_all(shapes[inside])
    uncertain = shapely.union_all(shapes[boundary])
    repeats, pairs = temporal_repeat_support(frame, shapes, region, day)
    return {
        "loaded_inside_scan_count": int(inside.sum()),
        "loaded_boundary_scan_count": int(boundary.sum()),
        "loaded_outside_scan_count": int((~inside & ~boundary).sum()),
        "loaded_inside_area_m2": float(admitted.area),
        "loaded_boundary_area_m2": float(uncertain.area),
        "repeat_pair_count": len(pairs),
        **{f"loaded_repeat_{int(h)}h_area_m2": float(g.area) for h, g in repeats.items()},
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
    }, admitted


def expected_pairs_for_day(pairs, day):
    day = training_day(day)
    allowed = {(day + pd.Timedelta(d, unit="D")).strftime("%Y-%m-%d") for d in (-1, 0, 1)}
    result = [p["sample_id"] for p in pairs if p["source_day"] in allowed]
    require(bool(result) and len(result) == len(set(result)), "Fixed neighbour-source scope")
    return result
