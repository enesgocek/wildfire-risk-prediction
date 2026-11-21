"""Score fixed RFs in the approved 2022 calendar diagnostic, with no training or true labels."""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd
from audit_satellite_pu_ranking_run import pair_credit

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import weather_policy
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
EXECUTION = ROOT / "configs/source_calendar_fixed_model_execution_v1.json"
PLAN = BASE / "source_calendar_fixed_model_plan_v1/20261121T165748Z_848be12d/readback.json"
PLAN_SHA = "9bdbbee2d4398fd2ae95e0ec1b27fdd286f589133d52a50b2b89873abe01271f"
REVIEW = BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896"
PROPOSALS = BASE / "satellite_PU_L_proposals_v1/20261120T005519Z_62f3f815"
VARIANTS = ("full_27_features", "weather_only", "static_cover_terrain_only")
INDICATOR = "existing_scenario_proposal_context"


def validate_execution(execution):
    join.require(
        execution["decision_source"]
        == "user_authorizes_autonomous_progress_after_specific_fixed_model_diagnostic_proposal"
        and execution["plan_readback_sha256"] == PLAN_SHA
        and execution["fixed_model_scoring_authorized"] is True
        and execution["new_auxiliary_source_indicator_codes_authorized"] is True,
        "Specific diagnostic follows the user's autonomous continuation instruction",
    )
    join.require(
        all(
            execution[k] is False
            for k in (
                "indicator_is_verified_fire_Y",
                "model_refitting_authorized",
                "new_hyperparameter_or_scenario_selection_authorized",
                "original_U_or_weights_changed",
                "new_Y_or_accepted_L_assignment_authorized",
                "negative_label_permitted",
                "fire_probabilities_or_validated_risk_colors_authorized",
                "scientific_values_2023_2024_2025_read_permitted",
                "final_merge_permitted",
            )
        )
        and execution["daily_observation_status"] == "unknown",
        "Auxiliary scoring cannot open training, true labels, risk colors or final merge",
    )


def held_calendar(features, qa, roles):
    join.require(
        features.columns.tolist() == join.KEYS + join.feature_names(),
        "X allowlist excludes metadata",
    )
    join.require(
        roles.target.isna().all() and roles.accepted_L_membership.isna().all(),
        "No true Y or accepted L",
    )
    join.require(
        roles.daily_observation_status.eq("unknown").all()
        and roles.role_is_model_training_permission.eq(False).all(),
        "Calendar X roles are not training permission",
    )
    for table in (features, qa, roles):
        join.require(not table.duplicated(join.KEYS).any(), "Unique calendar keys")
    held = (
        roles.loc[roles.review_temporal_role.eq("proposed_assessment_2022")]
        .sort_values(join.KEYS)
        .reset_index(drop=True)
    )
    for stamp in held.prediction_timestamp_utc:
        t = datetime.fromisoformat(stamp)
        join.require(
            t.year == 2022
            and t.utcoffset() == UTC.utcoffset(t)
            and t.time().replace(tzinfo=None) == datetime.min.time()
            and stamp[:10] != "2022-12-31",
            "2022 midnight diagnostic rows only",
        )
    keys = list(held[join.KEYS].itertuples(index=False, name=None))
    x = features.set_index(join.KEYS).loc[keys].reset_index()
    q = qa.set_index(join.KEYS).loc[keys].reset_index()
    return x, q, held


def comparisons(frame, score_column):
    source = frame.loc[frame[INDICATOR]]
    other = frame.loc[~frame[INDICATOR]]
    require = join.require
    require(len(source) and len(other), "Both observed source-context groups")
    same = (source.grid_id.to_numpy()[:, None] == other.grid_id.to_numpy()[None, :]) & (
        source.prediction_timestamp_utc.str[:7].to_numpy()[:, None]
        == other.prediction_timestamp_utc.str[:7].to_numpy()[None, :]
    )
    quality = {
        "all": np.ones(same.shape, dtype=bool),
        "complete_weather_both": source.weather_complete.to_numpy()[:, None]
        & other.weather_complete.to_numpy()[None, :],
        "complete_27_features_both": source.complete_27_features.to_numpy()[:, None]
        & other.complete_27_features.to_numpy()[None, :],
    }
    rows = []
    for scheme, spatial in (
        ("all_pairs", np.ones(same.shape, dtype=bool)),
        ("within_grid_year_month", same),
    ):
        for profile, eligible in quality.items():
            result = pair_credit(source[score_column], other[score_column], spatial & eligible)
            rows.append(
                {
                    "scheme": scheme,
                    "quality_profile": profile,
                    "source_context_keys": len(source),
                    "other_calendar_keys": len(other),
                    **result,
                }
            )
    return rows


def run():
    execution = json.loads(EXECUTION.read_bytes())
    validate_execution(execution)
    join.require(digest(PLAN) == PLAN_SHA, "Exact reviewed diagnostic plan")
    plan = json.loads(PLAN.read_bytes())
    pins = {PLAN: PLAN_SHA, EXECUTION: digest(EXECUTION), Path(__file__): digest(Path(__file__))}
    pins.update({ROOT / p: h for p, h in plan["input_sha256"].items()})
    for name in (
        "feature_join",
        "feature_partition",
        "core_transfer",
        "target_admission",
        "weather_policy",
    ):
        p = ROOT / f"src/wildfire_risk_prediction/{name}.py"
        pins[p] = digest(p)
    helper = ROOT / "scripts/quality/audit_satellite_pu_ranking_run.py"
    pins[helper] = digest(helper)
    join.require(
        all(digest(p) == h for p, h in pins.items()),
        "Current X, metadata, proposals and model files",
    )
    review = json.loads((REVIEW / "readback.json").read_bytes())
    snapshot = REVIEW / review["snapshot_directory"]
    features, qa, roles = [
        parse_csv((snapshot / n).read_bytes())
        for n in ("features.csv", "provenance.csv", "review_roles.csv")
    ]
    x, q, held = held_calendar(features, qa, roles)
    join.require(len(x) == 6573, "Exact approved calendar key count")
    groups = parse_csv((PROPOSALS / "all_first_cells_with_proposal_flags.csv").read_bytes())
    groups = groups.loc[groups.possible_L_proposal]
    out = (
        BASE
        / "source_calendar_fixed_model_run_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    print(out.relative_to(ROOT).as_posix(), flush=True)
    artifacts, metrics, states = {}, [], []
    for scenario, counts in sorted(plan["scenario_counts"].items()):
        source_keys = set(
            groups.loc[groups.scenario.eq(scenario), join.KEYS].itertuples(index=False, name=None)
        )
        frame = x[join.KEYS].copy()
        frame[INDICATOR] = [
            k in source_keys for k in frame[join.KEYS].itertuples(index=False, name=None)
        ]
        join.require(
            int(frame[INDICATOR].sum()) == counts["existing_scenario_proposal_context_keys"],
            "Same source proposals; unknown days not fire negatives",
        )
        frame["weather_complete"] = x[weather_policy.MODEL_FEATURES].notna().all(axis=1)
        frame["complete_27_features"] = x[join.feature_names()].notna().all(axis=1)
        frame["true_Y"] = float("nan")
        frame["accepted_L_membership"] = float("nan")
        frame["daily_observation_status"] = "unknown"
        for spec in [m for m in plan["fixed_models"] if m["scenario"] == scenario]:
            path = ROOT / spec["path"]
            join.require(digest(path) == spec["sha256"], "Trusted local fitted model identity")
            saved = joblib.load(path)
            model, retained = saved["model"], saved["retained_features"]
            join.require(
                set(retained) <= set(join.feature_names())
                and model.named_steps["model"].n_jobs == 1,
                "Frozen whitelisted ordered RF inference",
            )
            before = joblib.hash(model)
            score = model.predict_proba(x[retained])[:, 1]
            join.require(
                joblib.hash(model) == before
                and np.isfinite(score).all()
                and ((score >= 0) & (score <= 1)).all(),
                "Fixed model state and finite auxiliary scores",
            )
            column = spec["variant"] + "_auxiliary_source_score"
            frame[column] = score
            states.append(
                {
                    "scenario": scenario,
                    "variant": spec["variant"],
                    "model_path": spec["path"],
                    "model_sha256": spec["sha256"],
                    "state_hash_before_and_after": before,
                }
            )
            metrics.extend(
                {"scenario": scenario, "variant": spec["variant"], **row}
                for row in comparisons(frame, column)
            )
            if spec["variant"] == "static_cover_terrain_only":
                join.require(
                    frame.groupby("grid_id")[column].nunique().eq(1).all(),
                    "Static RF invariant across days in the same grid",
                )
        path = out / (scenario + "_calendar_scores.csv")
        frame.to_csv(path, index=False)
        pd.testing.assert_frame_equal(frame, parse_csv(path.read_bytes()), check_exact=True)
        artifacts[path.name] = digest(path)
        print(scenario, "6573 fixed-model scores complete; Y/L unknown", flush=True)
    join.require(
        len(states) == 27 and len(metrics) == 162, "All fixed models and declared comparisons"
    )
    p = out / "comparison_summary.csv"
    pd.DataFrame(metrics).to_csv(p, index=False)
    artifacts[p.name] = digest(p)
    join.require(
        all(digest(p) == h for p, h in pins.items()),
        "Consumed fitted models and input snapshots unchanged",
    )
    report = {
        "status": "fixed_RF_calendar_diagnostic_complete_not_fire_validation",
        "decision": execution,
        "rows_per_scenario": 6573,
        "scenarios": 9,
        "fixed_models_scored": 27,
        "new_models_fitted": 0,
        "model_state_checks": states,
        "metrics": metrics,
        "true_Y_or_accepted_L_created": 0,
        "auxiliary_source_indicator_codes_created_for_diagnostic_only": True,
        "source_conditioned_sample_is_population_or_blind_test": False,
        "fire_probabilities_or_validated_risk_colors_created": False,
        "original_U_or_weights_changed": False,
        "final_merge_performed": False,
        "gate": specification(),
        "producer_sha256": digest(Path(__file__)),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": artifacts,
    }
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        run()
    else:
        try:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--worker"],
                cwd=ROOT,
                timeout=15 * 60,
                check=False,
            )
            raise SystemExit(result.returncode)
        except subprocess.TimeoutExpired:
            print(
                "Local 15-minute limit reached; partial diagnostic retained, no acceptance.",
                flush=True,
            )
            raise SystemExit(124) from None
