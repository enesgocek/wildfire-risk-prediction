"""Habitat diagnostics preserve uncertain cells and the correct area denominator."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.habitat_review import review_habitat
from wildfire_risk_prediction.landscape import CLASS_CODES


def row(key, forest=0.25, shrub=0.25, water=0.5):
    result = {f"lc_{code}_fraction": 0.0 for code in CLASS_CODES}
    result.update(
        {
            "grid_id": key,
            "reference_year": 2017,
            "covered_area_km2": 2,
            "lc_111_fraction": forest,
            "lc_20_fraction": shrub,
            "lc_200_fraction": water,
            "forest_fraction": forest,
            "shrub_fraction": shrub,
            "herbaceous_fraction": 0,
            "agriculture_fraction": 0,
            "urban_fraction": 0,
            "water_fraction": water,
            "unknown_fraction": 0,
            "natural_vegetation_fraction": forest + shrub,
            "aoi_area_m2": 3e6,
            "terrain_valid_area_m2": 3.03e6,
            "terrain_support_to_aoi_ratio": 1.01,
            "historical_available_at": None,
            "landcover_suitability_decided": False,
            "usage": "retrospective_candidate_features_only",
        }
    )
    return result


def test_preserves_water_only_cell_and_uses_raster_coverage_area():
    frame = pd.DataFrame([row("mixed"), row("water", 0, 0, 1)])
    original = frame.copy(deep=True)
    cells, report = review_habitat(frame, ["mixed", "water"])
    pd.testing.assert_frame_equal(frame, original)
    assert len(cells) == 2 and report["rows_removed"] == 0
    assert cells.habitat_eligibility.eq("undecided").all()
    assert not cells.negative_label_permitted.any()
    assert report["water_only_cells"] == 1
    assert report["class_area_km2_within_landcover_coverage"]["forest_fraction"] == 0.5
    assert report["landcover_covered_area_km2"] == 4
    assert report["aoi_area_km2"] == 6
    boundary = next(
        s
        for s in report["sensitivity"]
        if s["measure"] == "forest_fraction" and s["exploratory_threshold_inclusive"] == 0.25
    )
    assert boundary["cells_at_or_above"] == 1
    assert boundary["landcover_covered_area_km2_of_cells_at_or_above"] == 2
    assert report["threshold_selected"] is None
    assert report["labels_created"] is False
    assert report["habitat_eligibility_decided"] is False


def test_unknown_landcover_never_becomes_ineligible():
    unknown = row("unknown", 0, 0, 0)
    unknown.update(lc_0_fraction=1, unknown_fraction=1)
    cells, report = review_habitat(pd.DataFrame([unknown]), ["unknown"])
    assert report["unknown_cover_present_cells"] == 1
    assert cells.habitat_eligibility.iloc[0] == "undecided"
    assert all(s["cells_at_or_above"] == 0 for s in report["sensitivity"])


def test_boundary_area_review_does_not_clip_ratio_or_remove_cell():
    edge = row("edge")
    edge.update(terrain_valid_area_m2=3.18e6, terrain_support_to_aoi_ratio=1.06)
    cells, report = review_habitat(pd.DataFrame([edge]), ["edge"])
    assert cells.terrain_support_to_aoi_ratio.iloc[0] == 1.06
    assert report["terrain_area_review_cells"] == 1
    assert report["terrain_area_review_aoi_km2"] == 3
    assert report["rows_removed"] == 0


@pytest.mark.parametrize(
    "column,value",
    [
        ("aoi_area_m2", 0),
        ("aoi_area_m2", np.nan),
        ("terrain_valid_area_m2", -1),
        ("terrain_support_to_aoi_ratio", 0.5),
        ("forest_fraction", 0.75),
        ("lc_111_fraction", np.nan),
        ("lc_111_fraction", -0.1),
        ("landcover_suitability_decided", True),
        ("historical_available_at", "2020-01-01"),
        ("usage", "operational"),
    ],
)
def test_invalid_support_or_changed_contract_rejected(column, value):
    frame = pd.DataFrame([row("g")])
    frame[column] = value
    with pytest.raises(ValueError):
        review_habitat(frame, ["g"])


def test_empty_missing_and_duplicate_keys_rejected():
    for frame, ids in [
        (pd.DataFrame(), []),
        (pd.DataFrame([row("g")]), ["other"]),
        (pd.DataFrame([row("g"), row("g")]), ["g"]),
    ]:
        with pytest.raises(ValueError):
            review_habitat(frame, ids)


def load_script():
    path = Path(__file__).resolve().parents[1] / "scripts/landcover/review_habitat.py"
    spec = importlib.util.spec_from_file_location("habitat_review_script", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "change,error",
    [
        ({"final_test_accessed": True}, "scope"),
        ({"habitat_eligibility_decided": True}, "scope"),
        ({"table": "../../outside.csv"}, "path"),
        ({"table_sha256": "changed"}, "hash"),
    ],
)
def test_manifest_fail_closed_before_loading_table(tmp_path, monkeypatch, change, error):
    module = load_script()
    static = tmp_path / "data/interim/landscape/v1"
    static.mkdir(parents=True)
    manifest = {
        "version": "landscape_retro_v1",
        "grid_count": 2899,
        "final_test_accessed": False,
        "labels_created": False,
        "historical_availability_verified": False,
        "habitat_eligibility_decided": False,
        "table": "data/interim/landscape/v1/grid_static.csv",
        "table_sha256": "original",
        **change,
    }
    (static / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(module, "sha", lambda _: "original")

    def forbidden(*args, **kwargs):
        raise AssertionError("CSV read before manifest rejection")

    monkeypatch.setattr(module.pd, "read_csv", forbidden)
    with pytest.raises(ValueError, match=error):
        module.load_accepted_static(tmp_path)
