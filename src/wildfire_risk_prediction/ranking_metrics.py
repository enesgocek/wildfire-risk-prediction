"""Uncalibrated binary ranking arithmetic, separate from probability evaluation/admission."""

import numpy as np

from wildfire_risk_prediction.feature_join import require


def binary_rank_metrics(target, score, *, target_meaning):
    """Tie-grouped AP/PR/ROC on known synthetic Y or observed S, never admit real fire Y.

    Scores may be any finite real number. No score normalization, calibration,
    Brier/log-loss, target imputation, confidence interval or model fitting occurs.
    A future real-fire controller needs its own scientific admission protocol.
    """
    require(
        target_meaning in {"synthetic_Y", "observed_source_S"},
        "Explicit synthetic or auxiliary source semantics; real fire admission is separate",
    )
    y, scores = np.asarray(target), np.asarray(score)
    require(
        y.ndim == scores.ndim == 1
        and len(y) == len(scores)
        and len(y) > 0
        and y.dtype.kind in "biuf"
        and scores.dtype.kind in "iuf",
        "Aligned nonempty numeric labels and real ranking scores",
    )
    require(np.isfinite(y).all() and np.isin(y, [0, 1]).all(), "Known binary membership only")
    require(np.isfinite(scores).all(), "Finite scores; no silent dropping or filling")
    positives = int(np.count_nonzero(y))
    negatives = len(y) - positives
    result = {
        "target_meaning": target_meaning,
        "sample_count": len(y),
        "positive_memberships": positives,
        "negative_memberships": negatives,
        "average_precision": None,
        "pr_auc_trapezoid": None,
        "roc_auc": None,
        "status": "defined" if positives and negatives else "undefined_single_class",
        "score_is_probability": False,
        "probability_metrics_computed": False,
        "scientific_fire_labels_accepted": False,
    }
    if not (positives and negatives):
        return result
    # Reverse an ascending sort, avoiding overflow from negating extreme integer scores.
    order = np.argsort(scores, kind="stable")[::-1]
    ordered = scores[order]
    ends = np.r_[np.flatnonzero(ordered[:-1] != ordered[1:]), len(y) - 1]
    tp = np.cumsum(y[order], dtype=np.float64)[ends]
    fp = ends + 1 - tp
    recall = tp / positives
    precision = tp / (ends + 1)
    result["average_precision"] = float(np.sum(np.diff(np.r_[0.0, recall]) * precision))
    result["pr_auc_trapezoid"] = float(np.trapezoid(np.r_[1.0, precision], np.r_[0.0, recall]))
    result["roc_auc"] = float(np.trapezoid(np.r_[0.0, recall], np.r_[0.0, fp / negatives]))
    return result
