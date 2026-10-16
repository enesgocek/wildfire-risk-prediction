import math

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.evaluation_alerts import daily_alerts
from wildfire_risk_prediction.evaluation_folds import audit_training_fold, forward_year_skeleton
from wildfire_risk_prediction.evaluation_metrics import (
    binary_metrics,
    calibration_bins,
    compare_training_predictions,
)


def metadata(day, event="one", grid="g1", block="west"):
    return pd.DataFrame(
        {
            "grid_id": [grid],
            "prediction_timestamp_utc": [day + "T00:00:00Z"],
            "event_ids": [[event]] if event else [[]],
            "event_membership_complete": [True],
            "spatial_block": [block],
        }
    )


def alerts():
    return pd.DataFrame(
        {
            "grid_id": ["b", "a", "c", "d"],
            "prediction_timestamp_utc": ["2021-07-01T00:00:00Z"] * 3 + ["2021-07-02T00:00:00Z"],
            "probability": [0.9, 0.9, 0.2, 0.8],
            "target": [None, 0.0, 1.0, None],
        }
    )


def test_ap_and_trapezoid_are_distinct_on_hand_computable_example():
    result = binary_metrics([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])
    assert result["average_precision"] == pytest.approx(5 / 6)
    assert result["pr_auc_trapezoid"] == pytest.approx(19 / 24)
    assert result["roc_auc"] == pytest.approx(0.75)
    assert result["prevalence"] == 0.5
    assert result["brier_binary"] == pytest.approx((0.01 + 0.16 + 0.65**2 + 0.04) / 4)


def test_ties_are_grouped_without_using_input_order_to_improve_ap():
    scores = []
    for order in ([0, 1, 2, 3], [3, 2, 1, 0], [1, 3, 0, 2]):
        result = binary_metrics(np.array([0, 1, 0, 1])[order], [0.5] * 4)
        scores.append(result["average_precision"])
        assert result["roc_auc"] == 0.5
    assert scores == [0.5, 0.5, 0.5]


@pytest.mark.parametrize("y,p,expected", [([0, 1], [0.0, 1.0], 1.0), ([0, 1], [1.0, 0.0], 0.5)])
def test_perfect_and_reversed_rankings(y, p, expected):
    result = binary_metrics(y, p)
    assert result["average_precision"] == expected
    assert math.isfinite(result["log_loss"]) and result["log_loss_clipped_count"] == 2


@pytest.mark.parametrize("y", [[0, 0], [1, 1]])
def test_single_class_has_probability_losses_but_no_discrimination_claim(y):
    result = binary_metrics(y, [0.2, 0.8])
    assert result["ranking_metric_status"] == "undefined_single_class"
    assert all(result[k] is None for k in ("average_precision", "pr_auc_trapezoid", "roc_auc"))
    assert math.isfinite(result["brier_binary"]) and math.isfinite(result["log_loss"])


@pytest.mark.parametrize(
    "y,p",
    [
        ([], []),
        ([0, 1], [0.5]),
        ([0, None], [0.2, 0.8]),
        ([0, np.nan], [0.2, 0.8]),
        ([0, 2], [0.2, 0.8]),
        (["0", "1"], [0.2, 0.8]),
        ([0, 1], [0.2, np.inf]),
        ([0, 1], [0.2, np.nan]),
        ([0, 1], [-0.01, 0.5]),
        ([0, 1], [0.5, 1.01]),
        ([[0, 1]], [[0.2, 0.8]]),
        ([0, 1], [".2", ".8"]),
    ],
)
def test_bad_or_unknown_scoring_inputs_rejected(y, p):
    with pytest.raises(ValueError):
        binary_metrics(y, p)


def test_calibration_bin_edges_empty_bins_and_one_are_accounted_for():
    bins = calibration_bins([0, 1, 0], [0.0, 0.5, 1.0], bin_count=4)
    assert bins["count"].tolist() == [1, 0, 1, 1]
    assert bins.loc[1, ["mean_probability", "observed_fraction"]].isna().all()
    assert bins["count"].sum() == 3 and bins.loc[3, "mean_probability"] == 1


def test_decimal_bin_boundary_is_not_moved_left_by_multiply_roundoff():
    bins = calibration_bins([1], [0.58], bin_count=50)
    assert bins.loc[29, "count"] == 1 and bins.loc[28, "count"] == 0


def test_paired_models_align_keys_instead_of_pairing_by_row_order():
    frame = alerts().iloc[:3].copy()
    frame["target"] = [0, 1, 0]
    reversed_rows = frame.iloc[::-1]
    result = compare_training_predictions(frame, reversed_rows)
    assert result["sample_count"] == 3
    assert all(value == 0 for value in result["right_minus_left"].values())
    assert result["confidence_intervals"] is None and not result["labels_accepted"]


@pytest.mark.parametrize(
    "change",
    ["missing_row", "different_key", "different_target", "duplicate_key", "unknown_target", "2025"],
)
def test_paired_model_comparison_rejects_changed_evaluation_universe(change):
    left = alerts().iloc[:3].copy()
    left["target"] = [0, 1, 0]
    right = left.copy()
    if change == "missing_row":
        right = right.iloc[1:]
    if change == "different_key":
        right.loc[0, "grid_id"] = "other"
    if change == "different_target":
        right.loc[0, "target"] = 1
    if change == "duplicate_key":
        right = pd.concat([right, right.iloc[[0]]])
    if change == "unknown_target":
        right["target"] = pd.Series([0, None, 0], dtype=object)
    if change == "2025":
        right["prediction_timestamp_utc"] = "2025-01-01T00:00:00Z"
    with pytest.raises(ValueError):
        compare_training_predictions(left, right)


@pytest.mark.parametrize("count", [None, 0, -1, True, 2.5, 1001])
def test_calibration_requires_explicit_valid_bin_count(count):
    with pytest.raises(ValueError):
        calibration_bins([0, 1], [0.2, 0.8], bin_count=count)


def test_adjacent_open_closed_daily_windows_can_meet_without_overlap():
    result = audit_training_fold(
        metadata("2021-01-01"), metadata("2021-01-02", "two"), embargo_hours=0
    )
    assert not result["labels_accepted"] and not result["model_ready"]
    with pytest.raises(ValueError, match="embargo"):
        audit_training_fold(metadata("2021-01-01"), metadata("2021-01-02", "two"), embargo_hours=1)


def test_shared_event_is_detected_even_when_secondary_in_multi_event_membership():
    train = metadata("2021-01-01")
    validation = metadata("2021-02-01", "two")
    validation.at[0, "event_ids"] = ["two", "one"]
    with pytest.raises(ValueError, match="Same event"):
        audit_training_fold(train, validation, embargo_hours=24)


@pytest.mark.parametrize(
    "change",
    [
        "future_training",
        "2024",
        "2025",
        "unknown_events",
        "string_membership",
        "duplicate_event",
        "non_midnight",
        "naive",
        "null_time",
        "duplicate_utc",
    ],
)
def test_time_and_event_leakage_guard_rejects_invalid_fold_metadata(change):
    train, held = metadata("2021-01-01"), metadata("2021-03-01", "two")
    if change == "future_training":
        train = metadata("2022-01-01")
    if change in {"2024", "2025"}:
        held = metadata(change + "-01-01", "two")
    if change == "unknown_events":
        train["event_membership_complete"] = False
    if change == "string_membership":
        train.at[0, "event_ids"] = "one"
    if change == "duplicate_event":
        train.at[0, "event_ids"] = ["one", "one"]
    if change == "non_midnight":
        train.at[0, "prediction_timestamp_utc"] = "2021-01-01T01:00:00Z"
    if change == "naive":
        train.at[0, "prediction_timestamp_utc"] = "2021-01-01T00:00:00"
    if change == "null_time":
        train.at[0, "prediction_timestamp_utc"] = None
    if change == "duplicate_utc":
        train = pd.concat(
            [train, train.assign(prediction_timestamp_utc="2021-01-01T00:00:00+00:00")]
        )
    with pytest.raises(ValueError):
        audit_training_fold(train, held, embargo_hours=0)


@pytest.mark.parametrize("hours", [None, True, -1, 0.5, float("nan"), float("inf")])
def test_embargo_is_never_implicitly_chosen(hours):
    with pytest.raises(ValueError):
        audit_training_fold(
            metadata("2021-01-01"), metadata("2022-01-01", "two"), embargo_hours=hours
        )


def test_spatial_block_check_is_explicit_and_distinct_from_temporal_check():
    train, held = metadata("2021-01-01"), metadata("2022-01-01", "two")
    assert not audit_training_fold(train, held, embargo_hours=24)["spatial_blocks_checked"]
    with pytest.raises(ValueError, match="Spatial blocks"):
        audit_training_fold(train, held, embargo_hours=24, spatial_column="spatial_block")
    held["spatial_block"] = "east"
    assert audit_training_fold(train, held, embargo_hours=24, spatial_column="spatial_block")[
        "spatial_blocks_checked"
    ]


def test_forward_year_skeleton_never_enters_validation_or_final_and_keeps_policy_pending():
    plans = forward_year_skeleton()
    assert [p["held_out_year"] for p in plans] == [2019, 2020, 2021, 2022, 2023]
    assert all(max(p["fit_years"]) < p["held_out_year"] for p in plans)
    assert all(
        p["embargo_hours"] is None and p["event_boundary_policy"] == "pending" for p in plans
    )


def test_alert_capacity_tie_order_unknown_and_small_days_are_separate():
    source = alerts()
    before = source.copy(deep=True)
    selected, counts = daily_alerts(source, capacity=2, tie_policy="grid_id_ascending")
    pd.testing.assert_frame_equal(source, before)
    assert selected.loc[selected.selected, "grid_id"].tolist() == ["b", "a", "d"]
    assert counts.selected_cells.tolist() == [2, 1]
    assert counts.selected_verified_negative_cells.tolist() == [1, 0]
    assert counts.selected_unadjudicated_cells.tolist() == [1, 1]
    assert counts.unique_event_recall.isna().all()
    assert counts.loc[0, "verified_false_alerts_per_1000_adjudicated_units"] == 500
    assert pd.isna(counts.loc[1, "verified_false_alerts_per_1000_adjudicated_units"])
    one, _ = daily_alerts(source, capacity=1, tie_policy="grid_id_ascending")
    assert one.loc[one.selected, "grid_id"].tolist() == ["a", "d"]


def test_utc_spellings_share_capacity_but_duplicate_identity_is_rejected():
    source = alerts()
    source.loc[0, "prediction_timestamp_utc"] = "2021-07-01T00:00:00+00:00"
    _, counts = daily_alerts(source, capacity=1, tie_policy="grid_id_ascending")
    assert len(counts) == 2 and counts.selected_cells.eq(1).all()
    source = pd.concat(
        [source, source.iloc[[0]].assign(prediction_timestamp_utc="2021-07-01T00:00:00Z")]
    )
    with pytest.raises(ValueError, match="Canonical UTC"):
        daily_alerts(source, capacity=1, tie_policy="grid_id_ascending")


@pytest.mark.parametrize(
    "capacity,tie",
    [
        (None, "grid_id_ascending"),
        (True, "grid_id_ascending"),
        (0, "grid_id_ascending"),
        (1, None),
        (1, "target_descending"),
    ],
)
def test_alert_policy_must_be_explicit_and_never_use_target_to_break_tie(capacity, tie):
    with pytest.raises(ValueError):
        daily_alerts(alerts(), capacity=capacity, tie_policy=tie)


@pytest.mark.parametrize(
    "change",
    [
        "bad_target",
        "missing_score",
        "out_of_range_score",
        "holdout",
        "missing_grid",
        "naive_time",
        "duplicate_key",
    ],
)
def test_alert_accounting_rejects_invalid_universe_instead_of_dropping_rows(change):
    frame = alerts()
    if change == "bad_target":
        frame.loc[0, "target"] = 2
    if change == "missing_score":
        frame.loc[0, "probability"] = np.nan
    if change == "out_of_range_score":
        frame.loc[0, "probability"] = 1.1
    if change == "holdout":
        frame.loc[0, "prediction_timestamp_utc"] = "2024-01-01T00:00:00Z"
    if change == "missing_grid":
        frame.loc[0, "grid_id"] = None
    if change == "naive_time":
        frame.loc[0, "prediction_timestamp_utc"] = "2021-07-01T00:00:00"
    if change == "duplicate_key":
        frame = pd.concat([frame, frame.iloc[[0]]])
    with pytest.raises(ValueError):
        daily_alerts(frame, capacity=1, tie_policy="grid_id_ascending")
