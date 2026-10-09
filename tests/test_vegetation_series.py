"""Calendar, source completeness, separate windows and daily past-only behavior."""

from datetime import timedelta

import pandas as pd
import pytest

from wildfire_risk_prediction.vegetation import summary_row
from wildfire_risk_prediction.vegetation_series import daily_candidates, month_schedule


@pytest.mark.parametrize("month,count", [("2018-08", 31), ("2020-02", 29), ("2019-02", 28)])
def test_calendar_and_weekly_schedule(month, count):
    days, cutoffs = month_schedule(month)
    assert len(days) == count
    assert [t.day for t in cutoffs] == list(range(1, count + 1, 7))


@pytest.mark.parametrize(
    "month", ["2024-01", "2025-01", "2017-12", "2018-13", "2018-8", "2018-08-01"]
)
def test_invalid_or_nontraining_month_fails_before_any_network(month):
    with pytest.raises(ValueError):
        month_schedule(month)


def fixture():
    _, cutoffs = month_schedule("2018-08")
    rows = []
    for t in cutoffs:
        for window in (30, 60):
            p = {
                "grid_id": "A",
                "vegetation_support_m2": 100,
                "ndvi_m2": 50,
                "ndmi_m2": 20,
                "observation_count_m2": 200,
                "latest_age_days_m2": 200,
                "median_age_days_m2": 300,
            }
            row = summary_row(p, 100, t, window)
            row.update(
                source_acquisition_latest_utc=(t - timedelta(days=2)).isoformat(),
                source_batch="batch.json",
                snapshot_manifest_sha256="a" * 64,
            )
            rows.append(row)
    return pd.DataFrame(rows)


def test_daily_values_use_prior_snapshot_and_advance_pixel_age():
    frame = daily_candidates(fixture(), ["A"], "2018-08")
    assert len(frame) == 62 and frame.vegetation_present.all()
    row = frame[frame.prediction_timestamp_utc.eq("2018-08-07T00:00:00+00:00")].iloc[0]
    assert row.snapshot_cutoff_utc == "2018-08-01T00:00:00+00:00"
    assert row.latest_pixel_age_mean_days == 8
    assert frame.available_at.isna().all()


def test_missing_short_window_never_filled_by_long_window():
    source = fixture()
    mask = source.window_days.eq(30)
    source.loc[mask, "valid_area_m2"] = 0
    source.loc[mask, "support_to_aoi_ratio"] = 0
    source.loc[
        mask,
        [
            "ndvi_median_mean",
            "ndmi_median_mean",
            "latest_pixel_age_mean_days",
            "median_pixel_age_mean_days",
        ],
    ] = float("nan")
    frame = daily_candidates(source, ["A"], "2018-08")
    assert not frame[frame.window_days.eq(30)].vegetation_present.any()
    assert frame[frame.window_days.eq(60)].vegetation_present.all()


@pytest.mark.parametrize("kind", ["missing", "duplicate", "unknown_grid", "availability"])
def test_changed_snapshot_scope_is_rejected(kind):
    frame = fixture()
    if kind == "missing":
        frame = frame.iloc[1:]
    elif kind == "duplicate":
        frame = pd.concat([frame, frame.iloc[:1]], ignore_index=True)
    elif kind == "unknown_grid":
        frame.loc[0, "grid_id"] = "B"
    else:
        frame.loc[0, "available_at"] = "2018-08-01T00:00:00Z"
    with pytest.raises(ValueError):
        daily_candidates(frame, ["A"], "2018-08")
