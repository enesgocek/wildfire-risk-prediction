"""Materialize the researcher's one-case possible L membership without any target labels."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import assert_targets_unassigned

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
POLICY = ROOT / "configs/source_linked_L_proposal_v1.json"
PILOT = BASE / "noisy_positive_pu_pilot_v1/20261119T121014Z_122b22c7/readback.json"
CONTEXT = BASE / "salur_event_context_v1/20261118T230221Z_cab0c9e1/readback.json"
MARKER = (
    BASE
    / "public_start_geometry_v1/forestry_chamber_2021/salur_marker_v1"
    / "20261108T194701Z_a7895f19/readback.json"
)
NATIVE = BASE / "salur_native_support_v1/20261119T114722Z_fb7ab551/readback.json"
PINS = {
    PILOT: "85d563d82dc13656136fe855e8e80252e5ef28dbdbb799fe3a0c814a3414f0b2",
    CONTEXT: "89ffb290079ae4167cbf3b577e9787cbbde5092118acaab0d43d704189dad846",
    MARKER: "fa15c440eb6a025aada777cab58544c23ba5083302ede626adb45a222da788d8",
    NATIVE: "26735f235170998749b763847281c109c72a878231af4535e8272f65b596ec89",
}


def main():
    require(all(digest(p) == h for p, h in PINS.items()), "Pinned review inputs")
    policy = json.loads(POLICY.read_text())
    require(
        policy["version"] == "source_linked_L_proposal_v1"
        and policy["source_case_id"] == "salur_2021_07_28",
        "Single-case researcher direction",
    )
    for key in (
        "candidate_L_is_verified_true_positive",
        "source_location_accuracy_bound_measured",
        "positive_enrichment_verified",
        "global_case_mapping_policy_accepted",
        "positive_label_permitted",
        "negative_label_permitted",
        "model_ready",
        "training_authorized",
        "final_merge_permitted",
    ):
        require(policy[key] is False, "No scientific acceptance from possible membership")
    require(policy["daily_observation_status"] == "unknown", "Unknown observation state")
    pilot, context, marker, native = [
        json.loads(p.read_text()) for p in (PILOT, CONTEXT, MARKER, NATIVE)
    ]
    pins = {**PINS, POLICY: digest(POLICY)}
    for name in ("L_case_cell_ambiguity.csv", "U_key_sample.csv"):
        p = PILOT.parent / name
        pins[p] = pilot["artifact_sha256"][name]
        require(digest(p) == pins[p], "Prepared key tables unchanged")
    local = CONTEXT.parent / "local_detections.csv"
    pins[local] = context["artifact_sha256"][local.name]
    require(digest(local) == pins[local], "Catalog-local membership")
    points = pd.read_csv(local)
    first = points.loc[points.detection_id.eq(native["detection_id"])]
    selected = policy["candidate_grid_id"]
    require(
        len(first) == 1 and first.grid_id.iloc[0] == selected == context["marker_cell"],
        "Same local native center and reference cell",
    )
    require(
        len(marker["estimates"]) == 2
        and all(v["center_cell"] == selected for v in marker["estimates"].values()),
        "Both source marker fits retained",
    )
    table = pd.read_csv(PILOT.parent / "L_case_cell_ambiguity.csv")
    assert_targets_unassigned(table)
    require(
        len(table) == 4 and table.source_case_id.eq(policy["source_case_id"]).all(),
        "One four-cell case",
    )
    table["proposed_membership"] = table.grid_id.map(
        lambda g: "possible_noisy_L" if g == selected else "review_unassigned"
    )
    table["membership_is_target_label"] = False
    candidate_l = table.loc[table.grid_id.eq(selected)].copy()
    remaining = table.loc[~table.grid_id.eq(selected)].copy()
    require(
        len(candidate_l) == 1
        and len(remaining) == 3
        and set(table.grid_id) == set(candidate_l.grid_id) | set(remaining.grid_id),
        "No first-cell deletion or duplication",
    )
    require(
        candidate_l.reference_marker_cell_match.all()
        and not remaining.reference_marker_cell_match.any(),
        "Source matching role",
    )
    out = (
        BASE
        / "source_linked_L_proposal_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("possible_L_cell.csv", candidate_l),
        ("remaining_case_cells.csv", remaining),
    ):
        p = out / name
        frame.to_csv(p, index=False, mode="x")
        check = pd.read_csv(p)
        pd.testing.assert_frame_equal(frame.reset_index(drop=True), check, check_dtype=False)
        assert_targets_unassigned(check)
        artifacts[name] = digest(p)
    result = {
        "status": "one_possible_L_cell_prepared_not_a_fire_label",
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "script_sha256": digest(Path(__file__)),
        "artifact_sha256": artifacts,
        "source_cases": 1,
        "possible_L_rows": 1,
        "other_case_cells_retained": 3,
        "common_case_identity_preserved": True,
        "U_sample_sha256_unchanged": pins[PILOT.parent / "U_key_sample.csv"],
        "verified_positive_labels": 0,
        "verified_negative_labels": 0,
        "alpha_estimated": False,
        "beta_estimated": False,
        "model_trained": False,
        "features_joined": False,
        "final_merge_performed": False,
        "heldout_values_read": False,
        "global_mapping_policy_accepted": False,
    }
    require(all(digest(p) == h for p, h in pins.items()), "Input closure")
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(json.loads(p.read_text()) == result, "Readback")
    print(p.relative_to(ROOT), digest(p))
    print("PASS one possible L row, three preserved alternatives, U unchanged; no target labels")


if __name__ == "__main__":
    main()
