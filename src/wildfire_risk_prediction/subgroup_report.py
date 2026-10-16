"""Training-only subgroup denominators and strictly synthetic score rehearsal."""

import itertools

import numpy as np
import pandas as pd

from wildfire_risk_prediction.evaluation_metrics import binary_metrics
from wildfire_risk_prediction.feature_join import boolean, require, utc_times

PROVINCES = ("Antalya", "Mu\u011fla", "\u0130zmir", "Mersin")
SEASONS = ("winter", "spring", "summer", "autumn")
SUPPORT = ("missing", "zero", "positive")
METRICS = ("average_precision", "pr_auc_trapezoid", "brier_binary", "log_loss", "roc_auc")


def _optional_numbers(values, name, *, binary=False):
    present = values.dropna()
    require(
        present.map(
            lambda x: (
                isinstance(x, (int, float, np.integer, np.floating))
                and not isinstance(x, (bool, np.bool_))
                and np.isfinite(x)
            )
        ).all(),
        f"Numeric finite or missing {name}; no string coercion",
    )
    result = values.to_numpy(dtype=np.float64, na_value=np.nan)
    require(
        np.isin(result[~np.isnan(result)], [0, 1]).all()
        if binary
        else ((result[~np.isnan(result)] >= 0) & (result[~np.isnan(result)] <= 1)).all(),
        f"Valid {name} range",
    )
    return result


def grouped_report(frame, *, scope):
    """Emit empty strata too. Partial labelled/scored groups never receive metrics."""
    require(scope in ("unlabelled_method_pilot", "synthetic_scores"), "Explicit supported scope")
    required = {
        "grid_id",
        "prediction_timestamp_utc",
        "primary_province",
        "calendar_season",
        "nominal_land_fraction",
        "target",
        "daily_observation_status",
        "negative_label_permitted",
        "labels_created",
        "accepted_label_rule",
    }
    require(frame.columns.is_unique and required <= set(frame) and len(frame) > 0, "Report schema")
    work = frame.copy(deep=True).reset_index(drop=True)
    require(
        work.grid_id.map(lambda x: isinstance(x, str) and bool(x.strip())).all(),
        "Complete string grid identities",
    )
    times = utc_times(work.prediction_timestamp_utc)
    require(
        times.notna().all()
        and times.eq(times.dt.normalize()).all()
        and times.dt.year.between(2018, 2023).all(),
        "Training-only daily UTC subgroup report",
    )
    require(pd.MultiIndex.from_arrays([work.grid_id, times]).is_unique, "Unique canonical grid/day")
    require(work.primary_province.isin(PROVINCES).all(), "Known primary province assignment")
    season = times.dt.month.map(
        {
            12: "winter",
            1: "winter",
            2: "winter",
            3: "spring",
            4: "spring",
            5: "spring",
            6: "summer",
            7: "summer",
            8: "summer",
            9: "autumn",
            10: "autumn",
            11: "autumn",
        }
    )
    require(work.calendar_season.eq(season).all(), "Season must agree with UTC issue date")
    require(work.daily_observation_status.eq("unknown").all(), "Observation acceptance unchanged")
    for name in ("negative_label_permitted", "labels_created", "accepted_label_rule"):
        boolean(work[name], name)
        require(not work[name].any(), "Label gate closed in this preparation")
    support = work.nominal_land_fraction
    require(
        support.dropna()
        .map(
            lambda x: (
                isinstance(x, (int, float, np.integer, np.floating))
                and not isinstance(x, (bool, np.bool_))
                and np.isfinite(x)
                and 0 <= x <= 1 + 1e-8
            )
        )
        .all(),
        "Nominal support fraction or missing, with recorded 1e-8 numerical tolerance",
    )
    work["support_status"] = np.where(
        support.isna(), "missing", np.where(support.eq(0), "zero", "positive")
    )
    y = _optional_numbers(work.target, "target", binary=True)
    probabilities = (
        work.probability if "probability" in work else pd.Series(np.nan, index=work.index)
    )
    p = _optional_numbers(probabilities, "probability")
    if scope == "unlabelled_method_pilot":
        require(np.isnan(y).all() and np.isnan(p).all(), "No real labels or predictions admitted")
    else:
        require(work.grid_id.str.startswith("synthetic_").all(), "Explicit synthetic grids only")
    work["known"], work["predicted"] = ~np.isnan(y), ~np.isnan(p)
    work["y"], work["p"] = y, p
    work["issue"] = times
    strata = [("all", "all", pd.Series(True, index=work.index))]
    for dimension, levels in (
        ("primary_province", PROVINCES),
        ("calendar_season", SEASONS),
        ("support_status", SUPPORT),
    ):
        strata.extend((dimension, level, work[dimension].eq(level)) for level in levels)
    strata.extend(
        (
            "province_season",
            province + "|" + season_name,
            work.primary_province.eq(province) & work.calendar_season.eq(season_name),
        )
        for province, season_name in itertools.product(PROVINCES, SEASONS)
    )
    rows = []
    for dimension, level, chosen in strata:
        group = work.loc[chosen]
        n, known, predicted = len(group), int(group.known.sum()), int(group.predicted.sum())
        paired = int((group.known & group.predicted).sum())
        if not n:
            status = "empty_group"
        elif scope == "unlabelled_method_pilot":
            status = "not_run_real_preparation"
        elif known != n or predicted != n:
            status = "incomplete_targets_or_predictions_no_subset_scoring"
        else:
            status = "computed_synthetic_only"
        metrics = {name: None for name in METRICS}
        ranking_status = "not_computed"
        if status == "computed_synthetic_only":
            result = binary_metrics(group.y.to_numpy(), group.p.to_numpy())
            metrics = {name: result[name] for name in METRICS}
            ranking_status = result["ranking_metric_status"]
        rows.append(
            {
                "scope": scope,
                "dimension": dimension,
                "stratum": level,
                "unit_count": n,
                "distinct_grid_count": int(group.grid_id.nunique()),
                "distinct_issue_dates": int(group.issue.nunique()),
                "known_target_count": known,
                "positive_count": int(group.y.eq(1).sum()),
                "verified_negative_count": int(group.y.eq(0).sum()),
                "unknown_target_count": n - known,
                "prediction_present_count": predicted,
                "prediction_missing_count": n - predicted,
                "paired_known_prediction_count": paired,
                "known_without_prediction_count": known - paired,
                "unknown_with_prediction_count": predicted - paired,
                "unknown_without_prediction_count": n - known - predicted + paired,
                "known_target_positive_fraction": float(group.y.sum() / known) if known else None,
                "nominal_support_missing_count": int(group.support_status.eq("missing").sum()),
                "nominal_support_zero_count": int(group.support_status.eq("zero").sum()),
                "nominal_support_positive_count": int(group.support_status.eq("positive").sum()),
                "nominal_support_above_one_within_tolerance_count": int(
                    group.nominal_land_fraction.gt(1).sum()
                ),
                "observation_unknown_count": n,
                "metric_status": status,
                "ranking_metric_status": ranking_status,
                **metrics,
                "independent_event_count": None,
                "confidence_intervals": None,
                "statistical_support_status": "not_assessed",
                "labels_accepted": False,
                "model_ready": False,
            }
        )
    result = pd.DataFrame(rows)
    for _, marginal in result.groupby("dimension"):
        require(int(marginal.unit_count.sum()) == len(work), "Marginal unit conservation")
        require(
            int(marginal.known_target_count.sum()) == int(work.known.sum()),
            "Marginal target conservation",
        )
    return result
