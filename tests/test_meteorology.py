"""Meteorology time boundaries, missing-area behavior and final-test guard."""

import importlib.util
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/meteorology/prepare_era5_land.py"
SPEC = importlib.util.spec_from_file_location("meteorology", SCRIPT)
meteorology = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(meteorology)


def test_time_window_stays_before_target_across_year_boundary():
    target = datetime(2018, 1, 1, tzinfo=UTC)
    start, end = meteorology.window(target, 336)
    assert start == datetime(2017, 12, 18, tzinfo=UTC)
    assert end == target  # Exclusive end; latest valid timestamp is T-1 hour.
    assert end - timedelta(hours=1) < target


@pytest.mark.parametrize(
    "start,end",
    [
        ("2025-01-01", "2025-01-02"),
        ("2024-12-31", "2025-01-02"),
        ("2017-12-31", "2018-01-02"),
        ("2018-01-02", "2018-01-01"),
    ],
)
def test_prediction_dates_guard_final_test_and_invalid_range(start, end):
    with pytest.raises(ValueError):
        list(meteorology.days(start, end))


def test_last_validation_day_is_allowed_with_exclusive_end():
    assert list(meteorology.days("2024-12-31", "2025-01-01")) == [date(2024, 12, 31)]


def test_area_mean_preserves_missingness_and_coverage():
    values = np.array([10.0, 20.0, -9999.0])
    grids = np.array([0, 0, 1, 1, 2])
    pixels = np.array([0, 1, 1, 2, 2])
    areas = np.array([1.0, 3.0, 2.0, 2.0, 4.0])
    means, fractions = meteorology.area_mean(
        values, grids, pixels, areas, np.array([4.0, 4.0, 4.0])
    )
    np.testing.assert_allclose(means[:2], [17.5, 20.0])
    assert np.isnan(means[2])
    np.testing.assert_allclose(fractions, [1.0, 0.5, 0.0])


def test_area_mean_does_not_treat_zero_rain_as_missing():
    mean, fraction = meteorology.area_mean(
        np.array([0.0]), np.array([0]), np.array([0]), np.array([1.0]), np.array([1.0])
    )
    assert mean[0] == 0.0
    assert fraction[0] == 1.0


@pytest.fixture
def archived_day(tmp_path):
    """A valid file hash cannot by itself establish its date or feature order."""
    target = date(2018, 1, 1)
    path = tmp_path / "2018-01-01.tif"
    manifest = {"height": 1, "width": 1, "transform": [0.1, 0, 30, 0, -0.1, 38]}
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=1,
        width=1,
        count=len(meteorology.FEATURES),
        dtype="float32",
        crs="EPSG:4326",
        transform=Affine(*manifest["transform"]),
    ) as dst:
        dst.write(np.zeros((len(meteorology.FEATURES), 1, 1), dtype="float32"))
    metadata = {
        "source": meteorology.SOURCE,
        "version": meteorology.VERSION,
        "prediction_date": str(target),
        "features": meteorology.FEATURES.copy(),
        "available_at": None,
        "usage": "retrospective_reanalysis_only",
        "source_timestamp_end_exclusive": "2018-01-01T00:00:00Z",
        "precipitation_interval_end_utc": "2017-12-31T23:00:00Z",
        "weights_manifest": manifest,
        "sha256": meteorology.sha(path),
    }
    return path, target, manifest, metadata


def test_archive_accepts_current_contract(archived_day):
    path, target, manifest, metadata = archived_day
    path.with_suffix(".json").write_text(json.dumps(metadata), encoding="utf-8")
    meteorology.verify_archive(path, target, manifest)


@pytest.mark.parametrize(
    "field,value",
    [
        ("prediction_date", "2018-01-02"),
        ("version", "old_processing"),
        ("source", "different_source"),
        ("features", list(reversed(meteorology.FEATURES))),
        ("source_timestamp_end_exclusive", "2018-01-02T00:00:00Z"),
        ("precipitation_interval_end_utc", "2018-01-01T00:00:00Z"),
        ("available_at", "2017-12-31T23:00:00Z"),
        ("sha256", "incorrect_hash"),
    ],
)
def test_archive_rejects_wrong_provenance(archived_day, field, value):
    path, target, manifest, metadata = archived_day
    metadata[field] = value
    path.with_suffix(".json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match=field):
        meteorology.verify_archive(path, target, manifest)
