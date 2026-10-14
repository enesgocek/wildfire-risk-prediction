"""Graph evidence does not turn recurrence, Type context or missing days into labels."""

import hashlib
import json

import pandas as pd
import pytest

from wildfire_risk_prediction.event_case_trace import shortest, trace_cases
from wildfire_risk_prediction.target_admission import detection_windows


def inputs():
    source = pd.DataFrame(
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
                ("a", "G1", "2019-05-01T10:00:00+00:00", 31.0),
                ("a2", "G2", "2019-05-01T10:00:00+00:00", 31.0001),
                ("b", "G1", "2019-05-03T10:00:00+00:00", 31.007),
                ("c", "G1", "2019-05-05T10:00:00+00:00", 31.014),
            )
        ]
    )
    cases, members = [], []
    for cid, scenario, keys in (
        ("BROAD", "d1000m_t72h", ["a", "a2", "b", "c"]),
        ("FINE", "d500m_t72h", ["c"]),
    ):
        frame = source.loc[source.detection_id.isin(keys)].copy()
        earliest = frame.loc[frame.detection_timestamp_utc.eq(frame.detection_timestamp_utc.min())]
        first = frame.detection_timestamp_utc.min()
        cases.append(
            {
                "cluster_id": cid,
                "scenario": scenario,
                "review_family_id": "F",
                "target": None,
                "detection_count": len(frame),
                "first_detection_utc": first,
                "last_detection_utc": frame.detection_timestamp_utc.max(),
                "candidate_prediction_timestamp_utc": detection_windows(pd.Series([first]))
                .iloc[0]
                .prediction_timestamp_utc.isoformat(),
                "earliest_grid_ids_json": json.dumps(sorted(earliest.grid_id.unique())),
                "earliest_detection_count": len(earliest),
                "membership_sha256": hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest(),
            }
        )
        frame["cluster_id"], frame["scenario"] = cid, scenario
        members.append(frame)
    source["nearest_static_distance_m_within_1000m"] = [20.0, 25.0, 30.0, None]
    source["static_prior_records_1000m"] = [1, 2, 3, 0]
    source["static_simultaneous_records_1000m"] = 0
    source["static_later_records_1000m"] = 0
    return pd.DataFrame(cases), pd.concat(members, ignore_index=True), source, ["2019-05-06"]


def test_local_edges_allow_long_total_duration_and_preserve_all_first_ties():
    summary, paths, comparison, points = trace_cases(*inputs())
    broad = summary.loc[summary.cluster_id.eq("BROAD")].iloc[0]
    assert broad.duration_hours == 96 > broad.edge_gap_limit_hours
    assert broad.maximum_first_to_anchor_path_hops == 2
    p = paths.loc[paths.cluster_id.eq("BROAD")]
    assert set(p.first_detection_id) == {"a", "a2"}
    assert p.edge_absolute_gap_hours.dropna().le(72).all()
    assert p.edge_distance_m.dropna().le(1000).all()
    assert not p.path_is_spread_direction.any()
    assert json.loads(broad.deferred_days_in_context_calendar_envelope_json) == ["2019-05-06"]
    assert summary.target.isna().all() and points.target.isna().all()
    assert not comparison.same_physical_event_accepted.any()
    assert comparison.iloc[0].nested_memberships
    assert points.static_prior_records_1000m.gt(0).sum() == 3
    assert len(points) == 4  # No exclusion for prior Type context; no-match distance stays missing.
    assert pd.isna(
        points.loc[points.detection_id.eq("c"), "nearest_static_distance_m_within_1000m"].iloc[0]
    )
    fine = summary.loc[summary.cluster_id.eq("FINE")].iloc[0]
    assert fine.maximum_first_to_anchor_path_hops == 0
    assert len(paths.loc[paths.cluster_id.eq("FINE")]) == 1  # A zero-edge witness retains its node.


def test_trace_is_row_order_invariant():
    args = inputs()
    expected = trace_cases(*args)
    actual = trace_cases(*(x.sample(frac=1, random_state=42) for x in args[:3]), args[3])
    for a, b in zip(expected, actual, strict=True):
        pd.testing.assert_frame_equal(a.reset_index(drop=True), b.reset_index(drop=True))


def test_disconnected_saved_membership_is_rejected():
    c, m, p, days = inputs()
    c.loc[c.cluster_id.eq("BROAD"), "scenario"] = "d500m_t72h"
    m.loc[m.cluster_id.eq("BROAD"), "scenario"] = "d500m_t72h"
    with pytest.raises(ValueError, match="disconnected"):
        trace_cases(c, m, p, days)


def test_no_common_anchor_is_not_invented_from_a_family_name():
    c, m, p, days = inputs()
    c.loc[0] = c.iloc[1]
    c.loc[0, "cluster_id"] = "OTHER"
    c.loc[0, "first_detection_utc"] = c.loc[0, "last_detection_utc"] = "2019-05-03T10:00:00+00:00"
    m = pd.concat(
        [m.loc[m.cluster_id.eq("FINE")], m.loc[m.detection_id.eq("b")].assign(cluster_id="OTHER")]
    )
    with pytest.raises(ValueError, match="common anchor"):
        trace_cases(c, m, p.loc[p.detection_id.isin(["b", "c"])], days)


@pytest.mark.parametrize(
    "corruption",
    [
        "target",
        "hash",
        "first_tie",
        "source_coordinate",
        "source_time",
        "source_count",
        "fractional_count",
        "scenario",
        "unknown_scenario",
        "duplicate_member",
        "duplicate_context",
        "changed_shared_point",
        "holdout",
        "source_exception_holdout",
    ],
)
def test_invalid_evidence_is_rejected(corruption):
    c, m, p, days = inputs()
    if corruption == "target":
        c.loc[0, "target"] = 0
    elif corruption == "hash":
        c.loc[0, "membership_sha256"] = "0" * 64
    elif corruption == "first_tie":
        c.loc[0, "earliest_grid_ids_json"] = '["G1"]'
    elif corruption == "source_coordinate":
        p.loc[0, "longitude"] += 0.001
    elif corruption == "source_time":
        p.loc[0, "detection_timestamp_utc"] = "2019-05-02T10:00:00+00:00"
    elif corruption == "source_count":
        p.loc[0, "static_prior_records_1000m"] = -1
    elif corruption == "fractional_count":
        p["static_prior_records_1000m"] = 0.5
    elif corruption == "scenario":
        m.loc[0, "scenario"] = "d2000m_t72h"
    elif corruption == "unknown_scenario":
        c.loc[0, "scenario"] = "d9999m_t72h"
    elif corruption == "duplicate_member":
        m = pd.concat([m, m.iloc[:1]], ignore_index=True)
    elif corruption == "duplicate_context":
        p = pd.concat([p, p.iloc[:1]], ignore_index=True)
    elif corruption == "changed_shared_point":
        m.loc[m.cluster_id.eq("FINE"), "longitude"] += 0.001
    elif corruption == "holdout":
        m.loc[0, "detection_timestamp_utc"] = "2025-05-01T10:00:00+00:00"
    else:
        days = ["2024-01-01"]
    with pytest.raises(ValueError):
        trace_cases(c, m, p, days)


def test_shortest_path_tie_break_and_no_path():
    adjacency = {"a": {"c", "b"}, "b": {"d"}, "c": {"d"}, "d": set()}
    assert shortest(adjacency, "a", "d") == ["a", "b", "d"]
    with pytest.raises(ValueError, match="not connected"):
        shortest(adjacency, "d", "a")
