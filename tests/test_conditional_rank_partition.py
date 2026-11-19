import copy
import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def proposal():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/quality/prepare_conditional_rank_partition.py"
    )
    spec = importlib.util.spec_from_file_location("rank_partition_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "stamp,expected",
    [
        ("2021-12-30T00:00:00+00:00", "proposed_fit_2018_2021"),
        ("2021-12-31T00:00:00+00:00", "boundary_review_not_used"),
        ("2022-01-01T00:00:00+00:00", "proposed_assessment_2022"),
        ("2022-12-31T00:00:00+00:00", "boundary_review_not_used"),
    ],
)
def test_right_closed_endpoints_and_role_boundary(proposal, stamp, expected):
    assert proposal.window_partition(stamp) == expected


def case(name, start, alternatives):
    return {
        "archive_row": name,
        "diagnostic_focus": True,
        "researcher_retained_outside_L": False,
        "target": None,
        "membership": "review_unassigned",
        "conditional_center_grid_ids": ["A"],
        "conditional_target_window_starts": [start],
        "temporal_alternatives": [{"window_start_utc": t} for t in alternatives],
    }


def test_crossing_alternative_purges_whole_proposed_dependency_component_without_mutation(proposal):
    one = case(
        "one",
        "2021-12-30T00:00:00+00:00",
        ["2021-12-29T00:00:00+00:00", "2021-12-31T00:00:00+00:00"],
    )
    two = case("two", "2021-12-29T00:00:00+00:00", ["2021-12-28T00:00:00+00:00"])
    cases = [one, two, {"diagnostic_focus": False}]
    before = copy.deepcopy(cases)
    keys, records = proposal.propose_sources(cases, [["one", "two"]])
    assert set(keys.values()) == set(records.values()) == {"boundary_review_not_used"}
    assert cases == before


def test_different_source_rows_at_same_key_remain_in_record_mapping(proposal):
    rows = [
        case(name, "2021-05-01T00:00:00+00:00", ["2021-05-01T00:00:00+00:00"])
        for name in ["one", "two"]
    ]
    keys, records = proposal.propose_sources(rows, [["one", "two"]])
    assert len(keys) == 1 and len(records) == 2


def test_duplicate_blocks_or_retention_override_are_rejected(proposal):
    row = case("one", "2021-05-01T00:00:00+00:00", ["2021-05-01T00:00:00+00:00"])
    with pytest.raises(ValueError, match="Nonoverlapping"):
        proposal.propose_sources([row], [["one"], ["one"]])
    with pytest.raises(ValueError, match="Retained source"):
        proposal.propose_sources([row | {"researcher_retained_outside_L": True}], [])


def test_nonmidnight_partition_metadata_is_rejected(proposal):
    with pytest.raises(ValueError, match="Midnight"):
        proposal.window_partition("2021-05-01T01:00:00+00:00")
