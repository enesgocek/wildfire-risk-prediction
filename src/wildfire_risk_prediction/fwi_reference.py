"""Native-node and matched-day helpers for an exploratory FWI reference, not fire labels."""

from datetime import UTC, datetime, timedelta

import numpy as np
from pyproj import Geod

from .feature_join import require

SOURCE_RADIUS_M = 6367470.0


def lagged_band(stamp):
    dt = datetime.fromisoformat(stamp)
    require(
        dt.tzinfo is not None
        and dt.utcoffset() == timedelta(0)
        and dt.hour == dt.minute == dt.second == dt.microsecond == 0
        and datetime(2022, 6, 2, tzinfo=UTC) <= dt <= datetime(2022, 6, 30, tzinfo=UTC),
        "Only approved June 2-30 UTC midnights",
    )
    prior = dt - timedelta(days=1)
    return prior.day, prior.date().isoformat()


def nearest_node(lon, lat, longitudes, latitudes):
    """Select by source-sphere geodesic distance, without inspecting raster validity."""
    xs, ys = np.asarray(longitudes), np.asarray(latitudes)
    require(
        xs.ndim == ys.ndim == 1
        and len(xs) > 1
        and len(ys) > 1
        and np.isfinite(xs).all()
        and np.isfinite(ys).all()
        and np.isfinite([lon, lat]).all()
        and xs.min() <= lon <= xs.max()
        and ys.min() <= lat <= ys.max(),
        "Finite point within native node extent",
    )
    xx, yy = np.meshgrid(xs, ys)
    sphere = Geod(a=SOURCE_RADIUS_M, b=SOURCE_RADIUS_M)
    _, _, distance = sphere.inv(
        np.full(xx.size, lon), np.full(yy.size, lat), xx.ravel(), yy.ravel()
    )
    tied = np.flatnonzero(np.abs(distance - distance.min()) <= 1e-6)
    index = int(tied[0])  # deterministic smallest row, then column
    row, col = np.unravel_index(index, xx.shape)
    ellipsoid = Geod(ellps="WGS84")
    _, _, alternative = ellipsoid.inv(
        np.full(xx.size, lon), np.full(yy.size, lat), xx.ravel(), yy.ravel()
    )
    return {
        "native_row": int(row),
        "native_column": int(col),
        "native_longitude": float(xx[row, col]),
        "native_latitude": float(yy[row, col]),
        "distance_on_source_sphere_m": float(distance[index]),
        "equal_distance_nodes_at_1e_minus_6_m": len(tied),
        "WGS84_distance_to_selected_node_m": float(alternative[index]),
        "same_nearest_node_using_WGS84_distance": int(np.argmin(alternative)) == index,
    }


def sample_preserving_missing(band, row, col):
    value = np.ma.asarray(band)[row, col]
    if np.ma.is_masked(value):
        return float("nan")
    return float(value) if np.isfinite(value) and value >= 0 else float("nan")


def matched_pairs(grids, stamps, source, support):
    a, b = [], []
    groups = {}
    for i, (grid, stamp, flag) in enumerate(zip(grids, stamps, support, strict=True)):
        if flag:
            groups.setdefault((grid, stamp[:7]), []).append(i)
    for group in groups.values():
        for left in group:
            if source[left]:
                for right in group:
                    if not source[right]:
                        a.append(left)
                        b.append(right)
    return np.asarray(a, dtype=int), np.asarray(b, dtype=int)


def pair_credit(values, left, right):
    if not len(left):
        return {"pairs": 0, "wins": 0, "ties": 0, "auxiliary_pair_AUC": None}
    delta = np.asarray(values)[left] - np.asarray(values)[right]
    require(np.isfinite(delta).all(), "Finite scores on the declared common pairs")
    wins, ties = int((delta > 0).sum()), int((delta == 0).sum())
    return {
        "pairs": len(left),
        "wins": wins,
        "ties": ties,
        "auxiliary_pair_AUC": (wins + ties / 2) / len(left),
    }
