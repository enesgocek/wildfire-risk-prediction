import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def prepare(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "cross_source_scope_test", folder / "prepare_cross_source_calendar_features.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "flag",
    [
        "new_model_fitting_authorized",
        "scientific_values_2023_2024_2025_read_permitted",
        "final_merge_permitted",
    ],
)
def test_separate_source_choice_keeps_fit_year_and_merge_gates_closed(prepare, flag):
    config = json.loads(prepare.CONFIG.read_bytes())
    prepare.validate(config)
    with pytest.raises(ValueError):
        prepare.validate(config | {flag: True})
