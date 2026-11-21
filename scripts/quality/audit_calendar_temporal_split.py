"""Audit observed graph overlap and potential matched-date support; do not select/train a method."""

import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
LINEAGE = BASE / "satellite_PU_lineage_v1/20261120T003414Z_a21f7422"
OLD_SPLIT = BASE / "satellite_PU_partition_v1/20261120T010148Z_74c8eee5"
CALENDAR = BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896"
PROPOSALS = BASE / "satellite_PU_L_proposals_v1/20261120T005519Z_62f3f815"


def potential_support(keys, phase, complete_keys, affected, source, role):
    strata = defaultdict(lambda: [0, 0])
    source_count, other_count = 0, 0
    for key in keys & complete_keys - affected:
        if phase[key] != role:
            continue
        position = 0 if key in source else 1
        strata[(key[0], key[1][:7])][position] += 1
        source_count += position == 0
        other_count += position == 1
    return {
        "complete_dynamic_source_context_rows": source_count,
        "complete_dynamic_other_rows_not_fire_negatives": other_count,
        "potential_same_grid_year_month_pairs": sum(a * b for a, b in strata.values()),
        "strata_with_both_source_contexts": sum(bool(a and b) for a, b in strata.values()),
    }


def main():
    inputs = {
        LINEAGE
        / "readback.json": "b13d15d640f51662bd75fc65a25769ca02ceb69c80836c4fe2b99e788ae2e530",
        OLD_SPLIT
        / "readback.json": "7f8169cf0dbc365ea576e722c66e018d63812829be1810f1bf90bd3dfebef7ff",
        CALENDAR
        / "readback.json": "b718ed5d7ff492ddaf6d5217e7f88b3f62a6024a9d2138f4225154b3e3576040",
        PROPOSALS
        / "readback.json": "679a5ad9eab6342fa153c46cbbcc8f1e494b92256b592ba84f24823d0c0a4a85",
    }
    join.require(
        all(digest(p) == h for p, h in inputs.items()), "Exact graph, role and calendar receipts"
    )
    reports = {
        folder: json.loads((folder / "readback.json").read_bytes())
        for folder in (LINEAGE, OLD_SPLIT, CALENDAR, PROPOSALS)
    }
    for folder, names in (
        (LINEAGE, ("d2000m_t72h/detections.csv",)),
        (OLD_SPLIT, ("proposed_key_roles.csv",)),
        (PROPOSALS, ("all_first_cells_with_proposal_flags.csv",)),
    ):
        inputs.update({folder / n: reports[folder]["artifact_sha256"][n] for n in names})
    inputs.update({CALENDAR / p: h for p, h in reports[CALENDAR]["artifact_sha256"].items()})
    join.require(
        all(digest(p) == h for p, h in inputs.items()), "Current metadata and graph artifacts"
    )
    snapshot = CALENDAR / reports[CALENDAR]["snapshot_directory"]
    metadata = parse_csv((snapshot / "review_roles.csv").read_bytes())
    features = parse_csv((snapshot / "features.csv").read_bytes()).set_index(join.KEYS)
    keys = set(metadata[join.KEYS].itertuples(index=False, name=None))
    phase = {
        tuple(r[k] for k in join.KEYS): r["review_temporal_role"]
        for r in metadata.to_dict("records")
    }
    detected = parse_csv((LINEAGE / "d2000m_t72h/detections.csv").read_bytes())
    context, block_roles = defaultdict(set), defaultdict(set)
    for row in detected.itertuples():
        t = datetime.fromisoformat(row.timestamp_utc) - timedelta(microseconds=1)
        stamp = t.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        key = (row.grid_id, stamp)
        if key in keys:
            context[key].add(row.final_graph_membership_sha256)
            block_roles[row.final_graph_membership_sha256].add(phase[key])
    shared = {g for g, roles in block_roles.items() if len(roles) > 1}
    affected = {k for k in keys if context[k] & shared}
    held_blocks = {g for k in keys if phase[k] == "proposed_assessment_2022" for g in context[k]}
    old = parse_csv((OLD_SPLIT / "proposed_key_roles.csv").read_bytes())
    proposals = parse_csv((PROPOSALS / "all_first_cells_with_proposal_flags.csv").read_bytes())
    proposals = proposals.loc[proposals.possible_L_proposal]
    dynamic = [
        f
        for f in join.feature_names()
        if f.startswith(("vegetation_", "temperature_", "dewpoint_", "wind_", "soil_", "rain_"))
    ]
    join.require(len(dynamic) == 15, "Exactly eleven weather and four vegetation fields")
    complete_mask = features[dynamic].notna().all(axis=1)
    complete_keys = set(features.index[complete_mask].tolist())
    print("Graph and complete-dynamic masks ready", flush=True)
    summaries = []
    for scenario, block in proposals.groupby("scenario", sort=True):
        source = set(block[join.KEYS].itertuples(index=False, name=None))
        old_fit_blocks = set()
        for row in old.to_dict("records"):
            if row["proposed_partition"] == "proposed_fit_2018_2021" and (
                row["original_U_sample_present"]
                or scenario in json.loads(row["proposed_scenarios_json"])
            ):
                old_fit_blocks.update(json.loads(row["observed_graph_context_ids_json"]))
        potential = {}
        for role in ("proposed_fit_2018_2021", "proposed_assessment_2022"):
            potential[role] = potential_support(keys, phase, complete_keys, affected, source, role)
        summaries.append(
            {
                "scenario": scenario,
                "old_fitted_key_graphs_shared_with_new_calendar_2022": len(
                    old_fit_blocks & held_blocks
                ),
                "potential_complete_dynamic_pair_support_not_training": potential,
            }
        )
    out = (
        BASE
        / "source_calendar_temporal_split_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    report = {
        "status": "observed_graph_split_and_potential_pair_support_audited_not_new_training",
        "calendar_keys": len(keys),
        "calendar_keys_with_observed_detection_graph_context": sum(bool(context[k]) for k in keys),
        "shared_observed_graph_blocks_between_calendar_roles": len(shared),
        "calendar_keys_affected_if_future_fit_quarantines_shared_graphs": len(affected),
        "scenario_summaries": summaries,
        "dynamic_feature_names": dynamic,
        "graph_is_verified_physical_event_identity": False,
        "new_source_indicator_labels_or_pair_matrix_created": False,
        "model_fitted": False,
        "row_deleted_from_original_calendar": False,
        "new_Y_or_accepted_L_created": 0,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in inputs.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    join.require(
        all(digest(p) == h for p, h in inputs.items()), "Original metadata and X unchanged"
    )
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print(
        "shared_observed_blocks", len(shared), "affected_calendar_keys", len(affected), flush=True
    )


if __name__ == "__main__":
    main()
