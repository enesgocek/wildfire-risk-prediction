import json

import pandas as pd
import pytest

from wildfire_risk_prediction import target_admission as target


def test_right_closed_midnight_and_nanosecond_boundaries():
    values = pd.Series(
        ["2018-08-02T00:00:00Z", "2018-08-02T00:00:00.000000001Z", "2018-08-01T23:59:59.999999999Z"]
    )
    windows = target.detection_windows(values)
    assert windows.prediction_timestamp_utc.dt.strftime("%Y-%m-%d").tolist() == [
        "2018-08-01",
        "2018-08-02",
        "2018-08-01",
    ]


def test_training_boundary_inclusive_end_is_not_silently_accepted():
    values = pd.Series(
        [
            "2018-01-01T00:00:00Z",
            "2018-01-01T00:00:00.000000001Z",
            "2023-12-31T12:00:00Z",
            "2022-12-31T12:00:00Z",
        ]
    )
    assert target.detection_windows(values).training_window_boundary_review.tolist() == [
        True,
        False,
        True,
        False,
    ]


@pytest.mark.parametrize(
    "value",
    [
        None,
        "2017-12-31T12:00:00Z",
        "2024-01-01T00:00:00Z",
        "2025-01-01T00:00:00Z",
        "2018-08-01T00:00:00",
    ],
)
def test_missing_non_utc_and_holdout_detections_rejected(value):
    with pytest.raises(ValueError):
        target.detection_windows(pd.Series([value]))


@pytest.mark.parametrize("value", [0, 1, False, True, "0", "1"])
def test_unaccepted_labels_cannot_be_enabled_by_observed_flag(value):
    frame = pd.DataFrame(
        {
            "target": [value],
            "daily_observation_status": ["observed"],
            "negative_label_permitted": [True],
        }
    )
    with pytest.raises(ValueError, match="not admitted"):
        target.assert_targets_unassigned(frame)


def test_empty_matches_stay_unknown():
    frame = pd.DataFrame(
        {
            "target": pd.Series([pd.NA, pd.NA], dtype="Int8"),
            "event_count": [0, 0],
            "daily_observation_status": ["unknown"] * 2,
        }
    )
    target.assert_targets_unassigned(frame)
    assert frame.target.isna().all()
    assert not target.specification()["negative_label_permitted"]


def test_event_identity_disjointness():
    target.assert_event_disjoint(
        pd.DataFrame({"event_id": ["e1", "e1", "e2"], "split": ["train", "train", "validation"]})
    )
    with pytest.raises(ValueError, match="multiple splits"):
        target.assert_event_disjoint(
            pd.DataFrame({"event_id": ["e1", "e1"], "split": ["train", "validation"]})
        )
    with pytest.raises(ValueError, match="sealed"):
        target.assert_event_disjoint(pd.DataFrame({"event_id": ["e1"], "split": ["final_test"]}))


def test_review_does_not_choose_canonical_first_grid():
    catalog = pd.DataFrame(
        {
            "cluster_id": ["c1"],
            "membership_sha256": ["a" * 64],
            "first_detection_utc": ["2018-08-01T12:00:00Z"],
            "candidate_prediction_timestamp_utc": ["2018-08-01T00:00:00Z"],
            "earliest_grid_ids_json": [json.dumps(["g1", "g2"])],
            "earliest_grid_count": [2],
            "canonical_first_grid_id": ["g1"],
            "event_status": ["exploratory_cluster_only"],
            "negative_label_permitted": [False],
            "temporal_chain_review": [False],
            "spatial_chain_review": [False],
            "multi_grid_first_detection_review": [True],
            "calendar_year_crossing_review": [False],
            "period_start_context_missing": [False],
            "period_end_context_missing": [False],
        }
    )
    output, summary = target.review_catalog(catalog)
    assert output.target.isna().all()
    assert "canonical_first_grid_id" not in output
    assert summary["binary_targets_created"] == 0
    assert summary["additional_case_review"] == 1
    catalog.candidate_prediction_timestamp_utc = "2018-07-31T00:00:00Z"
    with pytest.raises(ValueError, match="Right-closed"):
        target.review_catalog(catalog)
