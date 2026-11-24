"""Execute the accepted bounded assessment using only frozen 2022 score CSVs."""

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction import source_disjoint_evaluation as evaluation
from wildfire_risk_prediction import source_disjoint_plan as planning
from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PLAN = BASE / "source_disjoint_evaluation_preparation_v1/20261124T030406Z_9554fb98"
AUDIT = BASE / "source_disjoint_preparation_audit_v1/20261124T030456Z_26cc1be8"
RUN = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"
CONFIG = ROOT / "configs/source_disjoint_evaluation_execution_v1.json"
VARIANTS = {
    "primary_weather_XGBoost": "new_primary_weather_source_score_not_probability",
    "broad_weather_XGBoost": "previous_broad_xgboost_source_score_not_probability",
    "frozen_linear": "previous_broad_frozen_linear_source_score_not_probability",
}


def work(out):
    started = time.monotonic()
    decision = json.loads(CONFIG.read_bytes())
    if (
        decision["selected_direction"] != "A_run_bounded_frozen_source_overlap_assessment"
        or any(
            decision[k]
            for k in (
                "new_training",
                "new_predictions",
                "new_source_membership",
                "new_Y_or_L",
                "closed_years",
                "risk_probability_or_validated_colors",
                "final_merge",
            )
        )
        or decision["maximum_runtime_seconds"] != 900
        or decision["maximum_metric_rows"] != 405
    ):
        raise ValueError("Exact accepted assessment scope")
    pins = {
        PLAN / "readback.json": decision["preparation_readback_sha256"],
        AUDIT / "readback.json": decision["preparation_audit_sha256"],
        RUN / "readback.json": "004f7d27d6b0f1825b2b00d7a2825b311e2483b5f2d73c7063cadd9b45b2946d",
        CONFIG: digest(CONFIG),
        Path(evaluation.__file__): digest(Path(evaluation.__file__)),
        Path(planning.__file__): digest(Path(planning.__file__)),
    }
    for folder in (PLAN, RUN):
        receipt = json.loads((folder / "readback.json").read_bytes())
        pins.update({folder / name: sha for name, sha in receipt["artifact_sha256"].items()})
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Frozen proposal and model outputs")
    proposal = json.loads((PLAN / "execution_proposal.json").read_bytes())
    anchors = pd.read_csv(PLAN / "source_anchor_inventory.csv")
    support = pd.read_csv(PLAN / "planned_support.csv")
    old = pd.read_csv(RUN / "metrics.csv", float_precision="round_trip")
    results, registries = [], []
    reference_keys = None
    for scenario in proposal["scenarios"]:
        if time.monotonic() - started > 900:
            raise TimeoutError("Local time budget")
        scores = pd.read_csv(
            RUN / scenario / "separate_Mersin_scores.csv", float_precision="round_trip"
        )
        if reference_keys is None:
            reference_keys = scores[evaluation.KEYS].copy()
        pd.testing.assert_frame_equal(reference_keys, scores[evaluation.KEYS], check_exact=True)
        for group in planning.GROUPS:
            pairs = evaluation.comparison_indices(scores, anchors, group)
            registry = pairs.copy()
            registry.insert(0, "source_group", group)
            registry.insert(0, "scenario", scenario)
            registries.append(registry)
            masks = evaluation.slice_masks(pairs)
            for section, mask in masks.items():
                part = pairs.loc[mask]
                planned = support.loc[
                    support.source_group.eq(group) & support["slice"].eq(section)
                ].iloc[0]
                if len(part) != planned.planned_comparison_pairs_per_model_scenario:
                    raise ValueError("Fixed planned comparison days")
                for variant, column in VARIANTS.items():
                    values = scores[column].to_numpy()
                    metric = evaluation.ordering_metric(
                        values[part.calendar_row_source.to_numpy()],
                        values[part.calendar_row_other.to_numpy()],
                    )
                    if group == planning.GROUPS[0]:
                        original = old.loc[
                            old.cohort.eq("separate_Mersin")
                            & old.scenario.eq(scenario)
                            & old.variant.eq(variant)
                            & old["slice"].eq(section)
                        ].iloc[0]
                        if tuple(metric.values()) != (
                            original.pairs,
                            original.wins,
                            original.ties,
                            original.auxiliary_pair_AUC,
                        ):
                            raise ValueError("Exact original 135 reference metrics")
                    results.append(
                        {
                            "source_group": group,
                            "scenario": scenario,
                            "variant": variant,
                            "slice": section,
                        }
                        | metric
                    )
    if len(results) != 405:
        raise ValueError("Bounded complete metric inventory")
    table = pd.DataFrame(results)
    original = table.loc[table.source_group.eq(planning.GROUPS[0])].set_index(
        ["scenario", "variant", "slice"]
    )
    deltas = []
    for row in table.loc[table.source_group.ne(planning.GROUPS[0])].to_dict("records"):
        baseline = original.loc[(row["scenario"], row["variant"], row["slice"])]
        deltas.append(
            row
            | {
                "original_pairs": int(baseline.pairs),
                "delta_from_original": row["auxiliary_pair_AUC"] - baseline.auxiliary_pair_AUC
                if pd.notna(row["auxiliary_pair_AUC"]) and pd.notna(baseline.auxiliary_pair_AUC)
                else None,
            }
        )
    table.to_csv(out / "metrics.csv", index=False)
    pd.DataFrame(deltas).to_csv(out / "group_vs_original_delta.csv", index=False)
    pd.concat(registries, ignore_index=True).to_csv(out / "paired_day_registry.csv", index=False)
    (out / "execution_decision.json").write_text(
        json.dumps(decision, indent=2) + "\n", encoding="utf-8"
    )
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Earlier artifacts preserved")
    body = {
        "status": "accepted_source_overlap_assessment_complete_pending_separate_audit",
        "decision": decision,
        "elapsed_worker_seconds": time.monotonic() - started,
        "metric_rows": len(table),
        "original_metric_rows_restored": 135,
        "new_nested_subset_metric_rows": len(deltas),
        "pair_registry_rows": sum(len(r) for r in registries),
        "new_training_or_prediction_calls": 0,
        "excluded_sources_relabelled": 0,
        "true_fire_validation": False,
        "final_merge": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(
        json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker:
        work(args.worker)
        return
    out = (
        BASE
        / "source_disjoint_frozen_assessment_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    subprocess.run(
        [sys.executable, str(Path(__file__)), "--worker", str(out)],
        cwd=ROOT,
        timeout=900,
        check=True,
    )
    print(out.relative_to(ROOT).as_posix(), "child_completed_pending_independent_audit", flush=True)


if __name__ == "__main__":
    main()
