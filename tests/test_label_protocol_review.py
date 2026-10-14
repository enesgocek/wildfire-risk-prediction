"""Scenario comparison is an evidence queue, never automatic target admission."""

import json

import pandas as pd
import pytest
from test_window_pilot import prepared

from wildfire_risk_prediction.label_protocol_review import FLAGS, SCENARIOS, compare_catalogs
from wildfire_risk_prediction.observation_window_pilot import append_diagnostics


def catalogs(cells=("G3", "G4")):
    row = {
        "membership_sha256": "a" * 64,
        "first_detection_utc": "2022-01-18T12:00:00Z",
        "candidate_prediction_timestamp_utc": "2022-01-18T00:00:00Z",
        "earliest_grid_ids_json": json.dumps(list(cells)),
        "earliest_grid_count": len(cells),
        "event_status": "exploratory_cluster_only",
        "negative_label_permitted": False,
        **{f: False for f in FLAGS if f != "training_window_boundary_review"},
    }
    row["multi_grid_first_detection_review"] = len(cells) > 1
    return {s: pd.DataFrame([{**row, "cluster_id": s + "_C1"}]) for s in SCENARIOS}


def test_all_tied_first_cells_match_and_membership_agreement_does_not_assign_labels():
    original, summaries, scope = prepared()
    sample = append_diagnostics(original, summaries, scope)
    result, matches, overview = compare_catalogs(sample, catalogs(), sample.grid_id)
    assert len(matches) == 9 * len(sample) and len(overview) == 9
    for grid in ("G3", "G4"):
        row = result.loc[result.grid_id.eq(grid)].iloc[0]
        assert row.scenarios_with_candidate == 9
        assert row.catalog_match_state == "all_scenarios_match_memberships_equal"
        assert "multi_grid_first_detection_review" in json.loads(row.catalog_review_flags_json)
    pd.testing.assert_frame_equal(result[sample.columns], sample)
    assert result.target.isna().all() and not result.route_is_label_admission.any()
    assert result.protocol_status.eq("draft_unaccepted").all()
    assert (
        result.loc[result.grid_id.eq("G0"), "proposed_review_route"].iloc[0]
        == "outside_water_scope_audit_only"
    )


def test_presence_agreement_does_not_hide_different_memberships_and_no_match_is_not_negative():
    original, summaries, scope = prepared()
    sample = append_diagnostics(original, summaries, scope)
    different = catalogs(("G3",))
    different[SCENARIOS[0]]["membership_sha256"] = "b" * 64
    result, _, _ = compare_catalogs(sample, different, sample.grid_id)
    assert (
        result.loc[result.grid_id.eq("G3"), "catalog_match_state"].iloc[0]
        == "all_scenarios_match_memberships_differ"
    )
    assert (
        result.loc[result.grid_id.eq("G2"), "catalog_match_state"].iloc[0]
        == "no_candidate_in_any_scenario"
    )
    assert result.target.isna().all()
    different[SCENARIOS[0]]["earliest_grid_ids_json"] = '["G2"]'
    result, _, _ = compare_catalogs(sample, different, sample.grid_id)
    assert result.loc[result.grid_id.eq("G3"), "scenarios_with_candidate"].iloc[0] == 8
    assert result.loc[result.grid_id.eq("G2"), "scenarios_with_candidate"].iloc[0] == 1


@pytest.mark.parametrize("problem", ["missing_scenario", "unknown_grid", "label", "gate"])
def test_changed_protocol_or_coverage_rejected(problem):
    original, summaries, scope = prepared()
    sample = append_diagnostics(original, summaries, scope)
    source = catalogs()
    if problem == "missing_scenario":
        source.pop(SCENARIOS[0])
    elif problem == "unknown_grid":
        source = catalogs(("not_in_scope",))
    elif problem == "label":
        sample["target"] = 0
    else:
        sample["window_negative_label_permitted"] = True
    with pytest.raises(ValueError):
        compare_catalogs(sample, source, sample.grid_id)
