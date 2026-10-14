"""Overlapping review cases expose rule sensitivity; families are not fire identities."""

import hashlib
import json

import pandas as pd

from wildfire_risk_prediction.feature_join import boolean, require, utc_times
from wildfire_risk_prediction.target_admission import assert_targets_unassigned, review_catalog

VERSION = "event_decision_review_v1"
GATES = {
    "source_semantics": "Archive version/Type meaning and source exceptions documented",
    "event_definition": "Grouping version and split/merge/continuation cases adjudicated",
    "first_cell": "Simultaneous first cells and location uncertainty resolved by versioned rule",
    "habitat": "Eligible vegetation domain and boundary/agriculture exceptions documented",
    "negative_observation": "Target-window alignment and observation sufficiency justified",
    "period_boundary": "Window endpoints, context and cross-split event policy documented",
}


def protocol():
    """Export requirements, without an approval switch or label-producing path."""
    return {
        "version": VERSION,
        "status": "draft_requires_researcher_and_advisor_review",
        "scope": "training_purposive_case_diagnostics_only",
        "window": "(T,T+24h]",
        "gates": [
            {
                "gate": key,
                "criterion": value,
                "status": "unaccepted",
                "required_record_fields": [
                    "policy_version",
                    "reviewer_id",
                    "reviewed_at_utc",
                    "rationale",
                    "evidence_path_and_sha256",
                    "source_lineage_and_limits",
                ],
            }
            for key, value in GATES.items()
        ],
        "scenario_selected": None,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
    }


def sensitivity(cases, members, spatial, links):
    """Connect cases sharing a detection, then compare their saved first-time/cell sets.

    Transitive overlap is only a review convenience. Missing scenarios in this
    purposive packet are not treated as agreement or evidence of stability.
    """
    checked = review_catalog(cases)[0]
    require(
        checked.training_window_boundary_review.eq(cases.training_window_boundary_review).all(),
        "Saved boundary flags agree with target windows",
    )
    assert_targets_unassigned(cases)
    require(cases.cluster_id.is_unique, "Case identifiers unique across scenarios")
    ids = set(cases.cluster_id)
    require(
        set(members.cluster_id) == ids
        and not members.duplicated(["cluster_id", "detection_id"]).any(),
        "Exact case membership, without repeated detections",
    )
    # Accepted member CSVs use a space separator; only normalize that separator in memory.
    times = utc_times(members.detection_timestamp_utc.str.replace(" ", "T", n=1, regex=False))
    require(times.notna().all() and times.dt.year.between(2018, 2023).all(), "Training only")
    consistent = ["grid_id", "detection_timestamp_utc", "latitude", "longitude", "source_sensor"]
    require(
        members.groupby("detection_id")[consistent].nunique(dropna=False).le(1).all().all(),
        "A shared detection retains identical source attributes",
    )
    parent = {key: key for key in sorted(ids)}

    def find(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    for _, shared in members.groupby("detection_id", sort=True):
        keys = sorted(shared.cluster_id)
        for key in keys[1:]:
            a, b = sorted([find(keys[0]), find(key)])
            parent[b] = a
    for case in cases.itertuples():
        subset = members.loc[members.cluster_id.eq(case.cluster_id)]
        t = times.loc[subset.index]
        first = subset.loc[t.eq(t.min())]
        require(
            len(subset) == case.detection_count
            and subset.scenario.eq(case.scenario).all()
            and t.min() == pd.Timestamp(case.first_detection_utc)
            and t.max() == pd.Timestamp(case.last_detection_utc)
            and len(first) == case.earliest_detection_count
            and sorted(first.grid_id.unique()) == json.loads(case.earliest_grid_ids_json),
            "Case counts, times and all earliest cells agree with source members",
        )
    require(
        spatial.cluster_id.is_unique
        and set(spatial.cluster_id) <= ids
        and not links.duplicated(["cluster_id", "reference_id"]).any()
        and set(links.cluster_id) <= set(spatial.cluster_id),
        "Unambiguous reference context keys",
    )
    require(
        spatial.first_rows.eq(
            spatial.cluster_id.map(cases.set_index("cluster_id").earliest_detection_count)
        ).all()
        and spatial.first_rows_in_any_reference.ge(0).all()
        and spatial.first_rows_in_any_reference.le(spatial.first_rows).all(),
        "Reference first-point counts agree with cases",
    )
    for frame in (spatial, links):
        require("target" in frame and frame.target.isna().all(), "No reference labels")
        boolean(frame.identity_accepted, "Reference identity gate")
        require(not frame.identity_accepted.any(), "No accepted reference identity")
    boolean(links.calendar_interval_overlap_hint, "Calendar diagnostic")
    require(
        links.source_independence.eq("shared_satellite_lineage_not_independent_ground_truth").all(),
        "Reference lineage preserved",
    )
    output = cases.copy().sort_values("cluster_id").reset_index(drop=True)
    output["overlap_component"] = output.cluster_id.map(find)
    families = []
    for _, group in output.groupby("overlap_component", sort=True):
        keys = sorted(group.cluster_id)
        family_id = "review_" + hashlib.sha256("|".join(keys).encode()).hexdigest()[:16]
        cells = group.earliest_grid_ids_json.map(lambda s: tuple(json.loads(s)))
        first = pd.to_datetime(group.first_detection_utc, utc=True)
        family = {
            "review_family_id": family_id,
            "case_variants": len(group),
            "scenarios_present": group.scenario.nunique(),
            "membership_patterns": group.membership_sha256.nunique(),
            "first_time_variants": first.nunique(),
            "first_time_span_hours": (first.max() - first.min()).total_seconds() / 3600,
            "first_grid_set_variants": cells.nunique(),
            "target_window_variants": group.candidate_prediction_timestamp_utc.nunique(),
            "multiple_cases_in_one_scenario": group.scenario.duplicated().any(),
            "case_ids_json": json.dumps(keys),
            "family_is_event_identity": False,
        }
        families.append(family)
        for field in (
            "review_family_id",
            "first_time_variants",
            "first_grid_set_variants",
            "target_window_variants",
            "multiple_cases_in_one_scenario",
        ):
            output.loc[group.index, field] = family[field]
    output = output.drop(columns="overlap_component")
    reference = spatial.set_index("cluster_id")
    reasons = []
    for row in output.itertuples():
        reason = []
        for field in (
            "temporal_chain_review",
            "spatial_chain_review",
            "multi_grid_first_detection_review",
            "calendar_year_crossing_review",
            "period_start_context_missing",
            "period_end_context_missing",
            "training_window_boundary_review",
        ):
            if getattr(row, field):
                reason.append(field)
        for field in ("first_time_variants", "first_grid_set_variants", "target_window_variants"):
            if getattr(row, field) > 1:
                reason.append("overlap_family_" + field)
        if row.multiple_cases_in_one_scenario:
            reason.append("overlap_family_split_merge_context")
        if row.cluster_id not in reference.index:
            reason.append("perimeter_not_assessed")
        else:
            s = reference.loc[row.cluster_id]
            if s.first_rows_in_any_reference < s.first_rows:
                reason.append("first_points_not_all_in_final_perimeter")
            selected = links.loc[links.cluster_id.eq(row.cluster_id)]
            if (~selected.calendar_interval_overlap_hint).any():
                reason.append("spatial_reference_calendar_mismatch")
        reasons.append(json.dumps(sorted(reason)))
    output["review_reasons_json"] = reasons
    # Ordering only: case families whose recorded candidate target changes are read first.
    output["review_order_group"] = output.target_window_variants.map(
        lambda n: "A_target_window_differs" if n > 1 else "B_other_open_cases"
    )
    output["review_status"] = "not_reviewed"
    output["label_admission"] = "blocked_by_unaccepted_protocol"
    output["target"] = pd.Series(pd.NA, index=output.index, dtype="Int8")
    assert_targets_unassigned(output)
    require(pd.DataFrame(families).review_family_id.is_unique, "Unique review families")
    return output.sort_values(
        ["review_order_group", "review_family_id", "cluster_id"]
    ), pd.DataFrame(families)
