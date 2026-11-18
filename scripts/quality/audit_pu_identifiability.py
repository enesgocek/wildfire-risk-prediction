"""Exact synthetic counterexamples for unrestricted PU and coarse event supervision.

This is a mathematical diagnostic, not a PU estimator or a labeling protocol.
No real observations, feature tables, validation years, or final test are read.
"""

import hashlib
import json
from datetime import UTC, datetime
from fractions import Fraction as F
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset/pu_method_review_v1"
PDF = BASE / "sources/he26a.pdf"
PDF_SHA256 = "04d34a9bbbf47360e04796a67ec0d6e738b39aad6ec5c378887e0fc1fe36b95a"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def world(name, risks, propensities):
    """Construct P(X,Y,S) with two equally likely groups and pure positive labels."""
    joint = {}
    for group, risk, propensity in zip(("A", "B"), risks, propensities, strict=True):
        require(0 < risk < 1 and 0 < propensity <= 1, "Valid probabilities")
        weight = F(1, 2)
        joint[group, 0, 0] = weight * (1 - risk)
        joint[group, 0, 1] = F(0)
        joint[group, 1, 0] = weight * risk * (1 - propensity)
        joint[group, 1, 1] = weight * risk * propensity
    require(sum(joint.values()) == 1, "Joint probability sums to one")
    observed = {
        (group, labeled): sum(joint[group, y, labeled] for y in (0, 1))
        for group in ("A", "B")
        for labeled in (0, 1)
    }
    prior = sum(value for (_, y, _), value in joint.items() if y == 1)
    return {
        "name": name,
        "group_risks": dict(zip(("A", "B"), risks, strict=True)),
        "group_labeling_propensities": dict(zip(("A", "B"), propensities, strict=True)),
        "class_prior": prior,
        "higher_risk_group": "A" if risks[0] > risks[1] else "B",
        "observed_joint": {f"{group},S={s}": value for (group, s), value in observed.items()},
        "joint": {f"{group},Y={y},S={s}": value for (group, y, s), value in joint.items()},
    }


def counterexamples():
    worlds = [
        world("constant_selection", (F(1, 25), F(1, 50)), (F(1, 2), F(1, 2))),
        world("feature_selection_other_prior", (F(1, 40), F(1, 10)), (F(4, 5), F(1, 10))),
        world("feature_selection_same_prior", (F(1, 40), F(7, 200)), (F(4, 5), F(2, 7))),
    ]
    require(
        all(w["observed_joint"] == worlds[0]["observed_joint"] for w in worlds),
        "All worlds have exactly the same observable joint distribution",
    )
    require(worlds[0]["class_prior"] != worlds[1]["class_prior"], "Different priors possible")
    require(worlds[0]["class_prior"] == worlds[2]["class_prior"], "Same prior also possible")
    require(
        worlds[0]["higher_risk_group"] != worlds[1]["higher_risk_group"]
        and worlds[0]["higher_risk_group"] != worlds[2]["higher_risk_group"],
        "Latent risk rankings reverse",
    )
    # Exact enumeration proves that a positive group/count does not select a member.
    assignments = [(1, 0, 0), (0, 1, 0)]
    require(
        assignments[0] != assignments[1] and all(max(a) == 1 and sum(a) == 1 for a in assignments),
        "Same positive bag and count, different positive cells",
    )
    events = [("cell_A_day_1", "cell_A_day_1"), ("cell_A_day_1", "cell_B_day_1")]
    require(
        len(events[0]) == len(events[1]) == 2
        and len(set(events[0])) == 1
        and len(set(events[1])) == 2,
        "Same incident count, different binary cell-day counts",
    )
    return {
        "worlds": worlds,
        "coarse_positive_bag_assignments": assignments,
        "same_incident_count_assignments": events,
        "result": "nonidentifiable_without_additional_restrictions",
        "limitations": [
            "Synthetic populations, not measured wildfire frequencies or model results",
            "Unrestricted feature-dependent selection, not a counterexample to PGPU guarantees",
            "One coarse bag does not resolve its members; learning across bags is not excluded",
            "Administrative scope and event-window semantics also require reconciliation",
        ],
    }


def main():
    with PDF.open("rb") as stream:
        require(hashlib.file_digest(stream, "sha256").hexdigest() == PDF_SHA256, "Source PDF")
    evidence = counterexamples()
    gate = specification()
    require(
        gate["daily_observation_status"] == "unknown"
        and not gate["positive_label_permitted"]
        and not gate["negative_label_permitted"]
        and not gate["model_ready"],
        "Existing closed admission protocol",
    )
    run = BASE / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    run.mkdir(parents=True, exist_ok=False)
    report = {
        "scope": "exact_synthetic_identifiability_diagnostic_only",
        "created_utc": datetime.now(UTC).isoformat(),
        "source_pdf_sha256": PDF_SHA256,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "paper_url": "https://proceedings.mlr.press/v337/he26a.html",
        "evidence": evidence,
        "target_admission": gate,
        "real_data_read": False,
        "model_trained": False,
        "method_accepted": False,
        "final_merge_approval": False,
    }
    encoded = json.dumps(report, default=str, ensure_ascii=False, indent=2) + "\n"
    destination = run / "readback.json"
    destination.write_text(encoded, encoding="utf-8")
    require(json.loads(destination.read_bytes()) == json.loads(encoded), "JSON readback")
    print(run.relative_to(ROOT))
    print("PASS exact synthetic counterexamples; no real labels or model accepted")
    print("SHA256", hashlib.sha256(destination.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
