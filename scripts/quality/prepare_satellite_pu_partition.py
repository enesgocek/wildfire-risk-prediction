"""Propose temporal pilot roles using observed graph context, never physical-event acceptance."""

import csv
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd
from prepare_full_u_feature_review import U_SHA, U
from prepare_satellite_pu_L_proposals import PARENT as COVER_PARENT
from prepare_satellite_pu_L_proposals import PARENT_SHA as COVER_PARENT_SHA
from prepare_source_pu_feature_review import review_key

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import detection_windows, specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PROPOSALS = BASE / "satellite_PU_L_proposals_v1/20261120T005519Z_62f3f815/readback.json"
PROPOSALS_SHA = "679a5ad9eab6342fa153c46cbbcc8f1e494b92256b592ba84f24823d0c0a4a85"
LINEAGE = BASE / "satellite_PU_lineage_v1/20261120T003414Z_a21f7422/readback.json"
LINEAGE_SHA = "b13d15d640f51662bd75fc65a25769ca02ceb69c80836c4fe2b99e788ae2e530"


def period(stamp):
    t = datetime.fromisoformat(stamp)
    require(
        t.tzinfo is not None
        and t.utcoffset() == timedelta(0)
        and t.time().replace(tzinfo=None) == datetime.min.time(),
        "UTC midnight pilot role",
    )
    if datetime(2018, 1, 1, tzinfo=UTC) <= t and t + timedelta(days=1) < datetime(
        2022, 1, 1, tzinfo=UTC
    ):
        return "proposed_fit_2018_2021"
    if datetime(2022, 1, 1, tzinfo=UTC) <= t and t + timedelta(days=1) < datetime(
        2023, 1, 1, tzinfo=UTC
    ):
        return "proposed_assessment_2022"
    return "boundary_review_not_used"


def partitions(keys, graph_context):
    initial = {key: period(key[1]) for key in keys}
    by_block = defaultdict(set)
    for key, phase in initial.items():
        for block in graph_context.get(key, set()):
            by_block[block].add(phase)
    bad = {
        block
        for block, phases in by_block.items()
        if len(phases) > 1 or "boundary_review_not_used" in phases
    }
    final = {
        key: "boundary_review_not_used" if graph_context.get(key, set()) & bad else phase
        for key, phase in initial.items()
    }
    kept = defaultdict(set)
    for key, phase in final.items():
        if phase != "boundary_review_not_used":
            kept[phase].update(graph_context.get(key, set()))
    require(
        not (kept["proposed_fit_2018_2021"] & kept["proposed_assessment_2022"]),
        "No shared observed graph blocks",
    )
    return final, bad


def main():
    pins = {
        PROPOSALS: PROPOSALS_SHA,
        LINEAGE: LINEAGE_SHA,
        COVER_PARENT: COVER_PARENT_SHA,
        U: U_SHA,
    }
    require(all(digest(p) == h for p, h in pins.items()), "Frozen preparation/proposal/U")
    proposal, lineage = [json.loads(p.read_bytes()) for p in (PROPOSALS, LINEAGE)]
    files = {
        PROPOSALS.parent / "proposal_key_union.csv": proposal["artifact_sha256"][
            "proposal_key_union.csv"
        ],
        PROPOSALS.parent / "all_first_cells_with_proposal_flags.csv": proposal["artifact_sha256"][
            "all_first_cells_with_proposal_flags.csv"
        ],
        LINEAGE.parent / "d2000m_t72h/detections.csv": lineage["artifact_sha256"][
            "d2000m_t72h/detections.csv"
        ],
    }
    pins.update(files)
    require(
        all(digest(p) == h for p, h in pins.items()),
        "Exact proposal and conservative graph context",
    )
    with U.open(encoding="utf-8", newline="") as stream:
        u_rows = list(csv.DictReader(stream))
    u_keys = {review_key(r["grid_id"], r["prediction_timestamp_utc"]) for r in u_rows}
    proposals = pd.read_csv(PROPOSALS.parent / "proposal_key_union.csv")
    source_keys = {
        review_key(g, t)
        for g, t in proposals[["grid_id", "prediction_timestamp_utc"]].itertuples(
            index=False, name=None
        )
    }
    require(
        len(u_keys) == 2048 and len(source_keys) == 1670 and proposals.target.isna().all(),
        "Same review populations",
    )
    detected = pd.read_csv(LINEAGE.parent / "d2000m_t72h/detections.csv")
    require(
        len(detected) == 28396 and detected.event_membership_complete.eq(False).all(),
        "Observed graph is not verified event membership",
    )
    by_id = detected.set_index("detection_id").final_graph_membership_sha256.to_dict()
    graph_context = defaultdict(set)
    windows = detection_windows(detected.timestamp_utc)
    for detection, window in zip(detected.itertuples(), windows.itertuples(), strict=True):
        key = (detection.grid_id, window.prediction_timestamp_utc.isoformat())
        if key in u_keys:
            graph_context[key].add(detection.final_graph_membership_sha256)
    groups = pd.read_csv(PROPOSALS.parent / "all_first_cells_with_proposal_flags.csv")
    selected = groups.loc[groups.possible_L_proposal]
    proposed_scenarios = defaultdict(set)
    for row in selected.itertuples():
        key = (row.grid_id, row.prediction_timestamp_utc)
        proposed_scenarios[key].add(row.scenario)
        graph_context[key].update(by_id[i] for i in json.loads(row.first_detection_ids_json))
    require(
        set(proposed_scenarios) == source_keys, "Every source proposal has raw graph provenance"
    )
    roles, bad = partitions(source_keys | u_keys, graph_context)
    rows = [
        {
            "grid_id": g,
            "prediction_timestamp_utc": t,
            "proposed_partition": phase,
            "original_U_sample_present": (g, t) in u_keys,
            "possible_L_proposal_present": (g, t) in source_keys,
            "proposed_scenarios_json": json.dumps(sorted(proposed_scenarios.get((g, t), set()))),
            "observed_graph_context_ids_json": json.dumps(sorted(graph_context.get((g, t), set()))),
            "observed_graph_membership_is_complete_physical_event": False,
            "target": None,
            "accepted_L_membership": None,
        }
        for (g, t), phase in sorted(roles.items())
    ]
    summaries = []
    for scenario in sorted(selected.scenario.unique()):
        summary = {"scenario": scenario}
        for phase in (
            "proposed_fit_2018_2021",
            "proposed_assessment_2022",
            "boundary_review_not_used",
        ):
            summary[phase] = {
                "U": sum(
                    r["original_U_sample_present"] and r["proposed_partition"] == phase
                    for r in rows
                ),
                "possible_L_keys": sum(
                    scenario in json.loads(r["proposed_scenarios_json"])
                    and r["proposed_partition"] == phase
                    for r in rows
                ),
            }
        summaries.append(summary)
    out = (
        BASE
        / "satellite_PU_partition_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    p = out / "proposed_key_roles.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    report = {
        "status": "satellite_pilot_partition_prepared_not_training_or_scientific_acceptance",
        "unique_keys_preserved": len(rows),
        "original_U_keys": 2048,
        "possible_L_key_union": 1670,
        "source_U_overlap_keys_preserved": len(source_keys & u_keys),
        "shared_observed_graph_blocks_after_quarantine": 0,
        "cross_or_boundary_graph_blocks": len(bad),
        "U_keys_with_observed_graph_context": sum(bool(graph_context.get(k)) for k in u_keys),
        "scenario_summaries": summaries,
        "true_physical_events_independence_verified": False,
        "2022_is_blind_independent_test": False,
        "original_U_sampling_or_weights_changed": False,
        "labels_or_accepted_L_created": 0,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "artifact_sha256": {p.name: digest(p)},
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    require(all(digest(p) == h for p, h in pins.items()), "Frozen inputs unchanged")
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    print("readback_sha256", digest(path), flush=True)
    for item in summaries:
        print(json.dumps(item), flush=True)


if __name__ == "__main__":
    main()
