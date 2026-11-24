"""Prepare a concrete nested-source evaluation proposal; do not evaluate scores."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction import source_disjoint_plan as planning
from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
UI = BASE / "historical_research_prototype_v2/20261123T195053Z_aa61b349"
RUN = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"
CONFIG = ROOT / "configs/source_disjoint_evaluation_proposal_v1.json"


def main():
    policy = json.loads(CONFIG.read_bytes())
    if policy["status"] != "proposed_pending_researcher_method_decision" or any(
        policy[k]
        for k in (
            "new_training",
            "new_predictions",
            "new_threshold_selection",
            "new_Y_or_L",
            "observation_policy_change",
            "fire_validation_claim",
            "closed_years",
            "final_merge",
        )
    ):
        raise ValueError("Preparation only")
    if policy["source_groups"] != list(planning.GROUPS) or policy["slices"] != list(
        planning.SLICES
    ):
        raise ValueError("Fixed proposed groups and unchanged comparison windows")
    pins = {
        UI / "readback.json": "1afe43954ce0ccbe139df71e414fda7b0d0faf9dbfc332ae66fbc0beea80caa1",
        RUN / "readback.json": "004f7d27d6b0f1825b2b00d7a2825b311e2483b5f2d73c7063cadd9b45b2946d",
        CONFIG: digest(CONFIG),
        Path(planning.__file__): digest(Path(planning.__file__)),
    }
    for folder in (UI, RUN):
        receipt = json.loads((folder / "readback.json").read_bytes())
        pins.update({folder / n: sha for n, sha in receipt["artifact_sha256"].items()})
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Frozen source bytes")
    raw = (UI / "review_data.js").read_text(encoding="utf-8").strip()
    payload = json.loads(raw.removeprefix("globalThis.RESEARCH_DATA=")[:-1])
    if payload["scientific_state"] != {
        "target": None,
        "accepted_L_membership": None,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "fire_risk_validated": False,
    }:
        raise ValueError("Unknown scientific target")
    # The preparation uses keys, memberships and quality only, not score or X arrays.
    records = [
        {k: r[k] for k in ("cohort", "grid", "time", "flags", "eligible")}
        for r in payload["records"]
    ]
    anchors = planning.inventory(records)
    counts = planning.support(anchors)
    metrics = pd.read_csv(RUN / "metrics.csv", usecols=["cohort", "slice", "pairs"])
    for row in counts.loc[counts.source_group.eq(planning.GROUPS[0])].itertuples():
        original = metrics.loc[
            metrics.cohort.eq("separate_Mersin") & metrics["slice"].eq(row.slice)
        ]
        if (
            len(original) != 27
            or not original.pairs.eq(row.planned_comparison_pairs_per_model_scenario).all()
        ):
            raise ValueError("Every existing reference pair count restored")
    fit_rows = []
    for scenario in payload["scenarios"]:
        cells = set(pd.read_csv(RUN / scenario / "fit_layout.csv", usecols=["grid_id"]).grid_id)
        for group in planning.GROUPS:
            selected = anchors.loc[planning.group_mask(anchors, group) & anchors.primary_eligible]
            fit_rows.append(
                {
                    "scenario": scenario,
                    "source_group": group,
                    "eligible_source_days_in_seen_fit_cells": int(
                        selected.grid_id.isin(cells).sum()
                    ),
                    "eligible_source_days_in_unseen_fit_cells": int(
                        (~selected.grid_id.isin(cells)).sum()
                    ),
                }
            )
    expected = (
        len(planning.GROUPS)
        * len(planning.SLICES)
        * len(payload["scenarios"])
        * len(policy["models"])
    )
    if expected != policy["maximum_metric_rows"]:
        raise ValueError("Proposed evaluation work limit")
    out = (
        BASE
        / "source_disjoint_evaluation_preparation_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    anchors.to_csv(out / "source_anchor_inventory.csv", index=False)
    counts.to_csv(out / "planned_support.csv", index=False)
    pd.DataFrame(fit_rows).to_csv(out / "planned_seen_cell_support.csv", index=False)
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Source bytes changed")
    proposal = policy | {
        "scenarios": payload["scenarios"],
        "planned_support_rows": counts.to_dict("records"),
        "no_execution_authorization_receipt_present": True,
    }
    (out / "execution_proposal.json").write_text(
        json.dumps(proposal, indent=2) + "\n", encoding="utf-8"
    )
    body = {
        "status": "key_membership_feasibility_complete_proposed_evaluation_not_run",
        "source_anchors": len(anchors),
        "eligible_source_anchors": int(anchors.primary_eligible.sum()),
        "new_performance_metrics_computed": 0,
        "new_model_or_prediction_calls": 0,
        "source_groups_are_nested_not_independent": True,
        "true_fire_validation": False,
        "scientific_state": payload["scientific_state"],
        "final_merge": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), body["status"], flush=True)


if __name__ == "__main__":
    main()
