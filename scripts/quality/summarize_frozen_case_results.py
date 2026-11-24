"""Summarize audited case context and draw existing common-pair metrics."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CASES = BASE / "frozen_rank_case_review_v1/20261124T024256Z_abeb3e00"
AUDIT = BASE / "frozen_rank_case_audit_v1/20261124T024500Z_68829a04"
RUN = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"


def main():
    audit = json.loads((AUDIT / "readback.json").read_bytes())
    if audit["status"] != "independent_frozen_rank_case_audit_passed" or audit[
        "source_readback_sha256"
    ] != digest(CASES / "readback.json"):
        raise ValueError("Case audit binding")
    pins = {
        AUDIT / "readback.json": digest(AUDIT / "readback.json"),
        CASES / "readback.json": digest(CASES / "readback.json"),
        RUN / "readback.json": "004f7d27d6b0f1825b2b00d7a2825b311e2483b5f2d73c7063cadd9b45b2946d",
    }
    for folder in (CASES, RUN):
        receipt = json.loads((folder / "readback.json").read_bytes())
        pins.update({folder / p: sha for p, sha in receipt["artifact_sha256"].items()})
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Current frozen data")
    cases = pd.read_csv(CASES / "all_source_day_cases.csv", float_precision="round_trip")
    stable = cases.loc[cases.all_nine_scenario_support].copy()
    summaries = []
    for cohort, group in stable.groupby("cohort", sort=True):
        span = group.primary_credit_max - group.primary_credit_min
        summaries.append(
            {
                "cohort": cohort,
                "all_case_inventory_rows": int(cases.cohort.eq(cohort).sum()),
                "all_nine_case_rows": len(group),
                "credit_mean_min": float(group.primary_credit_mean.min()),
                "credit_mean_median": float(group.primary_credit_mean.median()),
                "credit_mean_max": float(group.primary_credit_mean.max()),
                "median_nine_scenario_credit_span": float(span.median()),
                "max_nine_scenario_credit_span": float(span.max()),
                "cases_strictly_both_sides_of_half_credit": int(
                    (group.primary_credit_min.lt(0.5) & group.primary_credit_max.gt(0.5)).sum()
                ),
            }
        )
    metrics = pd.read_csv(RUN / "metrics.csv", float_precision="round_trip")
    variants = ["primary_weather_XGBoost", "broad_weather_XGBoost", "frozen_linear"]
    labels = ["Ana tam-alan XGBoost", "Önceki geniş-alan XGBoost", "Dondurulmuş doğrusal"]
    colors = ["#24516c", "#98633f", "#6a7082"]
    slices = ["all_same_grid_month", "gap_1_to_3_days"]
    figure, axes = plt.subplots(2, 2, figsize=(12, 6.5), constrained_layout=True)
    plotted = []
    for row, cohort in enumerate(("four_province", "separate_Mersin")):
        for col, section in enumerate(slices):
            axis = axes[row, col]
            for y, (variant, color) in enumerate(zip(variants, colors, strict=True)):
                group = metrics.loc[
                    metrics.cohort.eq(cohort)
                    & metrics.variant.eq(variant)
                    & metrics["slice"].eq(section)
                ].sort_values("scenario")
                if len(group) != 9:
                    raise ValueError("All nine common-pair metrics required")
                values = group.auxiliary_pair_AUC.to_numpy()
                if not ((values >= 0.4) & (values <= 0.7)).all():
                    raise ValueError("Plot bounds would hide a metric")
                axis.plot([min(values), max(values)], [y, y], color=color, linewidth=2)
                axis.scatter(values, [y + (i - 4) * 0.035 for i in range(9)], color=color, s=24)
                plotted.extend(group.to_dict("records"))
            axis.axvline(0.5, linestyle="--", color="#aaaaaa", linewidth=1)
            axis.set_xlim(0.4, 0.7)
            axis.set_ylim(2.5, -0.5)
            axis.set_yticks(range(3), labels=labels, fontsize=9)
            area = "Dört-il aday takvimi" if row == 0 else "Ayrı Mersin kaynak takvimi"
            window = (
                "Aynı hücre/ayın tüm karşılaştırmaları"
                if col == 0
                else "Yalnız 1–3 gün uzaklıktaki günler"
            )
            axis.set_title(area + "\n" + window, fontsize=10)
            axis.set_xlabel("Yardımcı kaynak-gün sıra kredisi", fontsize=9)
            axis.grid(axis="x", alpha=0.15)
    figure.suptitle(
        "Mevcut 2022 ortak çiftleri: dokuz ayarın tamamı\n"
        "Noktalar ayarları, çizgiler min–maks aralığını gösterir; "
        "güven aralığı ve gerçek yangın başarımı değildir.",
        fontsize=12,
    )
    out = (
        BASE
        / "frozen_case_result_synthesis_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    figure.savefig(out / "existing_model_comparison.png", dpi=160)
    plt.close(figure)
    pd.DataFrame(summaries).to_csv(out / "case_support_summary.csv", index=False)
    pd.DataFrame(plotted).to_csv(out / "plotted_existing_metrics.csv", index=False)
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Inputs changed")
    body = {
        "status": "audited_case_descriptive_synthesis_complete",
        "posthoc": True,
        "new_model_or_prediction_calls": 0,
        "all_nine_cases": len(stable),
        "plotted_existing_metric_rows": len(plotted),
        "new_fire_labels": 0,
        "half_credit_crossing_is_risk_threshold": False,
        "final_merge": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), body["status"], flush=True)


if __name__ == "__main__":
    main()
