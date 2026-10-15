import importlib.util
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

SPEC = importlib.util.spec_from_file_location(
    "core_spatial", Path(__file__).parents[1] / "scripts/quality/review_observation_core_pair.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def parent(tmp_path, **changes):
    report = {
        "status": "one_pair_bytes_and_headers_passed",
        "sample_id": "SNPP:2018045.0000",
        "plan_sha256": "a" * 64,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "labels_created": False,
        **changes,
    }
    module.write_json(tmp_path / "native_probe.json", report)
    sha = module.digest(tmp_path / "native_probe.json")
    module.write_json(tmp_path / "completion_readback.json", {"report_sha256": sha})
    module.write_json(
        tmp_path / "launcher_receipt.json", {"status": "child_completed", "plan_sha256": "a" * 64}
    )
    return sha


@pytest.mark.parametrize(
    "changes",
    [
        {"sample_id": "SNPP:2025045.0000"},
        {"negative_label_permitted": True},
        {"labels_created": True},
        {"daily_observation_status": "observed"},
        {"status": "failed_outputs_retained"},
    ],
)
def test_scope_and_scientific_permissions_cannot_be_widened(tmp_path, changes):
    sha = parent(tmp_path, **changes)
    with pytest.raises(ValueError, match="training-only"):
        module.accepted_parent(tmp_path, sha)


def test_unfinished_or_modified_native_parent_is_not_accepted(tmp_path):
    sha = parent(tmp_path)
    assert module.accepted_parent(tmp_path, sha)["labels_created"] is False
    (tmp_path / "launcher_receipt.json").write_text(
        json.dumps({"status": "failed_outputs_retained", "plan_sha256": "a" * 64})
    )
    with pytest.raises(ValueError, match="training-only"):
        module.accepted_parent(tmp_path, sha)
    (tmp_path / "native_probe.json").write_text("{}")
    with pytest.raises(ValueError, match="Pinned native"):
        module.accepted_parent(tmp_path, sha)


def test_csv_preserves_granule_key_zeroes_and_detects_numeric_corruption(tmp_path):
    frame = pd.DataFrame({"pair_key": ["2018045.0000"], "count": [123], "valid": [False]})
    path = tmp_path / "table.csv"
    frame.to_csv(path, index=False)
    assert module.read_table(path, frame).pair_key.iloc[0] == "2018045.0000"
    frame.assign(count=124).to_csv(path, index=False)
    with pytest.raises(ValueError, match="numeric values"):
        module.read_table(path, frame)


def test_equal_area_geometry_at_wrong_location_is_rejected(tmp_path):
    parts = gpd.GeoDataFrame({"grid_id": ["one"]}, geometry=[box(0, 0, 10, 10)], crs=6933)
    table = pd.DataFrame({"grid_id": ["one"], "land_area_estimate_m2": [25.0]})
    saved = gpd.GeoDataFrame({"grid_id": ["one"]}, geometry=[box(20, 20, 25, 25)], crs=6933)
    path = tmp_path / "test.gpkg"
    saved.to_file(path, layer="land", driver="GPKG", index=False)
    with pytest.raises(ValueError, match="inside AOI"):
        module.verify_geometry(path, table, parts, ["land"])


def test_existing_receipt_is_never_overwritten(tmp_path):
    path = tmp_path / "receipt.json"
    module.write_json(path, {"status": "first"})
    with pytest.raises(ValueError, match="overwrite"):
        module.write_json(path, {"status": "second"})
    assert json.loads(path.read_text())["status"] == "first"
