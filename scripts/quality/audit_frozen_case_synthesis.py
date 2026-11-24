"""Verify the descriptive summary and every plotted existing metric separately."""

import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCE = BASE / "frozen_case_result_synthesis_v1/20261124T024652Z_f63eea3c"
CASES = BASE / "frozen_rank_case_review_v1/20261124T024256Z_abeb3e00"
RUN = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"


def main():
    receipt = json.loads((SOURCE / "readback.json").read_bytes())
    pins = {ROOT / name: sha for name, sha in receipt["input_sha256"].items()}
    pins.update({SOURCE / name: sha for name, sha in receipt["artifact_sha256"].items()})
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Frozen synthesis source bytes")
    inventory = pd.read_csv(CASES / "all_source_day_cases.csv", float_precision="round_trip")
    summary = pd.read_csv(SOURCE / "case_support_summary.csv", float_precision="round_trip")
    if len(summary) != 2 or summary.cohort.nunique() != 2:
        raise ValueError("Both cohorts once")
    for row in summary.to_dict("records"):
        all_cases = inventory.loc[inventory.cohort.eq(row["cohort"])].to_dict("records")
        records = [r for r in all_cases if r["all_nine_scenario_support"]]
        means = [r["primary_credit_mean"] for r in records]
        spans = [r["primary_credit_max"] - r["primary_credit_min"] for r in records]
        expected = {
            "all_case_inventory_rows": len(all_cases),
            "all_nine_case_rows": len(records),
            "credit_mean_min": min(means),
            "credit_mean_median": median(means),
            "credit_mean_max": max(means),
            "median_nine_scenario_credit_span": median(spans),
            "max_nine_scenario_credit_span": max(spans),
            "cases_strictly_both_sides_of_half_credit": sum(
                r["primary_credit_min"] < 0.5 < r["primary_credit_max"] for r in records
            ),
        }
        if any(row[k] != v for k, v in expected.items()):
            raise ValueError("Case summary independently recomputed")
    source = pd.read_csv(RUN / "metrics.csv", float_precision="round_trip")
    expected_metrics = source.loc[source["slice"].isin(["all_same_grid_month", "gap_1_to_3_days"])]
    plotted = pd.read_csv(SOURCE / "plotted_existing_metrics.csv", float_precision="round_trip")
    keys = ["cohort", "scenario", "variant", "slice"]
    pd.testing.assert_frame_equal(
        plotted.sort_values(keys).reset_index(drop=True),
        expected_metrics.sort_values(keys).reset_index(drop=True),
        check_exact=True,
    )
    if len(plotted) != 108 or plotted.duplicated(keys).any():
        raise ValueError("All existing figure points exactly once")
    out = (
        BASE
        / "frozen_case_synthesis_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    body = {
        "status": "independent_case_summary_and_108_figure_values_verified",
        "source_readback_sha256": digest(SOURCE / "readback.json"),
        "cohorts": 2,
        "existing_metrics": len(plotted),
        "scientific_figure_png_inspected_separately": False,
        "new_training_or_predictions": 0,
        "true_fire_validation": False,
        "auditor_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), body["status"], flush=True)


if __name__ == "__main__":
    main()
