from fractions import Fraction
from itertools import product

import numpy as np
import pytest

from wildfire_risk_prediction.ranking_metrics import binary_rank_metrics


def test_uncalibrated_scores_have_rank_metrics_without_probability_metrics():
    y = [1, 0, 1, 0]
    result = binary_rank_metrics(y, [-2.0, -3.0, 90.0, -4.0], target_meaning="synthetic_Y")
    assert result["average_precision"] == result["roc_auc"] == 1
    assert result["score_is_probability"] is False
    assert not any(k in result for k in ("brier_binary", "log_loss", "prevalence"))
    assert result["scientific_fire_labels_accepted"] is False


def test_ties_are_grouped_and_do_not_depend_on_order_within_group():
    reference = binary_rank_metrics(
        [1, 0, 1, 0], [4, 4, -2, -2], target_meaning="observed_source_S"
    )
    assert reference["average_precision"] == 0.5
    assert reference["pr_auc_trapezoid"] == 0.625
    assert reference["roc_auc"] == 0.5
    result = binary_rank_metrics([0, 1, 0, 1], [4, 4, -2, -2], target_meaning="observed_source_S")
    assert result == reference


def test_exact_small_binary_cases_match_independent_pair_and_threshold_arithmetic():
    # Exhaustive 14 mixed labelings x 81 three-level score vectors.
    for target in product((0, 1), repeat=4):
        if sum(target) in (0, 4):
            continue
        for scores in product((-9, 0, 12), repeat=4):
            result = binary_rank_metrics(target, scores, target_meaning="synthetic_Y")
            positives = [s for y, s in zip(target, scores, strict=True) if y]
            negatives = [s for y, s in zip(target, scores, strict=True) if not y]
            auc = sum(
                Fraction(1) if p > n else Fraction(1, 2) if p == n else Fraction(0)
                for p in positives
                for n in negatives
            ) / (len(positives) * len(negatives))
            ap = Fraction(0)
            for threshold in sorted(set(scores), reverse=True):
                new_tp = sum(y and s == threshold for y, s in zip(target, scores, strict=True))
                tp = sum(y and s >= threshold for y, s in zip(target, scores, strict=True))
                selected = sum(s >= threshold for s in scores)
                ap += Fraction(new_tp, len(positives)) * Fraction(tp, selected)
            assert result["average_precision"] == pytest.approx(float(ap), abs=1e-15)
            assert result["roc_auc"] == pytest.approx(float(auc), abs=1e-15)
            changed = binary_rank_metrics(
                target, [s**3 + 30 for s in scores], target_meaning="synthetic_Y"
            )
            assert changed == result


def test_extreme_finite_and_integer_minimum_do_not_overflow():
    with np.errstate(all="raise"):
        for scores in ([np.iinfo(np.int64).min, 1], [-1e308, 1e308]):
            result = binary_rank_metrics([0, 1], scores, target_meaning="synthetic_Y")
            assert result["roc_auc"] == 1


@pytest.mark.parametrize(
    "labels,scores,meaning",
    [
        ([1, None], [2, 3], "synthetic_Y"),
        ([1, 2], [2, 3], "synthetic_Y"),
        ([1, 0], [2, np.nan], "synthetic_Y"),
        ([1, 0], [2, np.inf], "synthetic_Y"),
        ([1, 0], [2], "synthetic_Y"),
        ([], [], "synthetic_Y"),
        ([1, 0], [2, 3], "verified_fire_Y"),
    ],
)
def test_unknowns_or_unsupported_semantics_do_not_become_fire_metrics(labels, scores, meaning):
    with pytest.raises(ValueError):
        binary_rank_metrics(labels, scores, target_meaning=meaning)


@pytest.mark.parametrize("labels", [[0, 0], [1, 1]])
def test_single_class_is_explicitly_undefined(labels):
    result = binary_rank_metrics(labels, [-10, 200], target_meaning="synthetic_Y")
    assert result["status"] == "undefined_single_class"
    assert all(result[k] is None for k in ("average_precision", "pr_auc_trapezoid", "roc_auc"))
