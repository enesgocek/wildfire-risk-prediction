"""Validate the existing October lineage core against the new Salur reference context."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
from audit_stage_one_selection import verify

from wildfire_risk_prediction.event_lineage import VERSION, trace_lineage, verify_ancestry_records
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/reports/dataset/salur_event_context_v1/20261118T230221Z_cab0c9e1"
SOURCE_SHA = "89ffb290079ae4167cbf3b577e9787cbbde5092118acaab0d43d704189dad846"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(source, radius, gap, cutoff=None):
    if cutoff is not None:
        time = pd.to_datetime(source.detection_timestamp_utc, utc=True, format="ISO8601")
        source = source.loc[time.le(cutoff)]
    result = trace_lineage(source, distance_m=radius, gap_hours=gap)
    verify_ancestry_records(result[0], result[2], result[3])
    return result


def prefix_equal(prefix, full, cutoff):
    for index, time_field in (
        (0, "first_detection_utc"),
        (1, "recorded_at_utc"),
        (2, "recorded_at_utc"),
        (3, "timestamp_utc"),
    ):
        expected = full[index]
        mask = pd.to_datetime(expected[time_field], utc=True, format="ISO8601").le(cutoff)
        columns = [c for c in expected if c != "final_graph_membership_sha256"]
        pd.testing.assert_frame_equal(
            prefix[index][columns], expected.loc[mask, columns].reset_index(drop=True)
        )


def resolve(states):
    origins = {}
    for row in states.sort_values(["recorded_at_utc", "ancestry_state_id"]).itertuples():
        parents = json.loads(row.parent_state_ids_json)
        origins[row.ancestry_state_id] = (
            set().union(*(origins[p] for p in parents)) if parents else {row.birth_candidate_id}
        )
    return origins


def main():
    report = json.loads(verify(SOURCE / "readback.json", SOURCE_SHA).read_bytes())
    members = pd.read_csv(
        verify(SOURCE / "component_members.csv", report["artifact_sha256"]["component_members.csv"])
    )
    now = datetime.now(UTC)
    out = (
        ROOT
        / "outputs/reports/dataset/salur_lineage_validation_v1"
        / (now.strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    common = members.loc[members.scenario.eq("d2000m_t72h")].copy()
    common_ids = set(common.detection_id)
    artifacts, summaries, matched, assignment_pins = {}, [], [], {}
    local_id = report["first_local_ids"][0]
    older_id = report["future_edge_witness"]["historical_detection_id"]
    edge = pd.Timestamp(report["future_edge_witness"]["first_edge_utc"])
    cutoffs = {
        "first_local": pd.Timestamp(report["first_local_detection_utc"]),
        "target_end": pd.Timestamp(report["target_end_utc"]),
        "before_first_edge": pd.Timestamp(edge.value - 1, unit="ns", tz="UTC"),
        "at_first_edge": edge,
    }
    for old in report["scenarios"]:
        scenario = old["scenario"]
        radius, gap = (int(v) for v in scenario[1:].replace("m_t", " ").rstrip("h").split())
        source = members.loc[members.scenario.eq(scenario)].copy()
        full = replay(source, radius, gap)
        born, changed, states, detected, stats = full
        expected = hashlib.sha256("\n".join(sorted(source.detection_id)).encode()).hexdigest()
        require(
            stats["final_graph_components"] == 1
            and stats["source_detections"] == old["member_count"]
            and set(detected.final_graph_membership_sha256) == {expected},
            "Frozen component partition",
        )
        for cutoff in cutoffs.values():
            prefix_equal(replay(source, radius, gap, cutoff), full, cutoff)
        ancestry = resolve(states)
        indexed = detected.set_index("detection_id")
        local_births = ancestry[indexed.loc[local_id, "ancestry_state_id_at_ingestion"]]
        selected = born.loc[born.birth_candidate_id.isin(local_births)]
        require(
            len(selected) == 1
            and selected.first_detection_utc.eq(report["first_local_detection_utc"]).all()
            and report["marker_cell"] in json.loads(selected.earliest_grid_ids_json.iloc[0]),
            "Source-linked Salur birth retained",
        )
        summary = {
            "scenario": scenario,
            "detections": len(detected),
            "birth_hypotheses": len(born),
            "merge_nodes": int(changed.transition.eq("merge").sum()),
            "final_components": stats["final_graph_components"],
            "local_birth_ids": sorted(local_births),
            "local_birth_first_cells": json.loads(selected.earliest_grid_ids_json.iloc[0]),
            "local_birth_time": selected.first_detection_utc.iloc[0],
            "prefix_history_unchanged": True,
        }
        if scenario == "d2000m_t72h":
            older_births = ancestry[indexed.loc[older_id, "ancestry_state_id_at_ingestion"]]
            require(local_births.isdisjoint(older_births), "Distinct early hypotheses")
            merged = states.loc[states.recorded_at_utc.eq(edge.isoformat())]
            require(
                any(local_births | older_births <= ancestry[k] for k in merged.ancestry_state_id),
                "Known future merge preserves both histories",
            )
            summary["known_future_merge_preserves_both_births"] = True
            summary["historical_birth_ids"] = sorted(older_births)
        folder = out / scenario
        folder.mkdir()
        for name, table in zip(
            ("birth_candidates", "transitions", "ancestry_states", "detection_ancestry"),
            full[:4],
            strict=True,
        ):
            file = folder / f"{name}.csv"
            table.to_csv(file, index=False)
            disk = pd.read_csv(file)
            if "target" in table:
                require(table.target.isna().all() and disk.target.isna().all(), "No labels")
            require(len(disk) == len(table), "Output row count")
            artifacts[file.relative_to(out).as_posix()] = digest(file)
        verify_ancestry_records(
            pd.read_csv(folder / "birth_candidates.csv"),
            pd.read_csv(folder / "ancestry_states.csv"),
            pd.read_csv(folder / "detection_ancestry.csv"),
        )
        shared = replay(common, radius, gap)
        key = f"data/interim/event_grouping/{scenario}_assignments.csv"
        assignment_pins[key] = report["input_sha256"][key]
        saved = pd.read_csv(verify(ROOT / key, assignment_pins[key]))
        selected_assignments = saved.loc[saved.detection_id.isin(common_ids)]
        touched = set(selected_assignments.cluster_id)
        require(
            set(saved.loc[saved.cluster_id.isin(touched), "detection_id"]) == common_ids,
            "Complete common-cohort graph components",
        )
        expected = {
            hashlib.sha256("\n".join(sorted(g.detection_id)).encode()).hexdigest()
            for _, g in selected_assignments.groupby("cluster_id")
        }
        require(set(shared[3].final_graph_membership_sha256) == expected, "Paired partition")
        matched.append(
            {
                "scenario": scenario,
                "detections": len(shared[3]),
                "birth_hypotheses": len(shared[0]),
                "merge_nodes": int(shared[1].transition.eq("merge").sum()),
                "final_components": shared[4]["final_graph_components"],
                "target": None,
            }
        )
        summaries.append(summary)
    comparison = out / "common_cohort_comparison.csv"
    pd.DataFrame(matched).to_csv(comparison, index=False)
    artifacts[comparison.name] = digest(comparison)
    gate = specification()
    require(
        gate["daily_observation_status"] == "unknown"
        and not gate["positive_label_permitted"]
        and not gate["negative_label_permitted"],
        "Closed scientific gate",
    )
    receipt = {
        "version": VERSION,
        "created_utc": now.isoformat(),
        "scope": "existing_core_nine_bounded_salur_components_only",
        "researcher_direction": "A_preserve_birth_history_at_merges",
        "reused_core_document": "docs/EVENT_LINEAGE_2026-10-16.md",
        "source_readback_sha256": SOURCE_SHA,
        "source_members_sha256": report["artifact_sha256"]["component_members.csv"],
        "code_sha256": {
            name: digest(ROOT / name)
            for name in (
                "src/wildfire_risk_prediction/event_lineage.py",
                "src/wildfire_risk_prediction/event_review.py",
                "scripts/quality/review_salur_lineage.py",
                "tests/test_event_lineage_prefix.py",
            )
        },
        "common_cohort_assignment_sha256": assignment_pins,
        "artifact_sha256": artifacts,
        "prefix_replays": 36,
        "scenarios": summaries,
        "common_cohort_scenarios": matched,
        "common_cohort_detection_count": len(common),
        "prefix_comparison_excludes_retrospective_final_membership_hash": True,
        "preliminary_draft_source_preservation": (
            "outputs/reports/dataset/lineage_draft_preservation_v1/20261118T232202Z_cc671778"
        ),
        "target_admission": gate,
        "model_trained": False,
        "final_merge_approval": False,
    }
    file = out / "readback.json"
    file.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    require(json.loads(file.read_bytes()) == receipt, "JSON readback")
    print(out.relative_to(ROOT))
    print(pd.DataFrame(matched).drop(columns="target").to_string(index=False))
    print("SHA256", digest(file))


if __name__ == "__main__":
    main()
