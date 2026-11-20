import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def proposal():
    path = (
        Path(__file__).resolve().parents[1] / "scripts/quality/prepare_satellite_pu_L_proposals.py"
    )
    spec = importlib.util.spec_from_file_location("sat_L_proposal_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_WF1538_boundary_mixed_and_other_first_cells_are_preserved_without_membership(proposal):
    policy = json.loads(proposal.POLICY.read_bytes())
    frame = pd.DataFrame(
        {
            "grid_id": ["A", "B", "C", policy["WF1538_retained_key"][0]],
            "prediction_timestamp_utc": ["2022-05-27T00:00:00+00:00"] * 4,
            "all_first_centers_woody_2017": [True, False, True, True],
            "all_first_centers_woody_both_maps": [False] * 4,
            "fit_role_boundary_review": [False, False, True, False],
            "target": [None] * 4,
            "weak_positive_membership": [None] * 4,
        }
    )
    result = proposal.propose(frame, policy)
    assert len(result) == 4 and result.possible_L_proposal.tolist() == [True, False, False, False]
    assert result.target.isna().all() and result.weak_positive_membership.isna().all()
    assert result.loc[3, "proposal_status"] == "retained_outside_L_by_researcher"
    assert result.loc[0, "proposal_status"] == "possible_L_not_accepted"


def test_requiring_CORINE_or_granting_training_cannot_be_silently_enabled(proposal):
    policy = json.loads(proposal.POLICY.read_bytes())
    for flag in ("CORINE_2018_required_for_proposal", "model_training_authorized"):
        with pytest.raises(ValueError):
            proposal.propose(pd.DataFrame(), policy | {flag: True})
