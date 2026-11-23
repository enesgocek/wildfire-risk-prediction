"""Bounded source-context ranking inputs; never assign scientific fire targets."""

import numpy as np
import pandas as pd

from .feature_join import KEYS, require
from .ranking_queries import DYNAMIC_FEATURES, query_inventory


def validate_execution(policy, proposal):
    require(
        policy["decision_source"] == "user_continue_after_specific_A_XGBoost_ranking_proposal"
        and policy["new_models_authorized"] == 9
        and policy["fit_years"] == [2018, 2019, 2020, 2021]
        and policy["exploratory_assessment_year"] == 2022
        and policy["local_time_limit_seconds"] == 900
        and policy["dependency"] == "xgboost==3.4.1",
        "Bounded execution following concrete A proposal",
    )
    require(
        all(
            policy[k] is False
            for k in (
                "scientific_values_2023_2024_2025_read_permitted",
                "hyperparameter_search_permitted",
                "original_U_or_weights_changed",
                "true_Y_or_accepted_L_assignment_authorized",
                "negative_label_permitted",
                "fire_probabilities_or_validated_risk_colors_authorized",
                "cloud_permitted",
                "final_merge_permitted",
            )
        )
        and policy["daily_observation_status"] == "unknown"
        and proposal["objective"] == "rank:pairwise"
        and proposal["new_training_authorized"] is False,
        "Historical proposal unchanged; execution grants no scientific label acceptance",
    )


def training_layout(meta, source, complete):
    """Return original row indices and sorted qids for complete mixed fit queries."""
    inventory = query_inventory(meta, source, complete)
    eligible = inventory.loc[
        inventory.pilot_role.eq("proposed_fit_2018_2021") & inventory.informative_for_ordering,
        ["grid_id", "calendar_month"],
    ]
    work = meta[KEYS].copy()
    work["calendar_month"] = work.prediction_timestamp_utc.str[:7]
    work["calendar_row"] = np.arange(len(meta))
    work["relevance_source_context_not_Y"] = source
    work = work.loc[complete].merge(eligible, on=["grid_id", "calendar_month"], how="inner")
    work = work.sort_values(["grid_id", "calendar_month", "prediction_timestamp_utc"])
    work["qid"] = pd.factorize(pd.MultiIndex.from_frame(work[["grid_id", "calendar_month"]]))[0]
    require(len(work) > 0 and work.qid.is_monotonic_increasing, "Sorted informative fit queries")
    require(work.prediction_timestamp_utc.str[:4].astype(int).le(2021).all(), "Fit only 2018-2021")
    return work.reset_index(drop=True)


def matched_pairs(meta, source, complete, role):
    query_inventory(meta, source, complete)
    frame = meta.loc[complete & meta.review_temporal_role.eq(role), KEYS].copy()
    frame["source"] = np.asarray(source)[frame.index]
    frame["month"] = frame.prediction_timestamp_utc.str[:7]
    a, b = [], []
    for _, group in frame.groupby(["grid_id", "month"], sort=True):
        s, u = group.index[group.source].to_numpy(), group.index[~group.source].to_numpy()
        a.extend(np.repeat(s, len(u)))
        b.extend(np.tile(u, len(s)))
    require(len(a) > 0, "Matched source-context pairs exist")
    return pd.DataFrame({"source_calendar_row": a, "other_calendar_row": b}, dtype="int64")


def finite_features(x):
    require(not x.duplicated(KEYS).any(), "Unique feature keys")
    return np.isfinite(x[DYNAMIC_FEATURES].to_numpy(dtype=float)).all(axis=1)


def evaluate_slices(meta, pair_frame, scores):
    """Source ordering credit, with temporal direction and gap checks; not fire AUC."""
    a, b = pair_frame.to_numpy(dtype=int).T
    dates = pd.to_datetime(meta.prediction_timestamp_utc, utc=True, format="ISO8601")
    delta = dates.iloc[a].reset_index(drop=True) - dates.iloc[b].reset_index(drop=True)
    delta = delta.dt.total_seconds().to_numpy() / 86400
    masks = {
        "all_same_grid_month": np.ones(len(a), dtype=bool),
        "gap_1_to_3_days": (abs(delta) >= 1) & (abs(delta) <= 3),
        "gap_4_to_30_days": abs(delta) >= 4,
        "other_day_before_source_day": delta > 0,
        "other_day_after_source_day": delta < 0,
    }
    if "province_area_intersections" in meta:
        for province in ("Antalya", "Izmir", "Mersin", "Mugla"):
            masks["province_" + province] = (
                meta.province_area_intersections.fillna("")
                .str.split("|")
                .map(lambda v, p=province: p in v)
                .to_numpy()[a]
            )
    for grid in sorted(set(meta.grid_id.iloc[a])):
        masks["cell_" + grid] = meta.grid_id.to_numpy()[a] == grid
    diff = np.asarray(scores)[a] - np.asarray(scores)[b]
    require(np.isfinite(diff).all(), "Scores finite on identical comparison support")
    rows = []
    for name, mask in masks.items():
        n, wins, ties = (
            int(mask.sum()),
            int(((diff > 0) & mask).sum()),
            int(((diff == 0) & mask).sum()),
        )
        rows.append(
            {
                "slice": name,
                "pairs": n,
                "wins": wins,
                "ties": ties,
                "auxiliary_pair_AUC": (wins + ties / 2) / n if n else None,
            }
        )
    return rows
