"""Descriptive support sensitivity for fixed source-context ordering; no estimator."""

from fractions import Fraction

import numpy as np
import pandas as pd

from .feature_join import KEYS, require


def validate_records(records, score_columns):
    require(not records.empty and not records.duplicated(KEYS).any(), "Unique diagnostic keys")
    dates = pd.to_datetime(records.prediction_timestamp_utc, utc=True, format="ISO8601")
    require(
        dates.dt.year.eq(2022).all() and dates.eq(dates.dt.normalize()).all(),
        "Only existing 2022 UTC daily rows",
    )
    require(
        records.target.isna().all()
        and records.accepted_L_membership.isna().all()
        and records.daily_observation_status.eq("unknown").all(),
        "Unknown scientific targets",
    )
    require(
        records.source_context.dtype == records.primary_eligible.dtype == np.dtype(bool),
        "Explicit source-context and support flags",
    )
    require(
        np.isfinite(
            records.loc[records.primary_eligible, score_columns].to_numpy(dtype=float)
        ).all(),
        "All variants finite on identical primary support",
    )


def source_day_credits(records, variants):
    validate_records(records, list(variants.values()))
    work = records.loc[records.primary_eligible].copy()
    work["calendar_month"] = work.prediction_timestamp_utc.str[:7]
    rows = []
    for (grid, month), group in work.groupby(["grid_id", "calendar_month"], sort=True):
        other = group.loc[~group.source_context]
        if other.empty:
            continue
        for row in group.loc[group.source_context].itertuples(index=False):
            for variant, column in variants.items():
                diff = getattr(row, column) - other[column].to_numpy()
                wins, ties = int((diff > 0).sum()), int((diff == 0).sum())
                rows.append(
                    {
                        "variant": variant,
                        "grid_id": grid,
                        "source_prediction_timestamp_utc": row.prediction_timestamp_utc,
                        "calendar_month": month,
                        "province_area_intersections": row.province_area_intersections,
                        "cell_seen_in_fit": bool(row.cell_seen_in_fit),
                        "pairs": len(other),
                        "wins": wins,
                        "ties": ties,
                        "credit_twice": 2 * wins + ties,
                        "source_day_order_credit_not_fire_performance": float(
                            Fraction(2 * wins + ties, 2 * len(other))
                        ),
                    }
                )
    return pd.DataFrame(rows)


def exact_ratio(credits):
    pairs = int(credits.pairs.sum())
    return Fraction(int(credits.credit_twice.sum()), 2 * pairs) if pairs else None


def average_ratios(groups):
    values = [exact_ratio(group) for _, group in groups]
    values = [v for v in values if v is not None]
    return float(sum(values, Fraction(0)) / len(values)) if values else None


def summarize(credits):
    require(not credits.empty and credits.variant.nunique() == 1, "One supported fixed variant")
    require(
        not credits.duplicated(["grid_id", "source_prediction_timestamp_utc"]).any(),
        "Each source-day counts once within a variant",
    )
    pair_count = int(credits.pairs.sum())
    return {
        "pairs": pair_count,
        "wins": int(credits.wins.sum()),
        "ties": int(credits.ties.sum()),
        "source_days": len(credits),
        "cells": credits.grid_id.nunique(),
        "cell_months": len(credits[["grid_id", "calendar_month"]].drop_duplicates()),
        "pair_weighted_credit": float(exact_ratio(credits)),
        "equal_source_day_credit": float(
            sum(
                (
                    Fraction(int(r.credit_twice), 2 * int(r.pairs))
                    for r in credits.itertuples(index=False)
                ),
                Fraction(0),
            )
            / len(credits)
        ),
        "equal_cell_month_credit": average_ratios(
            credits.groupby(["grid_id", "calendar_month"], sort=True)
        ),
        "equal_cell_credit": average_ratios(credits.groupby("grid_id", sort=True)),
        "largest_cell_pair_fraction": float(
            Fraction(int(credits.groupby("grid_id").pairs.sum().max()), pair_count)
        ),
    }


def contextual_slices(credits):
    masks = {}
    for name in sorted(set("|".join(credits.province_area_intersections).split("|"))):
        masks["province_" + name] = credits.province_area_intersections.str.split("|").map(
            lambda v, n=name: n in v
        )
    for month in sorted(credits.calendar_month.unique()):
        masks["month_" + month] = credits.calendar_month.eq(month)
    masks["cell_seen_in_fit"] = credits.cell_seen_in_fit
    masks["cell_not_seen_in_fit"] = ~credits.cell_seen_in_fit
    return masks


def leave_one_cell_out(credits):
    baseline = exact_ratio(credits)
    require(baseline is not None, "Supported baseline")
    rows = []
    for grid in sorted(credits.grid_id.unique()):
        retained = credits.loc[credits.grid_id.ne(grid)]
        ratio = exact_ratio(retained)
        rows.append(
            {
                "omitted_cell": grid,
                "retained_pairs": int(retained.pairs.sum()),
                "retained_source_days": len(retained),
                "credit_after_omitting_cell": float(ratio) if ratio is not None else None,
                "difference_from_all_cells": float(ratio - baseline) if ratio is not None else None,
            }
        )
    return pd.DataFrame(rows)
