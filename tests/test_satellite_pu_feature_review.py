import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def review(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "satellite_features_test", folder / "prepare_satellite_pu_feature_review.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parts():
    first = pd.DataFrame(
        {
            "grid_id": ["A", "B"],
            "prediction_timestamp_utc": ["2021-06-01T00:00:00+00:00"] * 2,
            "x": [0.0, np.nan],
        }
    )
    second = first.copy()
    second["grid_id"] = ["B", "C"]
    second["x"] = [np.nan, 2.0]
    return first, second


def test_one_feature_key_can_keep_two_provenance_roles_without_row_loss_or_imputation(review):
    first, second = parts()
    result = review.combine_exact(first, second)
    assert result.grid_id.tolist() == ["A", "B", "C"]
    assert result.x.iloc[0] == 0 and pd.isna(result.x.iloc[1]) and result.x.iloc[2] == 2


def test_conflicting_same_key_or_duplicate_snapshot_is_rejected(review):
    first, second = parts()
    second.loc[0, "x"] = 7
    with pytest.raises(AssertionError):
        review.combine_exact(first, second)
    with pytest.raises(ValueError):
        review.combine_exact(pd.concat([first, first]), second)


def test_unknown_role_targets_roundtrip_without_losing_two_possible_roles(review):
    from wildfire_risk_prediction.feature_partition import parse_csv

    first, _ = parts()
    keys = set(first[review.join.KEYS].itertuples(index=False, name=None))
    table = review.roles_table(first, keys, keys)
    assert table.original_U_sample_present.all() and table.possible_L_proposal_present.all()
    assert table.target.isna().all() and table.accepted_L_membership.isna().all()
    saved = parse_csv(table.to_csv(index=False).encode())
    pd.testing.assert_frame_equal(table, saved, check_dtype=False, check_exact=True)
