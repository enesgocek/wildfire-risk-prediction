import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def pilot(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "satellite_ranking_plan_test", folder / "run_satellite_pu_ranking_pilot.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "changes",
    [
        {"auxiliary_model_fitting_authorized": True},
        {"final_merge_permitted": True},
        {"scenario_selected": "d1000m_t24h"},
        {"maximum_fits": 28},
        {"hyperparameter_search": True},
    ],
)
def test_preparation_cannot_grant_fitting_select_best_scenario_or_tune(pilot, changes):
    policy = json.loads(pilot.POLICY.read_bytes())
    with pytest.raises(ValueError):
        pilot.validate_proposal(policy | changes)


def toy(pilot):
    roles = pd.DataFrame(
        {
            "grid_id": ["A", "B", "C", "D", "E"],
            "prediction_timestamp_utc": ["2019-06-01T00:00:00+00:00"] * 2
            + ["2022-06-01T00:00:00+00:00"] * 3,
            "proposed_partition": ["proposed_fit_2018_2021"] * 2 + ["proposed_assessment_2022"] * 3,
            "original_U_sample_present": [True, False, True, False, False],
            "possible_L_proposal_present": [False, True, False, True, True],
            "proposed_scenarios_json": [
                "[]",
                '["d500m_t24h"]',
                "[]",
                '["d500m_t24h"]',
                '["d2000m_t72h"]',
            ],
            "target": [np.nan] * 5,
            "accepted_L_membership": [np.nan] * 5,
        }
    )
    features = roles[pilot.join.KEYS].copy()
    for name in pilot.join.feature_names():
        features[name] = np.arange(5, dtype=float)
    return roles, features


def test_scenario_S_is_not_real_Y_and_original_U_stays_in_both_periods(pilot):
    roles, features = toy(pilot)
    tables = pilot.scenario_tables(roles, features, "d500m_t24h")
    train, s_train = tables["proposed_fit_2018_2021"]
    held, s_held = tables["proposed_assessment_2022"]
    assert train.grid_id.tolist() == ["A", "B"] and held.grid_id.tolist() == ["C", "D"]
    assert s_train.tolist() == s_held.tolist() == [0, 1]
    assert roles.target.isna().all() and roles.accepted_L_membership.isna().all()
    assert train.columns.tolist() == pilot.join.KEYS + pilot.join.feature_names()


def test_role_overlap_does_not_silently_delete_original_U(pilot):
    roles, features = toy(pilot)
    roles.loc[0, "possible_L_proposal_present"] = True
    with pytest.raises(ValueError, match="Overlapping"):
        pilot.scenario_tables(roles, features, "d500m_t24h")
    assert roles.original_U_sample_present.sum() == 2


def test_post_target_QA_cannot_be_a_model_feature(pilot):
    roles, features = toy(pilot)
    features["first_detection_confidence"] = 95
    with pytest.raises(ValueError, match="allowlist"):
        pilot.scenario_tables(roles, features, "d500m_t24h")


def test_run_refuses_old_or_missing_permission_before_loading_features(
    pilot, tmp_path, monkeypatch
):
    plan = tmp_path / "plan.json"
    plan.write_text('{"maximum_fits": 27}', encoding="utf-8")
    execution = tmp_path / "execution.json"
    execution.write_text(
        '{"decision_source": "explicit_user_selection_A_run_limited_conditional_ranking_pilot", '
        '"auxiliary_model_fitting_authorized": true}',
        encoding="utf-8",
    )
    monkeypatch.setattr(pilot, "load_preparation", lambda: pytest.fail("X must not be loaded"))
    with pytest.raises(ValueError, match="New explicit"):
        pilot.run(plan, execution)


def test_new_auxiliary_decision_cannot_grant_fire_or_merge_permission(pilot, tmp_path):
    path = tmp_path / "plan.json"
    path.write_text('{"maximum_fits": 27}', encoding="utf-8")
    decision = {
        "decision_source": "explicit_user_selection_A_run_four_province_satellite_auxiliary_pilot",
        "auxiliary_model_fitting_authorized": True,
        "plan_readback_sha256": pilot.digest(path),
        "authorized_models": list(pilot.NAMES),
        "maximum_fits": 27,
        "Y_remains_null": True,
        **dict.fromkeys(pilot.CLOSED, False),
    }
    pilot.validate_execution(decision, path, {"maximum_fits": 27})
    for flag in pilot.CLOSED:
        with pytest.raises(ValueError):
            pilot.validate_execution(decision | {flag: True}, path, {"maximum_fits": 27})
