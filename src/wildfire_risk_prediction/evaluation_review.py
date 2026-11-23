"""Inspection-only support accounting across overlapping source-conditioned calendars."""

import numpy as np
import pandas as pd

from .feature_join import KEYS, require
from .ranking_queries import DYNAMIC_FEATURES


def checked_feature_union(frames):
    """Preserve shared values exactly; never average conflicting calendar copies."""
    combined = pd.concat(frames, ignore_index=True)
    require(list(combined.columns) == list(frames[0].columns), "Identical feature schemas")
    require(all(not x.duplicated(KEYS).any() for x in frames), "Unique keys in each source")
    names = [x for x in combined.columns if x not in KEYS]
    duplicates = combined.loc[combined.duplicated(KEYS, keep=False)]
    for _, group in duplicates.groupby(KEYS, sort=False):
        values = group[names].to_numpy(dtype=float)
        require(
            np.all((values == values[0]) | (np.isnan(values) & np.isnan(values[0]))),
            "Shared feature values identical, including missingness",
        )
    return combined.drop_duplicates(KEYS).sort_values(KEYS).reset_index(drop=True)


def rank_positions(metadata, scores):
    """Within-cell/month descriptive positions only; no percentage or risk band."""
    dates = pd.to_datetime(metadata.prediction_timestamp_utc, utc=True, format="ISO8601")
    require(
        dates.dt.year.eq(2022).all() and not metadata.duplicated(KEYS).any(),
        "Only existing unique 2022 inspection records",
    )
    require(
        metadata.target.isna().all()
        and metadata.accepted_L_membership.isna().all()
        and metadata.daily_observation_status.eq("unknown").all(),
        "Unknown fire targets",
    )
    values = np.asarray(scores, dtype=float)
    require(
        len(values) == len(metadata) and not np.isinf(values).any(),
        "Aligned finite-or-missing scores",
    )
    work = metadata[KEYS].copy()
    work["month"] = dates.dt.strftime("%Y-%m")
    work["score"] = values
    grouped = work.groupby(["grid_id", "month"], sort=False).score
    return pd.DataFrame(
        {
            "position_in_available_cell_month_days": grouped.rank(
                ascending=False, method="average"
            ),
            "available_days_in_cell_month": grouped.transform("count"),
        }
    )


def support_counts(metadata, source, complete, fit_layout):
    require(len(source) == len(complete) == len(metadata), "Aligned support arrays")
    require(
        np.asarray(source).dtype == np.asarray(complete).dtype == np.dtype(bool), "Boolean support"
    )
    require(
        fit_layout.prediction_timestamp_utc.str[:4].astype(int).between(2018, 2021).all(),
        "Only already fitted historical rows for support description",
    )
    work = metadata[KEYS].copy()
    work["source"] = source
    work["complete"] = complete
    work["month"] = work.prediction_timestamp_utc.str[:7]
    fit_cells = set(fit_layout.grid_id)
    fit_cell_months = set(
        zip(fit_layout.grid_id, fit_layout.prediction_timestamp_utc.str[5:7], strict=True)
    )
    cells = set(work.grid_id)
    supported = work.loc[work.complete]
    count = pairs = 0
    for _, group in supported.groupby(["grid_id", "month"]):
        s, u = int(group.source.sum()), int((~group.source).sum())
        count += s > 0 and u > 0
        pairs += s * u
    return {
        "records": len(work),
        "cells": len(cells),
        "complete_dynamic_records": len(supported),
        "missing_dynamic_records": len(work) - len(supported),
        "source_records": int(work.source.sum()),
        "complete_source_records": int(supported.source.sum()),
        "informative_cell_months": count,
        "possible_comparison_pairs": pairs,
        "assessment_cells_seen_in_fit": len(cells & fit_cells),
        "assessment_cells_not_seen_in_fit": len(cells - fit_cells),
        "complete_records_from_fit_cells": int(supported.grid_id.isin(fit_cells).sum()),
        "complete_records_from_unseen_cells": int((~supported.grid_id.isin(fit_cells)).sum()),
        "complete_records_with_same_cell_and_month_number_in_fit": sum(
            (g, t[5:7]) in fit_cell_months
            for g, t in supported[KEYS].itertuples(index=False, name=None)
        ),
    }


def missingness_table(features, cohort):
    require(not features.duplicated(KEYS).any(), "Unique missingness keys")
    rows = []
    for name in DYNAMIC_FEATURES:
        missing = ~np.isfinite(features[name].to_numpy(dtype=float))
        rows.append(
            {
                "cohort": cohort,
                "feature": name,
                "missing_records": int(missing.sum()),
                "records": len(features),
            }
        )
    return pd.DataFrame(rows)
