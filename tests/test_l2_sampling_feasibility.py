"""Sampling design, temporal boundaries and cost guardrails; no network fixtures."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "sampling", Path(__file__).resolve().parents[1] / "scripts/cloud/assess_l2_sampling.py"
)
sampling = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sampling)


def test_cyclic_month_equal_inclusion_including_leap_february():
    days = pd.date_range("2020-02-01", "2020-02-29").strftime("%Y-%m-%d").tolist()
    counts = dict.fromkeys(days, 0)
    for start in range(len(days)):
        for day in sampling.cyclic_block(days, start, 7):
            counts[day] += 1
    assert set(counts.values()) == {7}


def test_monthly_sample_nested_reproducible_and_training_only():
    small, p7 = sampling.sample_dates(7)
    medium, p14 = sampling.sample_dates(14)
    large, _ = sampling.sample_dates(21)
    assert small < medium < large < set(sampling.calendar())
    assert [len(small), len(medium), len(large)] == [504, 1008, 1512]
    assert sampling.sample_dates(7) == (small, p7)
    assert sampling.sample_dates(7, 17)[0] != small
    assert all("2018-01-01" <= day <= "2023-12-31" for day in large)
    for month in {d[:7] for d in sampling.calendar()}:
        days = [d for d in sampling.calendar() if d.startswith(month)]
        assert sum(d.startswith(month) for d in small) == 7
        assert all(p7[d] == 7 / len(days) for d in small if d.startswith(month))
        assert all(p14[d] == 14 / len(days) for d in medium if d.startswith(month))


@pytest.mark.parametrize("count", [0, -1, 29, 7.5])
def test_reject_invalid_sample_count(count):
    with pytest.raises(ValueError, match="Invalid sampling"):
        sampling.sample_dates(count)


def test_guard_dates_kept_separate_and_external_not_read():
    days, external = sampling.guards({"2018-01-01", "2023-12-31"})
    assert days == {"2018-01-01", "2018-01-02", "2023-12-30", "2023-12-31"}
    assert external == ["2017-12-31", "2024-01-01"]
    with pytest.raises(ValueError, match="outside training"):
        sampling.guards({"2025-01-01"})


def test_open_left_closed_right_target_window_at_midnight():
    result = sampling.target_day(
        pd.Series(["2021-08-01T00:00:00Z", "2021-08-01T00:00:01Z", "2021-08-02T00:00:00Z"])
    )
    assert result.tolist() == ["2021-07-31", "2021-08-01", "2021-08-01"]


def test_ecdf_uses_design_weights_and_rejects_invalid_weights():
    assert sampling.weighted_ecdf_distance([0, 0, 1], [0, 1], [2, 1]) == 0
    assert sampling.weighted_ecdf_distance([0, 0, 1], [0, 1], [1, 1]) == pytest.approx(1 / 6)
    with pytest.raises(ValueError, match="weight"):
        sampling.weighted_ecdf_distance([0], [0], [np.nan])


def test_cost_reuses_only_nominal_july_and_tracks_unpaired():
    nominal = pd.DataFrame(
        {
            "day": ["2023-07-01", "2023-08-01", "2023-08-02"],
            "estimated_bytes": [100, 200, 300],
        }
    )
    pairs = pd.DataFrame(
        {
            "day": ["2023-07-01", "2023-08-01", "2023-08-02", "2023-08-01"],
            "pair_status": ["nominal_unique_pair"] * 3 + ["geolocation_only"],
        }
    )
    result = sampling.cost({"2023-07-01", "2023-08-01"}, pairs, nominal, 60)
    assert result["nominal_pairs"] == 2
    assert result["pending_nominal_pairs"] == 1
    assert result["pending_catalogue_estimated_GB_decimal"] == 200 / 1e9
    assert result["reused_July_nominal_pairs"] == 1
    assert result["pending_pair_phase_hours_extrapolated"] == 1 / 60
    assert result["unpaired_records_not_discarded_or_negative"] == 1


def save_catalogue(tmp_path, bad_role=False, bad_year=False, allow_negative=False):
    day = "2025-01-01" if bad_year else "2020-01-01"
    pair = pd.DataFrame(
        {
            "sensor": ["SNPP"],
            "pair_key": ["2020001.0100"],
            "day": [day],
            "pair_status": ["nominal_unique_pair"],
            "actual_input_identity_verified": [False],
            "negative_label_permitted": [allow_negative],
        }
    )
    granules = pd.DataFrame(
        {
            "sensor": ["SNPP"] * 2,
            "pair_key": ["2020001.0100"] * 2,
            "role": ["fire", "fire" if bad_role else "geolocation"],
            "concept_id": ["fire-1", "geo-1"],
            "start_utc": [day + "T01:00:00Z"] * 2,
            "actual_input_identity_verified": [False] * 2,
            "negative_label_permitted": [allow_negative] * 2,
            "catalogue_size_bytes_estimate": [100.2, 200.3],
        }
    )
    pp, gp = tmp_path / "pairs.csv", tmp_path / "granules.csv"
    pair.to_csv(pp, index=False)
    granules.to_csv(gp, index=False)
    return pp, gp


def test_catalogue_requires_both_sources_and_preserves_size_estimate(tmp_path):
    paths = save_catalogue(tmp_path)
    _, nominal = sampling.read_catalogue(*paths)
    assert nominal.estimated_bytes.tolist() == [300]


@pytest.mark.parametrize("change", ["bad_role", "bad_year", "allow_negative"])
def test_catalogue_rejects_missing_source_sealed_year_and_labels(tmp_path, change):
    paths = save_catalogue(tmp_path, **{change: True})
    with pytest.raises(ValueError):
        sampling.read_catalogue(*paths)


def test_landcover_bins_keep_roundoff_but_reject_real_out_of_range(tmp_path, monkeypatch):
    monkeypatch.setattr(sampling, "ROOT", tmp_path)
    monkeypatch.setattr(sampling, "sample_dates", lambda count: ({"2020-01-01"}, {}))
    directory = tmp_path / "data/interim"
    directory.mkdir(parents=True)
    path = directory / "grid_landcover_2017.csv"
    grid = "E6933_5K_V1_C510_R920"
    cover = pd.DataFrame(
        {
            "grid_id": [grid],
            "reference_year": [2017],
            "natural_vegetation_fraction": [1.000000000000005],
        }
    )
    cover.to_csv(path, index=False)
    firms = pd.DataFrame({"grid_id": [grid], "target_day": ["2020-01-01"]})
    before = path.read_bytes()
    table, _ = sampling.spatial_cover_summary(firms, {grid})
    assert set(table.loc[table.dimension.eq("cover_bin_descriptive_only"), "group"]) == {
        "90_to_100_percent"
    }
    assert path.read_bytes() == before
    cover["natural_vegetation_fraction"] = 1.01
    cover.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Landcover fraction"):
        sampling.spatial_cover_summary(firms, {grid})
