"""Later bridging, exact cutoffs and equal-time ties must be explicit in diagnostics."""

import json

import pandas as pd
import pytest

from wildfire_risk_prediction.event_window_context import prefix_first_sets


def source():
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
            for key, grid, time, lon in (
                ("a", "G1", "2019-01-01T23:00:00+00:00", 31.0),
                ("b", "G2", "2019-01-01T23:00:00+00:00", 31.008),
                ("bridge", "G3", "2019-01-02T00:01:00+00:00", 31.004),
            )
        ]
    )


def run(frame=None, end="2019-01-02T00:00:00+00:00", anchors=("a", "b")):
    return prefix_first_sets(
        source() if frame is None else frame,
        list(anchors),
        end_utc=end,
        distance_m=500,
        gap_hours=24,
    )


def test_later_bridge_merges_two_earliest_cell_sets_but_not_before_cutoff():
    before = run()
    after = run(end="2019-01-02T00:01:00+00:00")
    assert len(before) == 2 and len(after) == 1
    assert sorted(before.earliest_grid_ids_json.map(json.loads).sum()) == ["G1", "G2"]
    assert json.loads(after.earliest_grid_ids_json.iloc[0]) == ["G1", "G2"]
    assert before.target.isna().all() and after.target.isna().all()


def test_equal_time_processing_is_invariant_to_source_order():
    pd.testing.assert_frame_equal(run(), run(source().iloc[::-1]))


def test_anchor_in_one_branch_does_not_take_first_cell_from_disconnected_branch():
    before = run(anchors=("b",))
    assert json.loads(before.earliest_grid_ids_json.iloc[0]) == ["G2"]


def test_future_shortcut_does_not_imply_future_dependency_when_prefix_has_another_path():
    frame = source()
    extra = frame.iloc[[0, 0]].copy().reset_index(drop=True)
    extra["detection_id"] = ["pre1", "pre2"]
    extra["grid_id"] = ["G3", "G4"]
    extra["longitude"] = [31.0025, 31.0055]
    extra["detection_timestamp_utc"] = ["2019-01-01T23:05:00+00:00", "2019-01-01T23:10:00+00:00"]
    before = run(pd.concat([frame, extra]))
    assert len(before) == 1
    assert before.member_count.iloc[0] == 4
    assert json.loads(before.earliest_grid_ids_json.iloc[0]) == ["G1", "G2"]


@pytest.mark.parametrize("damage", ["future_anchor", "missing_anchor", "naive", "holdout"])
def test_bad_cutoff_or_source_rejected(damage):
    kwargs = {}
    if damage == "future_anchor":
        kwargs["anchors"] = ("bridge",)
    elif damage == "missing_anchor":
        kwargs["anchors"] = ("missing",)
    elif damage == "naive":
        kwargs["end"] = "2019-01-02T00:00:00"
    else:
        frame = source()
        frame.loc[2, "detection_timestamp_utc"] = "2024-01-01T00:00:00+00:00"
        kwargs["frame"] = frame
    with pytest.raises(ValueError):
        run(**kwargs)
