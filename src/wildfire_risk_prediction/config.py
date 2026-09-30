"""Load and validate the agreed pilot protocol before any experiment."""

from pathlib import Path
from typing import Any

import yaml

PILOT_PROVINCES = {"Antalya", "Muğla", "İzmir", "Mersin"}
EXPECTED_SPLITS = {"train": [2018, 2023], "validation": [2024, 2024], "final_test": [2025, 2025]}


def validate_config(config: Any) -> dict:
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a YAML mapping.")
    required = {
        "project": ("name", "scope", "provinces"),
        "prediction": ("grid_size_m", "horizon_hours", "issue_time_utc", "target"),
        "splits": ("train", "validation", "final_test"),
        "experiment": ("seed", "primary_metric", "name"),
    }
    for section, keys in required.items():
        if not isinstance(config.get(section), dict):
            raise ValueError(f"Missing or invalid section: {section}")
        for key in keys:
            if key not in config[section]:
                raise ValueError(f"Missing required field: {section}.{key}")
    provinces = config["project"]["provinces"]
    if (
        not isinstance(provinces, list)
        or not all(isinstance(province, str) for province in provinces)
        or len(provinces) != 4
        or set(provinces) != PILOT_PROVINCES
    ):
        raise ValueError("Pilot provinces must be Antalya, Muğla, İzmir and Mersin, once each.")
    if config["project"]["scope"] != "pilot":
        raise ValueError("Project scope must be pilot.")
    for split in EXPECTED_SPLITS:
        years = config["splits"][split]
        if (
            not isinstance(years, list)
            or len(years) != 2
            or not all(type(year) is int for year in years)
            or years[0] > years[1]
        ):
            raise ValueError(f"Invalid year range: splits.{split}")
    ranges = [config["splits"][split] for split in EXPECTED_SPLITS]
    for index, first in enumerate(ranges):
        for second in ranges[index + 1 :]:
            if max(first[0], second[0]) <= min(first[1], second[1]):
                raise ValueError("Train, validation and final test years must not overlap.")
    if config["splits"] != EXPECTED_SPLITS:
        raise ValueError("Temporal protocol is fixed: train 2018–2023, validation 2024, test 2025.")
    prediction = config["prediction"]
    if type(prediction["horizon_hours"]) is not int or prediction["horizon_hours"] != 24:
        raise ValueError("Prediction horizon must be 24 hours.")
    if type(prediction["grid_size_m"]) is not int or prediction["grid_size_m"] != 5000:
        raise ValueError("Grid size must be 5000 metres.")
    if prediction["issue_time_utc"] != "00:00" or prediction["target"] != "fire_next_24h":
        raise ValueError("Prediction must use 00:00 UTC and target fire_next_24h.")
    if type(config["experiment"]["seed"]) is not int or config["experiment"]["seed"] < 0:
        raise ValueError("Experiment seed must be a non-negative integer.")
    if config["experiment"]["primary_metric"] != "pr_auc":
        raise ValueError("Primary metric must be pr_auc.")
    for section, key in (("project", "name"), ("experiment", "name")):
        if not isinstance(config[section][key], str) or not config[section][key].strip():
            raise ValueError(f"Field {section}.{key} must be a non-empty string.")
    return config


def load_config(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Configuration file not found: {path}")
    try:
        return validate_config(yaml.safe_load(path.read_text(encoding="utf-8")))
    except yaml.YAMLError as error:
        raise ValueError("Configuration is not valid YAML.") from error
