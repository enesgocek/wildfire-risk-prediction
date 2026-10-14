"""Quality counts cannot silently become eligibility or binary labels."""

from copy import deepcopy

import pytest

from wildfire_risk_prediction import dataset_batch as batch
from wildfire_risk_prediction import dataset_quality as quality
from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_month


@pytest.fixture
def reports():
    return [
        {
            "status": "complete_month_candidate_readback_passed",
            "version": feature_month.VERSION,
            "month": item["month"],
            "split": "train",
            "days": feature_month.calendar_days(item["month"]),
            "rows": item["candidate_rows_before_exclusions"],
            "candidate_features": join.feature_names(),
            "inputs_unchanged": True,
            "daily_observation_status": "unknown",
            "missing_by_feature": dict.fromkeys(join.feature_names(), 0),
            "vegetation_supported_cell_days": {"30": 0, "60": 0},
            **dict.fromkeys(feature_month.FALSE_FLAGS, False),
        }
        for item in batch.calendar_inventory()
    ]


def test_weighted_marginal_counts_do_not_invent_complete_cases(reports):
    reports[0]["missing_by_feature"][join.feature_names()[0]] = 100
    reports[1]["missing_by_feature"][join.feature_names()[0]] = 200
    original = deepcopy(reports)
    result = quality.summarize(reports)
    assert result["rows"] == 6351709 and result["days"] == 2191
    first = result["features"][0]
    assert first["missing_cell_days"] == 300
    assert first["missing_fraction"] == 300 / 6351709
    assert first["worst_month"] == "2018-02"
    assert result["complete_case_rows"] is result["eligible_training_rows"] is None
    assert sum(y["rows"] for y in result["yearly"]) == result["rows"]
    assert reports == original


@pytest.mark.parametrize(
    "change", ["duplicate", "partial", "heldout", "gate", "schema", "calendar"]
)
def test_bad_scope_and_acceptance_rejected(reports, change):
    if change == "duplicate":
        reports[-1] = deepcopy(reports[0])
    elif change == "partial":
        reports.pop()
    elif change == "heldout":
        reports[-1]["month"] = "2025-01"
    elif change == "gate":
        reports[0]["negative_label_permitted"] = True
    elif change == "schema":
        reports[0]["missing_by_feature"]["target"] = 0
    else:
        reports[0]["days"].pop()
    with pytest.raises(ValueError):
        quality.summarize(reports)


@pytest.mark.parametrize("bad_count", [-1, 89870, True, 0.5, "1"])
def test_invalid_marginal_counts_rejected(reports, bad_count):
    reports[0]["missing_by_feature"][join.feature_names()[0]] = bad_count
    with pytest.raises(ValueError):
        quality.summarize(reports)


def test_source_gaps_flag_closed_midnight_endpoint_without_applying_exclusions():
    review = quality.source_gap_review(["2018-06-13", "2023-12-31"])
    assert review["conservative_target_review_dates"] == [
        "2018-06-12",
        "2018-06-13",
        "2023-12-30",
        "2023-12-31",
    ]
    assert review["calendar_cell_days_to_review"] == 11596
    assert not review["automatic_exclusions_applied"] and review["negative_labels_created"] == 0


def test_gap_at_training_start_does_not_open_previous_split():
    result = quality.source_gap_review(["2018-01-01"])
    assert result["conservative_target_review_dates"] == ["2018-01-01"]


@pytest.mark.parametrize("days", [["2024-01-01"], ["2025-01-01"], ["2018-06-13"] * 2])
def test_gap_scope_does_not_open_validation_or_test(days):
    with pytest.raises(ValueError):
        quality.source_gap_review(days)
