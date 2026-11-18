"""Close the bounded Anamur/Menderes comparison with the unchanged lineage core."""

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import pandas as pd
from audit_stage_one_selection import verify
from review_salur_lineage import prefix_equal, replay

from wildfire_risk_prediction.event_review import training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
PRIOR = (
    ROOT / "outputs/reports/dataset/july_case_admission_v1/20261108T122815Z_6b4e98d6/readback.json"
)
PRIOR_SHA = "ee5575a918833b4e28df2032c5a28f9f630177252bb8648c7c744a9ebd416b77"
CATALOG = "data/interim/firms_combined_candidates_2018_2024.csv"
CELLS = {
    "menderes_north": {"E6933_5K_V1_C525_R906"},
    "menderes_south": {"E6933_5K_V1_C524_R906", "E6933_5K_V1_C524_R905"},
    "anamur": {"E6933_5K_V1_C632_R864"},
}


def main():
    began = perf_counter()
    prior = json.loads(verify(PRIOR, PRIOR_SHA).read_bytes())
    verify(ROOT / CATALOG, prior["inputs_sha256"][CATALOG])
    selected = set().union(*CELLS.values())
    with (ROOT / CATALOG).open(encoding="utf-8-sig", newline="") as stream:
        rows = [
            r
            for r in csv.DictReader(stream)
            if r["acq_date"] in ("2023-07-10", "2023-07-11") and r["grid_id"] in selected
        ]
    source = training_detections(pd.DataFrame(rows))
    inputs = {str(PRIOR.relative_to(ROOT)): PRIOR_SHA, CATALOG: prior["inputs_sha256"][CATALOG]}
    results, birth_tables, detection_tables = [], [], []
    end = pd.Timestamp("2023-07-11", tz="UTC")
    for scenario in sorted(prior["menderes_full_components"]):
        key = f"data/interim/event_grouping/{scenario}_assignments.csv"
        inputs[key] = prior["inputs_sha256"][key]
        assignments = pd.read_csv(verify(ROOT / key, inputs[key]))
        radius, gap = (int(v) for v in scenario[1:].replace("m_t", " ").rstrip("h").split())
        for name, cells in CELLS.items():
            group = source.loc[source.grid_id.isin(cells)].copy()
            expected = (
                prior["anamur_full_components"][scenario][0]
                if name == "anamur"
                else prior["menderes_full_components"][scenario][name.split("_")[1]]
            )
            require(len(group) == expected["members"], "Prior group size")
            matched = assignments.loc[assignments.detection_id.isin(group.detection_id)]
            require(
                len(matched) == len(group) and matched.cluster_id.nunique() == 1,
                "Source identities",
            )
            whole = assignments.loc[assignments.cluster_id.eq(matched.cluster_id.iloc[0])]
            require(set(whole.detection_id) == set(group.detection_id), "Complete frozen component")
            full = replay(group, radius, gap)
            born, transitions, _, detected, stats = full
            require(
                len(born) == 1
                and not transitions.transition.eq("merge").any()
                and stats["final_graph_components"] == 1
                and born.first_detection_utc.iloc[0] == expected["first_detection_utc"]
                and json.loads(born.earliest_grid_ids_json.iloc[0]) == expected["first_grid_ids"],
                "Stable first hypothesis matches previous review",
            )
            for cutoff in (group.timestamp.min(), end):
                prefix_equal(replay(group, radius, gap, cutoff), full, cutoff)
            birth_tables.append(
                born.assign(review_case=name, source_cluster_id=matched.cluster_id.iloc[0])
            )
            detection_tables.append(detected.assign(review_case=name))
            results.append(
                {
                    "scenario": scenario,
                    "review_case": name,
                    "detections": len(group),
                    "birth_hypotheses": len(born),
                    "merge_transitions": 0,
                    "first_detection_utc": born.first_detection_utc.iloc[0],
                    "first_cells_json": born.earliest_grid_ids_json.iloc[0],
                    "detections_after_first_target_end": int(group.timestamp.gt(end).sum()),
                    "prefix_history_unchanged": True,
                    "target": None,
                }
            )
    require(len(source) == 19 and len(results) == 27, "Bounded three-group comparison")
    out = (
        ROOT
        / "outputs/reports/dataset/july_lineage_validation_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in {
        "comparison.csv": pd.DataFrame(results),
        "birth_candidates.csv": pd.concat(birth_tables, ignore_index=True),
        "detection_ancestry.csv": pd.concat(detection_tables, ignore_index=True),
    }.items():
        p = out / name
        frame.to_csv(p, index=False)
        require(pd.read_csv(p).target.isna().all(), "No output labels")
        artifacts[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    gate = specification()
    require(not gate["positive_label_permitted"] and not gate["negative_label_permitted"], "Gate")
    report = {
        "scope": "two_case_three_catalog_groups_training_only",
        "input_sha256": inputs,
        "artifact_sha256": artifacts,
        "code_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in (
                "src/wildfire_risk_prediction/event_lineage.py",
                "scripts/quality/review_salur_lineage.py",
                "scripts/quality/review_july_lineage.py",
            )
        },
        "unique_source_detections": len(source),
        "group_scenario_comparisons": len(results),
        "prefix_replays": 54,
        "new_fire_labels_accepted": 0,
        "local_elapsed_seconds": perf_counter() - began,
        "elapsed_is_full_dataset_runtime_estimate": False,
        "target_admission": gate,
        "scientific_stage_one_accepted": False,
        "model_trained": False,
        "final_merge_approval": False,
    }
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    require(json.loads(p.read_bytes()) == report, "JSON readback")
    print(out.relative_to(ROOT))
    print("PASS 27 bounded comparisons and 54 prefixes; no scientific label admission")
    print("SHA256", hashlib.sha256(p.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
