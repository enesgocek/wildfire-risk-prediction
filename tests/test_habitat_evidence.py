import pandas as pd
import pytest

from wildfire_risk_prediction.habitat_evidence import assemble_review


def inputs():
    native = pd.DataFrame(
        [
            {
                "detection_id": "a",
                "center_cover_group_2017": "forest",
                "forest_shrub_fraction_of_entire_support": 0.8,
                "target": None,
                "positive_label_permitted": False,
                "negative_label_permitted": False,
                "habitat_label_accepted": False,
                "reference_cover_groups": '["forest", "agriculture"]',
                "residual_bowtie": False,
            }
        ]
    )
    quality = pd.DataFrame(
        [
            {
                "detection_id": "a",
                "quality_threshold_accepted": False,
                "habitat_accepted": False,
                "fire_label_accepted": False,
                "cloud_cirrus_fraction": 0,
                "cloud_shadow_fraction": 0,
                "dark_or_cast_shadow_fraction": 0,
                "unclassified_fraction": 0,
                "nodata_defective_fraction": 0,
                "snow_ice_fraction": 0,
            }
        ]
    )
    witness = pd.DataFrame(
        [
            {"detection_id": "a", "scenario": "s1", "cluster_id": "c1"},
            {"detection_id": "a", "scenario": "s2", "cluster_id": "c2"},
        ]
    )
    return native, quality, [], witness


def test_green_clean_forest_reference_never_becomes_admission():
    out = assemble_review(*inputs()).iloc[0]
    assert out.reference_review_route == "forest_shrub_center_check"
    assert out.natural_forest_shrub_admission == "undecided"
    assert not out.woody_crop_distinction_verified
    assert not out.automatic_exclusion
    assert pd.isna(out.target)
    assert out.scenario_membership_count == 2


@pytest.mark.parametrize(
    "fraction,route", [(0, "other_reference_cover_check"), (0.01, "mixed_support_check")]
)
def test_nonforest_center_kept_with_its_spatial_context(fraction, route):
    n, q, h, w = inputs()
    n.loc[0, "center_cover_group_2017"] = "agriculture"
    n.loc[0, "forest_shrub_fraction_of_entire_support"] = fraction
    out = assemble_review(n, q, h, w)
    assert len(out) == 1 and out.iloc[0].reference_review_route == route
    assert not out.automatic_exclusion.any()


@pytest.mark.parametrize(
    "problem", ["duplicate", "missing_image", "accepted", "target", "missing_witness"]
)
def test_incompatible_evidence_fails(problem):
    n, q, h, w = inputs()
    if problem == "duplicate":
        q = pd.concat([q, q])
    elif problem == "missing_image":
        q.loc[0, "detection_id"] = "other"
    elif problem == "accepted":
        q.loc[0, "habitat_accepted"] = True
    elif problem == "target":
        n.loc[0, "target"] = 1
    else:
        w = w.iloc[:0]
    with pytest.raises(ValueError):
        assemble_review(n, q, h, w)


def test_human_note_preserved_without_independent_or_final_acceptance():
    n, q, _, w = inputs()
    h = [
        {
            "detection_id": "a",
            "researcher_confirmation": True,
            "preliminary_cover_context": "forest_shrub_context",
            "habitat_admission_accepted": False,
            "independent_expert_validation": False,
        }
    ]
    out = assemble_review(n, q, h, w).iloc[0]
    assert out.researcher_confirmation_recorded
    assert out.researcher_preliminary_context == "forest_shrub_context"
    assert not out.independent_event_identity_verified
    assert not out.final_merge_permitted
