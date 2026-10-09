"""Full-grid checkpoint and batching behavior; no live Earth Engine calls."""

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/landcover/prepare_vegetation_full_grid.py"
SPEC = importlib.util.spec_from_file_location("vegetation_full_grid", PATH)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def feature(key):
    return {"properties": {"grid_id": key, "aoi_area_km2": 1.0}}


def raw_fixture():
    spec = {"target": "2018-08-01"}
    raw = {
        "contract": spec,
        "grid_ids": ["A"],
        "window_days": 30,
        "available_at": None,
        "scene_ids": [],
        "scene_acquisition_utc": [],
        "properties": [{"grid_id": "A"}],
    }
    return spec, raw


def test_batches_cover_each_grid_once_independent_of_input_order():
    features = [feature(f"G{i:04}") for i in range(2899)]
    groups = runner.batches(features[::-1], 64)
    assert len(groups) == 46
    assert len(groups[-1]) == 19
    assert [f for group in groups for f in group] == features


@pytest.mark.parametrize(
    "features,size", [([], 64), ([feature("A")] * 2, 64), ([feature("A")], 65)]
)
def test_batches_reject_invalid_grid_or_size(features, size):
    with pytest.raises(ValueError):
        runner.batches(features, size)


def test_unsupported_checkpoint_reuses_without_network(tmp_path):
    spec, raw = raw_fixture()
    path = tmp_path / "cached.json"
    runner.save(path, raw)
    assert runner.extract(spec, [feature("A")], 30, path) == "reused"
    row = runner.validate_raw(raw, spec, [feature("A")], 30)[0]
    assert row["valid_area_m2"] == 0
    assert row["usage"] == "retrospective_candidate_only"


@pytest.mark.parametrize("kind", ["contract", "ids", "duplicate", "future", "release"])
def test_cached_corruption_or_future_source_fails_closed(kind):
    spec, original = raw_fixture()
    raw = deepcopy(original)
    if kind == "contract":
        raw["contract"]["target"] = "2018-08-02"
    elif kind == "ids":
        raw["grid_ids"] = ["B"]
    elif kind == "duplicate":
        raw["properties"] *= 2
    elif kind == "future":
        raw["scene_ids"] = ["scene"]
        raw["scene_acquisition_utc"] = ["2018-08-01T00:00:00Z"]
    else:
        raw["available_at"] = "2018-07-31T12:00:00Z"
    with pytest.raises(ValueError):
        runner.validate_raw(raw, spec, [feature("A")], 30)


def test_final_test_cutoff_rejected_before_authentication():
    with pytest.raises(ValueError):
        runner.contract("2025-08-01", 64)
