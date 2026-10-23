"""Descriptive Sentinel-2 scene quality, without habitat or fire labels."""

import math

import numpy as np
from rasterio.features import geometry_mask
from rasterio.windows import Window, from_bounds
from shapely.geometry import mapping


def bounded_window(bounds, transform, width, height, margin=500, *, clip_context=False):
    if transform.b != 0 or transform.d != 0 or transform.a <= 0 or transform.e >= 0:
        raise ValueError("North-up raster required")
    left, bottom, right, top = bounds
    core = from_bounds(left, bottom, right, top, transform=transform)
    if (
        core.col_off < 0
        or core.row_off < 0
        or core.col_off + core.width > width
        or core.row_off + core.height > height
    ):
        raise ValueError("Approximate support crosses raster boundary")
    candidate = from_bounds(
        left - margin, bottom - margin, right + margin, top + margin, transform=transform
    )
    c0, r0 = math.floor(candidate.col_off), math.floor(candidate.row_off)
    c1 = math.ceil(candidate.col_off + candidate.width)
    r1 = math.ceil(candidate.row_off + candidate.height)
    if min(c0, r0) < 0 or c1 > width or r1 > height:
        if not clip_context:
            raise ValueError("Review context crosses raster boundary")
        c0, r0, c1, r1 = max(c0, 0), max(r0, 0), min(c1, width), min(r1, height)
    if max((c1 - c0) * transform.a, (r1 - r0) * -transform.e) > 2500:
        raise ValueError("Review context size bound exceeded")
    return Window(c0, r0, c1 - c0, r1 - r0)


def support_quality(scl, valid, transform, polygon):
    if scl.ndim != 2 or valid.shape != scl.shape:
        raise ValueError("Aligned two-dimensional masks required")
    inside = geometry_mask(
        [mapping(polygon)], out_shape=scl.shape, transform=transform, invert=True, all_touched=False
    )
    total = int(inside.sum())
    if not total:
        raise ValueError("No pixel centres in approximate support")
    values = np.where(valid, scl, 0)[inside]
    if not np.isin(values, np.arange(12)).all():
        raise ValueError("Unexpected SCL code")
    counts = {str(code): int((values == code).sum()) for code in range(12)}
    return {
        "support_pixel_centres": total,
        "scl_counts": counts,
        "cloud_cirrus_fraction": sum(counts[str(i)] for i in (8, 9, 10)) / total,
        "cloud_shadow_fraction": counts["3"] / total,
        "dark_or_cast_shadow_fraction": counts["2"] / total,
        "nodata_defective_fraction": (counts["0"] + counts["1"]) / total,
        "unclassified_fraction": counts["7"] / total,
        "snow_ice_fraction": counts["11"] / total,
        "vegetation_fraction_not_forest": counts["4"] / total,
        "nonvegetated_fraction": counts["5"] / total,
        "water_fraction": counts["6"] / total,
        "quality_threshold_accepted": False,
        "habitat_accepted": False,
        "fire_label_accepted": False,
    }
