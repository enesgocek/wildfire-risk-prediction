import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def split(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "sat_split_test", folder / "prepare_satellite_pu_partition.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_boundary_target_window_is_not_accepted_into_either_role(split):
    assert split.period("2021-12-30T00:00:00+00:00") == "proposed_fit_2018_2021"
    assert split.period("2021-12-31T00:00:00+00:00") == "boundary_review_not_used"
    assert split.period("2022-01-01T00:00:00+00:00") == "proposed_assessment_2022"
    assert split.period("2022-12-31T00:00:00+00:00") == "boundary_review_not_used"


def test_shared_observed_block_is_quarantined_for_both_source_and_U_context(split):
    a = ("A", "2021-12-29T00:00:00+00:00")
    b = ("B", "2022-01-02T00:00:00+00:00")
    c = ("C", "2020-04-01T00:00:00+00:00")
    roles, bad = split.partitions({a, b, c}, {a: {"cross"}, b: {"cross"}, c: {"safe"}})
    assert bad == {"cross"} and roles[a] == roles[b] == "boundary_review_not_used"
    assert roles[c] == "proposed_fit_2018_2021" and len(roles) == 3


def test_absence_of_graph_context_does_not_remove_U_or_create_membership(split):
    key = ("U", "2022-04-01T00:00:00+00:00")
    roles, bad = split.partitions({key}, {})
    assert roles == {key: "proposed_assessment_2022"} and not bad
