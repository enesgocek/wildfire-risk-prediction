import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def audit(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "sat_rank_audit_test", folder / "audit_satellite_pu_ranking_run.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pair_credit_ties_empty_and_unequal_stratum_sizes(audit):
    assert audit.pair_credit([0.5], [0.1, 0.5, 0.9])["auxiliary_S_pair_AUC"] == 0.5
    assert audit.pair_credit([], [0.5])["auxiliary_S_pair_AUC"] is None
    # Two separate strata have AUC 1 and 0, but unequal pair counts 1 and 4.
    mask = np.array([[1, 0, 0], [0, 1, 1], [0, 1, 1]], dtype=bool)
    result = audit.pair_credit([1.0, 0.0, 0.0], [0.0, 1.0, 1.0], mask)
    assert result["pairs"] == 5 and result["auxiliary_S_pair_AUC"] == 0.2


def test_invalid_scores_or_misaligned_mask_are_not_silently_dropped(audit):
    with pytest.raises(ValueError):
        audit.pair_credit([np.nan], [0.5])
    with pytest.raises(ValueError):
        audit.pair_credit([0.2, 0.3], [0.5], np.array([[True]]))


def test_province_boundary_overlap_is_counted_once_per_pair(audit):
    frame = pd.DataFrame(
        {
            audit.S: [1, 1, 0, 0],
            "month": [7, 8, 7, 7],
            "woody_half": [True, True, True, False],
            "province_support": ["Antalya|Mersin", "Izmir", "Mersin|Antalya", "Mugla"],
            "complete_27_features": [True, True, False, True],
        }
    )
    result = audit.comparison_masks(frame)
    assert result["shared_province_area"].tolist() == [[True, False], [False, False]]
    assert result["same_month_woody_half_shared_province"].sum() == 1
    assert result["both_complete_27_features"].sum() == 2
    assert len(frame) == 4  # Unsupported comparisons do not remove original rows.


def test_top_list_keeps_all_boundary_ties_and_does_not_pick_arbitrary_keys(audit):
    scores = pd.Series([0.9, 0.8, 0.8, 0.1], index=["a", "b", "c", "d"])
    assert audit.top_with_ties(scores, 2) == {"a", "b", "c"}
    assert audit.top_with_ties(scores.sample(frac=1, random_state=7), 2) == {"a", "b", "c"}
    with pytest.raises(ValueError):
        audit.top_with_ties(scores, 0)
