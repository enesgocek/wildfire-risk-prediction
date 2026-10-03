"""Batch date isolation and fail-closed retry classification."""

import importlib.util
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "runner", ROOT / "scripts/meteorology/complete_remaining_years.py"
)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.mark.parametrize("first,last", [(2020, 2024), (2021, 2025), (2025, 2025), (2024, 2021)])
def test_batch_rejects_outside_remaining_years(first, last):
    with pytest.raises(ValueError):
        runner.year_windows(first, last)


def test_leap_year_months_cover_every_day_once_and_stop_before_final_test():
    months = runner.month_windows(2024)
    assert months[0][0] == "2024-01-01" and months[-1][1] == "2025-01-01"
    assert all(a[1] == b[0] for a, b in zip(months, months[1:], strict=False))
    assert sum((date.fromisoformat(b) - date.fromisoformat(a)).days for a, b in months) == 366


def test_network_timeout_is_retried_but_source_corruption_is_not():
    assert runner.transient_failure("TimeoutError: The read operation timed out")
    assert not runner.transient_failure("ValueError: Raster provenance mismatch (sha256)")
    assert not runner.transient_failure("ValueError: Incomplete source timestamps")
