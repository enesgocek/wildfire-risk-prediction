import importlib.util
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def audit():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/quality/audit_calendar_fixed_model_diagnostic.py"
    )
    spec = importlib.util.spec_from_file_location("calendar_scalar_audit_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scalar_same_stratum_credit_does_not_use_other_grids_or_drop_input_rows(audit):
    frame = pd.DataFrame(
        {
            "grid_id": ["A", "A", "B", "B"],
            "prediction_timestamp_utc": ["2022-05-01T00:00:00+00:00", "2022-05-02T00:00:00+00:00"]
            * 2,
            audit.INDICATOR: [True, False, True, False],
            "weather_complete": [True, True, True, False],
            "complete_27_features": [True] * 4,
            "score": [0.4, 0.4, 0.9, 0.9],
        }
    )
    result = audit.scalar_credit(frame, "score", within=True, quality="all")
    assert result["pairs"] == 2 and result["doubled_credit"] == 2
    assert result["auxiliary_S_pair_AUC"] == 0.5
    result = audit.scalar_credit(frame, "score", within=True, quality="complete_weather_both")
    assert result["pairs"] == 1 and len(frame) == 4
    frame["weather_complete"] = False
    result = audit.scalar_credit(frame, "score", within=True, quality="complete_weather_both")
    assert result["pairs"] == 0 and result["auxiliary_S_pair_AUC"] is None


def test_broad_rank_sum_and_stratum_scalar_credit_agree_with_exact_tie_example(audit):
    frame = pd.DataFrame(
        {
            "grid_id": ["A"] * 4,
            "prediction_timestamp_utc": [f"2022-05-{d:02d}T00:00:00+00:00" for d in (1, 2, 3, 4)],
            audit.INDICATOR: [True, True, False, False],
            "weather_complete": [True] * 4,
            "complete_27_features": [True] * 4,
            "score": [0.2, 0.5, 0.5, 0.9],
        }
    )
    for within in (False, True):
        result = audit.scalar_credit(frame, "score", within=within, quality="all")
        assert result["pairs"] == 4 and result["doubled_credit"] == 1
        assert result["auxiliary_S_pair_AUC"] == 0.125
