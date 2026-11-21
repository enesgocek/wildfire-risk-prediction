"""Record the fixed 18 ablations in local MLflow, with a prior database backup."""

import json
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from mlflow import MlflowClient

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "outputs/reports/dataset/satellite_PU_ablation_run_v1/20261120T014426Z_44c25642"
AUDIT = ROOT / "outputs/reports/dataset/satellite_PU_ablation_audit_v1/20261120T014740Z_3cdb2359"
RUN_SHA = "fa9321e6268ffba478c6250d6cc32b0d5516ce3b872b9a8271920edb9d1d3324"
AUDIT_SHA = "783d2678aa895aafcf3a388e634ac12fe567fb0e40a3affcdbeae7c450fd45c0"


def main():
    receipt = RUN / "mlflow_record.json"
    require(not receipt.exists(), "Never replace experiment receipts")
    require(
        digest(RUN / "readback.json") == RUN_SHA and digest(AUDIT / "readback.json") == AUDIT_SHA,
        "Frozen experiment and audit",
    )
    report, audit = [json.loads((p / "readback.json").read_bytes()) for p in (RUN, AUDIT)]
    for folder, body in ((RUN, report), (AUDIT, audit)):
        require(
            all(digest(folder / p) == h for p, h in body["artifact_sha256"].items()),
            "Current local artifacts",
        )
    tracking = ROOT / "outputs/mlflow"
    tracking.mkdir(exist_ok=True)
    database = tracking / "mlflow.db"
    backup = None
    if database.exists():
        backup = tracking / (
            "before-satellite-ablation-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".db"
        )
        require(not backup.exists(), "Unique database backup")
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as source:
            with sqlite3.connect(backup) as destination:
                source.backup(destination)
    client = MlflowClient(tracking_uri=f"sqlite:///{database.as_posix()}")
    name = "satellite-source-ranking-pilot"
    experiment = client.get_experiment_by_name(name)
    experiment_id = (
        experiment.experiment_id
        if experiment
        else client.create_experiment(
            name, artifact_location=(tracking / "artifacts/satellite-source-ranking-pilot").as_uri()
        )
    )
    require(
        client.get_experiment(experiment_id).artifact_location.startswith(tracking.as_uri()),
        "Local artifact storage only",
    )
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    run = client.create_run(
        experiment_id,
        tags={
            "mlflow.runName": "18-fixed-weather-and-static-auxiliary-ablations",
            "run_type": "auxiliary_S_feature_ablations_not_fire_Y",
            "git_revision": revision,
            "readback_sha256": RUN_SHA,
            "fire_model_registry_entry_created": "false",
        },
    )
    run_id = run.info.run_id
    try:
        for k, value in {
            "seed": 20261120,
            "fit_years": "2018-2021",
            "assessment_year": 2022,
            "models_fitted": 18,
            "fit_U": 1648,
            "assessment_U": 400,
            "scenario_selected": "none",
            "true_Y_or_accepted_L_created": 0,
            "target_semantics": "observed_proposal_S_not_true_fire_Y",
            "run_readback_sha256": RUN_SHA,
            "audit_readback_sha256": AUDIT_SHA,
        }.items():
            client.log_param(run_id, k, value)
        for row in report["metrics"]:
            client.log_metric(
                run_id,
                row["scenario"] + "_" + row["variant"] + "_auxiliary_S_AUC",
                row["auxiliary_S_ROC_AUC"],
            )
        for folder, names, area in (
            (RUN, ("readback.json",), "run"),
            (
                AUDIT,
                ("readback.json", "fixed_score_comparisons.csv", "feature_group_comparison.png"),
                "audit",
            ),
        ):
            for artifact in names:
                client.log_artifact(run_id, str(folder / artifact), artifact_path=area)
        client.log_artifact(
            run_id,
            str(ROOT / "configs/satellite_pu_ablation_execution_v1.json"),
            artifact_path="decision",
        )
        client.set_terminated(run_id, status="FINISHED")
    except Exception:
        client.set_terminated(run_id, status="FAILED")
        raise
    restored = client.get_run(run_id)
    require(
        restored.info.status == "FINISHED" and len(restored.data.metrics) == 18,
        "All 18 metrics read back",
    )
    result = {
        "readback_sha256": RUN_SHA,
        "audit_sha256": AUDIT_SHA,
        "tracking_scope": "workspace_local_SQLite_and_local_artifacts_only",
        "experiment_name": name,
        "experiment_id": experiment_id,
        "run_id": run_id,
        "run_status": restored.info.status,
        "metrics_read_back": 18,
        "prior_database_backup": backup.relative_to(ROOT).as_posix() if backup else None,
        "backup_sha256": digest(backup) if backup else None,
        "main_fire_model_or_model_registry_entry_created": False,
        "producer_sha256": digest(Path(__file__)),
    }
    receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PASS local MLflow receipt and 18 metrics; no new fitting or external tracking")
    print("receipt_sha256", digest(receipt))


if __name__ == "__main__":
    main()
