"""Summarize audited fixed rankers and record exact metrics in workspace-only MLflow."""

import argparse
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    run, audit = args.run.resolve(), args.audit.resolve()
    require(
        run.parent == (BASE / "nonlinear_rank_run_v1").resolve()
        and audit.parent == (BASE / "nonlinear_rank_audit_v1").resolve(),
        "Workspace outputs only",
    )
    rr, ar = [json.loads((f / "readback.json").read_bytes()) for f in (run, audit)]
    require(
        ar["run_directory"] == run.relative_to(ROOT).as_posix()
        and ar["status"] == "nine_saved_rankers_pairs_scores_and_metrics_independently_confirmed",
        "Completed independent audit for this run",
    )
    pins = {ROOT / p: h for p, h in ar["input_sha256"].items()}
    pins[audit / "readback.json"] = digest(audit / "readback.json")
    require(all(digest(p) == h for p, h in pins.items()), "Audited files still unchanged")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "nonlinear_rank_closure_v1" / stamp
    out.mkdir(parents=True)
    metrics = pd.read_csv(run / "metrics.csv", float_precision="round_trip")
    wide = metrics.pivot(
        index=["scenario", "cohort", "slice", "pairs"],
        columns="variant",
        values="auxiliary_pair_AUC",
    ).reset_index()
    wide["difference_XGBoost_minus_frozen_linear"] = wide.XGBoost - wide.frozen_linear
    wide.to_csv(out / "comparisons.csv", index=False)
    summary = wide.loc[
        wide["slice"].isin(
            [
                "all_same_grid_month",
                "gap_1_to_3_days",
                "gap_4_to_30_days",
                "other_day_before_source_day",
                "other_day_after_source_day",
            ]
        )
    ].copy()
    summary.to_csv(out / "temporal_summary.csv", index=False)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=True)
    for row, cohort in enumerate(("four_province", "separate_Mersin")):
        for col, part in enumerate(("all_same_grid_month", "gap_1_to_3_days")):
            ax = axes[row, col]
            t = summary.loc[summary.cohort.eq(cohort) & summary["slice"].eq(part)].sort_values(
                "scenario"
            )
            for model, color, marker in (
                ("XGBoost", "#0067a5", "o"),
                ("frozen_linear", "#bd6913", "s"),
            ):
                ax.plot(
                    t.scenario, t[model], marker=marker, color=color, label=model, linewidth=1.5
                )
            ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8)
            ax.set_title(cohort + " | " + part)
            ax.set_ylabel("Auxiliary source-order pair AUC")
            ax.set_ylim(0.4, 0.72)
            ax.tick_params(axis="x", labelrotation=65)
            ax.grid(axis="y", alpha=0.2)
    axes[0, 0].legend(loc="upper left")
    fig.suptitle(
        "Fixed dynamic ranking comparison — explored 2022\n"
        "Source-conditioned calendars; not verified fire performance",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out / "fixed_rank_comparison.png", dpi=160)
    plt.close(fig)
    tracking = ROOT / "outputs/mlflow"
    database = tracking / "mlflow.db"
    require(database.is_file(), "Existing local tracking database")
    backup = tracking / ("before-nonlinear-rank-" + stamp + ".db")
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as source:
        with sqlite3.connect(backup) as destination:
            source.backup(destination)
    client = MlflowClient(tracking_uri="sqlite:///" + database.as_posix())
    name = "fixed-nonlinear-dynamic-source-ranking"
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
        "Strictly workspace local artifact target",
    )
    run_id = client.create_run(
        experiment_id,
        tags={
            "mlflow.runName": "nine-fixed-XGBoost-source-rankers-2018to2021-two2022-calendars",
            "scope": "auxiliary_source_ordering_not_true_fire_performance",
            "run_readback_sha256": digest(run / "readback.json"),
            "audit_readback_sha256": digest(audit / "readback.json"),
        },
    ).info.run_id
    selected = metrics.loc[
        ~metrics["slice"].str.startswith("cell_") & metrics.auxiliary_pair_AUC.notna()
    ]
    values = {
        f"{r.scenario}_{r.cohort}_{r.variant}_{r.slice}": r.auxiliary_pair_AUC
        for r in selected.itertuples(index=False)
    }
    require(len(values) == len(selected), "Unique summary metric identities")
    try:
        for key, value in {
            "new_models_in_scientific_run": 9,
            "new_models_in_closure": 0,
            "fit_years": "2018-2021",
            "explored_assessment_year": 2022,
            "dynamic_features": 15,
            "hyperparameter_search": False,
            "source_membership_is_true_fire_label": False,
            "probability_or_validated_risk_colors": False,
            "production_scenario_selected": "none",
            "final_merge": False,
            "xgboost_version": rr["environment"]["xgboost"],
        }.items():
            client.log_param(run_id, key, value)
        entries = [
            Metric(k, v, int(datetime.now(UTC).timestamp() * 1000), 0) for k, v in values.items()
        ]
        client.log_batch(run_id, metrics=entries)
        client.log_artifacts(run_id, str(run), artifact_path="scientific_run")
        client.log_artifacts(run_id, str(audit), artifact_path="independent_audit")
        client.log_artifacts(run_id, str(out), artifact_path="summary")
        client.set_terminated(run_id, "FINISHED")
    except Exception:
        client.set_terminated(run_id, "FAILED")
        raise
    restored = client.get_run(run_id)
    require(
        restored.info.status == "FINISHED" and restored.data.metrics == values,
        "Exact local MLflow metric readback",
    )
    require(
        all(digest(p) == h for p, h in pins.items()), "Original files preserved through closure"
    )
    report = {
        "status": "audited_fixed_nonlinear_ranking_recorded_and_closed",
        "run_directory": run.relative_to(ROOT).as_posix(),
        "audit_directory": audit.relative_to(ROOT).as_posix(),
        "mlflow_run_id": run_id,
        "exact_local_metric_readback": len(values),
        "database_backup": backup.relative_to(ROOT).as_posix(),
        "backup_sha256": digest(backup),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
        "new_models_in_closure": 0,
        "true_fire_validation": False,
        "production_scenario_selected": None,
        "final_merge_performed": False,
    }
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print("local MLflow", run_id, "exact metrics", len(values), flush=True)


if __name__ == "__main__":
    main()
