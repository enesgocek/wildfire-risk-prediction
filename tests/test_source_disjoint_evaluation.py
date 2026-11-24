import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.source_disjoint_evaluation import (
    comparison_indices,
    ordering_metric,
    slice_masks,
)


def calendar():
    meta = pd.DataFrame(
        {
            "grid_id": ["g"] * 5,
            "prediction_timestamp_utc": [f"2022-01-{d:02}T00:00:00+00:00" for d in (1, 2, 3, 4, 9)],
            "primary_weather_and_dynamic_15_eligible": [True, True, True, True, False],
            "target": [None] * 5,
            "accepted_L_membership": [None] * 5,
            "daily_observation_status": ["unknown"] * 5,
        }
    )
    anchors = meta.iloc[:2, :2].copy()
    anchors["exact_key_category"] = ["same_key_satellite_proposal", "absent_from_four_calendar"]
    return meta, anchors


def test_subset_changes_source_list_without_turning_omitted_source_into_control():
    meta, anchors = calendar()
    pairs = comparison_indices(meta, anchors, "exclude_any_same_key_satellite_proposal")
    assert pairs.calendar_row_source.tolist() == [1, 1]
    assert pairs.calendar_row_other.tolist() == [2, 3]
    assert slice_masks(pairs)["gap_1_to_3_days"].all()
    assert not slice_masks(pairs)["other_day_before_source_day"].any()
    full = comparison_indices(meta, anchors, "original_source_calendar")
    assert len(full) == 4 and meta.target.isna().all()


def test_ties_missing_support_and_unusable_scores_are_explicit():
    result = ordering_metric([3, 2, 1], [2, 2, 2])
    assert result == {"pairs": 3, "wins": 1, "ties": 1, "auxiliary_pair_AUC": 0.5}
    assert ordering_metric([], [])["auxiliary_pair_AUC"] is None
    with pytest.raises(ValueError, match="Finite aligned"):
        ordering_metric([np.nan], [1])


def test_future_year_and_accepted_target_are_rejected():
    meta, anchors = calendar()
    meta.loc[0, "prediction_timestamp_utc"] = "2023-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="Existing 2022"):
        comparison_indices(meta, anchors, "original_source_calendar")
    meta, anchors = calendar()
    meta.loc[0, "target"] = 1
    with pytest.raises(ValueError, match="Unknown scientific"):
        comparison_indices(meta, anchors, "original_source_calendar")
