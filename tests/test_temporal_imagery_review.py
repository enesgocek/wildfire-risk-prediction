"""Temporal selection and remote-asset boundary behavior, without network calls."""

from copy import deepcopy

import pytest
from shapely.geometry import box, mapping

from wildfire_risk_prediction.preevent_imagery import utc_time
from wildfire_risk_prediction.public_sentinel_windows import public_asset
from wildfire_risk_prediction.temporal_imagery_review import alternative_dates

SUPPORT = box(0, 0, 1, 1)
CUTOFF = utc_time("2021-08-01T00:00:00Z")


def item(identity, date, cloud=1):
    return {
        "id": identity,
        "collection": "sentinel-2-l2a",
        "geometry": mapping(box(-1, -1, 2, 2)),
        "properties": {"datetime": date + "T09:00:00Z", "eo:cloud_cover": cloud},
        "assets": {k: {} for k in ("B04", "B03", "B02", "SCL", "visual")},
    }


def test_distinct_dates_not_processing_versions_and_deterministic_order():
    original = item("original", "2021-07-01", 0)
    records = [
        original,
        item("same_day_reprocessed", "2021-07-01", 0),
        item("b", "2021-07-20", 1),
        item("a", "2021-07-20", 1),
        item("c", "2021-07-25", 2),
        item("future", "2021-08-02", 0),
        item("old", "2021-01-01", 0),
    ]
    assert [p["id"] for p in alternative_dates(records[::-1], original, SUPPORT, CUTOFF)] == [
        "a",
        "c",
    ]


def test_equal_cloud_prefers_recent_and_missing_cloud_last():
    original = item("original", "2021-07-01")
    records = [
        original,
        item("old", "2021-07-02"),
        item("recent", "2021-07-03"),
        item("missing", "2021-07-31", None),
    ]
    assert [p["id"] for p in alternative_dates(records, original, SUPPORT, CUTOFF)] == [
        "recent",
        "old",
    ]


@pytest.mark.parametrize(
    "defect", ["footprint", "asset", "too_few", "duplicate", "missing_original"]
)
def test_invalid_or_insufficient_evidence_rejected(defect):
    original = item("original", "2021-07-01")
    records = [original, item("a", "2021-07-10"), item("b", "2021-07-20")]
    records = deepcopy(records)
    if defect == "footprint":
        records[1]["geometry"] = mapping(box(0, 0, 0.5, 0.5))
    elif defect == "asset":
        del records[1]["assets"]["visual"]
    elif defect == "too_few":
        records.pop()
    elif defect == "duplicate":
        records.append(deepcopy(records[1]))
    else:
        records.pop(0)
    with pytest.raises(ValueError):
        alternative_dates(records, original, SUPPORT, CUTOFF)


def test_final_test_period_rejected():
    with pytest.raises(ValueError):
        alternative_dates([], item("x", "2025-07-01"), SUPPORT, utc_time("2025-08-01T00:00:00Z"))


@pytest.mark.parametrize(
    "href",
    [
        "http://sentinel2l2a01.blob.core.windows.net/sentinel2-l2/x.tif",
        "https://sentinel2l2a01.blob.core.windows.net.evil.example/sentinel2-l2/x.tif",
        "https://user@sentinel2l2a01.blob.core.windows.net/sentinel2-l2/x.tif",
        "https://sentinel2l2a01.blob.core.windows.net/private/x.tif",
        "https://sentinel2l2a01.blob.core.windows.net/sentinel2-l2/x.tif?secret=example",
    ],
)
def test_asset_boundary_rejects_credentials_queries_and_other_hosts(href):
    with pytest.raises(ValueError):
        public_asset(href)


def test_public_asset_identity():
    assert public_asset("https://sentinel2l2a02.blob.core.windows.net/sentinel2-l2/x.tif") == (
        "sentinel2l2a02",
        "sentinel2-l2",
    )
