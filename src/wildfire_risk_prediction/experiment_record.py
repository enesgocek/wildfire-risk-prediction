"""Deterministic preparation records, never executable training authorizations."""

import hashlib
import json
import re
from pathlib import Path, PurePosixPath

import numpy as np

from wildfire_risk_prediction.evaluation_folds import audit_training_fold, forward_year_skeleton
from wildfire_risk_prediction.feature_join import feature_names, require
from wildfire_risk_prediction.fold_preprocessing import (
    fit_fold_preprocessor,
    identities,
    numeric_matrix,
)
from wildfire_risk_prediction.target_admission import specification

VERSION = "experiment_preparation_v1"
REQUIRED_FILES = (
    "configs/evaluation_core_v1.json",
    "configs/fold_preprocessing_v1.json",
    "src/wildfire_risk_prediction/experiment_record.py",
    "src/wildfire_risk_prediction/evaluation_folds.py",
    "src/wildfire_risk_prediction/fold_preprocessing.py",
    "src/wildfire_risk_prediction/feature_join.py",
    "src/wildfire_risk_prediction/target_admission.py",
    "src/wildfire_risk_prediction/final_merge_gate.py",
    "pyproject.toml",
    "uv.lock",
)


def content_digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _file(root, name):
    require(isinstance(name, str) and "\\" not in name, "Relative POSIX input path")
    path = PurePosixPath(name)
    require(
        bool(path.parts)
        and not path.is_absolute()
        and ":" not in name
        and all(part not in ("", ".", "..") for part in name.split("/")),
        "Canonical contained relative input path",
    )
    require(
        not any(part.startswith(".") for part in path.parts)
        and not re.search(r"(?i)(credential|token|connection|client_secret|password)", path.name)
        and (
            path.parts[0] in {"configs", "src", "tests", "scripts"}
            or path.parts[:3] == ("outputs", "reports", "dataset")
            or name in {"uv.lock", "pyproject.toml"}
        ),
        "Explicit code/config/report inputs only; private paths forbidden",
    )
    current = root
    for part in path.parts:
        current = current / part
        require(not current.is_symlink(), "No symlink input components")
    require(
        current.is_file() and current.resolve().is_relative_to(root.resolve()),
        "Contained regular input file",
    )
    return current


def snapshot_files(root, expected):
    """Hash explicitly named files; do not scan directories or expose file contents."""
    root = Path(root)
    require(isinstance(expected, dict) and expected, "Explicit nonempty input map")
    result = []
    for name, sha in sorted(expected.items()):
        require(
            sha is None or isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha),
            "Expected SHA-256 format",
        )
        path = _file(root, name)
        with path.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        require(sha is None or actual == sha, "Bound input changed")
        result.append({"path": name, "sha256": actual, "bytes": path.stat().st_size})
    return result


def _pinned_json(root, name, snapshots):
    entry = next(item for item in snapshots if item["path"] == name)
    raw = _file(Path(root), name).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == entry["sha256"], "Policy changed during read")
    return json.loads(raw)


def _metadata_digest(frame, spatial_column):
    keys = identities(frame)
    rows = [
        {
            "key": list(key),
            "event_ids": sorted(frame.iloc[i].event_ids),
            "event_membership_complete": bool(frame.iloc[i].event_membership_complete),
            "spatial_block": frame.iloc[i][spatial_column] if spatial_column else None,
        }
        for i, key in enumerate(keys)
    ]
    return content_digest(sorted(rows, key=lambda item: item["key"]))


def _matrix_digest(frame, features):
    keys = identities(frame)
    values = numeric_matrix(frame, tuple(features))
    rows = [
        [list(key), [None if np.isnan(x) else float(x) for x in values[i]]]
        for i, key in enumerate(keys)
    ]
    return content_digest({"features": list(features), "rows": sorted(rows)})


def synthetic_fold_record(train, held_out, train_metadata, held_out_metadata, **options):
    """Small explicit fixtures only; no real fold or label admission is performed."""
    for frame in (train, held_out, train_metadata, held_out_metadata):
        require(
            len(frame) <= 1000
            and identities(frame)
            and frame.grid_id.str.startswith("synthetic_").all(),
            "Only bounded explicitly synthetic identities allowed",
        )
    state = fit_fold_preprocessor(train, train_metadata, held_out_metadata, **options)
    train_result = state.transform(train, partition="training")
    held_result = state.transform(held_out, partition="held_out")
    spatial_column = options.get("spatial_column")
    body = {
        "scope": "synthetic_fixture_only",
        "audit": audit_training_fold(
            train_metadata,
            held_out_metadata,
            embargo_hours=options["embargo_hours"],
            spatial_column=spatial_column,
        ),
        "spatial_column": spatial_column,
        "training_metadata_sha256": _metadata_digest(train_metadata, spatial_column),
        "held_out_metadata_sha256": _metadata_digest(held_out_metadata, spatial_column),
        "training_features_sha256": _matrix_digest(train, state.features),
        "held_out_features_sha256": _matrix_digest(held_out, state.features),
        "transformed_training_sha256": _matrix_digest(train_result, state.retained_features),
        "transformed_held_out_sha256": _matrix_digest(held_result, state.retained_features),
        "preprocessing": state.summary(),
    }
    return {**body, "fold_id": content_digest(body)}


def build_preparation_record(root, *, inputs, synthetic_folds=None, synthetic_seed=None):
    expected = dict.fromkeys(REQUIRED_FILES)
    expected.update(inputs)
    snapshots = snapshot_files(root, expected)
    evaluation = _pinned_json(root, REQUIRED_FILES[0], snapshots)
    preprocessing = _pinned_json(root, REQUIRED_FILES[1], snapshots)
    require(
        evaluation["primary_metric"] == "average_precision"
        and evaluation["primary_metric_decision"] == "explicit_user_choice_2026-10-16"
        and evaluation["labels_accepted"] is False
        and evaluation["model_ready"] is False
        and evaluation["final_merge_performed"] is False,
        "Current selected AP and closed evaluation gates required",
    )
    require(
        all(
            preprocessing[key] is None
            for key in (
                "selected_real_imputation",
                "selected_real_scaling",
                "selected_real_empty_policy",
            )
        )
        and preprocessing["labels_accepted"] is False
        and preprocessing["model_ready"] is False
        and preprocessing["final_merge_performed"] is False,
        "No real preprocessing selection or admission",
    )
    synthetic = synthetic_folds is not None
    if synthetic:
        require(
            isinstance(synthetic_folds, list)
            and synthetic_folds
            and type(synthetic_seed) is int
            and 0 <= synthetic_seed < 2**32,
            "Explicit nonempty synthetic folds and bounded seed",
        )
        fold_ids = []
        for fold in synthetic_folds:
            body = {key: value for key, value in fold.items() if key != "fold_id"}
            require(
                fold["scope"] == "synthetic_fixture_only"
                and fold["preprocessing"]["labels_accepted"] is False
                and fold["preprocessing"]["model_ready"] is False
                and fold["fold_id"] == content_digest(body),
                "Unchanged synthetic fold preparation only",
            )
            fold_ids.append(fold["fold_id"])
        require(len(fold_ids) == len(set(fold_ids)), "No duplicate synthetic folds")
    else:
        require(synthetic_seed is None, "Real preparation has no selected model seed")
    body = {
        "version": VERSION,
        "status": "preparation_record_not_executable_experiment",
        "scope": "synthetic_rehearsal" if synthetic else "current_real_preparation_only",
        "inputs": snapshots,
        "candidate_features": feature_names(),
        "evaluation_policy": evaluation,
        "preprocessing_policy": preprocessing,
        "label_protocol_snapshot": specification(),
        "calendar_skeleton": forward_year_skeleton(),
        "synthetic_folds": sorted(synthetic_folds, key=lambda x: x["fold_id"]) if synthetic else [],
        "synthetic_seed": synthetic_seed,
        "real_model": None,
        "real_hyperparameters": None,
        "real_sampling_policy": None,
        "real_calibration_policy": None,
        "real_final_review": None,
        "real_final_merge_approval": None,
        "labels_accepted": False,
        "model_ready": False,
        "training_authorized": False,
        "final_merge_performed": False,
        "validation_or_final_data_accessed": False,
    }
    # Detached JSON types; callers cannot mutate the record by changing source objects.
    record = json.loads(json.dumps({**body, "record_id": content_digest(body)}, allow_nan=False))
    require(
        snapshots == snapshot_files(root, {x["path"]: x["sha256"] for x in snapshots}),
        "Input closure before record return",
    )
    return record


def verify_preparation_record(root, record):
    """Reopen bound inputs; hashes are provenance checks, not authentication or approval."""
    require(isinstance(record, dict) and isinstance(record.get("inputs"), list), "Record schema")
    pins = {item["path"]: item["sha256"] for item in record["inputs"]}
    require(len(pins) == len(record["inputs"]), "Unique record input paths")
    require(set(REQUIRED_FILES) <= set(pins), "Mandatory policy, code and lock inputs")
    synthetic = record.get("scope") == "synthetic_rehearsal"
    rebuilt = build_preparation_record(
        root,
        inputs=pins,
        synthetic_folds=record.get("synthetic_folds") if synthetic else None,
        synthetic_seed=record.get("synthetic_seed"),
    )
    require(record == rebuilt, "Record fields or identity changed; new record required")
    return {"status": "preparation_record_readback_passed", "training_authorized": False}
