"""Test closed permissions, temporal spillovers and review-only population slicing."""

import copy
import importlib.util
import json
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Point, box


@pytest.fixture
def pilot(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "source_pu_protocol_test", folder / "prepare_source_conditioned_pu_protocol.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def policy(pilot):
    return json.loads(pilot.POLICY.read_bytes())


@pytest.mark.parametrize(
    "flag",
    [
        "new_L_memberships_permitted",
        "WF1538_retention_overridden",
        "positive_label_permitted",
        "negative_label_permitted",
        "training_authorized",
        "final_merge_permitted",
        "2025_final_values_read_permitted",
    ],
)
def test_preparation_direction_cannot_open_label_or_execution_gates(pilot, policy, flag):
    altered = copy.deepcopy(policy)
    altered[flag] = True
    with pytest.raises(ValueError, match="scientific gates"):
        pilot.validate_policy(altered)


@pytest.mark.parametrize(
    "section,flag",
    [
        ("geometry_diagnostics", "radii_are_measured_location_error_bounds"),
        ("geometry_diagnostics", "all_intersected_cells_are_positive"),
        ("time_diagnostics", "select_clock_using_satellite_match"),
        ("time_diagnostics", "source_clock_is_first_satellite_detection"),
        ("U_domain_diagnostic", "unknown_is_negative"),
        ("U_domain_diagnostic", "drop_overlaps_with_source_keys"),
        ("U_domain_diagnostic", "geographic_overlap_proves_shared_class_conditionals"),
    ],
)
def test_hypotheses_cannot_be_promoted_to_truth_or_assumption_validation(
    pilot, policy, section, flag
):
    policy[section][flag] = True
    with pytest.raises(ValueError):
        pilot.validate_policy(policy)


def test_approved_config_stays_preparation_only(pilot, policy):
    pilot.validate_policy(policy)
    policy["mixture_requirements"]["beta"] = 0.8
    with pytest.raises(ValueError, match="No rate estimates"):
        pilot.validate_policy(policy)


def test_changed_decision_parent_or_unbounded_scenario_is_rejected(pilot, policy):
    policy["decision_parent_sha256"] = "other_parent"
    with pytest.raises(ValueError, match="reviewed parent"):
        pilot.validate_policy(policy)
    policy["decision_parent_sha256"] = pilot.PARENT_SHA
    policy["time_diagnostics"]["day_shifts"].append(365)
    with pytest.raises(ValueError, match="time alternatives"):
        pilot.validate_policy(policy)


def test_day_shifts_keep_outside_fit_alternatives_flagged(pilot):
    first = pilot.shifted_windows("2018-01-01T00:00:00+00:00", [-1, 0, 1])
    assert [x["inside_fit"] for x in first] == [False, True, True]
    last = pilot.shifted_windows("2022-12-30T00:00:00+00:00", [-1, 0, 1])
    assert [x["inside_fit"] for x in last] == [True, True, False]
    assert last[-1]["window_start_utc"].startswith("2022-12-31")


@pytest.mark.parametrize(
    "stamp",
    [
        "2023-01-01T00:00:00+00:00",
        "2025-01-01T00:00:00+00:00",
        "2021-05-01T12:00:00+00:00",
        "2021-05-01T00:00:00",
    ],
)
def test_source_window_must_be_fit_midnight_utc(pilot, stamp):
    with pytest.raises(ValueError):
        pilot.shifted_windows(stamp, [-1, 0, 1])


def test_buffer_across_cell_boundary_expands_geometry_without_cell_selection(pilot):
    grid = gpd.GeoDataFrame(
        {"grid_id": ["A", "B"]},
        geometry=[box(0, 0, 5000, 5000), box(5000, 0, 10000, 5000)],
        crs=6933,
    )
    result = pilot.spatial_options(Point(4990, 2500), grid, [0, 250, 1000])
    assert [x["grid_ids"] for x in result] == [["A"], ["A", "B"], ["A", "B"]]


def test_outside_point_is_not_forced_and_zero_area_touch_is_not_a_buffer_cell(pilot):
    grid = gpd.GeoDataFrame({"grid_id": ["A"]}, geometry=[box(0, 0, 5000, 5000)], crs=6933)
    result = pilot.spatial_options(Point(-250, 2500), grid, [0, 250, 1000])
    assert [x["grid_ids"] for x in result] == [[], [], ["A"]]


def u_row(grid="A", **changes):
    return {
        "grid_id": grid,
        "prediction_timestamp_utc": "2021-05-01T00:00:00+00:00",
        "target": "",
        "daily_observation_status": "unknown",
        **changes,
    }


def test_geographic_slice_keeps_source_overlap_and_copies_rows_without_changing_original(pilot):
    original = [u_row("A"), u_row("B")]
    before = copy.deepcopy(original)
    result = pilot.domain_slice(original, {"A"})
    assert result == [original[0]] and original == before
    assert result[0] is not original[0]
    assert result[0]["target"] == ""


@pytest.mark.parametrize(
    "stamp",
    [
        "2023-01-01T00:00:00+00:00",
        "2024-01-01T00:00:00+00:00",
        "2025-01-01T00:00:00+00:00",
        "2022-12-31T00:00:00+00:00",
    ],
)
def test_u_role_is_checked_before_any_other_context(pilot, stamp):
    with pytest.raises(ValueError, match="Fit U"):
        pilot.domain_slice([{"prediction_timestamp_utc": stamp}], {"A"})


@pytest.mark.parametrize("target", [0, "0", 1, "1"])
def test_u_cannot_already_have_a_binary_target(pilot, target):
    with pytest.raises(ValueError, match="U remains unknown"):
        pilot.domain_slice([u_row(target=target)], {"A"})


def test_duplicate_u_keys_are_not_silently_deduplicated(pilot):
    with pytest.raises(ValueError, match="Unique frozen U"):
        pilot.domain_slice([u_row(), u_row()], {"A"})


def test_cell_multiplicity_preserves_counts_and_survives_json_roundtrip(pilot):
    cases = [
        {
            "diagnostic_focus": True,
            "spatial_alternatives": [{"radius_projection_plane_m": 250, "grid_ids": ids}],
        }
        for ids in (["A"], ["B"], ["A", "B"], [])
    ] + [{"diagnostic_focus": False, "spatial_alternatives": []}]
    result = pilot.cell_multiplicity(cases, [250])
    assert result == {"250": {"0": 1, "1": 2, "2": 1}}
    assert json.loads(json.dumps(result)) == result
    assert sum(result["250"].values()) == 4


def test_dependency_blocks_are_transitive_but_do_not_merge_or_label_source_records(pilot):
    def case(name, cells):
        return {
            "archive_row": name,
            "diagnostic_focus": True,
            "spatial_alternatives": [{"radius_projection_plane_m": 1000, "grid_ids": cells}],
            "temporal_alternatives": [
                {"inside_fit": True, "window_start_utc": "2021-05-01T00:00:00+00:00"}
            ],
        }

    cases = [
        case("A", ["left"]),
        case("B", ["left", "right"]),
        case("C", ["right"]),
        case("D", ["other"]),
    ]
    original = copy.deepcopy(cases)
    result = pilot.plausible_key_dependencies(cases)
    assert result["multiple_source_record_blocks"] == [["A", "B", "C"]]
    assert result["all_hypothesis_components"] == 2
    assert not result["components_are_independent_physical_fires"]
    assert (
        not result["source_records_merged_or_deleted"] and not result["fold_assignment_performed"]
    )
    assert cases == original


def test_outside_fit_hypotheses_and_retained_wf1538_do_not_create_dependency_links(pilot):
    base = {
        "diagnostic_focus": True,
        "spatial_alternatives": [{"radius_projection_plane_m": 1000, "grid_ids": ["A"]}],
        "temporal_alternatives": [
            {"inside_fit": False, "window_start_utc": "2023-01-01T00:00:00+00:00"}
        ],
    }
    result = pilot.plausible_key_dependencies(
        [
            base | {"archive_row": "one"},
            base | {"archive_row": "two"},
            {"archive_row": "WF1538", "diagnostic_focus": False},
        ]
    )
    assert result["all_hypothesis_components"] == 2
    assert result["multiple_source_record_blocks"] == []
