"""Outcome-independent sampling of source-table rows, never of verified physical fires."""

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import require


def sample_source_keys(frame, *, per_year, seed):
    """Accept only identifiers/year; reject outcome, cover, location and quality inputs."""
    require(set(frame.columns) == {"archive_row", "year"}, "Only identifier/year selection inputs")
    require(type(per_year) is int and per_year > 0, "Positive integer sample size per year")
    require(type(seed) is int and seed >= 0, "Nonnegative integer seed")
    require(
        not frame.empty and frame.archive_row.map(lambda v: isinstance(v, str) and bool(v)).all(),
        "Nonempty source identifiers",
    )
    require(frame.archive_row.is_unique, "Source row identifiers must be unique")
    data = frame.copy()
    years = pd.to_numeric(data.year, errors="raise")
    require(years.notna().all() and years.mod(1).eq(0).all(), "Integer source years")
    data["year"] = years.astype(int)
    require(set(data.year) == set(range(2018, 2023)), "Exactly fit-role source years 2018–2022")
    rng = np.random.Generator(np.random.PCG64(seed))
    selected = []
    for _year, group in data.sort_values(["year", "archive_row"]).groupby("year", sort=True):
        group = group.reset_index(drop=True)
        require(len(group) >= per_year, "Not enough source rows in a year; do not replace")
        positions = np.sort(rng.choice(len(group), size=per_year, replace=False))
        part = group.iloc[positions].copy()
        part["source_rows_in_year"] = len(group)
        part["inclusion_probability_within_source_year"] = per_year / len(group)
        part["review_role"] = "source_sampling_review_only_not_L"
        part["target"] = np.nan
        selected.append(part)
    result = pd.concat(selected, ignore_index=True)
    require(
        len(result) == 5 * per_year and result.archive_row.is_unique, "Unique stratified sample"
    )
    return result
