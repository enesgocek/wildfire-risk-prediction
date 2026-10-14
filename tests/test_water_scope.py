"""Mapped-water scope must preserve tiny land shares and every label gate."""

import json
from pathlib import Path

import pandas as pd
import pytest

from wildfire_risk_prediction.landscape import CLASS_CODES, FOREST_CODES
from wildfire_risk_prediction.water_scope import (
    attach_water_scope,
    build_water_scope,
    retain_water_scope,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def policy():
    return json.loads((ROOT / "configs/water_scope_v1.json").read_text())


def row(key, fractions):
    values = {c: fractions.get(c, 0.0) for c in CLASS_CODES}
    forest = sum(values[c] for c in FOREST_CODES)
    return {
        "grid_id": key,
        "reference_year": 2017,
        "covered_area_km2": 0.5,
        "aoi_area_m2": 500001,
        **{f"lc_{c}_fraction": v for c, v in values.items()},
        "forest_fraction": forest,
        "shrub_fraction": values[20],
        "herbaceous_fraction": values[30],
        "agriculture_fraction": values[40],
        "urban_fraction": values[50],
        "water_fraction": values[80] + values[200],
        "unknown_fraction": values[0],
        "natural_vegetation_fraction": forest + values[20] + values[30],
        "historical_available_at": None,
        "landcover_suitability_decided": False,
        "usage": "retrospective_candidate_features_only",
    }


@pytest.mark.parametrize(
    "fractions,excluded",
    [
        ({80: 1}, True),
        ({200: 1}, True),
        ({80: 0.4, 200: 0.6}, True),
        ({200: 1 - 1e-12, 111: 1e-12}, False),
        ({80: 0.999999, 0: 0.000001}, False),
        ({90: 1}, False),  # Wetlands are not class 80/200 water.
        ({0: 1}, False),
        ({40: 1}, False),  # Scope is not a forest-only habitat filter.
    ],
)
def test_class_absence_not_rounded_water_sum(policy, fractions, excluded):
    static = pd.DataFrame([row("g", fractions)])
    original = static.copy(deep=True)
    scope = build_water_scope(static, ["g"], policy)
    assert bool(scope.water_scope_included.iloc[0]) is not excluded
    pd.testing.assert_frame_equal(original, static)


@pytest.mark.parametrize("problem", ["negative", "duplicate", "keys", "policy", "future"])
def test_reject_invalid_or_changed_contract(policy, problem):
    static = pd.DataFrame([row("g", {80: 1})])
    keys = ["g"]
    if problem == "negative":
        static.loc[0, "lc_90_fraction"] = -1e-12
    elif problem == "duplicate":
        static = pd.concat([static, static])
    elif problem == "keys":
        keys = ["other"]
    elif problem == "policy":
        policy["mixed_cell_threshold"] = 0.25
    else:
        static.loc[0, "reference_year"] = 2024
    with pytest.raises(ValueError):
        build_water_scope(static, keys, policy)


def test_domain_view_keeps_original_order_nullable_targets_and_observation(policy):
    static = pd.DataFrame([row("water", {200: 1}), row("land", {111: 1})])
    scope = build_water_scope(static, ["water", "land"], policy)
    original = pd.DataFrame(
        {
            "grid_id": ["land", "water", "land"],
            "target": pd.Series([pd.NA, pd.NA, pd.NA], dtype="Int8"),
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "feature": [1.0, float("nan"), 3.0],
        }
    )
    original.index = [9, 1, 9]
    annotated = attach_water_scope(original, scope)
    pd.testing.assert_frame_equal(annotated[original.columns], original)
    selected = retain_water_scope(original, scope)
    pd.testing.assert_frame_equal(selected[original.columns], original.iloc[[0, 2]])
    assert annotated.water_scope_included.tolist() == [True, False, True]
    assert selected.target.isna().all()
    assert not selected.negative_label_permitted.any()
    with pytest.raises(ValueError, match="already attached"):
        attach_water_scope(annotated, scope)
    with pytest.raises(ValueError, match="coverage"):
        attach_water_scope(pd.DataFrame({"grid_id": ["missing"]}), scope)
    scope.loc[0, "water_scope_included"] = not scope.loc[0, "water_scope_included"]
    with pytest.raises(ValueError, match="flag contract"):
        attach_water_scope(original, scope)
