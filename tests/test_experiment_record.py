import copy
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.experiment_record import (
    REQUIRED_FILES,
    build_preparation_record,
    content_digest,
    snapshot_files,
    synthetic_fold_record,
    verify_preparation_record,
)
from wildfire_risk_prediction.feature_join import KEYS, feature_names

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def record_root(tmp_path):
    for name in REQUIRED_FILES:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return tmp_path


def fixtures():
    def metadata(year):
        return pd.DataFrame(
            {
                "grid_id": ["synthetic_a", "synthetic_b", "synthetic_c"],
                "prediction_timestamp_utc": [f"{year}-07-01T00:00:00Z"] * 3,
                "event_ids": [[f"{year}_event"], [], []],
                "event_membership_complete": [True] * 3,
                "block": [str(year)] * 3,
            }
        )

    train_meta, held_meta = metadata(2020), metadata(2021)
    train, held = train_meta[KEYS].copy(), held_meta[KEYS].copy()
    features = feature_names()[:2]
    train[features[0]], train[features[1]] = [1.0, np.nan, 5.0], 7.0
    held[features[0]], held[features[1]] = [np.nan, 100.0, -100.0], 9.0
    options = dict(
        features=features,
        imputation="median",
        standardize=True,
        empty_policy="error",
        embargo_hours=0,
        spatial_column="block",
    )
    return train, held, train_meta, held_meta, options


def fold():
    train, held, train_meta, held_meta, options = fixtures()
    return synthetic_fold_record(train, held, train_meta, held_meta, **options)


def test_real_preparation_deterministic_readback_and_closed_gates(record_root):
    first = build_preparation_record(record_root, inputs={})
    second = build_preparation_record(record_root, inputs={})
    assert first == second
    assert first["scope"] == "current_real_preparation_only"
    assert first["synthetic_folds"] == []
    assert first["real_model"] is None
    assert first["real_final_review"] is None
    assert first["real_final_merge_approval"] is None
    assert first["evaluation_policy"]["primary_metric"] == "average_precision"
    assert first["label_protocol_snapshot"]["daily_observation_status"] == "unknown"
    assert first["label_protocol_snapshot"]["negative_label_permitted"] is False
    assert first["training_authorized"] is False
    assert len(first["calendar_skeleton"]) == 5
    assert verify_preparation_record(record_root, first)["training_authorized"] is False


def test_canonical_json_roundtrip_input_order_and_detached_fold(record_root):
    fixture = fold()
    record = build_preparation_record(
        record_root, inputs={}, synthetic_folds=[fixture], synthetic_seed=3
    )
    restored = json.loads(json.dumps(record))
    assert verify_preparation_record(record_root, restored)["training_authorized"] is False
    fixture["preprocessing"]["training_medians"][feature_names()[0]] = -999
    assert record["synthetic_folds"][0]["preprocessing"] != fixture["preprocessing"]
    paths = dict.fromkeys(reversed(REQUIRED_FILES))
    assert snapshot_files(record_root, paths) == snapshot_files(
        record_root, dict(reversed(paths.items()))
    )


@pytest.mark.parametrize("changed", ["value", "event", "block", "scaling", "order"])
def test_fold_identity_tracks_values_events_blocks_and_options_not_row_order(changed):
    train, held, train_meta, held_meta, options = fixtures()
    before = fold()
    if changed == "value":
        held.loc[0, feature_names()[0]] = 123.0
    elif changed == "event":
        held_meta.at[1, "event_ids"] = ["new_event"]
    elif changed == "block":
        held_meta["block"] = "different"
    elif changed == "scaling":
        options["standardize"] = False
    else:
        train, held = train.iloc[::-1], held.iloc[::-1]
        train_meta, held_meta = train_meta.iloc[::-1], held_meta.iloc[::-1]
    after = synthetic_fold_record(train, held, train_meta, held_meta, **options)
    assert (before["fold_id"] == after["fold_id"]) is (changed == "order")
    if changed in ("value", "event", "block"):
        assert before["preprocessing"] == after["preprocessing"]


@pytest.mark.parametrize(
    "problem", ["real_id", "unknown_event", "shared_event", "2025", "missing_row"]
)
def test_synthetic_fold_rejects_real_or_unaudited_partitions(problem):
    train, held, train_meta, held_meta, options = fixtures()
    if problem == "real_id":
        train.loc[0, "grid_id"] = "actual_grid"
    elif problem == "unknown_event":
        held_meta.loc[0, "event_membership_complete"] = False
    elif problem == "shared_event":
        held_meta.at[0, "event_ids"] = train_meta.iloc[0].event_ids
    elif problem == "2025":
        held_meta.prediction_timestamp_utc = "2025-07-01T00:00:00Z"
    else:
        held = held.iloc[1:]
    with pytest.raises(ValueError):
        synthetic_fold_record(train, held, train_meta, held_meta, **options)


@pytest.mark.parametrize("problem", ["bytes", "missing", "same_length"])
def test_bound_files_reopened_and_changes_rejected(record_root, problem):
    record = build_preparation_record(record_root, inputs={})
    path = record_root / "src/wildfire_risk_prediction/final_merge_gate.py"
    if problem == "missing":
        path.unlink()
    elif problem == "same_length":
        path.write_bytes(path.read_bytes().replace(b"True", b"None", 1))
    else:
        path.write_bytes(path.read_bytes() + b"\n# changed\n")
    with pytest.raises(ValueError):
        verify_preparation_record(record_root, record)


@pytest.mark.parametrize(
    "field,value",
    [
        ("training_authorized", True),
        ("model_ready", True),
        ("labels_accepted", True),
        ("final_merge_performed", True),
        ("validation_or_final_data_accessed", True),
        ("real_final_merge_approval", {"decision": "continue"}),
        ("real_model", "classifier"),
    ],
)
def test_rehashing_record_cannot_turn_preparation_into_authorization(record_root, field, value):
    record = build_preparation_record(record_root, inputs={})
    record[field] = value
    record["record_id"] = content_digest({k: v for k, v in record.items() if k != "record_id"})
    with pytest.raises(ValueError):
        verify_preparation_record(record_root, record)


@pytest.mark.parametrize(
    "problem", ["duplicate_input", "missing_required", "fold_mutation", "seed"]
)
def test_structural_record_mutations_rejected(record_root, problem):
    record = build_preparation_record(
        record_root, inputs={}, synthetic_folds=[fold()], synthetic_seed=3
    )
    if problem == "duplicate_input":
        record["inputs"].append(copy.deepcopy(record["inputs"][0]))
    elif problem == "missing_required":
        record["inputs"].pop()
    elif problem == "fold_mutation":
        record["synthetic_folds"][0]["preprocessing"]["training_rows"] += 1
    else:
        record["synthetic_seed"] = None
    with pytest.raises(ValueError):
        verify_preparation_record(record_root, record)


@pytest.mark.parametrize(
    "path",
    [
        "../uv.lock",
        "configs/../uv.lock",
        "C:/outside.json",
        ".env",
        "configs/token.json",
        "data/raw/x",
        "configs\\x.json",
    ],
)
def test_private_or_noncanonical_paths_rejected(record_root, path):
    with pytest.raises(ValueError):
        snapshot_files(record_root, {path: None})


def test_expected_hash_and_unselected_real_policy_enforced(record_root):
    with pytest.raises(ValueError, match="changed"):
        snapshot_files(record_root, {"uv.lock": "0" * 64})
    path = record_root / "configs/fold_preprocessing_v1.json"
    spec = json.loads(path.read_text())
    spec["selected_real_imputation"] = "median"
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="No real preprocessing"):
        build_preparation_record(record_root, inputs={})


def test_duplicate_fold_and_real_seed_without_synthetic_scope_rejected(record_root):
    fixture = fold()
    with pytest.raises(ValueError, match="duplicate"):
        build_preparation_record(
            record_root, inputs={}, synthetic_folds=[fixture, fixture], synthetic_seed=3
        )
    with pytest.raises(ValueError, match="no selected model seed"):
        build_preparation_record(record_root, inputs={}, synthetic_seed=3)
