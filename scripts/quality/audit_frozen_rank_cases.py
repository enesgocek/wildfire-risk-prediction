"""Independently check illustrative case selection, ranks and feature references."""

import json
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from statistics import median
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCE = BASE / "frozen_rank_case_review_v1/20261124T024256Z_abeb3e00"
PROTOTYPE = BASE / "historical_research_prototype_v2/20261123T195053Z_aa61b349"
SUPPORT = BASE / "frozen_score_support_diagnostic_v1/20261124T022210Z_e025acc0"
KEYS = ["cohort", "grid_id", "source_prediction_timestamp_utc"]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def ratio(values):
    return float(Fraction(sum(values), 2 * len(values))) if values else None


def main():
    receipt = json.loads((SOURCE / "readback.json").read_bytes())
    pins = {ROOT / p: sha for p, sha in receipt["input_sha256"].items()}
    pins.update({SOURCE / p: sha for p, sha in receipt["artifact_sha256"].items()})
    check(all(digest(p) == sha for p, sha in pins.items()), "Frozen inputs and artifacts")

    def read(name):
        return pd.read_csv(SOURCE / (name + ".csv"), float_precision="round_trip")

    inventory, cases, feature, lines, comparisons = [
        read(n)
        for n in (
            "all_source_day_cases",
            "illustrative_cases",
            "feature_context",
            "monthly_rank_context",
            "case_comparisons",
        )
    ]
    credits = pd.read_csv(SUPPORT / "source_day_order_credits.csv", float_precision="round_trip")
    primary = credits.loc[credits.variant.eq("primary_weather_XGBoost")]
    check(
        not inventory.duplicated(KEYS).any() and len(inventory) == primary.groupby(KEYS).ngroups,
        "Full source-day inventory",
    )
    for row in inventory.to_dict("records"):
        group = primary.loc[(primary[KEYS] == pd.Series({k: row[k] for k in KEYS})).all(axis=1)]
        values = [Fraction(int(r.credit_twice), 2 * int(r.pairs)) for r in group.itertuples()]
        check(
            len(group) == row["scenario_count"]
            and row["all_nine_scenario_support"] == (len(group) == 9),
            "Scenario support",
        )
        check(
            row["primary_credit_mean"] == float(sum(values, Fraction()) / len(values))
            and row["primary_credit_min"] == float(min(values))
            and row["primary_credit_max"] == float(max(values)),
            "All-scenario credit aggregation",
        )
    chosen = []
    for cohort in sorted(inventory.cohort.unique()):
        candidates = inventory.loc[
            inventory.cohort.eq(cohort) & inventory.all_nine_scenario_support
        ].to_dict("records")
        candidates.sort(
            key=lambda r: (
                r["primary_credit_mean"],
                r["grid_id"],
                r["source_prediction_timestamp_utc"],
            )
        )
        n = len(candidates)
        center = sorted(range(2, n - 2), key=lambda i: (abs(i - (n - 1) / 2), i))[:2]
        for i in [0, 1, *sorted(center), n - 2, n - 1]:
            chosen.append(tuple(candidates[i][k] for k in KEYS))
    check(
        chosen == list(cases[KEYS].itertuples(index=False, name=None)),
        "Exact disjoint low/central/high examples",
    )
    check(
        cases.target.isna().all()
        and cases.accepted_L_membership.isna().all()
        and cases.daily_observation_status.eq("unknown").all()
        and cases.negative_label_permitted.eq(False).all(),
        "Scientific state remains unknown",
    )
    raw = (PROTOTYPE / "review_data.js").read_text(encoding="utf-8").strip()
    data = json.loads(raw.removeprefix("globalThis.RESEARCH_DATA=")[:-1])
    dictionary = {r["name"]: i for i, r in enumerate(data["dictionary"])}
    checked_pairs = checked_features = checked_ranks = 0
    for case in cases.to_dict("records"):
        records = [
            r
            for r in data["records"]
            if r["eligible"]
            and r["cohort"] == case["cohort"]
            and r["grid"] == case["grid_id"]
            and r["time"][:7] == case["source_prediction_timestamp_utc"][:7]
        ]
        records.sort(key=lambda r: r["time"])
        source = next(r for r in records if r["time"] == case["source_prediction_timestamp_utc"])
        check(source["flags"] == 511, "Stable nine-scenario source context")
        other_by_time = {r["time"]: r for r in records}
        table = comparisons.loc[comparisons.case_id.eq(case["case_id"])]
        for i, scenario in enumerate(data["scenarios"]):
            expected_times = {r["time"] for r in records if not r["flags"] & (1 << i)}
            rows = table.loc[table.scenario.eq(scenario)]
            check(
                len(rows) == len(expected_times)
                and set(rows.other_prediction_timestamp_utc) == expected_times,
                "All comparison days exactly once",
            )
            for row in rows.to_dict("records"):
                other = other_by_time[row["other_prediction_timestamp_utc"]]
                delta = (
                    datetime.fromisoformat(other["time"]) - datetime.fromisoformat(source["time"])
                ).days
                check(row["other_day_minus_source_day"] == delta, "Date direction")
                for j, variant in enumerate(("primary", "broad", "linear")):
                    a, b = source["scores"][i][j], other["scores"][i][j]
                    check(
                        row[variant + "_source_score"] == a
                        and row[variant + "_other_score"] == b
                        and row[variant + "_order_credit_twice"] == 2 * (a > b) + (a == b),
                        "Raw frozen score credit",
                    )
                checked_pairs += 1
        for variant in ("primary", "broad", "linear"):
            for name, selected in (
                ("near", table.loc[table.other_day_minus_source_day.abs().between(1, 3)]),
                ("before", table.loc[table.other_day_minus_source_day.lt(0)]),
                ("after", table.loc[table.other_day_minus_source_day.gt(0)]),
            ):
                value = ratio(selected[variant + "_order_credit_twice"].tolist())
                actual = case[variant + "_" + name + "_credit"]
                check(
                    (value is None and pd.isna(actual)) or value == actual, "Case temporal slices"
                )
        reference = [r for r in records if r["flags"] == 0]
        for row in feature.loc[feature.case_id.eq(case["case_id"])].to_dict("records"):
            i = dictionary[row["feature"]]
            values = [r["x"][i] for r in reference]
            source_value = source["x"][i]
            check(
                row["source_value"] == source_value
                and row["stable_unassigned_reference_days"] == len(values),
                "Feature reference identity",
            )
            check(row["reference_median"] == median(values), "Feature reference median")
            check(
                row["source_greater_reference_credit"]
                == ratio([2 * (source_value > v) + (source_value == v) for v in values]),
                "Feature relative context",
            )
            checked_features += 1
        for row in lines.loc[lines.case_id.eq(case["case_id"])].to_dict("records"):
            target = other_by_time[row["prediction_timestamp_utc"]]
            ranks = []
            for i in range(9):
                value = target["scores"][i][0]
                ranks.append(
                    Fraction(
                        2
                        + 2 * sum(r["scores"][i][0] > value for r in records)
                        + sum(r["scores"][i][0] == value for r in records)
                        - 1,
                        2,
                    )
                )
            check(
                row["primary_rank_mean"] == float(sum(ranks, Fraction()) / 9)
                and row["primary_rank_min"] == float(min(ranks))
                and row["primary_rank_max"] == float(max(ranks)),
                "Direct tie-aware monthly ranks",
            )
            checked_ranks += 1
    check(all(digest(p) == sha for p, sha in pins.items()), "Inputs preserved")
    out = (
        BASE
        / "frozen_rank_case_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    body = {
        "status": "independent_frozen_rank_case_audit_passed",
        "case_inventory_rows": len(inventory),
        "illustrative_cases": len(cases),
        "comparison_rows": checked_pairs,
        "feature_context_rows": checked_features,
        "monthly_rank_rows": checked_ranks,
        "new_model_or_prediction_calls": 0,
        "true_fire_error_validation": False,
        "source_readback_sha256": digest(SOURCE / "readback.json"),
        "auditor_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), body["status"], flush=True)


if __name__ == "__main__":
    main()
