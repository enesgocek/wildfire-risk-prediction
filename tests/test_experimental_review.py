import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.experimental_review import memberships
from wildfire_risk_prediction.feature_join import feature_names


def inputs():
    x = pd.DataFrame(
        {
            "grid_id": ["a", "a"],
            "prediction_timestamp_utc": ["2022-01-01T00:00:00+00:00", "2022-01-02T00:00:00+00:00"],
        }
    )
    for name in feature_names():
        x[name] = [1.0, np.nan]
    m = x[["grid_id", "prediction_timestamp_utc"]].copy()
    m["target"], m["accepted_L_membership"] = np.nan, np.nan
    m["daily_observation_status"] = "unknown"
    m["known_proposal_key_in_union"] = [True, False]
    lineage = pd.DataFrame(
        {
            "scenario": ["A", "B"],
            "grid_id": ["a", "a"],
            "prediction_timestamp_utc": [x.prediction_timestamp_utc[0]] * 2,
            "possible_L_proposal": [True, False],
        }
    )
    return x, m, lineage


def test_proposals_remain_scenario_specific_and_missingness_is_preserved():
    x, m, lineage = inputs()
    r = memberships(x, m, lineage, ["A", "B"])
    assert r.scenario_proposal_bitmask_for_display_only.tolist() == [1, 0]
    assert r.missing_feature_count.tolist() == [0, 27]
    assert r.target.isna().all() and not r.negative_label_permitted.any()
    assert x.iloc[1][feature_names()].isna().all()


def test_true_labels_and_new_proposal_keys_are_rejected():
    x, m, lineage = inputs()
    m.loc[0, "target"] = 1
    with pytest.raises(ValueError, match="Unassigned"):
        memberships(x, m, lineage, ["A", "B"])
    x, m, lineage = inputs()
    lineage.loc[0, "grid_id"] = "outside"
    with pytest.raises(ValueError, match="retained"):
        memberships(x, m, lineage, ["A", "B"])


def test_key_order_and_proposal_union_cannot_silently_change():
    x, m, lineage = inputs()
    with pytest.raises(AssertionError):
        memberships(x, m.iloc[::-1].reset_index(drop=True), lineage, ["A", "B"])
    m.loc[0, "known_proposal_key_in_union"] = False
    with pytest.raises(ValueError, match="union"):
        memberships(x, m, lineage, ["A", "B"])


def test_later_years_cannot_enter_inspection_scope():
    x, m, lineage = inputs()
    stamp = "2023-01-01T00:00:00+00:00"
    x.loc[0, "prediction_timestamp_utc"] = stamp
    m.loc[0, "prediction_timestamp_utc"] = stamp
    lineage.loc[0, "prediction_timestamp_utc"] = stamp
    with pytest.raises(ValueError, match="approved"):
        memberships(x, m, lineage, ["A", "B"])


def test_ISO_source_times_allow_fractional_and_whole_seconds_without_accepting_garbage():
    path = Path(__file__).resolve().parents[1] / "scripts/quality/audit_experimental_su_bundle.py"
    spec = importlib.util.spec_from_file_location("su_time_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parsed = module.parse_source_times(
        pd.Series(["2019-03-20T08:28:02.123+00:00", "2019-03-20T08:28:02+00:00", None, "invalid"])
    )
    assert parsed.notna().tolist() == [True, True, False, False]
