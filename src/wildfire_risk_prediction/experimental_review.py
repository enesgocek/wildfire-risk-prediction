"""Preserve scenario proposals as review context, never promote S/U to true labels."""

import pandas as pd

from .feature_join import KEYS, feature_names, require


def memberships(features, roles, lineage, scenarios):
    require(features.columns.tolist() == KEYS + feature_names(), "Exact candidate feature schema")
    require(not features.duplicated(KEYS).any() and not roles.duplicated(KEYS).any(), "Unique keys")
    pd.testing.assert_frame_equal(features[KEYS], roles[KEYS], check_exact=True)
    require(
        roles.target.isna().all()
        and roles.accepted_L_membership.isna().all()
        and roles.daily_observation_status.eq("unknown").all(),
        "Unassigned true target and accepted L",
    )
    require(
        features.prediction_timestamp_utc.str[:4]
        .isin(["2018", "2019", "2020", "2021", "2022"])
        .all(),
        "Only approved inspection years",
    )
    require(set(lineage.scenario) == set(scenarios), "All unchanged scenario directions")
    proposed = lineage.loc[lineage.possible_L_proposal.eq(True)]
    meta = roles.copy()
    all_keys = set(map(tuple, features[KEYS].to_numpy()))
    bitmask = [0] * len(meta)
    for i, scenario in enumerate(scenarios):
        selected = set(map(tuple, proposed.loc[proposed.scenario.eq(scenario), KEYS].to_numpy()))
        require(selected <= all_keys, "Every existing proposal key retained in the calendar")
        flag = [k in selected for k in map(tuple, features[KEYS].to_numpy())]
        meta["S_candidate_context_" + scenario] = flag
        bitmask = [a | (int(b) << i) for a, b in zip(bitmask, flag, strict=True)]
    meta["scenario_proposal_bitmask_for_display_only"] = bitmask
    union = meta.scenario_proposal_bitmask_for_display_only.gt(0)
    require(
        union.equals(meta.known_proposal_key_in_union),
        "Exact previous proposal union; no new S assignment",
    )
    meta["missing_feature_count"] = features[feature_names()].isna().sum(axis=1)
    meta["negative_label_permitted"] = False
    meta["scope"] = "experimental_calendar_inspection_not_population_U_or_training_acceptance"
    return meta
