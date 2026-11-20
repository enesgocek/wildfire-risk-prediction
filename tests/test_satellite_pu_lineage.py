import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def replay(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "satellite_replay_test", folder / "replay_satellite_pu_lineage.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_role_guard_precedes_other_fields(replay):
    row = {
        "detection_id": "A",
        "grid_id": "G",
        "source_sensor": "SNPP",
        "type": "0",
        "confidence": "n",
        "detection_timestamp_utc": "2021-07-28T10:11:00+00:00",
        "latitude": "37",
        "longitude": "30",
    }
    result = replay.fit_source(
        [
            row,
            {"detection_timestamp_utc": "2023-01-02T00:00:00+00:00"},
            {"detection_timestamp_utc": "2025-01-02T00:00:00+00:00"},
        ]
    )
    assert result.detection_id.tolist() == ["A"]


def test_first_cells_midnight_and_fit_upper_boundary_are_preserved(replay):
    births = pd.DataFrame(
        {
            "birth_candidate_id": ["a", "b"],
            "first_detection_utc": ["2022-12-31T00:00:00+00:00", "2022-12-31T10:00:00+00:00"],
            "earliest_grid_ids_json": ['["A","B"]', '["C"]'],
        }
    )
    keys = replay.first_keys(births)
    assert keys.grid_id.tolist() == ["A", "B", "C"]
    assert keys.prediction_timestamp_utc.str[:10].tolist() == [
        "2022-12-30",
        "2022-12-30",
        "2022-12-31",
    ]
    assert keys.fit_role_boundary_review.tolist() == [False, False, True]
    assert keys.target.isna().all() and keys.weak_positive_membership.isna().all()


def test_same_input_static_first_does_not_swallow_later_birth_cells(replay):
    frame = pd.DataFrame(
        {
            "detection_id": ["one", "two", "three"],
            "grid_id": ["A", "B", "C"],
            "timestamp": pd.to_datetime(
                ["2021-07-28T10:11Z", "2021-07-28T10:12Z", "2021-07-28T10:12Z"]
            ),
        }
    )
    detected = pd.DataFrame(
        {"detection_id": frame.detection_id, "final_graph_membership_sha256": ["merged"] * 3}
    )
    static = replay.static_first_keys(frame, detected)
    births = pd.DataFrame(
        {
            "birth_candidate_id": ["a", "b"],
            "first_detection_utc": ["2021-07-28T10:11:00+00:00", "2021-07-28T10:12:00+00:00"],
            "earliest_grid_ids_json": ['["A"]', '["B","C"]'],
        }
    )
    kept = replay.first_keys(births)
    assert static.grid_id.tolist() == ["A"] and kept.grid_id.tolist() == ["A", "B", "C"]


@pytest.mark.parametrize(
    "flag",
    [
        "model_training_authorized",
        "negative_label_permitted",
        "new_L_memberships_permitted",
        "final_merge_permitted",
    ],
)
def test_preparation_authority_cannot_be_expanded(replay, flag):
    policy = json.loads(replay.POLICY.read_bytes())
    policy[flag] = True
    with pytest.raises(ValueError):
        replay.validate_policy(policy)
