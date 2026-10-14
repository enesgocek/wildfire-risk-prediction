"""Sampling diagnostics and human examples preserve missingness and closed negative gates."""

import json

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.label_review import STRATA
from wildfire_risk_prediction.observation_review import (
    audit_sample,
    boundary_scan_review,
    select_human_examples,
)
from wildfire_risk_prediction.observation_table import NUMERIC, TIMES


def sample():
    rows = []
    for i in range(6):
        present = i != 0
        land = i in (1, 3, 4)
        centers = i != 5
        row = {"obs_" + c: 0.0 if present else np.nan for c in NUMERIC}
        row.update({"obs_" + c: None for c in TIMES})
        if present:
            row.update(
                obs_aoi_area_m2=100.0,
                obs_reconstructed_domain_area_estimate_m2=100.0,
                obs_reconstructed_domain_fraction_estimate=1.0,
                obs_nominal_nonfire_land_fraction_estimate=float(land),
                obs_cloud_fraction_estimate=float(i in (1, 2, 4)),
                obs_nominal_confidence_fire=int(i == 4),
                obs_any_center_scan_count=2 if centers else 0,
                obs_nominal_land_center_scan_count=2 if land else 0,
                obs_boundary_unknown_scan_count=int(i == 4),
                obs_nominal_land_center_longest_envelope_gap_seconds=43200 if land else 86400,
            )
            for kind, has in (("any_center", centers), ("nominal_land_center", land)):
                if has:
                    row[f"obs_{kind}_first_start_utc"] = "2022-01-18T01:00:00Z"
                    row[f"obs_{kind}_last_end_utc"] = "2022-01-18T12:00:00Z"
        row.update(
            grid_id=f"G{i}",
            prediction_timestamp_utc="2022-01-18T00:00:00Z",
            obs_nominal_granule_day="2022-01-18",
            obs_product_present=present,
            obs_daily_observation_status="unknown",
            obs_negative_label_permitted=False,
            obs_target_window_alignment="boundary_timing_unresolved",
            year=2022,
            quarter=1,
            geography_stratum="sector1",
            signal_stratum="source_product_absent"
            if not present
            else "thermal_center_present"
            if i == 4
            else "product_present_no_selected_thermal_center",
            review_unit_id=f"random:G{i}:2022-01-18",
            sampling_rank_sha256=f"{i:064d}",
            target=None,
        )
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame["sample_n"] = frame.groupby(STRATA).grid_id.transform("size")
    frame["population_n"] = frame.sample_n * 100
    frame["inclusion_fraction"] = 0.01
    frame["expansion_weight"] = 100.0
    return frame


def test_no_thermal_and_high_union_area_do_not_admit_negatives():
    result = audit_sample(sample())
    assert result.target.isna().all()
    assert not result.obs_negative_label_permitted.any()
    assert not result.exact_target_window_coverage_proven.any()
    assert result.land_cloud_union_overlap_diagnostic.sum() == 2
    assert result.no_nominal_land_center.sum() == 2
    assert result.no_selected_center.sum() == 1
    assert result.review_status.eq("not_reviewed").all()
    assert all(
        "exact_window_alignment_unresolved" in json.loads(x)
        for x in result.negative_admission_blockers_json
    )
    assert pd.isna(result.iloc[0].nominal_land_longest_envelope_gap_hours)


def test_six_examples_are_purpose_selected_and_order_invariant():
    result = audit_sample(sample())
    a = select_human_examples(result)
    b = select_human_examples(result.sample(frac=1, random_state=42))
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == 6 and a.review_unit_id.is_unique and a.target.isna().all()
    assert a.review_status.eq("not_reviewed").all()
    assert a.example_selection.str.startswith("purpose_selected").all()


@pytest.mark.parametrize(
    "corruption",
    [
        "label",
        "reliable_flag",
        "missing_zero",
        "holdout",
        "duplicate",
        "sampling_weight",
        "sample_n",
        "alignment",
        "nominal_day",
        "count_time",
        "envelope_outside",
        "negative_measurement",
        "signal",
    ],
)
def test_changed_source_or_false_acceptance_is_rejected(corruption):
    x = sample()
    if corruption == "label":
        x.loc[0, "target"] = 0
    elif corruption == "reliable_flag":
        x["obs_negative_label_permitted"] = True
    elif corruption == "missing_zero":
        x.loc[0, "obs_cloud"] = 0.0
    elif corruption == "holdout":
        x["prediction_timestamp_utc"] = "2025-01-18T00:00:00Z"
    elif corruption == "duplicate":
        x = pd.concat([x, x.iloc[:1]], ignore_index=True)
    elif corruption == "sampling_weight":
        x["expansion_weight"] = 1
    elif corruption == "sample_n":
        x["sample_n"] = 99
    elif corruption == "alignment":
        x["obs_target_window_alignment"] = "resolved"
    elif corruption == "nominal_day":
        x["obs_nominal_granule_day"] = "2022-01-17"
    elif corruption == "count_time":
        x.loc[1, "obs_nominal_land_center_first_start_utc"] = None
    elif corruption == "envelope_outside":
        x.loc[1, "obs_any_center_last_end_utc"] = "2022-01-19T00:00:01Z"
    elif corruption == "negative_measurement":
        x.loc[1, "obs_cloud_fraction_estimate"] = -0.1
    else:
        x.loc[1, "signal_stratum"] = "thermal_center_present"
    with pytest.raises(ValueError):
        audit_sample(x)


def scans():
    return pd.DataFrame(
        {
            "sensor": ["SNPP"] * 4,
            "pair_key": ["2022018.2354"] * 4,
            "scan_index": range(4),
            "start_utc": [
                "2022-01-18T00:00:00Z",
                "2022-01-18T23:59:59.5Z",
                "2022-01-19T00:00:00Z",
                "2022-01-19T00:00:00.001Z",
            ],
            "end_utc": [
                "2022-01-18T00:00:00.5Z",
                "2022-01-19T00:00:00.05Z",
                "2022-01-19T00:00:00.5Z",
                "2022-01-19T00:00:00.5Z",
            ],
            "day_window_status": ["boundary_unknown"] * 3 + ["outside"],
            "nominal_granule_boundary_crossed": [True] * 4,
        }
    )


def test_open_left_closed_right_scan_boundary_never_becomes_a_pixel_time():
    result = boundary_scan_review(scans(), "2022-01-18")
    assert result.target.isna().all()
    assert result.scan_classification_readback.eq("matched_not_pixel_timestamp_acceptance").all()
    x = scans()
    x.loc[0, "day_window_status"] = "inside"
    with pytest.raises(ValueError, match="classification"):
        boundary_scan_review(x, "2022-01-18")


def test_exact_right_endpoint_inside_and_final_period_rejected():
    x = scans().iloc[:1].copy()
    x["start_utc"], x["end_utc"] = "2022-01-18T23:59:59Z", "2022-01-19T00:00:00Z"
    x["day_window_status"] = "inside"
    assert boundary_scan_review(x, "2022-01-18").day_window_status.eq("inside").all()
    with pytest.raises(ValueError, match="Training"):
        boundary_scan_review(x, "2025-01-18")
