"""A complete source packet, high area and multiple sensors are not label acceptance."""

import copy

import pandas as pd
import pytest
from test_label_protocol_review import catalogs
from test_window_pilot import prepared

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.background_readiness import (
    inspection_preview,
    release_state,
    review_background,
)
from wildfire_risk_prediction.final_merge_gate import require_final_merge_approval
from wildfire_risk_prediction.label_protocol_review import compare_catalogs
from wildfire_risk_prediction.observation_window import review_window, source_schedule
from wildfire_risk_prediction.observation_window_pilot import append_diagnostics


def evidence():
    sample, summaries, scope = prepared()
    frame = pd.DataFrame(
        [
            {
                "grid_id": "G1",
                "sensor": sensor,
                "pair_key": pair,
                "scan_index": 1,
                "pixel_center_count": 2,
                "land_nominal_input_no_residual": 2,
                "nominal_confidence_fire": 0,
                "high_confidence_fire": 0,
                "start_utc": f"2022-01-18T{hour:02d}:00:00Z",
                "end_utc": f"2022-01-18T{hour:02d}:00:01Z",
                "source_nominal_day": "2022-01-18",
            }
            for sensor, pair, hour in (("SNPP", "p1", 1), ("N20", "p2", 13))
        ]
    )
    scans, summary = review_window(frame, "2022-01-18", "G1", source_schedule("2022-01-18", set()))
    summaries = pd.concat(
        [summaries.loc[summaries.grid_id.ne("G1")], pd.DataFrame([summary])], ignore_index=True
    )
    sample = append_diagnostics(sample, summaries, scope)
    pilot, _, _ = compare_catalogs(sample, catalogs(), sample.grid_id)
    scans["review_unit_id"] = "random:G1:2022-01-18"
    return pilot, scans


def test_high_area_and_multiple_sensors_remain_unassigned_and_strata_are_preserved():
    pilot, scans = evidence()
    before = pilot.copy(deep=True)
    rows, screens = review_background(pilot, scans)
    pd.testing.assert_frame_equal(pilot, before)
    assert len(rows) == 1 and len(screens) == 4
    assert rows.iloc[0].background_land_sensor_count == 2
    assert rows.iloc[0].background_land_granule_count == 2
    assert rows.iloc[0].background_land_scan_envelope_union_seconds == 2
    assert rows.iloc[0].background_nominal_land_cloud_union_overlap
    assert screens.raw_selected_units.eq(1).all()
    assert screens.selected_with_nominal_land_cloud_overlap.eq(1).all()
    assert not screens.scientifically_accepted.any()
    assert not screens.negative_label_permitted.any() and rows.target.isna().all()
    assert rows.expansion_weight.tolist() == [100.0]


@pytest.mark.parametrize(
    "problem",
    [
        "target",
        "negative_gate",
        "false_coverage",
        "missing_scan",
        "duplicate_scan",
        "wrong_time_key",
        "thermal",
        "changed_interval",
        "wrong_grid",
        "source_count",
        "no_land",
    ],
)
def test_bad_evidence_or_artificial_admission_is_rejected(problem):
    pilot, scans = evidence()
    selected = pilot.grid_id.eq("G1")
    if problem == "target":
        pilot.loc[selected, "target"] = 0
    elif problem == "negative_gate":
        pilot.loc[selected, "window_negative_label_permitted"] = True
    elif problem == "false_coverage":
        pilot.loc[selected, "window_exact_target_window_coverage_proven"] = True
    elif problem == "missing_scan":
        scans = scans.iloc[:0]
    elif problem == "duplicate_scan":
        scans = pd.concat([scans, scans.iloc[:1]])
    elif problem == "wrong_time_key":
        scans["prediction_timestamp_utc"] = "2022-01-19T00:00:00Z"
    elif problem == "thermal":
        scans.loc[0, "nominal_confidence_fire"] = 1
    elif problem == "changed_interval":
        scans.loc[0, "start_utc"] = "2022-01-18T00:00:00Z"
    elif problem == "wrong_grid":
        scans.loc[0, "grid_id"] = "G2"
    elif problem == "source_count":
        scans.loc[0, "land_nominal_input_no_residual"] = 1
    else:
        pilot.loc[selected, "window_loaded_nominal_land_center_definite_count"] = 0
    with pytest.raises(ValueError):
        review_background(pilot, scans)


def readiness():
    features = {
        "status": "candidate_index_structural_readback_passed",
        "candidate_calendar_complete": True,
        "verified_candidate_months": 72,
        "verified_candidate_rows": 6351709,
        "model_ready": False,
        "labels_created": False,
        "scientific_acceptance_granted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "final_test_accessed": False,
    }
    observations = {
        "status": "structural_readback_passed",
        "months_reread": 72,
        "rows_reread": 6351709,
        "missing_product_rows": 5798,
        "negative_label_permitted": False,
    }
    sources = {
        name: "synthetic_evidence"
        for name in ("features", "observation", "background", "event_trace")
    }
    return features, observations, sources


def test_structural_success_does_not_approve_labels_or_final_merge():
    args = readiness()
    before = copy.deepcopy(args)
    state = release_state(*args)
    assert args == before
    assert set(state["parts"]) == {"weather", "landscape", "vegetation", "observation", "targets"}
    assert state["inspection_preview_ready"] and not state["model_ready"]
    assert not state["labelled_training_dataset_ready"] and not state["final_merge_authorized"]
    assert state["parts"]["targets"]["status"] == "not_admitted_no_binary_target_part"
    with pytest.raises(PermissionError):
        require_final_merge_approval(state, None)


@pytest.mark.parametrize(
    "problem",
    [
        "partial_features",
        "model_ready",
        "partial_observation",
        "zero_missing",
        "negative_gate",
        "missing_evidence",
    ],
)
def test_invalid_part_preflight_is_not_ready(problem):
    features, observations, sources = readiness()
    if problem == "partial_features":
        features["verified_candidate_months"] = 71
    elif problem == "model_ready":
        features["model_ready"] = True
    elif problem == "partial_observation":
        observations["rows_reread"] -= 1
    elif problem == "zero_missing":
        observations["missing_product_rows"] = 0
    elif problem == "negative_gate":
        observations["negative_label_permitted"] = True
    else:
        del sources["background"]
    with pytest.raises(ValueError):
        release_state(features, observations, sources)


def preview_evidence():
    sample, _ = evidence()
    features = sample[join.KEYS].copy()
    for col in join.feature_names():
        features[col] = 1.0
    features.loc[0, join.feature_names()[0]] = float("nan")
    return sample, features


def test_inspection_join_keeps_missing_values_weights_and_water_flags():
    sample, features = preview_evidence()
    result = inspection_preview(sample, features.iloc[::-1])
    assert len(result) == 6 and result.target.isna().all()
    assert pd.isna(result.loc[0, join.feature_names()[0]])
    assert result.expansion_weight.equals(sample.expansion_weight)
    assert result.water_scope_included.equals(sample.water_scope_included)
    assert not result.model_ready.any()


@pytest.mark.parametrize(
    "problem",
    [
        "missing_key",
        "extra_key",
        "duplicate",
        "holdout",
        "infinity",
        "label",
        "extra_feature",
        "too_many_units",
    ],
)
def test_inspection_cannot_hide_join_loss_or_become_full_assembly(problem):
    sample, features = preview_evidence()
    if problem == "missing_key":
        features = features.iloc[1:]
    elif problem == "extra_key":
        features.loc[0, "grid_id"] = "unknown"
    elif problem == "duplicate":
        features = pd.concat([features, features.iloc[:1]])
    elif problem == "holdout":
        sample["prediction_timestamp_utc"] = features["prediction_timestamp_utc"] = (
            "2024-01-18T00:00:00Z"
        )
    elif problem == "infinity":
        features.loc[0, join.feature_names()[0]] = float("inf")
    elif problem == "label":
        sample.loc[0, "target"] = 0
    elif problem == "extra_feature":
        features["target_day_cloud"] = 0.0
    else:
        sample = pd.concat([sample] * 67, ignore_index=True)
    with pytest.raises(ValueError):
        inspection_preview(sample, features)
