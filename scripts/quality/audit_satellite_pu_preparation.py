"""Bind ancestry first detections to historical local cover; keep all memberships unassigned."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
LINEAGE = BASE / "satellite_PU_lineage_v1/20261120T003414Z_a21f7422/readback.json"
LINEAGE_SHA = "b13d15d640f51662bd75fc65a25769ca02ceb69c80836c4fe2b99e788ae2e530"
COVER = BASE / "satellite_PU_cover_v1/20261120T003942Z_3f82694d/readback.json"
COVER_SHA = "ae771636b7c230afe7b9603b00f266eab3a3a3fa408a56f9b765a27f6da34900"


def first_cell_context(births, keys, points):
    require(
        points.detection_id.is_unique and births.birth_candidate_id.is_unique,
        "Unique input identities",
    )
    require(births.target.isna().all() and keys.target.isna().all(), "Unassigned target only")
    indexed = points.set_index("detection_id")
    key_index = keys.set_index(["birth_candidate_id", "grid_id"])
    require(key_index.index.is_unique, "All initial cells once per candidate")
    rows = []
    for birth in births.itertuples():
        ids = json.loads(birth.birth_detection_ids_json)
        first = indexed.loc[ids]
        require(
            first.detection_timestamp_utc.map(pd.Timestamp)
            .eq(pd.Timestamp(birth.first_detection_utc))
            .all(),
            "Exact same-time first detections, not later cover",
        )
        require(
            set(first.grid_id) == set(json.loads(birth.earliest_grid_ids_json)),
            "All first cells retained",
        )
        for cell, group in first.groupby("grid_id", sort=True):
            key = key_index.loc[(birth.birth_candidate_id, cell)]
            a = group.cgls_2017_center_context.eq("forest_shrub")
            b = group.corine_2018_center_context.eq("forest_shrub")
            rows.append(
                {
                    "birth_candidate_id": birth.birth_candidate_id,
                    "scenario": birth.scenario,
                    "grid_id": cell,
                    "prediction_timestamp_utc": key.prediction_timestamp_utc,
                    "first_detection_utc": birth.first_detection_utc,
                    "first_detection_ids_json": json.dumps(sorted(group.index.tolist())),
                    "first_center_count": len(group),
                    "cgls_2017_woody_center_count": int(a.sum()),
                    "corine_2018_woody_center_count": int(b.sum()),
                    "both_maps_woody_center_count": int((a & b).sum()),
                    "all_first_centers_woody_2017": bool(a.all()),
                    "any_first_center_woody_2017": bool(a.any()),
                    "all_first_centers_woody_both_maps": bool((a & b).all()),
                    "fit_role_boundary_review": bool(key.fit_role_boundary_review),
                    "reference_map_context_is_actual_event_habitat": False,
                    "weak_positive_membership": None,
                    "target": None,
                }
            )
    require(len(rows) == len(keys), "No lost first-cell rows")
    return pd.DataFrame(rows)


def main():
    pins = {LINEAGE: LINEAGE_SHA, COVER: COVER_SHA}
    require(all(digest(p) == h for p, h in pins.items()), "Completed lineage and map records")
    lineage, cover = [json.loads(p.read_bytes()) for p in (LINEAGE, COVER)]
    for parent, report in ((LINEAGE, lineage), (COVER, cover)):
        pins.update({parent.parent / p: h for p, h in report["artifact_sha256"].items()})
    require(all(digest(p) == h for p, h in pins.items()), "Current parent artifacts")
    points = pd.read_csv(
        COVER.parent / "historical_center_context.csv", float_precision="round_trip"
    )
    require(len(points) == 28396 and points.target.isna().all(), "Same unlabelled fit source")
    summaries, tables = [], []
    out = (
        BASE
        / "satellite_PU_preparation_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    for old in lineage["scenarios"]:
        name = old["scenario"]
        births = pd.read_csv(LINEAGE.parent / name / "births.csv")
        keys = pd.read_csv(LINEAGE.parent / name / "birth_cell_keys.csv")
        table = first_cell_context(births, keys, points)
        tables.append(table)
        inside = table.loc[~table.fit_role_boundary_review]

        def key_count(mask, data=inside):
            return len(data.loc[mask, ["grid_id", "prediction_timestamp_utc"]].drop_duplicates())

        summaries.append(
            {
                "scenario": name,
                "birth_first_cell_rows": len(table),
                "fit_boundary_rows_preserved": int(table.fit_role_boundary_review.sum()),
                "fit_distinct_cell_day_keys": key_count(pd.Series(True, index=inside.index)),
                "fit_keys_with_any_woody_2017_first_center": key_count(
                    inside.any_first_center_woody_2017
                ),
                "fit_keys_with_an_all_woody_2017_first_cell_group": key_count(
                    inside.all_first_centers_woody_2017
                ),
                "fit_keys_with_an_all_woody_both_maps_first_cell_group": key_count(
                    inside.all_first_centers_woody_both_maps
                ),
                "new_L_or_Y_memberships": 0,
            }
        )
    combined = pd.concat(tables, ignore_index=True)
    path = out / "all_scenario_first_cell_cover_review.csv"
    combined.to_csv(path, index=False)
    report = {
        "status": "four_province_satellite_PU_protocol_inputs_prepared_not_L_Y_or_model_acceptance",
        "scenario_summaries": summaries,
        "all_first_cell_rows": len(combined),
        "CGLS_2017_is_primary_preevent_context_proposal_only": True,
        "CORINE_2018_is_auxiliary_context_not_mandatory_filter": True,
        "admission_rule_selected": None,
        "new_L_or_Y_memberships": 0,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "artifact_sha256": {path.name: digest(path)},
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    require(all(digest(p) == h for p, h in pins.items()), "Original evidence unchanged")
    destination = out / "readback.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    print("readback_sha256", digest(destination), flush=True)
    for item in summaries:
        print(json.dumps(item), flush=True)


if __name__ == "__main__":
    main()
