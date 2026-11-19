"""Prepare a concrete temporal pilot partition proposal; never fit or relabel data."""

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
REVIEW = BASE / "source_pu_feature_review_v1/20261119T210151Z_3e99d4a1/readback.json"
REVIEW_SHA = "ccc9086c505e22028a670ab9451e2323f429cd8048b83b4c2361519ec2916405"
PROTOCOL = BASE / "source_conditioned_pu_protocol_v1/20261119T200942Z_3bc1ded8/readback.json"
PROTOCOL_SHA = "c22b246a5f93563115a193de7022d63accdabb18938ac5a635f4916ff3951df9"
POLICY = ROOT / "configs/conditional_pu_ranking_pilot_v1.json"
PDF = BASE / "conditional_pu_ranking_v1/sources/20261119T210000Z/menon15.pdf"
PDF_SHA = "5c20f1f2bd415493bbb77966ab9b6b1d1f26b8a4323206dae3df9172e96ded2f"
CUT = datetime(2022, 1, 1, tzinfo=UTC)
START, END = datetime(2018, 1, 1, tzinfo=UTC), datetime(2023, 1, 1, tzinfo=UTC)


def window_partition(start):
    stamp = datetime.fromisoformat(start)
    require(stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0), "UTC partition window")
    require(stamp.time().replace(tzinfo=None) == datetime.min.time(), "Midnight partition window")
    end = stamp + timedelta(days=1)
    if START <= stamp and end < CUT:
        return "proposed_fit_2018_2021"
    if CUT <= stamp and end < END:
        return "proposed_assessment_2022"
    return "boundary_review_not_used"


def propose_sources(cases, multi_blocks):
    focus = {r["archive_row"]: r for r in cases if r["diagnostic_focus"]}
    require(len(focus) == sum(r["diagnostic_focus"] for r in cases), "Unique source identity")
    raw = {}
    for key, row in focus.items():
        require(
            not row["researcher_retained_outside_L"]
            and row["target"] is None
            and row["membership"] == "review_unassigned",
            "Retained source state",
        )
        phases = {window_partition(t["window_start_utc"]) for t in row["temporal_alternatives"]}
        raw[key] = next(iter(phases)) if len(phases) == 1 else "boundary_review_not_used"
    result = dict(raw)
    seen = set()
    for block in multi_blocks:
        require(
            set(block) <= set(focus) and not (seen & set(block)),
            "Nonoverlapping known dependency blocks",
        )
        seen.update(block)
        phases = {raw[k] for k in block}
        if len(phases) != 1 or "boundary_review_not_used" in phases:
            for key in block:
                result[key] = "boundary_review_not_used"
    by_key = defaultdict(set)
    for key, row in focus.items():
        by_key[
            (row["conditional_center_grid_ids"][0], row["conditional_target_window_starts"][0])
        ].add(result[key])
    return {
        k: next(iter(v)) if len(v) == 1 else "boundary_review_not_used" for k, v in by_key.items()
    }, result


def main():
    pins = {REVIEW: REVIEW_SHA, PROTOCOL: PROTOCOL_SHA, PDF: PDF_SHA, POLICY: digest(POLICY)}
    require(all(digest(p) == h for p, h in pins.items()), "Pinned inputs and new proposal")
    review, protocol, policy = [json.loads(p.read_bytes()) for p in (REVIEW, PROTOCOL, POLICY)]
    require(
        policy["feature_review_sha256"] == REVIEW_SHA
        and policy["source_protocol_sha256"] == PROTOCOL_SHA
        and policy["source_paper_sha256"] == PDF_SHA,
        "Proposal bound to inspected files",
    )
    require(
        policy["status"] == "concrete_method_proposal_awaiting_researcher_direction"
        and not policy["auxiliary_model_fitting_authorized"]
        and not policy["training_authorized"],
        "No fitting direction yet",
    )
    require(
        policy["proposed_preprocessing"]["preprocessing_fitted_now"] is False,
        "No learned preprocessing",
    )
    features_path = REVIEW.parent / "features.csv"
    inspection_path = REVIEW.parent / "inspection.csv"
    for path in (features_path, inspection_path):
        pins[path] = review["artifact_sha256"][path.name]
    require(all(digest(p) == h for p, h in pins.items()), "Feature review identity")
    source_plan, case_plan = propose_sources(
        protocol["cases"], protocol["plausible_key_dependencies"]["multiple_source_record_blocks"]
    )
    with inspection_path.open(encoding="utf-8", newline="") as f:
        entries = list(csv.DictReader(f))
    rows = []
    for row in entries:
        require(
            row["target"] == "" and row["daily_observation_status"] == "unknown",
            "Targets remain unknown",
        )
        key = (row["grid_id"], row["prediction_timestamp_utc"])
        phase = (
            source_plan[key]
            if row["review_population"] == "source_center_hypothesis"
            else window_partition(key[1])
        )
        rows.append(
            {
                "grid_id": key[0],
                "prediction_timestamp_utc": key[1],
                "review_population": row["review_population"],
                "proposed_partition": phase,
                "target": None,
            }
        )
    require(
        len(rows) == 877 and len(source_plan) == 374 and len(case_plan) == 380,
        "Full review units retained",
    )
    features = pd.read_csv(features_path)
    feature_names = review["feature_columns"]
    fit_keys = {
        (r["grid_id"], r["prediction_timestamp_utc"])
        for r in rows
        if r["proposed_partition"] == "proposed_fit_2018_2021"
    }
    fit = features.set_index(["grid_id", "prediction_timestamp_utc"]).loc[sorted(fit_keys)]
    counts = {
        phase: dict(
            Counter(r["review_population"] for r in rows if r["proposed_partition"] == phase)
        )
        for phase in sorted({r["proposed_partition"] for r in rows})
    }
    report = {
        "status": "conditional_ranking_partition_proposal_ready_researcher_direction_pending",
        "proposal": policy,
        "review_keys_retained": len(rows),
        "partition_counts_by_review_population": counts,
        "source_record_partition_counts": dict(Counter(case_plan.values())),
        "source_record_proposed_partitions": case_plan,
        "all_missing_features_in_proposed_fit": [k for k in feature_names if fit[k].isna().all()],
        "proposed_fit_missing_counts": {k: int(fit[k].isna().sum()) for k in feature_names},
        "proposed_key_partitions": rows,
        "partitioning_is_physical_event_validation": False,
        "auxiliary_membership_labels_created": False,
        "true_fire_labels_created": 0,
        "preprocessing_fitted": False,
        "model_fitted": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    out = (
        BASE
        / "conditional_rank_partition_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == report, "Partition proposal roundtrip")
    require(all(digest(p) == h for p, h in pins.items()), "Inputs unchanged")
    print(out.relative_to(ROOT).as_posix())
    print(json.dumps(counts))
    print("PASS partition_proposal_only; no auxiliary labels, imputation, fit or target admission")
    print("readback_sha256", digest(path))


if __name__ == "__main__":
    main()
