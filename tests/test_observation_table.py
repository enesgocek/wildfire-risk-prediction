"""Observation absence stays missing, and diagnostic measurements never open label gates."""

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction import observation_table as obs


def sources():
    areas = pd.DataFrame({"grid_id": ["b", "a"], "aoi_area_m2": [100.0, 100.0]})
    for group in obs.GROUPS:
        areas[group + "_area_estimate_m2"] = [20.0, 30.0]
        areas[group + "_fraction_estimate"] = [0.2, 0.3]
    areas["method"] = obs.METHOD
    centers = pd.DataFrame({"grid_id": ["a", "b"]})
    for field in obs.COUNTS + obs.DURATIONS:
        centers[field] = 0
    for field in obs.TIMES:
        centers[field] = np.nan
    for frame in (areas, centers):
        frame["daily_observation_status"] = "unknown"
        frame["negative_label_permitted"] = False
    return areas, centers


def test_key_alignment_and_real_zero_preserved_without_negative_permission():
    frame = obs.diagnostic_day("2018-01-02", ["a", "b"], *sources())
    assert frame.grid_id.tolist() == ["a", "b"]
    assert frame.obs_cloud_area_estimate_m2.tolist() == [30.0, 20.0]
    assert frame.obs_nominal_confidence_fire.eq(0).all()
    assert obs.summarize(frame)["eligible_negative_rows"] is None
    assert obs.summarize(frame)["binary_targets_created"] == 0


def test_absent_product_remains_nan_instead_of_no_fire_zero():
    frame = obs.diagnostic_day("2018-06-13", ["a", "b"])
    assert frame[["obs_" + field for field in obs.DIAGNOSTICS]].isna().all().all()
    assert obs.summarize(frame)["rows_missing_product"] == 2
    frame.loc[0, "obs_nominal_confidence_fire"] = 0
    with pytest.raises(ValueError):
        obs.summarize(frame)


@pytest.mark.parametrize("problem", ["duplicates", "gate", "count", "ratio", "method", "duration"])
def test_bad_source_or_false_acceptance_fails(problem):
    area, center = sources()
    if problem == "duplicates":
        center["grid_id"] = "a"
    elif problem == "gate":
        area["negative_label_permitted"] = True
    elif problem == "count":
        center["pixel_center_count"] = -1
    elif problem == "ratio":
        area["cloud_fraction_estimate"] = 0.9
    elif problem == "method":
        area["method"] = "official_footprint"
    else:
        center["any_center_envelope_union_seconds"] = 86401
    with pytest.raises(ValueError):
        obs.diagnostic_day("2018-01-02", ["a", "b"], area, center)


@pytest.mark.parametrize("day", ["2024-01-01", "2025-01-01"])
def test_held_out_scope_rejected(day):
    with pytest.raises(ValueError):
        obs.diagnostic_day(day, ["a", "b"])


def test_one_missing_input_does_not_silently_become_gap():
    area, _ = sources()
    with pytest.raises(ValueError):
        obs.diagnostic_day("2018-01-02", ["a", "b"], area)
