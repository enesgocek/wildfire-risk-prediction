"""Prepare a bounded nine-scenario experiment; fitting requires a separate explicit decision."""

import argparse
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd
import sklearn
from run_conditional_pu_ranking_pilot import NAMES, fit_auxiliary, model_input
from verify_satellite_pu_pilot_inputs import REPORTS

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv
from wildfire_risk_prediction.ranking_metrics import binary_rank_metrics
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
POLICY = ROOT / "configs/satellite_pu_ranking_pilot_v1.json"
CLOSED = (
    "main_fire_model_training_authorized",
    "accepted_L_or_Y_created",
    "negative_label_permitted",
    "fire_probabilities_or_validated_risk_colors_permitted",
    "true_fire_AP_or_AUC_permitted",
    "final_merge_permitted",
    "scientific_values_2023_2024_2025_read_permitted",
)


def validate_proposal(policy):
    join.require(
        policy["models"] == list(NAMES)
        and policy["maximum_fits"] == 27
        and policy["all_nine_scenarios_required"] is True
        and policy["scenario_selected"] is None,
        "Fixed nine-scenario, three-model comparison",
    )
    join.require(
        all(policy[k] is False for k in CLOSED)
        and policy["auxiliary_model_fitting_authorized"] is False
        and policy["hyperparameter_search"] is False
        and policy["scenario_selection_by_best_auxiliary_score_permitted"] is False
        and policy["daily_observation_status"] == "unknown",
        "Preparation does not grant scientific acceptance or fitting",
    )
    join.require(
        policy["proposed_models"]
        == {
            "logistic_regression": {"C": 1.0, "max_iter": 1000, "class_weight": None},
            "random_forest": {
                "n_estimators": 100,
                "max_depth": 6,
                "min_samples_leaf": 5,
                "n_jobs": 2,
                "class_weight": None,
            },
        }
        and policy["seed"] == 20261120
        and policy["maximum_wall_minutes"] == 15,
        "Fixed previous auxiliary model sizes and bounded local budget",
    )


def validate_execution(execution, plan_path, plan):
    join.require(
        execution.get("decision_source")
        == "explicit_user_selection_A_run_four_province_satellite_auxiliary_pilot"
        and execution.get("auxiliary_model_fitting_authorized") is True
        and execution.get("plan_readback_sha256") == digest(plan_path),
        "New explicit fitting decision bound to this concrete plan required",
    )
    join.require(
        all(execution.get(k) is False for k in CLOSED)
        and execution.get("authorized_models") == list(NAMES)
        and execution.get("maximum_fits") == plan["maximum_fits"] == 27
        and execution.get("Y_remains_null") is True,
        "Only auxiliary S comparison; real Y and main gates remain closed",
    )


def scenario_tables(roles, features, scenario):
    join.require(
        roles.target.isna().all() and roles.accepted_L_membership.isna().all(),
        "Unknown Y and accepted L",
    )
    join.require(
        not (roles.original_U_sample_present & roles.possible_L_proposal_present).any(),
        "Overlapping acquisition roles require a new protocol; never silently drop U",
    )
    join.require(
        features.columns.tolist() == join.KEYS + join.feature_names(),
        "X allowlist excludes time, location, satellite and post-T QA metadata",
    )
    source = roles.proposed_scenarios_json.map(lambda x: scenario in json.loads(x))
    tables = {}
    index = features.set_index(join.KEYS)
    for phase in ("proposed_fit_2018_2021", "proposed_assessment_2022"):
        selected = roles.loc[
            roles.proposed_partition.eq(phase) & (roles.original_U_sample_present | source)
        ].copy()
        keys = list(selected[join.KEYS].itertuples(index=False, name=None))
        join.require(len(keys) == len(set(keys)), "One physical feature key per scenario")
        membership = source.loc[selected.index].to_numpy(dtype=np.int8)
        join.require(set(np.unique(membership)) == {0, 1}, "Both observed acquisition groups")
        tables[phase] = (index.loc[keys].reset_index(), membership)
    return tables


def load_preparation():
    policy = json.loads(POLICY.read_bytes())
    validate_proposal(policy)
    pins, reports, folders = (
        {POLICY: digest(POLICY), Path(__file__): digest(Path(__file__))},
        {},
        {},
    )
    for name, (relative, sha) in REPORTS.items():
        folder = folders[name] = BASE / relative
        p = folder / "readback.json"
        pins[p] = sha
        join.require(digest(p) == sha, "Frozen preparation receipt")
        reports[name] = json.loads(p.read_bytes())
        check = folder / "separate_readback.json"
        separate = json.loads(check.read_bytes())
        join.require(separate["parent_readback_sha256"] == sha, "Separate readback binding")
        pins[check] = digest(check)
        for artifact, expected in reports[name]["artifact_sha256"].items():
            pins[folder / artifact] = expected
    # The reusable model helper is pinned without changing its earlier scientific run.
    helper = ROOT / "scripts/quality/run_conditional_pu_ranking_pilot.py"
    pins[helper] = digest(helper)
    for module in (
        "feature_join",
        "feature_partition",
        "landscape",
        "weather_policy",
        "ranking_metrics",
        "target_admission",
        "core_transfer",
    ):
        p = ROOT / f"src/wildfire_risk_prediction/{module}.py"
        pins[p] = digest(p)
    join.require(all(digest(p) == h for p, h in pins.items()), "Exact consumed snapshots/code")
    for field, name in (
        ("feature_review_sha256", "features"),
        ("partition_readback_sha256", "partition"),
        ("possible_L_proposals_sha256", "proposals"),
    ):
        join.require(policy[field] == REPORTS[name][1], "Proposal input identities")
    features = parse_csv((folders["features"] / "features.csv").read_bytes())
    roles = parse_csv((folders["partition"] / "proposed_key_roles.csv").read_bytes())
    join.require(len(features) == len(roles) == 3718, "Exact prepared universe")
    return policy, pins, reports, features, roles


def fresh_folder(kind):
    out = BASE / kind / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    out.mkdir(parents=True)
    return out


def prepare():
    policy, pins, reports, features, roles = load_preparation()
    comparisons = []
    for summary in reports["partition"]["scenario_summaries"]:
        scenario = summary["scenario"]
        tables = scenario_tables(roles, features, scenario)
        counts = {"scenario": scenario}
        for phase, (x, s) in tables.items():
            counts[phase] = {
                "keys": len(x),
                "possible_proposal_S": int(s.sum()),
                "U": int((s == 0).sum()),
            }
            join.require(
                counts[phase]["U"] == summary[phase]["U"]
                and counts[phase]["possible_proposal_S"] == summary[phase]["possible_L_keys"],
                "Concrete experiment agrees with frozen temporal partition",
            )
        comparisons.append(counts)
    join.require(len(comparisons) == 9, "All scenarios retained")
    plan = {
        "status": "concrete_27_auxiliary_fits_prepared_waiting_for_new_explicit_decision",
        "decision": policy,
        "maximum_fits": 27,
        "comparisons": comparisons,
        "auxiliary_S_created_now": False,
        "preprocessing_fitted_now": False,
        "models_fitted_now": 0,
        "real_Y_or_accepted_L_created": 0,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "gate": specification(),
    }
    out = fresh_folder("satellite_PU_ranking_plan_v1")
    path = out / "readback.json"
    path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    print("plan_readback_sha256", digest(path), flush=True)
    print("PREPARED ONLY; no fitting, labels, scientific acceptance or final merge", flush=True)


def run(plan_path, execution_path):
    # This check precedes even loading the scientific feature snapshots.
    plan = json.loads(plan_path.read_bytes())
    execution = json.loads(execution_path.read_bytes())
    validate_execution(execution, plan_path, plan)
    policy, pins, _, features, roles = load_preparation()
    join.require(
        plan["input_sha256"] == {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "Reviewed plan still matches all current data and code",
    )
    pins.update({plan_path: digest(plan_path), execution_path: digest(execution_path)})
    out, started = fresh_folder("satellite_PU_ranking_run_v1"), monotonic()
    print(out.relative_to(ROOT).as_posix(), flush=True)
    metrics, artifacts = [], {}
    for comparison in plan["comparisons"]:
        tables = scenario_tables(roles, features, comparison["scenario"])
        train, s_train = tables["proposed_fit_2018_2021"]
        assessment, s_test = tables["proposed_assessment_2022"]
        for name in NAMES:
            join.require(
                monotonic() - started < 60 * policy["maximum_wall_minutes"],
                "Wall budget reached; keep partial checkpoints",
            )
            model, retained = fit_auxiliary(name, train[join.feature_names()], s_train, policy)
            state = joblib.hash(model)
            score = model.predict_proba(
                model_input(name, assessment[join.feature_names()], retained)
            )[:, 1]
            join.require(
                joblib.hash(model) == state and np.isfinite(score).all(),
                "No assessment fit or invalid scores",
            )
            folder = out / comparison["scenario"]
            folder.mkdir(exist_ok=True)
            saved_model = folder / f"{name}.joblib"
            joblib.dump(
                {
                    "model": model,
                    "retained_features": retained,
                    "meaning": "proposal_S_not_true_fire_Y",
                },
                saved_model,
            )
            saved = joblib.load(saved_model)
            np.testing.assert_array_equal(
                saved["model"].predict_proba(
                    model_input(name, assessment[join.feature_names()], retained)
                )[:, 1],
                score,
            )
            predictions = assessment[join.KEYS].copy()
            predictions["observed_proposal_S"] = s_test
            predictions["auxiliary_source_score_not_fire_probability"] = score
            predictions["true_Y"] = float("nan")
            predictions["daily_observation_status"] = "unknown"
            p = folder / f"{name}_assessment.csv"
            predictions.to_csv(p, index=False)
            pd.testing.assert_frame_equal(
                predictions, parse_csv(p.read_bytes()), check_dtype=False, check_exact=True
            )
            rank = binary_rank_metrics(s_test, score, target_meaning="observed_source_S")
            metrics.append(
                {
                    "scenario": comparison["scenario"],
                    "model": name,
                    "assessment_proposal_membership_ROC_AUC": rank["roc_auc"],
                    "retained_features": retained,
                    "fit_model_state_hash": state,
                }
            )
            for path in (p, saved_model):
                artifacts[path.relative_to(out).as_posix()] = digest(path)
            print(comparison["scenario"], name, "auxiliary_S_complete", flush=True)
    join.require(
        len(metrics) == 27 and all(digest(p) == h for p, h in pins.items()),
        "All fixed comparisons and unchanged inputs",
    )
    report = {
        "status": "authorized_auxiliary_satellite_S_comparison_complete_not_fire_model_acceptance",
        "decision": execution,
        "metrics": metrics,
        "models_fitted": 27,
        "true_Y_and_accepted_L_created": 0,
        "true_fire_AP_or_AUC_computed": False,
        "source_target_alignment_verified": False,
        "risk_colors_or_fire_probabilities_created": False,
        "main_fire_model_trained": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": artifacts,
        "gate": specification(),
        "environment": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "elapsed_seconds": round(monotonic() - started, 3),
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
    if args.run:
        join.require(
            args.plan is not None and args.execution is not None,
            "Separate plan and explicit execution decision required",
        )
        if args.worker:
            run(args.plan.resolve(), args.execution.resolve())
        else:
            try:
                child = subprocess.run(
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
                raise SystemExit(child.returncode)
            except subprocess.TimeoutExpired:
                print(
                    "Local 15-minute budget reached; partial checkpoints retained, no acceptance.",
                    flush=True,
                )
                raise SystemExit(124) from None
    else:
        join.require(
            args.plan is None and args.execution is None and not args.worker,
            "Default is preparation only",
        )
        prepare()


if __name__ == "__main__":
    main()
