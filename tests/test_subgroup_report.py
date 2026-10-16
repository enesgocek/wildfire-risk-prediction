import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.subgroup_report import METRICS, PROVINCES, grouped_report


def fixture():
    frame = pd.DataFrame(
        {
            "grid_id": [f"synthetic_{i}" for i in range(8)],
            "prediction_timestamp_utc": ["2021-07-01T00:00:00Z"] * 4
            + ["2021-01-01T00:00:00Z"] * 2
            + ["2021-04-01T00:00:00Z", "2021-10-01T00:00:00Z"],
            "primary_province": ["Mersin"] * 4 + ["Antalya"] * 2 + [PROVINCES[2], PROVINCES[1]],
            "calendar_season": ["summer"] * 4 + ["winter"] * 2 + ["spring", "autumn"],
            "nominal_land_fraction": [1.0, 0, 1.0, np.nan, 0, 1, 1, 1],
            "target": [0, 0, 1, 1, np.nan, 1, 0, 0],
            "probability": [0.1, 0.4, 0.35, 0.8, 0.9, 0.7, np.nan, 0.2],
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "labels_created": False,
            "accepted_label_rule": False,
        }
    )
    return frame


def row(report, dimension="all", stratum="all"):
    return report.loc[report.dimension.eq(dimension) & report.stratum.eq(stratum)].iloc[0]


def test_explicit_denominators_preserve_every_marginal_and_no_partial_scores():
    report = grouped_report(fixture(), scope="synthetic_scores")
    assert len(report) == 28
    all_units = row(report)
    assert all_units.unit_count == 8
    assert all_units.known_target_count == 7
    assert all_units.positive_count == 3
    assert all_units.verified_negative_count == 4
    assert all_units.unknown_target_count == 1
    assert all_units.prediction_present_count == 7
    assert all_units.prediction_missing_count == 1
    assert all_units.paired_known_prediction_count == 6
    assert all_units.known_without_prediction_count == 1
    assert all_units.unknown_with_prediction_count == 1
    assert all_units.unknown_without_prediction_count == 0
    assert all_units.known_target_positive_fraction == pytest.approx(3 / 7)
    assert all_units[list(METRICS)].isna().all()
    for _, group in report.groupby("dimension"):
        assert group.unit_count.sum() == 8
        assert group.known_target_count.sum() == 7
        assert group.unknown_target_count.sum() == 1


def test_fully_known_synthetic_group_matches_hand_example_and_single_class_undefined():
    report = grouped_report(fixture(), scope="synthetic_scores")
    mersin = row(report, "primary_province", "Mersin")
    assert mersin.average_precision == pytest.approx(5 / 6)
    assert mersin.pr_auc_trapezoid == pytest.approx(19 / 24)
    assert mersin.brier_binary == pytest.approx((0.01 + 0.16 + 0.65**2 + 0.04) / 4)
    single = row(report, "primary_province", PROVINCES[1])
    assert single.brier_binary == pytest.approx(0.04)
    assert pd.isna(single.average_precision)
    assert single.ranking_metric_status == "undefined_single_class"
    assert single.statistical_support_status == "not_assessed"


def test_empty_groups_keep_zero_counts_and_null_metrics_not_perfect_scores():
    report = grouped_report(fixture(), scope="synthetic_scores")
    empty = row(report, "province_season", "Antalya|summer")
    assert empty.unit_count == empty.positive_count == empty.verified_negative_count == 0
    assert empty.metric_status == "empty_group"
    assert empty[list(METRICS)].isna().all()
    assert pd.isna(empty.known_target_positive_fraction)


def test_real_unlabelled_ledger_cannot_create_scores_even_with_positive_nominal_support():
    frame = fixture().drop(columns="probability")
    frame.grid_id = [f"real_grid_{i}" for i in range(len(frame))]
    frame.target = np.nan
    report = grouped_report(frame, scope="unlabelled_method_pilot")
    assert row(report).unit_count == row(report).unknown_target_count == 8
    assert row(report).nominal_support_positive_count == 5
    assert report[list(METRICS)].isna().all().all()
    assert report.independent_event_count.isna().all()
    assert report.confidence_intervals.isna().all()
    assert not report.labels_accepted.any()


@pytest.mark.parametrize("problem", ["prediction", "target"])
def test_real_labels_or_fake_model_predictions_rejected(problem):
    frame = fixture()
    frame.target, frame.probability = np.nan, np.nan
    frame.loc[0, "probability" if problem == "prediction" else "target"] = (
        0.5 if problem == "prediction" else 0
    )
    with pytest.raises(ValueError, match="No real"):
        grouped_report(frame, scope="unlabelled_method_pilot")


@pytest.mark.parametrize("value", ["0.7", True, np.inf, -0.1, 1.1])
def test_invalid_probabilities_are_rejected_not_silently_dropped(value):
    frame = fixture()
    frame.probability = [value] * len(frame)
    with pytest.raises(ValueError):
        grouped_report(frame, scope="synthetic_scores")


@pytest.mark.parametrize("value", ["0", True, np.inf, 2])
def test_invalid_targets_are_rejected_not_changed(value):
    frame = fixture()
    frame.target = [value] * len(frame)
    with pytest.raises(ValueError):
        grouped_report(frame, scope="synthetic_scores")


@pytest.mark.parametrize(
    "problem",
    [
        "season",
        "province",
        "2024",
        "2025",
        "duplicate_alias",
        "blank_grid",
        "non_midnight",
        "schema",
    ],
)
def test_invalid_metadata_and_cohorts_rejected(problem):
    frame = fixture()
    if problem == "season":
        frame.loc[0, "calendar_season"] = "winter"
    elif problem == "province":
        frame.loc[0, "primary_province"] = "unknown"
    elif problem in ("2024", "2025"):
        frame.prediction_timestamp_utc = problem + "-07-01T00:00:00Z"
    elif problem == "duplicate_alias":
        added = frame.iloc[[0]].copy()
        added.prediction_timestamp_utc = "2021-07-01T00:00:00+00:00"
        frame = pd.concat([frame, added])
    elif problem == "blank_grid":
        frame.loc[0, "grid_id"] = " "
    elif problem == "non_midnight":
        frame.loc[0, "prediction_timestamp_utc"] = "2021-07-01T01:00:00Z"
    else:
        frame = frame.drop(columns="target")
    with pytest.raises(ValueError):
        grouped_report(frame, scope="synthetic_scores")


@pytest.mark.parametrize(
    "field,value",
    [
        ("negative_label_permitted", True),
        ("labels_created", True),
        ("accepted_label_rule", "false"),
        ("daily_observation_status", "observed"),
    ],
)
def test_report_cannot_open_acceptance_by_caller_flags(field, value):
    frame = fixture()
    frame[field] = value
    with pytest.raises(ValueError):
        grouped_report(frame, scope="synthetic_scores")


def test_nominal_support_missing_and_rounding_excess_are_recorded_not_clipped():
    frame = fixture()
    frame.loc[0, "nominal_land_fraction"] = 1 + 5e-9
    before = frame.copy(deep=True)
    report = grouped_report(frame, scope="synthetic_scores")
    total = row(report)
    assert total.nominal_support_missing_count == 1
    assert total.nominal_support_zero_count == 2
    assert total.nominal_support_positive_count == 5
    assert total.nominal_support_above_one_within_tolerance_count == 1
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("value", [-1e-10, 1.001, np.inf, "0.5", True])
def test_invalid_nominal_support_rejected(value):
    frame = fixture()
    frame.nominal_land_fraction = [value] * len(frame)
    with pytest.raises(ValueError):
        grouped_report(frame, scope="synthetic_scores")


def test_order_index_and_nullable_numeric_invariance():
    frame = fixture()
    expected = grouped_report(frame, scope="synthetic_scores")
    frame.target = frame.target.astype("Int8")
    frame.probability = frame.probability.astype("Float64")
    actual = grouped_report(frame.iloc[::-1], scope="synthetic_scores")
    pd.testing.assert_frame_equal(expected, actual)


def test_scope_and_synthetic_identity_are_explicit():
    with pytest.raises(ValueError):
        grouped_report(fixture(), scope="real_scores")
    frame = fixture()
    frame.loc[0, "grid_id"] = "real_grid"
    with pytest.raises(ValueError, match="synthetic"):
        grouped_report(frame, scope="synthetic_scores")
