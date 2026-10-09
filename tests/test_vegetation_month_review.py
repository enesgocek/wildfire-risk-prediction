"""Missing support stays missing; separate windows and period isolation in review."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/quality/review_vegetation_months.py"
SPEC = importlib.util.spec_from_file_location("month_support_review", PATH)
reviewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer)


def frame():
    rows = []
    for window in (30, 60):
        for present in (True, False):
            rows.append(
                {
                    "grid_id": "A",
                    "window_days": window,
                    "vegetation_present": present,
                    "support_to_aoi_ratio": 0.95 if present else float("nan"),
                    "snapshot_age_days": 6 if present else float("nan"),
                    "latest_pixel_age_mean_days": 12 if present else float("nan"),
                    "median_pixel_age_mean_days": 25 if present else float("nan"),
                    "ndvi_median_mean": 0.5 if present else float("nan"),
                    "ndmi_median_mean": -0.1 if present else float("nan"),
                }
            )
    return pd.DataFrame(rows)


def test_missing_denominator_and_age_population_are_explicit():
    summaries = reviewer.summarize(frame())
    assert [r["window_days"] for r in summaries] == [30, 60]
    for result in summaries:
        assert result["missing_rows"] == 1 and result["missing_fraction"] == 0.5
        assert result["rows_support_at_least_90pct"] == 1
        assert result["median_pixel_age_p50_days_supported"] == 25


def test_missing_values_are_never_silently_counted_as_zero():
    table = frame()
    table.loc[~table.vegetation_present, "ndvi_median_mean"] = 0
    with pytest.raises(ValueError, match="remain missing"):
        reviewer.summarize(table)


def test_all_missing_window_has_null_age_percentile():
    table = frame()
    table.loc[table.window_days.eq(30), "vegetation_present"] = False
    table.loc[table.window_days.eq(30), reviewer.COLUMNS[3:]] = float("nan")
    result = reviewer.summarize(table)[0]
    assert result["missing_fraction"] == 1
    assert result["median_pixel_age_p50_days_supported"] is None


@pytest.mark.parametrize("months", [["2018-08", "2025-01"], ["2024-01"], [], ["2018-08"] * 2])
def test_invalid_scope_precedes_source_access(months, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Scope rejected before loading source checker")

    monkeypatch.setattr(reviewer.importlib.util, "spec_from_file_location", forbidden)
    with pytest.raises(ValueError):
        reviewer.review(months)
