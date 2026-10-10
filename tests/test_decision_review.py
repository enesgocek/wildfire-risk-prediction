import json

import pandas as pd
import pytest

from wildfire_risk_prediction.decision_review import (
    event_cases,
    habitat_cases,
    support_intersection,
)


def habitat():
    return pd.DataFrame(
        {
            "grid_id": ["a", "b", "c"],
            "habitat_eligibility": ["undecided"] * 3,
            "negative_label_permitted": [False] * 3,
            "aoi_area_km2": [1, 2, 3],
            "covered_area_km2": [0.5, 1.5, 2.5],
            "forest_fraction": [0.5, 0.1, 0.0],
            "shrub_fraction": [0.2, 0.1, 0.0],
            "natural_vegetation_fraction": [0.8, 0.3, 0.0],
            "forest_shrub_fraction": [0.7, 0.2, 0.0],
            "agriculture_fraction": [0.1, 0.7, 0.0],
            "water_only_flag": [False, False, True],
            "terrain_area_review_flag": [True, False, False],
        }
    )


def coverage():
    return pd.DataFrame(
        {
            "grid_id": ["c", "a", "b"],
            "training_min_coverage": [1, 0, 0.8],
            "training_max_coverage": [1, 0, 0.8],
        }
    )


def test_intersection_keeps_distinct_area_denominators_and_inclusive_threshold():
    source = habitat()
    table, groups, scenarios = support_intersection(source, coverage())
    assert table.grid_id.tolist() == ["a", "b", "c"]
    assert groups[0]["aoi_area_km2"] == 1
    assert groups[0]["forest_class_area_km2"] == 0.25  # covered raster area, not AOI.
    assert sum(g["cells"] for g in groups) == 3
    entry = next(
        s
        for s in scenarios
        if s["measure"] == "forest_fraction" and s["threshold_inclusive"] == 0.1
    )
    assert entry["cells"] == 2 and entry["weather_none_cells"] == 1
    assert table.habitat_eligibility.eq("undecided").all()


def test_diagnostic_requires_known_invariant_weather_keys():
    weather = coverage()
    weather.loc[0, "grid_id"] = "bad"
    with pytest.raises(ValueError):
        support_intersection(habitat(), weather)
    weather = coverage()
    weather.loc[0, "training_min_coverage"] = 0.1
    with pytest.raises(ValueError, match="invariant"):
        support_intersection(habitat(), weather)


def test_habitat_case_reasons_overlap_without_duplicate_rows():
    table, _, _ = support_intersection(habitat(), coverage())
    cases = habitat_cases(table)
    assert cases.grid_id.is_unique and len(cases) == 3
    assert "terrain_area_review" in json.loads(cases.iloc[0].selection_reasons_json)
    assert cases.sampling.eq("purposive_review_not_representative").all()


def test_event_cases_order_stable_and_no_event_decision():
    frame = pd.DataFrame(
        {
            "cluster_id": ["a", "b", "c"],
            "first_detection_utc": ["2018-06-01T12:00:00Z"] * 3,
            "event_status": ["exploratory_cluster_only"] * 3,
            "duration_hours": [30, 30, 0],
            "max_distance_from_canonical_first_m": [600, 10, 0],
            "earliest_grid_count": [2, 1, 1],
            "temporal_chain_review": [True, True, False],
            "spatial_chain_review": [True, False, False],
            "multi_grid_first_detection_review": [True, False, False],
            "calendar_year_crossing_review": [False] * 3,
            "period_start_context_missing": [False] * 3,
            "period_end_context_missing": [False] * 3,
        }
    )
    a = event_cases(frame)
    b = event_cases(frame.iloc[::-1])
    pd.testing.assert_frame_equal(a, b)
    assert a.cluster_id.tolist() == ["a", "c"]
    assert a.event_status.eq("exploratory_cluster_only").all()
    assert len(json.loads(a.iloc[0].selection_reasons_json)) == 3


def test_holdout_case_input_rejected():
    frame = pd.DataFrame(
        {
            "cluster_id": ["a"],
            "event_status": ["exploratory_cluster_only"],
            "first_detection_utc": ["2024-01-01T01:00:00Z"],
        }
    )
    with pytest.raises(ValueError, match="Training"):
        event_cases(frame)
