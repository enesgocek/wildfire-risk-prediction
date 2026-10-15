import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "completed_review",
    Path(__file__).parents[1] / "scripts/quality/review_completed_observation_pilot.py",
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def example():
    units = pd.DataFrame([{"review_unit_id": "one", "grid_id": "g1", "target_day": "2021-05-15"}])
    row = {
        **units.iloc[0].to_dict(),
        "target": None,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "full_daily_observation_proven": False,
        "all_planned_pairs_processed": True,
        "missing_pair_count": 0,
        "missing_pairs_json": "[]",
        "expected_pair_count": 2,
        "completed_pair_count": 2,
        "required_geometry_pair_count": 2,
        "outside_by_native_time_pair_count": 1,
        "reference_neighbour_pair_count": 3,
        "loaded_scan_rows": 3,
        "loaded_inside_scan_count": 2,
        "loaded_boundary_scan_count": 0,
        "loaded_outside_scan_count": 1,
        "loaded_inside_area_m2": 80.0,
        "loaded_boundary_area_m2": 0.0,
        "loaded_repeat_1h_area_m2": 75.0,
        "loaded_repeat_6h_area_m2": 65.0,
        "loaded_repeat_12h_area_m2": 50.0,
    }
    for group, area in (
        ("reconstructed_domain", 100.0),
        ("nominal_nonfire_land", 80.0),
        ("cloud", 70.0),
    ):
        row[group + "_loaded_inside_m2"] = area
        row[group + "_loaded_boundary_m2"] = 0.0
    return (
        pd.DataFrame([row]),
        units,
        pd.Series({"g1": 100.0}),
        {"2021-05-15": ["p1", "p2"]},
        {"2021-05-15": ["p0"]},
    )


def test_cloud_and_land_unions_can_overlap_without_becoming_labelled():
    result = module.validate_summary(*example())
    assert result.nominal_land_fraction.iloc[0] == 0.8
    assert result.cloud_fraction.iloc[0] == 0.7
    assert result.target.isna().all() and not result.negative_label_permitted.any()


@pytest.mark.parametrize(
    "column,value",
    [
        ("target", 0),
        ("negative_label_permitted", True),
        ("full_daily_observation_proven", True),
        ("missing_pairs_json", '["p2"]'),
        ("expected_pair_count", 3),
        ("loaded_scan_rows", 4),
        ("loaded_inside_scan_count", 1.5),
        ("cloud_loaded_inside_m2", 101.0),
        ("nominal_nonfire_land_loaded_inside_m2", np.nan),
        ("loaded_repeat_12h_area_m2", 70.0),
        ("review_unit_id", "different"),
    ],
)
def test_invalid_scope_counts_areas_or_scientific_gates_are_rejected(column, value):
    args = example()
    args[0][column] = value
    with pytest.raises(ValueError):
        module.validate_summary(*args)
