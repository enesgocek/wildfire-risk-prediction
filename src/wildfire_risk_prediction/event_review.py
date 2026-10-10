"""Training-only readback of exploratory clusters; no confirmed events or labels."""

import hashlib
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pyproj import Geod
from shapely.geometry import Point, box
from shapely.strtree import STRtree

VERSION = "event_grouping_review_v1"
GEOD = Geod(ellps="WGS84")


@dataclass(frozen=True)
class SpatialLinks:
    distance_m: int
    fingerprint: str
    neighbours: tuple


def spatial_fingerprint(frame):
    columns = ["detection_id", "longitude", "latitude", "timestamp"]
    return hashlib.sha256(frame[columns].to_csv(index=False).encode()).hexdigest()


def training_detections(frame):
    """Reject holdout rows rather than silently filter inside scientific code."""
    required = [
        "detection_id",
        "grid_id",
        "source_sensor",
        "detection_timestamp_utc",
        "latitude",
        "longitude",
        "type",
        "confidence",
    ]
    if frame.empty or frame[required].isna().any().any():
        raise ValueError("Missing detection fields")
    if not frame.detection_id.is_unique:
        raise ValueError("Duplicate detection key")
    result = frame[required].copy()
    result["timestamp"] = pd.to_datetime(
        result.detection_timestamp_utc, utc=True, errors="raise", format="ISO8601"
    )
    if not result.timestamp.dt.year.between(2018, 2023).all():
        raise ValueError("Only training 2018–2023 allowed")
    if not result.source_sensor.isin(["SNPP", "N20"]).all():
        raise ValueError("Unexpected sensor")
    if not (result["type"].astype(str).eq("0") & result.confidence.isin(["n", "h"])).all():
        raise ValueError("Candidate selection changed")
    for column, low, high in (("longitude", 20, 40), ("latitude", 30, 45)):
        result[column] = pd.to_numeric(result[column], errors="raise")
        if not np.isfinite(result[column]).all() or not result[column].between(low, high).all():
            raise ValueError("Coordinates outside pilot search envelope")
    return result.sort_values(["timestamp", "detection_id"]).reset_index(drop=True)


def spatial_links(frame, distance_m):
    """Conservative pilot bounding box, followed by exact WGS84 distance."""
    if distance_m not in (500, 1000, 2000):
        raise ValueError("Unregistered exploratory distance")
    frame = training_detections(frame)
    lon = frame.longitude.to_numpy(float)
    lat = frame.latitude.to_numpy(float)
    tree = STRtree([Point(x, y) for x, y in zip(lon, lat, strict=True)])
    # 100 km/degree is conservative in this validated 30–45 latitude envelope.
    dy = distance_m / 100000
    dx = dy / np.cos(np.deg2rad(45 + dy))
    links = []
    for i in range(len(frame)):
        neighbours = tree.query(box(lon[i] - dx, lat[i] - dy, lon[i] + dx, lat[i] + dy))
        neighbours = neighbours[neighbours > i]
        if len(neighbours):
            _, _, distances = GEOD.inv(
                np.full(len(neighbours), lon[i]),
                np.full(len(neighbours), lat[i]),
                lon[neighbours],
                lat[neighbours],
            )
            neighbours = neighbours[np.asarray(distances) <= distance_m]
        neighbours.setflags(write=False)
        links.append(neighbours)
    return SpatialLinks(distance_m, spatial_fingerprint(frame), tuple(links))


def review_partition(frame, assignments, links, distance_m, gap_hours):
    """Rebuild components and prove partition equality without relying on cluster names."""
    if distance_m not in (500, 1000, 2000) or gap_hours not in (24, 48, 72):
        raise ValueError("Unregistered exploratory scenario")
    frame = training_detections(frame)
    if (
        not isinstance(links, SpatialLinks)
        or links.distance_m != distance_m
        or links.fingerprint != spatial_fingerprint(frame)
        or len(links.neighbours) != len(frame)
    ):
        raise ValueError("Spatial link coverage")
    if not assignments.detection_id.is_unique or set(assignments.detection_id) != set(
        frame.detection_id
    ):
        raise ValueError("Assignment key coverage")
    saved = assignments.set_index("detection_id").loc[frame.detection_id].reset_index()
    if saved.cluster_id.isna().any():
        raise ValueError("Missing cluster identity")
    for column in ("grid_id", "source_sensor"):
        if not saved[column].eq(frame[column]).all():
            raise ValueError("Assignment provenance mismatch")
    times = pd.to_datetime(saved.timestamp, utc=True, errors="raise", format="ISO8601")
    if not times.eq(frame.timestamp).all():
        raise ValueError("Assignment time mismatch")
    ns = frame.timestamp.astype("int64").to_numpy()
    parent = np.arange(len(frame))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    edges = 0
    for i, neighbours in enumerate(links.neighbours):
        selected = neighbours[ns[neighbours] - ns[i] <= gap_hours * 3600 * 10**9]
        edges += len(selected)
        for j in selected:
            first, second = find(i), find(int(j))
            if first != second:
                parent[second] = first
    roots = np.array([find(i) for i in range(len(frame))])
    comparison = pd.DataFrame({"rebuilt": roots, "saved": saved.cluster_id})
    if (
        comparison.groupby("rebuilt").saved.nunique().ne(1).any()
        or comparison.groupby("saved").rebuilt.nunique().ne(1).any()
    ):
        raise ValueError("Cluster partition differs from rebuilt graph")
    rows = []
    frame["cluster_id"] = saved.cluster_id.to_numpy()
    for cluster, group in frame.groupby("cluster_id", sort=True):
        first = group.iloc[0]
        earliest = group.loc[group.timestamp.eq(first.timestamp)]
        _, _, dist = GEOD.inv(
            np.full(len(group), first.longitude),
            np.full(len(group), first.latitude),
            group.longitude.to_numpy(),
            group.latitude.to_numpy(),
        )
        duration = (group.timestamp.max().value - first.timestamp.value) / (3600 * 10**9)
        # The registered target is (T,T+24h], including exact midnight at its right edge.
        day_ns = 24 * 3600 * 10**9
        prediction = pd.Timestamp(
            ((first.timestamp.value - 1) // day_ns) * day_ns, unit="ns", tz="UTC"
        )
        member_hash = hashlib.sha256("\n".join(sorted(group.detection_id)).encode()).hexdigest()
        rows.append(
            {
                "cluster_id": cluster,
                "membership_sha256": member_hash,
                "detection_count": len(group),
                "first_detection_utc": first.timestamp.isoformat(),
                "last_detection_utc": group.timestamp.max().isoformat(),
                "canonical_first_detection_id": first.detection_id,
                "canonical_first_grid_id": first.grid_id,
                "earliest_detection_count": len(earliest),
                "earliest_grid_count": earliest.grid_id.nunique(),
                "earliest_grid_ids_json": json_list(earliest.grid_id),
                "grid_count": group.grid_id.nunique(),
                "sensor_count": group.source_sensor.nunique(),
                "duration_hours": duration,
                "max_distance_from_canonical_first_m": float(np.max(dist)),
                "temporal_chain_review": duration > gap_hours,
                "spatial_chain_review": float(np.max(dist)) > distance_m + 1e-6,
                "multi_grid_first_detection_review": earliest.grid_id.nunique() > 1,
                "candidate_prediction_timestamp_utc": prediction.isoformat(),
                "calendar_year_crossing_review": first.timestamp.year != group.timestamp.max().year,
                "period_start_context_missing": first.timestamp.value
                <= pd.Timestamp("2018-01-01", tz="UTC").value + gap_hours * 3600 * 10**9,
                "period_end_context_missing": group.timestamp.max().value
                >= pd.Timestamp("2024-01-01", tz="UTC").value - gap_hours * 3600 * 10**9,
                "event_status": "exploratory_cluster_only",
                "negative_label_permitted": False,
            }
        )
    catalog = pd.DataFrame(rows)
    summary = {
        "scenario": f"d{distance_m}m_t{gap_hours}h",
        "detection_count": len(frame),
        "cluster_count": len(catalog),
        "pair_connection_count": edges,
        "temporal_chain_review_clusters": int(catalog.temporal_chain_review.sum()),
        "spatial_chain_review_clusters": int(catalog.spatial_chain_review.sum()),
        "multi_grid_first_detection_clusters": int(catalog.multi_grid_first_detection_review.sum()),
        "calendar_year_crossing_clusters": int(catalog.calendar_year_crossing_review.sum()),
        "period_context_missing_clusters": int(
            (catalog.period_start_context_missing | catalog.period_end_context_missing).sum()
        ),
        "longest_cluster_hours": float(catalog.duration_hours.max()),
        "largest_cluster_detections": int(catalog.detection_count.max()),
        "maximum_first_detection_distance_m": float(
            catalog.max_distance_from_canonical_first_m.max()
        ),
        "rows_removed": 0,
        "partition_readback_passed": True,
    }
    return catalog, summary


def json_list(values):
    return json.dumps(sorted(set(values)), ensure_ascii=False)
