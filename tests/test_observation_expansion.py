"""Method-pilot selection cannot turn missing strata or source versions into accepted labels."""

import copy

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from wildfire_risk_prediction.observation_expansion import (
    calendar_dates,
    province_support,
    raw_references,
    select_core,
    unique_sources,
)


def test_province_overlap_preserves_border_and_unassigned_cells():
    parts = gpd.GeoDataFrame(
        {"grid_id": ["border", "outside"]}, geometry=[box(0, 0, 4, 1), box(10, 0, 11, 1)], crs=6933
    )
    provinces = gpd.GeoDataFrame(
        {"province": ["B", "A"]}, geometry=[box(2, 0, 4, 1), box(0, 0, 2, 1)], crs=6933
    )
    wide, long = province_support(parts, provinces)
    assert wide.primary_province.iloc[0] == "A"  # Stable lexical tie, no input-order tie.
    assert wide.province_intersection_count.tolist() == [2, 0]
    assert pd.isna(wide.primary_province.iloc[1])
    assert long.aoi_fraction.tolist() == [0.5, 0.5]
    assert wide.unassigned_province_area_m2.tolist() == [0, 1]


def test_provincial_polygon_overlap_is_reported_without_normalizing_it_away():
    parts = gpd.GeoDataFrame({"grid_id": ["G"]}, geometry=[box(0, 0, 3, 1)], crs=6933)
    provinces = gpd.GeoDataFrame(
        {"province": ["A", "B"]}, geometry=[box(0, 0, 2, 1), box(1, 0, 3, 1)], crs=6933
    )
    wide, _ = province_support(parts, provinces)
    assert wide.province_overlap_sum_excess_m2.iloc[0] == 1


def candidates():
    return pd.DataFrame(
        [
            {
                "grid_id": f"G{i}",
                "prediction_timestamp_utc": "2021-02-15T00:00:00Z",
                "primary_province": "A",
                "signal_group": "no_selected_thermal_center",
                "cover_group": kind,
                "water_scope_included": True,
                "obs_daily_observation_status": "unknown",
                "obs_negative_label_permitted": False,
            }
            for i, kind in enumerate(["forest_shrub", "forest_shrub", "agriculture"])
        ]
    )


def test_selection_is_order_independent_keeps_cover_diversity_and_empty_strata():
    dates = calendar_dates([2021], {"winter": "02-15"})
    f = candidates()
    a, qa = select_core(f, dates, ["A", "B"], "fixed")
    b, qb = select_core(f.iloc[::-1], dates, ["A", "B"], "fixed")
    assert a.grid_id.tolist() == b.grid_id.tolist() and a.cover_group.nunique() == 2
    assert a.target.isna().all() and not a.population_error_estimation_permitted.any()
    assert qa.selected_units.tolist() == [2, 0, 0, 0]
    assert qa.unfilled_slots.sum() == 6
    pd.testing.assert_frame_equal(qa, qb)


def test_water_rule_is_used_without_replacing_an_unfilled_quota():
    f = candidates()
    f["water_scope_included"] = False
    with pytest.raises(ValueError):
        select_core(f, calendar_dates([2021], {"winter": "02-15"}), ["A"], "s")


@pytest.mark.parametrize(
    "column,value",
    [
        ("obs_negative_label_permitted", True),
        ("obs_daily_observation_status", "observed"),
        ("target", 0),
        ("prediction_timestamp_utc", "2024-02-15T00:00:00Z"),
    ],
)
def test_open_label_or_holdout_candidates_fail(column, value):
    f = candidates()
    f[column] = value
    with pytest.raises(ValueError):
        select_core(f, calendar_dates([2021], {"winter": "02-15"}), ["A"], "s")


@pytest.mark.parametrize("years", [[2024], [2025], [2018, 2018], [2018.0]])
def test_calendar_does_not_request_holdout_or_duplicate_years(years):
    with pytest.raises(ValueError):
        calendar_dates(years, {"winter": "02-15"})


def packet():
    return {
        "day": "2021-02-15",
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "pair_ids": ["SNPP:2021046.0100"],
        "sources": [
            {
                "sample_id": "SNPP:2021046.0100",
                "audit": {
                    "sample_id": "SNPP:2021046.0100",
                    "negative_label_permitted": False,
                    "sources": {
                        "fire": {
                            "path": "raw/VNP14IMG.A2021046.0100.002.2024000000000.nc",
                            "bytes": 100,
                            "sha256": "a" * 64,
                        },
                        "geolocation": {
                            "path": "raw/VNP03IMG.A2021046.0100.002.2021000000000.nc",
                            "bytes": 1000,
                            "sha256": "b" * 64,
                        },
                    },
                },
            }
        ],
    }


def test_shared_sources_count_once_without_certifying_current_remote_availability():
    frame = raw_references(packet())
    queue = unique_sources(pd.concat([frame, frame], ignore_index=True))
    assert len(queue) == 2 and queue.bytes.sum() == 1100
    assert queue.current_remote_availability.eq("not_checked").all()


def test_source_version_conflict_fails_instead_of_choosing_one():
    frame = raw_references(packet())
    changed = frame.copy()
    changed.loc[0, "sha256"] = "c" * 64
    with pytest.raises(ValueError):
        unique_sources(pd.concat([frame, changed], ignore_index=True))


@pytest.mark.parametrize(
    "kind", ["wrong_day", "wrong_filename", "bad_size", "bad_sha", "missing_role", "permission"]
)
def test_invalid_packet_cannot_supply_a_budget(kind):
    p = copy.deepcopy(packet())
    sources = p["sources"][0]["audit"]["sources"]
    if kind == "wrong_day":
        p["day"] = "2021-02-16"
    if kind == "wrong_filename":
        sources["fire"]["path"] = "VNP14IMG.A2021046.0100.001.2024000000000.nc"
    if kind == "bad_size":
        sources["fire"]["bytes"] = 1.5
    if kind == "bad_sha":
        sources["fire"]["sha256"] = "missing"
    if kind == "missing_role":
        del sources["geolocation"]
    if kind == "permission":
        p["negative_label_permitted"] = True
    with pytest.raises(ValueError):
        raw_references(p)
