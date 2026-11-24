import pytest

from wildfire_risk_prediction.source_disjoint_plan import inventory, support


def record(cohort, day, flags=0, eligible=True):
    return {
        "cohort": cohort,
        "grid": "g",
        "time": f"2022-01-{day:02}T00:00:00+00:00",
        "flags": flags,
        "eligible": eligible,
    }


def test_removed_source_is_not_reclassified_as_control():
    rows = [
        record("separate_Mersin", 1, 511),
        record("separate_Mersin", 2, 511),
        record("separate_Mersin", 3),
        record("separate_Mersin", 4),
        record("four_province", 1, 1),
    ]
    anchors = inventory(rows)
    assert anchors.planned_pairs_all_same_grid_month.tolist() == [2, 2]
    plan = support(anchors)
    overall = plan[plan["slice"].eq("all_same_grid_month")]
    assert overall.planned_comparison_pairs_per_model_scenario.tolist() == [4, 2, 2]
    assert overall.eligible_source_anchors.tolist() == [2, 1, 1]
    assert "target" not in anchors and "score" not in anchors


def test_ineligible_anchor_retained_but_does_not_produce_pairs():
    anchors = inventory([record("separate_Mersin", 1, 511, False), record("separate_Mersin", 2)])
    assert len(anchors) == 1 and anchors.planned_pairs_all_same_grid_month.iloc[0] == 0
    result = support(anchors)
    assert result.planned_comparison_pairs_per_model_scenario.eq(0).all()
    assert result.all_source_anchors.eq(1).all()


def test_future_year_duplicates_and_scenario_varying_source_rejected():
    row = record("separate_Mersin", 1, 511)
    with pytest.raises(ValueError, match="Unique"):
        inventory([row, row])
    with pytest.raises(ValueError, match="2022"):
        inventory([row | {"time": "2023-01-01T00:00:00+00:00"}])
    with pytest.raises(ValueError, match="Fixed original"):
        inventory([row | {"flags": 1}])
