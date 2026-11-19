"""Review prior ancestry and later links for one Marmaris case; never accept real events."""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
from review_salur_lineage import prefix_equal, replay, resolve

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
NATIVE = BASE / "marmaris_native_support_v1/20261119T130257Z_bf16c6bd/readback.json"
PLAN = BASE / "observation_core_transfer_v1/20261119T124453Z_f5b8c745/native_plan.json"
CATALOG = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
PINS = {
    NATIVE: "09baaccbd41d5e8a175b2bd988d46acf25c782fd5ac0b20ab21679bea6024ff4",
    PLAN: "04b40b06a7137b0fbea2618a141867ad2fef13052e265ed070c13f34b358a864",
    CATALOG: "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5",
}
FIRST = pd.Timestamp("2022-06-21T23:22:00Z")
TARGET_START = pd.Timestamp("2022-06-21T00:00:00Z")
TARGET_END = pd.Timestamp("2022-06-22T00:00:00Z")


def main():
    require(all(digest(p) == h for p, h in PINS.items()), "Pinned native/context inputs")
    plan = json.loads(PLAN.read_text())
    primary_ids = set(plan["selection_catalog_ids"])
    native = json.loads(NATIVE.read_text())
    context_ids = {p["detection_id"] for p in native["points"]}
    with CATALOG.open(encoding="utf-8-sig", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if "2022-06-01" <= r["acq_date"] <= "2022-06-23"]
    frame = pd.DataFrame(rows)
    require(frame.detection_timestamp_utc.str.startswith("2022-06").all(), "2022 fit-role only")
    require(context_ids <= set(frame.detection_id), "Full case membership retained")
    out = (
        BASE
        / "marmaris_temporal_context_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    frame.to_csv(out / "bounded_June_catalog.csv", index=False)
    summaries = []
    for radius in (500, 1000, 2000):
        for gap in (24, 48, 72):
            scenario = f"d{radius}m_t{gap}h"
            full = replay(frame, radius, gap)
            checked = {}
            for name, cutoff in (("first_local", FIRST), ("target_end", TARGET_END)):
                prefix = replay(frame, radius, gap, cutoff)
                prefix_equal(prefix, full, cutoff)
                origins = resolve(prefix[2])
                indexed = prefix[3].set_index("detection_id")
                case_rows = indexed.loc[indexed.index.isin(primary_ids)]
                require(set(case_rows.index) == primary_ids, "All five source-near anchors")
                ids = set().union(
                    *(origins[state] for state in case_rows.ancestry_state_id_at_ingestion)
                )
                born = prefix[0].loc[prefix[0].birth_candidate_id.isin(ids)].copy()
                starts = pd.to_datetime(born.first_detection_utc, utc=True)
                early_ids = set(born.loc[starts.lt(TARGET_START), "birth_candidate_id"])
                groups = []
                for row in born.itertuples():
                    source_time = pd.Timestamp(row.first_detection_utc)
                    groups.append(
                        {
                            "birth_candidate_id": row.birth_candidate_id,
                            "first_detection_utc": row.first_detection_utc,
                            "earliest_grid_ids": json.loads(row.earliest_grid_ids_json),
                            "birth_before_target_start": bool(source_time < TARGET_START),
                            "birth_within_72h_of_left_boundary": bool(
                                source_time < pd.Timestamp("2022-06-04T00:00:00Z")
                            ),
                        }
                    )
                checked[name] = {
                    "source_rows_available": len(prefix[3]),
                    "matched_anchor_birth_candidates": groups,
                    "anchor_ids_with_preT_ancestry": sorted(
                        identity
                        for identity, row in case_rows.iterrows()
                        if origins[row.ancestry_state_id_at_ingestion] & early_ids
                    ),
                    "matched_ancestry_starts_at_first_local_minute": bool(starts.eq(FIRST).all()),
                    "prefix_history_unchanged_by_later_data": True,
                }
                folder = out / scenario / name
                folder.mkdir(parents=True, exist_ok=False)
                for filename, table in zip(
                    ("births.csv", "transitions.csv", "states.csv", "detections.csv"),
                    prefix[:4],
                    strict=True,
                ):
                    table.to_csv(folder / filename, index=False)
            summaries.append({"scenario": scenario, "checks": checked})
            print(scenario, "history_checked", flush=True)
    result = {
        "scope": "Marmaris_bounded_June_ancestry_diagnostic_only",
        "catalog_rows": len(frame),
        "catalog_days": ["2022-06-01", "2022-06-23"],
        "source_case_id": "marmaris_2022",
        "planned_anchor_ids": sorted(primary_ids),
        "full_future_context_end_inclusive": "2022-06-23T23:59:59.999999Z",
        "target_window": [TARGET_START.isoformat(), TARGET_END.isoformat()],
        "scenarios": summaries,
        "left_censoring_outside_saved_catalog_resolved": False,
        "absence_of_prior_detections_is_observation_coverage_proof": False,
        "new_physical_ignitions_verified": False,
        "source_three_vs_four_starts_resolved": False,
        "L_memberships_created": 0,
        "labels_created": False,
        "gate": specification(),
        "model_trained": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
        "code_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in [
                Path(__file__),
                ROOT / "scripts/quality/review_salur_lineage.py",
                ROOT / "src/wildfire_risk_prediction/event_lineage.py",
                ROOT / "src/wildfire_risk_prediction/event_review.py",
            ]
        },
        "artifact_sha256": {
            p.relative_to(out).as_posix(): digest(p) for p in out.rglob("*") if p.is_file()
        },
    }
    require(all(digest(p) == h for p, h in PINS.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Report readback")
    print(path.relative_to(ROOT).as_posix(), digest(path))


if __name__ == "__main__":
    main()
