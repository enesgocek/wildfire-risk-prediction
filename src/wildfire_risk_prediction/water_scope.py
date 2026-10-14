"""Researcher-approved mapped-water domain; independent of label admission."""

import json

import numpy as np

from wildfire_risk_prediction.landscape import CLASS_CODES, validate_cover

VERSION = "water_scope_v1"
WATER_CODES = (80, 200)
SCOPE_COLUMNS = ["water_scope_included", "water_scope_reason", "water_scope_version"]


def validate_policy(policy):
    """Reject silently changed semantics; a new rule needs a new version."""
    expected = {
        "version": VERSION,
        "decision_date": "2026-10-14",
        "decision_authority": "researcher",
        "selected_option": "A",
        "reference_year": 2017,
        "water_discrete_classes": list(WATER_CODES),
        "exclusion_rule": "all_nonwater_discrete_fractions_exactly_zero",
        "mixed_cells": "retain",
        "mixed_cell_threshold": None,
        "full_habitat_policy_accepted": False,
        "independent_source_accuracy_verified": False,
        "historical_availability_verified": False,
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
    }
    # JSON comparison also distinguishes booleans from integer lookalikes.
    if json.dumps(policy, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError("Unsupported water scope policy")


def build_water_scope(static, grid_ids, policy):
    """Keep every source row; flag only cells with no non-water class area."""
    validate_policy(policy)
    if static.empty or static.grid_id.isna().any():
        raise ValueError("Missing water scope keys")
    cover = validate_cover(static, grid_ids)
    components = cover[[f"lc_{c}_fraction" for c in CLASS_CODES]]
    if components.lt(0).any().any():
        raise ValueError("Negative class components cannot define absence")
    if (
        not cover.historical_available_at.isna().all()
        or not cover.landcover_suitability_decided.eq(False).all()  # noqa: E712
        or not cover.usage.eq("retrospective_candidate_features_only").all()
    ):
        raise ValueError("Static retrospective contract changed")
    area = cover.aoi_area_m2.to_numpy(float)
    if not np.isfinite(area).all() or (area <= 0).any():
        raise ValueError("Invalid AOI support")
    water = cover[[f"lc_{c}_fraction" for c in WATER_CODES]].sum(axis=1)
    nonwater = cover[[f"lc_{c}_fraction" for c in CLASS_CODES if c not in WATER_CODES]]
    # Never round away a real positive land/unknown/wetland fraction.
    excluded = nonwater.eq(0).all(axis=1) & water.gt(0)
    result = cover[
        ["grid_id", "reference_year", "covered_area_km2", "aoi_area_m2", "water_fraction"]
    ].copy()
    result["nonwater_discrete_fraction"] = nonwater.sum(axis=1)
    result["forest_shrub_fraction"] = cover.forest_fraction + cover.shrub_fraction
    result["water_scope_included"] = ~excluded
    result["water_scope_reason"] = np.select(
        [excluded, water.gt(0)],
        ["excluded_map_water", "retained_mixed"],
        default="retained_no_water",
    )
    result["water_scope_version"] = VERSION
    return result.sort_values("grid_id").reset_index(drop=True)


def attach_water_scope(frame, scope):
    """Attach domain flags without changing row order, targets or observation gates."""
    if (
        "grid_id" not in frame
        or frame.grid_id.isna().any()
        or scope.grid_id.isna().any()
        or not scope.grid_id.is_unique
        or not set(frame.grid_id).issubset(set(scope.grid_id))
    ):
        raise ValueError("Water scope grid coverage")
    if any(c in frame for c in SCOPE_COLUMNS):
        raise ValueError("Water scope already attached")
    if (
        scope.water_scope_included.dtype != bool
        or not scope.water_scope_version.eq(VERSION).all()
        or not scope.water_scope_reason.isin(
            ["excluded_map_water", "retained_mixed", "retained_no_water"]
        ).all()
        or not scope.water_scope_included.eq(
            scope.water_scope_reason.ne("excluded_map_water")
        ).all()
    ):
        raise ValueError("Water scope flag contract")
    lookup = scope.set_index("grid_id")
    result = frame.copy(deep=True)
    for column in SCOPE_COLUMNS:
        result[column] = frame.grid_id.map(lookup[column])
    return result


def retain_water_scope(frame, scope):
    """Explicit modelling-domain view; excluded rows remain in source artifacts."""
    annotated = attach_water_scope(frame, scope)
    return annotated.loc[annotated.water_scope_included].copy()
