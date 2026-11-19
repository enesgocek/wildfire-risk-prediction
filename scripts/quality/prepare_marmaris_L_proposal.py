"""Materialize one approved membership proposal and index two cases without labels/features."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import assert_targets_unassigned, specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
POLICY = ROOT / "configs/marmaris_L_proposal_v1.json"
DIRECTION = BASE / "marmaris_L_direction_v1/20261119T131723Z_8bba0c84/readback.json"
SALUR = BASE / "source_linked_L_proposal_v1/20261119T121351Z_2d9aeb30/readback.json"
PILOT = BASE / "noisy_positive_pu_pilot_v1/20261119T121014Z_122b22c7/readback.json"
PINS = {
    DIRECTION: "c6b5206886af35fa34f7cc195fb662904ea20196e30c1dc1c89c82fd3e3021e4",
    SALUR: "d0a09ecb249eb81d75e4494beaf0ca9989092c813ddd6b40e4acf0817576ab3e",
    PILOT: "85d563d82dc13656136fe855e8e80252e5ef28dbdbb799fe3a0c814a3414f0b2",
}


def main():
    pins = dict(PINS)
    require(all(digest(p) == h for p, h in pins.items()), "Pinned preparation parents")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    require(
        policy["version"] == "marmaris_L_proposal_v1"
        and policy["scope"] == "single_Marmaris_case_proposal_not_global_mapping_rule"
        and policy["decision_parent_sha256"] == pins[DIRECTION],
        "Explicit one-case direction",
    )
    require(policy["M2_cover_uncertainty_preserved"] is True, "M2 remains uncertain")
    for field in (
        "snap_center_to_nearest_land_cell",
        "symbol_center_inside_clipped_AOI",
        "source_location_accuracy_bound_measured",
        "source_three_vs_four_starts_resolved",
        "researcher_cover_percentages_are_measured",
        "candidate_L_is_verified_true_positive",
        "global_case_mapping_policy_accepted",
        "positive_enrichment_verified",
        "class_conditional_selection_verified",
        "positive_label_permitted",
        "negative_label_permitted",
        "model_ready",
        "training_authorized",
        "final_merge_permitted",
    ):
        require(policy[field] is False, "No scientific acceptance from proposal direction")
    require(policy["daily_observation_status"] == "unknown", "Unknown daily observation retained")
    direction, salur, pilot = [
        json.loads(p.read_text(encoding="utf-8")) for p in (DIRECTION, SALUR, PILOT)
    ]
    require(
        direction["current_L_memberships_created"] == 0
        and direction["researcher_cover_notes"]["notes"]["M2"]["preliminary_cover"]
        == "uncertain_wooded_cover",
        "Review uncertainty preserved",
    )
    pins[POLICY] = digest(POLICY)
    table_path = DIRECTION.parent / "conditional_cell_options.csv"
    pins[table_path] = direction["artifact_sha256"][table_path.name]
    require(digest(table_path) == pins[table_path], "Original conditional options unchanged")
    table = pd.read_csv(table_path)
    assert_targets_unassigned(table)
    selected = policy["candidate_grid_id"]
    require(
        len(table) == 3 and table.source_case_id.eq(policy["source_case_id"]).all(),
        "Three preserved case-cell alternatives",
    )
    chosen = table.loc[table.grid_id.eq(selected)]
    require(
        len(chosen) == 1
        and chosen.both_symbol_fits_overlap_this_cell.all()
        and chosen.planned_primary_centers.eq(5).all()
        and not chosen.symbol_center_inside_clipped_AOI.any(),
        "Area match, never a snapped point",
    )
    require(table.prediction_timestamp_utc.eq(policy["prediction_timestamp_utc"]).all(), "Same T")
    table = table.drop(
        columns=[
            "current_membership",
            "if_researcher_selects_option_A",
            "if_researcher_selects_option_B",
        ]
    )
    table["proposed_membership"] = table.grid_id.map(
        lambda grid: "possible_noisy_L" if grid == selected else "review_unassigned"
    )
    table["membership_is_target_label"] = False
    table["daily_observation_status"] = "unknown"
    possible = table.loc[table.grid_id.eq(selected)].copy()
    remaining = table.loc[~table.grid_id.eq(selected)].copy()
    require(len(possible) == 1 and len(remaining) == 2, "One proposal and two unassigned cells")
    old_path, alternatives_path = (
        SALUR.parent / "possible_L_cell.csv",
        SALUR.parent / "remaining_case_cells.csv",
    )
    for p in (old_path, alternatives_path):
        pins[p] = salur["artifact_sha256"][p.name]
        require(digest(p) == pins[p], "Earlier Salur proposal unchanged")
    old = pd.read_csv(old_path)
    assert_targets_unassigned(old)
    require(
        len(old) == 1 and old.proposed_membership.eq("possible_noisy_L").all(),
        "One earlier proposal",
    )
    u_path = PILOT.parent / "U_key_sample.csv"
    pins[u_path] = pilot["artifact_sha256"][u_path.name]
    require(digest(u_path) == pins[u_path], "Outcome-independent U sample unchanged")
    u = pd.read_csv(u_path)
    assert_targets_unassigned(u)
    require(
        len(u) == 2048 and u.review_role.eq("U_unknown_not_negative").all(), "Same unknown sample"
    )
    out = (
        BASE
        / "marmaris_L_proposal_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    for name, frame in (("possible_L_cell.csv", possible), ("remaining_case_cells.csv", remaining)):
        path = out / name
        frame.to_csv(path, index=False, mode="x")
        check = pd.read_csv(path)
        pd.testing.assert_frame_equal(frame.reset_index(drop=True), check, check_dtype=False)
        assert_targets_unassigned(check)
    # This is an evidence index, not a joined model table or a fitted L sample.
    registry = []
    for case_table, source_path, basis in (
        (old, old_path, "source_marker_point_fits_and_native_center"),
        (possible, out / "possible_L_cell.csv", "visible_symbol_area_intersection"),
    ):
        row = case_table.iloc[0]
        overlap = u.grid_id.eq(row.grid_id) & u.prediction_timestamp_utc.eq(
            row.prediction_timestamp_utc
        )
        registry.append(
            {
                "source_case_id": row.source_case_id,
                "grid_id": row.grid_id,
                "prediction_timestamp_utc": row.prediction_timestamp_utc,
                "target_end_inclusive_utc": row.target_end_inclusive_utc,
                "proposal_artifact": source_path.relative_to(ROOT).as_posix(),
                "proposal_sha256": digest(source_path),
                "source_geometry_basis": basis,
                "U_sample_key_overlap": int(overlap.sum()),
                "U_overlaps_removed": False,
                "proposed_membership": "possible_noisy_L",
                "target": None,
                "independent_true_positive_verified": False,
            }
        )
    require(
        len({(r["grid_id"], r["prediction_timestamp_utc"]) for r in registry}) == 2,
        "Distinct proposal keys, not independent fire verification",
    )
    pd.DataFrame(registry).to_csv(out / "two_case_review_index.csv", index=False)
    assert_targets_unassigned(pd.read_csv(out / "two_case_review_index.csv"))
    result = {
        "status": "Marmaris_possible_L_proposal_prepared_not_a_fire_label",
        "source_case_id": policy["source_case_id"],
        "possible_L_rows_this_case": 1,
        "other_case_cells_retained": 2,
        "M2_cover_uncertainty_preserved": True,
        "review_index_source_cases": 2,
        "review_index_possible_L_rows": 2,
        "true_independent_fire_count_verified": False,
        "global_mapping_policy_accepted": False,
        "U_sample_rows": len(u),
        "U_sample_sha256_unchanged": pins[u_path],
        "positive_enrichment_verified": False,
        "shared_class_conditionals_verified": False,
        "alpha_estimated": False,
        "beta_estimated": False,
        "verified_positive_labels": 0,
        "verified_negative_labels": 0,
        "features_joined": False,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    require(all(digest(p) == h for p, h in pins.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == result, "Readback")
    print(path.relative_to(ROOT).as_posix(), digest(path))
    print(
        "PASS one Marmaris proposal, two retained alternatives; two-case review index, U unchanged"
    )


if __name__ == "__main__":
    main()
