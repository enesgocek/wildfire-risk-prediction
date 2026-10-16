"""Measure post-window graph context with exact witnesses and bounded prefix rebuilds."""

import hashlib
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.event_window_context import prefix_first_sets
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
TRACE = "outputs/reports/dataset/sensitive_trace_v1/20261014T194620Z_284f08c1"
DECISION = "outputs/reports/dataset/event_cell_decision_v1/20261016T153227Z_54400785"
PATH_KEYS = [
    "review_unit_id",
    "scenario",
    "cluster_id",
    "first_detection_id",
    "anchor_detection_id",
]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline window-context audit")


def run():
    socket.create_connection = deny
    socket.socket.connect = deny
    pins = {}

    def bind(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular context evidence")
        value = sha(path)
        require(expected is None or expected == value, "Pinned context evidence")
        pins[name] = value
        return path

    old = json.loads(
        bind(
            TRACE + "/readback.json",
            "f613115b0d67caea55353b102e2c420d1879666dfc8f94ea52416b0e9954fa11",
        ).read_text()
    )
    bind(
        TRACE + "/completion_readback.json",
        "000ed76785212fc4a2b32cc4bdb806aabddba7c22b7ddee0caab85a3ad40dac1",
    )
    files = {name: bind(TRACE + "/" + name, h) for name, h in old["artifact_sha256"].items()}
    decision = json.loads(
        bind(
            DECISION + "/readback.json",
            "84ed43250e05a8023bbcc51ecf57978e9b3709de35070698a98eefa3ce1e6abf",
        ).read_text()
    )
    bind(
        DECISION + "/completion_readback.json",
        "1a8ba2ce82b55f2a911bf6d87e8b6bb9fc83e8727c4b1f897887c603889edcfd",
    )
    policy = json.loads(
        bind(
            "configs/first_cell_candidates_v1.json",
            "34e1bdc4d41dd58bbb504c3ec8ff7b0884454c182cc511207c25c437d180cb32",
        ).read_text()
    )
    require(
        decision["selected_first_cell_policy"] == policy["version"]
        and policy["method"] == "all_recorded_earliest_cells"
        and not decision["labels_created"],
        "Selected candidate direction only",
    )
    for name in (
        "src/wildfire_risk_prediction/event_window_context.py",
        "src/wildfire_risk_prediction/event_review.py",
        "src/wildfire_risk_prediction/feature_join.py",
        "tests/test_event_window_context.py",
        "scripts/quality/audit_event_window_context.py",
        "docs/research/event_grouping_sources_2026-10-16.json",
    ):
        bind(name)
    contexts = pd.read_csv(files["unit_scenario_components.csv"], float_precision="round_trip")
    catalog = pd.read_csv(files["component_graph_review.csv"], float_precision="round_trip")
    members = pd.read_csv(files["component_source_members.csv"], float_precision="round_trip")
    paths = pd.read_csv(files["first_to_pilot_anchor_paths.csv"], float_precision="round_trip")
    require(
        len(contexts) == len(catalog) == 181 and contexts.review_unit_id.nunique() == 19,
        "Frozen nineteen-case scope",
    )
    require(all(f.target.isna().all() for f in (contexts, catalog, members, paths)), "No labels")
    require(
        catalog.cluster_id.is_unique
        and set(members.cluster_id) == set(catalog.cluster_id)
        and not members.duplicated(["cluster_id", "detection_id"]).any(),
        "Member identity",
    )
    raw_cols = [
        "grid_id",
        "source_sensor",
        "detection_timestamp_utc",
        "latitude",
        "longitude",
        "type",
        "confidence",
    ]
    require(
        members.groupby("detection_id")[raw_cols].nunique().eq(1).all().all(),
        "Source identity consistent across scenarios",
    )
    training_detections(members.drop_duplicates("detection_id"))
    require(
        not contexts.duplicated(["review_unit_id", "scenario", "cluster_id"]).any(), "Context keys"
    )
    require(not paths.duplicated(PATH_KEYS + ["path_step"]).any(), "Path step keys")
    joined = paths.merge(
        members[["cluster_id", "detection_id", *raw_cols]],
        on=["cluster_id", "detection_id"],
        how="left",
        validate="many_to_one",
        suffixes=("", "_source"),
    )
    require(
        joined.latitude.notna().all() and joined.grid_id.eq(joined.grid_id_source).all(),
        "Witness source keys",
    )
    source_time = pd.to_datetime(joined.detection_timestamp_utc, utc=True, format="ISO8601")
    require(
        source_time.eq(pd.to_datetime(joined.timestamp_utc, utc=True)).all(), "Witness source times"
    )
    ordered = joined.sort_values(PATH_KEYS + ["path_step"]).reset_index(drop=True)
    grouped = ordered.groupby(PATH_KEYS, sort=False)
    previous = grouped[["longitude", "latitude", "timestamp_utc"]].shift()
    has_edge = ordered.path_step.gt(0)
    distances = GEOD.inv(
        previous.loc[has_edge, "longitude"].to_numpy(),
        previous.loc[has_edge, "latitude"].to_numpy(),
        ordered.loc[has_edge, "longitude"].to_numpy(),
        ordered.loc[has_edge, "latitude"].to_numpy(),
    )[2]
    dt = (
        pd.to_datetime(ordered.loc[has_edge, "timestamp_utc"], utc=True)
        - pd.to_datetime(previous.loc[has_edge, "timestamp_utc"], utc=True)
    ).dt.total_seconds() / 3600
    radius = ordered.loc[has_edge, "scenario"].str.extract(r"d(\d+)m")[0].astype(int)
    gap = ordered.loc[has_edge, "scenario"].str.extract(r"t(\d+)h")[0].astype(int)
    require(
        np.allclose(distances, ordered.loc[has_edge, "edge_distance_m"], atol=1e-6, rtol=0)
        and np.allclose(dt, ordered.loc[has_edge, "edge_signed_gap_hours"], atol=1e-9, rtol=0)
        and (distances <= radius.to_numpy() + 1e-6).all()
        and (dt.abs().to_numpy() <= gap).all(),
        "Fresh exact witness edge checks",
    )
    for keys, part in grouped:
        require(
            part.path_step.tolist() == list(range(len(part)))
            and part.detection_id.iloc[0] == keys[3]
            and part.detection_id.iloc[-1] == keys[4],
            "Complete first-to-anchor witness",
        )
    result, rebuilt = [], []
    member_groups = dict(tuple(members.groupby("cluster_id", sort=False)))
    path_groups = dict(
        tuple(paths.groupby(["review_unit_id", "scenario", "cluster_id"], sort=False))
    )
    cat = catalog.set_index("cluster_id")
    for context in contexts.itertuples():
        frame = member_groups[context.cluster_id]
        row = cat.loc[context.cluster_id]
        times = pd.to_datetime(frame.detection_timestamp_utc, utc=True, format="ISO8601")
        first = frame.loc[times.eq(times.min())]
        require(
            len(frame) == row.detection_count
            and times.min() == pd.Timestamp(context.first_detection_utc)
            and sorted(first.grid_id.unique()) == json.loads(context.earliest_grid_ids_json)
            and hashlib.sha256("\n".join(sorted(frame.detection_id)).encode()).hexdigest()
            == context.membership_sha256,
            "Saved full component",
        )
        anchors = json.loads(context.anchor_detection_ids_json)
        first_ids = json.loads(context.first_detection_ids_json)
        t = pd.Timestamp(context.prediction_timestamp_utc)
        end = t + pd.Timedelta(24, unit="h")
        require(
            set(first_ids) == set(first.detection_id)
            and len(set(anchors)) == len(anchors)
            and set(anchors) <= set(frame.detection_id),
            "First/anchor source coverage",
        )
        anchor_times = times.loc[frame.detection_id.isin(anchors)]
        require(anchor_times.gt(t).all() and anchor_times.le(end).all(), "In-window anchors")
        witness = path_groups[(context.review_unit_id, context.scenario, context.cluster_id)]
        pairs = set(zip(witness.first_detection_id, witness.anchor_detection_id, strict=True))
        require(pairs == {(a, b) for a in first_ids for b in anchors}, "Exact witness pair matrix")
        future_path = (pd.to_datetime(witness.timestamp_utc, utc=True) > end).any()
        if future_path:
            radius, gap = int(row.edge_radius_m), int(row.edge_gap_hours)
            prefix = prefix_first_sets(
                frame, anchors, end_utc=end, distance_m=radius, gap_hours=gap
            )
            for item in prefix.to_dict("records"):
                rebuilt.append(
                    {
                        "review_unit_id": context.review_unit_id,
                        "scenario": context.scenario,
                        "cluster_id": context.cluster_id,
                        **item,
                    }
                )
            signatures = sorted(
                (r.first_detection_utc, tuple(json.loads(r.earliest_grid_ids_json)))
                for r in prefix.itertuples()
            )
            proof = "exact_prefix_graph_rebuild"
        else:
            signatures = [
                (
                    context.first_detection_utc,
                    tuple(sorted(json.loads(context.earliest_grid_ids_json))),
                )
            ]
            proof = "all_first_to_anchor_paths_within_window_end"
        prefix_match = any(
            t < pd.Timestamp(time) <= end and context.grid_id in cells for time, cells in signatures
        )
        full_match = t < times.min() <= end and context.grid_id in set(first.grid_id)
        require(full_match == context.catalog_first_candidate_match, "Full-window match")
        result.append(
            {
                "review_unit_id": context.review_unit_id,
                "scenario": context.scenario,
                "cluster_id": context.cluster_id,
                "prediction_timestamp_utc": t.isoformat(),
                "grid_id": context.grid_id,
                "full_first_time": context.first_detection_utc,
                "full_first_cells_json": context.earliest_grid_ids_json,
                "members_after_window_end": int(times.gt(end).sum()),
                "proof_method": proof,
                "prefix_anchor_component_count": len(signatures),
                "prefix_first_signatures_json": json.dumps(signatures),
                "first_signature_changed": signatures
                != [
                    (
                        context.first_detection_utc,
                        tuple(sorted(json.loads(context.earliest_grid_ids_json))),
                    )
                ],
                "full_candidate_match": bool(full_match),
                "prefix_candidate_match": bool(prefix_match),
                "target": None,
            }
        )
    comparison = pd.DataFrame(result)
    by_scenario = comparison.groupby(["review_unit_id", "scenario"], as_index=False).agg(
        full_candidate_match=("full_candidate_match", "any"),
        prefix_candidate_match=("prefix_candidate_match", "any"),
        first_signature_changed=("first_signature_changed", "any"),
    )
    by_scenario["candidate_presence_changed"] = (
        by_scenario.full_candidate_match != by_scenario.prefix_candidate_match
    )
    by_scenario["target"] = None
    unit_summary = by_scenario.groupby("review_unit_id", as_index=False).agg(
        scenarios=("scenario", "nunique"),
        signature_changed=("first_signature_changed", "sum"),
        candidate_presence_changed=("candidate_presence_changed", "sum"),
    )
    require(len(by_scenario) == 171 and unit_summary.scenarios.eq(9).all(), "All nine comparisons")
    unit_summary["target"] = None
    out = (
        ROOT
        / "outputs/reports/dataset/event_window_context_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    frames = {
        "context_comparison.csv": comparison,
        "unit_scenario_comparison.csv": by_scenario,
        "unit_summary.csv": unit_summary,
        "rebuilt_prefix_components.csv": pd.DataFrame(rebuilt),
    }
    for name, frame in frames.items():
        frame.to_csv(out / name, index=False)
        disk = pd.read_csv(out / name, float_precision="round_trip")
        require(disk.target.isna().all(), "Empty targets on readback")
        pd.testing.assert_frame_equal(disk.drop(columns="target"), frame.drop(columns="target"))
    require(all(sha(ROOT / name) == value for name, value in pins.items()), "Direct-input closure")

    def save(name, value):
        (out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    save("input_manifest.json", pins)
    save(
        "readback.json",
        {
            "status": "window_context_diagnostic_only",
            "input_count": len(pins),
            "contexts": len(comparison),
            "unit_scenarios": len(by_scenario),
            "purposive_units": 19,
            "contexts_with_later_members": int(comparison.members_after_window_end.gt(0).sum()),
            "exact_prefix_context_rebuilds": int(
                comparison.proof_method.eq("exact_prefix_graph_rebuild").sum()
            ),
            "contexts_with_changed_first_signature": int(comparison.first_signature_changed.sum()),
            "units_with_changed_first_signature": int(unit_summary.signature_changed.gt(0).sum()),
            "unit_scenarios_with_changed_candidate_presence": int(
                by_scenario.candidate_presence_changed.sum()
            ),
            "units_with_changed_candidate_presence": int(
                unit_summary.candidate_presence_changed.gt(0).sum()
            ),
            "labels_created": False,
            "selected_event_policy": None,
            "model_ready": False,
            "negative_label_permitted": False,
            "daily_observation_status": "unknown",
            "final_merge_performed": False,
            "validation_accessed": False,
            "final_test_accessed": False,
            "diagnostic_network_requests": 0,
            "cloud_jobs_started": 0,
            "artifact_sha256": {p.name: sha(p) for p in out.iterdir() if p.is_file()},
        },
    )
    save("completion_readback.json", {"report_sha256": sha(out / "readback.json")})
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
