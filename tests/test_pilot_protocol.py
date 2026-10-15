import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from wildfire_risk_prediction.pilot_protocol import unit_evidence


def scans(hours, ends=None):
    ends = ends or [h + 0.01 for h in hours]
    t = pd.Timestamp("2021-05-15", tz="UTC")
    return pd.DataFrame(
        {
            "grid_id": ["g"] * len(hours),
            "scan_id": [str(i) for i in range(len(hours))],
            "orbit_id": ["SNPP:1"] * len(hours),
            "start_utc": [(t + pd.Timedelta(h, unit="h")).isoformat() for h in hours],
            "end_utc": [(t + pd.Timedelta(h, unit="h")).isoformat() for h in ends],
            "pixel_center_count": [1] * len(hours),
            "nominal_confidence_fire": [0] * len(hours),
            "high_confidence_fire": [0] * len(hours),
        }
    )


def test_full_daily_union_can_have_three_empty_time_bins_and_no_label():
    row, bins = unit_evidence(
        scans([1, 2]), np.array([box(0, 0, 1, 1)] * 2), box(0, 0, 1, 1), "2021-05-15"
    )
    assert row["nominal_land_daily_m2"] == 1
    assert row["nominal_land_all_four_bins_m2"] == 0
    assert [r["nominal_land_area_m2"] for r in bins] == [1, 0, 0, 0]
    assert row["nominal_land_sensor_orbit_count"] == 1
    assert row["target"] is None and row["negative_label_permitted"] is False


def test_different_parts_in_four_slots_do_not_prove_same_place_repeat():
    shapes = np.array([box(i, 0, i + 1, 1) for i in range(4)])
    row, bins = unit_evidence(scans([1, 7, 13, 19]), shapes, box(0, 0, 4, 1), "2021-05-15")
    assert all(r["nominal_land_area_m2"] == 1 for r in bins)
    assert row["nominal_land_daily_m2"] == 4 and row["nominal_land_all_four_bins_m2"] == 0


def test_scan_crossing_bin_boundary_not_admitted_to_either_bin():
    row, bins = unit_evidence(
        scans([5.99], [6.01]), np.array([box(0, 0, 1, 1)]), box(0, 0, 1, 1), "2021-05-15"
    )
    assert row["nominal_land_daily_m2"] == 1
    assert row["internal_bin_boundary_land_m2"] == 1
    assert sum(r["nominal_land_area_m2"] for r in bins) == 0


def test_day_boundary_thermal_count_kept_separate():
    frame = scans([0, 1], [0.01, 1.01])
    frame["nominal_confidence_fire"] = 1
    row, bins = unit_evidence(frame, np.array([box(0, 0, 1, 1)] * 2), box(0, 0, 1, 1), "2021-05-15")
    assert row["thermal_center_definite_count"] == row["thermal_center_boundary_count"] == 1
    assert row["thermal_center_outside_loaded_count"] == 0


def test_no_usable_land_has_full_day_gap_even_when_geometry_arrays_present():
    row, bins = unit_evidence(
        scans([1]), np.array([box(0, 0, 0, 0).buffer(0)]), box(0, 0, 1, 1), "2021-05-15"
    )
    assert row["anypart_land_longest_envelope_gap_seconds"] == 86400
    assert row["nominal_land_sensor_orbit_count"] == 0


def test_four_full_bins_still_does_not_create_a_negative_label():
    row, bins = unit_evidence(
        scans([1, 7, 13, 19]), np.array([box(0, 0, 1, 1)] * 4), box(0, 0, 1, 1), "2021-05-15"
    )
    assert row["nominal_land_all_four_bins_fraction"] == 1
    assert row["anypart_land_longest_envelope_gap_seconds"] > 5 * 3600
    assert row["target"] is None


@pytest.mark.parametrize(
    "change", ["duplicate", "count", "overflow", "outside_geometry", "holdout"]
)
def test_invalid_source_or_holdout_is_rejected(change):
    frame = scans([1, 7])
    shapes = np.array([box(0, 0, 1, 1)] * 2)
    day = "2021-05-15"
    if change == "duplicate":
        frame["scan_id"] = "same"
    if change == "count":
        frame["nominal_confidence_fire"] = 0.5
    if change == "overflow":
        frame["nominal_confidence_fire"] = 2
    if change == "outside_geometry":
        shapes[0] = box(0, 0, 2, 1)
    if change == "holdout":
        day = "2025-05-15"
    with pytest.raises(ValueError):
        unit_evidence(frame, shapes, box(0, 0, 1, 1), day)
