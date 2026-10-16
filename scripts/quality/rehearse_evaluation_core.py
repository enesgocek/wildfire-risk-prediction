"""Synthetic evaluation rehearsal and rejection of unknown real targets; no fitting."""

import importlib.metadata
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn import metrics as reference

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.evaluation_alerts import daily_alerts
from wildfire_risk_prediction.evaluation_folds import audit_training_fold, forward_year_skeleton
from wildfire_risk_prediction.evaluation_metrics import (
    binary_metrics,
    calibration_bins,
    compare_training_predictions,
)
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
PARENT = Path("outputs/reports/dataset/observation_protocol_evidence_v1/20261015T143126Z_dc01eb0c")
PARENT_SHA = "c87a96944635f650a9eb30005d959a56d998cd73154b3b48441a80e0e1a59df2"


def run():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline evaluation core rehearsal")

    socket.socket.connect = deny
    socket.create_connection = deny
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained evaluation input",
        )
        sha = digest(path)
        require(expected is None or expected == sha, "Evaluation input unchanged")
        pins[path.relative_to(ROOT).as_posix()] = sha
        return path

    def read(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    spec = read("configs/evaluation_core_v1.json")
    require(
        spec["primary_metric"] == "average_precision"
        and spec["primary_metric_decision"] == "explicit_user_choice_2026-10-16"
        and spec["labels_accepted"] is False
        and spec["model_ready"] is False,
        "Selected AP arithmetic with closed training gates",
    )
    require(
        all(
            spec[k] is None
            for k in (
                "embargo_hours",
                "spatial_block_definition",
                "daily_alert_capacity",
                "daily_alert_tie_policy",
                "calibration_bin_count",
                "event_first_cell_policy",
                "confidence_interval_protocol",
            )
        ),
        "Unselected scientific/operational policies remain open",
    )
    for name in (
        Path(__file__).relative_to(ROOT),
        "src/wildfire_risk_prediction/evaluation_metrics.py",
        "src/wildfire_risk_prediction/evaluation_folds.py",
        "src/wildfire_risk_prediction/evaluation_alerts.py",
        "tests/test_evaluation_core.py",
        "configs/project.yaml",
        "uv.lock",
        "src/wildfire_risk_prediction/core_transfer.py",
        "src/wildfire_risk_prediction/cmr_identity.py",
        "src/wildfire_risk_prediction/feature_join.py",
        "src/wildfire_risk_prediction/landscape.py",
        "src/wildfire_risk_prediction/weather_policy.py",
        "src/wildfire_risk_prediction/vegetation.py",
    ):
        retained(name)
    parent = read(PARENT / "readback.json", PARENT_SHA)
    closing = read(PARENT / "completion_readback.json")
    require(
        closing["report_sha256"] == PARENT_SHA and parent["labels_created"] is False,
        "Retained unlabelled real pilot report",
    )
    units = pd.read_csv(
        retained(
            PARENT / "unit_protocol_evidence.csv",
            parent["artifact_sha256"]["unit_protocol_evidence.csv"],
        )
    )
    require(
        len(units) == 156
        and units.target.isna().all()
        and units.daily_observation_status.eq("unknown").all()
        and not units.negative_label_permitted.any(),
        "Real pilot remains unadmitted",
    )
    real_guard = False
    try:
        binary_metrics(units.target.to_numpy(), np.full(len(units), 0.5))
    except ValueError:
        real_guard = True
    require(real_guard, "Unknown real targets cannot be scored")

    rng = np.random.default_rng(20261016)
    cases = [
        (np.array([0, 0, 1, 1]), np.array([0.1, 0.4, 0.35, 0.8])),
        (np.array([0, 1, 0, 1]), np.full(4, 0.5)),
        (np.array([0, 1]), np.array([0.0, 1.0])),
        (np.zeros(4), np.array([0.0, 0.2, 0.8, 1.0])),
        (np.ones(4), np.array([0.0, 0.2, 0.8, 1.0])),
    ]
    for i in range(50):
        size = int(rng.integers(3, 128))
        y, p = rng.integers(0, 2, size=size), rng.uniform(size=size)
        if i % 2:
            p = np.round(p, 1)
        cases.append((y, p))
    differences = {
        k: 0.0
        for k in ("average_precision", "pr_auc_trapezoid", "roc_auc", "brier_binary", "log_loss")
    }
    for y, p in cases:
        result = binary_metrics(y, p)
        expected = {
            "brier_binary": reference.brier_score_loss(y, p, pos_label=1, scale_by_half=True),
            "log_loss": reference.log_loss(y, p, labels=[0, 1]),
        }
        if len(np.unique(y)) == 2:
            precision, recall, _ = reference.precision_recall_curve(y, p, drop_intermediate=False)
            expected.update(
                average_precision=reference.average_precision_score(y, p),
                pr_auc_trapezoid=reference.auc(recall, precision),
                roc_auc=reference.roc_auc_score(y, p),
            )
        for metric, value in expected.items():
            differences[metric] = max(differences[metric], abs(result[metric] - value))
            require(abs(result[metric] - value) <= 1e-12, "Independent metric implementation check")
    example = binary_metrics(*cases[0])
    bins = calibration_bins(*cases[0], bin_count=4)
    require(bins["count"].sum() == len(cases[0][0]), "Synthetic calibration sample conservation")

    def metadata(day, event, block):
        return pd.DataFrame(
            {
                "grid_id": ["synthetic_grid"],
                "prediction_timestamp_utc": [day + "T00:00:00Z"],
                "event_ids": [[event]],
                "event_membership_complete": [True],
                "spatial_block": [block],
            }
        )

    train = metadata("2021-01-01", "synthetic_event_a", "west")
    held = metadata("2022-01-01", "synthetic_event_b", "east")
    fold = audit_training_fold(train, held, embargo_hours=24, spatial_column="spatial_block")
    shared_rejected = holdout_rejected = False
    for change in ("shared_event", "holdout"):
        bad = (
            metadata("2022-01-01", "synthetic_event_a", "east")
            if change == "shared_event"
            else metadata("2025-01-01", "synthetic_event_b", "east")
        )
        try:
            audit_training_fold(train, bad, embargo_hours=24)
        except ValueError:
            if change == "shared_event":
                shared_rejected = True
            else:
                holdout_rejected = True
    require(shared_rejected and holdout_rejected, "Event/final-test protection rehearsal")
    _, alerts = daily_alerts(
        pd.DataFrame(
            {
                "grid_id": ["b", "a", "c"],
                "prediction_timestamp_utc": ["2021-07-01T00:00:00Z"] * 3,
                "probability": [0.9, 0.9, 0.2],
                "target": [None, 0.0, 1.0],
            }
        ),
        capacity=2,
        tie_policy="grid_id_ascending",
    )
    require(
        alerts.selected_unadjudicated_cells.item() == 1
        and alerts.selected_verified_negative_cells.item() == 1,
        "Unknown alert is not false",
    )
    paired_fixture = pd.DataFrame(
        {
            "grid_id": ["a", "b", "c"],
            "prediction_timestamp_utc": ["2021-07-01T00:00:00Z"] * 3,
            "probability": [0.1, 0.7, 0.5],
            "target": [0, 1, 0],
        }
    )
    paired = compare_training_predictions(paired_fixture, paired_fixture.iloc[::-1])
    require(
        all(value == 0 for value in paired["right_minus_left"].values()),
        "Same keyed predictions are invariant to row order",
    )

    out = (
        ROOT
        / "outputs/reports/dataset/evaluation_core_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)

    def save(name, value):
        (out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    save(
        "synthetic_example_metrics.json",
        {"scope": "synthetic_contract_fixture_only", "metrics": example},
    )
    save(
        "metric_crosscheck.json",
        {
            "synthetic_cases": len(cases),
            "tolerance": 1e-12,
            "maximum_absolute_differences": differences,
            "reference_implementation": "scikit-learn",
            "version": importlib.metadata.version("scikit-learn"),
        },
    )
    save("training_year_skeleton.json", forward_year_skeleton())
    save("paired_rehearsal.json", {"scope": "synthetic_keyed_predictions_only", **paired})
    save(
        "fold_rehearsal.json",
        {
            "scope": "synthetic_metadata_only",
            "passing_example": fold,
            "shared_event_rejected": shared_rejected,
            "final_year_rejected": holdout_rejected,
        },
    )
    save(
        "current_label_guard.json",
        {
            "real_unassigned_targets": len(units),
            "scoring_rejected": real_guard,
            "real_scores_produced": 0,
            "real_predictions_produced": 0,
        },
    )
    alerts.to_csv(out / "synthetic_alert_counts.csv", index=False)
    bins.to_csv(out / "synthetic_calibration_bins.csv", index=False)
    require(
        all(digest(ROOT / name) == sha for name, sha in pins.items()), "Final evaluation closure"
    )
    save("input_manifest.json", pins)
    save(
        "readback.json",
        {
            "status": "evaluation_core_rehearsed_no_model_training",
            "primary_metric": spec["primary_metric"],
            "synthetic_crosscheck_cases": len(cases),
            "real_unknown_targets_rejected": len(units),
            "training_year_skeletons": 5,
            "input_file_count": len(pins),
            "network_bytes": 0,
            "cloud_jobs_started": 0,
            "classifiers_fitted": 0,
            "calibrators_fitted": 0,
            "real_labels_created": False,
            "labels_accepted": False,
            "model_ready": False,
            "final_merge_performed": False,
            "validation_or_final_data_accessed": False,
            "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
        },
    )
    save(
        "completion_readback.json",
        {
            "status": "passed_core_rehearsal_not_scientific_acceptance",
            "report_sha256": digest(out / "readback.json"),
        },
    )
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
