"""Retain chronological candidate births and graph mergers on frozen review components."""

import hashlib
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.event_lineage import VERSION, trace_lineage, verify_ancestry_records
from wildfire_risk_prediction.event_review import spatial_links
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = "outputs/reports/dataset/event_window_context_v1/20261016T183626Z_0c072991"
TRACE = "outputs/reports/dataset/sensitive_trace_v1/20261014T194620Z_284f08c1"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline lineage diagnostic")


def run():
    socket.create_connection = deny
    socket.socket.connect = deny
    pins = {}

    def bind(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular lineage input")
        digest = sha(path)
        require(expected is None or digest == expected, "Pinned lineage input")
        pins[name] = digest
        return path

    previous = json.loads(
        bind(
            PREVIOUS + "/readback.json",
            "52be23b64057c01666a3de8fe341f5646b1e6aa97c2bbeccd819c9eaa3ca21b4",
        ).read_text()
    )
    receipt = json.loads(
        bind(
            PREVIOUS + "/completion_readback.json",
            "27e700bf751b64fe50dc1fec706b2aadffe1823c3c030a9506ca400ccb1c9ef8",
        ).read_text()
    )
    require(
        receipt["report_sha256"] == sha(ROOT / PREVIOUS / "readback.json")
        and not previous["labels_created"],
        "Previous diagnostic receipt",
    )
    old_pins = json.loads(
        bind(
            PREVIOUS + "/input_manifest.json", previous["artifact_sha256"]["input_manifest.json"]
        ).read_text()
    )
    frames = {}
    for name in (
        "component_source_members.csv",
        "component_graph_review.csv",
        "unit_scenario_components.csv",
    ):
        path = TRACE + "/" + name
        frames[name] = pd.read_csv(bind(path, old_pins[path]), float_precision="round_trip")
    policy = json.loads(
        bind(
            "configs/first_cell_candidates_v1.json",
            old_pins["configs/first_cell_candidates_v1.json"],
        ).read_text()
    )
    require(
        policy["method"] == "all_recorded_earliest_cells"
        and policy["grouping_scenario_selected"] is None
        and policy["positive_label_permitted"] is False,
        "Candidate-only first cells",
    )
    for name in (
        "src/wildfire_risk_prediction/event_lineage.py",
        "tests/test_event_lineage.py",
        "scripts/quality/audit_event_lineage.py",
        "src/wildfire_risk_prediction/event_review.py",
        "src/wildfire_risk_prediction/feature_join.py",
    ):
        bind(name, old_pins.get(name))
    members, catalog, contexts = (
        frames[n]
        for n in (
            "component_source_members.csv",
            "component_graph_review.csv",
            "unit_scenario_components.csv",
        )
    )
    require(
        len(catalog) == len(contexts) == 181 and contexts.review_unit_id.nunique() == 19,
        "Frozen sensitive context scope",
    )
    require(
        catalog.cluster_id.is_unique
        and set(members.cluster_id) == set(catalog.cluster_id)
        and all(f.target.isna().all() for f in (members, catalog, contexts)),
        "Unlabelled source scope",
    )
    groups = dict(tuple(members.groupby("cluster_id", sort=False)))
    cache, ledger = {}, {}
    births, transitions, states, assignments, summaries = [], [], [], [], []
    for i, row in enumerate(catalog.itertuples(), 1):
        frame = groups[row.cluster_id]
        require(
            hashlib.sha256("\n".join(sorted(frame.detection_id)).encode()).hexdigest()
            == row.membership_sha256,
            "Source component membership",
        )
        key = (int(row.edge_radius_m), row.membership_sha256)
        if key not in cache:
            cache[key] = spatial_links(frame, int(row.edge_radius_m))
        born, changed, ancestry, detected, stats = trace_lineage(
            frame,
            distance_m=int(row.edge_radius_m),
            gap_hours=int(row.edge_gap_hours),
            links=cache[key],
        )
        require(
            stats["source_detections"] == row.detection_count
            and stats["edge_count"] == row.verified_internal_graph_edges
            and stats["final_graph_components"] == 1
            and set(detected.final_graph_membership_sha256) == {row.membership_sha256},
            "Exact saved edge count and final graph partition",
        )
        first = pd.to_datetime(born.first_detection_utc, utc=True)
        original_first_cells = sorted(
            {
                cell
                for cells in born.loc[first.eq(first.min()), "earliest_grid_ids_json"]
                for cell in json.loads(cells)
            }
        )
        require(
            first.min() == pd.Timestamp(row.first_detection_utc)
            and original_first_cells == json.loads(row.earliest_grid_ids_json),
            "All original earliest cells preserved across birth candidates",
        )
        ledger[row.cluster_id] = (born, detected)
        for table, store in (
            (born, births),
            (changed, transitions),
            (ancestry, states),
            (detected, assignments),
        ):
            copy = table.copy()
            copy["source_cluster_id"] = row.cluster_id
            store.append(copy)
        summaries.append(
            {
                "source_cluster_id": row.cluster_id,
                "scenario": row.scenario,
                **stats,
                "merge_transitions": int(changed.transition.eq("merge").sum()),
                "continuation_transitions": int(changed.transition.eq("continuation").sum()),
                "ambiguous_ingestion_detections": int(
                    detected.origin_candidate_count_at_ingestion.gt(1).sum()
                ),
            }
        )
        if i % 30 == 0:
            print(f"Reviewed component contexts {i}/{len(catalog)}", flush=True)
    comparisons, anchor_tables = [], []
    for context in contexts.itertuples():
        born, detected = ledger[context.cluster_id]
        t = pd.Timestamp(context.prediction_timestamp_utc)
        end = t + pd.Timedelta(24, unit="h")
        first = pd.to_datetime(born.first_detection_utc, utc=True)
        match = (
            first.gt(t)
            & first.le(end)
            & born.earliest_grid_ids_json.map(
                lambda value, grid=context.grid_id: grid in json.loads(value)
            )
        )
        comparisons.append(
            {
                "review_unit_id": context.review_unit_id,
                "scenario": context.scenario,
                "static_first_candidate_match": context.catalog_first_candidate_match,
                "chronological_birth_candidate_match": bool(match.any()),
                "target": None,
            }
        )
        anchors = set(json.loads(context.anchor_detection_ids_json))
        chosen = detected.loc[detected.detection_id.isin(anchors)].copy()
        require(len(chosen) == len(anchors), "Exact anchor ancestry coverage")
        chosen["review_unit_id"] = context.review_unit_id
        anchor_tables.append(chosen)
    comparisons = (
        pd.DataFrame(comparisons)
        .groupby(["review_unit_id", "scenario"], as_index=False)
        .agg(
            static_first_candidate_match=("static_first_candidate_match", "any"),
            chronological_birth_candidate_match=("chronological_birth_candidate_match", "any"),
        )
    )
    require(
        len(comparisons) == 171
        and comparisons.groupby("review_unit_id").scenario.nunique().eq(9).all(),
        "Nineteen by nine comparison matrix",
    )
    require(
        (
            ~comparisons.static_first_candidate_match
            | comparisons.chronological_birth_candidate_match
        ).all(),
        "No static first match lost by retaining births",
    )
    comparisons["additional_birth_candidate_match"] = (
        comparisons.chronological_birth_candidate_match & ~comparisons.static_first_candidate_match
    )
    comparisons["target"] = None
    tables = {
        "birth_candidates.csv": pd.concat(births, ignore_index=True),
        "transitions.csv": pd.concat(transitions, ignore_index=True),
        "ancestry_states.csv": pd.concat(states, ignore_index=True),
        "detection_ancestry.csv": pd.concat(assignments, ignore_index=True),
        "component_summary.csv": pd.DataFrame(summaries),
        "unit_scenario_comparison.csv": comparisons,
        "anchor_ancestry.csv": pd.concat(anchor_tables, ignore_index=True),
    }
    require(
        tables["birth_candidates.csv"].birth_candidate_id.is_unique
        and tables["ancestry_states.csv"].ancestry_state_id.is_unique,
        "No candidate identity collisions across contexts",
    )
    summary = tables["component_summary.csv"]
    require(
        (summary.birth_candidates - summary.merge_component_reduction).eq(1).all(),
        "Each original component conserved independently",
    )
    out = (
        ROOT
        / "outputs/reports/dataset/event_lineage_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    reloaded = {}
    for name, table in tables.items():
        table.to_csv(out / name, index=False)
        disk = pd.read_csv(out / name, keep_default_na=False)
        reloaded[name] = disk.copy()
        if "target" in table:
            require(table.target.isna().all() and disk.target.eq("").all(), "No labels on disk")
            reloaded[name]["target"] = pd.NA
            disk, table = disk.drop(columns="target"), table.drop(columns="target")
        pd.testing.assert_frame_equal(disk, table.fillna(""))
    ancestry_proof = verify_ancestry_records(
        reloaded["birth_candidates.csv"],
        reloaded["ancestry_states.csv"],
        reloaded["detection_ancestry.csv"],
    )
    require(all(sha(ROOT / n) == value for n, value in pins.items()), "Input closure")

    def save(name, value):
        (out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    save("input_manifest.json", pins)
    anchors = tables["anchor_ancestry.csv"]
    save(
        "readback.json",
        {
            "status": "chronological_ancestry_diagnostic_not_event_acceptance",
            "version": VERSION,
            **ancestry_proof,
            "input_count": len(pins),
            "component_contexts": len(summary),
            "context_detection_rows": int(summary.source_detections.sum()),
            "unique_source_detections": members.detection_id.nunique(),
            "birth_candidates_across_contexts": len(tables["birth_candidates.csv"]),
            "merge_transitions_across_contexts": int(summary.merge_transitions.sum()),
            "merge_component_reduction": int(summary.merge_component_reduction.sum()),
            "contexts_with_multiple_birth_candidates": int(summary.birth_candidates.gt(1).sum()),
            "additional_unit_scenario_birth_matches": int(
                comparisons.additional_birth_candidate_match.sum()
            ),
            "units_with_additional_birth_match": comparisons.loc[
                comparisons.additional_birth_candidate_match, "review_unit_id"
            ].nunique(),
            "anchor_scenario_rows": len(anchors),
            "ambiguous_anchor_scenario_rows": int(
                anchors.origin_candidate_count_at_ingestion.gt(1).sum()
            ),
            "labels_created": False,
            "selected_grouping_policy": None,
            "physical_events_accepted": 0,
            "event_membership_complete": False,
            "model_ready": False,
            "negative_label_permitted": False,
            "daily_observation_status": "unknown",
            "final_merge_performed": False,
            "validation_accessed": False,
            "final_test_accessed": False,
            "network_requests": 0,
            "cloud_jobs_started": 0,
            "artifact_sha256": {p.name: sha(p) for p in out.iterdir() if p.is_file()},
        },
    )
    save("completion_readback.json", {"report_sha256": sha(out / "readback.json")})
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
