"""First-cell comparisons count units, not detection/event totals; targets stay empty."""

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from wildfire_risk_prediction.evaluation_folds import training_metadata
from wildfire_risk_prediction.first_cell_candidates import candidate_cells

SPEC = importlib.util.spec_from_file_location(
    "event_cell_decision",
    Path(__file__).parents[1] / "scripts/quality/prepare_event_cell_decision.py",
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def fixture(cells=("G1", "G2"), extra_unique=False, first="2019-01-01T01:00:00+00:00"):
    units = pd.DataFrame(
        [
            {
                "review_unit_id": "u",
                "grid_id": "G1",
                "prediction_timestamp_utc": "2019-01-01T00:00:00+00:00",
                "target": None,
            }
        ]
    )
    components = pd.DataFrame(
        [
            {
                "cluster_id": "c",
                "scenario": "s",
                "earliest_grid_count": len(cells),
                "duration_hours": 1,
                "target": None,
            }
        ]
    )
    matched = (
        pd.Timestamp("2019-01-01T00:00:00+00:00")
        < pd.Timestamp(first)
        <= pd.Timestamp("2019-01-02T00:00:00+00:00")
        and "G1" in cells
    )
    contexts = pd.DataFrame(
        [
            {
                **units.iloc[0].to_dict(),
                "scenario": "s",
                "cluster_id": "c",
                "first_detection_utc": first,
                "earliest_grid_ids_json": json.dumps(cells),
                "catalog_first_candidate_match": matched,
            }
        ]
    )
    if extra_unique:
        components = pd.concat(
            [components, components.assign(cluster_id="c2", earliest_grid_count=1)]
        )
        contexts = pd.concat(
            [contexts, contexts.assign(cluster_id="c2", earliest_grid_ids_json='["G1"]')]
        )
    return units, contexts, components


def test_all_first_cells_remain_candidates_but_unique_policy_withholds_tie():
    cases, impact = module.compare_candidates(*fixture())
    assert cases.A_scenarios_with_candidate.tolist() == [1]
    assert cases.B_scenarios_with_candidate.tolist() == [0]
    assert impact.units_losing_all_candidates_under_B.tolist() == [1]
    assert cases.target.isna().all() and impact.target.isna().all()


def test_another_unique_component_preserves_unit_candidate_without_counting_two_events():
    cases, impact = module.compare_candidates(*fixture(extra_unique=True))
    assert cases.A_scenarios_with_candidate.tolist() == [1]
    assert cases.B_scenarios_with_candidate.tolist() == [1]
    assert impact.units_losing_all_candidates_under_B.tolist() == [0]


def test_single_cell_component_agrees():
    cases, _ = module.compare_candidates(*fixture(cells=("G1",)))
    assert cases.A_scenarios_with_candidate.tolist() == cases.B_scenarios_with_candidate.tolist()


@pytest.mark.parametrize(
    ("first", "expected"),
    [("2019-01-01T00:00:00+00:00", 0), ("2019-01-02T00:00:00+00:00", 1)],
)
def test_window_left_open_right_closed(first, expected):
    cases, _ = module.compare_candidates(*fixture(first=first))
    assert cases.A_scenarios_with_candidate.tolist() == [expected]
    assert cases.target.isna().all()


@pytest.mark.parametrize("damage", ["label", "duplicate", "string_bool", "cell_count", "key"])
def test_corrupt_or_prelabelled_context_rejected(damage):
    units, contexts, components = fixture()
    if damage == "label":
        units["target"] = 1
    elif damage == "duplicate":
        contexts = pd.concat([contexts, contexts])
    elif damage == "string_bool":
        contexts["catalog_first_candidate_match"] = "False"
    elif damage == "cell_count":
        components["earliest_grid_count"] = 1
    else:
        contexts["grid_id"] = "OTHER"
    with pytest.raises(ValueError):
        module.compare_candidates(units, contexts, components)


def cell_inputs():
    root = Path(__file__).parents[1]
    policy = json.loads((root / "configs/first_cell_candidates_v1.json").read_text())
    components = pd.DataFrame(
        [
            {
                "scenario": "s",
                "cluster_id": "s_c",
                "target": None,
                "first_detection_utc": "2019-01-01T23:29:00+00:00",
                "earliest_grid_ids_json": '["G2", "G1"]',
                "earliest_grid_count": 2,
            }
        ]
    )
    return components, policy


def test_selected_A_keeps_both_cells_under_one_candidate_without_event_admission():
    rows = candidate_cells(*cell_inputs())
    assert rows.grid_id.tolist() == ["G1", "G2"]
    assert rows.candidate_component_id.nunique() == 1
    assert rows.first_cell_count.tolist() == [2, 2]
    assert not rows.event_identity_accepted.any()
    assert not rows.event_membership_complete.any()
    assert rows.target.isna().all()


@pytest.mark.parametrize("damage", ["duplicate_cell", "count", "timezone", "holdout", "label"])
def test_cell_expansion_rejects_bad_source_or_scope(damage):
    components, policy = cell_inputs()
    if damage == "duplicate_cell":
        components["earliest_grid_ids_json"] = '["G1", "G1"]'
    elif damage == "count":
        components["earliest_grid_count"] = 1
    elif damage == "timezone":
        components["first_detection_utc"] = "2019-01-01T23:29:00"
    elif damage == "holdout":
        components["first_detection_utc"] = "2024-01-01T23:29:00+00:00"
    else:
        components["target"] = 1
    with pytest.raises(ValueError):
        candidate_cells(components, policy)


def test_user_method_direction_cannot_open_label_gates():
    components, policy = cell_inputs()
    policy["positive_label_permitted"] = True
    with pytest.raises(ValueError, match="admission gates"):
        candidate_cells(components, policy)


def test_exploratory_candidate_ids_cannot_satisfy_training_membership_gate():
    rows = candidate_cells(*cell_inputs())
    rows["prediction_timestamp_utc"] = "2019-01-01T00:00:00+00:00"
    rows["event_ids"] = rows.candidate_component_id.map(lambda key: [key])
    with pytest.raises(ValueError, match="Resolved event membership"):
        training_metadata(rows)
