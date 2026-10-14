"""Scaled reader and pilot joins preserve source integrity, time keys and sample design."""

import hashlib
import io
import json
import time
import zipfile

import pandas as pd
import pytest
from test_observation_review import sample

from wildfire_risk_prediction.observation_window import FIELDS, review_window, source_schedule
from wildfire_risk_prediction.observation_window_pilot import append_diagnostics, stratum_impacts
from wildfire_risk_prediction.observation_window_source import (
    COMPACT_SHA,
    DELIVERY,
    JULY,
    PARTS_SHA,
    read_month,
)


def archive_bytes(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return stream.getvalue()


def source(tmp_path, form, corruption=None):
    day = "2023-07-01" if form == "july" else "2022-01-18"
    frame = pd.DataFrame(
        [
            {
                "grid_id": "G",
                "sensor": "SNPP",
                "pair_key": "2022018.2354",
                "scan_index": 202,
                "start_utc": day + "T23:59:59.481722951Z",
                "end_utc": day + "T23:59:59.981722951Z",
                "pixel_center_count": 5,
                "land_nominal_input_no_residual": 4,
                "nominal_confidence_fire": 1,
                "high_confidence_fire": 0,
            }
        ]
    )
    if corruption == "duplicate":
        frame = pd.concat([frame, frame])
    data = frame.to_csv(index=False).encode()
    report = {
        "day": day,
        "parts_sha256": PARTS_SHA,
        "compact_code_sha256": COMPACT_SHA,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "outputs_sha256": {"scan_grid.csv": hashlib.sha256(data).hexdigest()},
    }
    if corruption == "daily_gate":
        report["negative_label_permitted"] = True
    if corruption == "inner_hash":
        report["outputs_sha256"]["scan_grid.csv"] = "0" * 64
    files = {"report.json": json.dumps(report).encode(), "scan_grid.csv": data}
    if form == "july":
        name = JULY
        data = archive_bytes({day + "/" + n: b for n, b in files.items()})
    elif form == "month":
        name = DELIVERY + "/month/" + day[:7] + "/payload.zip"
        data = archive_bytes({day + ".zip": archive_bytes(files)})
    else:
        name = DELIVERY + "/day/" + day + "/payload.zip"
        data = archive_bytes(files)
    path = tmp_path / name
    path.parent.mkdir(parents=True)
    path.write_bytes(data)
    monthly = {
        "month": day[:7],
        "days": [day],
        "missing_source_days": [],
        "status": "observation_month_materialization_passed",
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "input_payload_sha256": {name: hashlib.sha256(data).hexdigest()},
    }
    if corruption == "payload":
        monthly["input_payload_sha256"][name] = "0" * 64
    return day, monthly


@pytest.mark.parametrize("form", ["month", "day", "july"])
def test_reader_all_accepted_packaging_forms_and_exact_pair_identity(tmp_path, form):
    day, report = source(tmp_path, form)
    result = read_month(tmp_path, report, {day: {"G", "no_center_grid"}}, time.monotonic() + 60)
    assert result["frames"][day].pair_key.tolist() == ["2022018.2354"]
    assert result["frames"][day].start_utc.iloc[0].endswith("481722951Z")
    assert len(result["inputs"]) == 1 and set(result["inner"][day]) == {
        "report.json",
        "scan_grid.csv",
    }


@pytest.mark.parametrize("problem", ["duplicate", "daily_gate", "inner_hash", "payload"])
def test_reader_rejects_changed_source(tmp_path, problem):
    day, report = source(tmp_path, "month", problem)
    with pytest.raises(ValueError):
        read_month(tmp_path, report, {day: {"G"}}, time.monotonic() + 60)


def test_holdout_request_rejected_before_any_file_access(tmp_path):
    for day in ("2024-01-01", "2025-01-01"):
        with pytest.raises(ValueError, match="Training only"):
            read_month(tmp_path / "does_not_exist", {}, {day: {"G"}}, time.monotonic() + 60)


def prepared():
    frame = sample()
    empty = pd.DataFrame(columns=FIELDS + ["source_nominal_day"])
    summaries = []
    for row in frame.itertuples():
        _, summary = review_window(
            empty, "2022-01-18", row.grid_id, source_schedule("2022-01-18", set())
        )
        summaries.append(summary)
    scope = pd.DataFrame(
        {
            "grid_id": frame.grid_id,
            "water_scope_version": "water_scope_v1",
            "water_scope_included": True,
            "water_scope_reason": "retained_mixed",
        }
    )
    scope.loc[0, ["water_scope_included", "water_scope_reason"]] = [False, "excluded_map_water"]
    return frame, pd.DataFrame(summaries), scope


def test_join_matches_utc_aliases_preserves_nulls_weights_and_all_units():
    frame, summaries, scope = prepared()
    before = frame.copy(deep=True)
    result = append_diagnostics(frame, summaries.sample(frac=1, random_state=1), scope)
    pd.testing.assert_frame_equal(result[frame.columns], before)
    assert result.target.isna().all() and result.window_target.isna().all()
    assert result.iloc[0].water_scope_included == False  # noqa: E712
    assert pd.isna(result.iloc[0].loaded_window_vs_nominal_thermal_count_delta)
    assert pd.isna(result.iloc[0].obs_cloud)
    strata = stratum_impacts(result)
    assert strata.sample_n.sum() == len(frame)
    assert strata.population_n.sum() == frame.expansion_weight.sum()
    assert strata.window_boundary_scan_present_expanded_count_estimate.sum() == 0


@pytest.mark.parametrize("problem", ["duplicate", "unmatched", "label", "negative_gate", "weight"])
def test_pilot_acceptance_guard_rejects_corruption(problem):
    frame, summaries, scope = prepared()
    if problem == "duplicate":
        summaries = pd.concat([summaries, summaries.iloc[:1]])
    elif problem == "unmatched":
        summaries.loc[0, "grid_id"] = "other"
    elif problem == "label":
        summaries["target"] = 0
    elif problem == "negative_gate":
        summaries["negative_label_permitted"] = True
    else:
        frame["expansion_weight"] = 1
    with pytest.raises((ValueError, AssertionError)):
        append_diagnostics(frame, summaries, scope)
