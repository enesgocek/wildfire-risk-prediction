import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.ranking_queries import DYNAMIC_FEATURES, query_inventory


def sample():
    return pd.DataFrame(
        {
            "grid_id": ["a", "a", "a", "b"],
            "prediction_timestamp_utc": [
                "2021-01-01T00:00:00+00:00",
                "2021-01-02T00:00:00+00:00",
                "2021-02-01T00:00:00+00:00",
                "2021-01-02T00:00:00+00:00",
            ],
            "review_temporal_role": ["proposed_fit_2018_2021"] * 4,
            "target": [np.nan] * 4,
            "accepted_L_membership": [np.nan] * 4,
            "daily_observation_status": ["unknown"] * 4,
        }
    )


def test_queries_never_cross_cell_or_month_and_do_not_fill_missing_days():
    m = sample()
    r = query_inventory(m, [True, False, False, False], [True] * 4)
    assert len(r) == 3 and r.possible_cross_context_pairs.sum() == 1
    assert r.all_rows_retained.sum() == 4
    r = query_inventory(m, [True, False, False, False], [False, True, True, True])
    assert r.possible_cross_context_pairs.sum() == 0


def test_seen_assessment_year_cannot_be_assigned_to_training():
    m = sample()
    m.loc[0, "prediction_timestamp_utc"] = "2022-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="pilot years"):
        query_inventory(m, [True, False, False, False], [True] * 4)


def test_later_year_or_true_label_or_bad_mask_is_rejected():
    m = sample()
    m.loc[0, "prediction_timestamp_utc"] = "2023-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="2018-2022"):
        query_inventory(m, [True, False, False, False], [True] * 4)
    m = sample()
    m.loc[0, "target"] = 1
    with pytest.raises(ValueError, match="Unassigned"):
        query_inventory(m, [True, False, False, False], [True] * 4)
    with pytest.raises(ValueError, match="Boolean"):
        query_inventory(sample(), [1, 0, 0, 0], [True] * 4)


def test_dynamic_schema_excludes_location_time_and_static_cover():
    assert len(DYNAMIC_FEATURES) == len(set(DYNAMIC_FEATURES)) == 15
    assert not {"grid_id", "calendar_month", "forest_fraction", "elevation_mean_m"} & set(
        DYNAMIC_FEATURES
    )


def test_preparation_policy_cannot_grant_training():
    import importlib.util
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    path = root / "scripts/quality/prepare_nonlinear_rank_comparison.py"
    spec = importlib.util.spec_from_file_location("rank_proposal_guard", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy = json.loads((root / "configs/nonlinear_rank_proposal_v1.json").read_bytes())
    module.validate_policy(policy)
    with pytest.raises(ValueError, match="Preparation"):
        module.validate_policy({**policy, "new_training_authorized": True})
