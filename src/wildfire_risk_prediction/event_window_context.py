"""Rebuild a saved component's window-prefix graph for diagnostics, never event labels."""

import hashlib
import json

import numpy as np
import pandas as pd

from wildfire_risk_prediction.event_review import spatial_links, training_detections
from wildfire_risk_prediction.feature_join import require


def prefix_first_sets(source, anchors, *, end_utc, distance_m, gap_hours):
    """Find all earliest cells of anchor-containing components at a fixed cutoff.

    This is an induced subgraph of a previously saved exploratory component.
    It is not FEDS, a sequential birth/merge tracker, or a proposed label rule.
    """
    require(distance_m in (500, 1000, 2000) and gap_hours in (24, 48, 72), "Saved scenario")
    end = pd.Timestamp(end_utc)
    require(
        not pd.isna(end) and end.tzinfo is not None and end.utcoffset().total_seconds() == 0,
        "Explicit UTC cutoff",
    )
    full = training_detections(source)
    require(
        isinstance(anchors, (list, tuple))
        and len(anchors) > 0
        and len(anchors) == len(set(anchors))
        and set(anchors) <= set(full.detection_id),
        "Distinct saved anchors",
    )
    frame = full.loc[full.timestamp.le(end)].reset_index(drop=True)
    require(set(anchors) <= set(frame.detection_id), "Anchor cannot follow cutoff")
    links = spatial_links(frame, distance_m)
    times = frame.timestamp.astype("int64").to_numpy()
    parent = np.arange(len(frame))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return int(i)

    for i, neighbours in enumerate(links.neighbours):
        for j in neighbours[times[neighbours] - times[i] <= gap_hours * 3_600_000_000_000]:
            a, b = find(i), find(int(j))
            parent[b] = a
    roots = pd.Series([find(i) for i in range(len(frame))], index=frame.index)
    selected = set(roots.loc[frame.detection_id.isin(anchors)])
    rows = []
    for root in sorted(selected):
        group = frame.loc[roots.eq(root)]
        first = group.loc[group.timestamp.eq(group.timestamp.min())]
        rows.append(
            {
                "prefix_membership_sha256": hashlib.sha256(
                    "\n".join(sorted(group.detection_id)).encode()
                ).hexdigest(),
                "anchor_ids_json": json.dumps(sorted(set(group.detection_id) & set(anchors))),
                "first_detection_utc": first.timestamp.iloc[0].isoformat(),
                "earliest_grid_ids_json": json.dumps(sorted(first.grid_id.unique())),
                "member_count": len(group),
                "target": None,
            }
        )
    return pd.DataFrame(rows).sort_values("prefix_membership_sha256").reset_index(drop=True)
