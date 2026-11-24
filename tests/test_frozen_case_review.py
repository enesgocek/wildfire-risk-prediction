from fractions import Fraction

import pandas as pd
import pytest

from wildfire_risk_prediction.frozen_case_review import (
    feature_context,
    inventory,
    select_examples,
    timeline,
)


def test_inventory_requires_scenario_support_and_does_not_weight_by_comparator_count():
    data = pd.DataFrame(
        [
            {
                "cohort": "c",
                "grid_id": "a",
                "source_prediction_timestamp_utc": "2022-01-01T00:00:00+00:00",
                "variant": "primary_weather_XGBoost",
                "scenario": scenario,
                "pairs": n,
                "credit_twice": credit,
                "province_area_intersections": "Mersin",
            }
            for scenario, n, credit in [("s1", 3, 6), ("s2", 1, 0)]
        ]
    )
    result = inventory(data, 2).iloc[0]
    assert result.primary_credit_mean == float(Fraction(1, 2))
    assert result.all_nine_scenario_support
    assert not inventory(data.head(1), 2).iloc[0].all_nine_scenario_support
    with pytest.raises(ValueError, match="Unique"):
        inventory(pd.concat([data, data]), 2)
    data["source_prediction_timestamp_utc"] = "2023-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="2022"):
        inventory(data, 2)


def test_illustration_is_disjoint_deterministic_and_not_only_favorable():
    data = pd.DataFrame(
        [
            {
                "cohort": "c",
                "grid_id": f"g{i:02}",
                "source_prediction_timestamp_utc": "2022-01-01",
                "all_nine_scenario_support": True,
                "primary_credit_mean": i / 9,
            }
            for i in range(10)
        ]
    )
    selected = select_examples(data.sample(frac=1, random_state=5))
    assert selected.grid_id.tolist() == ["g00", "g01", "g04", "g05", "g08", "g09"]
    assert selected.case_id.nunique() == 6 and selected.illustrative_tier.nunique() == 3


def test_ranks_handle_ties_and_feature_context_never_labels_unassigned_negative():
    records = [
        {"time": f"2022-01-{i:02}", "flags": flag, "x": [x], "scores": [[score, 0, 0]]}
        for i, flag, x, score in [(1, 1, 3, 5), (2, 0, 3, 5), (3, 0, 1, 0)]
    ]
    result = timeline(records, 1)
    assert result.primary_rank_mean.tolist() == [1.5, 1.5, 3]
    payload = {"dictionary": [{"name": "x", "unit": "u"}]}
    context = feature_context(payload, records, records[0], ["x"]).iloc[0]
    assert context.stable_unassigned_reference_days == 2
    assert context.reference_median == 2
    assert context.source_greater_reference_credit == 0.75
    missing = feature_context(payload, records[:1], records[0], ["x"]).iloc[0]
    assert pd.isna(missing.reference_median)
    assert "target" not in context and "false_alarm" not in context
