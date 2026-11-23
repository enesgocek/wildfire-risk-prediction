"""Record the audited FWI reference locally, without training or changing original results."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from mlflow import MlflowClient

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "fwi_reference_comparison_run_v1/20261123T101431Z_805e6449"
AUDIT = BASE / "fwi_reference_comparison_audit_v1/20261123T101705Z_98c1ab80"


def main():
    pins = {
        RUN / "readback.json": "5e5a7bd7a920b15d1288c7969b9841c62ac9948af5e74255c901ff6eb5a4d40c",
        AUDIT / "readback.json": "3a52234b5aaf064037dd0404eb0b2c907054d91335339a952690a1f1732c7ae5",
    }
    for p, sha in pins.items():
        require(digest(p) == sha, "Frozen run and audit")
    run, audit = [json.loads((p / "readback.json").read_bytes()) for p in (RUN, AUDIT)]
    for folder, body in ((RUN, run), (AUDIT, audit)):
        require(
            all(digest(folder / name) == sha for name, sha in body["artifact_sha256"].items()),
            "Audited artifacts unchanged",
        )
    tracking = ROOT / "outputs/mlflow"
    database = tracking / "mlflow.db"
    require(database.is_file(), "Existing workspace local tracking only")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    backup = tracking / ("before-fwi-reference-" + stamp + ".db")
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as source:
        with sqlite3.connect(backup) as destination:
            source.backup(destination)
    client = MlflowClient(tracking_uri="sqlite:///" + database.as_posix())
    name = "fwi-retrospective-reference-pilot"
    experiment = client.get_experiment_by_name(name)
    experiment_id = (
        experiment.experiment_id
        if experiment
        else client.create_experiment(
            name,
            artifact_location=(tracking / "artifacts/fwi-retrospective-reference-pilot").as_uri(),
        )
    )
    require(
        client.get_experiment(experiment_id).artifact_location.startswith(tracking.as_uri()),
        "Local artifact target",
    )
    run_id = client.create_run(
        experiment_id,
        tags={
            "mlflow.runName": "June2022-Mersin-FWI-vs-nine-frozen-scores",
            "scope": "auxiliary_source_calendar_not_verified_fire_performance",
            "run_readback_sha256": digest(RUN / "readback.json"),
        },
    ).info.run_id
    values = {
        r["variant"] + "_" + r["slice"] + "_auxiliary_pair_AUC": r["auxiliary_pair_AUC"]
        for r in run["metrics"]
        if r["auxiliary_pair_AUC"] is not None
    }
    try:
        for key, value in {
            "new_models_fitted": 0,
            "source_calendar_keys": 7,
            "calendar_rows": 203,
            "common_pairs": 196,
            "nominal_calendar_lag_days": 1,
            "operational_validity_verified": False,
            "true_fire_validation": False,
            "scenario_selected_for_production": "none",
        }.items():
            client.log_param(run_id, key, value)
        for key, value in values.items():
            client.log_metric(run_id, key, value)
        client.log_artifacts(run_id, str(RUN), artifact_path="reference_comparison")
        client.log_artifacts(run_id, str(AUDIT), artifact_path="independent_readback")
        client.set_terminated(run_id, "FINISHED")
    except Exception:
        client.set_terminated(run_id, "FAILED")
        raise
    restored = client.get_run(run_id)
    require(
        restored.info.status == "FINISHED" and restored.data.metrics == values,
        "Exact 50 local metrics restored",
    )
    out = BASE / "fwi_reference_comparison_closure_v1" / stamp
    out.mkdir(parents=True)
    result = {
        "status": "audited_FWI_reference_recorded_in_local_MLflow",
        "run_id": run_id,
        "metrics_exact_readback": len(values),
        "tracking_scope": "workspace_local_SQLite_and_file_artifacts_only",
        "database_backup": backup.relative_to(ROOT).as_posix(),
        "backup_sha256": digest(backup),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "new_models_or_registry_entries": 0,
        "operational_or_true_fire_validation": False,
        "final_merge_performed": False,
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print("local MLflow run", run_id, "exact metric readback", len(values), flush=True)


if __name__ == "__main__":
    main()
