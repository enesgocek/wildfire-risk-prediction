"""Spatial support diagnostics for listed approximate swaths; never label admission."""

import numpy as np
import shapely

from wildfire_risk_prediction.feature_join import require


def overlap_bounds(domain, land, cloud):
    """Area-only bounds for two subsets of the same reconstructed domain, in m²."""
    domain, land, cloud = np.broadcast_arrays(
        np.asarray(domain, dtype=float),
        np.asarray(land, dtype=float),
        np.asarray(cloud, dtype=float),
    )
    require(
        np.isfinite([domain, land, cloud]).all()
        and (domain >= 0).all()
        and (land >= 0).all()
        and (cloud >= 0).all()
        and (land <= domain).all()
        and (cloud <= domain).all(),
        "Finite subset areas in one domain required",
    )
    return np.maximum(0, land + cloud - domain), np.minimum(land, cloud)


def spatial_support(swaths):
    """Union and area seen in at least two listed granules, not independent passes.

    Arrays contain one geometry per grid cell, in the same projected CRS/order.
    A repeated polygon contributes once regardless of swath multiplicity.
    """
    require(bool(swaths), "At least one spatial swath required")
    arrays = [np.asarray(g, dtype=object) for g in swaths]
    size = len(arrays[0])
    require(size > 0 and all(g.shape == (size,) for g in arrays), "Aligned geometry arrays")
    for g in arrays:
        require(
            not shapely.is_missing(g).any() and shapely.is_valid(g).all(),
            "Valid explicit geometries required",
        )
    union = np.full(size, shapely.GeometryCollection(), dtype=object)
    repeated = union.copy()
    maximum = np.zeros(size)
    for g in arrays:
        repeated = shapely.union(repeated, shapely.intersection(union, g))
        union = shapely.union(union, g)
        maximum = np.maximum(maximum, shapely.area(g))
    return union, repeated, maximum
