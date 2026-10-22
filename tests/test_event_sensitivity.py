import pandas as pd
import pytest

from wildfire_risk_prediction.event_sensitivity import summarize_candidates
from wildfire_risk_prediction.label_protocol_review import SCENARIOS

GRID = "E6933_5K_V1_C520_R916"


def evidence():
    return pd.DataFrame(
        [
            {
                "scenario": s,
                "candidate_component_id": s + "_C1",
                "membership_sha256": "a" * 64,
                "grid_id": GRID,
                "first_detection_utc": "2021-01-02T01:00:00+00:00",
                "prediction_timestamp_utc": "2021-01-02T00:00:00+00:00",
                "review_flags_json": "[]",
            }
            for s in SCENARIOS
        ]
    )


def test_all_agreement_is_unlabelled_and_permutation_invariant():
    data = evidence()
    result = summarize_candidates(data)
    pd.testing.assert_frame_equal(result, summarize_candidates(data.sample(frac=1, random_state=2)))
    row = result.iloc[0]
    assert row.scenarios_with_candidate == 9
    assert row.review_category == "all_presence_time_and_membership_equal"
    assert result.target.isna().all()
    assert not row.positive_label_permitted and not row.negative_label_permitted
    assert not row.event_membership_complete


def test_partial_support_never_creates_background_zero():
    data = evidence()
    data.loc[0, "grid_id"] = "E6933_5K_V1_C521_R916"
    result = summarize_candidates(data)
    assert sorted(result.scenarios_with_candidate) == [1, 8]
    assert result.review_category.eq("candidate_presence_sensitive").all()
    assert result.target.isna().all()


@pytest.mark.parametrize(
    "field,value",
    [
        ("membership_sha256", "b" * 64),
        ("first_detection_utc", "2021-01-02T02:00:00+00:00"),
    ],
)
def test_presence_agreement_is_not_membership_or_first_time_agreement(field, value):
    data = evidence()
    data.loc[0, field] = value
    row = summarize_candidates(data).iloc[0]
    assert row.scenarios_with_candidate == 9
    assert row.review_category == "all_presence_time_or_membership_sensitive"


def test_multiple_components_in_one_scenario_count_as_one_support():
    data = evidence()
    extra = data.iloc[[0]].copy()
    extra["candidate_component_id"] += "_other"
    extra["membership_sha256"] = "b" * 64
    row = summarize_candidates(pd.concat([data, extra])).iloc[0]
    assert row.scenarios_with_candidate == 9
    assert row.component_matches_max_present_scenario == 2


def test_tied_first_cells_stay_under_common_component_identity():
    data = evidence()
    extra = data.copy()
    extra["grid_id"] = "E6933_5K_V1_C521_R916"
    result = summarize_candidates(pd.concat([data, extra]))
    assert len(result) == 2 and result.scenarios_with_candidate.eq(9).all()


def test_midnight_first_detection_preserves_previous_training_boundary_context():
    data = evidence()
    data["first_detection_utc"] = "2018-01-01T00:00:00+00:00"
    data["prediction_timestamp_utc"] = "2017-12-31T00:00:00+00:00"
    assert not summarize_candidates(data).iloc[0].prediction_inside_training


@pytest.mark.parametrize(
    "case", ["missing_scenario", "duplicate", "holdout", "target", "wrong_window", "bad_hash"]
)
def test_invalid_evidence_rejected(case):
    data = evidence()
    if case == "missing_scenario":
        data = data.iloc[1:]
    elif case == "duplicate":
        data = pd.concat([data, data.iloc[[0]]])
    elif case == "holdout":
        data["first_detection_utc"] = "2024-01-01T01:00:00+00:00"
        data["prediction_timestamp_utc"] = "2024-01-01T00:00:00+00:00"
    elif case == "target":
        data["target"] = 1
    elif case == "wrong_window":
        data.loc[0, "prediction_timestamp_utc"] = "2021-01-01T00:00:00+00:00"
    elif case == "bad_hash":
        data.loc[0, "membership_sha256"] = "invalid"
    with pytest.raises(ValueError):
        summarize_candidates(data)
