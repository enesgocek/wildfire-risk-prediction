"""Bind current preparation evidence and separate synthetic folds; no real training."""

import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.experiment_record import (
    build_preparation_record,
    content_digest,
    synthetic_fold_record,
    verify_preparation_record,
)
from wildfire_risk_prediction.feature_join import KEYS, feature_names, require

ROOT = Path(__file__).resolve().parents[2]
PARENT = Path("outputs/reports/dataset/fold_preprocessing_v1/20261016T011740Z_706c3793")
PARENT_SHA = "8cc2ac561d0fc73e5b71a080de497451bbe5424ad6593b0cefee45ea0569caae"


def synthetic_fixtures():
    rng = np.random.default_rng(20261016)
    features = feature_names()[:3]
    result = []
    for year in (2019, 2022):

        def metadata(selected_year, count):
            return pd.DataFrame(
                {
                    "grid_id": [f"synthetic_{i}" for i in range(count)],
                    "prediction_timestamp_utc": [f"{selected_year}-07-01T00:00:00Z"] * count,
                    "event_ids": [[f"synthetic_event_{selected_year}_{i}"] for i in range(count)],
                    "event_membership_complete": [True] * count,
                    "block": [str(selected_year)] * count,
                }
            )

        train_meta, held_meta = metadata(year - 1, 6), metadata(year, 4)
        train, held = train_meta[KEYS].copy(), held_meta[KEYS].copy()
        for name in features:
            train[name], held[name] = rng.normal(size=6), rng.normal(size=4)
        train.loc[1, features[0]], held.loc[1, features[0]] = np.nan, np.nan
        train[features[1]], held[features[1]] = 7.0, 9.0
        for scale in (False, True):
            result.append(
                synthetic_fold_record(
                    train,
                    held,
                    train_meta,
                    held_meta,
                    features=features,
                    imputation="median",
                    standardize=scale,
                    empty_policy="error",
                    embargo_hours=0,
                    spatial_column="block",
                )
            )
    return result


def run():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline experiment preparation")

    socket.socket.connect = deny
    socket.create_connection = deny
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained experiment preparation input",
        )
        sha = digest(path)
        require(expected is None or expected == sha, "Experiment preparation input unchanged")
        pins[path.relative_to(ROOT).as_posix()] = sha
        return path

    def read(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    parent = read(PARENT / "readback.json", PARENT_SHA)
    closing = read(PARENT / "completion_readback.json")
    require(closing["report_sha256"] == PARENT_SHA, "Parent report closure")
    for name, sha in parent["artifact_sha256"].items():
        retained(PARENT / name, sha)
    for name, sha in read(PARENT / "input_manifest.json").items():
        retained(name, sha)
    require(
        parent["real_feature_partitions_fitted"] == 0
        and parent["labels_accepted"] is False
        and parent["model_ready"] is False,
        "Parent is preparation only",
    )
    for name in (
        Path(__file__).relative_to(ROOT),
        "tests/test_experiment_record.py",
    ):
        retained(name)

    current = build_preparation_record(ROOT, inputs=pins)
    synthetic = build_preparation_record(
        ROOT, inputs=pins, synthetic_folds=synthetic_fixtures(), synthetic_seed=20261016
    )
    require(
        current["record_id"] == build_preparation_record(ROOT, inputs=pins)["record_id"],
        "Deterministic current preparation identity",
    )
    checks = []
    forged = json.loads(json.dumps(current))
    forged["training_authorized"] = True
    forged["record_id"] = content_digest({k: v for k, v in forged.items() if k != "record_id"})
    try:
        verify_preparation_record(ROOT, forged)
    except ValueError:
        checks.append("rehashing_does_not_authorize_training")
    require(len(checks) == 1, "Forged training flag rejected")

    out = (
        ROOT
        / "outputs/reports/dataset/experiment_preparation_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)

    def save(name, value):
        (out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    for name, record in (
        ("current_preparation_record.json", current),
        ("synthetic_preparation_record.json", synthetic),
    ):
        save(name, record)
        restored = json.loads((out / name).read_text(encoding="utf-8"))
        verify_preparation_record(ROOT, restored)
        require(restored == record, "Exact record serialization/readback")
        checks.append(name + "_readback_passed")
    pins = {item["path"]: item["sha256"] for item in current["inputs"]}
    require(all(digest(ROOT / name) == sha for name, sha in pins.items()), "Final input closure")
    save("record_readback_checks.json", checks)
    save("input_manifest.json", pins)
    save(
        "readback.json",
        {
            "status": "experiment_preparation_recorded_no_executable_training",
            "current_preparation_id": current["record_id"],
            "synthetic_preparation_id": synthetic["record_id"],
            "input_file_count": len(pins),
            "preparation_record_count": 2,
            "synthetic_fold_count": len(synthetic["synthetic_folds"]),
            "real_executable_fold_count": 0,
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
            "status": "passed_preparation_record_only",
            "report_sha256": digest(out / "readback.json"),
        },
    )
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
