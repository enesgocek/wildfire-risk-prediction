"""Rule sensitivity must preserve ties, incomplete comparisons and closed label gates."""

import json

import pandas as pd
import pytest

from wildfire_risk_prediction.event_decision_review import protocol, sensitivity
from wildfire_risk_prediction.target_admission import detection_windows


def inputs():
    points = {
        "x": ("2021-07-28T10:00:00+00:00", "G1"),
        "y": ("2021-07-29T00:00:00+00:00", "G2"),
        "z": ("2021-07-30T10:00:00+00:00", "G3"),
        "q": ("2021-07-28T10:00:00+00:00", "G4"),
        "r": ("2021-07-28T10:00:00+00:00", "G5"),
    }
    cases, members = [], []
    for cid, scenario, ids in (
        ("A", "s1", "xy"),
        ("B", "s2", "yz"),
        ("C", "s1", "z"),
        ("D", "s3", "qr"),
    ):
        first = min(points[i][0] for i in ids)
        grids = sorted(points[i][1] for i in ids if points[i][0] == first)
        window = detection_windows(pd.Series([first])).iloc[0]
        row = {
            "cluster_id": cid,
            "scenario": scenario,
            "membership_sha256": cid * 64,
            "event_status": "exploratory_cluster_only",
            "target": None,
            "negative_label_permitted": False,
            "first_detection_utc": first,
            "last_detection_utc": max(points[i][0] for i in ids),
            "candidate_prediction_timestamp_utc": window.prediction_timestamp_utc.isoformat(),
            "earliest_grid_ids_json": json.dumps(grids),
            "earliest_grid_count": len(grids),
            "earliest_detection_count": len(grids),
            "detection_count": len(ids),
            "training_window_boundary_review": bool(window.training_window_boundary_review),
        }
        for flag in (
            "temporal_chain_review",
            "spatial_chain_review",
            "calendar_year_crossing_review",
            "period_start_context_missing",
            "period_end_context_missing",
        ):
            row[flag] = False
        row["multi_grid_first_detection_review"] = len(grids) > 1
        cases.append(row)
        for i in ids:
            time, grid = points[i]
            members.append(
                {
                    "cluster_id": cid,
                    "scenario": scenario,
                    "detection_id": i,
                    "detection_timestamp_utc": time,
                    "grid_id": grid,
                    "latitude": 37.0,
                    "longitude": 31.0,
                    "source_sensor": "SNPP",
                }
            )
    spatial = pd.DataFrame(
        [
            {
                "cluster_id": "A",
                "first_rows": 1,
                "first_rows_in_any_reference": 0,
                "identity_accepted": False,
                "target": None,
            }
        ]
    )
    links = pd.DataFrame(
        [
            {
                "cluster_id": "A",
                "reference_id": "51931",
                "identity_accepted": False,
                "source_independence": "shared_satellite_lineage_not_independent_ground_truth",
                "calendar_interval_overlap_hint": False,
                "target": None,
            }
        ]
    )
    return pd.DataFrame(cases), pd.DataFrame(members), spatial, links


def test_transitive_overlap_is_review_context_and_midnight_maps_to_previous_window():
    cases, members, spatial, links = inputs()
    queue, families = sensitivity(cases, members, spatial, links)
    a = queue.set_index("cluster_id")
    assert a.loc[["A", "B", "C"], "review_family_id"].nunique() == 1
    assert a.loc["A", "review_family_id"] != a.loc["D", "review_family_id"]
    family = families.loc[families.case_variants.eq(3)].iloc[0]
    assert family.first_time_variants == 3
    assert family.target_window_variants == 2  # B's midnight is still in A's window.
    assert family.multiple_cases_in_one_scenario
    assert len(families) == 2 and not families.family_is_event_identity.any()
    assert queue.target.isna().all() and queue.review_status.eq("not_reviewed").all()
    assert queue.label_admission.eq("blocked_by_unaccepted_protocol").all()
    assert json.loads(a.loc["D", "earliest_grid_ids_json"]) == ["G4", "G5"]
    assert "perimeter_not_assessed" in json.loads(a.loc["D", "review_reasons_json"])
    reasons = json.loads(a.loc["A", "review_reasons_json"])
    assert "spatial_reference_calendar_mismatch" in reasons
    assert "first_points_not_all_in_final_perimeter" in reasons


def test_order_invariance_and_missing_scenarios_not_imputed():
    args = inputs()
    a, b = sensitivity(*args)
    c, d = sensitivity(*(frame.sample(frac=1, random_state=42) for frame in args))
    pd.testing.assert_frame_equal(a.reset_index(drop=True), c.reset_index(drop=True))
    pd.testing.assert_frame_equal(b, d)
    singleton = b.loc[b.case_variants.eq(1)].iloc[0]
    assert singleton.scenarios_present == 1
    assert singleton.first_grid_set_variants == 1  # Not proof of nine-scenario stability.


def test_no_reference_assessment_retains_all_cases_and_missing_evidence_reason():
    cases, members, spatial, links = inputs()
    q, _ = sensitivity(cases, members, spatial.iloc[:0], links.iloc[:0])
    assert len(q) == 4 and q.target.isna().all()
    assert all("perimeter_not_assessed" in json.loads(s) for s in q.review_reasons_json)


@pytest.mark.parametrize(
    "corruption",
    [
        "label",
        "count",
        "first_cell",
        "candidate_time",
        "boundary_flag",
        "duplicate_member",
        "source_conflict",
        "naive_member_time",
        "future_member",
        "scenario",
        "missing_case_members",
        "reference_identity",
        "reference_count",
        "reference_label",
        "reference_lineage",
        "calendar_flag",
        "duplicate_reference",
        "unknown_reference_case",
    ],
)
def test_corrupt_or_unaccepted_evidence_is_rejected(corruption):
    c, m, s, links = inputs()
    if corruption == "label":
        c.loc[0, "target"] = 1
    elif corruption == "count":
        c.loc[0, "detection_count"] = 22
    elif corruption == "first_cell":
        c.loc[0, "earliest_grid_ids_json"] = '["WRONG"]'
    elif corruption == "candidate_time":
        c.loc[0, "candidate_prediction_timestamp_utc"] = "2021-07-27T00:00:00+00:00"
    elif corruption == "boundary_flag":
        c.loc[0, "training_window_boundary_review"] = True
    elif corruption == "duplicate_member":
        m = pd.concat([m, m.iloc[:1]], ignore_index=True)
    elif corruption == "source_conflict":
        m.loc[1, "grid_id"] = "DIFFERENT"
    elif corruption == "naive_member_time":
        m.loc[0, "detection_timestamp_utc"] = "2021-07-28 10:00:00"
    elif corruption == "future_member":
        m.loc[0, "detection_timestamp_utc"] = "2025-07-28T10:00:00+00:00"
    elif corruption == "scenario":
        m.loc[0, "scenario"] = "changed"
    elif corruption == "missing_case_members":
        m = m.loc[~m.cluster_id.eq("D")]
    elif corruption == "reference_identity":
        links["identity_accepted"] = True
    elif corruption == "reference_count":
        s["first_rows"] = 2
    elif corruption == "reference_label":
        s["target"] = 0
    elif corruption == "reference_lineage":
        links["source_independence"] = "independent"
    elif corruption == "calendar_flag":
        links["calendar_interval_overlap_hint"] = "False"
    elif corruption == "duplicate_reference":
        links = pd.concat([links, links], ignore_index=True)
    else:
        links["cluster_id"] = "UNKNOWN"
    with pytest.raises(ValueError):
        sensitivity(c, m, s, links)


def test_draft_exports_six_unaccepted_requirements_without_enabling_labels():
    p = protocol()
    assert len(p["gates"]) == 6 and all(g["status"] == "unaccepted" for g in p["gates"])
    assert p["status"].startswith("draft") and p["scenario_selected"] is None
    assert not p["positive_label_permitted"] and not p["negative_label_permitted"]
    assert not p["model_ready"] and p["daily_observation_status"] == "unknown"
