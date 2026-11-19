import importlib.util
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def pilot():
    path = (
        Path(__file__).resolve().parents[1] / "scripts/quality/run_conditional_pu_ranking_pilot.py"
    )
    spec = importlib.util.spec_from_file_location("conditional_execution_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "change",
    [
        {"auxiliary_model_fitting_authorized": False},
        {"negative_label_permitted": True},
        {"main_fire_model_training_authorized": True},
        {"final_merge_permitted": True},
    ],
)
def test_auxiliary_decision_cannot_be_missing_or_grant_main_research_permissions(pilot, change):
    execution = json.loads(pilot.EXECUTION.read_bytes()) | change
    with pytest.raises(ValueError):
        pilot.validate_execution(execution, json.loads(pilot.PROPOSAL.read_bytes()))


def toy(pilot):
    frame = pd.DataFrame({k: np.zeros(8) for k in pilot.join.feature_names()})
    frame["temperature_mean_c"] = [1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0]
    frame["forest_fraction"] = np.nan
    return frame, np.array([0, 0, 0, 0, 1, 1, 1, 1])


@pytest.mark.parametrize("name", ["logistic_regression", "random_forest"])
def test_only_fit_values_learn_medians_and_assessment_does_not_change_state(pilot, name):
    frame, membership = toy(pilot)
    proposal = json.loads(pilot.PROPOSAL.read_bytes())
    model, retained = pilot.fit_auxiliary(name, frame, membership, proposal)
    assert "forest_fraction" not in retained
    imputer = model.named_steps["impute"]
    assert imputer.statistics_[retained.index("temperature_mean_c")] == 5.0
    state = joblib.hash(model)
    held = frame.copy()
    held["temperature_mean_c"] = [np.nan] + [1e6] * 7
    scores = model.predict_proba(pilot.model_input(name, held, retained))[:, 1]
    assert np.isfinite(scores).all() and joblib.hash(model) == state
    assert frame.temperature_mean_c.isna().sum() == 1
    if name == "random_forest":
        assert model.named_steps["model"].n_jobs == 1
        np.testing.assert_array_equal(
            model.predict_proba(pilot.model_input(name, held, retained))[:, 1], scores
        )


def test_metadata_or_target_column_is_rejected_before_model_fit(pilot):
    frame, membership = toy(pilot)
    frame["target"] = membership
    with pytest.raises(ValueError, match="allowlist"):
        pilot.fit_auxiliary(
            "logistic_regression", frame, membership, json.loads(pilot.PROPOSAL.read_bytes())
        )


def test_missingness_control_is_five_feature_family_flags_without_QA_values(pilot):
    frame, membership = toy(pilot)
    flags = pilot.family_missing_flags(frame)
    assert flags.columns.tolist() == ["weather", "cover", "terrain", "vegetation30", "vegetation60"]
    assert flags.cover.eq(1).all() and flags.terrain.eq(0).all()
    assert flags.weather.sum() == 1
    model, retained = pilot.fit_auxiliary(
        "missingness_control", frame, membership, json.loads(pilot.PROPOSAL.read_bytes())
    )
    assert retained == flags.columns.tolist()
    assert np.isfinite(model.predict_proba(flags)).all()
