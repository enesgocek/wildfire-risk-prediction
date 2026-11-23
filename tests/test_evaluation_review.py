import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.evaluation_review import (
    checked_feature_union,
    rank_positions,
    support_counts,
)


def metadata():
    return pd.DataFrame(
        {
            "grid_id": ["a", "a", "a", "b"],
            "prediction_timestamp_utc": [
                "2022-01-01T00:00:00+00:00",
                "2022-01-02T00:00:00+00:00",
                "2022-01-03T00:00:00+00:00",
                "2022-01-01T00:00:00+00:00",
            ],
            "target": [np.nan] * 4,
            "accepted_L_membership": [np.nan] * 4,
            "daily_observation_status": ["unknown"] * 4,
        }
    )


def test_shared_features_preserve_nulls_and_reject_conflicts_not_average():
    a = metadata().iloc[:2, :2].copy()
    a["value"] = [1.0, np.nan]
    b = a.iloc[[1]].copy()
    result = checked_feature_union([a, b])
    assert len(result) == 2 and pd.isna(result.value.iloc[1])
    b["value"] = 0.0
    with pytest.raises(ValueError, match="Shared feature"):
        checked_feature_union([a, b])
    with pytest.raises(ValueError, match="Unique keys"):
        checked_feature_union([pd.concat([a, a])])


def test_positions_are_local_and_tied_not_probabilities_and_missing_stays_missing():
    m = metadata()
    r = rank_positions(m, [8.0, 8.0, np.nan, 100.0])
    np.testing.assert_array_equal(r.position_in_available_cell_month_days, [1.5, 1.5, np.nan, 1])
    assert r.available_days_in_cell_month.tolist() == [2, 2, 2, 1]
    assert m.target.isna().all()


def test_later_year_or_claimed_fire_label_is_rejected():
    m = metadata()
    m.loc[0, "prediction_timestamp_utc"] = "2023-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="existing unique 2022"):
        rank_positions(m, [1.0] * 4)
    m = metadata()
    m.loc[0, "target"] = 0
    with pytest.raises(ValueError, match="Unknown fire targets"):
        rank_positions(m, [1.0] * 4)


def test_support_counts_preserve_unseen_cells_and_do_not_call_them_validation():
    m = metadata()
    layout = m.iloc[[0]].copy()
    layout["prediction_timestamp_utc"] = "2020-01-01T00:00:00+00:00"
    result = support_counts(
        m, np.array([True, False, False, True]), np.array([True, True, False, True]), layout
    )
    assert result["possible_comparison_pairs"] == 1
    assert result["assessment_cells_seen_in_fit"] == 1
    assert result["assessment_cells_not_seen_in_fit"] == 1
    assert result["complete_records_from_unseen_cells"] == 1
    assert result["complete_records_with_same_cell_and_month_number_in_fit"] == 2
    layout["prediction_timestamp_utc"] = "2022-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="already fitted historical"):
        support_counts(m, np.ones(4, dtype=bool), np.ones(4, dtype=bool), layout)
