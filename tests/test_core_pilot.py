import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from wildfire_risk_prediction.core_pilot import (
    expected_pairs_for_day,
    scan_shapes,
    source_progress,
    window_geometry,
)

SPEC = importlib.util.spec_from_file_location(
    "pilot_area_test", Path(__file__).parents[1] / "scripts/firms/estimate_l2_observed_area.py"
)
area = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(area)


def test_missing_source_is_explicit_and_never_admits_a_negative():
    result = source_progress(["one", "two"], ["one"])
    assert result["missing_pairs"] == ["two"]
    assert not result["all_planned_pairs_processed"]
    assert not result["negative_label_permitted"]
    full = source_progress(["one", "two"], ["two", "one"])
    assert full["all_planned_pairs_processed"] and full["daily_observation_status"] == "unknown"
    assert not full["negative_label_permitted"]


@pytest.mark.parametrize(
    "expected,done",
    [([], []), (["one", "one"], []), (["one"], ["one", "one"]), (["one"], ["other"])],
)
def test_wrong_or_duplicate_source_scope_fails(expected, done):
    with pytest.raises(ValueError):
        source_progress(expected, done)


def scans():
    return pd.DataFrame(
        {
            "grid_id": ["G", "G"],
            "scan_id": ["a", "b"],
            "orbit_id": ["SNPP:1", "SNPP:2"],
            "start_utc": ["2018-02-14T01:00:00Z", "2018-02-14T13:00:01Z"],
            "end_utc": ["2018-02-14T01:00:01Z", "2018-02-14T13:00:02Z"],
        }
    )


def test_previous_day_scan_area_cannot_enter_next_target_day():
    result, geometry = window_geometry(
        scans(), [box(0, 0, 1, 1)] * 2, box(0, 0, 2, 2), "2018-02-15"
    )
    assert result["loaded_outside_scan_count"] == 2
    assert geometry.is_empty and result["loaded_inside_area_m2"] == 0
    assert not result["negative_label_permitted"]


def test_partial_source_time_repeat_requires_common_ground_and_distinct_orbit():
    result, union = window_geometry(
        scans(), [box(0, 0, 2, 1), box(1, 0, 3, 1)], box(0, 0, 3, 1), "2018-02-14"
    )
    assert union.area == 3
    assert result["loaded_repeat_12h_area_m2"] == 1
    assert not result["negative_label_permitted"]


def test_empty_loaded_data_preserves_unknown():
    frame = scans().iloc[:0]
    result, shape = window_geometry(frame, [], box(0, 0, 1, 1), "2018-02-15")
    assert result["loaded_inside_scan_count"] == 0 and shape.is_empty
    assert result["daily_observation_status"] == "unknown"
    assert not result["negative_label_permitted"]


def test_midnight_boundary_does_not_become_definite_area():
    frame = scans().iloc[:1].copy()
    frame.loc[0, "start_utc"] = "2018-02-14T23:59:59Z"
    frame.loc[0, "end_utc"] = "2018-02-15T00:00:01Z"
    result, shape = window_geometry(frame, [box(0, 0, 1, 1)], box(0, 0, 2, 2), "2018-02-15")
    assert shape.is_empty and result["loaded_boundary_area_m2"] == 1
    assert result["loaded_boundary_scan_count"] == 1


@pytest.mark.parametrize("day", ["2024-02-15", "2025-02-15"])
def test_holdout_cannot_enter_method_pilot(day):
    with pytest.raises(ValueError):
        window_geometry(scans(), [box(0, 0, 1, 1)] * 2, box(0, 0, 2, 2), day)


class Identity:
    def transform(self, x, y):
        return x, y


def test_scan_geometry_conserves_holes_classes_and_zero_cells():
    lon = np.tile(np.arange(4), (32, 1)).astype(float)
    lat = np.tile(np.arange(32).reshape(-1, 1), (1, 4)).astype(float)
    mask = np.full(lon.shape, 5, dtype="uint8")
    qa = np.zeros(lon.shape, dtype="uint32")
    regions = np.array([box(0, 0, 3, 31), box(50, 50, 51, 51)], dtype=object)
    args = (regions, Identity(), area.interior_corners, area.audit.diagnostic_land)
    result = scan_shapes(lon, lat, mask, qa, *args)
    assert result["reconstructed_domain"][0].area == 60
    assert result["nominal_nonfire_land"][0].area == 60
    assert result["cloud"][0].is_empty
    assert all(shapes[1].is_empty for shapes in result.values())
    mask[:] = 4
    cloudy = scan_shapes(lon, lat, mask, qa, *args)
    assert cloudy["nominal_nonfire_land"][0].is_empty and cloudy["cloud"][0].area == 60
    lon[:, 1] = np.nan
    assert scan_shapes(lon, lat, mask, qa, *args)["cloud"][0].area < 60


def test_neighbour_scope_uses_all_three_days_without_holdout_reads():
    pairs = [
        {"sample_id": str(i), "source_day": day}
        for i, day in enumerate(
            ["2018-02-13", "2018-02-14", "2018-02-15", "2018-02-16", "2018-02-17"]
        )
    ]
    assert expected_pairs_for_day(pairs, "2018-02-15") == ["1", "2", "3"]
    with pytest.raises(ValueError):
        expected_pairs_for_day(pairs, "2025-02-15")
