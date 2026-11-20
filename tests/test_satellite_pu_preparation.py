import importlib.util
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def prep():
    path = Path(__file__).resolve().parents[1] / "scripts/quality/audit_satellite_pu_preparation.py"
    spec = importlib.util.spec_from_file_location("sat_prep_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def toy():
    births = pd.DataFrame(
        {
            "birth_candidate_id": ["one"],
            "scenario": ["d1000m_t24h"],
            "first_detection_utc": ["2021-07-28T10:12:00+00:00"],
            "birth_detection_ids_json": ['["a","b","c"]'],
            "earliest_grid_ids_json": ['["A","B"]'],
            "target": [None],
        }
    )
    keys = pd.DataFrame(
        {
            "birth_candidate_id": ["one", "one"],
            "grid_id": ["A", "B"],
            "prediction_timestamp_utc": ["2021-07-28T00:00:00+00:00"] * 2,
            "fit_role_boundary_review": [False, False],
            "target": [None, None],
        }
    )
    points = pd.DataFrame(
        {
            "detection_id": ["a", "b", "c"],
            "grid_id": ["A", "A", "B"],
            "detection_timestamp_utc": ["2021-07-28T10:12:00+00:00"] * 3,
            "cgls_2017_center_context": ["forest_shrub", "agriculture", "forest_shrub"],
            "corine_2018_center_context": ["forest_shrub", "agriculture", "agriculture"],
        }
    )
    return births, keys, points


def test_mixed_first_centers_and_map_conflict_keep_all_initial_cells_without_labels(prep):
    result = prep.first_cell_context(*toy())
    assert result.grid_id.tolist() == ["A", "B"]
    assert result.first_center_count.tolist() == [2, 1]
    assert result.all_first_centers_woody_2017.tolist() == [False, True]
    assert result.any_first_center_woody_2017.tolist() == [True, True]
    assert result.all_first_centers_woody_both_maps.tolist() == [False, False]
    assert result.target.isna().all() and result.weak_positive_membership.isna().all()


@pytest.mark.parametrize("change", ["later_detection", "lost_first_cell"])
def test_later_centers_or_lost_first_cell_are_not_silently_substituted(prep, change):
    births, keys, points = toy()
    if change == "later_detection":
        points.loc[0, "detection_timestamp_utc"] = "2021-07-29T10:12:00+00:00"
    else:
        births["earliest_grid_ids_json"] = '["A"]'
    with pytest.raises(ValueError):
        prep.first_cell_context(births, keys, points)
