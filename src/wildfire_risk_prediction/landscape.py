"""Landscape summaries with explicit support and retrospective provenance."""

from datetime import timedelta

import numpy as np
import pandas as pd

VERSION = "landscape_retro_v1"
FOREST_CODES = [*range(111, 117), *range(121, 127)]
CLASS_CODES = [0, 20, 30, 40, 50, 60, 70, 80, 90, 100, *FOREST_CODES, 200]
COVER_FEATURES = [
    "forest_fraction",
    "shrub_fraction",
    "herbaceous_fraction",
    "agriculture_fraction",
    "urban_fraction",
    "water_fraction",
    "natural_vegetation_fraction",
]
TERRAIN_FEATURES = [
    "elevation_mean_m",
    "elevation_std_m",
    "slope_mean_deg",
    "northness_mean",
    "eastness_mean",
]


def validate_cover(frame, grid_ids):
    """Check source class fractions and derivations without selecting habitat."""
    result = frame.copy(deep=True)
    if not result.grid_id.is_unique or set(result.grid_id) != set(grid_ids):
        raise ValueError("Landcover grid keys")
    if not result.reference_year.eq(2017).all():
        raise ValueError("Expected the frozen 2017 landcover")
    columns = [f"lc_{code}_fraction" for code in CLASS_CODES]
    values = result[columns].to_numpy(float)
    if not np.isfinite(values).all() or (values < -1e-9).any() or (values > 1 + 1e-9).any():
        raise ValueError("Landcover fraction bounds")
    if not np.allclose(values.sum(axis=1), 1, atol=1e-6, rtol=0):
        raise ValueError("Landcover fractions do not sum to one")
    expected = {
        "forest_fraction": result[[f"lc_{c}_fraction" for c in FOREST_CODES]].sum(axis=1),
        "shrub_fraction": result.lc_20_fraction,
        "herbaceous_fraction": result.lc_30_fraction,
        "agriculture_fraction": result.lc_40_fraction,
        "urban_fraction": result.lc_50_fraction,
        "water_fraction": result.lc_80_fraction + result.lc_200_fraction,
        "unknown_fraction": result.lc_0_fraction,
    }
    expected["natural_vegetation_fraction"] = (
        expected["forest_fraction"] + expected["shrub_fraction"] + expected["herbaceous_fraction"]
    )
    for name, value in expected.items():
        if not np.allclose(result[name], value, atol=1e-9, rtol=0):
            raise ValueError(f"Landcover composition: {name}")
    if not np.isfinite(result.covered_area_km2).all() or (result.covered_area_km2 <= 0).any():
        raise ValueError("Landcover area")
    return result


def terrain_summary(properties):
    """Turn area integrals into supported means; circular aspect excludes flats."""
    keys = [
        "support_m2",
        "elevation_m_m2",
        "elevation2_m2_m2",
        "slope_deg_m2",
        "aspect_support_m2",
        "northness_m2",
        "eastness_m2",
    ]
    raw = {key: properties.get(key) for key in keys}
    # Empty EE regions return null, not a measured zero elevation or slope.
    support = raw["support_m2"]
    if support is None or support == 0:
        if any(value not in (None, 0) for value in raw.values()):
            raise ValueError("Values without terrain support")
        return {
            "terrain_valid_area_m2": 0.0,
            "aspect_valid_area_m2": 0.0,
            **{name: np.nan for name in TERRAIN_FEATURES},
        }
    if not np.isfinite(support) or support < 0:
        raise ValueError("Terrain support")
    for key in keys[1:4]:
        if raw[key] is None or not np.isfinite(raw[key]):
            raise ValueError(f"Missing terrain integral: {key}")
    elevation = raw["elevation_m_m2"] / support
    second = raw["elevation2_m2_m2"] / support
    variance = second - elevation**2
    if variance < -1e-7 * max(1, second):
        raise ValueError("Negative terrain variance")
    slope = raw["slope_deg_m2"] / support
    if not -500 <= elevation <= 9000 or not 0 <= slope <= 90:
        raise ValueError("Terrain physical bounds")
    aspect_support = raw["aspect_support_m2"] or 0.0
    if not np.isfinite(aspect_support) or not 0 <= aspect_support <= support * (1 + 1e-9):
        raise ValueError("Aspect support")
    north = east = np.nan
    if aspect_support > 0:
        for key in ("northness_m2", "eastness_m2"):
            if raw[key] is None or not np.isfinite(raw[key]):
                raise ValueError("Missing aspect integral")
        north = raw["northness_m2"] / aspect_support
        east = raw["eastness_m2"] / aspect_support
        if north**2 + east**2 > 1 + 1e-7:
            raise ValueError("Aspect vector bounds")
    elif any(raw[k] not in (None, 0) for k in ("northness_m2", "eastness_m2")):
        raise ValueError("Aspect values without support")
    return {
        "terrain_valid_area_m2": float(support),
        "aspect_valid_area_m2": float(aspect_support),
        "elevation_mean_m": float(elevation),
        "elevation_std_m": float(np.sqrt(max(0, variance))),
        "slope_mean_deg": float(slope),
        "northness_mean": float(north),
        "eastness_mean": float(east),
    }


def landsat_indices(red_dn, nir_dn, swir_dn, qa_pixel, qa_radsat):
    """Landsat 8 C2 L2 scaling and strict paired NDVI/NDMI quality mask."""
    red, nir, swir = [
        np.asarray(v, dtype=float) * 0.0000275 - 0.2 for v in (red_dn, nir_dn, swir_dn)
    ]
    qa = np.asarray(qa_pixel, dtype=np.uint16)
    sat = np.asarray(qa_radsat, dtype=np.uint16)
    # Fill, dilated cloud, cirrus, cloud, shadow, snow and water.
    valid = ((qa & 0b10111111) == 0) & (sat == 0)
    valid &= (
        np.isfinite(red)
        & np.isfinite(nir)
        & np.isfinite(swir)
        & (red >= 0)
        & (nir >= 0)
        & (swir >= 0)
        & (red <= 1)
        & (nir <= 1)
        & (swir <= 1)
        & (nir + red > 0)
        & (nir + swir > 0)
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = np.where(valid, (nir - red) / (nir + red), np.nan)
        ndmi = np.where(valid, (nir - swir) / (nir + swir), np.nan)
    return ndvi, ndmi, valid


def validate_past_window(target, source_times):
    """Reject final-test dates and future acquisitions before remote requests."""
    target = pd.Timestamp(target)
    if pd.isna(target):
        raise ValueError("Prediction date missing")
    if target.tzinfo is None:
        target = target.tz_localize("UTC")
    else:
        target = target.tz_convert("UTC")
    target = target.to_pydatetime()
    if target.time().isoformat() != "00:00:00" or not 2018 <= target.year <= 2024:
        raise ValueError("Prediction must be 00:00 UTC in training/validation")
    times = pd.to_datetime(source_times, utc=True)
    if any(pd.isna(t) or t >= target or t < target - timedelta(days=60) for t in times):
        raise ValueError("Vegetation acquisition outside strict past window")
    return target
