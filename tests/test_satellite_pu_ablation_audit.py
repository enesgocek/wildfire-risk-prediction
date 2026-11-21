import importlib.util
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def audit(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "sat_ablation_audit_test", folder / "audit_satellite_pu_ablation.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_grid_controls_static_context_without_dropping_unsupported_rows(audit):
    frame = pd.DataFrame(
        {
            audit.S: [1, 1, 0, 0, 0],
            "grid_id": ["A", "A", "A", "A", "B"],
            "month": [6, 7, 6, 7, 6],
            "woody_half": [True] * 5,
            "province_support": ["Mersin"] * 5,
            "complete_27_features": [True] * 5,
        }
    )
    masks = audit.time_masks(frame)
    assert masks["same_grid"].sum() == 4
    assert masks["same_month_same_grid"].sum() == 2
    result = audit.pair_credit([0.4, 0.4], [0.4, 0.4, 0.9], masks["same_grid"])
    assert result["auxiliary_S_pair_AUC"] == 0.5
    assert result["U_keys_with_comparator"] == 2 and len(frame) == 5


def test_static_model_cannot_vary_by_day_within_one_unchanged_grid(audit):
    frame = pd.DataFrame({"grid_id": ["A", "A", "B"], audit.SCORE: [0.3, 0.3, 0.8]})
    result = audit.static_score_check(frame)
    assert result["grids_with_multiple_key_days"] == 1
    assert result["grids_with_variable_static_scores"] == 0
    frame.loc[1, audit.SCORE] = 0.4
    with pytest.raises(ValueError):
        audit.static_score_check(frame)
