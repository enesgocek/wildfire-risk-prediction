import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


def test_independent_pair_enumerator_keeps_exact_grid_year_month_and_half_tie():
    path = Path(__file__).resolve().parents[1] / "scripts/quality/audit_temporal_pairwise_pilot.py"
    spec = importlib.util.spec_from_file_location("temporal_pairwise_audit_test", path)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    rows = pd.DataFrame(
        {
            "grid_id": ["A", "A", "A", "B"],
            "prediction_timestamp_utc": [
                "2022-05-01T00:00:00+00:00",
                "2022-05-02T00:00:00+00:00",
                "2021-05-02T00:00:00+00:00",
                "2022-05-02T00:00:00+00:00",
            ],
            "review_temporal_role": ["held"] * 4,
        }
    )
    source = {tuple(rows.loc[0, audit.KEYS])}
    pairs = audit.independent_pairs(rows, np.array([True] * 4), source, "held")
    assert pairs == {(0, 1)}
    assert audit.independent_credit([0.4, 0.4, 0.9, 0.9], pairs) == 0.5
