"""Correct supplemental area diagnostics using frozen ASCII province codes, not display names."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.feature_partition import parse_csv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "temporal_pairwise_run_v1/20261121T174415Z_5a77b21e"
CLOSURE = BASE / "temporal_pairwise_closure_v1/20261121T175009Z_0d5f3e3d"
CONTEXT = BASE / "satellite_PU_ranking_audit_v1/20261120T013224Z_b8a45358"


def membership_mask(signatures, province_code):
    require(province_code in {"Antalya", "Izmir", "Mersin", "Mugla"}, "Frozen ASCII area code")
    return signatures.map(lambda signature: province_code in signature.split("|")).to_numpy()


def main():
    require(
        digest(CLOSURE / "readback.json")
        == "b4b4ce4c14d191296204812eb22c0eeecbb61192db3aceed0c0f7add68cee257",
        "Preserved original supplemental diagnostics",
    )
    closure = json.loads((CLOSURE / "readback.json").read_bytes())
    pins = {ROOT / p: h for p, h in closure["input_sha256"].items()}
    pins[CLOSURE / "readback.json"] = digest(CLOSURE / "readback.json")
    require(all(digest(p) == h for p, h in pins.items()), "Original audited inputs unchanged")
    report = json.loads((RUN / "readback.json").read_bytes())
    context = parse_csv((CONTEXT / "assessment_context.csv").read_bytes())
    mapping = context[["grid_id", "province_support"]].drop_duplicates()
    require(mapping.grid_id.is_unique, "One original area signature per grid")
    mapping = mapping.set_index("grid_id").province_support
    snapshot = (
        BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896/snapshot_8914be77"
    )
    metadata = parse_csv((snapshot / "review_roles.csv").read_bytes())
    held = metadata.index[metadata.review_temporal_role.eq("proposed_assessment_2022")]
    rows = []
    for summary in report["scenario_summaries"]:
        scenario = summary["scenario"]
        scores = parse_csv((RUN / scenario / "assessment_scores.csv").read_bytes())
        scores.index = held
        signatures = scores.grid_id.map(mapping)
        pairs = parse_csv((RUN / scenario / "assessment_pair_indices.csv").read_bytes())
        a, b = pairs.source_calendar_row.to_numpy(), pairs.other_calendar_row.to_numpy()
        for code, label in (
            ("Antalya", "Antalya"),
            ("Izmir", "İzmir"),
            ("Mersin", "Mersin"),
            ("Mugla", "Muğla"),
        ):
            mask = membership_mask(signatures.loc[a], code)
            require(mask.any(), "Every expected province has nonempty pair support")
            for column in (
                "temporal_pairwise_linear_score_not_probability",
                "full_27_features_auxiliary_source_score",
                "weather_only_auxiliary_source_score",
                "static_cover_terrain_only_auxiliary_source_score",
            ):
                delta = (
                    scores.loc[a[mask], column].to_numpy() - scores.loc[b[mask], column].to_numpy()
                )
                require(np.isfinite(delta).all(), "Complete dynamic pair scores")
                value = (int((delta > 0).sum()) + int((delta == 0).sum()) / 2) / len(delta)
                rows.append(
                    {
                        "scenario": scenario,
                        "province_code": code,
                        "province_display": label,
                        "score_column": column,
                        "pairs": len(delta),
                        "source_keys_with_comparator": len(set(a[mask])),
                        "auxiliary_pair_AUC": value,
                    }
                )
    out = (
        BASE
        / "temporal_pairwise_province_correction_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    p = out / "province_context_corrected.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    result = {
        "status": "supplemental_province_diagnostics_corrected_ASCII_display_mismatch",
        "correction_scope": (
            "original_Izmir_Mugla_supplemental_slices_were_empty_due_to_display_name_comparison"
        ),
        "original_closure_preserved": CLOSURE.relative_to(ROOT).as_posix(),
        "original_36_core_metrics_changed": False,
        "new_models_fitted": 0,
        "province_memberships_may_overlap": True,
        "nonempty_province_scenario_combinations": 36,
        "metric_rows": len(rows),
        "true_Y_or_accepted_L_created": 0,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {p.name: digest(p)},
        "producer_sha256": digest(Path(__file__)),
    }
    require(all(digest(p) == h for p, h in pins.items()), "No original data or model mutation")
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


if __name__ == "__main__":
    main()
