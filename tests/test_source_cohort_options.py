"""Protect unresolved source identity/time/geometry during cohort preparation."""

import importlib.util
from pathlib import Path

import geopandas as gpd
import pytest
from pyproj import Transformer
from shapely.geometry import box


@pytest.fixture
def cohort(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "cohort_options_test", folder / "prepare_source_cohort_options.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source(**changes):
    return {
        "event_id": "geography_id",
        "date": "2021-05-20",
        "year": "2021",
        "district": "A",
        "burned_area_ha": "1.0",
        "ignition_hour": "12",
        "longitude": "1",
        "latitude": "1",
        "coordinate_qc_pass": "True",
        **changes,
    }


def geometry():
    grid = gpd.GeoDataFrame(
        {"grid_id": ["left", "right"]}, geometry=[box(0, 0, 2, 2), box(2, 0, 4, 2)], crs=4326
    )
    return grid, box(0, 0, 4, 2), Transformer.from_crs(4326, 4326, always_xy=True)


def test_anonymous_id_difference_does_not_block_provisional_link_or_prove_identity(cohort):
    result = cohort.clock_options([source()], [source(event_id="different_clock_id")])[
        "geography_id"
    ]
    assert result["temporary_clock_signature_unique"]
    assert result["same_window_in_both_clock_hypotheses"]
    assert not result["physical_event_identity_verified"]
    assert not result["clock_standard_verified"]
    assert all(
        not w["is_admitted_first_satellite_detection_time"] for w in result["clock_hypotheses"]
    )


@pytest.mark.parametrize("duplicate_side", ["geography", "clock"])
def test_ambiguous_signature_does_not_choose_first_clock(cohort, duplicate_side):
    geography = [source()]
    clocks = [source(event_id="clock_id")]
    if duplicate_side == "geography":
        geography.append(source(event_id="other_geo"))
    else:
        clocks.append(source(event_id="other_clock", ignition_hour="1"))
    result = cohort.clock_options(geography, clocks)["geography_id"]
    assert not result["temporary_clock_signature_unique"]
    assert result["clock_hypotheses"] == []
    assert not result["same_window_in_both_clock_hypotheses"]


def test_two_possible_target_days_are_retained_without_clock_choice(cohort):
    result = cohort.clock_options([source()], [source(ignition_hour="2")])["geography_id"]
    assert result["conditional_target_window_starts"] == [
        "2021-05-19T00:00:00+00:00",
        "2021-05-20T00:00:00+00:00",
    ]
    assert not result["same_window_in_both_clock_hypotheses"]


def test_midnight_right_endpoint_keeps_previous_target_day(cohort):
    result = cohort.clock_options([source()], [source(ignition_hour="0")])["geography_id"]
    assert result["conditional_target_window_starts"] == ["2021-05-19T00:00:00+00:00"]


def test_window_crossing_fit_boundary_is_flagged_without_dropping_source(cohort):
    geo = source(date="2018-01-01", year="2018")
    row = cohort.assemble([geo], [geo | {"ignition_hour": "1"}], *geometry())[0]
    assert not row["all_clock_hypotheses_in_current_fit"]
    assert row["archive_row"] == geo["event_id"]
    assert row["membership"] == "review_unassigned" and row["target"] is None


@pytest.mark.parametrize("year", [2017, 2023, 2024, 2025])
def test_nonfit_source_rows_rejected_before_coordinates(cohort, year):
    row = source(year=str(year), date=f"{year}-05-20", longitude="not_to_be_parsed")
    with pytest.raises(ValueError, match="Fit-role"):
        cohort.assemble([row], [], *geometry())


def test_date_year_inconsistency_rejected(cohort):
    with pytest.raises(ValueError, match="Source year/date"):
        cohort.clock_options([source(date="2025-05-20")], [])


@pytest.mark.parametrize("changes", [{"longitude": "5"}, {"coordinate_qc_pass": "False"}])
def test_outside_or_qc_failed_source_is_never_forced_to_nearest_cell(cohort, changes):
    result = cohort.point_options(source(**changes), *geometry())
    assert result["conditional_center_grid_ids"] == []
    assert not result["point_forced_to_nearest_grid"]


def test_shared_cell_boundary_preserves_two_cells(cohort):
    row = cohort.assemble([source(longitude="2")], [source()], *geometry())[0]
    assert row["conditional_center_grid_ids"] == ["left", "right"]
    assert not row["metadata_transportable_under_center_and_clock_hypotheses"]
    assert row["target"] is None


def test_wf1538_explicit_retention_survives_otherwise_transportable_metadata(cohort):
    row = cohort.assemble([source(event_id="WF1538")], [source()], *geometry())[0]
    assert row["metadata_transportable_under_center_and_clock_hypotheses"]
    assert row["researcher_retained_outside_L"]
    assert row["membership"] == "review_unassigned" and row["target"] is None


def test_satellite_and_cover_results_do_not_affect_metadata_flags(cohort):
    base = source()
    poisoned = base | {"fire_detected": False, "forest_fraction": 0, "cloud_fraction": 1}
    assert cohort.assemble([base], [base], *geometry()) == cohort.assemble(
        [poisoned], [base], *geometry()
    )


def test_duplicate_geography_identifier_rejected(cohort):
    with pytest.raises(ValueError, match="Unique geography"):
        cohort.clock_options([source(), source(district="B")], [])


def test_distinct_source_rows_at_same_conditional_key_are_not_counted_as_distinct_fires(cohort):
    rows = [
        source(),
        source(event_id="other", burned_area_ha="2.0"),
        source(event_id="WF1538", burned_area_ha="3.0"),
    ]
    prepared = cohort.assemble(rows, rows, *geometry())
    result = cohort.summarize_key_collisions(prepared)
    assert result["source_rows"] == 2 and result["distinct_conditional_cell_days"] == 1
    assert result["shared_conditional_cell_days"][0]["source_rows"] == ["geography_id", "other"]
    assert not result["same_cell_day_proves_same_physical_event"]
    assert not result["source_records_deduplicated_or_merged"]
    assert len(prepared) == 3 and all(r["target"] is None for r in prepared)
