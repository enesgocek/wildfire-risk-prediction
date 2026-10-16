"""Birth retention, simultaneous merging, causal ancestry and final partition checks."""

import json

import pandas as pd
import pytest

from wildfire_risk_prediction.event_lineage import trace_lineage, verify_ancestry_records
from wildfire_risk_prediction.event_review import spatial_links


def points(rows):
    return pd.DataFrame(
        [
            {
                "detection_id": key,
                "grid_id": grid,
                "source_sensor": "SNPP",
                "detection_timestamp_utc": time,
                "latitude": 37.0,
                "longitude": lon,
                "type": 0,
                "confidence": "n",
            }
            for key, grid, time, lon in rows
        ]
    )


def bridge():
    return points(
        [
            ("a", "G1", "2019-01-01T23:00:00+00:00", 31.0),
            ("b", "G2", "2019-01-01T23:00:00+00:00", 31.008),
            ("c", "G3", "2019-01-02T00:01:00+00:00", 31.004),
        ]
    )


def run(frame, **kwargs):
    return trace_lineage(frame, distance_m=500, gap_hours=24, **kwargs)


def test_later_merge_keeps_both_births_and_does_not_choose_one_origin_for_bridge():
    births, transitions, states, detections, summary = run(bridge())
    assert len(births) == 2 and transitions.transition.tolist() == ["birth", "birth", "merge"]
    assert summary["final_graph_components"] == 1 and summary["merge_component_reduction"] == 1
    assert detections.set_index("detection_id").origin_candidate_count_at_ingestion.to_dict() == {
        "a": 1,
        "b": 1,
        "c": 2,
    }
    assert len(json.loads(states.iloc[-1].parent_state_ids_json)) == 2
    assert births.target.isna().all() and detections.target.isna().all()
    assert not detections.event_membership_complete.any()
    assert verify_ancestry_records(births, states, detections)["ancestry_dag_verified"]


def test_append_future_preserves_earlier_ingestion_states_and_birth_ledger():
    earlier = run(bridge().iloc[:2])
    later = run(bridge())
    pd.testing.assert_frame_equal(earlier[0], later[0])
    cols = [c for c in earlier[3] if c != "final_graph_membership_sha256"]
    pd.testing.assert_frame_equal(earlier[3][cols], later[3].iloc[:2][cols])


def test_equal_time_ties_share_one_birth_and_are_input_order_invariant():
    frame = bridge().copy()
    frame["detection_timestamp_utc"] = "2019-01-01T23:00:00+00:00"
    a, b = run(frame), run(frame.iloc[::-1])
    assert len(a[0]) == 1
    assert json.loads(a[0].earliest_grid_ids_json.iloc[0]) == ["G1", "G2", "G3"]
    for first, second in zip(a[:4], b[:4], strict=True):
        pd.testing.assert_frame_equal(first, second)


def test_same_time_three_way_merge_is_one_update_with_reduction_two():
    frame = points(
        [
            ("a", "G1", "2019-01-01T01:00:00+00:00", 31.0),
            ("b", "G2", "2019-01-01T01:00:00+00:00", 31.008),
            ("c", "G3", "2019-01-01T01:00:00+00:00", 31.016),
            ("x", "G4", "2019-01-01T02:00:00+00:00", 31.004),
            ("y", "G5", "2019-01-01T02:00:00+00:00", 31.012),
        ]
    )
    births, transitions, _, _, summary = run(frame)
    merges = transitions.loc[transitions.transition.eq("merge")]
    assert len(births) == 3 and len(merges) == 1
    assert merges.predecessor_component_count.tolist() == [3]
    assert summary["merge_component_reduction"] == 2


def test_disconnected_new_branches_sharing_a_previous_component_are_one_continuation():
    frame = points(
        [
            ("a", "G1", "2019-01-01T01:00:00+00:00", 31.0),
            ("b", "G2", "2019-01-01T01:00:00+00:00", 31.004),
            ("c", "G3", "2019-01-01T01:00:00+00:00", 31.008),
            ("x", "G4", "2019-01-01T02:00:00+00:00", 30.996),
            ("y", "G5", "2019-01-01T02:00:00+00:00", 31.012),
        ]
    )
    births, transitions, _, _, _ = run(frame)
    assert len(births) == 1
    assert transitions.transition.tolist() == ["birth", "continuation"]
    assert json.loads(transitions.incoming_detection_ids_json.iloc[-1]) == ["x", "y"]


@pytest.mark.parametrize(("hour", "births"), [("01", 1), ("02", 2)])
def test_inclusive_gap_and_longer_gap(hour, births):
    frame = points(
        [
            ("a", "G1", "2019-01-01T01:00:00+00:00", 31.0),
            ("b", "G1", f"2019-01-02T{hour}:00:00+00:00", 31.0),
        ]
    )
    assert len(run(frame)[0]) == births


@pytest.mark.parametrize("damage", ["holdout", "duplicate", "stale_links", "float_parameter"])
def test_bad_scope_and_provenance_fail_before_lineage(damage):
    frame = bridge()
    kwargs = {}
    if damage == "holdout":
        frame.loc[2, "detection_timestamp_utc"] = "2024-01-01T00:00:00+00:00"
    elif damage == "duplicate":
        frame.loc[2, "detection_id"] = "a"
    elif damage == "stale_links":
        kwargs["links"] = spatial_links(frame, 500)
        frame.loc[2, "longitude"] += 0.01
    else:
        with pytest.raises(ValueError, match="Saved scenario"):
            trace_lineage(frame, distance_m=500.0, gap_hours=24)
        return
    with pytest.raises(ValueError):
        run(frame, **kwargs)


@pytest.mark.parametrize("damage", ["missing_parent", "cycle", "count", "future_state"])
def test_independent_parent_dag_readback_rejects_corruption(damage):
    born, _, states, detected, _ = run(bridge())
    if damage == "missing_parent":
        states.loc[2, "parent_state_ids_json"] = '["missing"]'
    elif damage == "cycle":
        states.loc[2, "parent_state_ids_json"] = json.dumps([states.ancestry_state_id.iloc[2]])
    elif damage == "count":
        detected.loc[2, "origin_candidate_count_at_ingestion"] = 1
    else:
        detected.loc[0, "ancestry_state_id_at_ingestion"] = states.ancestry_state_id.iloc[2]
        detected.loc[0, "origin_candidate_count_at_ingestion"] = 2
    with pytest.raises(ValueError):
        verify_ancestry_records(born, states, detected)
