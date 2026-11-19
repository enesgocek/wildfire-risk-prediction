import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def cover():
    path = Path(__file__).resolve().parents[1] / "scripts/quality/audit_source_conditioned_cover.py"
    spec = importlib.util.spec_from_file_location("source_pu_cover_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def case(name="one", **changes):
    return {
        "archive_row": name,
        "year": 2021,
        "diagnostic_focus": True,
        "conditional_center_grid_ids": ["A"],
        "researcher_retained_outside_L": False,
        "target": None,
        "membership": "review_unassigned",
        **changes,
    }


def prior(**changes):
    return {
        "archive_row": "one",
        "year": "2021",
        "grid_id": "A",
        "corine_2018_center_code": 312,
        "center_context": "forest_shrub",
        **{
            f"{name}_{radius}m": count
            for radius in (250, 1000)
            for name, count in [
                ("sampled_pixels", 20),
                ("mapped_pixels", 20),
                ("forest_shrub_pixels", 14),
                ("agriculture_pixels", 6),
            ]
        },
        **changes,
    }


def test_future_and_nonfocus_context_not_accessed_and_no_forest_filter_applied(cover):
    agri = prior(corine_2018_center_code=243, center_context="agriculture")
    rows = cover.attach_cover(
        [case(), case("WF1538", diagnostic_focus=False)],
        [{"year": "2023"}, {"year": "2025"}, {"year": "2021", "archive_row": "WF1538"}, agri],
    )
    assert len(rows) == 1 and rows[0]["map_center_context"] == "agriculture"
    assert rows[0]["target"] is None and rows[0]["membership"] == "review_unassigned"
    assert not rows[0]["map_context_is_fire_type"] and not rows[0]["event_date_cover_verified"]


@pytest.mark.parametrize(
    "changes", [{"grid_id": "B"}, {"year": "2020"}, {"center_context": "agriculture"}]
)
def test_mismatched_reference_identity_or_legend_fails(cover, changes):
    with pytest.raises(ValueError):
        cover.attach_cover([case()], [prior(**changes)])


def test_missing_and_duplicate_evidence_fail_instead_of_silent_subset(cover):
    with pytest.raises(ValueError, match="All focused"):
        cover.attach_cover([case()], [])
    with pytest.raises(ValueError, match="Unique source"):
        cover.attach_cover([case()], [prior(), prior()])


def test_impossible_pixel_partition_is_rejected(cover):
    with pytest.raises(ValueError, match="Map support partition"):
        cover.attach_cover([case()], [prior(forest_shrub_pixels_250m=21)])


def test_both_map_groups_are_counted_without_calling_them_true_event_types(cover):
    rows = cover.attach_cover([case()], [prior()])
    summary = cover.summarize(rows)
    assert summary["center_context_counts"] == {"forest_shrub": 1}
    assert summary["forest_shrub_centers_with_agriculture_samples"] == {"250": 1, "1000": 1}
    assert not rows[0]["event_date_cover_verified"]


def test_retention_decision_cannot_be_overridden_in_a_cover_join(cover):
    with pytest.raises(ValueError, match="retention decision"):
        cover.attach_cover([case(researcher_retained_outside_L=True)], [prior()])


def test_duplicate_current_source_rows_are_not_collapsed_by_lookup(cover):
    with pytest.raises(ValueError, match="Unique focused"):
        cover.attach_cover([case(), case()], [prior()])
