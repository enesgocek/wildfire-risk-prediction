"""Offline synthetic preprocessing rehearsal; never fit real feature partitions."""

import importlib.metadata
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, feature_names, require
from wildfire_risk_prediction.fold_preprocessing import fit_fold_preprocessor

ROOT = Path(__file__).resolve().parents[2]
PARENT = Path("outputs/reports/dataset/evaluation_core_v1/20261016T010607Z_903eb104")
PARENT_SHA = "ba1ac26003a370be4bfece12a92a41f270dfdb9965b5dbceff0a7d52b6bf3266"


def metadata(year, count):
    return pd.DataFrame(
        {
            "grid_id": [f"synthetic_{i}" for i in range(count)],
            "prediction_timestamp_utc": [f"{year}-07-01T00:00:00Z"] * count,
            "event_ids": [[] for _ in range(count)],
            "event_membership_complete": [True] * count,
        }
    )


def run():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline preprocessing rehearsal")

    socket.socket.connect = deny
    socket.create_connection = deny
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained preprocessing input",
        )
        sha = digest(path)
        require(expected is None or sha == expected, "Preprocessing input unchanged")
        pins[path.relative_to(ROOT).as_posix()] = sha
        return path

    def read(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    parent = read(PARENT / "readback.json", PARENT_SHA)
    closing = read(PARENT / "completion_readback.json")
    require(closing["report_sha256"] == PARENT_SHA, "Parent closure")
    for name, sha in parent["artifact_sha256"].items():
        retained(PARENT / name, sha)
    for name, sha in read(PARENT / "input_manifest.json").items():
        retained(name, sha)
    require(
        parent["labels_accepted"] is False
        and parent["model_ready"] is False
        and parent["real_unknown_targets_rejected"] == 156,
        "Parent remains unlabelled, no real preprocessing admission",
    )
    config = read("configs/fold_preprocessing_v1.json")
    require(
        all(
            config[name] is None
            for name in (
                "selected_real_imputation",
                "selected_real_scaling",
                "selected_real_empty_policy",
            )
        )
        and not config["labels_accepted"]
        and not config["model_ready"],
        "Real preprocessing choices and scientific gates remain open",
    )
    for name in (
        Path(__file__).relative_to(ROOT),
        "src/wildfire_risk_prediction/fold_preprocessing.py",
        "tests/test_fold_preprocessing.py",
        "pyproject.toml",
    ):
        retained(name)

    rng = np.random.default_rng(20261016)
    features = tuple(feature_names()[:3])
    rows = []
    maximum = 0.0
    for case in range(40):
        train = metadata(2020, 4 + case)
        held = metadata(2021, 7)
        x = rng.normal(10, 3, size=(len(train), 3))
        x[rng.random(x.shape) < 0.3] = np.nan
        x[0] = [1, 2, 3]
        x[:, 1] = 7.0
        if case % 2:
            x[:, 2] = np.nan
        values = train[KEYS].copy()
        future = held[KEYS].copy()
        z = rng.normal(-100, 30, size=(len(held), 3))
        z[0] = np.nan
        for i, name in enumerate(features):
            values[name], future[name] = x[:, i], z[:, i]
        scaling = case % 3 != 0
        state = fit_fold_preprocessor(
            values,
            train,
            held,
            features=features,
            imputation="median",
            standardize=scaling,
            empty_policy="drop" if case % 2 else "error",
            embargo_hours=0,
        )
        selected = np.flatnonzero((~np.isnan(x)).any(axis=0))
        medians = np.nanmedian(x[:, selected], axis=0)
        imputed = np.where(np.isnan(x[:, selected]), medians, x[:, selected])
        expected = np.where(np.isnan(z[:, selected]), medians, z[:, selected])
        if scaling:
            scales = imputed.std(axis=0, ddof=0)
            scales[scales == 0] = 1
            expected = (expected - imputed.mean(axis=0)) / scales
        before = state.summary()
        result = state.transform(future, partition="held_out")
        actual = result[list(state.retained_features)].to_numpy()
        difference = float(np.max(np.abs(actual - expected)))
        maximum = max(maximum, difference)
        require(np.allclose(actual, expected, rtol=1e-12, atol=1e-12), "NumPy fixture agreement")
        future[features[0]] = 1e6
        state.transform(future, partition="held_out")
        require(state.summary() == before, "Held-out extremes cannot update statistics")
        rows.append(
            {
                "case": case,
                "training_rows": len(train),
                "held_out_rows": len(held),
                "standardize": scaling,
                "dropped_columns": 3 - len(selected),
                "maximum_absolute_difference": difference,
                "held_out_statistics_unchanged": True,
            }
        )

    out = (
        ROOT
        / "outputs/reports/dataset/fold_preprocessing_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)

    def save(name, value):
        (out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    save("synthetic_cases.json", rows)
    save("last_synthetic_statistics.json", {"scope": "synthetic_only", **state.summary()})
    save(
        "scope_guard.json",
        {
            "parent_unassigned_real_targets": 156,
            "real_feature_partitions_fitted": 0,
            "real_policy_selected": False,
            "validation_or_final_data_accessed": False,
        },
    )
    require(all(digest(ROOT / name) == sha for name, sha in pins.items()), "Final input closure")
    save("input_manifest.json", pins)
    save(
        "readback.json",
        {
            "status": "synthetic_fold_preprocessing_rehearsed_not_real_admission",
            "synthetic_cases": len(rows),
            "maximum_absolute_difference": maximum,
            "reference": "Independent NumPy medians and population standard deviations",
            "implementation_sklearn_version": importlib.metadata.version("scikit-learn"),
            "input_file_count": len(pins),
            "network_bytes": 0,
            "cloud_jobs_started": 0,
            "real_feature_partitions_fitted": 0,
            "classifiers_fitted": 0,
            "calibrators_fitted": 0,
            "labels_accepted": False,
            "model_ready": False,
            "final_merge_performed": False,
            "artifact_sha256": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
        },
    )
    save(
        "completion_readback.json",
        {
            "status": "passed_synthetic_preparation_only",
            "report_sha256": digest(out / "readback.json"),
        },
    )
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
