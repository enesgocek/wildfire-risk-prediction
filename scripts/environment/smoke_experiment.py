"""Record an infrastructure-only run; never load fire data or train a model."""

import hashlib
import json
import os
import platform
import random
import subprocess
from pathlib import Path

import mlflow
from dotenv import load_dotenv
from mlflow import MlflowClient

from wildfire_risk_prediction.config import load_config

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    config_path = ROOT / "configs" / "project.yaml"
    config = load_config(config_path)
    seed = config["experiment"]["seed"]
    random.seed(seed)
    tracking_dir = ROOT / "outputs" / "mlflow"
    tracking_dir.mkdir(parents=True, exist_ok=True)
    tracking_uri = (
        os.getenv("MLFLOW_TRACKING_URI") or f"sqlite:///{tracking_dir.as_posix()}/mlflow.db"
    )
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    experiment_name = config["experiment"]["name"]
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = client.create_experiment(
            experiment_name, artifact_location=(tracking_dir / "artifacts").as_uri()
        )
    else:
        experiment_id = experiment.experiment_id
    git_result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    git_revision = git_result.stdout.strip() if git_result.returncode == 0 else "uncommitted"
    lock_path = ROOT / "uv.lock"
    if not lock_path.is_file():
        raise RuntimeError("uv.lock is missing; run uv sync before the smoke experiment.")
    with mlflow.start_run(experiment_id=experiment_id, run_name="week01-smoke") as run:
        mlflow.set_tags({"run_type": "infrastructure_only", "git_revision": git_revision})
        mlflow.log_params(
            {
                "seed": seed,
                "provinces": ", ".join(config["project"]["provinces"]),
                "horizon_hours": config["prediction"]["horizon_hours"],
                "grid_size_m": config["prediction"]["grid_size_m"],
                "dataset_version": "synthetic-smoke-v1",
                "python_version": platform.python_version(),
                "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                "lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
            }
        )
        # An artificial fixture is provenance for this infrastructure test, not a fire dataset.
        fixture = {"kind": "synthetic_infrastructure_fixture", "value": random.random()}
        mlflow.log_dict(fixture, "synthetic_fixture.json")
        mlflow.log_dict(config, "resolved_config.json")
        mlflow.log_artifact(str(config_path), artifact_path="configuration")
        mlflow.log_artifact(str(lock_path), artifact_path="environment")
        mlflow.log_metric("infrastructure_check_passed", 1.0)
        run_id = run.info.run_id
    stored_run = client.get_run(run_id)
    if stored_run.info.status != "FINISHED":
        raise RuntimeError("Smoke run did not finish successfully.")
    report = {
        "run_id": run_id,
        "experiment": experiment_name,
        "status": stored_run.info.status,
        "tracking_uri": tracking_uri,
        "dataset_version": "synthetic-smoke-v1",
        "model_trained": False,
    }
    report_dir = ROOT / "outputs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "smoke_experiment.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Infrastructure check passed. MLflow run ID: {run_id}")


if __name__ == "__main__":
    main()
