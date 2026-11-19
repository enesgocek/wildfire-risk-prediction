"""Explicitly authorized source-membership models; Y remains unknown throughout."""

import json
import platform
import warnings
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from uuid import uuid4

import joblib
import matplotlib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import landscape, weather_policy
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.target_admission import specification

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
EXECUTION = ROOT / "configs/conditional_pu_ranking_execution_v1.json"
PROPOSAL = ROOT / "configs/conditional_pu_ranking_pilot_v1.json"
PARTITION = BASE / "conditional_rank_partition_v1/20261119T210609Z_511e5d9f/readback.json"
PARTITION_SHA = "c2ffa568ec7138c734b71a70d5091ba1ca1de46c38e67d58dd90fcd00eb1a391"
REVIEW = BASE / "source_pu_feature_review_v1/20261119T210151Z_3e99d4a1/readback.json"
REVIEW_SHA = "ccc9086c505e22028a670ab9451e2323f429cd8048b83b4c2361519ec2916405"
NAMES = ("logistic_regression", "random_forest", "missingness_control")


def validate_execution(execution, proposal):
    join.require(
        execution["decision_source"]
        == "explicit_user_selection_A_run_limited_conditional_ranking_pilot"
        and execution["auxiliary_model_fitting_authorized"] is True,
        "Explicit auxiliary fitting decision required",
    )
    join.require(
        execution["partition_readback_sha256"] == PARTITION_SHA
        and execution["feature_review_sha256"] == REVIEW_SHA,
        "Decision bound to reviewed inputs",
    )
    join.require(
        execution["authorized_models"] == list(NAMES) and execution["Y_remains_null"] is True,
        "Only named S models; no Y labels",
    )
    closed = (
        "S_codes_are_true_fire_labels",
        "hyperparameter_search_authorized",
        "main_fire_model_training_authorized",
        "new_L_memberships_permitted",
        "positive_label_permitted",
        "negative_label_permitted",
        "main_research_method_accepted",
        "fire_risk_probabilities_permitted",
        "true_fire_AP_or_AUC_permitted",
        "model_ready",
        "final_merge_permitted",
        "2023_calibration_values_read_permitted",
        "2024_comparison_values_read_permitted",
        "2025_final_values_read_permitted",
    )
    join.require(
        all(execution[k] is False for k in closed)
        and execution["daily_observation_status"] == "unknown",
        "Closed main-research gates",
    )
    join.require(
        proposal["seed"] == 20261120 and proposal["hyperparameter_search"] is False,
        "Fixed proposal, no tuning",
    )


def family_missing_flags(frame):
    families = {
        "weather": weather_policy.MODEL_FEATURES,
        "cover": landscape.COVER_FEATURES,
        "terrain": landscape.TERRAIN_FEATURES,
        **{
            f"vegetation{w}": [f"vegetation_{w}d_{f}" for f in join.VEGETATION_FEATURES]
            for w in (30, 60)
        },
    }
    return pd.DataFrame(
        {k: frame[v].isna().any(axis=1).astype(float) for k, v in families.items()},
        index=frame.index,
    )


def fit_auxiliary(name, train, membership, proposal):
    join.require(
        name in NAMES and set(np.unique(membership)) == {0, 1},
        "Named auxiliary model and both S groups",
    )
    join.require(
        train.columns.tolist() == join.feature_names(),
        "Exact feature allowlist; no target/metadata",
    )
    if name == "missingness_control":
        x = family_missing_flags(train)
        pipe = Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        **proposal["proposed_models"]["logistic_regression"],
                        random_state=proposal["seed"],
                    ),
                ),
            ]
        )
        retained = list(x.columns)
    else:
        retained = [k for k in train if train[k].notna().any()]
        join.require(retained, "Observed fit features")
        x = train[retained]
        steps = [
            (
                "impute",
                SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=False),
            )
        ]
        if name == "logistic_regression":
            steps += [
                ("scale", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        **proposal["proposed_models"][name], random_state=proposal["seed"]
                    ),
                ),
            ]
        else:
            steps += [
                (
                    "model",
                    RandomForestClassifier(
                        **proposal["proposed_models"][name], random_state=proposal["seed"]
                    ),
                )
            ]
        pipe = Pipeline(steps)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        pipe.fit(x, membership)
    if name == "random_forest":
        # Parallel probability accumulation can vary at the last bit; keep inference ordered.
        pipe.named_steps["model"].set_params(n_jobs=1)
    return pipe, retained


def model_input(name, frame, retained):
    return family_missing_flags(frame) if name == "missingness_control" else frame[retained]


def render(out, y, predictions, metrics):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    labels = {
        "logistic_regression": "Lojistik",
        "random_forest": "Random Forest",
        "missingness_control": "Yalnız eksiklik kontrolü",
    }
    for name in NAMES:
        x, z, _ = roc_curve(y, predictions[name])
        axes[0].plot(
            x,
            z,
            label=f"{labels[name]}: {metrics[name]['assessment_source_membership_ROC_AUC']:.3f}",
        )
    axes[0].plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1)
    axes[0].set(
        xlabel="U grubunda yüksek kaynak skoru payı",
        ylabel="Kaynak grubunda yüksek skor payı",
        title="Yardımcı kaynak üyeliği ROC • 2022",
    )
    axes[0].legend(fontsize=9)
    for code, label in ((0, "U: 87 anahtar"), (1, "Kaynak: 81 anahtar")):
        axes[1].hist(
            predictions["random_forest"][y == code],
            bins=np.linspace(0, 1, 11),
            alpha=0.6,
            label=label,
        )
    axes[1].set(
        xlabel="Random Forest kaynak üyeliği skoru",
        ylabel="Anahtar sayısı",
        title="Bu skor yangın olasılığı değildir",
    )
    axes[1].legend(fontsize=9)
    fig.suptitle(
        "Sınırlı yöntem pilotu • Gerçek yangın başarımı veya bağımsız test değil", fontsize=12
    )
    fig.text(
        0.5,
        0.015,
        "S=1: kaynak merkezi hipotezi; S=0: belirsiz U örneği. Gerçek yangın hedefi Y boş.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(out / "source_membership_diagnostic.png", dpi=130, facecolor="white")
    plt.close(fig)


def main():
    started = monotonic()
    execution, proposal = [json.loads(p.read_bytes()) for p in (EXECUTION, PROPOSAL)]
    validate_execution(execution, proposal)
    join.require(digest(PROPOSAL) == execution["proposal_sha256"], "Exact approved proposal")
    pins = {
        EXECUTION: digest(EXECUTION),
        PROPOSAL: execution["proposal_sha256"],
        PARTITION: PARTITION_SHA,
        REVIEW: REVIEW_SHA,
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "Pinned decision and snapshots")
    partition, review = [json.loads(p.read_bytes()) for p in (PARTITION, REVIEW)]
    for name in ("features.csv", "inspection.csv"):
        pins[REVIEW.parent / name] = review["artifact_sha256"][name]
    join.require(all(digest(p) == h for p, h in pins.items()), "Consumed feature snapshots")
    features = pd.read_csv(REVIEW.parent / "features.csv", float_precision="round_trip")
    inspection = pd.read_csv(REVIEW.parent / "inspection.csv", float_precision="round_trip")
    join.require(
        features.columns.tolist() == join.KEYS + join.feature_names()
        and inspection.target.isna().all()
        and inspection.daily_observation_status.eq("unknown").all(),
        "Whitelisted X; all Y remain unknown",
    )
    index = features.set_index(join.KEYS)
    tables = {}
    for phase, n in (("proposed_fit_2018_2021", 708), ("proposed_assessment_2022", 168)):
        rows = [r for r in partition["proposed_key_partitions"] if r["proposed_partition"] == phase]
        keys = [(r["grid_id"], r["prediction_timestamp_utc"]) for r in rows]
        join.require(
            len(keys) == len(set(keys)) == n and all(r["target"] is None for r in rows),
            "Fixed reviewed keys and unknown Y",
        )
        tables[phase] = (
            index.loc[keys].reset_index(),
            np.array([int(r["review_population"] == "source_center_hypothesis") for r in rows]),
        )
    train, s_train = tables["proposed_fit_2018_2021"]
    assessment, s_assessment = tables["proposed_assessment_2022"]
    join.require(
        pd.to_datetime(train.prediction_timestamp_utc, utc=True).dt.year.between(2018, 2021).all()
        and pd.to_datetime(assessment.prediction_timestamp_utc, utc=True).dt.year.eq(2022).all(),
        "Explicit auxiliary temporal roles",
    )
    join.require(
        s_train.sum() == 292 and s_assessment.sum() == 81,
        "Known source membership counts, not fire counts",
    )
    x_train, x_assessment = train[join.feature_names()], assessment[join.feature_names()]
    out = (
        BASE
        / "conditional_pu_ranking_run_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    metrics, predictions, snapshots, artifacts = {}, {}, {}, {}
    for name in NAMES:
        model, retained = fit_auxiliary(name, x_train, s_train, proposal)
        before = joblib.hash(model)
        train_score = model.predict_proba(model_input(name, x_train, retained))[:, 1]
        score = model.predict_proba(model_input(name, x_assessment, retained))[:, 1]
        join.require(
            joblib.hash(model) == before
            and np.isfinite(score).all()
            and ((score >= 0) & (score <= 1)).all(),
            "Assessment cannot update fitted state",
        )
        model_path = out / f"{name}.joblib"
        joblib.dump(
            {"model": model, "retained_features": retained, "purpose": "auxiliary_S_not_fire_Y"},
            model_path,
        )
        saved = joblib.load(model_path)
        np.testing.assert_array_equal(
            saved["model"].predict_proba(model_input(name, x_assessment, retained))[:, 1], score
        )
        artifacts[model_path.name] = digest(model_path)
        metrics[name] = {
            "fit_source_membership_ROC_AUC": float(roc_auc_score(s_train, train_score)),
            "assessment_source_membership_ROC_AUC": float(roc_auc_score(s_assessment, score)),
        }
        snapshots[name] = {"retained_features": retained, "fitted_state_joblib_hash": before}
        if "impute" in model.named_steps:
            imp = model.named_steps["impute"]
            snapshots[name].update(
                {
                    "fit_medians": dict(zip(retained, imp.statistics_.tolist(), strict=True)),
                    "missing_indicator_fit_indices": imp.indicator_.features_.tolist(),
                    "transformed_feature_names": imp.get_feature_names_out(retained).tolist(),
                }
            )
        if "scale" in model.named_steps:
            snapshots[name]["fit_scaler_means"] = model.named_steps["scale"].mean_.tolist()
            snapshots[name]["fit_scaler_scales"] = model.named_steps["scale"].scale_.tolist()
        predictions[name] = score
        print(name, json.dumps(metrics[name]), flush=True)
    values = assessment[join.KEYS].copy()
    values["S_observed_source_membership"] = s_assessment
    for name, scores in predictions.items():
        values[name + "_source_membership_score"] = scores
    values["Y_true_fire_target"] = pd.NA
    values["daily_observation_status"] = "unknown"
    values.to_csv(out / "assessment_source_scores.csv", index=False)
    saved = pd.read_csv(out / "assessment_source_scores.csv", float_precision="round_trip")
    join.require(
        saved.Y_true_fire_target.isna().all() and len(saved) == 168,
        "Prediction output has no true fire labels",
    )
    for name in NAMES:
        np.testing.assert_array_equal(saved[name + "_source_membership_score"], predictions[name])
    render(out, s_assessment, predictions, metrics)
    for name in ("assessment_source_scores.csv", "source_membership_diagnostic.png"):
        artifacts[name] = digest(out / name)
    report = {
        "status": "authorized_auxiliary_source_membership_pilot_complete_not_fire_model_acceptance",
        "decision": execution,
        "fit_keys": 708,
        "assessment_keys": 168,
        "boundary_review_keys_preserved": 1,
        "source_membership_S_counts": {
            "fit": {"source": 292, "U": 416},
            "assessment": {"source": 81, "U": 87},
        },
        "metrics": metrics,
        "fit_preprocessing_snapshots": snapshots,
        "true_fire_Y_labels_created": 0,
        "auxiliary_S_codes_created": 876,
        "new_L_memberships": 0,
        "model_trained": True,
        "model_kind": "auxiliary_source_membership_only",
        "main_fire_model_trained": False,
        "alpha_or_beta_estimated": False,
        "true_fire_AP_or_AUC_computed": False,
        "fire_risk_probabilities_created": False,
        "common_class_conditionals_verified": False,
        "source_target_alignment_accepted": False,
        "main_research_method_accepted": False,
        "final_merge_performed": False,
        "gate": specification(),
        "artifact_sha256": artifacts,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "environment": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "random_forest_fit_workers": proposal["proposed_models"]["random_forest"]["n_jobs"],
            "random_forest_prediction_workers": 1,
        },
        "elapsed_seconds": round(monotonic() - started, 3),
    }
    join.require(
        all(digest(p) == h for p, h in pins.items()), "Consumed inputs unchanged after fitting"
    )
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    join.require(json.loads(path.read_bytes()) == report, "Run report roundtrip")
    print(out.relative_to(ROOT).as_posix())
    print("PASS auxiliary_S_only; Y unknown, main fire model and final merge closed")
    print("readback_sha256", digest(path))


if __name__ == "__main__":
    main()
