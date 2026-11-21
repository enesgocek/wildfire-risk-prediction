"""Bind existing RFs to a proposed 2022 calendar diagnostic; no scoring, S assignment or fit."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.feature_partition import parse_csv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
POLICY = ROOT / "configs/source_calendar_fixed_model_diagnostic_v1.json"
REVIEW = BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896"
AUDIT = BASE / "source_calendar_feature_audit_v1/20261121T165526Z_5c6a7598"
FULL = BASE / "satellite_PU_ranking_run_v1/20261120T012805Z_04789b23"
FULL_SHA = "971b85def11809d0d48f4a3618233588e6a7022e7ddea5861fb94054cbcb84a1"
ABLATION = BASE / "satellite_PU_ablation_run_v1/20261120T014426Z_44c25642"
ABLATION_SHA = "fa9321e6268ffba478c6250d6cc32b0d5516ce3b872b9a8271920edb9d1d3324"
PROPOSALS = BASE / "satellite_PU_L_proposals_v1/20261120T005519Z_62f3f815"
PROPOSALS_SHA = "679a5ad9eab6342fa153c46cbbcc8f1e494b92256b592ba84f24823d0c0a4a85"


def main():
    policy = json.loads(POLICY.read_bytes())
    require(
        all(
            policy[k] is False
            for k in (
                "fixed_model_scoring_authorized",
                "new_auxiliary_source_indicator_codes_authorized",
                "model_refitting_authorized",
                "negative_label_permitted",
                "final_merge_permitted",
                "scientific_values_2023_2024_2025_read_permitted",
            )
        ),
        "Preparation cannot authorize the diagnostic",
    )
    pins = {
        POLICY: digest(POLICY),
        REVIEW / "readback.json": policy["calendar_X_readback_sha256"],
        AUDIT / "readback.json": policy["separate_calendar_X_audit_sha256"],
        FULL / "readback.json": FULL_SHA,
        ABLATION / "readback.json": ABLATION_SHA,
        PROPOSALS / "readback.json": PROPOSALS_SHA,
    }
    require(all(digest(p) == h for p, h in pins.items()), "Exact completed parents")
    review, audit = [json.loads((p / "readback.json").read_bytes()) for p in (REVIEW, AUDIT)]
    require(
        audit["parent_readback_sha256"] == policy["calendar_X_readback_sha256"],
        "Separate audit binding",
    )
    snapshot = REVIEW / review["snapshot_directory"]
    for relative, sha in review["artifact_sha256"].items():
        pins[REVIEW / relative] = sha
    metadata = parse_csv((snapshot / "review_roles.csv").read_bytes())
    require(
        metadata.target.isna().all() and metadata.accepted_L_membership.isna().all(),
        "No true labels",
    )
    held = metadata.loc[metadata.review_temporal_role.eq("proposed_assessment_2022")]
    require(
        len(held) == 6573 and held.prediction_timestamp_utc.str.startswith("2022-").all(),
        "Frozen 2022 diagnostic keys",
    )
    held_keys = set(
        held[["grid_id", "prediction_timestamp_utc"]].itertuples(index=False, name=None)
    )
    proposals = json.loads((PROPOSALS / "readback.json").read_bytes())
    groups_path = PROPOSALS / "all_first_cells_with_proposal_flags.csv"
    pins[groups_path] = proposals["artifact_sha256"][groups_path.name]
    require(digest(groups_path) == pins[groups_path], "Same unaccepted scenario proposals")
    groups = pd.read_csv(groups_path)
    scenario_counts, models = {}, []
    for scenario, block in groups.loc[groups.possible_L_proposal].groupby("scenario", sort=True):
        source = (
            set(block[["grid_id", "prediction_timestamp_utc"]].itertuples(index=False, name=None))
            & held_keys
        )
        scenario_counts[scenario] = {
            "calendar_rows": 6573,
            "existing_scenario_proposal_context_keys": len(source),
            "other_calendar_days_not_verified_fire_negatives": 6573 - len(source),
        }
    for folder, variant, selected in (
        (FULL, "full_27_features", "random_forest"),
        (ABLATION, "weather_only", "weather_only"),
        (ABLATION, "static_cover_terrain_only", "static_cover_terrain_only"),
    ):
        parent = json.loads((folder / "readback.json").read_bytes())
        for scenario in sorted(scenario_counts):
            relative = scenario + "/" + selected + ".joblib"
            p = folder / relative
            pins[p] = parent["artifact_sha256"][relative]
            models.append(
                {
                    "scenario": scenario,
                    "variant": variant,
                    "path": p.relative_to(ROOT).as_posix(),
                    "sha256": pins[p],
                }
            )
    require(
        len(models) == 27
        and len(scenario_counts) == 9
        and all(digest(p) == h for p, h in pins.items()),
        "All fixed models and unchanged X",
    )
    out = (
        BASE
        / "source_calendar_fixed_model_plan_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    report = {
        "status": "fixed_27_RF_calendar_diagnostic_proposed_not_scored_or_fitted",
        "policy": policy,
        "scenario_counts": scenario_counts,
        "fixed_models": models,
        "scored_rows_now": 0,
        "new_models_fitted": 0,
        "new_source_indicator_codes_assigned_now": False,
        "Y_or_accepted_L_created": 0,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print("PROPOSAL ONLY; no new scoring, S, Y, fit or final merge", flush=True)


if __name__ == "__main__":
    main()
