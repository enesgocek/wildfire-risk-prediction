"""Read back frozen training cluster scenarios and record unresolved event semantics."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.event_review import (
    VERSION,
    review_partition,
    spatial_links,
    training_detections,
)

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
    old_path = ROOT / "outputs/reports/event_grouping_sensitivity.json"
    old = json.loads(old_path.read_text(encoding="utf-8"))
    if sha(source) != old["source_sha256"]:
        raise ValueError("Frozen detection source changed")
    frame = pd.read_csv(source, dtype="string")
    years = pd.to_datetime(frame.detection_timestamp_utc, utc=True, errors="raise").dt.year
    if not years.between(2018, 2024).all():
        raise ValueError("Combined source contains unexpected year")
    validation_count = int(years.eq(2024).sum())
    frame = training_detections(frame.loc[years.between(2018, 2023)])
    if len(frame) != old["training_detection_count"]:
        raise ValueError("Frozen training count changed")
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = ROOT / "outputs/reports/events/review_v1" / run_id
    out.mkdir(parents=True, exist_ok=False)
    summaries, hashes = [], {}
    expected = {entry["scenario"]: entry for entry in old["scenarios"]}
    for distance in (500, 1000, 2000):
        links = spatial_links(frame, distance)
        for gap in (24, 48, 72):
            scenario = f"d{distance}m_t{gap}h"
            path = ROOT / f"data/interim/event_grouping/{scenario}_assignments.csv"
            catalog, summary = review_partition(
                frame, pd.read_csv(path, dtype="string"), links, distance, gap
            )
            for key in ("cluster_count", "pair_connection_count", "largest_cluster_detections"):
                if summary[key] != expected[scenario][key]:
                    raise ValueError(f"Frozen summary mismatch: {scenario} {key}")
            target = out / f"{scenario}_review.csv"
            catalog.to_csv(target, index=False, mode="x")
            pd.testing.assert_frame_equal(catalog, pd.read_csv(target), check_dtype=False)
            hashes[scenario] = {"assignments_sha256": sha(path), "review_sha256": sha(target)}
            summaries.append(summary)
            print(
                f"VERIFIED {scenario}: {summary['cluster_count']} exploratory clusters", flush=True
            )
    report = {
        "version": VERSION,
        "status": "passed_training_graph_partition_readback",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_sha256": sha(source),
        "old_report_sha256": sha(old_path),
        "source_rows": len(frame) + validation_count,
        "training_detection_count": len(frame),
        "validation_rows_excluded": validation_count,
        "final_test_accessed": False,
        "labels_created": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "confirmed_event_count": None,
        "scenario_selected": None,
        "scenarios": summaries,
        "artifact_sha256": hashes,
        "code_sha256": {
            p: sha(ROOT / p)
            for p in (
                "src/wildfire_risk_prediction/event_review.py",
                "scripts/firms/review_event_grouping.py",
            )
        },
        "limits": [
            "Connected components permit spatial and temporal chaining; not wildfire identity",
            "Canonical first grid breaks timestamp ties by detection id; never a final target",
            "Candidate window is (T,T+24h]; no reliable negative labels",
            "Offline graph uses later detections and can merge earlier clusters",
            "AOI boundaries and missing preceding/following source context truncate events",
            "Source Type interpretation awaits technical confirmation; "
            "no final vegetation-fire truth",
        ],
    }
    with (out / "review.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print("REPORT", (out / "review.json").relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
