"""Offline comparison design and synthetic arithmetic/role checks; no model fits."""

import importlib.metadata
import itertools
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_class_weight

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.evaluation_folds import audit_training_fold
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
PARENT = Path("outputs/reports/dataset/experiment_preparation_v1/20261016T013115Z_9990881e")
PARENT_SHA = "20d367d95f0ea330adacf5d678a72bb0f79c724b0bc4edd0383b114f4535983e"


def metadata(year, role):
    return pd.DataFrame(
        {
            "grid_id": [f"synthetic_{role}"],
            "prediction_timestamp_utc": [f"{year}-07-01T00:00:00Z"],
            "event_ids": [[f"synthetic_event_{role}"]],
            "event_membership_complete": [True],
        }
    )


def audit_roles(fit, calibration, assessment):
    # All three pairings matter: nonadjacent fit/assessment can share an event too.
    for earlier, later in ((fit, calibration), (fit, assessment), (calibration, assessment)):
        audit_training_fold(earlier, later, embargo_hours=0)


def run():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline imbalance/calibration design")

    socket.socket.connect = deny
    socket.create_connection = deny
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained comparison design input",
        )
        sha = digest(path)
        require(expected is None or expected == sha, "Comparison design input unchanged")
        pins[path.relative_to(ROOT).as_posix()] = sha
        return path

    def read(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    parent = read(PARENT / "readback.json", PARENT_SHA)
    require(
        read(PARENT / "completion_readback.json")["report_sha256"] == PARENT_SHA, "Parent closure"
    )
    for name, sha in parent["artifact_sha256"].items():
        retained(PARENT / name, sha)
    for name, sha in read(PARENT / "input_manifest.json").items():
        retained(name, sha)
    require(
        parent["training_authorized"] is False and parent["real_executable_fold_count"] == 0,
        "Preparation evidence only",
    )
    plan = read("configs/imbalance_calibration_plan_v1.json")
    retained(Path(__file__).relative_to(ROOT))
    require(
        plan["data_role_direction"] == "fit_2018_2022_calibration_2023_selection_2024"
        and plan["data_role_direction_source"] == "explicit_user_choice_2026-10-16"
        and plan["calendar_feasibility_verified"] is False,
        "Recorded user direction, not accepted calendar feasibility",
    )
    require(
        plan["primary_metric"] == "average_precision"
        and plan["class_weight_candidates"] == ["none", "balanced_fit_partition_only"]
        and plan["calibration_candidates"] == ["none", "sigmoid", "isotonic_conditional_support"]
        and plan["selected_class_weight"] is None
        and plan["selected_calibration"] is None
        and all(
            plan[key] is False
            for key in (
                "training_authorized",
                "labels_accepted",
                "model_ready",
                "final_merge_performed",
                "resampling_in_initial_comparison",
                "class_balancing_in_calibration_or_assessment",
                "calibration_training_key_overlap_permitted",
                "apply_old_calibrator_to_refitted_model",
                "real_class_counts_available",
            )
        ),
        "Unselected comparison design with closed admission",
    )
    candidates = [
        {
            "class_weight": weight,
            "calibration": calibration,
            "status": "proposed_not_run",
            "requires_additional_support_review": calibration == "isotonic_conditional_support",
            "real_score": None,
        }
        for weight, calibration in itertools.product(
            plan["class_weight_candidates"], plan["calibration_candidates"]
        )
    ]
    weights = []
    for negative, positive in ((1, 1), (9, 1), (90, 10), (99, 1), (10, 90), (37, 13)):
        y = np.array([0] * negative + [1] * positive)
        actual = compute_class_weight("balanced", classes=np.array([0, 1]), y=y)
        expected = np.array([(negative + positive) / (2 * count) for count in (negative, positive)])
        require(np.allclose(actual, expected, rtol=1e-12, atol=1e-12), "Synthetic balanced weights")
        require(
            np.allclose(actual * [negative, positive], len(y) / 2), "Equal synthetic class mass"
        )
        weights.append(
            {
                "synthetic_negative_units": negative,
                "synthetic_positive_units": positive,
                "class_0_weight": float(actual[0]),
                "class_1_weight": float(actual[1]),
            }
        )
    fit, calibration, assessment = (
        metadata(2021, "fit"),
        metadata(2022, "calibration"),
        metadata(2023, "assessment"),
    )
    audit_roles(fit, calibration, assessment)
    rejected = []
    for problem in (
        "fit_calibration_event",
        "fit_assessment_event",
        "calibration_assessment_event",
        "in_sample_calibration",
        "final_year",
    ):
        a, b, c = fit.copy(deep=True), calibration.copy(deep=True), assessment.copy(deep=True)
        if problem == "fit_calibration_event":
            b.at[0, "event_ids"] = a.iloc[0].event_ids
        elif problem == "fit_assessment_event":
            c.at[0, "event_ids"] = a.iloc[0].event_ids
        elif problem == "calibration_assessment_event":
            c.at[0, "event_ids"] = b.iloc[0].event_ids
        elif problem == "in_sample_calibration":
            b = a.copy(deep=True)
        else:
            c.prediction_timestamp_utc = "2025-07-01T00:00:00Z"
        try:
            audit_roles(a, b, c)
        except ValueError:
            rejected.append(problem)
    require(len(rejected) == 5, "All synthetic role leakage cases rejected")
    require(specification()["negative_label_permitted"] is False, "Unknown is not negative")

    out = (
        ROOT
        / "outputs/reports/dataset/imbalance_calibration_plan_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)

    def save(name, value):
        (out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    save("plan_snapshot.json", plan)
    save(
        "synthetic_weight_checks.json",
        {"scope": "synthetic_binary_units_not_events", "cases": weights},
    )
    save(
        "synthetic_role_checks.json",
        {
            "scope": "synthetic_training_years_only",
            "valid_example_passed": True,
            "rejected_cases": rejected,
            "embargo_hours_fixture_only": 0,
        },
    )
    pd.DataFrame(candidates).to_csv(out / "candidate_comparisons.csv", index=False)
    require(
        all(digest(ROOT / name) == sha for name, sha in pins.items()),
        "Final comparison design closure",
    )
    save("input_manifest.json", pins)
    save(
        "readback.json",
        {
            "status": "comparison_design_checked_not_training",
            "data_role_direction": plan["data_role_direction"],
            "calendar_feasibility_verified": False,
            "input_file_count": len(pins),
            "proposed_comparison_cells": len(candidates),
            "synthetic_weight_cases": len(weights),
            "synthetic_role_failures_rejected": len(rejected),
            "implementation_sklearn_version": importlib.metadata.version("scikit-learn"),
            "real_class_counts_available": False,
            "real_feature_partitions_fitted": 0,
            "classifiers_fitted": 0,
            "calibrators_fitted": 0,
            "network_bytes": 0,
            "cloud_jobs_started": 0,
            "labels_accepted": False,
            "model_ready": False,
            "training_authorized": False,
            "final_merge_performed": False,
            "validation_or_final_data_accessed": False,
            "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
        },
    )
    save(
        "completion_readback.json",
        {
            "status": "passed_design_preparation_only",
            "report_sha256": digest(out / "readback.json"),
        },
    )
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
