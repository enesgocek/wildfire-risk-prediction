import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def pilot():
    path = Path(__file__).resolve().parents[1] / "scripts/quality/run_temporal_pairwise_pilot.py"
    spec = importlib.util.spec_from_file_location("temporal_pairwise_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "flag",
    ["final_merge_permitted", "negative_label_permitted", "cloud_permitted", "fit_intercept"],
)
def test_pairwise_choice_cannot_open_other_work(pilot, flag):
    config = json.loads(pilot.CONFIG.read_bytes())
    with pytest.raises(ValueError):
        pilot.validate(config | {flag: True})


def test_pairs_are_same_grid_month_role_complete_and_exclude_other_source_days(pilot):
    frame = pd.DataFrame(
        {
            "grid_id": ["A"] * 5 + ["B"],
            "prediction_timestamp_utc": [
                f"2022-{m:02d}-{d:02d}T00:00:00+00:00"
                for m, d in [(5, 1), (5, 2), (5, 3), (5, 4), (6, 1), (5, 1)]
            ],
            "review_temporal_role": [pilot.HELD] * 4 + [pilot.FIT, pilot.HELD],
        }
    )
    source = {tuple(frame.loc[i, pilot.join.KEYS]) for i in (0, 2, 4, 5)}
    a, b = pilot.pair_indices(
        frame, pd.Series([True, True, True, False, True, True]), source, pilot.HELD
    )
    assert list(zip(a, b, strict=True)) == [(0, 1), (2, 1)]
    assert len(frame) == 6
    result = pilot.credit(np.array([0.5, 0.5, 0.2, np.nan, np.nan, 1.0]), a, b)
    assert result["pairs"] == 2 and result["auxiliary_pair_AUC"] == 0.25
