"""Describe fixed 2022 ranking support; no model loading, predictions or new labels."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction import frozen_score_diagnostics as diagnostic
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CONFIG = ROOT / "configs/frozen_score_diagnostics_v1.json"
PROTOTYPE = BASE / "historical_research_prototype_v2/20261123T195053Z_aa61b349"
RUN = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"
VARIANTS = {
    "primary_weather_XGBoost": "primary_score",
    "broad_weather_XGBoost": "broad_score",
    "frozen_linear": "linear_score",
}


def validate_policy(policy):
    require(
        policy["all_nine_scenarios_retained"] is True
        and policy["aggregations"]
        == ["pair_weighted", "equal_source_day", "equal_cell_month", "equal_cell"]
        and all(
            policy[k] is False
            for k in (
                "new_model_training",
                "new_predictions",
                "new_threshold_selection",
                "source_context_is_true_fire",
                "unassigned_is_true_negative",
                "main_AP_replaced",
                "new_Y_or_accepted_L",
                "closed_year_2023_2024_2025_values",
                "risk_probabilities_or_validated_colors",
                "final_merge",
            )
        ),
        "Only prespecified descriptive diagnostics on existing scores",
    )


def main():
    policy = json.loads(CONFIG.read_bytes())
    validate_policy(policy)
    pins = {
        PROTOTYPE
        / "readback.json": "1afe43954ce0ccbe139df71e414fda7b0d0faf9dbfc332ae66fbc0beea80caa1",
        RUN / "readback.json": "004f7d27d6b0f1825b2b00d7a2825b311e2483b5f2d73c7063cadd9b45b2946d",
        CONFIG: digest(CONFIG),
        Path(diagnostic.__file__): digest(Path(diagnostic.__file__)),
    }
    require(
        all(digest(p) == sha for p, sha in pins.items()), "Exact frozen experiment and prototype"
    )
    for folder in (PROTOTYPE, RUN):
        r = json.loads((folder / "readback.json").read_bytes())
        pins.update({folder / name: sha for name, sha in r["artifact_sha256"].items()})
    require(all(digest(p) == sha for p, sha in pins.items()), "Current immutable source bytes")
    raw = (PROTOTYPE / "review_data.js").read_text(encoding="utf-8").strip()
    prefix = "globalThis.RESEARCH_DATA="
    require(raw.startswith(prefix) and raw.endswith(";"), "Static JSON data assignment")
    data = json.loads(raw[len(prefix) : -1])
    require(
        data["scientific_state"]
        == {
            "target": None,
            "accepted_L_membership": None,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "fire_risk_validated": False,
        },
        "No scientific target assignment",
    )
    metrics = pd.read_csv(RUN / "metrics.csv", float_precision="round_trip")
    summary, contextual, omitted, source_tables = [], [], [], []
    for scenario_index, scenario in enumerate(data["scenarios"]):
        layout = pd.read_csv(RUN / scenario / "fit_layout.csv")
        seen = set(layout.grid_id)
        for cohort in ("four_province", "separate_Mersin"):
            records = pd.DataFrame(
                [
                    {
                        "grid_id": r["grid"],
                        "prediction_timestamp_utc": r["time"],
                        "primary_eligible": r["eligible"],
                        "source_context": bool(r["flags"] & (1 << scenario_index)),
                        "target": None,
                        "accepted_L_membership": None,
                        "daily_observation_status": "unknown",
                        "province_area_intersections": r["province"],
                        "cell_seen_in_fit": r["grid"] in seen,
                        "primary_score": r["scores"][scenario_index][0],
                        "broad_score": r["scores"][scenario_index][1],
                        "linear_score": r["scores"][scenario_index][2],
                    }
                    for r in data["records"]
                    if r["cohort"] == cohort
                ]
            )
            credits = diagnostic.source_day_credits(records, VARIANTS)
            require(not credits.empty, "Existing matched source-day support")
            credits.insert(0, "scenario", scenario)
            credits.insert(0, "cohort", cohort)
            source_tables.append(credits)
            for variant, group in credits.groupby("variant", sort=True):
                result = diagnostic.summarize(group)
                old = metrics.loc[
                    metrics.cohort.eq(cohort)
                    & metrics.scenario.eq(scenario)
                    & metrics.variant.eq(variant)
                    & metrics["slice"].eq("all_same_grid_month")
                ].iloc[0]
                require(
                    (
                        result["pairs"],
                        result["wins"],
                        result["ties"],
                        result["pair_weighted_credit"],
                    )
                    == (old.pairs, old.wins, old.ties, old.auxiliary_pair_AUC),
                    "Frozen global metrics restored exactly",
                )
                base = {"cohort": cohort, "scenario": scenario, "variant": variant}
                summary.append(base | result)
                for name, mask in diagnostic.contextual_slices(group).items():
                    if mask.any():
                        contextual.append(
                            base | {"slice": name} | diagnostic.summarize(group.loc[mask])
                        )
                    else:
                        contextual.append(
                            base
                            | {
                                "slice": name,
                                "pairs": 0,
                                "source_days": 0,
                                "cells": 0,
                                "cell_months": 0,
                                "pair_weighted_credit": None,
                            }
                        )
                table = diagnostic.leave_one_cell_out(group)
                for key, value in reversed(list(base.items())):
                    table.insert(0, key, value)
                omitted.append(table)
    out = (
        BASE
        / "frozen_score_support_diagnostic_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    pd.DataFrame(summary).to_csv(out / "aggregation_summary.csv", index=False)
    pd.DataFrame(contextual).to_csv(out / "contextual_summary.csv", index=False)
    pd.concat(source_tables, ignore_index=True).to_csv(
        out / "source_day_order_credits.csv", index=False
    )
    pd.concat(omitted, ignore_index=True).to_csv(out / "omit_one_assessment_cell.csv", index=False)
    require(all(digest(p) == sha for p, sha in pins.items()), "No earlier artifact modified")
    body = {
        "status": "fixed_score_support_diagnostics_complete_pending_separate_audit",
        "decision": policy,
        "frozen_summary_rows_restored": len(summary),
        "source_day_variant_rows": sum(len(t) for t in source_tables),
        "contextual_rows": len(contextual),
        "new_model_or_prediction_calls": 0,
        "source_day_is_verified_fire": False,
        "province_area_slices_may_overlap": True,
        "omitting_assessment_cells_is_spatially_heldout_training": False,
        "confidence_intervals_or_significance_test_created": False,
        "true_Y_or_accepted_L_created": 0,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    path = out / "readback.json"
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)
    print(
        "global metrics restored",
        len(summary),
        "source-day variant rows",
        body["source_day_variant_rows"],
        flush=True,
    )


if __name__ == "__main__":
    main()
