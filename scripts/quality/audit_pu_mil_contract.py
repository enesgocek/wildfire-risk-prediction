"""Reproduce an illustrative prior-shift calculation; no wildfire model or labels."""

import hashlib
import json
from datetime import UTC, datetime
from fractions import Fraction as F
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset/pu_mil_method_v1"
SOURCE = BASE / "20261119T111927Z_9aa388b0/bao_2018_v3.pdf"
SOURCE_SHA = "a32a9d6fdab37aa3aced49dce0a475d9db2290d07dc4fa837aecb02cc1441b60"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def illustration():
    # Finite distributions illustrate the section 3.4 algebra, not a bag generator.
    # In particular we do not claim iid draws guarantee at least one positive per bag.
    plus, minus = (F(4, 5), F(1, 5)), (F(1, 5), F(4, 5))
    theta, pi = F(1, 10), F(1, 10)
    rho = theta * pi
    p = tuple(theta * a + (1 - theta) * b for a, b in zip(plus, minus, strict=True))
    u = tuple(rho * a + (1 - rho) * b for a, b in zip(plus, minus, strict=True))
    require(sum(plus) == sum(minus) == sum(p) == sum(u) == 1, "Normalized densities")
    difference = tuple(a - b for a, b in zip(p, u, strict=True))
    expected = tuple(theta * (1 - pi) * (a - b) for a, b in zip(plus, minus, strict=True))
    require(difference == expected == (F(27, 500), -F(27, 500)), "Exact density identity")
    posterior = tuple(rho * a / b for a, b in zip(plus, u, strict=True))
    balanced = tuple(a / (a + b) for a, b in zip(plus, minus, strict=True))
    require(posterior == (F(4, 103), F(1, 397)), "Rare-population posterior")
    require(difference[0] > 0 and balanced[0] > F(1, 2) > posterior[0], "Decision vs probability")
    return {
        "synthetic_only": True,
        "positive_conditional_A_B": plus,
        "negative_conditional_A_B": minus,
        "theta": theta,
        "pi": pi,
        "unlabeled_pool_positive_fraction": rho,
        "positive_pool_marginal_A_B": p,
        "unlabeled_pool_marginal_A_B": u,
        "density_difference_A_B": difference,
        "balanced_population_posterior_A_B": balanced,
        "rare_population_posterior_A_B": posterior,
        "paper_classifier_is_not_a_probability_output": True,
        "bag_generation_or_positive_bag_guarantee_simulated": False,
    }


def main():
    require(sha(SOURCE) == SOURCE_SHA and SOURCE.stat().st_size == 725028, "Pinned primary PDF")
    gate = specification()
    require(
        gate["daily_observation_status"] == "unknown"
        and not any(
            gate[k] for k in ("positive_label_permitted", "negative_label_permitted", "model_ready")
        ),
        "Closed admission required",
    )
    result = {
        "scope": "primary_method_review_and_exact_synthetic_algebra_only",
        "source_url": "https://arxiv.org/pdf/1704.06767v3",
        "journal_doi": "10.1016/j.neunet.2018.05.001",
        "reviewed_sections": ["3.3", "3.4", "Appendix A"],
        "input_sha256": {SOURCE.relative_to(ROOT).as_posix(): SOURCE_SHA},
        "script_sha256": sha(Path(__file__)),
        "illustration": illustration(),
        "gate": gate,
        "method_accepted": False,
        "labels_created": False,
        "model_trained": False,
        "final_merge_performed": False,
        "heldout_data_read": False,
    }
    result = json.loads(json.dumps(result, default=str))
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = BASE / stamp
    out.mkdir(parents=True, exist_ok=False)
    report = out / "readback.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(json.loads(report.read_text(encoding="utf-8")) == result, "JSON readback")
    require(sha(SOURCE) == SOURCE_SHA, "Input unchanged")
    print(out.relative_to(ROOT))
    print("report_sha256", sha(report))
    print("PASS exact_density_identity_and_prior_shift; no wildfire labels or training")


if __name__ == "__main__":
    main()
