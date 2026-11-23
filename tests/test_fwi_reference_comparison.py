import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from wildfire_risk_prediction.fwi_reference import (
    lagged_band,
    matched_pairs,
    nearest_node,
    pair_credit,
    sample_preserving_missing,
)


def test_calendar_lag_rejects_same_day_shortcut_and_closed_years():
    assert lagged_band("2022-06-02T00:00:00+00:00") == (1, "2022-06-01")
    assert lagged_band("2022-06-30T00:00:00+00:00") == (29, "2022-06-29")
    for stamp in [
        "2022-06-01T00:00:00+00:00",
        "2023-06-02T00:00:00+00:00",
        "2022-06-02T12:00:00+00:00",
        "2022-06-02T00:00:00",
    ]:
        with pytest.raises(ValueError):
            lagged_band(stamp)


def test_nearest_node_tie_is_deterministic_and_outside_is_not_clamped():
    r = nearest_node(0, 0, [-1, 1], [1, -1])
    assert (r["native_row"], r["native_column"]) == (0, 0)
    assert r["equal_distance_nodes_at_1e_minus_6_m"] == 4
    with pytest.raises(ValueError, match="extent"):
        nearest_node(3, 0, [-1, 1], [1, -1])


def test_missing_nearest_is_never_replaced_with_valid_neighbor_and_zero_is_valid():
    a = np.ma.array([[123.0, 30.0], [0.0, 5.0]], mask=[[True, False], [False, False]])
    assert np.isnan(sample_preserving_missing(a, 0, 0))
    assert sample_preserving_missing(a, 1, 0) == 0


def test_pairs_do_not_cross_cell_month_or_missing_support():
    grids = ["a", "a", "a", "b", "a"]
    stamps = ["2022-06-02", "2022-06-03", "2022-06-04", "2022-06-03", "2022-07-01"]
    a, b = matched_pairs(
        grids, stamps, [True, False, False, False, False], [True, True, False, True, True]
    )
    assert list(zip(a, b, strict=True)) == [(0, 1)]


def test_credit_accounts_for_ties_without_negative_labels():
    r = pair_credit([2.0, 1.0, 2.0, 3.0], [0, 0, 0], [1, 2, 3])
    assert r == {"pairs": 3, "wins": 1, "ties": 1, "auxiliary_pair_AUC": 0.5}
    assert pair_credit([], [], [])["auxiliary_pair_AUC"] is None


def test_execution_scope_cannot_authorize_fit_final_merge_or_new_years():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts/quality/run_fwi_reference_comparison.py"
    spec = importlib.util.spec_from_file_location("fwi_comparison_scope", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = json.loads((root / "configs/fwi_reference_comparison_execution_v1.json").read_bytes())
    module.validate(config)
    for name in (
        "new_model_fitting_authorized",
        "final_merge_permitted",
        "new_2023_2024_2025_scientific_values_authorized",
    ):
        with pytest.raises(ValueError):
            module.validate({**config, name: True})
