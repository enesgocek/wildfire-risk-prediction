"""Apply the researcher-approved proposal direction; no accepted L, binary Y or training."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PARENT = BASE / "satellite_PU_preparation_v1/20261120T004314Z_88c008ce/readback.json"
PARENT_SHA = "1288a62e58f3982ca1b64147d2a36542a685117f770fa118259d8055ca619d8e"
POLICY = ROOT / "configs/satellite_pu_cover_direction_v1.json"
PROTECTED = {
    BASE / "wf1538_review_retention_v1/20261119T184009Z_0bd7da1f/readback.json": (
        "ed94ee3daa0fcfb9141ab651adb27ecde152023d4f798ab4aefbb8812b551848"
    ),
    BASE / "source_linked_L_proposal_v1/20261119T121351Z_2d9aeb30/readback.json": (
        "d0a09ecb249eb81d75e4494beaf0ca9989092c813ddd6b40e4acf0817576ab3e"
    ),
    BASE / "marmaris_L_proposal_v1/20261119T134021Z_5272c4bd/readback.json": (
        "89d0305b9f5c54809e6c1170a30c21fe1a0230da4afc65720d5eef5bc8c5f476"
    ),
}


def propose(frame, policy):
    require(
        policy["decision_source"]
        == (
            "explicit_user_selection_A_CGLS2017_primary_CORINE2018_auxiliary_"
            "prepare_possible_L_proposals"
        ),
        "Explicit cover preparation direction",
    )
    require(
        not any(
            policy[k]
            for k in (
                "CORINE_2018_required_for_proposal",
                "possible_L_proposals_are_accepted_L_memberships",
                "new_accepted_L_or_Y_labels_permitted",
                "negative_label_permitted",
                "model_training_authorized",
                "final_merge_permitted",
            )
        ),
        "Proposal cannot open admission or training",
    )
    require(
        frame.target.isna().all() and frame.weak_positive_membership.isna().all(),
        "Unassigned inputs",
    )
    for name in ("all_first_centers_woody_2017", "fit_role_boundary_review"):
        require(frame[name].map(lambda x: type(x) is bool).all(), "Explicit boolean review flags")
    result = frame.copy()
    grid, stamp = policy["WF1538_retained_key"]
    protected = result.grid_id.eq(grid) & result.prediction_timestamp_utc.eq(stamp)
    eligible = result.all_first_centers_woody_2017 & ~result.fit_role_boundary_review & ~protected
    result["possible_L_proposal"] = eligible
    result["researcher_WF1538_key_retention"] = protected
    result["proposal_status"] = "review_unassigned"
    result.loc[eligible, "proposal_status"] = "possible_L_not_accepted"
    result.loc[protected, "proposal_status"] = "retained_outside_L_by_researcher"
    result.loc[result.fit_role_boundary_review, "proposal_status"] = "fit_boundary_review"
    require(
        len(result) == len(frame)
        and result.target.isna().all()
        and result.weak_positive_membership.isna().all(),
        "All first cells remain; no Y or L",
    )
    return result


def main():
    pins = {PARENT: PARENT_SHA, POLICY: digest(POLICY), **PROTECTED}
    require(
        all(digest(p) == h for p, h in pins.items()), "Preparation and protected case identities"
    )
    parent, policy = [json.loads(p.read_bytes()) for p in (PARENT, POLICY)]
    source = PARENT.parent / "all_scenario_first_cell_cover_review.csv"
    pins[source] = parent["artifact_sha256"][source.name]
    require(digest(source) == pins[source], "Same complete first-cell context")
    frame = propose(pd.read_csv(source), policy)
    summaries = []
    for name, group in frame.groupby("scenario", sort=True):
        selected = group.loc[group.possible_L_proposal]
        summaries.append(
            {
                "scenario": name,
                "all_first_cell_rows_preserved": len(group),
                "possible_L_proposal_rows": len(selected),
                "possible_L_distinct_keys": len(
                    selected[["grid_id", "prediction_timestamp_utc"]].drop_duplicates()
                ),
                "WF1538_rows_retained_outside_proposal": int(
                    group.researcher_WF1538_key_retention.sum()
                ),
            }
        )
    selected = frame.loc[frame.possible_L_proposal]
    key_list = (
        selected[["grid_id", "prediction_timestamp_utc"]]
        .drop_duplicates()
        .sort_values(["grid_id", "prediction_timestamp_utc"])
    )
    key_list["target"] = pd.NA
    key_list["accepted_L_membership"] = pd.NA
    key_list["scope"] = "union_of_scenario_proposals_for_feature_review_only"
    out = (
        BASE
        / "satellite_PU_L_proposals_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    frame.to_csv(out / "all_first_cells_with_proposal_flags.csv", index=False)
    key_list.to_csv(out / "proposal_key_union.csv", index=False)
    report = {
        "status": "researcher_cover_direction_possible_L_proposals_only_not_admission",
        "decision": policy,
        "scenario_summaries": summaries,
        "all_first_cell_rows_preserved": len(frame),
        "possible_L_key_union": len(key_list),
        "new_accepted_L_or_Y_memberships": 0,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {
            n: digest(out / n)
            for n in ("all_first_cells_with_proposal_flags.csv", "proposal_key_union.csv")
        },
    }
    require(all(digest(p) == h for p, h in pins.items()), "Protected inputs remain unchanged")
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    print("possible_L_key_union", len(key_list), "readback_sha256", digest(path), flush=True)
    for item in summaries:
        print(json.dumps(item), flush=True)


if __name__ == "__main__":
    main()
