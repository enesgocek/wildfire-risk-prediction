from copy import deepcopy
from pathlib import Path

import pytest

from wildfire_risk_prediction.config import load_config, validate_config
from wildfire_risk_prediction.protocol import split_directory

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def config():
    return deepcopy(load_config(ROOT / "configs" / "project.yaml"))


def test_current_protocol(config):
    assert config["prediction"]["horizon_hours"] == 24
    assert config["splits"]["final_test"] == [2025, 2025]


@pytest.mark.parametrize("section", ["project", "prediction", "splits", "experiment"])
def test_missing_section_is_actionable(config, section):
    del config[section]
    with pytest.raises(ValueError, match=section):
        validate_config(config)


def test_missing_required_field(config):
    del config["prediction"]["target"]
    with pytest.raises(ValueError, match="prediction.target"):
        validate_config(config)


def test_overlap_is_rejected(config):
    config["splits"]["train"] = [2018, 2024]
    with pytest.raises(ValueError, match="overlap"):
        validate_config(config)


def test_nonoverlapping_but_changed_protocol_is_rejected(config):
    config["splits"]["train"] = [2018, 2022]
    with pytest.raises(ValueError, match="fixed"):
        validate_config(config)


def test_hatay_does_not_replace_mersin(config):
    config["project"]["provinces"] = ["Antalya", "Muğla", "İzmir", "Hatay"]
    with pytest.raises(ValueError, match="Pilot provinces"):
        validate_config(config)


@pytest.mark.parametrize("hours", [72, True, "24"])
def test_invalid_horizon(config, hours):
    config["prediction"]["horizon_hours"] = hours
    with pytest.raises(ValueError, match="24 hours"):
        validate_config(config)


def test_invalid_yaml(tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text("prediction: [", encoding="utf-8")
    with pytest.raises(ValueError, match="valid YAML"):
        load_config(path)


def test_final_test_is_blocked_by_default():
    with pytest.raises(PermissionError, match="sealed"):
        split_directory(ROOT, "final_test")


def test_explicit_final_evaluation_access():
    assert split_directory(ROOT, "final_test", allow_final_test=True).name == "final_test"


@pytest.mark.parametrize("split", ["train", "validation"])
def test_development_splits_are_accessible(split):
    assert split_directory(ROOT, split).name == split


def test_invalid_split_cannot_escape_directory():
    with pytest.raises(ValueError, match="Unknown split"):
        split_directory(ROOT, "../final_test")
