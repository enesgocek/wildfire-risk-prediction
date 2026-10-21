import csv
import io

import pytest

from wildfire_risk_prediction.firms_refresh import FIELDS, compare, read_delivery


def delivery(rows, **kwargs):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, FIELDS)
    writer.writeheader()
    for updates in rows:
        row = dict(
            zip(
                FIELDS,
                (
                    "36.123",
                    "30.5",
                    "300",
                    ".4",
                    ".5",
                    "2018-01-01",
                    "0030",
                    "SNPP",
                    "SNPP",
                    "n",
                    "2",
                    "280",
                    "1.2",
                    "N",
                    "0",
                ),
                strict=True,
            )
        )
        row.update(updates)
        writer.writerow(row)
    stream.seek(0)
    return read_delivery(stream, "2018-01-01", "2023-12-31", "SNPP", **kwargs)


def test_order_and_numeric_format_do_not_change_detection_multiset():
    a = delivery([{}, {"type": "2", "acq_time": "0040"}])
    b = delivery([{"type": "2", "acq_time": "40"}, {"latitude": "36.12300"}])
    r = compare(a, b)
    assert r["canonical_multiset_equal"]
    assert not r["text_field_multiset_equal"]
    assert not r["canonical_row_order_equal"]


def test_type_and_confidence_changes_are_counted_on_unique_keys():
    r = compare(delivery([{}]), delivery([{"type": "2", "confidence": "h"}]))
    assert r["changed_fields_at_unique_keys"] == {"confidence": 1, "type": 1}
    assert r["removed_detection_keys"] == r["added_detection_keys"] == 0
    assert r["type_transitions_at_changed_unique_keys"] == {"0->2": 1}


def test_duplicate_multiplicity_not_silently_deduplicated():
    r = compare(delivery([{}, {}]), delivery([{}]))
    assert not r["canonical_multiset_equal"]
    assert r["removed_or_changed_full_rows"] == 1
    assert r["ambiguous_changed_shared_keys"] == 1
    assert r["changed_unique_detection_keys"] == 0


@pytest.mark.parametrize(
    "change,projection",
    [
        ({"latitude": "36.124"}, "same_sensor_time_possible_coordinate_change"),
        ({"acq_time": "0031"}, "same_sensor_coordinates_possible_time_change"),
    ],
)
def test_coordinate_or_time_change_stays_unpaired(change, projection):
    r = compare(delivery([{}]), delivery([change]))
    assert r["added_detection_keys"] == r["removed_detection_keys"] == 1
    assert r["changed_unique_detection_keys"] == 0
    assert r["unpaired_residual_projection_overlaps"][projection] == 1


def test_old_validation_fields_not_parsed_and_new_outside_period_rejected():
    a = delivery([{}, {"acq_date": "2024-01-01", "latitude": "unparsed"}], allow_later=True)
    assert a["later_rows_skipped"] == 1
    assert compare(a, delivery([{}]))["canonical_multiset_equal"]
    with pytest.raises(ValueError, match="period"):
        delivery([{"acq_date": "2024-01-01"}])
    with pytest.raises(ValueError, match="period"):
        delivery([{"acq_date": "2025-01-01"}], allow_later=True)


@pytest.mark.parametrize(
    "change",
    [
        {"latitude": "NaN"},
        {"longitude": "181"},
        {"acq_time": "2400"},
        {"version": "4"},
        {"satellite": "N20"},
        {"type": "9"},
        {"acq_date": "2018-02-30"},
        {"confidence": ""},
    ],
)
def test_invalid_delivery_fails(change):
    with pytest.raises(ValueError):
        delivery([change])
