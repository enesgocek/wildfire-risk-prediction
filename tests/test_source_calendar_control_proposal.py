import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def proposal():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/quality/prepare_source_calendar_control_proposal.py"
    )
    spec = importlib.util.spec_from_file_location("calendar_control_proposal_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_anchor_day_is_not_removed_as_if_U_were_verified_negative(proposal):
    anchor = ("A", "2020-02-05T00:00:00+00:00")
    keys, strata = proposal.calendar_keys([anchor, ("A", "2020-02-12T00:00:00+00:00")])
    assert anchor in keys and len(keys) == 29 and len(strata) == 1
    assert ("A", "2020-02-29T00:00:00+00:00") in keys


def test_role_boundary_is_the_only_day_exclusion(proposal):
    keys, _ = proposal.calendar_keys(
        [("A", "2021-12-10T00:00:00+00:00"), ("A", "2022-12-10T00:00:00+00:00")]
    )
    assert len(keys) == 60
    assert ("A", "2021-12-30T00:00:00+00:00") in keys
    assert ("A", "2021-12-31T00:00:00+00:00") not in keys
    assert ("A", "2022-12-31T00:00:00+00:00") not in keys


@pytest.mark.parametrize(
    "stamp", ["2023-01-01T00:00:00+00:00", "2022-01-01T01:00:00+00:00", "2022-01-01T00:00:00"]
)
def test_sealed_year_or_wrong_issue_time_is_rejected(proposal, stamp):
    with pytest.raises(ValueError):
        proposal.calendar_keys([("A", stamp)])


def test_extent_preparation_cannot_grant_new_feature_training_or_label_permissions(proposal):
    policy = json.loads(proposal.POLICY.read_bytes())
    for name in (
        "new_feature_extraction_authorized",
        "new_model_fitting_authorized",
        "negative_label_permitted",
        "method_direction_selected",
    ):
        with pytest.raises(ValueError):
            proposal.validate_policy(policy | {name: True})
