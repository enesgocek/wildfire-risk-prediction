"""Compare Salur-local detections with frozen full and time-limited graph components."""

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
from audit_salur_start_marker import BASE, CATALOG, ROOT
from audit_stage_one_selection import verify

from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.event_window_context import prefix_first_sets
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

MARKER = BASE / "salur_marker_v1/20261108T194701Z_a7895f19/readback.json"
GRAPH = ROOT / "outputs/reports/events/review_v1/20261010T001137Z_320433ed"
PINS = {
    MARKER: "fa15c440eb6a025aada777cab58544c23ba5083302ede626adb45a222da788d8",
    GRAPH / "review.json": "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e",
    CATALOG: "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5",
}


def distances(frame, lon_lat):
    lon, lat = lon_lat
    return np.asarray(
        GEOD.inv(
            np.full(len(frame), lon),
            np.full(len(frame), lat),
            frame.longitude.to_numpy(float),
            frame.latitude.to_numpy(float),
        )[2]
    )


def first_signature(frame, lon_lat):
    first = frame.loc[frame.timestamp.eq(frame.timestamp.min())]
    return {
        "first_detection_utc": first.timestamp.iloc[0].isoformat(),
        "first_ids": sorted(first.detection_id),
        "first_cells": sorted(first.grid_id.unique()),
        "first_distance_to_marker_min_m": float(distances(first, lon_lat).min()),
        "first_distance_to_marker_max_m": float(distances(first, lon_lat).max()),
    }


def main():
    pins = {p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()}
    for path, expected in PINS.items():
        verify(path, expected)
    marker = json.loads(MARKER.read_bytes())
    graph = json.loads((GRAPH / "review.json").read_bytes())
    require(not graph["labels_created"], "Exploratory graph only")
    with CATALOG.open(encoding="utf-8-sig", newline="") as stream:
        records = [r for r in csv.DictReader(stream) if "2018" <= r["acq_date"][:4] <= "2023"]
    source = training_detections(pd.DataFrame(records))
    require(len(source) == graph["training_detection_count"] == 30295, "Training scope")
    start = pd.Timestamp(marker["window_start_utc"])
    end = pd.Timestamp(marker["window_end_utc"])
    onset = pd.Timestamp(marker["reported_outbreak_utc"])
    day = source.loc[source.timestamp.gt(start) & source.timestamp.le(end)].copy()
    center = marker["estimates"]["sentinel_2b_pre_event"]
    lon_lat = center["marker_lon_lat"]
    selections = []
    for estimate in marker["estimates"].values():
        local = day.loc[distances(day, estimate["marker_lon_lat"]) <= 1000]
        selections.append(set(local.detection_id))
        require(
            len(local) == estimate["catalogue_context_by_radius_m"]["1000"]["at_or_after_rows"]
            and local.timestamp.ge(onset).all(),
            "Pinned local selection matches source-time comparison",
        )
    require(selections[0] == selections[1] and len(selections[0]) == 11, "Two marker solutions")
    local = day.loc[day.detection_id.isin(selections[0])].copy()
    local["distance_to_marker_m"] = distances(local, lon_lat)
    initial_time = local.timestamp.min()
    initial_ids = sorted(local.loc[local.timestamp.eq(initial_time), "detection_id"])
    require(local.grid_id.eq(center["center_cell"]).all(), "All local centers in marker cell")
    rows, prefix_rows, component_frames, components = [], [], [], {}
    for scenario, hashes in graph["artifact_sha256"].items():
        radius, gap = (
            int(v) for v in scenario.removeprefix("d").replace("m_t", " ").rstrip("h").split()
        )
        file = ROOT / f"data/interim/event_grouping/{scenario}_assignments.csv"
        verify(file, hashes["assignments_sha256"])
        pins[file.relative_to(ROOT).as_posix()] = hashes["assignments_sha256"]
        assignments = pd.read_csv(file)
        require(
            assignments.detection_id.is_unique
            and set(assignments.detection_id) == set(source.detection_id),
            "Frozen assignment key coverage",
        )
        indexed = assignments.set_index("detection_id").loc[source.detection_id]
        require(
            indexed.grid_id.to_numpy().tolist() == source.grid_id.tolist()
            and indexed.source_sensor.to_numpy().tolist() == source.source_sensor.tolist()
            and pd.to_datetime(indexed.timestamp, utc=True, format="ISO8601").tolist()
            == source.timestamp.tolist(),
            "Frozen assignment source identity",
        )
        cluster_ids = assignments.loc[
            assignments.detection_id.isin(local.detection_id), "cluster_id"
        ]
        require(cluster_ids.nunique() == 1, "Selected local detections in one full component")
        cluster_id = cluster_ids.iloc[0]
        ids = set(assignments.loc[assignments.cluster_id.eq(cluster_id), "detection_id"])
        component = source.loc[source.detection_id.isin(ids)].copy()
        components[scenario] = component
        summary = first_signature(component, lon_lat)
        component_frames.append(
            component.assign(scenario=scenario, cluster_id=cluster_id, target=None)
        )
        review_file = GRAPH / f"{scenario}_review.csv"
        verify(review_file, hashes["review_sha256"])
        pins[review_file.relative_to(ROOT).as_posix()] = hashes["review_sha256"]
        saved = pd.read_csv(review_file).set_index("cluster_id").loc[cluster_id]
        require(
            len(component) == saved.detection_count
            and pd.Timestamp(saved.first_detection_utc)
            == pd.Timestamp(summary["first_detection_utc"])
            and sorted(json.loads(saved.earliest_grid_ids_json)) == summary["first_cells"]
            and hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()
            == saved.membership_sha256,
            "Independent full-component catalog readback",
        )
        result = {
            "scenario": scenario,
            "cluster_id": cluster_id,
            "member_count": len(component),
            "last_detection_utc": component.timestamp.max().isoformat(),
            **summary,
            "marker_cell_in_full_first_set": center["center_cell"] in summary["first_cells"],
        }
        for label, cutoff, anchors in (
            ("at_first_local_detection", initial_time, initial_ids),
            ("at_target_end", end, sorted(local.detection_id)),
        ):
            prefixes = prefix_first_sets(
                component, anchors, end_utc=cutoff, distance_m=radius, gap_hours=gap
            )
            require(prefixes.target.isna().all(), "Prefix is unlabeled")
            result[label] = prefixes.to_dict("records")
            for record in prefixes.to_dict("records"):
                prefix_rows.append({"scenario": scenario, "cutoff_kind": label, **record})
        rows.append(result)

    # Isolate the one additional historical node admitted by the 72 h scenario.
    wide = components["d2000m_t72h"]
    extra = wide.loc[~wide.detection_id.isin(components["d2000m_t48h"].detection_id)]
    require(len(extra) == 1, "Single additional node in the widest Salur component")
    historical = extra.iloc[0]
    edges = wide.loc[wide.detection_id.ne(historical.detection_id)].copy()
    edges["edge_distance_m"] = distances(edges, (historical.longitude, historical.latitude))
    edges["edge_gap_ns"] = edges.timestamp.astype("int64") - historical.timestamp.value
    edges = edges.loc[
        edges.edge_distance_m.le(2000)
        & edges.edge_gap_ns.ge(0)
        & edges.edge_gap_ns.le(72 * 3_600_000_000_000)
    ].sort_values(["timestamp", "detection_id"])
    require(not edges.empty, "At least one qualifying edge for the historical node")
    first_edge_time = edges.timestamp.iloc[0]
    before = pd.Timestamp(first_edge_time.value - 1, unit="ns", tz="UTC")
    witness_prefixes = {}
    for name, cutoff in (("before_first_edge", before), ("at_first_edge", first_edge_time)):
        prefixes = prefix_first_sets(
            wide, initial_ids, end_utc=cutoff, distance_m=2000, gap_hours=72
        )
        witness_prefixes[name] = prefixes.to_dict("records")
        for record in prefixes.to_dict("records"):
            prefix_rows.append({"scenario": "d2000m_t72h", "cutoff_kind": name, **record})
    require(
        first_edge_time > end
        and all(
            p["first_detection_utc"] == initial_time.isoformat()
            and center["center_cell"] in json.loads(p["earliest_grid_ids_json"])
            for p in witness_prefixes["before_first_edge"]
        )
        and all(
            p["first_detection_utc"] == historical.timestamp.isoformat()
            and center["center_cell"] not in json.loads(p["earliest_grid_ids_json"])
            for p in witness_prefixes["at_first_edge"]
        ),
        "Exact time-limited graph switch at the first qualifying edge",
    )
    witness = {
        "historical_detection_id": historical.detection_id,
        "historical_detection_utc": historical.timestamp.isoformat(),
        "historical_grid_id": historical.grid_id,
        "historical_distance_to_marker_m": float(distances(extra, lon_lat)[0]),
        "first_edge_detection_ids": sorted(
            edges.loc[edges.timestamp.eq(first_edge_time), "detection_id"]
        ),
        "first_edge_utc": first_edge_time.isoformat(),
        "first_edge_gap_hours": float(edges.edge_gap_ns.iloc[0] / 3_600_000_000_000),
        "first_edge_distance_m": float(edges.edge_distance_m.iloc[0]),
        "first_edge_minimum_time_margin_above_48h_hours": float(
            edges.edge_gap_ns.iloc[0] / 3_600_000_000_000 - 48
        ),
        "prefixes": witness_prefixes,
        "physical_fire_identity_inferred": False,
    }
    gate = specification()
    require(not gate["positive_label_permitted"] and not gate["negative_label_permitted"], "Gate")
    run = (
        ROOT
        / "outputs/reports/dataset/salur_event_context_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    run.mkdir(parents=True, exist_ok=False)
    tables = {
        "local_detections.csv": local.assign(target=None),
        "prefix_components.csv": pd.DataFrame(prefix_rows),
        "component_members.csv": pd.concat(component_frames, ignore_index=True),
        "historical_node_edges.csv": edges.assign(target=None),
    }
    artifacts = {}
    for name, frame in tables.items():
        file = run / name
        frame.to_csv(file, index=False)
        require(pd.read_csv(file).target.isna().all(), "No output targets")
        artifacts[name] = hashlib.sha256(file.read_bytes()).hexdigest()
    report = {
        "scope": "single_case_reported_marker_graph_diagnostic_only",
        "created_utc": datetime.now(UTC).isoformat(),
        "input_sha256": pins,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "artifact_sha256": artifacts,
        "marker_cell": center["center_cell"],
        "local_search_radius_m": 1000,
        "radius_is_ignition_error_bound": False,
        "local_detection_count": len(local),
        "first_local_detection_utc": initial_time.isoformat(),
        "first_local_ids": initial_ids,
        "reported_onset_utc": onset.isoformat(),
        "target_end_utc": end.isoformat(),
        "scenarios": rows,
        "future_edge_witness": witness,
        "target_admission": gate,
        "model_trained": False,
        "method_accepted": False,
        "final_merge_approval": False,
    }
    file = run / "readback.json"
    file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    require(json.loads(file.read_bytes()) == report, "Report readback")
    print(run.relative_to(ROOT))
    for row in rows:
        print(
            row["scenario"],
            row["member_count"],
            row["first_detection_utc"],
            "full",
            row["marker_cell_in_full_first_set"],
            "initial",
            [
                (p["member_count"], p["earliest_grid_ids_json"])
                for p in row["at_first_local_detection"]
            ],
            "end",
            [
                (p["member_count"], p["first_detection_utc"], p["earliest_grid_ids_json"])
                for p in row["at_target_end"]
            ],
        )
    print("SHA256", hashlib.sha256(file.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
