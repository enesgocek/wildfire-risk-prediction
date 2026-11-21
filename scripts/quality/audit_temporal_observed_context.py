"""Inspect existing scores against retained detection history; do not relabel, refit or exclude."""

import bisect
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
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
LINEAGE = BASE / "satellite_PU_lineage_v1/20261120T003414Z_a21f7422"
AUDIT = BASE / "temporal_pairwise_audit_v1/20261121T174613Z_2feb2bbd"


def windows(times, graph_ids, t):
    """Past (T-7d,T], target (T,T+24h]; zero retained records is not absence."""
    past_start = bisect.bisect_right(times, t - timedelta(days=7))
    split = bisect.bisect_right(times, t)
    end = bisect.bisect_right(times, t + timedelta(days=1))
    return split - past_start, end - split, set(graph_ids[split:end])


def main():
    pins = {
        RUN / "readback.json": "b8e847f8d510721ce84b788161ae40ac5f3bfa098154b0e56a013fc380f83d82",
        AUDIT / "readback.json": "7faff2ad4721a8984b3a4e34aae3ebdbe8c61dde3c5568477bd257ed3d68d086",
        LINEAGE
        / "readback.json": "b13d15d640f51662bd75fc65a25769ca02ceb69c80836c4fe2b99e788ae2e530",
    }
    require(
        all(digest(p) == h for p, h in pins.items()), "Frozen pilot and retained observed graph"
    )
    report = json.loads((RUN / "readback.json").read_bytes())
    lineage = json.loads((LINEAGE / "readback.json").read_bytes())
    pins.update({ROOT / p: h for p, h in report["input_sha256"].items()})
    pins.update({RUN / p: h for p, h in report["artifact_sha256"].items()})
    path = LINEAGE / "d2000m_t72h/detections.csv"
    pins[path] = lineage["artifact_sha256"]["d2000m_t72h/detections.csv"]
    require(all(digest(p) == h for p, h in pins.items()), "Current score and detection files")
    raw = parse_csv(path.read_bytes())
    grouped = defaultdict(list)
    for row in raw.itertuples():
        grouped[row.grid_id].append(
            (datetime.fromisoformat(row.timestamp_utc), row.final_graph_membership_sha256)
        )
    index = {}
    for grid, rows in grouped.items():
        ordered = sorted(rows)
        index[grid] = ([r[0] for r in ordered], [r[1] for r in ordered])
    snapshot = (
        BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896/snapshot_8914be77"
    )
    metadata = parse_csv((snapshot / "review_roles.csv").read_bytes())
    held = metadata.loc[metadata.review_temporal_role.eq("proposed_assessment_2022")]
    contexts, graphs = [], {}
    for i, row in held.iterrows():
        t = datetime.fromisoformat(row.prediction_timestamp_utc)
        past, target, graph = windows(*index.get(row.grid_id, ([], [])), t)
        graphs[i] = graph
        contexts.append(
            {
                "calendar_row": i,
                "grid_id": row.grid_id,
                "prediction_timestamp_utc": row.prediction_timestamp_utc,
                "retained_detections_previous_7d": past,
                "retained_detections_target_24h": target,
                "no_retained_records_is_fire_absence": False,
            }
        )
    context = pd.DataFrame(contexts).set_index("calendar_row")
    metrics = []
    for summary in report["scenario_summaries"]:
        scenario = summary["scenario"]
        frame = parse_csv((RUN / scenario / "assessment_scores.csv").read_bytes())
        frame.index = held.index
        pairs = parse_csv((RUN / scenario / "assessment_pair_indices.csv").read_bytes())
        a, b = pairs.source_calendar_row.to_numpy(), pairs.other_calendar_row.to_numpy()
        masks = {
            "all_reviewed_pairs": np.ones(len(a), dtype=bool),
            "other_target_has_retained_detection": context.loc[
                b, "retained_detections_target_24h"
            ].to_numpy()
            > 0,
            "other_target_no_retained_detection_unknown": context.loc[
                b, "retained_detections_target_24h"
            ].to_numpy()
            == 0,
            "both_previous_7d_no_retained_detection_unknown": (
                context.loc[a, "retained_detections_previous_7d"].to_numpy() == 0
            )
            & (context.loc[b, "retained_detections_previous_7d"].to_numpy() == 0),
            "other_target_shares_observed_graph_with_source": np.array(
                [bool(graphs[i] & graphs[j]) for i, j in zip(a, b, strict=True)]
            ),
        }
        for name, mask in masks.items():
            for column in (
                "temporal_pairwise_linear_score_not_probability",
                "full_27_features_auxiliary_source_score",
                "weather_only_auxiliary_source_score",
                "static_cover_terrain_only_auxiliary_source_score",
            ):
                delta = (
                    frame.loc[a[mask], column].to_numpy() - frame.loc[b[mask], column].to_numpy()
                )
                require(np.isfinite(delta).all(), "Retained complete-dynamic pairs")
                value = (
                    (int((delta > 0).sum()) + int((delta == 0).sum()) / 2) / len(delta)
                    if len(delta)
                    else None
                )
                metrics.append(
                    {
                        "scenario": scenario,
                        "context_slice": name,
                        "score_column": column,
                        "pairs": len(delta),
                        "source_keys_with_comparator": len(set(a[mask])),
                        "other_keys_with_comparator": len(set(b[mask])),
                        "auxiliary_pair_AUC": value,
                    }
                )
    out = (
        BASE
        / "temporal_observed_context_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    context.to_csv(out / "retained_detection_context.csv")
    pd.DataFrame(metrics).to_csv(out / "observed_context_metrics.csv", index=False)
    result = {
        "status": "existing_scores_observed_context_audited_no_new_fit_or_relabel",
        "retained_detection_rows": len(raw),
        "calendar_context_rows": len(context),
        "retained_detection_scope": "2018_2022_nominal_high_Type0_SNPP_N20_selected_catalogue_only",
        "graph_scope": "observed_maximum_2000m_72h_not_physical_event_identity",
        "seven_days_is_accepted_fire_quiet_period": False,
        "new_Y_or_L_or_source_training_labels_created": 0,
        "new_models_fitted": 0,
        "original_pairs_or_rows_removed": False,
        "negative_label_permitted": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    require(
        all(digest(p) == h for p, h in pins.items()), "Original scores/models/metadata preserved"
    )
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


if __name__ == "__main__":
    main()
