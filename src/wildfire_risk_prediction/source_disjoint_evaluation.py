"""Frozen-score comparisons with unchanged original unassigned control days."""

from fractions import Fraction

import numpy as np
import pandas as pd

from .feature_join import KEYS, require
from .source_disjoint_plan import group_mask


def comparison_indices(metadata, anchors, source_group):
    require(not metadata.duplicated(KEYS).any(), "Unique existing score calendar keys")
    dates = pd.to_datetime(metadata.prediction_timestamp_utc, utc=True, format="ISO8601")
    require(
        dates.dt.year.eq(2022).all() and dates.eq(dates.dt.normalize()).all(),
        "Existing 2022 UTC daily calendar only",
    )
    require(
        metadata.target.isna().all()
        and metadata.accepted_L_membership.isna().all()
        and metadata.daily_observation_status.eq("unknown").all(),
        "Unknown scientific targets",
    )
    work = metadata[KEYS].copy()
    work["calendar_row"] = np.arange(len(work))
    work["month"] = work.prediction_timestamp_utc.str[:7]
    key_values = pd.MultiIndex.from_frame(work[KEYS])
    all_source_keys = pd.MultiIndex.from_frame(anchors[KEYS])
    selected_source_keys = pd.MultiIndex.from_frame(
        anchors.loc[group_mask(anchors, source_group), KEYS]
    )
    eligible = metadata.primary_weather_and_dynamic_15_eligible.to_numpy()
    require(eligible.dtype == np.dtype(bool), "Frozen boolean primary eligibility")
    # All original source days remain excluded from controls, including omitted sources.
    sources = work.loc[eligible & key_values.isin(selected_source_keys)]
    controls = work.loc[eligible & ~key_values.isin(all_source_keys)]
    pairs = sources.merge(controls, on=["grid_id", "month"], suffixes=("_source", "_other"))
    pairs["other_day_minus_source_day"] = (
        pd.to_datetime(pairs.prediction_timestamp_utc_other, utc=True)
        - pd.to_datetime(pairs.prediction_timestamp_utc_source, utc=True)
    ).dt.days
    require(pairs.other_day_minus_source_day.ne(0).all(), "Different comparison days")
    return pairs


def slice_masks(pairs):
    delta = pairs.other_day_minus_source_day
    return {
        "all_same_grid_month": pd.Series(True, index=pairs.index),
        "gap_1_to_3_days": delta.abs().between(1, 3),
        "gap_4_to_30_days": delta.abs().between(4, 30),
        "other_day_before_source_day": delta.lt(0),
        "other_day_after_source_day": delta.gt(0),
    }


def ordering_metric(source_scores, other_scores):
    source, other = np.asarray(source_scores, dtype=float), np.asarray(other_scores, dtype=float)
    require(
        source.shape == other.shape
        and source.ndim == 1
        and np.isfinite(source).all()
        and np.isfinite(other).all(),
        "Finite aligned frozen score pairs",
    )
    count = len(source)
    wins, ties = int((source > other).sum()), int((source == other).sum())
    return {
        "pairs": count,
        "wins": wins,
        "ties": ties,
        "auxiliary_pair_AUC": float(Fraction(2 * wins + ties, 2 * count)) if count else None,
    }
