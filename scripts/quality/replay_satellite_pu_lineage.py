"""Replay the fixed fit-only satellite source under all saved ancestry scenarios; no labels."""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from uuid import uuid4

import pandas as pd
from review_salur_lineage import prefix_equal

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.event_lineage import trace_lineage, verify_ancestry_records
from wildfire_risk_prediction.event_review import spatial_links, training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import detection_windows, specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
POLICY = ROOT / "configs/satellite_noisy_pu_protocol_v1.json"
SOURCE = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
SOURCE_SHA = "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5"
KEYS = ["grid_id", "prediction_timestamp_utc"]


def fit_source(rows):
    selected = []
    for row in rows:
        if row["detection_timestamp_utc"][:4] not in {str(y) for y in range(2018, 2023)}:
            continue
        selected.append(
            {
                k: row[k]
                for k in (
                    "detection_id",
                    "grid_id",
                    "source_sensor",
                    "detection_timestamp_utc",
                    "latitude",
                    "longitude",
                    "type",
                    "confidence",
                )
            }
        )
    return training_detections(pd.DataFrame(selected))


def first_keys(births):
    mapped = detection_windows(births.first_detection_utc)
    result = []
    for row, window in zip(births.itertuples(), mapped.itertuples(), strict=True):
        for grid in json.loads(row.earliest_grid_ids_json):
            start = window.prediction_timestamp_utc
            result.append(
                {
                    "birth_candidate_id": row.birth_candidate_id,
                    "grid_id": grid,
                    "prediction_timestamp_utc": start.isoformat(),
                    "first_detection_utc": row.first_detection_utc,
                    "fit_role_boundary_review": start < pd.Timestamp("2018-01-01", tz="UTC")
                    or window.target_end_inclusive_utc >= pd.Timestamp("2023-01-01", tz="UTC"),
                    "weak_positive_membership": None,
                    "target": None,
                }
            )
    return pd.DataFrame(result)


def static_first_keys(frame, detected):
    joined = frame.merge(
        detected[["detection_id", "final_graph_membership_sha256"]],
        on="detection_id",
        validate="one_to_one",
    )
    rows = []
    for membership, group in joined.groupby("final_graph_membership_sha256"):
        first = group.loc[group.timestamp.eq(group.timestamp.min())]
        rows.append(
            {
                "birth_candidate_id": membership,
                "first_detection_utc": first.timestamp.iloc[0].isoformat(),
                "earliest_grid_ids_json": json.dumps(sorted(first.grid_id.unique())),
            }
        )
    return first_keys(pd.DataFrame(rows))


def validate_policy(policy):
    require(
        policy["decision_source"]
        == "explicit_user_selection_A_prepare_four_province_satellite_candidate_PU_protocol",
        "Explicit four-province preparation direction",
    )
    require(
        all(
            policy[k] is False
            for k in (
                "main_target_changed",
                "source_candidates_are_verified_physical_events",
                "unknown_is_negative",
                "candidate_overlap_with_U_removed",
                "WF1538_decision_overridden",
                "new_L_memberships_permitted",
                "positive_label_permitted",
                "negative_label_permitted",
                "model_training_authorized",
                "main_method_accepted",
                "final_merge_permitted",
                "2023_scientific_values_read_permitted",
                "2024_scientific_values_read_permitted",
                "2025_scientific_values_read_permitted",
            )
        ),
        "Preparation cannot open scientific gates",
    )
    require(
        policy["lineage_diagnostic"]["distances_m"] == [500, 1000, 2000]
        and policy["lineage_diagnostic"]["gaps_hours"] == [24, 48, 72]
        and policy["lineage_diagnostic"]["scenario_selected"] is None,
        "All saved scenarios, none selected",
    )


def main():
    started = monotonic()
    policy = json.loads(POLICY.read_bytes())
    validate_policy(policy)
    pins = {SOURCE: SOURCE_SHA, POLICY: digest(POLICY)}
    for path in (
        ROOT / "src/wildfire_risk_prediction/event_lineage.py",
        ROOT / "src/wildfire_risk_prediction/event_review.py",
        ROOT / "src/wildfire_risk_prediction/target_admission.py",
        Path(__file__).with_name("review_salur_lineage.py"),
    ):
        pins[path] = digest(path)
    require(
        all(digest(p) == h for p, h in pins.items()),
        "Fixed fit source and unchanged diagnostic core",
    )
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        frame = fit_source(csv.DictReader(stream))
    require(len(frame) == 28396 and frame.timestamp.dt.year.max() == 2022, "Same fit-only source")
    out = (
        BASE
        / "satellite_PU_lineage_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    (out / "inputs.json").write_text(
        json.dumps({p.relative_to(ROOT).as_posix(): h for p, h in pins.items()}, indent=2),
        encoding="utf-8",
    )
    summaries, union, artifacts = [], [], {}
    cutoff = pd.Timestamp(policy["lineage_diagnostic"]["prefix_cutoff_utc"])
    for radius in policy["lineage_diagnostic"]["distances_m"]:
        print("SPATIAL LINKS", radius, flush=True)
        links = spatial_links(frame, radius)
        for gap in policy["lineage_diagnostic"]["gaps_hours"]:
            scenario = f"d{radius}m_t{gap}h"
            print("LINEAGE REPLAY", scenario, flush=True)
            began = monotonic()
            result = trace_lineage(frame, distance_m=radius, gap_hours=gap, links=links)
            born, changes, states, detected, stats = result
            verified = verify_ancestry_records(born, states, detected)
            cells, baseline = first_keys(born), static_first_keys(frame, detected)
            cell_set = set(cells[KEYS].itertuples(index=False, name=None))
            baseline_set = set(baseline[KEYS].itertuples(index=False, name=None))
            require(baseline_set <= cell_set, "Static first keys retained by chronology")
            prefix_checked = [radius, gap] in policy["lineage_diagnostic"]["prefix_replay_pairs"]
            if prefix_checked:
                prefix = trace_lineage(
                    frame.loc[frame.timestamp.le(cutoff)], distance_m=radius, gap_hours=gap
                )
                prefix_equal(prefix, result, cutoff)
            folder = out / scenario
            folder.mkdir()
            for name, data in (
                ("births", born),
                ("transitions", changes),
                ("states", states),
                ("detections", detected),
                ("birth_cell_keys", cells),
                ("static_first_keys", baseline),
            ):
                path = folder / (name + ".csv")
                data.to_csv(path, index=False)
                artifacts[path.relative_to(out).as_posix()] = digest(path)
            summary = {
                "scenario": scenario,
                **stats,
                **verified,
                "birth_cell_day_keys": len(cell_set),
                "same_input_static_first_keys": len(baseline_set),
                "additional_birth_keys_hidden_by_later_graph_merges": len(cell_set - baseline_set),
                "multi_cell_births": int(
                    born.earliest_grid_ids_json.map(lambda x: len(json.loads(x)) > 1).sum()
                ),
                "fit_boundary_review_rows": int(cells.fit_role_boundary_review.sum()),
                "prefix_replayed_and_unchanged": prefix_checked,
                "elapsed_seconds": round(monotonic() - began, 3),
            }
            summaries.append(summary)
            union.append(cells.assign(scenario=scenario))
            receipt = folder / "scenario_receipt.json"
            receipt.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            artifacts[receipt.relative_to(out).as_posix()] = digest(receipt)
            print(json.dumps(summary), flush=True)
    pd.concat(union, ignore_index=True).to_csv(
        out / "all_scenario_birth_cell_keys.csv", index=False
    )
    artifacts["all_scenario_birth_cell_keys.csv"] = digest(out / "all_scenario_birth_cell_keys.csv")
    require(all(digest(p) == h for p, h in pins.items()), "Frozen inputs unchanged")
    report = {
        "status": "four_province_fit_lineage_preparation_complete_no_L_Y_or_training",
        "decision": policy,
        "source_detections": len(frame),
        "scenarios": summaries,
        "new_L_or_Y_memberships": 0,
        "physical_events_accepted": 0,
        "scenario_selected": None,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "artifact_sha256": artifacts,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "elapsed_seconds": round(monotonic() - started, 3),
    }
    destination = out / "readback.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    print("readback_sha256", digest(destination), flush=True)


if __name__ == "__main__":
    main()
