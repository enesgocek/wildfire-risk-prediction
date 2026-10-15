import pytest

from wildfire_risk_prediction.reference_readiness import matching_readiness, turkish_area


def reference():
    return {
        "reference_id": "example",
        "source_id": "s",
        "reported_date": "2021-07-29",
        "longitude": 28.0,
        "latitude": 37.0,
        "location_kind": "reported_origin_point",
        "location_uncertainty_m": 100.0,
        "event_time_lower_utc": "2021-07-29T12:00:00Z",
        "event_time_upper_utc": "2021-07-29T12:10:00Z",
        "time_semantics": "first_alert",
        "target": None,
    }


def source():
    return {
        "source_id": "s",
        "lineage_status": "documented_independent_incident_record",
        "access_status": "local_event_records_verified",
    }


def test_complete_alert_record_only_enables_matching_review_not_target_acceptance():
    row = matching_readiness(reference(), source())
    assert row["can_review_exact_grid_time_match"]
    assert not row["first_satellite_detection_time_proven"]
    assert not row["supports_negative_label"] and row["target"] is None


def test_date_only_table_without_coordinates_cannot_become_grid_label():
    ref = reference()
    for k in (
        "longitude",
        "latitude",
        "location_uncertainty_m",
        "event_time_lower_utc",
        "event_time_upper_utc",
    ):
        ref[k] = None
    ref["location_kind"] = "administrative_place_only"
    row = matching_readiness(
        ref, {**source(), "lineage_status": "institutional_context_not_audited"}
    )
    assert not row["can_review_exact_grid_time_match"] and not row["supports_negative_label"]
    assert "explicit_utc_time_bounds_missing" in row["unresolved_requirements"]


@pytest.mark.parametrize(
    "change",
    [
        "holdout",
        "naive_time",
        "partial_coordinates",
        "swapped_bounds",
        "target",
        "bad_longitude",
        "partial_time",
    ],
)
def test_bad_or_leaking_reference_is_rejected(change):
    ref = reference()
    if change == "holdout":
        ref["reported_date"] = "2025-07-29"
    if change == "naive_time":
        ref["event_time_lower_utc"] = "2021-07-29T12:00:00"
    if change == "partial_coordinates":
        ref["longitude"] = None
    if change == "swapped_bounds":
        ref["event_time_upper_utc"] = "2021-07-29T11:00:00Z"
    if change == "target":
        ref["target"] = 0
    if change == "bad_longitude":
        ref["longitude"] = 200
    if change == "partial_time":
        ref["event_time_upper_utc"] = None
    with pytest.raises(ValueError):
        matching_readiness(ref, source())


def test_shared_sensor_lineage_prevents_independent_matching_claim():
    row = matching_readiness(reference(), {**source(), "lineage_status": "shared_viirs_modis"})
    assert not row["can_review_exact_grid_time_match"]


@pytest.mark.parametrize(
    "text,value", [("9.051,6", 9051.6), ("10.737,0", 10737.0), ("132,32", 132.32)]
)
def test_turkish_decimal_preserved(text, value):
    assert turkish_area(text) == value


@pytest.mark.parametrize("text", ["9,051.6", "9051.6", "-1,0", "0,0"])
def test_ambiguous_or_nonpositive_area_rejected(text):
    with pytest.raises(ValueError):
        turkish_area(text)
