"""Reprocessed copies are one acquisition; post-T imagery cannot become pre-event evidence."""

import importlib.util
from datetime import UTC, datetime
from pathlib import Path

from shapely.geometry import box, mapping

SPEC = importlib.util.spec_from_file_location(
    "marmaris_cover",
    Path(__file__).resolve().parents[1] / "scripts/quality/prepare_marmaris_cover_review.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CUTOFF = datetime(2022, 6, 21, tzinfo=UTC)
SUPPORT = box(28, 36.8, 28.1, 36.9)


def scene(name, when):
    return {
        "id": name,
        "collection": "sentinel-2-l2a",
        "geometry": mapping(box(27, 36, 29, 38)),
        "properties": {
            "datetime": when,
            "eo:cloud_cover": 1,
            "s2:generation_time": "2024-01-01T00:00:00Z",
        },
        "assets": {key: {} for key in ("B04", "B03", "B02", "SCL", "visual")},
    }


def test_reprocessed_same_acquisition_does_not_fill_both_date_slots():
    items = [
        scene("B_copy", "2022-06-18T08:00:00Z"),
        scene("A_original", "2022-06-18T08:00:00Z"),
        scene("earlier", "2022-06-16T08:00:00Z"),
    ]
    selected = MODULE.select_scenes({"features": items}, SUPPORT, CUTOFF)
    assert [item["id"] for item, _ in selected] == ["A_original", "earlier"]
    assert all(not check["historical_available_at_verified"] for _, check in selected)


def test_equal_or_later_than_prediction_is_excluded_even_with_clear_sky():
    items = [
        scene("equal", "2022-06-21T00:00:00Z"),
        scene("later", "2022-06-21T08:00:00Z"),
        scene("before", "2022-06-20T23:59:59Z"),
    ]
    selected = MODULE.select_scenes({"features": items}, SUPPORT, CUTOFF)
    assert [item["id"] for item, _ in selected] == ["before"]


def test_scene_that_does_not_cover_support_cannot_supply_a_review_date():
    item = scene("misplaced", "2022-06-18T08:00:00Z")
    item["geometry"] = mapping(box(28, 36.8, 28.05, 36.85))
    assert MODULE.select_scenes({"features": [item]}, SUPPORT, CUTOFF) == []
