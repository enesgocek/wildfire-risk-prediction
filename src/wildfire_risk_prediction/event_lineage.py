"""Chronological connected-component ancestry diagnostic; not physical fire tracking."""

import hashlib
import json
from collections import defaultdict

import numpy as np
import pandas as pd

from wildfire_risk_prediction.event_review import (
    SpatialLinks,
    spatial_fingerprint,
    spatial_links,
    training_detections,
)
from wildfire_risk_prediction.feature_join import require

VERSION = "event_lineage_diagnostic_v1"


def identity(kind, scenario, keys):
    return (
        kind
        + "_"
        + hashlib.sha256(
            json.dumps([scenario, sorted(keys)], separators=(",", ":")).encode()
        ).hexdigest()
    )


def verify_ancestry_records(births, states, detections):
    """Independently traverse the saved parent DAG and reconcile ingestion states."""
    require(
        births.birth_candidate_id.is_unique and states.ancestry_state_id.is_unique,
        "Unique ancestry identities",
    )
    require(
        births.target.isna().all()
        and detections.target.isna().all()
        and detections.event_membership_complete.eq(False).all(),
        "Unadmitted ancestry",
    )
    born = births.set_index("birth_candidate_id")
    resolved, created = {}, {}
    for state in states.sort_values(["recorded_at_utc", "ancestry_state_id"]).itertuples():
        parents = json.loads(state.parent_state_ids_json)
        now = pd.Timestamp(state.recorded_at_utc)
        require(
            isinstance(parents, list)
            and len(parents) == len(set(parents))
            and all(p in resolved and created[p] < now for p in parents),
            "Earlier existing parent states only",
        )
        if not parents:
            require(state.birth_candidate_id in born.index, "Existing birth for leaf state")
            origins = frozenset([state.birth_candidate_id])
            require(
                pd.Timestamp(born.loc[state.birth_candidate_id, "first_detection_utc"]) == now,
                "Birth/leaf state time agreement",
            )
        else:
            require(
                len(parents) >= 2
                and (pd.isna(state.birth_candidate_id) or state.birth_candidate_id == ""),
                "Merge has no new birth identity",
            )
            origins = frozenset().union(*(resolved[p] for p in parents))
            require(
                len(origins) == sum(len(resolved[p]) for p in parents),
                "Distinct predecessor origins",
            )
        scenarios = set(born.loc[sorted(origins), "scenario"])
        require(
            len(scenarios) == 1
            and state.ancestry_state_id == identity("state", next(iter(scenarios)), origins)
            and state.origin_candidate_count == len(origins),
            "State identity/count agreement",
        )
        resolved[state.ancestry_state_id], created[state.ancestry_state_id] = origins, now
    require(frozenset().union(*resolved.values()) == set(born.index), "All births retained")
    counts = detections.ancestry_state_id_at_ingestion.map({k: len(v) for k, v in resolved.items()})
    created_times = pd.to_datetime(detections.ancestry_state_id_at_ingestion.map(created), utc=True)
    require(
        counts.notna().all()
        and counts.eq(detections.origin_candidate_count_at_ingestion).all()
        and created_times.le(pd.to_datetime(detections.timestamp_utc, utc=True)).all(),
        "Ingestion has complete nonfuture ancestry state references",
    )
    return {
        "ancestry_dag_verified": True,
        "birth_candidates_retained": len(born),
        "ancestry_states_verified": len(states),
        "detection_state_rows_verified": len(detections),
    }


def trace_lineage(source, *, distance_m, gap_hours, links=None):
    """Use saved point-edge rules, processing equal recorded times as one batch.

    Birth candidates are never erased after a graph merge. New detections after
    a merge retain an ambiguous ancestor state, rather than choosing one birth.
    States form a DAG; no quadratic ancestry lists are written for every pixel.
    The final partition is the same static graph, not an alternative fire truth.
    """
    require(
        type(distance_m) is int
        and distance_m in (500, 1000, 2000)
        and type(gap_hours) is int
        and gap_hours in (24, 48, 72),
        "Saved scenario",
    )
    frame = training_detections(source)
    if links is None:
        links = spatial_links(frame, distance_m)
    require(
        isinstance(links, SpatialLinks)
        and links.distance_m == distance_m
        and links.fingerprint == spatial_fingerprint(frame)
        and len(links.neighbours) == len(frame),
        "Exact spatial link provenance",
    )
    scenario = f"d{distance_m}m_t{gap_hours}h"
    times = frame.timestamp.astype("int64").to_numpy()
    incoming = [[] for _ in range(len(frame))]
    for i, neighbours in enumerate(links.neighbours):
        for j in neighbours[times[neighbours] - times[i] <= gap_hours * 3_600_000_000_000]:
            incoming[int(j)].append(i)
    parent = np.arange(len(frame))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return int(i)

    def union(i, j):
        a, b = sorted([find(i), find(j)])
        parent[b] = a

    active = {}
    births, transitions, states, detections = [], [], [], []
    for _, batch in frame.groupby("timestamp", sort=True):
        indices = batch.index.tolist()
        low = indices[0]
        predecessor_pairs = []
        edges = []
        for j in indices:
            for i in incoming[j]:
                if i < low:
                    predecessor_pairs.append((j, find(i)))
                edges.append((i, j))
        # Snapshot every predecessor before any same-time edge updates a root.
        previous = {root: active[root] for _, root in predecessor_pairs}
        for i, j in edges:
            union(i, j)
        groups, predecessors = defaultdict(list), defaultdict(set)
        for j in indices:
            groups[find(j)].append(j)
        for j, root in predecessor_pairs:
            predecessors[find(j)].add(root)
        for root in previous:
            del active[root]
        for root, current in sorted(groups.items()):
            prior = sorted(predecessors[root])
            ids = sorted(frame.loc[current, "detection_id"])
            now = batch.timestamp.iloc[0].isoformat()
            if not prior:
                birth_id = identity("birth", scenario, ids)
                ancestors = frozenset([birth_id])
                births.append(
                    {
                        "birth_candidate_id": birth_id,
                        "scenario": scenario,
                        "first_detection_utc": now,
                        "earliest_grid_ids_json": json.dumps(
                            sorted(frame.loc[current, "grid_id"].unique())
                        ),
                        "birth_detection_ids_json": json.dumps(ids),
                        "target": None,
                    }
                )
            else:
                ancestors = frozenset().union(*(previous[p][1] for p in prior))
                require(
                    len(ancestors) == sum(len(previous[p][1]) for p in prior),
                    "Disjoint predecessor ancestry",
                )
            state_id = identity("state", scenario, ancestors)
            transition = "birth" if not prior else "continuation" if len(prior) == 1 else "merge"
            if transition != "continuation":
                states.append(
                    {
                        "ancestry_state_id": state_id,
                        "recorded_at_utc": now,
                        "parent_state_ids_json": json.dumps(sorted(previous[p][0] for p in prior)),
                        "birth_candidate_id": birth_id if not prior else None,
                        "origin_candidate_count": len(ancestors),
                    }
                )
            active[root] = (state_id, ancestors)
            transitions.append(
                {
                    "scenario": scenario,
                    "recorded_at_utc": now,
                    "transition": transition,
                    "ancestry_state_id": state_id,
                    "predecessor_component_count": len(prior),
                    "incoming_detection_ids_json": json.dumps(ids),
                    "origin_candidate_count": len(ancestors),
                    "target": None,
                }
            )
            for j in current:
                point = frame.loc[j]
                detections.append(
                    {
                        "detection_id": point.detection_id,
                        "grid_id": point.grid_id,
                        "timestamp_utc": now,
                        "scenario": scenario,
                        "ancestry_state_id_at_ingestion": state_id,
                        "origin_candidate_count_at_ingestion": len(ancestors),
                        "transition_at_ingestion": transition,
                        "event_membership_complete": False,
                        "target": None,
                    }
                )
    groups = defaultdict(list)
    for i in range(len(frame)):
        groups[find(i)].append(i)
    membership = {}
    for root, indices in groups.items():
        keys = sorted(frame.loc[indices, "detection_id"])
        fingerprint = hashlib.sha256("\n".join(keys).encode()).hexdigest()
        membership.update({key: fingerprint for key in keys})
        require(root in active, "Final ancestry state exists")
    detections = pd.DataFrame(detections).sort_values("detection_id").reset_index(drop=True)
    detections["final_graph_membership_sha256"] = detections.detection_id.map(membership)
    births, transitions, states = (
        pd.DataFrame(births),
        pd.DataFrame(transitions),
        pd.DataFrame(states),
    )
    require(
        births.birth_candidate_id.is_unique and states.ancestry_state_id.is_unique,
        "Unique immutable births and ancestry states",
    )
    require(
        set(detections.detection_id) == set(frame.detection_id)
        and detections.detection_id.is_unique,
        "Each detection assigned exactly once",
    )
    reduction = int((transitions.predecessor_component_count - 1).clip(lower=0).sum())
    require(len(births) - reduction == len(groups), "Birth/merge component conservation")
    return (
        births,
        transitions,
        states,
        detections,
        {
            "source_detections": len(frame),
            "edge_count": sum(map(len, incoming)),
            "birth_candidates": len(births),
            "final_graph_components": len(groups),
            "merge_component_reduction": reduction,
            "physical_events_accepted": 0,
            "positive_label_permitted": False,
            "negative_label_permitted": False,
            "daily_observation_status": "unknown",
            "model_ready": False,
        },
    )
