import hashlib
import importlib.util
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def review():
    path = (
        Path(__file__).resolve().parents[1] / "scripts/quality/prepare_source_pu_feature_review.py"
    )
    spec = importlib.util.spec_from_file_location("source_feature_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "stamp",
    [
        "2023-01-01T00:00:00+00:00",
        "2024-01-01T00:00:00+00:00",
        "2025-01-01T00:00:00+00:00",
        "2022-12-31T00:00:00+00:00",
        "2021-05-01T12:00:00+00:00",
        "2021-05-01T00:00:00",
    ],
)
def test_review_role_checked_before_any_source_path(review, stamp):
    with pytest.raises(ValueError):
        review.review_key("A", stamp)


def source(name):
    return {
        "archive_row": name,
        "diagnostic_focus": True,
        "researcher_retained_outside_L": False,
        "target": None,
        "membership": "review_unassigned",
        "conditional_center_grid_ids": ["A"],
        "conditional_target_window_starts": ["2021-05-01T00:00:00+00:00"],
    }


def test_same_key_source_records_and_U_overlap_are_preserved_without_targets(review):
    u = [
        {
            "grid_id": "A",
            "prediction_timestamp_utc": "2021-05-01T00:00:00+00:00",
            "target": "",
            "daily_observation_status": "unknown",
        }
    ]
    sources, u_keys, mapping = review.collect_keys(
        [source("one"), source("two"), {"diagnostic_focus": False}], u
    )
    assert sources == u_keys and len(mapping) == 2
    assert {r["archive_row"] for r in mapping} == {"one", "two"}
    assert all(r["target"] is None for r in mapping)


def test_duplicate_source_or_retention_override_is_rejected(review):
    with pytest.raises(ValueError, match="Unique source"):
        review.collect_keys([source("one"), source("one")], [])
    row = source("WF1538") | {"researcher_retained_outside_L": True}
    with pytest.raises(ValueError, match="retention override"):
        review.collect_keys([row], [])


def test_file_role_guard_precedes_path_access(review, tmp_path):
    with pytest.raises(ValueError, match="Fit-only"):
        review.selected_file(tmp_path, {}, "2025-01-01", "features")


def test_changed_file_and_workspace_escape_fail(review, tmp_path):
    folder = tmp_path / "outputs/reports/dataset/feature_month_v1/run/parts/2021-05"
    folder.mkdir(parents=True)
    path = folder / "2021-05-01_features.csv"
    data = b"grid_id,prediction_timestamp_utc,x\nA,2021-05-01T00:00:00+00:00,1\n"
    path.write_bytes(data)
    entry = {
        "day": "2021-05-01",
        "kind": "features",
        "path": str(path.relative_to(tmp_path)),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    _, frame = review.selected_file(tmp_path, entry, "2021-05-01", "features")
    assert frame.x.iloc[0] == 1
    path.write_bytes(data.replace(b",1\n", b",2\n"))
    with pytest.raises(ValueError, match="content hash"):
        review.selected_file(tmp_path, entry, "2021-05-01", "features")
    with pytest.raises(ValueError, match="feature store"):
        review.selected_file(tmp_path, entry | {"path": "../outside.csv"}, "2021-05-01", "features")


def test_descriptions_preserve_missing_values_and_zero_without_imputation(review):
    rows = pd.DataFrame(
        [
            {
                "grid_id": "A",
                "prediction_timestamp_utc": "2021-05-01T00:00:00+00:00",
                **dict.fromkeys(review.join.feature_names(), 0.0),
            },
            {
                "grid_id": "B",
                "prediction_timestamp_utc": "2021-05-01T00:00:00+00:00",
                **dict.fromkeys(review.join.feature_names(), float("nan")),
            },
        ]
    )
    keys = {("A", "2021-05-01T00:00:00+00:00"), ("B", "2021-05-01T00:00:00+00:00")}
    r = review.describe(rows, keys)
    assert r["complete_27_feature_rows"] == 1
    assert all(v["missing"] == 1 and v["median"] == 0 for v in r["features"].values())
    assert rows.iloc[1][review.join.feature_names()].isna().all()
    with pytest.raises(ValueError, match="unique feature rows"):
        review.describe(pd.concat([rows, rows]), keys)
