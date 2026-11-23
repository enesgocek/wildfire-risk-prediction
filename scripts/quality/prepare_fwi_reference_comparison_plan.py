"""Count existing June 2022 calendar support for a proposed FWI comparison; do not join FWI."""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SCORES = BASE / "cross_source_fixed_model_run_v1/20261121T181438Z_bc972c9e"


def main():
    receipt = SCORES / "readback.json"
    require(
        digest(receipt) == "a4fb83beea02226eca149c5ca8a0383326a1db0143b2ca395adbc50a1e6ab6f9",
        "Original fixed-model result receipt",
    )
    original = json.loads(receipt.read_bytes())
    pins = {receipt: digest(receipt)}
    counts, first_keys = [], None
    for name, sha in original["artifact_sha256"].items():
        if not name.endswith("_source_calendar_scores.csv"):
            continue
        p = SCORES / name
        require(digest(p) == sha, "Existing score artifact unchanged")
        pins[p] = sha
        with p.open(encoding="utf-8", newline="") as stream:
            rows = [
                r
                for r in csv.DictReader(stream)
                if "2022-06-02" <= r["prediction_timestamp_utc"][:10] <= "2022-06-30"
            ]
        keys = sorted((r["grid_id"], r["prediction_timestamp_utc"]) for r in rows)
        require(len(set(keys)) == len(keys), "Unique calendar keys")
        require(first_keys is None or keys == first_keys, "Same rows across all nine settings")
        first_keys = keys
        require(
            all(
                r["target"] == r["accepted_L_membership"] == ""
                and r["daily_observation_status"] == "unknown"
                for r in rows
            ),
            "True labels remain blank; observation unknown",
        )
        complete = [r for r in rows if r["dynamic_15_complete"] == "True"]
        src = [r for r in complete if r["original_source_record_key_present"] == "True"]
        pairs = sum(
            sum(
                b["grid_id"] == a["grid_id"] and b["original_source_record_key_present"] == "False"
                for b in complete
            )
            for a in src
        )
        counts.append(
            {
                "scenario": name.split("_source_calendar")[0],
                "calendar_keys_before_FWI_support": len(rows),
                "grid_cells": len({r["grid_id"] for r in rows}),
                "source_calendar_keys_not_true_fires": sum(
                    r["original_source_record_key_present"] == "True" for r in rows
                ),
                "complete_existing_model_rows": len(complete),
                "potential_pairs_before_FWI_support": pairs,
            }
        )
    require(
        len(counts) == 9 and all(digest(p) == h for p, h in pins.items()),
        "Nine unchanged score files",
    )
    out = (
        BASE
        / "fwi_reference_comparison_plan_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    result = {
        "status": "comparison_scope_counted_proposal_only_not_execution_authorization",
        "scenario_counts": counts,
        "proposal": {
            "date_range": ["2022-06-02", "2022-06-30"],
            "FWI_nominal_day_relative_to_target_day": -1,
            "purpose": "exploratory_retrospective_reference_comparison_not_operational_backtest",
            "spatial_rule": "nearest_native_node_no_missing_replacement_no_resolution_gain",
            "comparison_support": "same_keys_and_pairs_with_finite_FWI_and_existing_model_score",
            "threshold_search_or_model_fitting": False,
            "new_downloads_or_cloud": False,
            "source_membership_is_true_Y": False,
            "new_2023_2024_2025_values": False,
            "risk_colors_labels_or_final_merge": False,
            "local_limit_seconds": 900,
            "researcher_method_direction_required_before_execution": True,
        },
        "FWI_arrays_read_or_joined": False,
        "new_scores_or_performance_metrics": 0,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print(json.dumps(counts[0], indent=2), flush=True)


if __name__ == "__main__":
    main()
