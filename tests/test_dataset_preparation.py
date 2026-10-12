"""Calendar completeness, release blockers and key-aligned target preview boundaries."""

import copy

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction import dataset_assembly as assembly
from wildfire_risk_prediction import dataset_batch as batch
from wildfire_risk_prediction import dataset_contract as contract
from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_month
from wildfire_risk_prediction import feature_partition as parts


def reference(month):
    day_count = len(feature_month.calendar_days(month))
    return {
        "month": month,
        "path": f"outputs/reports/dataset/feature_month_v1/job_{month}/readback.json",
        "sha256": "a" * 64,
        "manifest_sha256": "b" * 64,
        "rows": day_count * batch.GRID_COUNT,
    }


def source(month="2018-01"):
    return {
        "month": month,
        "readback": f"outputs/reports/landscape/month_v1/{month}/accepted.json",
        "readback_sha256": "a" * 64,
        "manifest_sha256": "b" * 64,
        "daily_table_sha256": "c" * 64,
        "daily_rows": 179738,
    }


def test_dictionary_exactly_matches_candidate_allowlist_and_keeps_audit_separate():
    value = contract.specification()
    assert [f["name"] for f in value["features"]] == join.feature_names()
    assert len(value["features"]) == 27
    assert not set(join.feature_names()) & set(value["provenance_columns"])
    assert all(f["missing_policy"] == "preserve_NaN_no_imputation" for f in value["features"])
    assert value["label_table_blueprint"]["implemented_binary_label_builder"] is False
    assert len(value["release_blockers"]) == 6 and value["model_ready"] is False


def test_calendar_inventory_has_correct_training_and_leap_validation_counts():
    train, validation = batch.calendar_inventory(), batch.calendar_inventory("validation")
    assert len(train) == 72 and sum(e["calendar_days"] for e in train) == 2191
    assert sum(e["candidate_rows_before_exclusions"] for e in train) == 6351709
    assert len(validation) == 12 and sum(e["calendar_days"] for e in validation) == 366
    assert sum(e["candidate_rows_before_exclusions"] for e in validation) == 1061034
    with pytest.raises(ValueError):
        batch.calendar_inventory("final_test")


def test_partial_reference_inventory_never_means_dataset_complete():
    plan = batch.build_plan([source()], [reference("2018-01")], {"src/method.py": "d" * 64})
    batch.validate_plan(plan)
    assert len(plan["entries"]) == 72
    assert plan["entries"][0]["action"] == "verify_existing_candidate"
    assert plan["entries"][1]["action"] == "await_source_reference"
    assert plan["source_reference_months"] == 1 and plan["candidate_reference_months"] == 1
    assert (
        plan["entries"][0]["vegetation_source_reference"]["table_bytes_verified_by_this_plan"]
        is False
    )
    assert plan["validation_preparation"]["executable_by_this_training_batch"] is False


@pytest.mark.parametrize("change", ["drop_month", "shuffle", "approval", "row_count", "validation"])
def test_plan_cannot_relax_calendar_split_or_acceptance(change):
    plan = batch.build_plan([], [], {"src/method.py": "d" * 64})
    if change == "drop_month":
        plan["entries"].pop()
    elif change == "shuffle":
        plan["entries"].reverse()
    elif change == "approval":
        plan["model_ready"] = True
    elif change == "row_count":
        plan["entries"][0]["candidate_rows_before_exclusions"] -= 1
    else:
        plan["entries"][0]["month"] = "2024-01"
    with pytest.raises(ValueError):
        batch.validate_plan(plan)


@pytest.mark.parametrize("path", ["../private.json", "/outside.json", "C:/private.json"])
def test_source_path_escape_rejected(path):
    value = source()
    value["readback"] = path
    with pytest.raises(ValueError):
        batch.vegetation_reference(value)


def test_duplicates_bad_hashes_and_wrong_source_row_count_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        batch.build_plan([source(), source()], [], {"src/method.py": "d" * 64})
    for field, value in [("daily_rows", 89869), ("readback_sha256", "not-a-hash")]:
        entry = source()
        entry[field] = value
        with pytest.raises(ValueError):
            batch.vegetation_reference(entry)
    with pytest.raises(ValueError, match="Duplicate"):
        batch.candidate_inventory([reference("2018-01")] * 2)


def test_even_full_candidate_calendar_cannot_grant_model_or_label_acceptance():
    value = batch.candidate_inventory([reference(e["month"]) for e in batch.calendar_inventory()])
    assert value["candidate_calendar_complete"] is True
    assert value["verified_candidate_rows"] == 6351709
    assert value["model_ready"] is False and value["labels_created"] is False
    assert value["negative_label_permitted"] is False and value["validation_ready"] is False
    assert len(value["release_blockers"]) == 6


def test_delivery_inventory_never_confuses_satellite_logs_with_payload_or_label_acceptance():
    plan = batch.build_plan([source()], [reference("2018-01")], {"src/method.py": "d" * 64})
    value = batch.delivery_inventory(plan, ["2018-01"])
    first = value["entries"][0]
    assert first["satellite_evidence"] == "log_catalogue_complete_only"
    assert first["satellite_payload_bytes_verified_by_this_check"] is False
    assert first["binary_label_ready"] is False and value["model_ready"] is False
    assert value["entries"][1]["vegetation_reference_present"] is False
    assert value["counts"]["satellite_log_catalogue_months"] == 1
    with pytest.raises(ValueError):
        batch.delivery_inventory(plan, ["2025-01"])


@pytest.fixture
def frames():
    day = "2018-01-01"
    features = pd.DataFrame(
        {"grid_id": ["g2", "g1"], "prediction_timestamp_utc": [day + "T00:00:00+00:00"] * 2}
    )
    for field in join.feature_names():
        features[field] = [np.nan, 0.5]
    qa = features[join.KEYS].copy().iloc[::-1].reset_index(drop=True)
    for field in parts.provenance_columns()[2:]:
        qa[field] = np.nan
    qa["operational_eligible"] = qa["habitat_eligibility_decided"] = False
    qa["usage"] = "retrospective_candidate_only"
    qa["join_version"] = join.VERSION
    labels = assembly.unassigned_targets(features).iloc[::-1].reset_index(drop=True)
    return features, qa, labels, ["g1", "g2"], day


def test_target_preview_matches_keys_not_row_order_and_preserves_missingness(frames):
    before = [f.copy(deep=True) for f in frames[:3]]
    frames[2]["prediction_timestamp_utc"] = "2018-01-01T00:00:00Z"
    candidate, qa, labels = assembly.assemble_day(*frames)
    assert (
        candidate.grid_id.tolist() == qa.grid_id.tolist() == labels.grid_id.tolist() == ["g1", "g2"]
    )
    assert candidate.iloc[1][join.feature_names()].isna().all()
    assert candidate.target.isna().all() and candidate.target.dtype == pd.Int8Dtype()
    assert candidate.columns.tolist() == join.KEYS + join.feature_names() + ["target"]
    assert "observation_status" not in candidate and "weather_primary_eligible" not in candidate
    for actual, expected in zip(frames[:2], before[:2], strict=True):
        pd.testing.assert_frame_equal(actual, expected)


@pytest.mark.parametrize(
    "change",
    [
        "binary_zero",
        "binary_one",
        "day",
        "duplicate",
        "lost_cell",
        "observed",
        "event_id",
        "habitat",
        "extra_column",
    ],
)
def test_unaccepted_or_misaligned_target_table_rejected(frames, change):
    features, qa, labels, ids, day = copy.deepcopy(frames)
    if change.startswith("binary"):
        labels.loc[0, "target"] = int(change == "binary_one")
    elif change == "day":
        labels.loc[0, "prediction_timestamp_utc"] = "2018-01-02T00:00:00Z"
    elif change == "duplicate":
        labels["grid_id"] = "g1"
    elif change == "lost_cell":
        labels = labels.iloc[:1]
    elif change == "observed":
        labels["observation_status"] = "observed"
    elif change == "event_id":
        labels["event_id"] = "unaccepted_cluster"
    elif change == "habitat":
        labels["habitat_status"] = "eligible"
    else:
        labels["approved"] = True
    with pytest.raises(ValueError):
        assembly.assemble_day(features, qa, labels, ids, day)
