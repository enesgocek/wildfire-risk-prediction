import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "summer_controls", Path(__file__).parents[1] / "scripts/firms/prepare_summer_l2_controls.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def fires():
    return pd.DataFrame(
        {
            "sensor": ["SNPP", "SNPP"],
            "pair_key": ["2019175.1000", "2019175.1006"],
            "start_utc": ["2019-06-24T10:00:00Z", "2019-06-24T10:06:00Z"],
            "end_utc": ["2019-06-24T10:06:00Z", "2019-06-24T10:12:00Z"],
        }
    )


def detections():
    return pd.DataFrame(
        {
            "detection_timestamp_utc": [
                "2019-06-24T10:00:00Z",
                "2019-06-24T10:05:00Z",
                "2019-06-24T10:06:00Z",
                "2019-06-24T10:12:00Z",
            ],
            "confidence": ["n", "l", "h", "n"],
            "type": ["2", "0", "0", "0"],
            "grid_id": ["a", "b", "c", "d"],
        }
    )


def test_nominal_minute_boundaries_and_type2_are_preserved():
    counts, diagnostic = module.nominal_groups(fires(), detections())
    assert counts.pilot_detection_count.tolist() == [2, 1]
    assert counts.pilot_nominal_high_all_types.tolist() == [1, 1]
    assert counts.archive_type2_nominal_high.tolist() == [1, 0]
    assert diagnostic["uniquely_matched_to_nominal_fire_interval"] == 3
    assert diagnostic["unmatched_to_nominal_fire_interval"] == 1
    assert diagnostic["unmatched_by_utc_day"] == {"2019-06-24": 1}
    assert diagnostic["ambiguous_nominal_interval_match"] == 0


def test_overlapping_nominal_intervals_remain_explicitly_ambiguous():
    overlapping = pd.concat([fires().iloc[:1], fires().iloc[:1]], ignore_index=True)
    _, diagnostic = module.nominal_groups(overlapping, detections())
    assert diagnostic["ambiguous_nominal_interval_match"] == 2
    assert diagnostic["uniquely_matched_to_nominal_fire_interval"] == 0


@pytest.mark.parametrize("day", ["2017-06-24", "2024-06-24", "2025-06-24"])
def test_detection_controls_cannot_use_nontraining_year(day):
    sample = detections().iloc[:1].copy()
    sample["detection_timestamp_utc"] = day + "T10:00:00Z"
    with pytest.raises(ValueError, match="Non-training"):
        module.nominal_groups(fires(), sample)


def test_unsorted_detections_are_rejected():
    with pytest.raises(ValueError, match="Bad detection times"):
        module.nominal_groups(fires(), detections().iloc[::-1])


def pairs():
    return pd.DataFrame(
        {
            "sensor": ["SNPP", "SNPP", "N20", "N20"],
            "pair_key": ["2019175.1000", "2019175.2200", "2019175.1100", "2019175.2300"],
            "day": ["2019-06-24"] * 4,
            "year": [2019] * 4,
            "month": [6] * 4,
            "start_utc": [
                "2019-06-24T10:00:00Z",
                "2019-06-24T22:00:00Z",
                "2019-06-24T11:00:00Z",
                "2019-06-24T23:00:00Z",
            ],
            "day_night": ["DAY", "NIGHT", "DAY", "NIGHT"],
            "pair_status": ["nominal_unique_pair"] * 4,
            "pilot_nominal_high_all_types": [5, 2, 3, 1],
            "nominal_high_grid_count": [2, 1, 2, 1],
            "pair_bytes_estimate": [100, 200, 150, 250],
        }
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("pair_status", "geolocation_only"),
        ("day_night", "UNKNOWN"),
        ("month", 1),
        ("pilot_nominal_high_all_types", 0),
    ],
)
def test_unresolved_non_summer_and_no_detection_pairs_not_shortlisted(field, value):
    sample = pairs()
    sample.loc[0, field] = value
    assert "2019175.1000" not in module.shortlist_pairs(sample).pair_key.tolist()


def test_stress_sampling_does_not_duplicate_strata_and_ties_are_deterministic():
    sample = pd.concat([pairs(), pairs().iloc[:1]], ignore_index=True)
    sample.loc[4, "pair_key"] = "2019175.0948"
    chosen = module.shortlist_pairs(sample)
    assert len(chosen) == 4
    assert "2019175.0948" in chosen.pair_key.tolist()


def test_day_requires_both_sensors_and_modes_and_all_catalogue_pairs():
    module.day_plan(pairs(), "2019-06-24")
    for field, value in (("sensor", "SNPP"), ("day_night", "DAY"), ("pair_status", "fire_only")):
        sample = pairs()
        sample[field] = value
        with pytest.raises(ValueError):
            module.day_plan(sample, "2019-06-24")


def test_cost_option_is_an_estimate_without_download_or_label_permission():
    option = module.describe_option(pairs(), "control")
    assert option["source_files"] == 8
    assert option["catalogue_bytes_estimate"] == 700
    assert option["largest_temporary_pair_bytes_estimate"] == 250
    assert option["cloud_condition"] == "not_assessed"
    assert option["raw_download_started"] is False
    assert option["negative_label_permitted"] is False
    assert option["actual_input_identity_verified"] is False


def test_duplicate_pairs_cannot_inflate_planned_bytes():
    with pytest.raises(ValueError, match="Duplicate"):
        module.describe_option(pd.concat([pairs(), pairs()]), "control")
