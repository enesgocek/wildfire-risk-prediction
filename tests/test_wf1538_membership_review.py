import copy
import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def review(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "wf1538_membership_test", folder / "prepare_wf1538_membership_review.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def notes(review):
    return json.loads(review.NOTES.read_text(encoding="utf-8"))


def test_actual_human_note_does_not_create_measurements_or_road_remainder(review):
    data = notes(review)
    before = copy.deepcopy(data)
    review.validate_notes(data)
    assert data == before
    assert data["notes"]["B"]["visual_wooded_estimate_percent"] == 45
    assert data["notes"]["B"]["visual_mountainous_estimate_percent"] == 35
    assert data["notes"]["B"]["road_percent_explicitly_reported"] is None


@pytest.mark.parametrize(
    "key",
    [
        "percentages_are_measured_area_fractions",
        "positive_label_permitted",
        "negative_label_permitted",
        "habitat_threshold_accepted",
        "same_physical_fire_verified",
        "training_authorized",
        "final_merge_permitted",
    ],
)
def test_cover_note_cannot_open_scientific_or_training_gates(review, key):
    data = notes(review)
    data[key] = True
    with pytest.raises(ValueError):
        review.validate_notes(data)


@pytest.mark.parametrize(
    "key,value",
    [
        ("landform_percentage_is_bare_ground_fraction", True),
        ("percentages_form_disjoint_landcover_classes", True),
        ("inferred_remainder_percent_created", True),
        ("road_percent_explicitly_reported", 20),
        ("detection_id", "different_candidate"),
    ],
)
def test_landform_reinterpretation_normalized_remainder_or_geometry_swap_is_rejected(
    review, key, value
):
    data = notes(review)
    data["notes"]["B"][key] = value
    with pytest.raises(ValueError):
        review.validate_notes(data)
