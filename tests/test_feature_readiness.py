"""Saved values/provenance must reject leakage and distinguish joint missingness from marginals."""

import pandas as pd
import pytest
from test_feature_join import sources as sources

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.feature_readiness import inspect_day


def saved(sources):
    weather, static, vegetation, ids, day = sources
    features, qa = join.join_day(weather, static, vegetation, ids, day)
    return features, qa, ids, day, static


def test_joint_missingness_preserves_zero_and_aligns_keys(sources):
    features, qa, ids, day, static = saved(sources)
    features.loc[features.grid_id.eq("g1"), "temperature_mean_c"] = 0.0
    result = inspect_day(features, qa.iloc[::-1], ids, day, static.iloc[::-1])
    assert result["complete_27_feature_rows"] == 1
    assert sum(result["joint_missing_family_counts"]) == 2
    assert result["joint_missing_family_counts"][1 + 4 + 8] == 1
    assert result["missing_by_feature"]["temperature_mean_c"] == 1
    assert result["eligible_labeled_rows"] is None
    assert result["publication_availability_verified"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("weather_source_last_timestamp_utc", "2018-08-01T00:00:00Z"),
        ("weather_available_at", "2018-08-01T00:00:00Z"),
        ("vegetation_30d_source_acquisition_latest_utc", "2018-08-01T00:00:00Z"),
        ("vegetation_60d_snapshot_age_days", 9.0),
        ("weather_primary_eligible", False),
        ("vegetation_30d_available_at", "2018-08-01T00:00:00Z"),
    ],
)
def test_leakage_and_invented_quality_rejected(sources, field, value):
    features, qa, ids, day, static = saved(sources)
    qa.loc[qa.grid_id.eq("g1"), field] = value
    with pytest.raises((ValueError, AssertionError)):
        inspect_day(features, qa, ids, day, static)


def test_changed_static_and_missing_support_fill_rejected(sources):
    features, qa, ids, day, static = saved(sources)
    features.loc[features.grid_id.eq("g1"), "forest_fraction"] = 0.0
    with pytest.raises(AssertionError):
        inspect_day(features, qa, ids, day, static)
    features, qa, ids, day, static = saved(sources)
    features.loc[features.grid_id.eq("g2"), "vegetation_30d_ndvi_median_mean"] = 0.0
    with pytest.raises(ValueError, match="support disagreement"):
        inspect_day(features, qa, ids, day, static)


def test_future_split_and_target_column_rejected(sources):
    features, qa, ids, day, static = saved(sources)
    features["target"] = pd.NA
    with pytest.raises(ValueError, match="allowlist"):
        inspect_day(features, qa, ids, day, static)
    features = features.drop(columns="target")
    with pytest.raises(ValueError, match="Training only"):
        inspect_day(features, qa, ids, "2025-01-01", static)
