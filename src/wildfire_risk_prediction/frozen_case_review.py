"""Posthoc illustrative context of fixed source-day rankings; never fire errors."""

from fractions import Fraction

import numpy as np
import pandas as pd

from .feature_join import require

CASE_KEYS = ["cohort", "grid_id", "source_prediction_timestamp_utc"]


def inventory(credits, scenario_count):
    primary = credits.loc[credits.variant.eq("primary_weather_XGBoost")].copy()
    require(not primary.duplicated(CASE_KEYS + ["scenario"]).any(), "Unique source-day/scenario")
    require(primary.pairs.gt(0).all(), "Supported source-day comparisons")
    dates = pd.to_datetime(primary.source_prediction_timestamp_utc, utc=True)
    require(dates.dt.year.eq(2022).all(), "Only existing 2022 case scores")
    rows = []
    for keys, group in primary.groupby(CASE_KEYS, sort=True):
        ratios = [Fraction(int(r.credit_twice), 2 * int(r.pairs)) for r in group.itertuples()]
        require(all(Fraction(0) <= v <= Fraction(1) for v in ratios), "Order credit bounds")
        rows.append(
            dict(zip(CASE_KEYS, keys, strict=True))
            | {
                "scenario_count": len(group),
                "all_nine_scenario_support": len(group) == scenario_count,
                "primary_credit_mean": float(sum(ratios, Fraction()) / len(ratios)),
                "primary_credit_min": float(min(ratios)),
                "primary_credit_max": float(max(ratios)),
                "comparator_count_min": int(group.pairs.min()),
                "comparator_count_max": int(group.pairs.max()),
                "province_area_intersections": group.province_area_intersections.iloc[0],
            }
        )
    return pd.DataFrame(rows)


def select_examples(cases):
    rows = []
    for cohort, group in cases.loc[cases.all_nine_scenario_support].groupby("cohort", sort=True):
        ordered = group.sort_values(
            ["primary_credit_mean", "grid_id", "source_prediction_timestamp_utc"],
            kind="stable",
        ).reset_index(drop=True)
        require(len(ordered) >= 6, "Six distinct illustrative cases per cohort")
        indices = [0, 1, len(ordered) - 2, len(ordered) - 1]
        remaining = [i for i in range(len(ordered)) if i not in indices]
        central = sorted(remaining, key=lambda i: (abs(2 * i - (len(ordered) - 1)), i))[:2]
        selections = [(i, "low_order") for i in indices[:2]]
        selections += [(i, "central_order") for i in sorted(central)]
        selections += [(i, "high_order") for i in indices[2:]]
        for number, (i, tier) in enumerate(selections, 1):
            rows.append(
                ordered.iloc[i].to_dict()
                | {
                    "case_id": f"{cohort}_{number:02d}",
                    "illustrative_tier": tier,
                    "order_position_in_all_nine_pool": i + 1,
                    "all_nine_pool_size": len(ordered),
                }
            )
    return pd.DataFrame(rows)


def month_context(payload, case):
    month = case["source_prediction_timestamp_utc"][:7]
    rows = sorted(
        [
            r
            for r in payload["records"]
            if r["cohort"] == case["cohort"]
            and r["grid"] == case["grid_id"]
            and r["time"][:7] == month
            and r["eligible"]
        ],
        key=lambda r: r["time"],
    )
    source = [r for r in rows if r["time"] == case["source_prediction_timestamp_utc"]]
    require(
        len(source) == 1 and source[0]["flags"] == (1 << len(payload["scenarios"])) - 1,
        "Stable source context in all scenarios",
    )
    require(all(r["time"].startswith("2022-") for r in rows), "Only existing 2022 context")
    return rows, source[0]


def timeline(rows, scenario_count):
    values = np.array([[r["scores"][i][0] for i in range(scenario_count)] for r in rows])
    require(np.isfinite(values).all(), "Finite frozen primary scores")
    ranks = pd.DataFrame(values).rank(axis=0, ascending=False, method="average")
    result = []
    for i, row in enumerate(rows):
        result.append(
            {
                "prediction_timestamp_utc": row["time"],
                "source_context_scenarios": row["flags"].bit_count(),
                "eligible_days_in_month": len(rows),
                "primary_rank_mean": float(ranks.iloc[i].mean()),
                "primary_rank_min": float(ranks.iloc[i].min()),
                "primary_rank_max": float(ranks.iloc[i].max()),
            }
        )
    return pd.DataFrame(result)


def feature_context(payload, rows, source, feature_names):
    dictionary = {entry["name"]: (i, entry) for i, entry in enumerate(payload["dictionary"])}
    reference = [r for r in rows if r["flags"] == 0]
    result = []
    for name in feature_names:
        index, entry = dictionary[name]
        value = source["x"][index]
        values = np.array([r["x"][index] for r in reference], dtype=float)
        require(np.isfinite(value) and np.isfinite(values).all(), "Complete dynamic context")
        ratio = (
            Fraction(int(2 * (values < value).sum() + (values == value).sum()), 2 * len(values))
            if len(values)
            else None
        )
        result.append(
            {
                "feature": name,
                "unit": entry["unit"],
                "source_value": value,
                "stable_unassigned_reference_days": len(values),
                "reference_median": float(np.median(values)) if len(values) else None,
                "source_greater_reference_credit": float(ratio) if ratio is not None else None,
            }
        )
    return pd.DataFrame(result)
