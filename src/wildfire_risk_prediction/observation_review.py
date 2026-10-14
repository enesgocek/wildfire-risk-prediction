"""Observation pilot diagnostics and human review examples; never reliable negatives."""

import json

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import boolean, require, utc_times
from wildfire_risk_prediction.label_review import KEYS, STRATA
from wildfire_risk_prediction.observation_table import DIAGNOSTICS, NUMERIC, summarize
from wildfire_risk_prediction.target_admission import assert_targets_unassigned

VERSION = "observation_evidence_review_v1"


def audit_sample(sample):
    assert_targets_unassigned(sample)
    summarize(sample)
    require(
        not sample.duplicated(KEYS).any() and sample.review_unit_id.is_unique, "Unique pilot units"
    )
    times = utc_times(sample.prediction_timestamp_utc)
    require(
        times.notna().all()
        and times.dt.year.between(2018, 2023).all()
        and times.eq(times.dt.normalize()).all(),
        "Training midnight pilot only",
    )
    require(
        sample.obs_nominal_granule_day.eq(times.dt.strftime("%Y-%m-%d")).all()
        and sample.obs_target_window_alignment.eq("boundary_timing_unresolved").all(),
        "Retain nominal day and unresolved alignment",
    )
    for _, group in sample.groupby(STRATA, dropna=False):
        require(
            group.population_n.nunique() == 1
            and group.sample_n.eq(len(group)).all()
            and group.population_n.ge(len(group)).all()
            and np.allclose(group.inclusion_fraction, len(group) / group.population_n)
            and np.allclose(group.expansion_weight, group.population_n / len(group)),
            "Retain unequal stratum sampling design",
        )
    present = sample.obs_product_present
    require(
        np.isfinite(sample.loc[present, ["obs_" + c for c in NUMERIC]].to_numpy(float)).all(),
        "Finite present diagnostics",
    )
    require(
        sample.loc[present, ["obs_" + c for c in NUMERIC]].ge(0).all().all(),
        "Nonnegative diagnostic measurements",
    )
    require(
        sample.loc[~present, ["obs_" + c for c in DIAGNOSTICS]].isna().all().all(),
        "Missing source diagnostics remain missing",
    )
    for kind in ("any_center", "nominal_land_center"):
        count = sample[f"obs_{kind}_scan_count"]
        start = utc_times(sample[f"obs_{kind}_first_start_utc"])
        end = utc_times(sample[f"obs_{kind}_last_end_utc"])
        has = present & count.gt(0)
        require(
            start.notna().eq(has).all() and end.notna().eq(has).all(), "Count/time presence agrees"
        )
        require(
            (start[has] <= end[has]).all()
            and (start[has] > times[has]).all()
            and (end[has] <= times[has] + pd.Timedelta(24, unit="h")).all(),
            "Retained center envelopes inside nominal target day",
        )
    thermal = sample.obs_nominal_confidence_fire + sample.obs_high_confidence_fire
    expected = np.where(
        ~present,
        "source_product_absent",
        np.where(
            thermal.gt(0), "thermal_center_present", "product_present_no_selected_thermal_center"
        ),
    )
    require(sample.signal_stratum.eq(expected).all(), "Sampling signals remain diagnostics")
    output = sample.copy()
    output["land_cloud_union_overlap_diagnostic"] = present & (
        sample.obs_nominal_nonfire_land_fraction_estimate + sample.obs_cloud_fraction_estimate
        > sample.obs_reconstructed_domain_fraction_estimate + 1e-9
    )
    output["no_nominal_land_center"] = present & sample.obs_nominal_land_center_scan_count.eq(0)
    output["no_selected_center"] = present & sample.obs_any_center_scan_count.eq(0)
    output["boundary_scan_present"] = present & sample.obs_boundary_unknown_scan_count.gt(0)
    output["nominal_land_longest_envelope_gap_hours"] = (
        sample.obs_nominal_land_center_longest_envelope_gap_seconds / 3600
    )
    reasons = []
    for row in output.itertuples():
        r = [
            "exact_window_alignment_unresolved",
            "observation_policy_unaccepted",
            "event_and_source_semantics_unaccepted",
            "habitat_policy_unaccepted",
        ]
        if not row.obs_product_present:
            r.append("source_product_absent")
        for flag in (
            "land_cloud_union_overlap_diagnostic",
            "no_nominal_land_center",
            "no_selected_center",
            "boundary_scan_present",
        ):
            if getattr(row, flag):
                r.append(flag)
        if row.signal_stratum == "thermal_center_present":
            r.append("thermal_class_requires_event_interpretation")
        reasons.append(json.dumps(r))
    output["negative_admission_blockers_json"] = reasons
    output["review_status"] = "not_reviewed"
    output["exact_target_window_coverage_proven"] = False
    output["target"] = pd.Series(pd.NA, index=output.index, dtype="Int8")
    return output


def select_human_examples(audited):
    """Illustrative extremes, explicitly separate from the 400-unit sampling design."""
    present = audited.obs_product_present
    no_thermal = audited.signal_stratum.eq("product_present_no_selected_thermal_center")
    neither = audited.no_selected_center
    both = audited.land_cloud_union_overlap_diagnostic & no_thermal
    choices = [
        ("A_missing_source", ~present, ["sampling_rank_sha256"], [True]),
        (
            "B_land_and_cloud_union",
            both,
            ["obs_cloud_fraction_estimate", "sampling_rank_sha256"],
            [False, True],
        ),
        (
            "C_no_land_center",
            present & no_thermal & audited.no_nominal_land_center & ~neither,
            ["sampling_rank_sha256"],
            [True],
        ),
        (
            "D_zero_thermal_with_land",
            present & no_thermal & ~audited.no_nominal_land_center,
            [
                "obs_nominal_nonfire_land_fraction_estimate",
                "nominal_land_longest_envelope_gap_hours",
                "sampling_rank_sha256",
            ],
            [False, True, True],
        ),
        ("E_midnight_boundary", audited.boundary_scan_present, ["sampling_rank_sha256"], [True]),
        ("F_area_without_center", present & neither, ["sampling_rank_sha256"], [True]),
    ]
    examples, used = [], set()
    for reason, mask, order, ascending in choices:
        subset = audited.loc[mask & ~audited.review_unit_id.isin(used)].sort_values(
            order, ascending=ascending
        )
        require(not subset.empty, "Requested human example exists: " + reason)
        row = subset.iloc[0].copy()
        row["example_id"] = reason
        row["example_selection"] = "purpose_selected_illustration_not_new_random_sample"
        examples.append(row)
        used.add(row.review_unit_id)
    result = pd.DataFrame(examples).reset_index(drop=True)
    require(result.review_unit_id.is_unique, "Distinct human examples")
    return result


def boundary_scan_review(frame, day):
    """Read back saved interval classification, keeping crossing thermal centers unassigned."""
    start, end = utc_times(frame.start_utc), utc_times(frame.end_utc)
    t = pd.Timestamp(day, tz="UTC")
    require(2018 <= t.year <= 2023 and (start <= end).all(), "Training scan intervals")
    require(not frame.duplicated(["sensor", "pair_key", "scan_index"]).any(), "Unique source scans")
    inside = (start > t) & (end <= t + pd.Timedelta(24, unit="h"))
    outside = (end <= t) | (start > t + pd.Timedelta(24, unit="h"))
    expected = np.where(inside, "inside", np.where(outside, "outside", "boundary_unknown"))
    require(frame.day_window_status.eq(expected).all(), "Saved scan-window classification agrees")
    boolean(frame.nominal_granule_boundary_crossed, "Saved boundary flag")
    output = frame.copy()
    output["target"] = pd.Series(pd.NA, index=output.index, dtype="Int8")
    output["scan_classification_readback"] = "matched_not_pixel_timestamp_acceptance"
    return output
