"""Multiple positive observation fragments must not establish daily negatives."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "comparison",
    Path(__file__).resolve().parents[1] / "scripts/firms/compare_l2_observation_samples.py",
)
comparison = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comparison)


def frame(ids, counts):
    return pd.DataFrame(
        {
            "grid_id": ids,
            "land": counts,
            "land_nominal_input_no_residual": counts,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
        }
    )


def test_union_aligns_by_grid_key_and_preserves_unknown_daily_status():
    a = frame(["a", "b", "c"], [1, 0, 0])
    b = frame(["c", "b", "a"], [0, 2, 0])
    result = comparison.compare_frames({"night": a, "day": b}).set_index("grid_id")
    assert result.any_sample_has_nominal_land_center.to_dict() == {"a": True, "b": True, "c": False}
    assert not result.all_samples_have_nominal_land_center.any()
    assert result.daily_observation_status.eq("unknown").all()
    assert not result.negative_label_permitted.any()


@pytest.mark.parametrize("ids", [["a", "a"], ["a", "c"]])
def test_missing_or_duplicate_grid_keys_are_rejected(ids):
    with pytest.raises(ValueError, match="grid keys"):
        comparison.compare_frames({"night": frame(["a", "b"], [1, 1]), "day": frame(ids, [1, 1])})


def test_preexisting_negative_permission_cannot_enter_sample_comparison():
    a = frame(["a"], [1])
    b = frame(["a"], [1])
    b["negative_label_permitted"] = True
    with pytest.raises(ValueError, match="unresolved diagnostic"):
        comparison.compare_frames({"night": a, "day": b})


def test_sensor_namespaces_preserve_same_time_swaths_separately():
    a = frame(["a", "b"], [1, 0])
    b = frame(["a", "b"], [0, 1])
    result = comparison.compare_frames({"SNPP:2019014.0930": a, "N20:2019014.0930": b})
    assert result.any_sample_has_nominal_land_center.all()
    assert not result.all_samples_have_nominal_land_center.any()
    assert comparison.parse_sample_key("2019014.0930") == ("SNPP", "2019014.0930")
    assert comparison.parse_sample_key("N20:2019014.0930") == ("N20", "2019014.0930")


@pytest.mark.parametrize("key", ["N21:2019014.0930", "../2019014.0930"])
def test_unknown_sensor_and_malformed_sample_key_are_rejected(key):
    with pytest.raises(ValueError, match="Invalid sensor/sample key"):
        comparison.parse_sample_key(key)
