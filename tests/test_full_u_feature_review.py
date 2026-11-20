import importlib.util
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box


@pytest.fixture
def review(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "full_u_test", folder / "prepare_full_u_feature_review.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_province_support_keeps_two_positive_areas_but_not_boundary_touches(review):
    grid = gpd.GeoDataFrame(
        {"grid_id": ["A", "B"]}, geometry=[box(0, 0, 2, 1), box(2, 0, 3, 1)], crs=6933
    )
    provinces = gpd.GeoDataFrame(
        {"GAUL1_NAME": ["left", "right", "touch_only"]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 3, 1), box(0, 1, 3, 2)],
        crs=6933,
    )
    support = review.province_support(grid, provinces)
    assert list(zip(support.grid_id, support.province, strict=True)) == [
        ("A", "left"),
        ("A", "right"),
        ("B", "right"),
    ]
    assert support.groupby("grid_id").fraction_of_grid_aoi_area.sum().eq(1).all()
    with pytest.raises(ValueError, match="equal-area"):
        review.province_support(grid.to_crs(4326), provinces)


def toy(review):
    sample = pd.DataFrame(
        {
            "grid_id": ["B", "A"],
            "prediction_timestamp_utc": ["2021-06-01T00:00:00+00:00"] * 2,
            "population_index": [2, 1],
            "sampling_weight": [2574.0] * 2,
            "sampling_probability": [0.0003] * 2,
            "review_role": ["U_unknown_not_negative"] * 2,
            "target": [np.nan] * 2,
            "daily_observation_status": ["unknown"] * 2,
        }
    )
    features = sample[review.join.KEYS].copy()
    for field in review.join.feature_names():
        features[field] = [0.0, np.nan]
    support = pd.DataFrame({"grid_id": ["A", "A", "B"], "province": ["left", "right", "right"]})
    return sample, features, support


def test_inspection_preserves_sample_order_weights_zero_missing_and_border_memberships(review):
    sample, features, support = toy(review)
    result = review.inspection_table(sample, features, support)
    pd.testing.assert_frame_equal(result[sample.columns], sample)
    assert result.province_support.tolist() == ["right", "left|right"]
    assert result.missing_feature_count.tolist() == [0, 27]
    pd.testing.assert_frame_equal(result[features.columns], features)


@pytest.mark.parametrize("change", ["missing_key", "duplicate_key", "known_Y", "missing_province"])
def test_no_silent_drop_or_label_admission(review, change):
    sample, features, support = toy(review)
    if change == "missing_key":
        features = features.iloc[:1]
    elif change == "duplicate_key":
        features = pd.concat([features, features.iloc[:1]])
    elif change == "known_Y":
        sample.loc[0, "target"] = 0
    else:
        support = support.loc[support.grid_id.ne("B")]
    with pytest.raises(ValueError):
        review.inspection_table(sample, features, support)
