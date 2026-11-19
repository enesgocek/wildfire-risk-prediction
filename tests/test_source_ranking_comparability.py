import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def audit():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/quality/audit_source_ranking_comparability.py"
    )
    spec = importlib.util.spec_from_file_location("comparability_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def toy(audit):
    # Most source keys are in warm months; the score knows only the season.
    frame = pd.DataFrame(
        {
            "grid_id": [f"G{i}" for i in range(6)],
            "prediction_timestamp_utc": ["2022-01-02T00:00:00+00:00"] * 3
            + ["2022-07-02T00:00:00+00:00"] * 3,
            audit.MEMBER: [1, 0, 0, 1, 1, 0],
            "Y_true_fire_target": [np.nan] * 6,
            "daily_observation_status": ["unknown"] * 6,
        }
    )
    for model in audit.MODELS:
        frame[model + "_source_membership_score"] = [0.1] * 3 + [0.9] * 3
    features = frame[audit.KEYS].copy()
    features["forest_fraction"] = [0.3] * 6
    features["shrub_fraction"] = [0.2] * 6
    return frame, features


def test_season_composition_can_separate_S_without_within_season_skill(audit):
    scores, features = toy(audit)
    frame = audit.assignments(scores, features)
    result, _ = audit.summarize(frame, "month", "random_forest")
    assert result["all_pairs"]["source_membership_pair_AUC"] == pytest.approx(2 / 3)
    assert result["within_stratum"]["source_membership_pair_AUC"] == 0.5
    assert result["within_stratum"]["pairs"] == 4
    assert result["between_strata"]["pairs"] == 5
    assert result["all_pairs"]["doubled_credit"] == 12
    shuffled, _ = audit.summarize(frame.sample(frac=1, random_state=4), "month", "random_forest")
    assert result == shuffled
    assert frame.woody_half.eq("woody_ge_0.5").all()  # Sum of both classes, inclusive boundary.
    assert frame.Y_true_fire_target.isna().all()


def test_within_auc_is_pair_weighted_not_mean_of_stratum_aucs(audit):
    frame = pd.DataFrame(
        {
            audit.MEMBER: [1, 0, 1, 1, 0, 0],
            "month": ["A", "A", "B", "B", "B", "B"],
            "random_forest_source_membership_score": [1, 0, 0, 0, 1, 1],
        }
    )
    result, rows = audit.summarize(frame, "month", "random_forest")
    assert result["within_stratum"]["source_membership_pair_AUC"] == 1 / 5
    assert [r["source_membership_pair_AUC"] for r in rows] == [1, 0]


def test_empty_comparison_is_null_and_rows_are_not_removed(audit):
    scores, features = toy(audit)
    frame = audit.assignments(scores, features)
    frame["month"] = np.where(frame[audit.MEMBER].eq(1), "only_source", "only_U")
    result, rows = audit.summarize(frame, "month", "logistic_regression")
    assert result["within_stratum"]["pairs"] == 0
    assert result["within_stratum"]["source_membership_pair_AUC"] is None
    assert result["one_membership_strata"] == 2
    assert result["source_keys_with_opposite_membership_in_stratum"] == 0
    assert sum(r["source_keys"] + r["U_keys"] for r in rows) == 6
    assert all(r["source_membership_pair_AUC"] is None for r in rows)


def test_credit_ties_and_direction(audit):
    assert audit.credit([0.5], [0.1, 0.5, 0.9]) == {
        "pairs": 3,
        "wins": 1,
        "ties": 1,
        "losses": 1,
        "doubled_credit": 3,
        "source_membership_pair_AUC": 0.5,
    }


@pytest.mark.parametrize(
    "column,value",
    [
        ("prediction_timestamp_utc", "2023-01-01T00:00:00+00:00"),
        ("prediction_timestamp_utc", "2022-01-01T00:00:00"),
        ("prediction_timestamp_utc", "2022-01-01T01:00:00+00:00"),
        ("Y_true_fire_target", 0),
        ("daily_observation_status", "observed"),
        ("S_observed_source_membership", 2),
        ("random_forest_source_membership_score", np.nan),
    ],
)
def test_unknown_target_role_and_score_guards(audit, column, value):
    scores, features = toy(audit)
    scores.loc[0, column] = value
    with pytest.raises(ValueError):
        audit.assignments(scores, features)


@pytest.mark.parametrize("kind", ["duplicate", "missing", "nan", "sum_above_one"])
def test_coverage_or_key_errors_are_not_silently_imputed(audit, kind):
    scores, features = toy(audit)
    if kind == "duplicate":
        features = pd.concat([features, features.iloc[:1]])
    elif kind == "missing":
        features = features.iloc[1:]
    elif kind == "nan":
        features.loc[0, "forest_fraction"] = np.nan
    else:
        features.loc[0, "forest_fraction"] = 0.9
    with pytest.raises(ValueError):
        audit.assignments(scores, features)
