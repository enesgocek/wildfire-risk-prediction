"""Pinned noisy-positive PU method review and exact illustrative rate recovery, not training."""

import hashlib
import json
from datetime import UTC, datetime
from fractions import Fraction as F
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCES = BASE / "noisy_positive_pu_review_v1/20261119T120218Z_655ee79b"
PREFIX = BASE / "salur_prefix_quality_v1/20261119T120007Z_42e00153/readback.json"
PREFIX_SHA = "69c361554207695fbaa20d28a46ee04372860dbdf0ad4635ee8e5c98ac3f716c"
PINS = {
    SOURCES
    / "jain_2016_nips.pdf": "76411399354dc4de3d296f8867071b5d25edf0b445cb809f76e05a2e3f824478",
    SOURCES
    / "jain_2017_aaai.pdf": "2b2594513ebf9b5dfc434704d3b989313647581c7613db0246a143c7f8a7933f",
    PREFIX: PREFIX_SHA,
}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def recover(alpha, beta, labeled_rate, unlabeled_rate):
    """Single-threshold mixture identity from AAAI 2017; parameters are supplied, not estimated."""
    require(
        all(isinstance(v, F) for v in (alpha, beta, labeled_rate, unlabeled_rate)),
        "Exact fractions",
    )
    require(0 <= alpha < beta <= 1, "Positive enrichment and nonzero denominator")
    require(0 <= labeled_rate <= 1 and 0 <= unlabeled_rate <= 1, "Rates in [0,1]")
    tpr = ((1 - alpha) * labeled_rate - (1 - beta) * unlabeled_rate) / (beta - alpha)
    fpr = (beta * unlabeled_rate - alpha * labeled_rate) / (beta - alpha)
    require(0 <= tpr <= 1 and 0 <= fpr <= 1, "Inconsistent mixtures; do not clip")
    return {
        "tpr": tpr,
        "fpr": fpr,
        "precision": alpha * tpr / unlabeled_rate if unlabeled_rate else None,
    }


def example():
    # A hypothetical population, not wildfire frequencies or a fitted classifier.
    alpha, beta, tpr, fpr = F(1, 20), F(4, 5), F(4, 5), F(1, 10)
    labeled = beta * tpr + (1 - beta) * fpr
    unlabeled = alpha * tpr + (1 - alpha) * fpr
    result = recover(alpha, beta, labeled, unlabeled)
    require(result == {"tpr": tpr, "fpr": fpr, "precision": F(8, 27)}, "Exact recovery")
    sample_l_fraction = F(1, 2)
    naive = (
        sample_l_fraction
        * labeled
        / (sample_l_fraction * labeled + (1 - sample_l_fraction) * unlabeled)
    )
    require(
        labeled == F(33, 50) and unlabeled == F(27, 200) and naive == F(44, 53),
        "Illustrative mixtures",
    )
    guards = 0
    for args in [(F(1, 2), F(1, 2), F(1, 2), F(1, 2)), (alpha, beta, F(0), F(1))]:
        try:
            recover(*args)
        except ValueError:
            guards += 1
    require(guards == 2, "Reject singular or inconsistent inputs")
    return {
        "synthetic_only": True,
        "alpha_unlabeled_positive_fraction": alpha,
        "beta_labeled_positive_fraction": beta,
        "true_tpr": tpr,
        "true_fpr": fpr,
        "labeled_prediction_rate": labeled,
        "unlabeled_prediction_rate": unlabeled,
        "fraction_labeled_in_pooled_pseudo_test": sample_l_fraction,
        "pseudo_precision_if_U_is_treated_as_negative": naive,
        "actual_population_precision": result["precision"],
        "recovered": result,
        "invalid_input_guards_verified": guards,
        "class_prior_or_noise_estimated_from_real_data": False,
        "average_precision_computed": False,
        "probabilities_calibrated": False,
    }


def main():
    require(all(sha(p) == h for p, h in PINS.items()), "Source PDF and native cohort pins")
    receipts = json.loads((SOURCES / "source_receipts.json").read_text())
    for name in ("jain_2016_nips.pdf", "jain_2017_aaai.pdf"):
        require(
            receipts[name]["sha256"] == PINS[SOURCES / name]
            and receipts[name]["http_status"] == 200
            and not receipts[name]["credentials_used"],
            "Anonymous primary source receipt",
        )
    prefix = json.loads(PREFIX.read_text())
    require(
        prefix["summary"]["native_matches"] == 74
        and prefix["summary"]["strict_low7_removed_count"] == 54,
        "Fixed case evidence",
    )
    gate = specification()
    require(
        gate["daily_observation_status"] == "unknown"
        and not any(
            gate[k] for k in ("positive_label_permitted", "negative_label_permitted", "model_ready")
        ),
        "Closed scientific admission",
    )
    result = {
        "scope": "primary_method_review_plus_synthetic_mixture_recovery_only",
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
        "source_receipt_sha256": sha(SOURCES / "source_receipts.json"),
        "script_sha256": sha(Path(__file__)),
        "illustration": example(),
        "project_interpretation": {
            "all_PU_methods_require_perfect_positive_labels": False,
            "noisy_positive_route_exists": True,
            "shared_class_conditionals_verified_for_project": False,
            "mutual_irreducibility_of_semantic_fire_classes_verified": False,
            "positive_enrichment_or_noise_rate_measured_for_project": False,
            "QA_warning_fraction_is_label_noise_fraction": False,
            "source_match_ambiguity_resolved_by_algorithm": False,
            "population_AP_or_calibration_recovered_for_project": False,
        },
        "gate": gate,
        "method_accepted": False,
        "labels_created": False,
        "model_trained": False,
        "final_merge_performed": False,
        "heldout_data_read": False,
    }
    result = json.loads(json.dumps(result, default=str))
    out = (
        BASE
        / "noisy_positive_pu_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Report readback")
    require(all(sha(p) == h for p, h in PINS.items()), "Input closure")
    print(path.relative_to(ROOT), sha(path))
    print(
        "PASS exact conditional rate recovery and invalid-input guards; "
        "no real prior/noise estimate"
    )


if __name__ == "__main__":
    main()
