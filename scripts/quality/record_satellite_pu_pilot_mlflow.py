"""Record completed auxiliary models in local MLflow, without a fire model registry entry."""

import json
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from mlflow import MlflowClient

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "outputs/reports/dataset/satellite_PU_ranking_run_v1/20261120T012805Z_04789b23"
AUDIT = ROOT / "outputs/reports/dataset/satellite_PU_ranking_audit_v1/20261120T013224Z_b8a45358"
RUN_SHA = "971b85def11809d0d48f4a3618233588e6a7022e7ddea5861fb94054cbcb84a1"
AUDIT_SHA = "19f67bcfecf918804a7365ee1c7d7bfc53da3e9956a87004ac275aa29f2f8f47"


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
            "Verified local artifacts",
        )
    tracking = ROOT / "outputs/mlflow"
    tracking.mkdir(exist_ok=True)
    database = tracking / "mlflow.db"
    backup = None
    if database.exists():
        backup = tracking / (
            "before-satellite-pilot-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".db"
        )
        require(not backup.exists(), "Unique database backup")
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as source:
            with sqlite3.connect(backup) as destination:
                source.backup(destination)
    uri = f"sqlite:///{database.as_posix()}"
    # Explicit SQLite and local artifact URI; never consume an external tracking env setting.
    client = MlflowClient(tracking_uri=uri)
    experiment_name = "satellite-source-ranking-pilot"
    experiment = client.get_experiment_by_name(experiment_name)
    experiment_id = (
        experiment.experiment_id
        if experiment
        else client.create_experiment(
            experiment_name,
            artifact_location=(tracking / "artifacts/satellite-source-ranking-pilot").as_uri(),
        )
    )
    stored = client.get_experiment(experiment_id)
    require(stored.artifact_location.startswith(tracking.as_uri()), "Local artifact storage only")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    run = client.create_run(
        experiment_id,
        tags={
            "mlflow.runName": "four-province-fixed-27-auxiliary-models",
            "run_type": "auxiliary_satellite_proposal_S_not_fire_Y",
            "git_revision": revision,
            "scientific_labels_accepted": "false",
            "fire_model_registry_entry_created": "false",
            "readback_sha256": RUN_SHA,
        },
    )
    run_id = run.info.run_id
    try:
        for k, value in {
            "seed": 20261120,
            "fit_years": "2018-2021",
            "assessment_year": 2022,
            "models_fitted": 27,
            "scenario_selected": "none",
            "fit_U": 1648,
            "assessment_U": 400,
            "target_semantics": "observed_proposal_S_not_true_fire_Y",
            "real_Y_or_accepted_L_created": 0,
            "final_merge_performed": False,
            "run_readback_sha256": RUN_SHA,
            "audit_readback_sha256": AUDIT_SHA,
        }.items():
            client.log_param(run_id, k, value)
        for row in report["metrics"]:
            client.log_metric(
                run_id,
                row["scenario"] + "_" + row["model"] + "_auxiliary_S_AUC",
                row["assessment_proposal_membership_ROC_AUC"],
            )
        for folder, names, area in (
            (RUN, ("readback.json",), "run"),
            (
                AUDIT,
                (
                    "readback.json",
                    "comparison_pairs.csv",
                    "province_diagnostics.csv",
                    "same_U_rank_stability.csv",
                    "auxiliary_diagnostics.png",
                ),
                "audit",
            ),
        ):
            for name in names:
                client.log_artifact(run_id, str(folder / name), artifact_path=area)
        client.log_artifact(
            run_id,
            str(ROOT / "configs/satellite_pu_ranking_execution_v1.json"),
            artifact_path="decision",
        )
        client.set_terminated(run_id, status="FINISHED")
    except Exception:
        client.set_terminated(run_id, status="FAILED")
        raise
    restored = client.get_run(run_id)
    require(
        restored.info.status == "FINISHED" and len(restored.data.metrics) == 27,
        "Read back all 27 recorded auxiliary metrics",
    )
    result = {
        "readback_sha256": RUN_SHA,
        "audit_sha256": AUDIT_SHA,
        "tracking_scope": "workspace_local_SQLite_and_local_artifacts_only",
        "experiment_name": experiment_name,
        "experiment_id": experiment_id,
        "run_id": run_id,
        "run_status": restored.info.status,
        "metrics_read_back": 27,
        "prior_database_backup": backup.relative_to(ROOT).as_posix() if backup else None,
        "backup_sha256": digest(backup) if backup else None,
        "main_fire_model_or_model_registry_entry_created": False,
        "producer_sha256": digest(Path(__file__)),
    }
    receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PASS local MLflow record and 27 metrics; no model registry or external tracking")
    print("receipt_sha256", digest(receipt))


if __name__ == "__main__":
    main()
