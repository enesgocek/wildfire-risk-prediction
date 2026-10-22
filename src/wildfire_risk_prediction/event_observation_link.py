"""Link candidate sensitivity to a bounded observation pilot, never infer absence."""

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import require

CATEGORIES = {
    "all_presence_time_and_membership_equal",
    "all_presence_time_or_membership_sensitive",
    "candidate_presence_sensitive",
}
KEYS = ["grid_id", "prediction_timestamp_utc"]


def _closed(frame, names):
    require("target" in frame and frame.target.isna().all(), "Unassigned targets")
    for name in names:
        require(frame[name].map(lambda x: isinstance(x, (bool, np.bool_))).all(), "Boolean gate")
        require(not frame[name].any(), "Closed admission gates")


def _training_days(series):
    times = pd.to_datetime(series, utc=True, format="ISO8601", errors="raise")
    require(times.notna().all() and times.dt.year.between(2018, 2023).all(), "Training only")
    require(times.eq(times.dt.floor("D")).all(), "Day-start key")
    return times.map(pd.Timestamp.isoformat)


def link_pilot(candidates, observations):
    """Preserve all pilot rows and return candidate keys outside this specific pilot."""
    require(not candidates.empty and not observations.empty, "Nonempty evidence")
    _closed(
        candidates,
        [
            "positive_label_permitted",
            "negative_label_permitted",
            "event_identity_accepted",
            "event_membership_complete",
        ],
    )
    _closed(
        observations,
        [
            "negative_label_permitted",
            "labels_created",
            "full_daily_observation_proven",
            "accepted_label_rule",
        ],
    )
    require(observations.daily_observation_status.eq("unknown").all(), "Unknown observation")
    c, o = candidates.copy(), observations.copy()
    c["prediction_timestamp_utc"] = _training_days(c.prediction_timestamp_utc)
    require(o.target_day.str.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}").all(), "ISO target day")
    o["prediction_timestamp_utc"] = _training_days(o.target_day)
    for frame in (c, o):
        require(frame.grid_id.notna().all() and not frame.duplicated(KEYS).any(), "Unique keys")
    require(o.review_unit_id.notna().all() and o.review_unit_id.is_unique, "Unique pilot units")
    require(c.review_category.isin(CATEGORIES).all(), "Known candidate categories")
    require(
        c.scenarios_with_candidate.between(1, 9).all()
        and c.scenarios_with_candidate.mod(1).eq(0).all(),
        "Scenario count",
    )
    require(
        c.review_category.eq("candidate_presence_sensitive")
        .eq(c.scenarios_with_candidate.lt(9))
        .all(),
        "Category and scenario count agree",
    )
    for name in (
        "expected_pair_count",
        "completed_pair_count",
        "missing_pair_count",
        "thermal_center_definite_count",
        "thermal_center_boundary_count",
    ):
        values = o[name]
        require(
            values.notna().all()
            and np.isfinite(values).all()
            and values.ge(0).all()
            and values.mod(1).eq(0).all(),
            "Finite integer counts",
        )
    require(
        o.completed_pair_count.add(o.missing_pair_count).eq(o.expected_pair_count).all(),
        "Pair plan balance",
    )
    require(
        o.all_planned_pairs_processed.map(lambda x: isinstance(x, (bool, np.bool_))).all(),
        "Explicit pair-plan boolean",
    )
    require(o.all_planned_pairs_processed.eq(o.missing_pair_count.eq(0)).all(), "Pair plan status")
    for name in (
        "nominal_land_fraction",
        "repeat_12h_fraction",
        "nominal_land_all_four_bins_fraction",
        "cloud_fraction",
    ):
        values = o[name]
        require(np.isfinite(values).all() and values.between(0, 1 + 1e-8).all(), "Area fractions")
    values = o.anypart_land_longest_envelope_gap_seconds
    require(np.isfinite(values).all() and values.between(0, 86400).all(), "Any-part time gap")
    selected = c[KEYS + ["scenarios_with_candidate", "review_category", "review_flags_json"]]
    joined = o.merge(selected, on=KEYS, how="left", validate="one_to_one", indicator=True)
    joined["first_candidate_present_in_catalog_union"] = joined["_merge"].eq("both")
    joined["candidate_review_category"] = joined.review_category.fillna(
        "no_first_candidate_in_any_scenario"
    )
    joined["pilot_geometry_plan_complete"] = joined.all_planned_pairs_processed
    joined["loaded_thermal_center_present"] = joined.thermal_center_definite_count.gt(0)
    routes = []
    for r in joined.itertuples():
        if not r.pilot_geometry_plan_complete:
            route = "incomplete_pilot_geometry_plan_review"
        elif r.thermal_center_boundary_count > 0:
            route = "boundary_thermal_time_review"
        elif not r.first_candidate_present_in_catalog_union:
            route = (
                "loaded_thermal_without_first_candidate_review"
                if r.loaded_thermal_center_present
                else "no_first_candidate_no_loaded_thermal_review"
            )
        elif r.candidate_review_category != "all_presence_time_and_membership_equal":
            route = "grouping_sensitive_candidate_observation_review"
        else:
            route = "agreement_candidate_observation_review"
        routes.append(route)
    joined["proposed_evidence_review_route"] = routes
    joined["positive_label_permitted"] = False
    joined["route_is_label_admission"] = False
    joined = joined.drop(columns=["_merge", "review_category"])
    pd.testing.assert_frame_equal(joined[observations.columns], observations.reset_index(drop=True))
    outside = c.merge(o[KEYS], on=KEYS, how="left", validate="one_to_one", indicator=True)
    outside = outside.loc[outside["_merge"].eq("left_only")].drop(columns="_merge")
    outside["detailed_observation_pilot_evidence_available"] = False
    outside["pilot_nominal_land_fraction"] = np.nan
    outside["pilot_thermal_center_present"] = np.nan
    outside["target"] = np.nan
    return joined, outside
