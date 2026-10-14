"""Review selection preserves uncertainty, midnight boundaries, ties and inclusion counts."""

import importlib.util
import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from wildfire_risk_prediction import label_review as review
from wildfire_risk_prediction.observation_table import DIAGNOSTICS

IDS = [f"E6933_5K_V1_C{c}_R900" for c in (500, 520, 540, 560)]


def observations():
    rows = []
    for day in range(1, 7):
        for grid in IDS:
            row = {"grid_id": grid, "prediction_timestamp_utc": f"2018-01-{day:02d}T00:00:00+00:00"}
            row.update({"obs_" + x: 0.0 if day != 6 else None for x in DIAGNOSTICS})
            row.update(
                obs_product_present=day != 6,
                obs_daily_observation_status="unknown",
                obs_negative_label_permitted=False,
                obs_target_window_alignment="boundary_timing_unresolved",
            )
            if day == 1:
                row["obs_nominal_confidence_fire"] = 1.0
            rows.append(row)
    return pd.DataFrame(rows)


def cases_and_members(first="2018-01-02T00:00:00+00:00", candidate="2018-01-01T00:00:00+00:00"):
    case = pd.DataFrame(
        [
            {
                "scenario": "d1000m_t24h",
                "cluster_id": "C1",
                "event_status": "exploratory_cluster_only",
                "negative_label_permitted": False,
                "first_detection_utc": first,
                "candidate_prediction_timestamp_utc": candidate,
                "earliest_grid_ids_json": json.dumps(IDS[:2]),
                "detection_count": 3,
            }
        ]
    )
    members = pd.DataFrame(
        [
            {
                "scenario": "d1000m_t24h",
                "cluster_id": "C1",
                "grid_id": grid,
                "detection_id": f"D{i}",
                "detection_timestamp_utc": first
                if i < 2
                else (datetime.fromisoformat(first) + timedelta(hours=2)).isoformat(),
            }
            for i, grid in enumerate(IDS[:3])
        ]
    )
    return case, members


def test_sample_is_row_and_partition_order_invariant_with_correct_fractions():
    frame = review.classify(observations(), review.geography(IDS))
    pop = frame.groupby(review.STRATA).size().rename("population_n").reset_index()
    direct = review.finalize_sample(frame, pop, 2)
    split = pd.concat([review.smallest(f, 2) for f in (frame.iloc[::2], frame.iloc[1::2])])
    other = review.finalize_sample(split.sample(frac=1, random_state=22), pop, 2)
    pd.testing.assert_frame_equal(direct, other)
    assert direct.target.isna().all()
    assert direct.review_unit_id.is_unique
    assert direct.inclusion_fraction.eq(direct.sample_n / direct.population_n).all()
    assert direct.expansion_weight.eq(direct.population_n / direct.sample_n).all()
    assert set(direct.signal_stratum) == {
        "thermal_center_present",
        "source_product_absent",
        "product_present_no_selected_thermal_center",
    }
    assert direct.groupby(review.STRATA).size().max() == 2


def test_absent_product_cannot_be_turned_into_measured_zero():
    frame = observations()
    frame.loc[~frame.obs_product_present, "obs_nominal_confidence_fire"] = 0
    with pytest.raises(ValueError, match="Absent products"):
        review.classify(frame, review.geography(IDS))


@pytest.mark.parametrize("change", ["positive_gate", "observation_gate", "holdout", "duplicate"])
def test_wrong_policy_or_frame_is_rejected(change):
    frame = observations()
    if change == "positive_gate":
        frame["obs_negative_label_permitted"] = True
    elif change == "observation_gate":
        frame["obs_daily_observation_status"] = "observed"
    elif change == "holdout":
        frame["prediction_timestamp_utc"] = frame.prediction_timestamp_utc.str.replace(
            "2018", "2025"
        )
    else:
        frame = pd.concat([frame, frame.iloc[:1]])
    with pytest.raises(ValueError):
        review.classify(frame, review.geography(IDS))


def test_tied_first_cells_and_midnight_preceding_window_retained():
    requests = review.event_requests(*cases_and_members())
    assert len(requests) == 4
    assert set(requests.grid_id) == set(IDS[:2])
    assert set(requests.observation_lookup_timestamp_utc) == {
        "2018-01-01T00:00:00+00:00",
        "2018-01-02T00:00:00+00:00",
    }
    linked = review.attach_events(requests, observations())
    assert linked.target.isna().all()
    assert not linked.exact_target_window_coverage_proven.any()
    assert linked.lookup_status.eq("matched_nominal_day_diagnostics").all()


def test_out_of_calendar_request_is_explicit_and_never_filled():
    case, members = cases_and_members("2018-01-01T00:00:00+00:00", "2017-12-31T00:00:00+00:00")
    linked = review.attach_events(review.event_requests(case, members), observations())
    outside = linked.loc[~linked.lookup_in_training_calendar]
    assert len(outside) == 2 and outside.obs_nominal_confidence_fire.isna().all()
    assert outside.lookup_status.eq("outside_training_calendar").all()
    assert outside.training_window_boundary_review.all()


def test_retained_space_separated_utc_member_display_is_normalized_only_in_memory():
    cases, members = cases_and_members()
    members["detection_timestamp_utc"] = members.detection_timestamp_utc.str.replace("T", " ")
    before = members.copy(deep=True)
    assert len(review.event_requests(cases, members)) == 4
    pd.testing.assert_frame_equal(before, members)


@pytest.mark.parametrize("change", ["lost_tie", "wrong_window", "lost_lookup"])
def test_event_evidence_loss_is_rejected(change):
    cases, members = cases_and_members()
    if change == "lost_tie":
        cases["earliest_grid_ids_json"] = json.dumps(IDS[:1])
    elif change == "wrong_window":
        cases["candidate_prediction_timestamp_utc"] = "2018-01-02T00:00:00+00:00"
    with pytest.raises(ValueError):
        request = review.event_requests(cases, members)
        if change == "lost_lookup":
            review.attach_events(request, observations().iloc[4:])


def test_review_forms_are_blank_without_machine_verdicts():
    result = review.blank_reviews(["event:a:C1", "random:g:2018-01-01"], "test")
    assert result[review.REVIEW_FIELDS].isna().all().all()
    assert result.review_status.eq("not_reviewed").all()
    with pytest.raises(ValueError):
        review.blank_reviews(["same", "same"], "test")


def test_geography_is_fixed_grid_column_sectors_not_province_guess():
    frame = review.geography(IDS)
    assert frame.geography_stratum.tolist() == [f"west_east_sector_{i}" for i in range(1, 5)]
    pd.testing.assert_frame_equal(frame, review.geography(IDS[::-1]))
    with pytest.raises(ValueError):
        review.geography(["unknown_grid"])


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/quality/prepare_label_review.py"
spec = importlib.util.spec_from_file_location("prepare_label_review_test", SCRIPT)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def test_changed_retained_hash_is_rejected_without_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    (tmp_path / "evidence.json").write_text('{"original":true}')
    digest = driver.sha(tmp_path / "evidence.json")
    (tmp_path / "evidence.json").write_text('{"original":false}')
    with pytest.raises(ValueError, match="hash changed"):
        driver.checked("evidence.json", digest, {})


def test_csv_readback_keeps_measured_zero_separate_from_unassigned_and_missing(tmp_path):
    frame = pd.DataFrame(
        {
            "measured": [0.0, float("nan")],
            "target": [pd.NA, pd.NA],
            "gate": [False, False],
            "reference": [pd.NA, "retained"],
        },
        index=[7, 9],
    )
    path = tmp_path / "review.csv"
    driver.write_verified_table(path, frame)
    actual = pd.read_csv(path)
    assert actual.measured.iloc[0] == 0 and pd.isna(actual.measured.iloc[1])
    assert actual.target.isna().all() and actual.gate.eq(False).all()
    with pytest.raises(FileExistsError):
        driver.write_verified_table(path, frame)


@pytest.mark.parametrize("allocation", [0, 11, 1.5, "2"])
def test_invalid_sampling_allocation_rejected_before_source_access(monkeypatch, allocation):
    monkeypatch.setattr(driver, "accepted_sources", lambda *a: pytest.fail("No input access"))
    with pytest.raises(ValueError):
        driver.run(allocation)


@pytest.mark.parametrize("change", ["holdout", "labels", "gate", "incomplete"])
def test_source_acceptance_rejected_before_case_files_are_opened(tmp_path, monkeypatch, change):
    months = [f"{y}-{m:02d}" for y in range(2018, 2024) for m in range(1, 13)]
    source = {
        "status": "selected_observation_months_materialized",
        "scope_is_full_training": True,
        "selected_months": months,
        "reports": [{"month": m} for m in months],
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "diagnostics_are_model_inputs": False,
        "model_ready": False,
        "final_test_accessed": False,
    }
    if change == "holdout":
        source["selected_months"] = months + ["2024-01"]
    elif change == "labels":
        source["labels_created"] = True
    elif change == "gate":
        source["negative_label_permitted"] = True
    else:
        source["reports"] = source["reports"][:-1]
    path = tmp_path / "source.json"
    path.write_text(json.dumps(source))
    calls = []

    def first_only(name, *args):
        calls.append(name)
        assert len(calls) == 1, "Invalid scope/policy must fail before other retained inputs"
        return path

    monkeypatch.setattr(driver, "checked", first_only)
    with pytest.raises(ValueError, match="Full training source"):
        driver.accepted_sources({})
