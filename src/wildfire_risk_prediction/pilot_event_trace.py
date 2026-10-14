"""Source and graph witnesses for pilot disagreements; never physical event labels."""

import hashlib
import json
import re
from collections import deque

import numpy as np
import pandas as pd

from wildfire_risk_prediction.event_case_trace import STATIC, shortest
from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require, utc_times
from wildfire_risk_prediction.label_protocol_review import SCENARIOS
from wildfire_risk_prediction.target_admission import assert_targets_unassigned, review_catalog


def temporal_graph(frame, radius, gap_hours):
    """Exact undirected WGS84 edges; bound candidates by time before distance work.

    Frame must be timestamp/id sorted. A local edge gap does not cap component duration.
    """
    require(radius in (500, 1000, 2000) and gap_hours in (24, 48, 72), "Registered graph")
    times = frame.timestamp.astype("int64").to_numpy()
    require(np.all(times[1:] >= times[:-1]), "Sorted graph times")
    keys = frame.detection_id.to_numpy()
    lon, lat = frame.longitude.to_numpy(float), frame.latitude.to_numpy(float)
    adjacency = {key: set() for key in keys}
    for i in range(len(frame)):
        end = np.searchsorted(times, times[i] + gap_hours * 3600 * 10**9, side="right")
        candidates = np.arange(i + 1, end)
        if not len(candidates):
            continue
        _, _, distances = GEOD.inv(
            np.full(len(candidates), lon[i]),
            np.full(len(candidates), lat[i]),
            lon[candidates],
            lat[candidates],
        )
        for j in candidates[np.asarray(distances) <= radius]:
            adjacency[keys[i]].add(keys[j])
            adjacency[keys[j]].add(keys[i])
    visited, pending = {keys[0]}, deque([keys[0]])
    while pending:
        for other in adjacency[pending.popleft()]:
            if other not in visited:
                visited.add(other)
                pending.append(other)
    require(len(visited) == len(keys), "Disconnected saved component")
    return adjacency


def trace_sensitive_units(units, matches, catalogs, assignments, source, deferred_days):
    """Trace every in-window anchor across all scenarios, including lost first matches.

    Source is the frozen training candidate/proximity table, not the holdout source.
    Components are read from previously verified assignments, not chosen anew.
    """
    assert_targets_unassigned(units)
    require(units.review_unit_id.is_unique, "Unique pilot units")
    require(not units.duplicated(["grid_id", "prediction_timestamp_utc"]).any(), "Pilot keys")
    prediction = utc_times(units.prediction_timestamp_utc)
    require(
        prediction.dt.year.between(2018, 2023).all()
        and prediction.eq(prediction.dt.floor("D")).all(),
        "Training daily pilot",
    )
    require(set(catalogs) == set(assignments) == set(SCENARIOS), "All nine scenarios")
    selected_matches = matches.loc[matches.review_unit_id.isin(units.review_unit_id)].copy()
    require(
        len(selected_matches) == len(units) * len(SCENARIOS)
        and not selected_matches.duplicated(["review_unit_id", "scenario"]).any()
        and set(selected_matches.scenario) == set(SCENARIOS),
        "Exact pilot scenario matrix",
    )
    points = training_detections(source)
    source_index = source.set_index("detection_id")
    context = source_index.loc[points.detection_id, STATIC]
    counts = context[STATIC[1:]].to_numpy(float)
    distance = context[STATIC[0]].dropna().to_numpy(float)
    require(
        np.isfinite(counts).all()
        and (counts >= 0).all()
        and (counts == np.floor(counts)).all()
        and np.isfinite(distance).all()
        and (distance >= 0).all()
        and (distance <= 1000).all(),
        "Valid retrospective source context",
    )
    deferred = [pd.Timestamp(day, tz="UTC") for day in deferred_days]
    require(all(2018 <= t.year <= 2023 for t in deferred), "Training source exceptions")
    by_id = points.set_index("detection_id", drop=False)
    unit_anchors = {}
    for row in units.sort_values("review_unit_id").itertuples():
        t = pd.Timestamp(row.prediction_timestamp_utc)
        anchors = points.loc[
            points.grid_id.eq(row.grid_id)
            & points.timestamp.gt(t)
            & points.timestamp.le(t + pd.Timedelta(24, unit="h")),
            "detection_id",
        ].tolist()
        require(bool(anchors), "Disagreement must have an in-window source anchor")
        unit_anchors[row.review_unit_id] = anchors

    contexts, variants, member_tables, paths = [], [], [], []
    match_index = selected_matches.set_index(["review_unit_id", "scenario"])
    for scenario in SCENARIOS:
        radius, gap = map(int, re.fullmatch(r"d(\d+)m_t(\d+)h", scenario).groups())
        saved = assignments[scenario]
        require(
            saved.detection_id.is_unique and set(saved.detection_id) == set(points.detection_id),
            "Assignment source coverage",
        )
        saved = saved.set_index("detection_id").loc[points.detection_id]
        require(saved.cluster_id.notna().all(), "Missing assigned cluster")
        for col in ("grid_id", "source_sensor"):
            require(saved[col].tolist() == points[col].tolist(), "Assignment source attributes")
        require(
            pd.to_datetime(saved.timestamp, utc=True, format="ISO8601").tolist()
            == points.timestamp.tolist(),
            "Assignment source timestamps",
        )
        catalog = catalogs[scenario]
        review_catalog(catalog)
        require(set(saved.cluster_id) == set(catalog.cluster_id), "Catalog assignment coverage")
        cat_index = catalog.set_index("cluster_id", drop=False)
        groups = saved.reset_index().groupby("cluster_id", sort=True).detection_id.agg(list)
        chosen = sorted(
            {saved.loc[key, "cluster_id"] for keys in unit_anchors.values() for key in keys}
        )
        cache = {}
        for cluster in chosen:
            row = cat_index.loc[cluster]
            require(cluster.startswith(scenario + "_"), "Scenario cluster identity")
            frame = points.loc[points.detection_id.isin(groups[cluster])].reset_index(drop=True)
            earliest = frame.loc[frame.timestamp.eq(frame.timestamp.min())]
            require(
                len(frame) == row.detection_count
                and frame.timestamp.min() == pd.Timestamp(row.first_detection_utc)
                and frame.timestamp.max() == pd.Timestamp(row.last_detection_utc)
                and hashlib.sha256("\n".join(sorted(frame.detection_id)).encode()).hexdigest()
                == row.membership_sha256
                and len(earliest) == row.earliest_detection_count
                and earliest.grid_id.nunique() == row.earliest_grid_count
                and sorted(earliest.grid_id.unique()) == json.loads(row.earliest_grid_ids_json)
                and earliest.iloc[0].detection_id == row.canonical_first_detection_id,
                "Saved membership and all first ties",
            )
            adjacency = temporal_graph(frame, radius, gap)
            cache[cluster] = (frame, earliest, adjacency)
            low = (frame.timestamp.min() - pd.Timedelta(gap, unit="h")).floor("D")
            high = (frame.timestamp.max() + pd.Timedelta(gap, unit="h")).floor("D")
            relevant = [t.strftime("%Y-%m-%d") for t in deferred if low <= t <= high]
            variants.append(
                {
                    "scenario": scenario,
                    **row.to_dict(),
                    "edge_radius_m": radius,
                    "edge_gap_hours": gap,
                    "verified_internal_graph_edges": sum(map(len, adjacency.values())) // 2,
                    "members_with_prior_type2_within_1000m": int(
                        source_index.loc[frame.detection_id, "static_prior_records_1000m"]
                        .gt(0)
                        .sum()
                    ),
                    "deferred_days_in_calendar_context_json": json.dumps(relevant),
                    "context_extends_outside_training": low.year < 2018 or high.year > 2023,
                    "assessment_status": "automated_trace_not_adjudicated",
                    "target": None,
                }
            )
            raw_cols = [
                c
                for c in (
                    *STATIC,
                    "source_record_number",
                    "acq_date",
                    "acq_time",
                    "version",
                    "frp",
                )
                if c in source_index
            ]
            members = frame.drop(columns="timestamp").join(
                source_index[raw_cols], on="detection_id", validate="one_to_one"
            )
            members["scenario"], members["cluster_id"] = scenario, cluster
            members["context_is_retrospective_not_predictor"] = True
            members["target"] = None
            member_tables.append(members)

        for unit in units.sort_values("review_unit_id").itertuples():
            t = pd.Timestamp(unit.prediction_timestamp_utc)
            anchors = unit_anchors[unit.review_unit_id]
            clusters = sorted(set(saved.loc[anchors, "cluster_id"]))
            expected_match_ids = []
            for cluster in clusters:
                frame, earliest, adjacency = cache[cluster]
                row = cat_index.loc[cluster]
                in_time = t < frame.timestamp.min() <= t + pd.Timedelta(24, unit="h")
                in_cell = unit.grid_id in set(earliest.grid_id)
                matched = bool(in_time and in_cell)
                if matched:
                    expected_match_ids.append(cluster)
                reason = (
                    "first_time_and_cell_match"
                    if matched
                    else "earlier_first_window_and_other_first_cell"
                    if not in_time and not in_cell
                    else "earlier_first_window"
                    if not in_time
                    else "other_first_cell"
                )
                local_anchors = [key for key in anchors if saved.loc[key, "cluster_id"] == cluster]
                contexts.append(
                    {
                        "review_unit_id": unit.review_unit_id,
                        "grid_id": unit.grid_id,
                        "prediction_timestamp_utc": t.isoformat(),
                        "scenario": scenario,
                        "cluster_id": cluster,
                        "membership_sha256": row.membership_sha256,
                        "member_count": len(frame),
                        "anchor_count": len(local_anchors),
                        "anchor_detection_ids_json": json.dumps(sorted(local_anchors)),
                        "first_detection_utc": row.first_detection_utc,
                        "first_detection_ids_json": json.dumps(sorted(earliest.detection_id)),
                        "earliest_grid_ids_json": row.earliest_grid_ids_json,
                        "first_time_in_target_window": bool(in_time),
                        "pilot_grid_in_first_cells": bool(in_cell),
                        "catalog_first_candidate_match": matched,
                        "first_match_explanation": reason,
                        "target": None,
                    }
                )
                for first in sorted(earliest.detection_id):
                    for anchor in sorted(local_anchors):
                        chain = shortest(adjacency, first, anchor)
                        for step, key in enumerate(chain):
                            point = by_id.loc[key]
                            dist, delta = None, None
                            if step:
                                previous = by_id.loc[chain[step - 1]]
                                _, _, dist = GEOD.inv(
                                    previous.longitude,
                                    previous.latitude,
                                    point.longitude,
                                    point.latitude,
                                )
                                delta = (
                                    point.timestamp - previous.timestamp
                                ).total_seconds() / 3600
                                require(dist <= radius and abs(delta) <= gap, "Path edge witness")
                            paths.append(
                                {
                                    "review_unit_id": unit.review_unit_id,
                                    "scenario": scenario,
                                    "cluster_id": cluster,
                                    "first_detection_id": first,
                                    "anchor_detection_id": anchor,
                                    "path_step": step,
                                    "detection_id": key,
                                    "timestamp_utc": point.timestamp.isoformat(),
                                    "grid_id": point.grid_id,
                                    "edge_distance_m": dist,
                                    "edge_signed_gap_hours": delta,
                                    "path_is_spread_direction": False,
                                    "target": None,
                                }
                            )
            old = match_index.loc[(unit.review_unit_id, scenario)]
            require(
                old.grid_id == unit.grid_id
                and pd.Timestamp(old.prediction_timestamp_utc) == t
                and sorted(json.loads(old.matched_cluster_ids_json)) == expected_match_ids
                and old.candidate_cluster_first_cell_matches == len(expected_match_ids)
                and sorted(json.loads(old.matched_membership_set_json))
                == sorted({cat_index.loc[c, "membership_sha256"] for c in expected_match_ids}),
                "Reproduced original first-candidate matches",
            )

    contexts = pd.DataFrame(contexts)
    variants = pd.DataFrame(variants)
    summaries = []
    for unit in units.sort_values("review_unit_id").itertuples():
        rows = contexts.loc[contexts.review_unit_id.eq(unit.review_unit_id)]
        pairs = rows.groupby("scenario", sort=True)
        summaries.append(
            {
                "review_unit_id": unit.review_unit_id,
                "grid_id": unit.grid_id,
                "prediction_timestamp_utc": unit.prediction_timestamp_utc,
                "anchor_detection_count": len(unit_anchors[unit.review_unit_id]),
                "scenarios_with_first_candidate_match": rows.loc[
                    rows.catalog_first_candidate_match, "scenario"
                ].nunique(),
                "first_time_signatures": len(
                    {tuple(sorted(g.first_detection_utc)) for _, g in pairs}
                ),
                "first_cell_signatures": len(
                    {tuple(sorted(g.earliest_grid_ids_json)) for _, g in pairs}
                ),
                "anchored_membership_signatures": len(
                    {tuple(sorted(g.membership_sha256)) for _, g in pairs}
                ),
                "largest_anchored_cluster": int(rows.member_count.max()),
                "first_match_explanations_json": json.dumps(
                    sorted(set(rows.first_match_explanation))
                ),
                "assessment_status": "automated_trace_not_adjudicated",
                "target": None,
            }
        )
    return (
        pd.DataFrame(summaries),
        contexts,
        variants,
        pd.concat(member_tables, ignore_index=True),
        pd.DataFrame(paths),
    )
