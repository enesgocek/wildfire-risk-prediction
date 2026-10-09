"""Temporal leakage, unknown availability and missing vegetation regression cases."""

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction import vegetation as veg


def snapshot(cutoff="2018-08-01", release=None):
    row = veg.summary_row(
        {
            "grid_id": "a",
            "vegetation_support_m2": 10,
            "ndvi_m2": 5,
            "ndmi_m2": 2,
            "observation_count_m2": 20,
            "latest_age_days_m2": 20,
            "median_age_days_m2": 100,
        },
        20,
        cutoff,
        30,
    )
    row.update(source_acquisition_latest_utc="2018-07-30T10:00:00Z", available_at=release)
    return row


def select(rows, dates, mode="retrospective"):
    return veg.as_of_snapshots(pd.DataFrame(rows), ["a", "b"], dates, 30, mode=mode)


def test_previous_snapshot_advances_age_without_backfill_and_expires():
    out = select([snapshot()], ["2018-07-31", "2018-08-02", "2018-08-09", "2018-08-10"])
    a = out[out.grid_id.eq("a")].reset_index(drop=True)
    assert a.vegetation_present.tolist() == [False, True, True, False]
    assert a.ndvi_median_mean.iloc[1] == 0.5
    assert a.latest_pixel_age_mean_days.iloc[1] == 3
    assert a.median_pixel_age_mean_days.iloc[2] == 18
    assert out[out.grid_id.eq("b")].ndvi_median_mean.isna().all()


def test_unknown_release_is_retrospective_only_and_future_release_waits():
    dates = ["2018-08-01", "2018-08-02"]
    assert select([snapshot()], dates).vegetation_present.sum() == 2
    assert not select([snapshot()], dates, "operational").vegetation_present.any()
    out = select([snapshot(release="2018-08-01T12:00Z")], dates, "operational")
    assert out[out.grid_id.eq("a")].vegetation_present.tolist() == [False, True]


def test_zero_support_remains_missing_even_when_catalog_has_scenes():
    row = veg.summary_row({"grid_id": "a"}, 20, "2018-08-01", 30)
    row["source_acquisition_latest_utc"] = None
    assert not select([row], ["2018-08-01"]).vegetation_present.any()
    assert np.isnan(row["ndvi_median_mean"])
    with pytest.raises(ValueError, match="without support"):
        veg.summary_row({"grid_id": "a", "ndvi_m2": 1}, 20, "2018-08-01", 30)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_acquisition_latest_utc", "2018-08-01T00:00Z"),
        ("source_acquisition_latest_utc", "2018-06-30T00:00Z"),
        ("available_at", "2018-07-01T00:00Z"),
        ("window_start_utc", "2018-07-01T00:00Z"),
        ("processing_version", "other"),
        ("window_days", 60),
        ("grid_id", "unknown"),
        ("ndvi_median_mean", 1.01),
        ("ndmi_median_mean", np.nan),
        ("latest_pixel_age_mean_days", -1),
        ("median_pixel_age_mean_days", 31),
        ("valid_area_m2", -1),
        ("support_to_aoi_ratio", np.inf),
    ],
)
def test_bad_provenance_and_values_rejected(field, value):
    row = snapshot()
    row[field] = value
    with pytest.raises(ValueError):
        select([row], ["2018-08-01"])


def test_duplicate_identity_and_target_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        select([snapshot(), snapshot()], ["2018-08-01"])
    with pytest.raises(ValueError, match="Duplicate prediction"):
        select([snapshot()], ["2018-08-01", "2018-08-01"])


@pytest.mark.parametrize("date", ["2025-01-01", "2017-12-31", "2018-08-01T10:00Z", None])
def test_final_test_or_invalid_target_blocked(date):
    with pytest.raises(ValueError):
        select([snapshot()], [date])


def test_final_test_snapshot_blocked_even_if_it_would_not_be_selected():
    row = snapshot()
    row["snapshot_cutoff_utc"] = "2025-01-01T00:00Z"
    with pytest.raises(ValueError):
        select([row], ["2018-08-01"])


def test_strict_window_boundary_timezone_and_training_scope():
    veg.validate_window("2018-08-01", 30, ["2018-07-02T00:00Z", "2018-07-31T23:59Z"])
    for time in ["2018-08-01T00:00Z", "2018-07-01T23:59Z", "2018-07-30", None]:
        with pytest.raises(ValueError):
            veg.validate_window("2018-08-01", 30, [time])
    with pytest.raises(ValueError):
        veg.prediction_time("2024-01-01", training_only=True)
