"""Create illustrative source-day context from existing 2022 scores, without fit."""

import json
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wildfire_risk_prediction import frozen_case_review as review
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.ranking_queries import DYNAMIC_FEATURES

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PROTOTYPE = BASE / "historical_research_prototype_v2/20261123T195053Z_aa61b349"
SUPPORT = BASE / "frozen_score_support_diagnostic_v1/20261124T022210Z_e025acc0"
AUDIT = BASE / "frozen_score_support_audit_v1/20261124T022742Z_5a966751"
CONFIG = ROOT / "configs/frozen_case_review_v1.json"


def main():
    policy = json.loads(CONFIG.read_bytes())
    require(
        all(
            policy[k] is False
            for k in (
                "new_training",
                "new_predictions",
                "new_risk_thresholds",
                "new_fire_labels",
                "closed_years",
                "causal_feature_explanation",
                "final_merge",
            )
        )
        and policy["illustrative_cases_per_cohort"] == 6,
        "Descriptive frozen-score context only",
    )
    pins = {
        PROTOTYPE
        / "readback.json": "1afe43954ce0ccbe139df71e414fda7b0d0faf9dbfc332ae66fbc0beea80caa1",
        SUPPORT
        / "readback.json": "b888b1a1ea01af8b59728395a940f4f7f87b22c46830752e350dd686e4f1efc9",
        AUDIT / "readback.json": "2aa0472d9ab3480b9426b0ddbfd2978f1e6d3b111aceb8128879d27f5b1393d2",
        CONFIG: digest(CONFIG),
        Path(review.__file__): digest(Path(review.__file__)),
    }
    for folder in (PROTOTYPE, SUPPORT):
        receipt = json.loads((folder / "readback.json").read_bytes())
        pins.update({folder / name: sha for name, sha in receipt["artifact_sha256"].items()})
    require(all(digest(p) == sha for p, sha in pins.items()), "Unchanged audited inputs")
    payload = (PROTOTYPE / "review_data.js").read_text(encoding="utf-8").strip()
    data = json.loads(payload.removeprefix("globalThis.RESEARCH_DATA=")[:-1])
    require(
        data["scientific_state"]
        == {
            "target": None,
            "accepted_L_membership": None,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "fire_risk_validated": False,
        },
        "Scientific target remains unknown",
    )
    count = len(data["scenarios"])
    require(count == 9, "All frozen scenarios")
    credits = pd.read_csv(SUPPORT / "source_day_order_credits.csv", float_precision="round_trip")
    cases = review.inventory(credits, count)
    selected = review.select_examples(cases)
    out = (
        BASE
        / "frozen_rank_case_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    details, features, timelines, summaries = [], [], [], []
    fig, axes = plt.subplots(4, 3, figsize=(15, 13), constrained_layout=True)
    for axis, case in zip(axes.flat, selected.to_dict("records"), strict=True):
        rows, source = review.month_context(data, case)
        feature_rows = review.feature_context(data, rows, source, DYNAMIC_FEATURES)
        line = review.timeline(rows, count)
        feature_rows.insert(0, "case_id", case["case_id"])
        line.insert(0, "case_id", case["case_id"])
        features.append(feature_rows)
        timelines.append(line)
        comparison_rows = []
        for i, scenario in enumerate(data["scenarios"]):
            for other in rows:
                if other["flags"] & (1 << i):
                    continue
                difference = (
                    datetime.fromisoformat(other["time"]) - datetime.fromisoformat(source["time"])
                ).days
                record = {
                    "case_id": case["case_id"],
                    "scenario": scenario,
                    "other_prediction_timestamp_utc": other["time"],
                    "other_day_minus_source_day": difference,
                    "other_source_context_scenarios": other["flags"].bit_count(),
                }
                for j, variant in enumerate(("primary", "broad", "linear")):
                    a, b = source["scores"][i][j], other["scores"][i][j]
                    record[variant + "_source_score"] = a
                    record[variant + "_other_score"] = b
                    record[variant + "_order_credit_twice"] = 2 * int(a > b) + int(a == b)
                comparison_rows.append(record)
        table = pd.DataFrame(comparison_rows)
        require(table.other_day_minus_source_day.ne(0).all(), "Different comparison dates")
        details.append(table)
        result = case | {
            "stable_unassigned_reference_days": int(
                feature_rows.stable_unassigned_reference_days.iloc[0]
            ),
            "source_day_rank_mean": float(
                line.loc[
                    line.prediction_timestamp_utc.eq(source["time"]), "primary_rank_mean"
                ].iloc[0]
            ),
            "eligible_days_in_month": len(rows),
            "target": None,
            "accepted_L_membership": None,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
        }
        for variant in ("primary", "broad", "linear"):
            for name, mask in (
                ("near", table.other_day_minus_source_day.abs().between(1, 3)),
                ("before", table.other_day_minus_source_day.lt(0)),
                ("after", table.other_day_minus_source_day.gt(0)),
            ):
                part = table.loc[mask]
                result[variant + "_" + name + "_pairs_across_scenarios"] = len(part)
                result[variant + "_" + name + "_credit"] = (
                    float(Fraction(int(part[variant + "_order_credit_twice"].sum()), 2 * len(part)))
                    if len(part)
                    else None
                )
        summaries.append(result)
        x = pd.to_datetime(line.prediction_timestamp_utc, utc=True).dt.day.to_numpy()
        axis.fill_between(
            x, line.primary_rank_min, line.primary_rank_max, color="#bed2e1", alpha=0.7
        )
        axis.plot(x, line.primary_rank_mean, color="#24516c", linewidth=1.4)
        axis.axvline(int(source["time"][8:10]), color="#ab6428", linestyle="--", linewidth=1.2)
        axis.scatter(
            [int(source["time"][8:10])], [result["source_day_rank_mean"]], color="#ab6428", zorder=4
        )
        axis.set_ylim(len(rows) + 1, 0)
        axis.set_title(
            f"{case['case_id']} | {case['illustrative_tier']}\n"
            f"{case['province_area_intersections']} {source['time'][:10]} | "
            f"{case['grid_id'].split('_V1_')[-1]}",
            fontsize=9,
        )
        axis.set_xlabel("Ayın günü", fontsize=8)
        axis.set_ylabel("Aynı hücre/ay sırası (1 üstte)", fontsize=8)
        axis.grid(alpha=0.15)
    fig.suptitle(
        "Mevcut 2022 skorları: 12 örnek kaynak günü\n"
        "Çizgi: dokuz ayarın ortalama sırası; bant: min–maks. "
        "Kaynak günü turuncu. Yangın olasılığı değildir.",
        fontsize=13,
    )
    fig.savefig(out / "case_rank_timelines.png", dpi=150)
    plt.close(fig)
    cases.to_csv(out / "all_source_day_cases.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / "illustrative_cases.csv", index=False)
    pd.concat(features, ignore_index=True).to_csv(out / "feature_context.csv", index=False)
    pd.concat(timelines, ignore_index=True).to_csv(out / "monthly_rank_context.csv", index=False)
    pd.concat(details, ignore_index=True).to_csv(out / "case_comparisons.csv", index=False)
    require(all(digest(p) == sha for p, sha in pins.items()), "No prior artifact changed")
    body = {
        "status": "frozen_rank_case_context_complete_pending_separate_audit",
        "policy": policy,
        "case_inventory_rows": len(cases),
        "illustrative_cases": len(selected),
        "illustrative_selection_is_representative_population_sample": False,
        "scenario_band_is_confidence_interval": False,
        "feature_contrasts_are_model_attribution": False,
        "new_model_or_prediction_calls": 0,
        "true_fire_errors_counted": 0,
        "final_merge": False,
        "scientific_state": data["scientific_state"],
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(
        json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(out.relative_to(ROOT).as_posix(), body["status"], flush=True)


if __name__ == "__main__":
    main()
