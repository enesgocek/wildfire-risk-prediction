"""Verify researcher-selected cell direction against the unchanged water scope."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "configs/cell_scope_direction_v1.json"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    policy = json.loads(POLICY.read_bytes())
    pins = {POLICY.relative_to(ROOT).as_posix(): sha(POLICY)}
    loaded = {}
    for stem in ("baseline_scope_report", "decision_comparison_report"):
        path = (ROOT / policy[stem]).resolve()
        require(path.is_relative_to(ROOT / "outputs"), "Local output evidence")
        expected = policy[stem + "_sha256"]
        require(sha(path) == expected, "Decision evidence changed")
        pins[policy[stem]] = expected
        loaded[stem] = (path, json.loads(path.read_bytes()))
    base_path, base = loaded["baseline_scope_report"]
    cmp_path, comparison = loaded["decision_comparison_report"]
    base_csv = base_path.parent / "grid_water_scope.csv"
    comparison_csv = cmp_path.parent / "cell_map_comparison.csv"
    for path, parent in ((base_csv, base), (comparison_csv, comparison)):
        require(sha(path) == parent["artifact_sha256"][path.name], "Table identity")
        pins[path.relative_to(ROOT).as_posix()] = sha(path)
    baseline = pd.read_csv(base_csv)
    compared = pd.read_csv(comparison_csv)
    require(baseline.grid_id.is_unique and compared.grid_id.is_unique, "Unique cell keys")
    joined = baseline[["grid_id", "water_scope_included"]].merge(
        compared[["grid_id", "water_scope_included"]],
        on="grid_id",
        how="outer",
        validate="one_to_one",
        suffixes=("_baseline", "_comparison"),
        indicator=True,
    )
    require(joined._merge.eq("both").all(), "Complete matching cell universes")
    require(
        joined.water_scope_included_baseline.eq(joined.water_scope_included_comparison).all(),
        "Same retained cell keys",
    )
    keep = sorted(baseline.loc[baseline.water_scope_included, "grid_id"])
    require(len(baseline) == policy["geographic_cells"] == 2899, "Geographic cells")
    require(len(keep) == policy["candidate_cells_retained"] == 2889, "Candidate population")
    require(
        len(baseline) - len(keep) == policy["baseline_water_excluded_cells"] == 10,
        "Existing water exclusions only",
    )
    require(
        policy["direction_accepted"] is True
        and policy["fraction_cut_applied"] is False
        and policy["additional_minimum_forest_shrub_fraction"] is None,
        "Explicit direction without additional fraction filter",
    )
    for key in (
        "full_habitat_policy_accepted",
        "positive_label_permitted",
        "negative_label_permitted",
        "model_ready",
        "final_merge_permitted",
    ):
        require(policy[key] is False, "Scope choice cannot grant scientific acceptance")
    require(policy["daily_observation_status"] == "unknown", "Observation state")
    baseline_policy = ROOT / policy["baseline_policy"]
    require(
        sha(baseline_policy) == base["input_sha256"][policy["baseline_policy"]],
        "Baseline policy unchanged",
    )
    pins[policy["baseline_policy"]] = sha(baseline_policy)
    pins[Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__))
    result = {
        "status": "researcher_direction_verified_not_label_or_merge_approval",
        "source_sha256": pins,
        "cells_retained": len(keep),
        "additional_cells_excluded": 0,
        "retained_grid_ids_sha256": hashlib.sha256(("\n".join(keep) + "\n").encode()).hexdigest(),
        "positive_labels_created": 0,
        "negative_labels_created": 0,
        "model_trained": False,
        "final_merge_performed": False,
    }
    out = (
        ROOT
        / "outputs/reports/dataset/cell_scope_direction_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    saved = out / "readback.json"
    saved.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(saved.read_bytes()) == result, "Decision readback")
    print(out.relative_to(ROOT).as_posix())
    print("PASS same_2889_candidate_cells; no additional filter or labels")
    print("readback_sha256", sha(saved))


if __name__ == "__main__":
    main()
