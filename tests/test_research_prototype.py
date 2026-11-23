import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def builder():
    spec = importlib.util.spec_from_file_location(
        "prototype_builder", ROOT / "scripts/quality/build_research_prototype.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_research_direction_is_not_verified_risk_or_new_year_permission():
    m = builder()
    p = json.loads((ROOT / "configs/research_prototype_direction_v1.json").read_bytes())
    m.validate(p)
    for k in (
        "new_training_authorized",
        "scientific_years_2023_2024_2025_open_authorized",
        "probability_or_validated_risk_colors_authorized",
        "final_merge_authorized",
    ):
        with pytest.raises(ValueError, match="No promotion"):
            m.validate(p | {k: True})


def test_payload_preserves_missing_as_null_not_zero():
    m = builder()
    assert m.finite(float("nan")) is None
    assert m.finite(float("inf")) is None
    assert m.finite(0) == 0
