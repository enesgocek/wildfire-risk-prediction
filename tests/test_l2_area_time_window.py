"""Respect open lower and closed upper target endpoints without guessing pixel time."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "union", Path(__file__).resolve().parents[1] / "scripts/firms/combine_l2_area_estimates.py"
)
union = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(union)


@pytest.mark.parametrize(
    "start,end,status",
    [
        ("2019-01-14T00:00:00Z", "2019-01-14T00:00:01Z", "boundary_unknown"),
        ("2019-01-13T23:59:59Z", "2019-01-14T00:00:00Z", "outside"),
        ("2019-01-14T00:00:01Z", "2019-01-14T00:00:02Z", "inside"),
        ("2019-01-14T23:59:59Z", "2019-01-15T00:00:00Z", "inside"),
        ("2019-01-15T00:00:00Z", "2019-01-15T00:00:01Z", "boundary_unknown"),
        ("2019-01-15T00:00:01Z", "2019-01-15T00:00:02Z", "outside"),
    ],
)
def test_target_endpoint_membership(start, end, status):
    assert (
        union.classify_scan_interval(start, end, "2019-01-14T00:00:00Z", "2019-01-15T00:00:00Z")
        == status
    )


def test_timezone_omission_is_rejected():
    with pytest.raises(ValueError, match="Timezone required"):
        union.classify_scan_interval(
            "2019-01-14T00:00:01",
            "2019-01-14T00:00:02Z",
            "2019-01-14T00:00:00Z",
            "2019-01-15T00:00:00Z",
        )


def test_normalized_duplicate_swaths_are_rejected_before_data_reads():
    with pytest.raises(ValueError, match="distinct swaths"):
        union.combine(["2019014.0042", "SNPP:2019014.0042"])
