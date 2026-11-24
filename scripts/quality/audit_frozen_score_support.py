"""Independently reconstruct fixed-score pairs with a relational self-join."""

import json
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCE = BASE / "frozen_score_support_diagnostic_v1/20261124T022210Z_e025acc0"
PROTOTYPE = BASE / "historical_research_prototype_v2/20261123T195053Z_aa61b349"
RUN = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"
VARIANTS = ["primary_weather_XGBoost", "broad_weather_XGBoost", "frozen_linear"]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def describe(frame):
    if frame.empty:
        return {"pairs": 0, "source_days": 0, "cells": 0, "cell_months": 0}

    def credit(f):
        return Fraction(int(f.numerator.sum()), 2 * int(f.pairs.sum()))

    def mean(values):
        return float(sum(values, Fraction()) / len(values))

    return {
        "pairs": int(frame.pairs.sum()),
        "wins": int(frame.wins.sum()),
        "ties": int(frame.ties.sum()),
        "source_days": len(frame),
        "cells": frame.grid_id.nunique(),
        "cell_months": len(frame[["grid_id", "calendar_month"]].drop_duplicates()),
        "pair_weighted_credit": float(credit(frame)),
        "equal_source_day_credit": mean(
            [Fraction(int(r.numerator), 2 * int(r.pairs)) for r in frame.itertuples()]
        ),
        "equal_cell_month_credit": mean(
            [credit(g) for _, g in frame.groupby(["grid_id", "calendar_month"])]
        ),
        "equal_cell_credit": mean([credit(g) for _, g in frame.groupby("grid_id")]),
        "largest_cell_pair_fraction": float(
            Fraction(int(frame.groupby("grid_id").pairs.sum().max()), int(frame.pairs.sum()))
        ),
    }


def compare(actual, expected):
    for key, value in expected.items():
        check(actual[key] == value, f"Independent mismatch: {key}")


def main():
    receipt = json.loads((SOURCE / "readback.json").read_bytes())
    pins = {ROOT / p: sha for p, sha in receipt["input_sha256"].items()}
    pins.update({SOURCE / p: sha for p, sha in receipt["artifact_sha256"].items()})
    pins[SOURCE / "readback.json"] = digest(SOURCE / "readback.json")
    check(all(digest(p) == sha for p, sha in pins.items()), "Input bytes")
    payload = (PROTOTYPE / "review_data.js").read_text(encoding="utf-8").strip()
    data = json.loads(payload.removeprefix("globalThis.RESEARCH_DATA=")[:-1])
    check(data["scientific_state"]["target"] is None, "Unknown true target")
    tables = {
        name: pd.read_csv(SOURCE / (name + ".csv"), float_precision="round_trip")
        for name in (
            "aggregation_summary",
            "contextual_summary",
            "source_day_order_credits",
            "omit_one_assessment_cell",
        )
    }
    reconstructed = []
    checked_summary = checked_context = checked_omission = 0
    for i, scenario in enumerate(data["scenarios"]):
        seen = set(pd.read_csv(RUN / scenario / "fit_layout.csv").grid_id)
        for cohort in ("four_province", "separate_Mersin"):
            records = pd.DataFrame(
                [
                    {
                        "grid_id": r["grid"],
                        "time": r["time"],
                        "month": r["time"][:7],
                        "source": bool(r["flags"] & (1 << i)),
                        "province": r["province"],
                        **{v: r["scores"][i][j] for j, v in enumerate(VARIANTS)},
                    }
                    for r in data["records"]
                    if r["cohort"] == cohort and r["eligible"]
                ]
            )
            check(records.time.str[:4].eq("2022").all(), "Only existing 2022")
            pairs = records.loc[records.source].merge(
                records.loc[~records.source], on=["grid_id", "month"], suffixes=("_s", "_u")
            )
            for variant in VARIANTS:
                difference = pairs[variant + "_s"] - pairs[variant + "_u"]
                pair_rows = pairs.assign(
                    wins=(difference > 0).astype(int), ties=(difference == 0).astype(int)
                )
                credits = (
                    pair_rows.groupby(["grid_id", "time_s"], as_index=False)
                    .agg(
                        pairs=("time_u", "size"),
                        wins=("wins", "sum"),
                        ties=("ties", "sum"),
                        calendar_month=("month", "first"),
                        province_area_intersections=("province_s", "first"),
                    )
                    .rename(columns={"time_s": "source_prediction_timestamp_utc"})
                )
                credits["numerator"] = 2 * credits.wins + credits.ties
                credits["cell_seen_in_fit"] = credits.grid_id.isin(seen)
                base = {"cohort": cohort, "scenario": scenario, "variant": variant}
                reconstructed.extend((base | r) for r in credits.to_dict("records"))

                def select(t, c=cohort, s=scenario, v=variant):
                    return t.loc[t.cohort.eq(c) & t.scenario.eq(s) & t.variant.eq(v)]

                compare(select(tables["aggregation_summary"]).iloc[0], describe(credits))
                checked_summary += 1
                for row in select(tables["contextual_summary"]).to_dict("records"):
                    name = row["slice"]
                    if name.startswith("province_"):
                        mask = credits.province_area_intersections.str.split("|").map(
                            lambda names, label=name[9:]: label in names
                        )
                    elif name.startswith("month_"):
                        mask = credits.calendar_month.eq(name[6:])
                    else:
                        check(name in ("cell_seen_in_fit", "cell_not_seen_in_fit"), "Known slice")
                        mask = credits.cell_seen_in_fit.eq(name == "cell_seen_in_fit")
                    expected = describe(credits.loc[mask])
                    compare(row, expected)
                    if not mask.any():
                        check(
                            pd.isna(row["pair_weighted_credit"]), "Absent support remains missing"
                        )
                    checked_context += 1
                baseline = Fraction(int(credits.numerator.sum()), 2 * int(credits.pairs.sum()))
                for row in select(tables["omit_one_assessment_cell"]).to_dict("records"):
                    remaining = credits.loc[credits.grid_id.ne(row["omitted_cell"])]
                    compare(
                        row,
                        {
                            "retained_pairs": int(remaining.pairs.sum()),
                            "retained_source_days": len(remaining),
                        },
                    )
                    if remaining.empty:
                        check(
                            pd.isna(row["credit_after_omitting_cell"]), "Missing omission support"
                        )
                    else:
                        ratio = Fraction(
                            int(remaining.numerator.sum()), 2 * int(remaining.pairs.sum())
                        )
                        compare(
                            row,
                            {
                                "credit_after_omitting_cell": float(ratio),
                                "difference_from_all_cells": float(ratio - baseline),
                            },
                        )
                    checked_omission += 1
    expected = pd.DataFrame(reconstructed).rename(columns={"numerator": "credit_twice"})
    actual = tables["source_day_order_credits"]
    keys = ["cohort", "scenario", "variant", "grid_id", "source_prediction_timestamp_utc"]
    check(not actual.duplicated(keys).any(), "Unique source-day variant keys")
    columns = expected.columns.tolist()
    pd.testing.assert_frame_equal(
        actual[columns].sort_values(keys).reset_index(drop=True),
        expected.sort_values(keys).reset_index(drop=True),
        check_dtype=False,
        check_exact=True,
    )
    for row in actual.itertuples():
        check(
            row.source_day_order_credit_not_fire_performance
            == float(Fraction(row.credit_twice, 2 * row.pairs)),
            "Source-day ratio",
        )
    check(all(digest(p) == sha for p, sha in pins.items()), "Unchanged inputs")
    out = (
        BASE
        / "frozen_score_support_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    body = {
        "status": "independent_relational_pair_audit_passed",
        "summary_rows": checked_summary,
        "context_rows": checked_context,
        "omission_rows": checked_omission,
        "source_day_variant_rows": len(actual),
        "model_calls": 0,
        "true_fire_validation": False,
        "final_merge": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "auditor_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), body["status"], flush=True)


if __name__ == "__main__":
    main()
