import json

import pandas as pd
import pytest

from wildfire_risk_prediction.reference_intake import FIELDS, REVIEW_FLAGS, audit_intake


def example():
    # Synthetic contract fixture, never a real independent incident or training label.
    row = dict.fromkeys(FIELDS, "")
    row.update(
        reference_id="example",
        source_id="source",
        source_record_id="0001",
        reported_date="2021-07-29",
        time_semantics="first_alert",
        time_standard="UTC",
        event_time_lower_utc="2021-07-29T12:00:00Z",
        event_time_upper_utc="2021-07-29T12:10:00Z",
        reported_province="Muğla",
        location_kind="reported_origin_point",
        longitude="28.0",
        latitude="37.0",
        source_crs="EPSG:4326",
        location_uncertainty_m="100",
        record_origin="field_report",
        source_document_sha256="a" * 64,
        use_terms="Synthetic fixture use terms",
    )
    return row


def inventory():
    return {
        "source": {
            "source_id": "source",
            "lineage_status": "documented_independent_incident_record",
            "access_status": "local_event_records_verified",
        }
    }


def evidence():
    return {"source": {**dict.fromkeys(REVIEW_FLAGS, True), "verified_document_sha256": ["a" * 64]}}


def audit(rows, sources=None, reviews=None):
    return audit_intake(
        pd.DataFrame(rows, columns=FIELDS),
        inventory() if sources is None else sources,
        evidence() if reviews is None else reviews,
    )


def test_review_ready_is_still_unknown_without_labels_or_absence_inference():
    row = audit([example()])[0]
    assert row["can_review_matching"] and row["row_status"] == "ready_for_matching_review_only"
    assert row["target"] is None and row["daily_observation_status"] == "unknown"
    assert not row["positive_label_permitted"] and not row["negative_label_permitted"]
    assert not row["supports_absence_inference"]


def test_empty_received_records_do_not_become_negative_examples():
    assert audit([]) == []


@pytest.mark.parametrize(
    "field",
    [
        "source_crs",
        "time_standard",
        "source_document_sha256",
        "use_terms",
        "record_origin",
        "source_record_id",
    ],
)
def test_missing_provenance_or_semantics_blocks_matching(field):
    row = {**example(), field: ""}
    result = audit([row])[0]
    assert not result["can_review_matching"] and result["row_status"] == "needs_source_review"


@pytest.mark.parametrize("flag", REVIEW_FLAGS)
def test_unreviewed_source_claims_never_auto_pass(flag):
    reviews = evidence()
    reviews["source"][flag] = False
    result = audit([example()], reviews=reviews)[0]
    assert not result["can_review_matching"] and flag + "_pending" in result["reason_codes"]


def test_unverified_document_or_other_coordinate_system_never_silently_converted():
    row = {**example(), "source_crs": "EPSG:32635", "longitude": "400000", "latitude": "4100000"}
    reviews = evidence()
    reviews["source"]["verified_document_sha256"] = []
    result = audit([row], reviews=reviews)[0]
    assert not result["can_review_matching"]
    assert "explicit_longitude_latitude_crs_not_ready" in result["reason_codes"]
    assert "source_document_not_locally_verified" in result["reason_codes"]


@pytest.mark.parametrize(
    "change",
    [
        {"longitude": ""},
        {"longitude": "181"},
        {"longitude": "28,1"},
        {"location_uncertainty_m": "-1"},
        {"reported_date": "2025-07-29"},
        {"event_time_lower_utc": "2021-07-29T12:00:00"},
        {"event_time_upper_utc": ""},
        {"event_time_upper_utc": "2021-07-29T11:00:00Z"},
        {"event_time_upper_utc": "2024-01-01T00:00:00Z"},
        {"source_document_sha256": "bad"},
        {"reported_clock_local": "25:91"},
        {"reported_clock_local": "around noon"},
        {"longitude": 28.0},
    ],
)
def test_malformed_or_holdout_record_is_isolated_without_losing_next_record(change):
    bad = {**example(), **change}
    good = {**example(), "reference_id": "second", "source_record_id": "0002"}
    result = audit([bad, good])
    assert result[0]["row_status"] == "invalid_record" and not result[0]["can_review_matching"]
    assert result[1]["can_review_matching"] and result[1]["input_record_number"] == 2


@pytest.mark.parametrize("duplicate", ["reference_id", "source_record_id"])
def test_duplicate_id_holds_every_affected_record_without_silent_deduplication(duplicate):
    second = {**example(), "reference_id": "second", "source_record_id": "0002"}
    second[duplicate] = example()[duplicate]
    result = audit([example(), second])
    assert len(result) == 2 and all(r["row_status"] == "invalid_record" for r in result)
    assert all("duplicate_" + duplicate in r["reason_codes"] for r in result)


def test_distinct_leading_zero_identifiers_and_source_namespaces_are_preserved():
    second = {**example(), "reference_id": "second", "source_record_id": "1"}
    assert all(r["can_review_matching"] for r in audit([example(), second]))
    second["source_id"], second["source_record_id"] = "other", "0001"
    sources = {**inventory(), "other": {**inventory()["source"], "source_id": "other"}}
    reviews = {**evidence(), "other": evidence()["source"]}
    assert all(r["can_review_matching"] for r in audit([example(), second], sources, reviews))


def test_public_context_can_remain_date_only_without_fabricated_coordinates_or_utc():
    row = {
        **example(),
        "source_crs": "",
        "longitude": "",
        "latitude": "",
        "event_time_lower_utc": "",
        "event_time_upper_utc": "",
        "time_standard": "",
        "location_kind": "administrative_place_only",
        "reported_clock_local": "14:42",
    }
    result = audit([row])[0]
    assert result["row_status"] == "needs_source_review"
    assert "explicit_utc_time_bounds_missing" in result["reason_codes"]
    assert "origin_coordinates_missing" in result["reason_codes"]


def test_output_and_schema_errors_do_not_echo_private_free_text_or_coordinates():
    row = {**example(), "use_terms": "PRIVATE_TEST_MARKER", "source_id": "unknown"}
    rendered = json.dumps(audit([row], reviews={}))
    assert "PRIVATE_TEST_MARKER" not in rendered and '"28.0"' not in rendered
    frame = pd.DataFrame([example()])
    frame["private_name"] = "PRIVATE_TEST_MARKER"
    with pytest.raises(ValueError, match="Exact normalized incident columns"):
        audit_intake(frame, inventory(), evidence())


@pytest.mark.parametrize("bad_flag", ["True", 1, None])
def test_source_review_flags_are_actual_booleans(bad_flag):
    reviews = evidence()
    reviews["source"]["use_terms_reviewed"] = bad_flag
    with pytest.raises(ValueError, match="Explicit source review booleans"):
        audit([example()], reviews=reviews)


def test_shared_satellite_lineage_remains_blocked_even_with_document_reviews():
    sources = inventory()
    sources["source"]["lineage_status"] = "shared_viirs_modis"
    result = audit([example()], sources=sources)[0]
    assert not result["can_review_matching"]
    assert "independent_incident_lineage_not_established" in result["reason_codes"]


@pytest.mark.parametrize("change", ["missing_review_state", "invalid_verified_hash"])
def test_incomplete_source_review_configuration_is_not_accepted(change):
    sources, reviews = inventory(), evidence()
    if change == "missing_review_state":
        sources["source"].pop("access_status")
    else:
        reviews["source"]["verified_document_sha256"] = ["bad"]
    with pytest.raises(ValueError):
        audit([example()], sources=sources, reviews=reviews)


@pytest.mark.parametrize("change", ["missing_column", "duplicate_column"])
def test_malformed_normalized_schema_is_rejected_before_any_rows_are_admitted(change):
    frame = pd.DataFrame([example()])
    if change == "missing_column":
        frame = frame.drop(columns="source_crs")
    else:
        frame = pd.concat([frame, frame[["reference_id"]]], axis=1)
    with pytest.raises(ValueError, match="Exact normalized incident columns"):
        audit_intake(frame, inventory(), evidence())
