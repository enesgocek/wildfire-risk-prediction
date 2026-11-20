import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def pilot(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "sat_ablation_test", folder / "run_satellite_pu_ablation_pilot.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("variant", ["weather_only", "static_cover_terrain_only"])
def test_ablation_excludes_other_groups_without_mutating_original_X(pilot, variant):
    frame = pd.DataFrame({name: [1.0, np.nan, 3.0] for name in pilot.join.feature_names()})
    previous = frame.copy(deep=True)
    masked = pilot.masked_features(frame, variant)
    for name in frame:
        if name in pilot.VARIANTS[variant]:
            pd.testing.assert_series_equal(masked[name], previous[name])
        else:
            assert masked[name].isna().all()
    pd.testing.assert_frame_equal(frame, previous)


def test_post_T_metadata_and_undeclared_variants_are_rejected(pilot):
    frame = pd.DataFrame({name: [1.0] for name in pilot.join.feature_names()})
    with pytest.raises(ValueError):
        pilot.masked_features(frame, "chosen_after_scoring")
    frame["future_satellite_confidence"] = 95
    with pytest.raises(ValueError):
        pilot.masked_features(frame, "weather_only")


def test_previous_27_fit_permission_cannot_start_an_eighteenth_new_model(
    pilot, tmp_path, monkeypatch
):
    plan = tmp_path / "plan.json"
    plan.write_text("{}", encoding="utf-8")
    execution = tmp_path / "execution.json"
    execution.write_text(
        json.dumps(
            {
                "decision_source": (
                    "explicit_user_selection_A_run_four_province_satellite_auxiliary_pilot"
                ),
                "auxiliary_model_fitting_authorized": True,
                "maximum_fits": 27,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        pilot, "prepared_inputs", lambda: pytest.fail("No new scientific data access")
    )
    with pytest.raises(ValueError, match="New explicit 18-fit"):
        pilot.run(plan, execution)
