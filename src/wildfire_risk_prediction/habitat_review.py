"""Diagnostic landcover sensitivity; never decides eligibility or fire labels."""

import numpy as np

from wildfire_risk_prediction.landscape import validate_cover

VERSION = "habitat_review_v1"
THRESHOLDS = (0.01, 0.10, 0.25, 0.50, 0.75)


def review_habitat(frame, grid_ids):
    """Keep all cells; fractions describe raster class area, not tree canopy."""
    if frame.empty:
        raise ValueError("Empty habitat input")
    cover = validate_cover(frame, grid_ids)
    if cover.grid_id.isna().any():
        raise ValueError("Missing grid key")
    if not cover.historical_available_at.isna().all():
        raise ValueError("Historical availability contract changed")
    if not cover.landcover_suitability_decided.eq(False).all():  # noqa: E712
        raise ValueError("Habitat decision already present")
    if not cover.usage.eq("retrospective_candidate_features_only").all():
        raise ValueError("Unexpected static usage")
    for column in ("aoi_area_m2", "terrain_valid_area_m2"):
        values = cover[column].to_numpy(float)
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f"Invalid area: {column}")
    if not cover.aoi_area_m2.gt(0).all():
        raise ValueError("Zero AOI area")
    ratio = cover.terrain_valid_area_m2 / cover.aoi_area_m2
    if not np.allclose(ratio, cover.terrain_support_to_aoi_ratio, rtol=0, atol=1e-9):
        raise ValueError("Terrain ratio mismatch")
    fractions = [
        "forest_fraction",
        "shrub_fraction",
        "herbaceous_fraction",
        "agriculture_fraction",
        "urban_fraction",
        "water_fraction",
        "unknown_fraction",
        "natural_vegetation_fraction",
    ]
    result = cover[["grid_id", "reference_year", "covered_area_km2", *fractions]].copy()
    result["forest_shrub_fraction"] = cover.forest_fraction + cover.shrub_fraction
    result["aoi_area_km2"] = cover.aoi_area_m2 / 1e6
    result["landcover_area_to_aoi_ratio"] = cover.covered_area_km2 / result.aoi_area_km2
    result["terrain_support_to_aoi_ratio"] = ratio
    result["terrain_area_review_flag"] = ~ratio.between(0.99, 1.01)
    result["water_only_flag"] = np.isclose(cover.water_fraction, 1, rtol=0, atol=1e-9)
    result["unknown_cover_present_flag"] = cover.unknown_fraction.gt(0)
    result["habitat_eligibility"] = "undecided"
    result["historical_availability_verified"] = False
    result["negative_label_permitted"] = False
    result["processing_version"] = VERSION
    total_area = float(result.covered_area_km2.sum())
    measures = ("forest_fraction", "forest_shrub_fraction", "natural_vegetation_fraction")
    sensitivity = []
    for measure in measures:
        for threshold in THRESHOLDS:
            mask = result[measure].ge(threshold)
            sensitivity.append(
                {
                    "measure": measure,
                    "exploratory_threshold_inclusive": threshold,
                    "cells_at_or_above": int(mask.sum()),
                    "cells_below": int((~mask).sum()),
                    "landcover_covered_area_km2_of_cells_at_or_above": float(
                        result.loc[mask, "covered_area_km2"].sum()
                    ),
                }
            )
    summary = {
        "version": VERSION,
        "grid_count": len(result),
        "rows_removed": 0,
        "aoi_area_km2": float(result.aoi_area_km2.sum()),
        "landcover_covered_area_km2": total_area,
        "class_area_km2_within_landcover_coverage": {
            name: float((result[name] * result.covered_area_km2).sum()) for name in fractions
        },
        "terrain_area_review_cells": int(result.terrain_area_review_flag.sum()),
        "terrain_area_review_aoi_km2": float(
            result.loc[result.terrain_area_review_flag, "aoi_area_km2"].sum()
        ),
        "water_only_cells": int(result.water_only_flag.sum()),
        "unknown_cover_present_cells": int(result.unknown_cover_present_flag.sum()),
        "sensitivity": sensitivity,
        "threshold_selected": None,
        "habitat_eligibility_decided": False,
        "historical_availability_verified": False,
        "labels_created": False,
        "negative_label_permitted": False,
        "final_test_accessed": False,
        "limits": [
            "2017 class map; later landcover changes and historical release unknown",
            "Class fractions are not percent tree canopy or validated habitat",
            "Exploratory thresholds are not model selection or exclusion rules",
            "Class areas use covered raster area; sensitivity reports whole cell coverage",
            "Terrain area flags use 0.99 to 1.01 only for numerical review",
            "Overlapping derived class groups must not be added together",
        ],
    }
    return result.sort_values("grid_id").reset_index(drop=True), summary
