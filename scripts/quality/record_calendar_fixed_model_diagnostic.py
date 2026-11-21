"""Record reviewed fixed-model calendar scores in local MLflow, with no fitting or registry."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from mlflow import MlflowClient

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "source_calendar_fixed_model_run_v1/20261121T171148Z_91ab9c78"
AUDIT = BASE / "source_calendar_fixed_model_audit_v1/20261121T171907Z_77821dec"
RUN_SHA = "ff51e4790f92eeca51b1db107c38c876a5a2b6ea34d54d4a3451d32754e28f4f"
AUDIT_SHA = "bd451bd1d8e93eeb81f1123004fb2de92aecbfa2c511522fff1486a5fc5f9e6f"


def main():
    receipt = RUN / "mlflow_record.json"
    require(not receipt.exists(), "Never replace local experiment receipts")
    require(
        digest(RUN / "readback.json") == RUN_SHA and digest(AUDIT / "readback.json") == AUDIT_SHA,
        "Reviewed fixed diagnostic",
    )
    report, audit = [json.loads((p / "readback.json").read_bytes()) for p in (RUN, AUDIT)]
    for folder, body in ((RUN, report), (AUDIT, audit)):
        require(
            all(digest(folder / p) == h for p, h in body["artifact_sha256"].items()),
            "Current score and audit artifacts",
        )
    tracking = ROOT / "outputs/mlflow"
    database = tracking / "mlflow.db"
    backup = tracking / (
        "before-calendar-fixed-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".db"
    )
    require(database.is_file() and not backup.exists(), "Existing local database and unique backup")
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as source:
        with sqlite3.connect(backup) as destination:
            source.backup(destination)
    client = MlflowClient(tracking_uri=f"sqlite:///{database.as_posix()}")
    experiment = client.get_experiment_by_name("satellite-source-ranking-pilot")
    require(
        experiment is not None and experiment.artifact_location.startswith(tracking.as_uri()),
        "Existing local experiment and artifacts only",
    )
    run = client.create_run(
        experiment.experiment_id,
        tags={
            "mlflow.runName": "2022-calendar-fixed-27-RF-no-new-fit",
            "run_type": "source_conditioned_calendar_context_diagnostic_not_fire_validation",
            "readback_sha256": RUN_SHA,
            "new_model_fitting": "false",
        },
    )
    run_id = run.info.run_id
    try:
        for key, value in {
            "assessment_year": 2022,
            "rows_per_scenario": 6573,
            "fixed_models_scored": 27,
            "models_fitted": 0,
            "true_Y_or_accepted_L_created": 0,
            "sample_is_population_or_blind_test": False,
            "final_merge_performed": False,
            "run_readback_sha256": RUN_SHA,
            "audit_sha256": AUDIT_SHA,
        }.items():
            client.log_param(run_id, key, value)
        count = 0
        for row in report["metrics"]:
            if row["auxiliary_S_pair_AUC"] is not None:
                key = "_".join(
                    (
                        row["scenario"],
                        row["variant"],
                        row["scheme"],
                        row["quality_profile"],
                        "context_AUC",
                    )
                )
                client.log_metric(run_id, key, row["auxiliary_S_pair_AUC"])
                count += 1
        for folder, names, area in (
            (RUN, ("readback.json", "comparison_summary.csv"), "diagnostic"),
            (
                AUDIT,
                (
                    "readback.json",
                    "province_within_calendar_support.csv",
                    "within_calendar_comparison.png",
                ),
                "audit",
            ),
        ):
            for name in names:
                client.log_artifact(run_id, str(folder / name), artifact_path=area)
        client.log_artifact(
            run_id,
            str(ROOT / "configs/source_calendar_fixed_model_execution_v1.json"),
            artifact_path="decision",
        )
        client.set_terminated(run_id, status="FINISHED")
    except Exception:
        client.set_terminated(run_id, status="FAILED")
        raise
    restored = client.get_run(run_id)
    require(
        restored.info.status == "FINISHED" and len(restored.data.metrics) == count,
        "Recorded diagnostic metrics read back",
    )
    receipt.write_text(
        json.dumps(
            {
                "status": "local_diagnostic_record_verified",
                "run_readback_sha256": RUN_SHA,
                "audit_sha256": AUDIT_SHA,
                "tracking_scope": "workspace_local_SQLite_and_local_artifacts_only",
                "run_id": run_id,
                "metrics_read_back": count,
                "models_fitted": 0,
                "prior_database_backup": backup.relative_to(ROOT).as_posix(),
                "backup_sha256": digest(backup),
                "model_registry_entry_created": False,
                "producer_sha256": digest(Path(__file__)),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "PASS local fixed-model diagnostic record; metrics",
        count,
        "receipt_sha256",
        digest(receipt),
        flush=True,
    )


if __name__ == "__main__":
    main()
