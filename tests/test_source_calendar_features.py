import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def preparation(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "calendar_X_preparation_test", folder / "prepare_source_calendar_features.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "flag",
    [
        "new_feature_extraction_authorized",
        "new_model_fitting_authorized",
        "negative_label_permitted",
        "final_merge_permitted",
    ],
)
def test_continuation_is_feature_preparation_only(preparation, flag):
    policy = json.loads(preparation.POLICY.read_bytes())
    policy[flag] = not policy[flag]
    with pytest.raises(ValueError):
        preparation.validate_decision(policy)


def toy(preparation):
    keys = pd.DataFrame(
        {"grid_id": ["A", "B"], "prediction_timestamp_utc": ["2020-02-05T00:00:00+00:00"] * 2}
    )
    features = keys.copy()
    for field in preparation.join.feature_names():
        features[field] = [1.0, np.nan]
    return features, keys.copy(), preparation.frame_keys(keys)


def test_month_checkpoint_roundtrip_keeps_missing_values_and_rejects_corruption(
    preparation, tmp_path
):
    features, qa, keys = toy(preparation)
    p = preparation.seal_month(tmp_path, "2020-02", features, qa, [{"day": "2020-02-05"}], keys, {})
    report, frames = preparation.read_month(p, preparation.digest(p), keys)
    assert report["rows"] == 2
    pd.testing.assert_frame_equal(frames[0], features)
    with (p.parent / "features.csv").open("a", encoding="utf-8") as stream:
        stream.write("changed\n")
    with pytest.raises(ValueError, match="Immutable month"):
        preparation.read_month(p, preparation.digest(p), keys)


def test_missing_duplicate_or_extra_key_cannot_be_accepted_as_a_completed_month(preparation):
    features, qa, keys = toy(preparation)
    for broken in (features.iloc[:1], pd.concat([features, features.iloc[:1]], ignore_index=True)):
        with pytest.raises(ValueError):
            preparation.verify_frames(broken, qa, keys)


def test_only_runtime_progress_can_be_replaced_accepted_receipt_stays_immutable(
    preparation, tmp_path
):
    path = tmp_path / "receipt.json"
    preparation.save_json(path, {"status": "sealed"})
    with pytest.raises(ValueError):
        preparation.save_json(path, {"status": "altered"})
    assert json.loads(path.read_bytes())["status"] == "sealed"
    progress = tmp_path / "runtime_progress.json"
    preparation.save_json(progress, {"months": 1})
    preparation.save_json(progress, {"months": 2})
    assert json.loads(progress.read_bytes())["months"] == 2


def test_blank_targets_and_memberships_roundtrip_without_becoming_labels(preparation, tmp_path):
    _, metadata, _ = toy(preparation)
    metadata["target"] = np.nan
    metadata["accepted_L_membership"] = np.nan
    metadata["daily_observation_status"] = "unknown"
    metadata["role_is_model_training_permission"] = False
    path = tmp_path / "review_roles.csv"
    metadata.to_csv(path, index=False)
    restored = preparation.parse_csv(path.read_bytes())
    pd.testing.assert_frame_equal(metadata, restored)
    assert restored.target.isna().all() and not restored.role_is_model_training_permission.any()
