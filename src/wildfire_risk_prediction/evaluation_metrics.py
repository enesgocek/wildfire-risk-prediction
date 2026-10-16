"""Binary evaluation arithmetic only; calling it never admits scientific labels."""

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import require, utc_times


def binary_inputs(target, probability):
    y, p = np.asarray(target), np.asarray(probability)
    require(
        y.ndim == p.ndim == 1
        and len(y) == len(p)
        and len(y) > 0
        and y.dtype.kind in "biuf"
        and p.dtype.kind in "biuf",
        "Aligned nonempty numeric binary targets and probabilities; unknowns cannot be scored",
    )
    y, p = y.astype(np.float64), p.astype(np.float64)
    require(np.isfinite(y).all() and np.isin(y, [0.0, 1.0]).all(), "Known binary targets only")
    require(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all(), "Finite probabilities in [0,1]")
    return y, p


def binary_metrics(target, probability):
    """Unweighted cell-day arithmetic. AP groups equal scores before recall changes."""
    y, p = binary_inputs(target, probability)
    positive, negative = int(y.sum()), int(len(y) - y.sum())
    epsilon = np.finfo(np.float64).eps
    clipped = np.clip(p, epsilon, 1 - epsilon)
    result = {
        "sample_count": len(y),
        "positive_count": positive,
        "negative_count": negative,
        "prevalence": float(y.mean()),
        "average_precision": None,
        "pr_auc_trapezoid": None,
        "roc_auc": None,
        "brier_binary": float(np.mean((p - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(clipped) + (1 - y) * np.log1p(-clipped))),
        "log_loss_clipped_count": int(np.count_nonzero(p != clipped)),
        "log_loss_epsilon": float(epsilon),
        "ranking_metric_status": "defined" if positive and negative else "undefined_single_class",
    }
    if positive and negative:
        order = np.argsort(-p, kind="stable")
        ends = np.r_[np.flatnonzero(np.diff(p[order]) != 0), len(y) - 1]
        tp = np.cumsum(y[order])[ends]
        fp = ends + 1 - tp
        recall, precision = tp / positive, tp / (ends + 1)
        result["average_precision"] = float(np.sum(np.diff(np.r_[0.0, recall]) * precision))
        result["pr_auc_trapezoid"] = float(np.trapezoid(np.r_[1.0, precision], np.r_[0.0, recall]))
        result["roc_auc"] = float(np.trapezoid(np.r_[0.0, recall], np.r_[0.0, fp / negative]))
    return result


def calibration_bins(target, probability, *, bin_count):
    """Fixed equal-width [left,right) bins, last includes 1; no calibrator is fitted."""
    require(type(bin_count) is int and 1 <= bin_count <= 1000, "Explicit bounded bin count")
    y, p = binary_inputs(target, probability)
    edges = np.arange(bin_count + 1, dtype=np.float64) / bin_count
    indices = np.minimum(np.searchsorted(edges, p, side="right") - 1, bin_count - 1)
    rows = []
    for i in range(bin_count):
        chosen = indices == i
        rows.append(
            {
                "bin_index": i,
                "left": float(edges[i]),
                "right": float(edges[i + 1]),
                "count": int(chosen.sum()),
                "mean_probability": float(p[chosen].mean()) if chosen.any() else None,
                "observed_fraction": float(y[chosen].mean()) if chosen.any() else None,
            }
        )
    return pd.DataFrame(rows)


def compare_training_predictions(left, right):
    """Align the same fully labelled training cohort before comparing probability scores."""
    required = {"grid_id", "prediction_timestamp_utc", "target", "probability"}
    aligned = []
    for frame in (left, right):
        require(frame.columns.is_unique and required <= set(frame), "Paired prediction schema")
        work = frame[list(required)].copy().reset_index(drop=True)
        require(
            work.grid_id.map(lambda x: isinstance(x, str) and bool(x.strip())).all(),
            "Paired grid identities",
        )
        times = utc_times(work.prediction_timestamp_utc)
        require(
            times.notna().all()
            and times.eq(times.dt.normalize()).all()
            and times.dt.year.between(2018, 2023).all(),
            "Training-only paired UTC issues",
        )
        work["prediction_timestamp_utc"] = times
        work = work.set_index(["grid_id", "prediction_timestamp_utc"])
        require(work.index.is_unique, "Unique paired grid/time keys")
        binary_inputs(work.target.to_numpy(), work.probability.to_numpy())
        aligned.append(work.sort_index())
    a, b = aligned
    require(a.index.equals(b.index), "Same comparison cohort required; no inner join or row loss")
    require(np.array_equal(a.target.to_numpy(), b.target.to_numpy()), "Same comparison targets")
    first = binary_metrics(a.target.to_numpy(), a.probability.to_numpy())
    second = binary_metrics(b.target.to_numpy(), b.probability.to_numpy())
    names = ("average_precision", "pr_auc_trapezoid", "brier_binary", "log_loss", "roc_auc")
    return {
        "sample_count": len(a),
        "left_metrics": first,
        "right_metrics": second,
        "right_minus_left": {
            k: second[k] - first[k] if first[k] is not None else None for k in names
        },
        "confidence_intervals": None,
        "labels_accepted": False,
    }
