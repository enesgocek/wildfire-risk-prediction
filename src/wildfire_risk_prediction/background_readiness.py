"""Background screening evidence and release state; screens never admit binary labels."""

import numpy as np
import pandas as pd

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.feature_join import require, utc_times
from wildfire_risk_prediction.observation_review import audit_sample
from wildfire_risk_prediction.observation_window import (
    COUNTS,
    KEYS,
    classify_intervals,
    loaded_envelope_metrics,
)
from wildfire_risk_prediction.target_admission import assert_targets_unassigned


def inspection_preview(sample, features):
    """Bounded review join, with exact keys and original NaN values; not final assembly."""
    assert_targets_unassigned(sample)
    require(len(sample) <= 400 and sample.review_unit_id.is_unique, "Bounded inspection units")
    require(features.columns.tolist() == join.KEYS + join.feature_names(), "Feature allowlist")
    require(
        not sample.duplicated(join.KEYS).any() and not features.duplicated(join.KEYS).any(),
        "Unique inspection keys",
    )
    require(
        set(map(tuple, sample[join.KEYS].values)) == set(map(tuple, features[join.KEYS].values)),
        "Exact inspection source keys",
    )
    stamps = utc_times(features.prediction_timestamp_utc)
    require(
        stamps.dt.year.between(2018, 2023).all() and stamps.eq(stamps.dt.floor("D")).all(),
        "Training inspection timestamps",
    )
    require(
        all(pd.api.types.is_numeric_dtype(features[c]) for c in join.feature_names()),
        "Numeric inspection features",
    )
    values = features[join.feature_names()].to_numpy(float)
    require((np.isfinite(values) | np.isnan(values)).all(), "Finite or missing inspection features")
    fields = [
        "review_unit_id",
        *join.KEYS,
        "proposed_review_route",
        "catalog_match_state",
        "expansion_weight",
        "water_scope_included",
        "window_incomplete_packet_set",
        "window_boundary_scan_present",
        "window_daily_observation_status",
        "target",
    ]
    result = sample[fields].merge(features, on=join.KEYS, how="left", validate="one_to_one")
    require(
        result.target.isna().all() and result.window_daily_observation_status.eq("unknown").all(),
        "Unassigned inspection",
    )
    result["usage"] = "limited_inspection_preview_not_training_dataset"
    result["model_ready"] = False
    return result


def review_background(sample, scans):
    """Retain the fixed full pilot design before selecting background candidates.

    Area unions are nominal-day diagnostics; intervals are neighbouring-day scan
    envelopes. Neither is all-day clear coverage or proof of physical fire absence.
    """
    audit_sample(sample)
    for flag in (
        "window_negative_label_permitted",
        "window_positive_label_permitted",
        "window_exact_target_window_coverage_proven",
    ):
        join.boolean(sample[flag], flag)
    require(
        sample.window_daily_observation_status.eq("unknown").all()
        and not sample.window_negative_label_permitted.any()
        and not sample.window_positive_label_permitted.any()
        and not sample.window_exact_target_window_coverage_proven.any()
        and sample.window_target.isna().all(),
        "Closed pilot window gates",
    )
    background = (
        sample.loc[sample.proposed_review_route.eq("background_observation_review")]
        .copy()
        .sort_values("review_unit_id")
        .reset_index(drop=True)
    )
    require(not background.empty, "Background review selection")
    require(
        background.water_scope_included.all()
        and background.window_all_three_nominal_packets_present.all()
        and not background.window_incomplete_packet_set.any()
        and not background.window_boundary_scan_present.any()
        and not background.window_loaded_definite_thermal_present.any()
        and background.scenarios_with_candidate.eq(0).all()
        and background.window_loaded_nominal_land_center_definite_count.gt(0).all(),
        "Background route preconditions",
    )
    require(set(scans.review_unit_id) <= set(sample.review_unit_id), "Known scan units")
    selected = scans.loc[scans.review_unit_id.isin(background.review_unit_id)].copy()
    require(
        set(selected.review_unit_id) == set(background.review_unit_id), "Background scan coverage"
    )
    require(not selected.duplicated(["review_unit_id", *KEYS]).any(), "Unique saved scans")
    values = selected[COUNTS].to_numpy(float)
    require(
        np.isfinite(values).all() and (values >= 0).all() and (values == np.floor(values)).all(),
        "Valid background source counts",
    )
    require(
        selected.land_nominal_input_no_residual.le(selected.pixel_center_count).all()
        and (selected.nominal_confidence_fire + selected.high_confidence_fire)
        .le(selected.pixel_center_count)
        .all(),
        "Source classes within total centers",
    )
    extra = []
    for row in background.itertuples():
        frame = selected.loc[selected.review_unit_id.eq(row.review_unit_id)]
        require(
            frame.grid_id.eq(row.grid_id).all()
            and utc_times(frame.prediction_timestamp_utc)
            .eq(pd.Timestamp(row.prediction_timestamp_utc))
            .all(),
            "Saved scan pilot keys",
        )
        day = pd.Timestamp(row.prediction_timestamp_utc).strftime("%Y-%m-%d")
        require(
            classify_intervals(frame, day).eq(frame.window_classification).all(),
            "Retained scan classifications",
        )
        require(not frame.window_classification.eq("boundary_unknown").any(), "No boundary route")
        inside = frame.loc[frame.window_classification.eq("inside")]
        thermal = inside.nominal_confidence_fire + inside.high_confidence_fire
        land = inside.loc[inside.land_nominal_input_no_residual.gt(0)]
        union, gap = loaded_envelope_metrics(land, day)
        require(
            thermal.eq(0).all()
            and inside.land_nominal_input_no_residual.sum()
            == row.window_loaded_nominal_land_center_definite_count
            and np.isclose(
                union,
                row.window_loaded_nominal_land_center_envelope_union_seconds,
                rtol=0,
                atol=1e-9,
            )
            and np.isclose(
                gap,
                row.window_loaded_nominal_land_center_longest_envelope_gap_seconds,
                rtol=0,
                atol=1e-9,
            ),
            "Source scan count and interval readback",
        )
        overlap = (
            row.obs_nominal_nonfire_land_fraction_estimate + row.obs_cloud_fraction_estimate
            > row.obs_reconstructed_domain_fraction_estimate + 1e-9
        )
        extra.append(
            {
                "review_unit_id": row.review_unit_id,
                "background_land_granule_count": len(
                    land[["sensor", "pair_key"]].drop_duplicates()
                ),
                "background_land_sensor_count": land.sensor.nunique(),
                "background_land_scan_envelope_union_seconds": union,
                "background_land_scan_longest_gap_hours": gap / 3600,
                "background_nominal_land_cloud_union_overlap": bool(overlap),
                "background_screen_is_label_admission": False,
                "background_negative_label_permitted": False,
                "background_assessment": "screening_evidence_not_fire_absence",
            }
        )
    output = background.merge(pd.DataFrame(extra), on="review_unit_id", validate="one_to_one")
    pd.testing.assert_frame_equal(output[background.columns], background)
    screens = []
    for name, area, granules, sensors, gap in (
        ("nominal_area_080_only", 0.8, 0, 0, None),
        ("nominal_area_090_only", 0.9, 0, 0, None),
        ("area090_two_granules", 0.9, 2, 1, None),
        ("area090_two_sensors_gap12h", 0.9, 2, 2, 12),
    ):
        mask = (
            output.obs_nominal_nonfire_land_fraction_estimate.ge(area)
            & output.background_land_granule_count.ge(granules)
            & output.background_land_sensor_count.ge(sensors)
        )
        if gap is not None:
            mask &= output.background_land_scan_longest_gap_hours.le(gap)
        output["hypothetical_screen_" + name] = mask
        screens.append(
            {
                "screen": name,
                "nominal_land_fraction_min": area,
                "distinct_land_granules_min": granules,
                "distinct_land_sensors_min": sensors,
                "scan_envelope_gap_max_hours": gap,
                "raw_selected_units": int(mask.sum()),
                "selected_with_nominal_land_cloud_overlap": int(
                    output.loc[mask, "background_nominal_land_cloud_union_overlap"].sum()
                ),
                "scientifically_accepted": False,
                "binary_labels_created": 0,
                "negative_label_permitted": False,
            }
        )
    require(output.target.isna().all(), "Background labels stay unassigned")
    return output, pd.DataFrame(screens)


def release_state(feature_audit, observation_audit, review_sources):
    """Record structural passes separately from missing scientific target acceptance."""
    require(
        feature_audit["status"] == "candidate_index_structural_readback_passed"
        and feature_audit["candidate_calendar_complete"] is True
        and feature_audit["verified_candidate_months"] == 72
        and feature_audit["verified_candidate_rows"] == 6351709
        and feature_audit["model_ready"] is False
        and feature_audit["labels_created"] is False
        and feature_audit["negative_label_permitted"] is False
        and feature_audit["daily_observation_status"] == "unknown"
        and feature_audit["final_test_accessed"] is False
        and feature_audit["scientific_acceptance_granted"] is False,
        "Fresh complete candidate audit with closed scientific gates",
    )
    require(
        observation_audit["months_reread"] == 72
        and observation_audit["rows_reread"] == 6351709
        and observation_audit["missing_product_rows"] == 5798
        and observation_audit["status"] == "structural_readback_passed"
        and observation_audit["negative_label_permitted"] is False,
        "Fresh observation structural audit",
    )
    require(
        set(review_sources) == {"features", "observation", "background", "event_trace"},
        "Exact release evidence sources",
    )
    parts = {
        name: {
            "status": "structurally_checked_scientific_acceptance_pending",
            "evidence": review_sources["features"],
            "feature_columns": count,
        }
        for name, count in (("weather", 11), ("landscape", 12), ("vegetation", 4))
    }
    parts["observation"] = {
        "status": "structurally_checked_negative_policy_pending",
        "evidence": review_sources["observation"],
        "missing_source_days": ["2018-06-13", "2023-12-31"],
    }
    parts["targets"] = {
        "status": "not_admitted_no_binary_target_part",
        "evidence": [review_sources["background"], review_sources["event_trace"]],
    }
    return {
        "status": "preflight_complete_scientific_release_blocked",
        "split": "train_2018_2023",
        "parts": parts,
        "scientific_protocol_status": "not_accepted",
        "inspection_preview_ready": True,
        "labelled_training_dataset_ready": False,
        "model_ready": False,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "final_merge_authorized": False,
        "final_merge_performed": False,
        "validation_ready": False,
        "final_test_accessed": False,
        "open_decisions": [
            "Source Type/version meaning and exceptions",
            "Versioned event recurrence and first-cell policy",
            "Habitat scope beyond the accepted map-water exclusion",
            "Observation-supported negatives versus explicitly different catalogue proxy target",
            "Period-edge embargo and future validation assembly",
        ],
    }
