import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def audit():
    path = Path(__file__).resolve().parents[1] / "scripts/quality/audit_antalya_annual_reference.py"
    spec = importlib.util.spec_from_file_location("annual_source_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inspect(audit, rows, **extra):
    args = dict(
        date_field="time",
        year=2018,
        longitude="30.96",
        latitude="36.93",
        source_role="reported_central_feature_record",
    )
    return audit.inspect_rows(rows, **(args | extra))


def test_skips_nonfit_values_before_coordinates(audit):
    rows = [
        {"time": f"{year}-05-01", "longitude": "must_not_be_parsed"}
        for year in (2013, 2019, 2023, 2024, 2025)
    ]
    result = inspect(audit, rows)
    assert result["year_rows_examined"] == 0
    assert all(b["matched_detection_rows"] == 0 for b in result["conditional_boxes"])
    assert result["target"] is None and not result["negative_label_permitted"]


def test_boundary_sensitivity_and_multiple_days_do_not_select_event_day(audit):
    rows = [
        {"time": "2018-05-01T12:00:00Z", "longitude": "30.965", "latitude": "36.935"},
        {"time": "2018-05-02", "longitude": "30.97", "latitude": "36.94"},
        {"time": "2018-05-03", "longitude": "30.9701", "latitude": "36.93"},
    ]
    result = inspect(audit, rows)
    small, large = result["conditional_boxes"]
    assert result["year_rows_examined"] == 3
    assert small["matched_detection_rows"] == 1
    assert large["matched_detection_rows"] == 2
    assert len(large["matched_catalogue_dates"]) == 2
    assert not large["dates_are_source_event_dates"]
    assert not large["is_total_location_error_bound"]
    assert result["source_event_day"] is None and result["target"] is None
    assert not result["same_physical_event_verified"]


@pytest.mark.parametrize("role", ["mean_center", "median_center", "village_center", "unknown"])
def test_aggregate_or_unknown_source_role_rejected(audit, role):
    with pytest.raises(ValueError, match="Aggregate centers"):
        inspect(audit, [], source_role=role)


@pytest.mark.parametrize("year", [2013, 2023, 2024, 2025, True])
def test_later_roles_and_nonfit_reference_years_rejected(audit, year):
    with pytest.raises(ValueError, match="Fit-role"):
        inspect(audit, [], year=year)


@pytest.mark.parametrize("coordinate", ["NaN", "Infinity", "45"])
def test_invalid_conditional_source_coordinates_rejected(audit, coordinate):
    with pytest.raises(ValueError):
        inspect(audit, [], longitude=coordinate)


def test_invalid_retained_date_fails_before_matching(audit):
    with pytest.raises(ValueError):
        inspect(audit, [{"time": "2018-invalid", "longitude": "30.96", "latitude": "36.93"}])
