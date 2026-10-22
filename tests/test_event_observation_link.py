import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.event_observation_link import link_pilot


def inputs():
    c = pd.DataFrame(
        {
            "grid_id": ["g1", "g4"],
            "prediction_timestamp_utc": ["2021-01-01T00:00:00+00:00"] * 2,
            "scenarios_with_candidate": [9, 3],
            "review_category": [
                "all_presence_time_and_membership_equal",
                "candidate_presence_sensitive",
            ],
            "review_flags_json": ["[]", "[]"],
            "positive_label_permitted": False,
            "negative_label_permitted": False,
            "event_identity_accepted": False,
            "event_membership_complete": False,
            "target": np.nan,
        }
    )
    o = pd.DataFrame(
        {
            "review_unit_id": ["u1", "u2", "u3"],
            "grid_id": ["g1", "g2", "g3"],
            "target_day": ["2021-01-01"] * 3,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "labels_created": False,
            "full_daily_observation_proven": False,
            "accepted_label_rule": False,
            "target": np.nan,
            "expected_pair_count": 1,
            "completed_pair_count": 1,
            "missing_pair_count": 0,
            "all_planned_pairs_processed": True,
            "thermal_center_definite_count": [1, 1, 0],
            "thermal_center_boundary_count": 0,
            "nominal_land_fraction": 0.99,
            "repeat_12h_fraction": 0.5,
            "nominal_land_all_four_bins_fraction": 0.0,
            "cloud_fraction": 0.2,
            "anypart_land_longest_envelope_gap_seconds": 45000.0,
        }
    )
    return c, o


def test_every_pilot_preserved_absence_distinguished_from_thermal_and_unknown():
    c, o = inputs()
    old_c, old_o = c.copy(deep=True), o.copy(deep=True)
    linked, outside = link_pilot(c, o)
    assert len(linked) == 3 and len(outside) == 1
    assert linked.first_candidate_present_in_catalog_union.tolist() == [True, False, False]
    assert linked.proposed_evidence_review_route.tolist() == [
        "agreement_candidate_observation_review",
        "loaded_thermal_without_first_candidate_review",
        "no_first_candidate_no_loaded_thermal_review",
    ]
    assert linked.target.isna().all() and outside.target.isna().all()
    assert outside.pilot_thermal_center_present.isna().all()
    assert outside.pilot_nominal_land_fraction.isna().all()
    assert not linked.route_is_label_admission.any()
    assert not linked.positive_label_permitted.any() and not linked.negative_label_permitted.any()
    pd.testing.assert_frame_equal(c, old_c)
    pd.testing.assert_frame_equal(o, old_o)


def test_sensitive_first_candidate_is_separate_review_route():
    c, o = inputs()
    c.loc[0, ["scenarios_with_candidate", "review_category"]] = [3, "candidate_presence_sensitive"]
    linked, _ = link_pilot(c, o)
    assert (
        linked.iloc[0].proposed_evidence_review_route
        == "grouping_sensitive_candidate_observation_review"
    )


def test_incomplete_plan_and_boundary_are_not_admitted():
    c, o = inputs()
    o.loc[0, ["completed_pair_count", "missing_pair_count", "all_planned_pairs_processed"]] = [
        0,
        1,
        False,
    ]
    o.loc[1, "thermal_center_boundary_count"] = 1
    linked, _ = link_pilot(c, o)
    assert linked.iloc[0].proposed_evidence_review_route == "incomplete_pilot_geometry_plan_review"
    assert linked.iloc[1].proposed_evidence_review_route == "boundary_thermal_time_review"
    assert linked.target.isna().all()


@pytest.mark.parametrize(
    "case",
    [
        "duplicate_candidate",
        "duplicate_pilot",
        "candidate_target",
        "observation_target",
        "open_gate",
        "string_gate",
        "validation",
        "bad_pair_count",
        "bad_fraction",
        "false_complete_plan",
        "bad_gap",
        "category_count_disagreement",
    ],
)
def test_invalid_evidence_rejected(case):
    c, o = inputs()
    if case == "duplicate_candidate":
        c = pd.concat([c, c.iloc[[0]]])
    elif case == "duplicate_pilot":
        o = pd.concat([o, o.iloc[[0]]])
    elif case == "candidate_target":
        c.loc[0, "target"] = 1
    elif case == "observation_target":
        o.loc[0, "target"] = 0
    elif case == "open_gate":
        o.loc[0, "accepted_label_rule"] = True
    elif case == "string_gate":
        o["negative_label_permitted"] = "False"
    elif case == "validation":
        o.loc[0, "target_day"] = "2024-01-01"
    elif case == "bad_pair_count":
        o.loc[0, "missing_pair_count"] = 1
    elif case == "bad_fraction":
        o.loc[0, "nominal_land_fraction"] = np.nan
    elif case == "false_complete_plan":
        o.loc[0, "all_planned_pairs_processed"] = False
    elif case == "bad_gap":
        o.loc[0, "anypart_land_longest_envelope_gap_seconds"] = 86401
    elif case == "category_count_disagreement":
        c.loc[0, "scenarios_with_candidate"] = 3
    with pytest.raises(ValueError):
        link_pilot(c, o)
