"""Prepare controlled feature-group ablations; further fitting needs a new plan-bound decision."""

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
from run_conditional_pu_ranking_pilot import fit_auxiliary
from run_satellite_pu_ranking_pilot import load_preparation, scenario_tables

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import landscape, weather_policy
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv
from wildfire_risk_prediction.ranking_metrics import binary_rank_metrics

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
POLICY = ROOT / "configs/satellite_pu_ablation_pilot_v1.json"
PARENT_PLAN = BASE / "satellite_PU_ranking_plan_v1/20261120T012319Z_6b617502/readback.json"
PARENT_RUN = BASE / "satellite_PU_ranking_run_v1/20261120T012805Z_04789b23/readback.json"
PARENT_AUDIT = BASE / "satellite_PU_ranking_audit_v1/20261120T013224Z_b8a45358/readback.json"
VARIANTS = {
    "weather_only": weather_policy.MODEL_FEATURES,
    "static_cover_terrain_only": landscape.COVER_FEATURES + landscape.TERRAIN_FEATURES,
}
CLOSED = (
    "new_Y_or_accepted_L_permitted",
    "main_fire_model_training_authorized",
    "fire_probability_or_validated_risk_color_permitted",
    "scientific_values_2023_2024_2025_read_permitted",
    "negative_label_permitted",
    "final_merge_permitted",
)


def masked_features(frame, variant):
    join.require(
        variant in VARIANTS and frame.columns.tolist() == join.feature_names(),
        "Whitelisted ablation of X only",
    )
    result = frame.copy()
    for name in result:
        if name not in VARIANTS[variant]:
            result[name] = np.nan
    return result


def validate_decision(execution, path):
    join.require(
        execution.get("decision_source")
        == "explicit_user_selection_A_run_18_static_weather_auxiliary_ablations"
        and execution.get("new_auxiliary_fitting_authorized") is True
        and execution.get("plan_readback_sha256") == digest(path)
        and execution.get("maximum_new_fits") == 18
        and execution.get("Y_remains_null") is True
        and all(execution.get(k) is False for k in CLOSED),
        "New explicit 18-fit decision required; earlier 27-fit permission is insufficient",
    )


def prepared_inputs():
    policy = json.loads(POLICY.read_bytes())
    join.require(
        policy["variants"] == list(VARIANTS)
        and policy["maximum_new_fits"] == 18
        and policy["new_auxiliary_fitting_authorized"] is False
        and all(policy[k] is False for k in CLOSED)
        and policy["hyperparameter_search_permitted"] is False
        and policy["scenario_selection_permitted"] is False,
        "Preparation preserves scope and scientific gates",
    )
    pins = {POLICY: digest(POLICY), Path(__file__): digest(Path(__file__))}
    for path, field in (
        (PARENT_PLAN, "parent_plan_readback_sha256"),
        (PARENT_RUN, "parent_run_readback_sha256"),
        (PARENT_AUDIT, "parent_audit_readback_sha256"),
    ):
        join.require(digest(path) == policy[field], "Exact approved parent experiment and audit")
        pins[path] = policy[field]
    parent_plan = json.loads(PARENT_PLAN.read_bytes())
    original_policy, bound, _, features, roles = load_preparation()
    join.require(
        parent_plan["input_sha256"]
        == {p.relative_to(ROOT).as_posix(): h for p, h in bound.items()},
        "Parent experiment inputs unchanged",
    )
    pins.update(bound)
    parent_run = json.loads(PARENT_RUN.read_bytes())
    for metric in parent_run["metrics"]:
        if metric["model"] == "random_forest":
            relative = metric["scenario"] + "/random_forest_assessment.csv"
            p = PARENT_RUN.parent / relative
            pins[p] = parent_run["artifact_sha256"][relative]
    join.require(all(digest(p) == h for p, h in pins.items()), "Frozen full RF scores, code and X")
    return policy, original_policy, parent_plan, features, roles, pins


def folder(kind):
    out = BASE / kind / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    out.mkdir(parents=True)
    return out


def prepare():
    policy, _, parent, features, roles, pins = prepared_inputs()
    for row in parent["comparisons"]:
        tables = scenario_tables(roles, features, row["scenario"])
        for phase, (x, s) in tables.items():
            join.require(
                len(x) == row[phase]["keys"] and int(s.sum()) == row[phase]["possible_proposal_S"],
                "Identical role populations",
            )
    report = {
        "status": "18_auxiliary_ablation_fits_proposed_not_executed",
        "decision": policy,
        "comparisons": parent["comparisons"],
        "feature_groups": VARIANTS,
        "new_models_fitted_now": 0,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
    }
    out = folder("satellite_PU_ablation_plan_v1")
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print("PREPARED ONLY; no additional fitting or label acceptance", flush=True)


def run(plan_path, execution_path):
    plan = json.loads(plan_path.read_bytes())
    execution = json.loads(execution_path.read_bytes())
    validate_decision(execution, plan_path)
    _, model_policy, _, features, roles, pins = prepared_inputs()
    join.require(
        plan["input_sha256"] == {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "Reviewed ablation plan unchanged",
    )
    pins.update({plan_path: digest(plan_path), execution_path: digest(execution_path)})
    out = folder("satellite_PU_ablation_run_v1")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    metrics, artifacts = [], {}
    for row in plan["comparisons"]:
        scenario = row["scenario"]
        tables = scenario_tables(roles, features, scenario)
        train, s_fit = tables["proposed_fit_2018_2021"]
        held, s_held = tables["proposed_assessment_2022"]
        parent = parse_csv(
            (PARENT_RUN.parent / scenario / "random_forest_assessment.csv").read_bytes()
        )
        pd.testing.assert_frame_equal(parent[join.KEYS], held[join.KEYS], check_exact=True)
        np.testing.assert_array_equal(parent.observed_proposal_S, s_held)
        for variant in VARIANTS:
            x = masked_features(train[join.feature_names()], variant)
            h = masked_features(held[join.feature_names()], variant)
            model, retained = fit_auxiliary("random_forest", x, s_fit, model_policy)
            join.require(
                set(retained) <= set(VARIANTS[variant]), "No out-of-group feature survived"
            )
            state = joblib.hash(model)
            score = model.predict_proba(h[retained])[:, 1]
            join.require(joblib.hash(model) == state, "No assessment refit")
            location = out / scenario
            location.mkdir(exist_ok=True)
            model_path = location / (variant + ".joblib")
            joblib.dump(
                {
                    "model": model,
                    "retained_features": retained,
                    "meaning": "auxiliary_S_not_fire_Y",
                },
                model_path,
            )
            saved = joblib.load(model_path)
            np.testing.assert_array_equal(saved["model"].predict_proba(h[retained])[:, 1], score)
            scores = held[join.KEYS].copy()
            scores["observed_proposal_S"] = s_held
            scores["auxiliary_source_score_not_fire_probability"] = score
            scores["true_Y"] = float("nan")
            scores["daily_observation_status"] = "unknown"
            path = location / (variant + "_assessment.csv")
            scores.to_csv(path, index=False)
            pd.testing.assert_frame_equal(
                scores, parse_csv(path.read_bytes()), check_dtype=False, check_exact=True
            )
            for p in (path, model_path):
                artifacts[p.relative_to(out).as_posix()] = digest(p)
            result = binary_rank_metrics(s_held, score, target_meaning="observed_source_S")
            metrics.append(
                {
                    "scenario": scenario,
                    "variant": variant,
                    "auxiliary_S_ROC_AUC": result["roc_auc"],
                    "retained_features": retained,
                }
            )
            print(scenario, variant, "auxiliary_ablation_complete", flush=True)
    join.require(
        len(metrics) == 18 and all(digest(p) == h for p, h in pins.items()),
        "All fixed ablations; original inputs unchanged",
    )
    report = {
        "status": "18_authorized_auxiliary_ablations_complete_not_fire_validation",
        "decision": execution,
        "metrics": metrics,
        "models_fitted": 18,
        "new_Y_or_accepted_L_created": 0,
        "main_fire_model_trained": False,
        "causal_feature_effect_or_fire_skill_established": False,
        "final_merge_performed": False,
        "artifact_sha256": artifacts,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
    }
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--execution", type=Path)
    args = parser.parse_args()
    if not args.run:
        join.require(
            not args.worker and args.plan is None and args.execution is None,
            "Default is preparation only",
        )
        prepare()
    else:
        join.require(
            args.plan is not None and args.execution is not None,
            "New explicit execution receipt required",
        )
        if args.worker:
            run(args.plan.resolve(), args.execution.resolve())
        else:
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--run",
                        "--worker",
                        "--plan",
                        str(args.plan.resolve()),
                        "--execution",
                        str(args.execution.resolve()),
                    ],
                    cwd=ROOT,
                    timeout=15 * 60,
                    check=False,
                )
                raise SystemExit(result.returncode)
            except subprocess.TimeoutExpired:
                print(
                    "Local 15-minute limit reached; partial checkpoints retained, no acceptance.",
                    flush=True,
                )
                raise SystemExit(124) from None


if __name__ == "__main__":
    main()
