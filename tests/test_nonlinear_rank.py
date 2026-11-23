import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.nonlinear_rank import (
    evaluate_slices,
    finite_features,
    matched_pairs,
    training_layout,
    validate_execution,
)
from wildfire_risk_prediction.ranking_queries import DYNAMIC_FEATURES

ROOT = Path(__file__).resolve().parents[1]


def metadata():
    return pd.DataFrame(
        {
            "grid_id": ["b", "a", "a", "a", "b", "a", "a"],
            "prediction_timestamp_utc": [
                "2021-01-01T00:00:00+00:00",
                "2021-01-01T00:00:00+00:00",
                "2021-01-02T00:00:00+00:00",
                "2021-02-01T00:00:00+00:00",
                "2021-01-02T00:00:00+00:00",
                "2022-01-01T00:00:00+00:00",
                "2022-01-03T00:00:00+00:00",
            ],
            "review_temporal_role": ["proposed_fit_2018_2021"] * 5
            + ["proposed_assessment_2022"] * 2,
            "target": [np.nan] * 7,
            "accepted_L_membership": [np.nan] * 7,
            "daily_observation_status": ["unknown"] * 7,
        }
    )


def test_training_only_mixed_complete_queries_with_sorted_qid_and_no_held_rows():
    m = metadata()
    source = np.array([True, True, False, True, False, True, False])
    complete = np.array([True, True, True, True, False, True, True])
    r = training_layout(m, source, complete)
    assert r.calendar_row.tolist() == [1, 2]
    assert r.qid.tolist() == [0, 0]
    assert r.relevance_source_context_not_Y.tolist() == [True, False]
    assert m.target.isna().all() and m.accepted_L_membership.isna().all()
    complete[4] = True
    r = training_layout(m, source, complete)
    assert r.calendar_row.tolist() == [1, 2, 0, 4]
    assert r.qid.tolist() == [0, 0, 1, 1]


def test_pair_identity_and_temporal_direction_ties_are_source_ordering_only():
    m = metadata()
    source = np.array([True, True, False, True, False, True, False])
    pairs = matched_pairs(m, source, np.ones(7, dtype=bool), "proposed_assessment_2022")
    assert pairs.to_numpy().tolist() == [[5, 6]]
    values = np.arange(7, dtype=float)
    metrics = {r["slice"]: r for r in evaluate_slices(m, pairs, values)}
    assert metrics["all_same_grid_month"]["auxiliary_pair_AUC"] == 0
    assert metrics["other_day_before_source_day"]["pairs"] == 0
    assert metrics["other_day_after_source_day"]["pairs"] == 1
    metrics = {r["slice"]: r for r in evaluate_slices(m, pairs, np.zeros(7))}
    assert metrics["gap_1_to_3_days"]["auxiliary_pair_AUC"] == 0.5
    assert metrics["gap_4_to_30_days"]["auxiliary_pair_AUC"] is None


def test_finite_support_rejects_infinities_without_imputation():
    x = metadata().iloc[:2].copy()
    for field in DYNAMIC_FEATURES:
        x[field] = [0.0, 1.0]
    x.loc[1, DYNAMIC_FEATURES[0]] = np.inf
    assert finite_features(x).tolist() == [True, False]


def test_temporal_role_tampering_or_true_label_is_not_training_permission():
    m = metadata()
    m.loc[5, "review_temporal_role"] = "proposed_fit_2018_2021"
    with pytest.raises(ValueError, match="pilot years"):
        training_layout(m, np.ones(7, dtype=bool), np.ones(7, dtype=bool))
    m = metadata()
    m.loc[0, "target"] = 1
    with pytest.raises(ValueError, match="Unassigned"):
        training_layout(m, np.ones(7, dtype=bool), np.ones(7, dtype=bool))


def test_execution_cannot_widen_scope_or_rewrite_historical_proposal():
    p = json.loads((ROOT / "configs/nonlinear_rank_execution_v1.json").read_bytes())
    proposal = json.loads((ROOT / "configs/nonlinear_rank_proposal_v1.json").read_bytes())
    validate_execution(p, proposal)
    for name in (
        "final_merge_permitted",
        "cloud_permitted",
        "negative_label_permitted",
        "scientific_values_2023_2024_2025_read_permitted",
        "hyperparameter_search_permitted",
    ):
        with pytest.raises(ValueError, match="Historical proposal"):
            validate_execution(p | {name: True}, proposal)
    with pytest.raises(ValueError, match="Bounded"):
        validate_execution(p | {"new_models_authorized": 10}, proposal)
    with pytest.raises(ValueError, match="Historical proposal"):
        validate_execution(p, proposal | {"new_training_authorized": True})


def audit_module():
    spec = importlib.util.spec_from_file_location(
        "audit_nonlinear", ROOT / "scripts/quality/audit_nonlinear_rank_comparison.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_independent_cartesian_audit_finds_exact_pair_keys_and_rejects_duplicates(tmp_path):
    audit = audit_module()
    meta = metadata()
    result = audit.cartesian(
        meta,
        np.array([True, True, False, True, False, True, False]),
        np.ones(7, dtype=bool),
        [2022],
    )
    assert result.tolist() == [[5, 6]]
    file = tmp_path / "pairs.csv"
    pd.DataFrame([[5, 6], [5, 6]]).to_csv(file, index=False)
    with pytest.raises(ValueError, match="duplicated"):
        audit.checked_pairs(file, result)


def test_independent_metric_audit_detects_wrong_credit_and_ascii_province():
    audit = audit_module()
    meta = metadata()
    meta["province_area_intersections"] = "Izmir"
    pairs = np.array([[5, 6]])
    table = pd.DataFrame(
        [
            {
                "variant": "XGBoost",
                "slice": "province_Izmir",
                "pairs": 1,
                "wins": 0,
                "ties": 1,
                "auxiliary_pair_AUC": 0.5,
            }
        ]
    )
    audit.verify_metrics(table, meta, pairs, np.zeros(7), np.ones(7))
    table.loc[0, "auxiliary_pair_AUC"] = 1.0
    with pytest.raises(ValueError, match="recomputed"):
        audit.verify_metrics(table, meta, pairs, np.zeros(7), np.ones(7))
