"""Close audited support exports, weather-QA checks and quality-aligned ranking locally."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib
import pandas as pd
from mlflow import MlflowClient
from mlflow.entities import Metric

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"
AUDIT = BASE / "primary_weather_rank_audit_v1/20261123T143500Z_2b454296"
EXPORT_AUDIT = BASE / "evaluation_review_audit_v1/20261123T142016Z_d7e03899"
QA_AUDIT = BASE / "weather_score_support_audit_v1/20261123T143011Z_0df65000"


def main():
    pins = {
        RUN / "readback.json": "004f7d27d6b0f1825b2b00d7a2825b311e2483b5f2d73c7063cadd9b45b2946d",
        AUDIT / "readback.json": "9aef378d9d3ecf90a515717dd6a1e70a1259fc960374c4026b16239252f2e468",
        EXPORT_AUDIT
        / "readback.json": "a380b44c870f999924a66cc4adfe9a07fbc4d01ab83eb2b76d3970e8c1a0f5b3",
        QA_AUDIT
        / "readback.json": "792ea4e55ddf0a1ea53fe21eb6992797c4b25a7a5929e243becb9bccf9d6926b",
    }
    require(all(digest(p) == h for p, h in pins.items()), "Exact independent audits")
    for folder in (AUDIT, EXPORT_AUDIT, QA_AUDIT):
        r = json.loads((folder / "readback.json").read_bytes())
        pins.update({ROOT / p: h for p, h in r["input_sha256"].items()})
    require(all(digest(p) == h for p, h in pins.items()), "All audited inputs still unchanged")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "dataset_support_review_closure_v1" / stamp
    out.mkdir(parents=True)
    metrics = pd.read_csv(RUN / "metrics.csv", float_precision="round_trip")
    comparison = metrics.pivot(
        index=["cohort", "scenario", "slice", "pairs"],
        columns="variant",
        values="auxiliary_pair_AUC",
    ).reset_index()
    comparison["primary_minus_broad_XGBoost"] = (
        comparison.primary_weather_XGBoost - comparison.broad_weather_XGBoost
    )
    comparison["primary_minus_frozen_linear"] = (
        comparison.primary_weather_XGBoost - comparison.frozen_linear
    )
    comparison.to_csv(out / "quality_aligned_comparison.csv", index=False)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=True)
    styles = (
        ("primary_weather_XGBoost", "Full-area fit XGBoost", "#0067a5", "o"),
        ("broad_weather_XGBoost", "Prior broad fit XGBoost", "#bd6913", "s"),
        ("frozen_linear", "Prior linear", "#6a6a6a", "^"),
    )
    for row, cohort in enumerate(("four_province", "separate_Mersin")):
        for col, part in enumerate(("all_same_grid_month", "gap_1_to_3_days")):
            ax = axes[row, col]
            frame = comparison.loc[
                comparison.cohort.eq(cohort) & comparison["slice"].eq(part)
            ].sort_values("scenario")
            for key, label, color, marker in styles:
                ax.plot(
                    frame.scenario,
                    frame[key],
                    label=label,
                    color=color,
                    marker=marker,
                    linewidth=1.3,
                )
            ax.set_title(cohort + " | " + part)
            ax.set_ylim(0.4, 0.72)
            ax.set_ylabel("Auxiliary source-order pair AUC")
            ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8)
            ax.tick_params(axis="x", labelrotation=65)
            ax.grid(axis="y", alpha=0.2)
    axes[0, 0].legend(loc="upper left", fontsize=8)
    fig.suptitle(
        "Weather QA alignment — identical full-area 2022 assessment pairs\n"
        "Exploratory source ordering, not verified fire prediction",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out / "weather_quality_aligned_comparison.png", dpi=160)
    plt.close(fig)
    database = ROOT / "outputs/mlflow/mlflow.db"
    tracking = database.parent
    backup = tracking / ("before-dataset-support-review-" + stamp + ".db")
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as source:
        with sqlite3.connect(backup) as destination:
            source.backup(destination)
    client = MlflowClient(tracking_uri="sqlite:///" + database.as_posix())
    name = "primary-weather-fixed-source-ranking"
    experiment = client.get_experiment_by_name(name)
    experiment_id = (
        experiment.experiment_id
        if experiment
        else client.create_experiment(
            name, artifact_location=(tracking / "artifacts" / name).as_uri()
        )
    )
    require(
        client.get_experiment(experiment_id).artifact_location.startswith(tracking.as_uri()),
        "Workspace-local experiment only",
    )
    run_id = client.create_run(
        experiment_id,
        tags={
            "mlflow.runName": "existing-primary-weather-rule-nine-fixed-rankers",
            "scope": "quality_alignment_not_true_fire_validation",
            "scientific_run_sha256": digest(RUN / "readback.json"),
            "audit_sha256": digest(AUDIT / "readback.json"),
        },
    ).info.run_id
    values = {
        f"{r.cohort}_{r.scenario}_{r.variant}_{r.slice}": r.auxiliary_pair_AUC
        for r in metrics.itertuples(index=False)
    }
    try:
        for key, value in {
            "new_models_in_scientific_run": 9,
            "new_models_in_closure": 0,
            "weather_profile": "preexisting_primary_full_area",
            "fit_years": "2018-2021",
            "exploratory_year": 2022,
            "hyperparameter_search": False,
            "new_quality_threshold": False,
            "source_score_is_verified_fire_risk": False,
            "final_merge": False,
        }.items():
            client.log_param(run_id, key, value)
        client.log_batch(
            run_id,
            metrics=[
                Metric(k, v, int(datetime.now(UTC).timestamp() * 1000), 0)
                for k, v in values.items()
            ],
        )
        client.log_artifacts(run_id, str(RUN), artifact_path="quality_aligned_run")
        client.log_artifacts(run_id, str(AUDIT), artifact_path="independent_run_audit")
        client.log_artifacts(run_id, str(out), artifact_path="comparison_summary")
        client.set_terminated(run_id, "FINISHED")
    except Exception:
        client.set_terminated(run_id, "FAILED")
        raise
    restored = client.get_run(run_id)
    require(
        restored.info.status == "FINISHED" and restored.data.metrics == values,
        "Exact 270 local metric readback",
    )
    require(
        all(digest(p) == h for p, h in pins.items()), "Immutable earlier artifacts after closure"
    )
    body = {
        "status": "audited_review_exports_weather_QA_and_primary_rankers_closed",
        "mlflow_run_id": run_id,
        "exact_local_metric_readback": len(values),
        "database_backup": backup.relative_to(ROOT).as_posix(),
        "backup_sha256": digest(backup),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
        "new_models_in_closure": 0,
        "new_Y_or_accepted_L": 0,
        "fire_risk_validated": False,
        "final_merge_performed": False,
    }
    path = out / "readback.json"
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)
    print("local MLflow", run_id, "exact metrics", len(values), flush=True)


if __name__ == "__main__":
    main()
