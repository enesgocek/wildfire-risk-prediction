"""Local graph witnesses and retrospective source context, without event adjudication."""

import hashlib
import json
import re
from collections import deque
from itertools import combinations

import numpy as np
import pandas as pd

from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import assert_targets_unassigned, detection_windows

STATIC = [
    "nearest_static_distance_m_within_1000m",
    "static_prior_records_1000m",
    "static_simultaneous_records_1000m",
    "static_later_records_1000m",
]


def shortest(adjacency, start, end):
    """Deterministic fewest-edge path; graph edges are undirected, not spread direction."""
    previous, queue = {start: None}, deque([start])
    while queue:
        node = queue.popleft()
        if node == end:
            path = []
            while node is not None:
                path.append(node)
                node = previous[node]
            return path[::-1]
        for other in sorted(adjacency[node]):
            if other not in previous:
                previous[other] = node
                queue.append(other)
    raise ValueError("Saved case is not connected under its registered scenario")


def trace_cases(cases, members, proximity, deferred_days):
    assert_targets_unassigned(cases)
    require(cases.cluster_id.is_unique, "Unique trace cases")
    require(
        set(members.cluster_id) == set(cases.cluster_id)
        and not members.duplicated(["cluster_id", "detection_id"]).any(),
        "Exact trace case members",
    )
    attrs = [
        "grid_id",
        "source_sensor",
        "detection_timestamp_utc",
        "latitude",
        "longitude",
        "type",
        "confidence",
    ]
    require(
        members.groupby("detection_id")[attrs].nunique(dropna=False).le(1).all().all(),
        "Shared trace detection attributes agree",
    )
    union = training_detections(members.drop_duplicates("detection_id"))
    require(
        proximity.detection_id.is_unique and set(proximity.detection_id) == set(union.detection_id),
        "Exact source-context detection keys",
    )
    context = proximity.set_index("detection_id").loc[union.detection_id]
    for col in ("latitude", "longitude"):
        require(
            np.array_equal(context[col].to_numpy(), union[col].to_numpy()), "Source coordinates"
        )
    require(
        pd.to_datetime(context.detection_timestamp_utc, utc=True).to_numpy().tolist()
        == union.timestamp.to_numpy().tolist(),
        "Source context times agree",
    )
    counts = context[STATIC[1:]].to_numpy(float)
    distance = context[STATIC[0]].dropna().to_numpy(float)
    require(
        np.isfinite(counts).all()
        and (counts >= 0).all()
        and (counts == np.floor(counts)).all()
        and np.isfinite(distance).all()
        and (distance >= 0).all()
        and (distance <= 1000).all(),
        "Valid retrospective proximity diagnostics",
    )
    deferred = [pd.Timestamp(day, tz="UTC") for day in deferred_days]
    require(all(2018 <= t.year <= 2023 for t in deferred), "Training source exceptions")
    context = context[STATIC].copy()
    context.index = union.detection_id
    points = union.merge(context, left_on="detection_id", right_index=True, validate="one_to_one")
    points = points.drop(columns="timestamp")
    points["source_context_status"] = "retrospective_type_semantics_pending_not_exclusion"
    points["target"] = pd.Series(pd.NA, index=points.index, dtype="Int8")
    summaries, paths, comparisons = [], [], []
    for family, group in cases.groupby("review_family_id", sort=True):
        sets = {
            r.cluster_id: set(members.loc[members.cluster_id.eq(r.cluster_id), "detection_id"])
            for r in group.itertuples()
        }
        common = set.intersection(*sets.values())
        require(
            bool(common), "A common anchor is required; transitive overlap alone is insufficient"
        )
        anchor = union.loc[union.detection_id.isin(common)].iloc[0].detection_id
        for row in group.sort_values("cluster_id").itertuples():
            match = re.fullmatch(r"d(500|1000|2000)m_t(24|48|72)h", row.scenario)
            require(match is not None, "Registered trace scenario")
            radius, gap = map(int, match.groups())
            frame = union.loc[union.detection_id.isin(sets[row.cluster_id])].reset_index(drop=True)
            earliest = frame.loc[frame.timestamp.eq(frame.timestamp.min())]
            window = detection_windows(pd.Series([row.first_detection_utc])).iloc[0]
            require(
                len(frame) == row.detection_count
                and members.loc[members.cluster_id.eq(row.cluster_id), "scenario"]
                .eq(row.scenario)
                .all()
                and frame.timestamp.min() == pd.Timestamp(row.first_detection_utc)
                and frame.timestamp.max() == pd.Timestamp(row.last_detection_utc)
                and hashlib.sha256("\n".join(sorted(frame.detection_id)).encode()).hexdigest()
                == row.membership_sha256
                and sorted(earliest.grid_id.unique()) == json.loads(row.earliest_grid_ids_json)
                and len(earliest) == row.earliest_detection_count
                and window.prediction_timestamp_utc
                == pd.Timestamp(row.candidate_prediction_timestamp_utc),
                "Case hash, times, all first cells and target window agree",
            )
            adjacency = {i: set() for i in frame.detection_id}
            edges = {}
            for a, b in combinations(frame.itertuples(), 2):
                _, _, d = GEOD.inv(a.longitude, a.latitude, b.longitude, b.latitude)
                hours = abs((b.timestamp - a.timestamp).total_seconds()) / 3600
                if d <= radius and hours <= gap:
                    adjacency[a.detection_id].add(b.detection_id)
                    adjacency[b.detection_id].add(a.detection_id)
                    edges[frozenset([a.detection_id, b.detection_id])] = (d, hours)
            # Confirm every retained point belongs to the existing case's graph.
            visited, queue = {anchor}, deque([anchor])
            while queue:
                for other in adjacency[queue.popleft()]:
                    if other not in visited:
                        visited.add(other)
                        queue.append(other)
            require(visited == set(frame.detection_id), "Saved case graph disconnected")
            longest_path = 0
            for start in earliest.detection_id:
                path = shortest(adjacency, start, anchor)
                longest_path = max(longest_path, len(path) - 1)
                for step, node in enumerate(path):
                    point = frame.set_index("detection_id").loc[node]
                    edge = edges[frozenset([path[step - 1], node])] if step else (None, None)
                    paths.append(
                        {
                            "review_family_id": family,
                            "cluster_id": row.cluster_id,
                            "scenario": row.scenario,
                            "first_detection_id": start,
                            "review_anchor_id": anchor,
                            "path_step": step,
                            "detection_id": node,
                            "timestamp_utc": point.timestamp.isoformat(),
                            "grid_id": point.grid_id,
                            "edge_distance_m": edge[0],
                            "edge_absolute_gap_hours": edge[1],
                            "path_is_spread_direction": False,
                        }
                    )
            interval = pd.Timedelta(gap, unit="h")
            low = (frame.timestamp.min() - interval).normalize()
            high = (frame.timestamp.max() + interval).normalize()
            relevant = [t.date().isoformat() for t in deferred if low <= t <= high]
            ctx = context.loc[frame.detection_id]
            summaries.append(
                {
                    "review_family_id": family,
                    "cluster_id": row.cluster_id,
                    "scenario": row.scenario,
                    "member_detections": len(frame),
                    "first_detection_utc": frame.timestamp.min().isoformat(),
                    "last_detection_utc": frame.timestamp.max().isoformat(),
                    "duration_hours": (
                        frame.timestamp.max() - frame.timestamp.min()
                    ).total_seconds()
                    / 3600,
                    "edge_distance_limit_m": radius,
                    "edge_gap_limit_hours": gap,
                    "graph_edge_count": len(edges),
                    "review_anchor_id": anchor,
                    "maximum_first_to_anchor_path_hops": longest_path,
                    "members_with_prior_type2_within_1000m": int(
                        ctx.static_prior_records_1000m.gt(0).sum()
                    ),
                    "deferred_days_in_context_calendar_envelope_json": json.dumps(relevant),
                    "context_extends_outside_training": low.year < 2018 or high.year > 2023,
                    "assessment_status": "automated_trace_not_adjudicated",
                    "target": None,
                }
            )
        for a, b in combinations(group.sort_values("cluster_id").itertuples(), 2):
            x, y = sets[a.cluster_id], sets[b.cluster_id]
            comparisons.append(
                {
                    "review_family_id": family,
                    "case_a": a.cluster_id,
                    "case_b": b.cluster_id,
                    "shared_detection_count": len(x & y),
                    "union_detection_count": len(x | y),
                    "a_only_detection_count": len(x - y),
                    "b_only_detection_count": len(y - x),
                    "nested_memberships": x <= y or y <= x,
                    "same_target_window": a.candidate_prediction_timestamp_utc
                    == b.candidate_prediction_timestamp_utc,
                    "same_physical_event_accepted": False,
                }
            )
    return pd.DataFrame(summaries), pd.DataFrame(paths), pd.DataFrame(comparisons), points
