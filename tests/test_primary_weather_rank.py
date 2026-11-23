import json
from pathlib import Path

import pytest

from wildfire_risk_prediction.primary_weather_rank import validate
from wildfire_risk_prediction.weather_policy import specification

ROOT = Path(__file__).resolve().parents[1]


def policies():
    return [
        json.loads((ROOT / "configs" / name).read_bytes())
        for name in ("primary_weather_rank_execution_v1.json", "nonlinear_rank_proposal_v1.json")
    ]


def test_quality_alignment_keeps_the_existing_primary_rule_and_scoped_fit():
    policy, proposal = policies()
    validate(policy, specification(), proposal)
    for key, value in (
        ("new_models", 10),
        ("profile", "choose_best_2022"),
        ("fit_years", [2018, 2019, 2020, 2021, 2022]),
    ):
        with pytest.raises(ValueError, match="Bounded quality"):
            validate(policy | {key: value}, specification(), proposal)
    with pytest.raises(ValueError, match="Bounded quality"):
        validate(policy, specification() | {"primary_minimum_valid_area_fraction": 0.9}, proposal)


def test_quality_run_does_not_authorize_risk_labels_future_years_or_parameter_search():
    policy, proposal = policies()
    for name in (
        "negative_label_permitted",
        "true_Y_or_accepted_L_assignment",
        "hyperparameter_search",
        "closed_year_2023_2024_2025_values_permitted",
        "final_merge_permitted",
        "risk_probability_or_validated_color_output",
    ):
        with pytest.raises(ValueError, match="No new method claims"):
            validate(policy | {name: True}, specification(), proposal)
