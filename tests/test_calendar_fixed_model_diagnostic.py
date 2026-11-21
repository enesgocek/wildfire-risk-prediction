import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def diagnostic(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "fixed_calendar_diagnostic_test", folder / "run_calendar_fixed_model_diagnostic.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "flag",
    [
        "model_refitting_authorized",
        "new_Y_or_accepted_L_assignment_authorized",
        "final_merge_permitted",
    ],
)
def test_autonomy_is_bounded_to_fixed_auxiliary_diagnostic(diagnostic, flag):
    decision = json.loads(diagnostic.EXECUTION.read_bytes())
    with pytest.raises(ValueError):
        diagnostic.validate_execution(decision | {flag: True})


def test_within_cell_month_pairs_remove_only_noncomparable_pairs_not_calendar_rows(diagnostic):
    frame = pd.DataFrame(
        {
            "grid_id": ["A", "A", "B", "B"],
            "prediction_timestamp_utc": ["2022-05-01T00:00:00+00:00", "2022-05-02T00:00:00+00:00"]
            * 2,
            diagnostic.INDICATOR: [True, False, True, False],
            "weather_complete": [True, True, True, False],
            "complete_27_features": [True] * 4,
            "score": [0.4, 0.4, 0.9, 0.9],
        }
    )
    rows = diagnostic.comparisons(frame, "score")
    same = next(
        r for r in rows if r["scheme"] == "within_grid_year_month" and r["quality_profile"] == "all"
    )
    valid = next(
        r
        for r in rows
        if r["scheme"] == "within_grid_year_month"
        and r["quality_profile"] == "complete_weather_both"
    )
    assert same["pairs"] == 2 and same["auxiliary_S_pair_AUC"] == 0.5
    assert valid["pairs"] == 1 and len(frame) == 4


def test_inference_keys_exclude_fit_and_cannot_read_a_sealed_year_as_2022(diagnostic):
    x = pd.DataFrame(
        {
            "grid_id": ["A", "B"],
            "prediction_timestamp_utc": ["2021-05-01T00:00:00+00:00", "2022-05-01T00:00:00+00:00"],
        }
    )
    roles = x.copy()
    for field in diagnostic.join.feature_names():
        x[field] = 0.2
    roles["review_temporal_role"] = ["proposed_fit_2018_2021", "proposed_assessment_2022"]
    roles["target"] = roles["accepted_L_membership"] = np.nan
    roles["daily_observation_status"] = "unknown"
    roles["role_is_model_training_permission"] = False
    qa = x[diagnostic.join.KEYS].copy()
    held, _, _ = diagnostic.held_calendar(x, qa, roles)
    assert held.grid_id.tolist() == ["B"]
    roles.loc[1, "prediction_timestamp_utc"] = "2024-05-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="2022 midnight"):
        diagnostic.held_calendar(x, qa, roles)
