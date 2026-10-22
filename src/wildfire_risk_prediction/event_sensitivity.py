"""Full-catalog first-cell sensitivity, without treating agreement as truth."""

import json
import re

import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.label_protocol_review import SCENARIOS
from wildfire_risk_prediction.target_admission import detection_windows


def summarize_candidates(frame):
    """Describe union keys only; missing scenario support never becomes a zero label."""
    fields = [
        "scenario",
        "candidate_component_id",
        "membership_sha256",
        "grid_id",
        "first_detection_utc",
        "prediction_timestamp_utc",
        "review_flags_json",
    ]
    require(not frame.empty and frame[fields].notna().all().all(), "Complete candidate evidence")
    require(set(frame.scenario) == set(SCENARIOS), "Exactly nine scenario catalogs")
    require("target" not in frame or frame.target.isna().all(), "No admitted targets")
    require(
        not frame.duplicated(["scenario", "candidate_component_id", "grid_id"]).any(),
        "One first-cell entry per scenario component",
    )
    data = frame.copy()
    first = pd.to_datetime(data.first_detection_utc, utc=True, format="ISO8601")
    prediction = pd.to_datetime(data.prediction_timestamp_utc, utc=True, format="ISO8601")
    require(first.dt.year.between(2018, 2023).all(), "Training first detections only")
    expected = detection_windows(data.first_detection_utc).prediction_timestamp_utc
    require(prediction.eq(expected).all(), "Right-closed prediction day")
    for row in data.itertuples():
        require(row.candidate_component_id.startswith(row.scenario + "_"), "Scenario identity")
        require(bool(re.fullmatch(r"[a-f0-9]{64}", row.membership_sha256)), "Membership digest")
        require(bool(re.fullmatch(r"E6933_5K_V1_C[0-9]+_R[0-9]+", row.grid_id)), "Grid key")
        flags = json.loads(row.review_flags_json)
        require(isinstance(flags, list) and all(isinstance(x, str) for x in flags), "Flags list")
    for _, group in data.groupby(["scenario", "candidate_component_id"], sort=False):
        require(
            group.first_detection_utc.nunique() == group.membership_sha256.nunique() == 1,
            "Shared component evidence",
        )
    data["first_detection_utc"] = first.map(pd.Timestamp.isoformat)
    data["prediction_timestamp_utc"] = prediction.map(pd.Timestamp.isoformat)
    units = []
    for (grid, stamp), group in data.groupby(["grid_id", "prediction_timestamp_utc"], sort=True):
        per_scenario = list(group.groupby("scenario", sort=True))
        count = len(per_scenario)
        time_sets = {tuple(sorted(set(g.first_detection_utc))) for _, g in per_scenario}
        membership_sets = {tuple(sorted(set(g.membership_sha256))) for _, g in per_scenario}
        flags = sorted({x for raw in group.review_flags_json for x in json.loads(raw)})
        time_equal, members_equal = len(time_sets) == 1, len(membership_sets) == 1
        if count < 9:
            category = "candidate_presence_sensitive"
        elif not time_equal or not members_equal:
            category = "all_presence_time_or_membership_sensitive"
        else:
            category = "all_presence_time_and_membership_equal"
        units.append(
            {
                "grid_id": grid,
                "prediction_timestamp_utc": stamp,
                "scenarios_with_candidate": count,
                "present_scenarios_json": json.dumps([s for s, _ in per_scenario]),
                "component_matches_min_present_scenario": min(len(g) for _, g in per_scenario),
                "component_matches_max_present_scenario": max(len(g) for _, g in per_scenario),
                "first_time_set_variants_present_scenarios": len(time_sets),
                "membership_set_variants_present_scenarios": len(membership_sets),
                "review_category": category,
                "review_flags_json": json.dumps(flags),
                "prediction_inside_training": 2018 <= pd.Timestamp(stamp).year <= 2023,
                "event_identity_accepted": False,
                "event_membership_complete": False,
                "positive_label_permitted": False,
                "negative_label_permitted": False,
                "target": None,
            }
        )
    return pd.DataFrame(units)
