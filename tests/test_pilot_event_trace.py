"""Pilot anchor tracing retains splits, lost matches, first ties and closed label gates."""

import json

import pandas as pd
import pytest

from wildfire_risk_prediction.event_case_trace import shortest
from wildfire_risk_prediction.event_review import (
    review_partition,
    spatial_links,
    training_detections,
)
from wildfire_risk_prediction.label_protocol_review import SCENARIOS
from wildfire_risk_prediction.pilot_event_trace import temporal_graph, trace_sensitive_units


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
                ("a", "G2", "2019-05-01T10:00:00+00:00", 31.0),
                ("a2", "G1", "2019-05-01T10:00:00+00:00", 31.0001),
                ("b", "G1", "2019-05-03T10:00:00+00:00", 31.007),
                ("c", "G1", "2019-05-05T10:00:00+00:00", 31.014),
                ("c2", "G1", "2019-05-05T10:00:00+00:00", 31.0141),
                ("e", "G1", "2019-05-05T10:00:00+00:00", 31.06),
            )
        ]
    )
    source["nearest_static_distance_m_within_1000m"] = 20.0
    source["static_prior_records_1000m"] = 1
    source["static_simultaneous_records_1000m"] = 0
    source["static_later_records_1000m"] = 1
    frame = training_detections(source)
    catalogs, assignments = {}, {}
    for scenario in SCENARIOS:
        radius, gap = int(scenario.split("m")[0][1:]), int(scenario.split("t")[1][:-1])
        groups = [1, 1, 2, 3, 3, 4] if radius == 500 or gap == 24 else [1, 1, 1, 1, 1, 4]
        saved = frame[["detection_id", "grid_id", "source_sensor", "timestamp"]].copy()
        saved["cluster_id"] = [f"{scenario}_C{n}" for n in groups]
        catalog, _ = review_partition(frame, saved, spatial_links(frame, radius), radius, gap)
        catalogs[scenario], assignments[scenario] = catalog, saved
    units = pd.DataFrame(
        [
            {
                "review_unit_id": name,
                "grid_id": grid,
                "prediction_timestamp_utc": f"2019-05-{day:02d}T00:00:00+00:00",
                "target": None,
            }
            for name, grid, day in (("multi", "G1", 5), ("partial", "G1", 3), ("tie", "G2", 1))
        ]
    )
    matches = []
    for row in units.itertuples():
        for scenario, cat in catalogs.items():
            selected = cat.loc[
                cat.candidate_prediction_timestamp_utc.eq(row.prediction_timestamp_utc)
                & cat.earliest_grid_ids_json.map(lambda x, grid=row.grid_id: grid in json.loads(x))
            ]
            matches.append(
                {
                    "review_unit_id": row.review_unit_id,
                    "grid_id": row.grid_id,
                    "prediction_timestamp_utc": row.prediction_timestamp_utc,
                    "scenario": scenario,
                    "candidate_cluster_first_cell_matches": len(selected),
                    "matched_cluster_ids_json": json.dumps(sorted(selected.cluster_id)),
                    "matched_membership_set_json": json.dumps(
                        sorted(set(selected.membership_sha256))
                    ),
                }
            )
    return units, pd.DataFrame(matches), catalogs, assignments, source, ["2019-05-06"]


def test_missing_first_matches_are_traced_via_original_anchors_without_labels():
    summary, contexts, variants, members, paths = trace_sensitive_units(*inputs())
    assert len(summary) == 3
    assert len(contexts[["review_unit_id", "scenario"]].drop_duplicates()) == 27
    partial = summary.set_index("review_unit_id").loc["partial"]
    assert partial.scenarios_with_first_candidate_match == 5
    rows = contexts.loc[contexts.review_unit_id.eq("partial")]
    assert rows.anchor_count.eq(1).all()  # The source record survives in every scenario.
    assert rows.first_match_explanation.eq("earlier_first_window").sum() == 4
    broad = variants.loc[variants.scenario.eq("d1000m_t72h") & variants.detection_count.eq(5)]
    assert broad.iloc[0].duration_hours == 96 > 72
    assert broad.iloc[0].earliest_grid_count == 2
    assert broad.iloc[0].members_with_prior_type2_within_1000m == 5
    multi = contexts.loc[contexts.review_unit_id.eq("multi") & contexts.scenario.eq("d1000m_t72h")]
    assert len(multi) == 2  # No invented single anchor common to disjoint components.
    assert set(members.detection_id) == {"a", "a2", "b", "c", "c2", "e"}
    chain = paths.loc[
        paths.review_unit_id.eq("multi")
        & paths.scenario.eq("d1000m_t72h")
        & paths.first_detection_id.eq("a")
        & paths.anchor_detection_id.eq("c")
    ]
    assert chain.detection_id.tolist() == ["a", "b", "c"]
    assert chain.edge_signed_gap_hours.dropna().tolist() == [48.0, 48.0]
    assert not paths.path_is_spread_direction.any()
    for table in (summary, contexts, variants, members, paths):
        assert table.target.isna().all()


def test_row_order_does_not_choose_first_tie_or_change_trace():
    units, matches, cats, assignments, source, days = inputs()
    expected = trace_sensitive_units(units, matches, cats, assignments, source, days)
    actual = trace_sensitive_units(
        units.iloc[::-1],
        matches.iloc[::-1],
        {k: v.iloc[::-1] for k, v in cats.items()},
        {k: v.iloc[::-1] for k, v in assignments.items()},
        source.iloc[::-1],
        days,
    )
    for left, right in zip(expected, actual, strict=True):
        pd.testing.assert_frame_equal(left, right)


@pytest.mark.parametrize(
    "corruption",
    [
        "target",
        "holdout",
        "assignment_time",
        "assignment_grid",
        "missing_source",
        "duplicate_source",
        "missing_scenario",
        "missing_match",
        "old_match",
        "member_hash",
        "first_tie",
        "negative_gate",
        "negative_context",
        "exception_holdout",
        "duplicate_unit",
    ],
)
def test_inconsistent_or_unadmitted_inputs_fail_closed(corruption):
    u, m, c, a, s, days = inputs()
    scenario = SCENARIOS[0]
    if corruption == "target":
        u.loc[0, "target"] = 1
    elif corruption == "holdout":
        s.loc[0, "detection_timestamp_utc"] = "2024-05-01T10:00:00+00:00"
    elif corruption == "assignment_time":
        a[scenario].loc[0, "timestamp"] += pd.Timedelta(1, unit="h")
    elif corruption == "assignment_grid":
        a[scenario].loc[0, "grid_id"] = "OTHER"
    elif corruption == "missing_source":
        s = s.iloc[1:]
    elif corruption == "duplicate_source":
        s = pd.concat([s, s.iloc[:1]], ignore_index=True)
    elif corruption == "missing_scenario":
        del a[scenario]
    elif corruption == "missing_match":
        m = m.iloc[1:]
    elif corruption == "old_match":
        m.loc[0, "matched_cluster_ids_json"] = "[]"
    elif corruption == "member_hash":
        c[scenario].loc[0, "membership_sha256"] = "0" * 64
    elif corruption == "first_tie":
        c[scenario].loc[0, "earliest_grid_ids_json"] = '["G2"]'
    elif corruption == "negative_gate":
        c[scenario].loc[0, "negative_label_permitted"] = True
    elif corruption == "negative_context":
        s.loc[0, "static_prior_records_1000m"] = -1
    elif corruption == "exception_holdout":
        days = ["2025-01-01"]
    else:
        u = pd.concat([u, u.iloc[:1]], ignore_index=True)
    with pytest.raises(ValueError):
        trace_sensitive_units(u, m, c, a, s, days)


def test_graph_disconnection_and_inclusive_distance_time_limits():
    source = inputs()[4].iloc[:3]
    frame = training_detections(source)
    graph = temporal_graph(frame, 1000, 48)
    assert graph["b"] == {"a", "a2"}
    with pytest.raises(ValueError, match="Disconnected"):
        temporal_graph(frame, 1000, 24)


def refresh(units, assignments, source):
    frame = training_detections(source)
    catalogs, matches = {}, []
    for scenario, saved in assignments.items():
        radius, gap = int(scenario.split("m")[0][1:]), int(scenario.split("t")[1][:-1])
        for col in ("timestamp", "grid_id"):
            saved[col] = saved.detection_id.map(frame.set_index("detection_id")[col])
        catalog, _ = review_partition(frame, saved, spatial_links(frame, radius), radius, gap)
        catalogs[scenario] = catalog
        for row in units.itertuples():
            selected = catalog.loc[
                catalog.candidate_prediction_timestamp_utc.eq(row.prediction_timestamp_utc)
                & catalog.earliest_grid_ids_json.map(
                    lambda x, grid=row.grid_id: grid in json.loads(x)
                )
            ]
            matches.append(
                {
                    "review_unit_id": row.review_unit_id,
                    "grid_id": row.grid_id,
                    "prediction_timestamp_utc": row.prediction_timestamp_utc,
                    "scenario": scenario,
                    "candidate_cluster_first_cell_matches": len(selected),
                    "matched_cluster_ids_json": json.dumps(sorted(selected.cluster_id)),
                    "matched_membership_set_json": json.dumps(
                        sorted(set(selected.membership_sha256))
                    ),
                }
            )
    return pd.DataFrame(matches), catalogs


def test_first_cell_can_change_within_the_same_target_day():
    u, _, _, a, s, days = inputs()
    u = u.loc[u.review_unit_id.eq("partial")]
    s.loc[s.detection_id.isin(["a", "a2"]), "detection_timestamp_utc"] = "2019-05-03T08:00:00+00:00"
    s.loc[s.detection_id.eq("a2"), "grid_id"] = "G2"
    for scenario in SCENARIOS:
        if not scenario.startswith("d500m_") and scenario.endswith("t24h"):
            a[scenario]["cluster_id"] = [f"{scenario}_C{n}" for n in (1, 1, 1, 3, 3, 4)]
    m, c = refresh(u, a, s)
    _, rows, _, _, _ = trace_sensitive_units(u, m, c, a, s, days)
    assert rows.first_time_in_target_window.all()
    assert rows.first_match_explanation.eq("other_first_cell").sum() == 6


def test_exact_right_midnight_is_included_and_left_midnight_is_excluded():
    u, _, _, a, s, days = inputs()
    u = u.loc[u.review_unit_id.eq("multi")].copy()
    u["prediction_timestamp_utc"] = "2019-05-04T00:00:00+00:00"
    s.loc[s.detection_id.isin(["c", "c2"]), "detection_timestamp_utc"] = "2019-05-05T00:00:00+00:00"
    m, c = refresh(u, a, s)
    summary, _, _, _, _ = trace_sensitive_units(u, m, c, a, s, days)
    assert summary.iloc[0].anchor_detection_count == 2
    u["prediction_timestamp_utc"] = "2019-05-05T00:00:00+00:00"
    m, c = refresh(u, a, s)
    summary, _, _, _, _ = trace_sensitive_units(u, m, c, a, s, days)
    assert summary.iloc[0].anchor_detection_count == 1  # Only e; c/c2 at T are excluded.


def test_undirected_shortest_witness_can_move_backwards_in_time():
    s = inputs()[4].loc[lambda x: x.detection_id.isin(["a", "b", "c"])].copy()
    s.loc[s.detection_id.eq("c"), "detection_timestamp_utc"] = "2019-05-02T10:00:00+00:00"
    frame = training_detections(s)
    graph = temporal_graph(frame, 1000, 48)
    chain = shortest(graph, "a", "c")
    assert chain == ["a", "b", "c"]
    times = frame.set_index("detection_id").loc[chain].timestamp
    assert times.diff().iloc[-1] == -pd.Timedelta(24, unit="h")
