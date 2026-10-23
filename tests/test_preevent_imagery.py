from copy import deepcopy
from datetime import UTC, datetime

import pytest
from shapely.geometry import box, mapping

from wildfire_risk_prediction.preevent_imagery import inspect_item, prediction_time, utc_time


def item():
    return {
        "id": "example",
        "collection": "sentinel-2-l2a",
        "geometry": mapping(box(25, 36, 27, 39)),
        "properties": {
            "datetime": "2018-05-13T08:55:59Z",
            "eo:cloud_cover": 0.2,
            "s2:generation_time": "2020-10-26T09:43:57Z",
        },
        "assets": {k: {} for k in ("B04", "B03", "B02", "SCL")},
    }


def test_midnight_belongs_to_previous_daily_target():
    assert prediction_time("2018-05-15T00:00:00Z") == datetime(2018, 5, 14, tzinfo=UTC)
    assert prediction_time("2018-05-15T00:00:01Z") == datetime(2018, 5, 15, tzinfo=UTC)


@pytest.mark.parametrize(
    "value", ["2024-02-01T10:00:00Z", "2025-01-01T12:00:00Z", "2018-01-01T00:00:00Z"]
)
def test_out_of_training_cutoff_rejected(value):
    with pytest.raises(ValueError):
        prediction_time(value)


def test_naive_time_rejected():
    with pytest.raises(ValueError):
        utc_time("2018-05-15T00:00:00")


def test_preacquisition_does_not_imply_historical_availability_or_label():
    row = inspect_item(item(), box(26, 37, 26.01, 37.01), utc_time("2018-05-15T00:00:00Z"))
    assert row["metadata_candidate"]
    assert row["product_generated_after_prediction"]
    assert not row["historical_available_at_verified"]
    assert not row["cover_label_accepted"]
    assert not row["local_cloud_quality_checked"]


@pytest.mark.parametrize(
    "acquired,expected",
    [
        ("2018-05-15T00:00:00Z", False),
        ("2018-05-15T08:00:00Z", False),
        ("2018-03-16T00:00:00Z", True),
        ("2018-03-15T23:59:59Z", False),
    ],
)
def test_strict_before_prediction_and_lookback(acquired, expected):
    value = item()
    value["properties"]["datetime"] = acquired
    assert (
        inspect_item(value, box(26, 37, 26.01, 37.01), utc_time("2018-05-15T00:00:00Z"))[
            "metadata_candidate"
        ]
        is expected
    )


def test_partial_scene_and_missing_quality_asset_not_selected():
    value = item()
    cutoff = utc_time("2018-05-15T00:00:00Z")
    assert not inspect_item(value, box(26, 37, 28, 38), cutoff)["metadata_candidate"]
    del value["assets"]["SCL"]
    assert not inspect_item(value, box(26, 37, 26.01, 37.01), cutoff)["metadata_candidate"]


def test_missing_cloud_is_unknown_not_zero_and_input_unchanged():
    value = item()
    del value["properties"]["eo:cloud_cover"]
    original = deepcopy(value)
    row = inspect_item(value, box(26, 37, 26.01, 37.01), utc_time("2018-05-15T00:00:00Z"))
    assert row["scene_cloud_percent"] is None
    assert value == original


def test_bad_cloud_metadata_rejected():
    value = item()
    value["properties"]["eo:cloud_cover"] = -1
    with pytest.raises(ValueError):
        inspect_item(value, box(26, 37, 26.01, 37.01), utc_time("2018-05-15T00:00:00Z"))
