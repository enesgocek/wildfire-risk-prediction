"""Join point-level review evidence without promoting it to habitat or fire truth."""

import json


def assemble_review(native, quality, human_records, witnesses):
    for frame in (native, quality):
        if frame.empty or frame.detection_id.isna().any() or not frame.detection_id.is_unique:
            raise ValueError("Unique nonempty point keys required")
    if set(native.detection_id) != set(quality.detection_id):
        raise ValueError("Point coverage mismatch")
    for column in (
        "positive_label_permitted",
        "negative_label_permitted",
        "habitat_label_accepted",
    ):
        if not native[column].eq(False).all():  # noqa: E712
            raise ValueError("Unaccepted native evidence required")
    for column in ("quality_threshold_accepted", "habitat_accepted", "fire_label_accepted"):
        if not quality[column].eq(False).all():  # noqa: E712
            raise ValueError("Unaccepted image evidence required")
    if not native.target.isna().all():
        raise ValueError("Targets must remain empty")
    human = {r["detection_id"]: r for r in human_records}
    if len(human) != len(human_records) or not set(human).issubset(set(native.detection_id)):
        raise ValueError("Invalid human review identities")
    if set(witnesses.detection_id) != set(native.detection_id):
        raise ValueError("Scenario witness coverage mismatch")
    rows = native.merge(quality, on="detection_id", validate="one_to_one")
    for record in human_records:
        if record["habitat_admission_accepted"] or record["independent_expert_validation"]:
            raise ValueError("Only preliminary human context supported")
    rows["reference_review_route"] = [
        "forest_shrub_center_check"
        if r.center_cover_group_2017 in ("forest", "shrub")
        else "mixed_support_check"
        if r.forest_shrub_fraction_of_entire_support > 0
        else "other_reference_cover_check"
        for r in rows.itertuples()
    ]
    rows["researcher_preliminary_context"] = [
        human.get(i, {}).get("preliminary_cover_context") for i in rows.detection_id
    ]
    rows["researcher_confirmation_recorded"] = [
        human.get(i, {}).get("researcher_confirmation", False) for i in rows.detection_id
    ]
    rows["scenario_membership_count"] = [
        len(
            witnesses.loc[
                witnesses.detection_id.eq(i), ["scenario", "cluster_id"]
            ].drop_duplicates()
        )
        for i in rows.detection_id
    ]
    rows["review_reasons_json"] = [
        json.dumps(
            [
                "reference_2017_not_current_cover",
                "woody_crop_vs_natural_cover_unresolved",
                *(
                    ["mixed_reference_cover"]
                    if len(json.loads(r.reference_cover_groups)) > 1
                    else []
                ),
                *(
                    ["local_quality_flags"]
                    if any(
                        getattr(r, k) > 0
                        for k in (
                            "cloud_cirrus_fraction",
                            "cloud_shadow_fraction",
                            "dark_or_cast_shadow_fraction",
                            "unclassified_fraction",
                            "nodata_defective_fraction",
                            "snow_ice_fraction",
                        )
                    )
                    else []
                ),
                *(["residual_bowtie"] if r.residual_bowtie else []),
            ]
        )
        for r in rows.itertuples()
    ]
    rows["natural_forest_shrub_admission"] = "undecided"
    rows["woody_crop_distinction_verified"] = False
    rows["independent_event_identity_verified"] = False
    rows["daily_observation_status"] = "unknown"
    rows["automatic_exclusion"] = False
    rows["final_merge_permitted"] = False
    return rows.sort_values("detection_id").reset_index(drop=True)
