"""Export the audited comparison and record all 405 values in local MLflow."""

import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "source_disjoint_frozen_assessment_v1/20261124T031245Z_91cd329d"
AUDIT = BASE / "source_disjoint_frozen_assessment_audit_v1/20261124T031414Z_9c5bc04c"


def main():
    os.environ["MLFLOW_ENABLE_TELEMETRY"] = "false"
    from mlflow import MlflowClient
    from mlflow.entities import Metric

    pins = {
        RUN / "readback.json": "7f6e16ff58084954610dea8ca41d9ca87ece9fd02192b076cfec5973845a5d23",
        AUDIT / "readback.json": "caf4f7650b1d8c5842e27a14d387081bb1967aa8b728a10e83c82d012afc2275",
    }
    report = json.loads((RUN / "readback.json").read_bytes())
    pins.update({RUN / name: sha for name, sha in report["artifact_sha256"].items()})
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Audited accepted assessment")
    metrics = pd.read_csv(RUN / "metrics.csv", float_precision="round_trip")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "source_disjoint_assessment_closure_v1" / stamp
    out.mkdir(parents=True)
    summary = metrics.groupby(["source_group", "variant", "slice"], sort=True).agg(
        scenarios=("scenario", "nunique"),
        pairs=("pairs", "first"),
        auxiliary_credit_min=("auxiliary_pair_AUC", "min"),
        auxiliary_credit_median=("auxiliary_pair_AUC", "median"),
        auxiliary_credit_max=("auxiliary_pair_AUC", "max"),
    )
    if not summary.scenarios.eq(9).all():
        raise ValueError("All nine scenarios in every reported group")
    summary.to_csv(out / "scenario_ranges.csv")
    groups = [
        "original_source_calendar",
        "exclude_any_same_key_satellite_proposal",
        "absent_from_four_province_calendar",
    ]
    variants = ["primary_weather_XGBoost", "broad_weather_XGBoost", "frozen_linear"]
    labels = ["Ana tam-alan XGBoost", "Önceki geniş-alan XGBoost", "Dondurulmuş doğrusal"]
    sections = ["all_same_grid_month", "gap_1_to_3_days"]
    colors = ["#24516c", "#a3693a", "#6a7082"]
    figure, axes = plt.subplots(2, 3, figsize=(15, 8), constrained_layout=True)
    points = []
    for row, section in enumerate(sections):
        for col, (variant, label) in enumerate(zip(variants, labels, strict=True)):
            axis = axes[row, col]
            for group, color, name in zip(
                groups,
                colors,
                ("G0: 65 kaynak günü", "G1: 59 kaynak günü", "G2: 56 kaynak günü"),
                strict=True,
            ):
                part = metrics.loc[
                    metrics.source_group.eq(group)
                    & metrics.variant.eq(variant)
                    & metrics["slice"].eq(section)
                ].sort_values("scenario")
                if len(part) != 9 or not part.auxiliary_pair_AUC.between(0.4, 0.65).all():
                    raise ValueError("All plotted values and bounds")
                axis.plot(
                    range(9),
                    part.auxiliary_pair_AUC,
                    color=color,
                    marker="o",
                    markersize=3.5,
                    label=name,
                )
                points.extend(part.to_dict("records"))
            axis.set_xticks(
                range(9),
                [s.replace("d", "").replace("m_t", "/").replace("h", "") for s in part.scenario],
                rotation=65,
                fontsize=8,
            )
            axis.set_ylim(0.4, 0.65)
            axis.axhline(0.5, color="#aaaaaa", linestyle="--", linewidth=0.8)
            axis.grid(axis="y", alpha=0.15)
            axis.set_title(
                label
                + (
                    "\nAynı hücre/ayın tüm çiftleri" if row == 0 else "\nYalnız 1–3 gün uzak günler"
                ),
                fontsize=10,
            )
            axis.set_xlabel("Gruplama ayarı: metre/saat", fontsize=8)
            axis.set_ylabel("Yardımcı kaynak-gün sıra kredisi", fontsize=9)
    axes[0, 0].legend(fontsize=8, loc="lower left")
    figure.suptitle(
        "2022 Mersin: aynı hücre–gün örtüşmesini ayırma\n"
        "G1: ortak S önerileri çıkarıldı; G2: dört-il takviminde anahtarı yok. "
        "İç içe kesitler; gerçek yangın başarımı değildir.",
        fontsize=12,
    )
    figure.savefig(out / "source_overlap_comparison.png", dpi=160)
    plt.close(figure)
    pd.DataFrame(points).to_csv(out / "figure_values.csv", index=False)
    database = ROOT / "outputs/mlflow/mlflow.db"
    tracking = database.parent
    backup = tracking / ("before-source-disjoint-assessment-" + stamp + ".db")
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as source:
        with sqlite3.connect(backup) as destination:
            source.backup(destination)
    client = MlflowClient(tracking_uri="sqlite:///" + database.as_posix())
    name = "frozen-source-overlap-assessment"
    experiment = client.get_experiment_by_name(name)
    experiment_id = (
        experiment.experiment_id
        if experiment
        else client.create_experiment(
            name, artifact_location=(tracking / "artifacts" / name).as_uri()
        )
    )
    if not client.get_experiment(experiment_id).artifact_location.startswith(
        tracking.as_uri() + "/"
    ):
        raise ValueError("Workspace-local artifacts only")
    run_id = client.create_run(
        experiment_id,
        tags={
            "mlflow.runName": "accepted-three-nested-source-subsets",
            "scope": "frozen_2022_source_ordering_not_true_fire_validation",
            "assessment_sha256": digest(RUN / "readback.json"),
            "audit_sha256": digest(AUDIT / "readback.json"),
        },
    ).info.run_id
    values = {
        f"{r.source_group}_{r.scenario}_{r.variant}_{r.slice}": r.auxiliary_pair_AUC
        for r in metrics.itertuples()
    }
    try:
        for k, value in {
            "existing_score_year": 2022,
            "models_fitted": 0,
            "new_predictions": 0,
            "source_groups_are_nested": True,
            "excluded_sources_relabelled": 0,
            "true_Y_or_L_created": 0,
            "fire_validation": False,
            "final_merge": False,
        }.items():
            client.log_param(run_id, k, value)
        client.log_batch(
            run_id,
            metrics=[
                Metric(k, v, int(datetime.now(UTC).timestamp() * 1000), 0)
                for k, v in values.items()
            ],
        )
        for folder, label in (
            (RUN, "assessment"),
            (AUDIT, "independent_audit"),
            (out, "comparison"),
        ):
            client.log_artifacts(run_id, str(folder), artifact_path=label)
        client.set_terminated(run_id, "FINISHED")
    except Exception:
        client.set_terminated(run_id, "FAILED")
        raise
    restored = client.get_run(run_id)
    if restored.info.status != "FINISHED" or restored.data.metrics != values:
        raise ValueError("Exact 405 local MLflow metric readback")
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Earlier artifacts remain unchanged")
    body = {
        "status": "audited_source_overlap_assessment_closed_local_only",
        "mlflow_run_id": run_id,
        "exact_local_metric_readback": len(values),
        "figure_value_rows": len(points),
        "scenario_range_rows": len(summary),
        "database_backup": backup.relative_to(ROOT).as_posix(),
        "backup_sha256": digest(backup),
        "new_training_or_prediction_calls": 0,
        "true_fire_validation": False,
        "final_merge": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(
        out.relative_to(ROOT).as_posix(),
        "local_MLflow",
        run_id,
        "exact_metrics",
        len(values),
        flush=True,
    )


if __name__ == "__main__":
    main()
