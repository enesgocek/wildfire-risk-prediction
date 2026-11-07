"""Check the frozen C case against catalogue history and local scan packets."""

import csv
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.observation_window import review_window, source_schedule
from wildfire_risk_prediction.observation_window_source import read_month_offline

ROOT = Path(__file__).resolve().parents[2]
BASE = "outputs/reports/dataset"
GRAPH = "outputs/reports/events/review_v1/20261010T001137Z_320433ed"
OBS = f"{BASE}/observation_materialization_v1/20261014T145638Z_c0881064"
CASE = f"{BASE}/pu_candidate_review_v1/20261107T213328Z_29cb887c/readback.json"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def scenario_membership(graph, anchor, retain):
    summaries = []
    for name, digests in sorted(graph["artifact_sha256"].items()):
        assignments = pd.read_csv(
            retain(
                f"data/interim/event_grouping/{name}_assignments.csv", digests["assignments_sha256"]
            )
        )
        require(
            len(assignments) == graph["training_detection_count"]
            and assignments.detection_id.is_unique,
            "Frozen training assignments",
        )
        match = assignments.loc[assignments.detection_id.eq(anchor.detection_id)]
        require(len(match) == 1, "Unique anchor assignment")
        cluster = match.iloc[0].cluster_id
        members = assignments.loc[assignments.cluster_id.eq(cluster)].copy()
        members["utc"] = pd.to_datetime(members.timestamp, utc=True, format="ISO8601")
        digest = hashlib.sha256("\n".join(sorted(members.detection_id)).encode()).hexdigest()
        catalogue = pd.read_csv(retain(f"{GRAPH}/{name}_review.csv", digests["review_sha256"]))
        rows = catalogue.loc[catalogue.cluster_id.eq(cluster)]
        require(len(rows) == 1, "Unique catalogue cluster")
        record = rows.iloc[0]
        require(
            len(members) == record.detection_count
            and digest == record.membership_sha256
            and members.utc.min() == pd.Timestamp(record.first_detection_utc) == anchor.timestamp,
            "Membership and first time",
        )
        first = members.loc[members.utc.eq(anchor.timestamp)]
        require(set(first.grid_id) == set(json.loads(record.earliest_grid_ids_json)), "First cells")
        summaries.append(
            {
                "scenario": name,
                "membership_sha256": digest,
                "member_count": len(members),
                "members": sorted(members.detection_id),
                "first_utc": anchor.timestamp.isoformat(),
                "last_utc": members.utc.max().isoformat(),
                "first_cells": sorted(set(first.grid_id)),
            }
        )
    require(
        len(summaries) == 9 and len({r["membership_sha256"] for r in summaries}) == 1, "Stability"
    )
    return summaries


def prior_neighbourhood(source, anchor):
    begin = anchor.timestamp - pd.Timedelta(hours=72)
    earlier = source.loc[source.timestamp.ge(begin) & source.timestamp.lt(anchor.timestamp)].copy()
    _, _, distance = GEOD.inv(
        [anchor.longitude] * len(earlier),
        [anchor.latitude] * len(earlier),
        earlier.longitude.to_numpy(),
        earlier.latitude.to_numpy(),
    )
    earlier["distance_m"] = distance
    fields = ["detection_id", "grid_id", "source_sensor", "timestamp", "distance_m"]
    nearest = earlier.sort_values(["distance_m", "detection_id"]).head(1)[fields]
    return {
        "begin_inclusive_utc": begin.isoformat(),
        "end_exclusive_utc": anchor.timestamp.isoformat(),
        "eligible_catalogue_rows_in_time_range": len(earlier),
        "nearby_counts": {
            str(radius): int(earlier.distance_m.le(radius).sum()) for radius in (500, 1000, 2000)
        },
        "same_cell_count": int(earlier.grid_id.eq(anchor.grid_id).sum()),
        "nearest_earlier_record": json.loads(nearest.to_json(orient="records", date_format="iso")),
    }


def scan_history(grid_id, retain):
    master = json.loads(
        retain(
            f"{OBS}/accepted_readback.json",
            "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14",
        ).read_text()
    )
    registry = json.loads(
        retain(
            "configs/gcp_source_blocks_2026-10-13.json",
            "c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95",
        ).read_text()
    )
    month = next(row for row in master["reports"] if row["month"] == "2021-08")
    schedules = {
        day: source_schedule(day, set(registry["deferred_days"]))
        for day in ("2021-08-12", "2021-08-13", "2021-08-14", "2021-08-15")
    }
    days = {
        day: {grid_id}
        for schedule in schedules.values()
        for day in schedule.loc[
            schedule.source_status.eq("available_training_packet"), "source_nominal_day"
        ]
    }
    packet = read_month_offline(ROOT, month, days, time.monotonic() + 120)
    for name, digest in packet["inputs"].items():
        retain(name, digest)
    summaries = []
    for day, schedule in schedules.items():
        frame = pd.concat(
            [packet["frames"][d] for d in schedule.source_nominal_day if d in packet["frames"]],
            ignore_index=True,
        )
        _, summary = review_window(frame, day, grid_id, schedule)
        del summary["target"]
        summaries.append(summary)
    return {
        "nominal_days": sorted(days),
        "inner_sha256": packet["inner"],
        "daily_windows": summaries,
    }


def main():
    pins = {}

    def retain(name, expected):
        path = ROOT / name
        require(path.resolve(strict=True).is_relative_to(ROOT), "Contained input")
        require(sha(path) == expected, f"Hash mismatch: {name}")
        pins[name] = expected
        return path

    case_report = json.loads(
        retain(CASE, "5b7fd0cc69efe03ff73dac67e65d58878add917f0a133917fe204715d07824ce").read_text()
    )
    case = next(row for row in case_report["review_cases"] if row["point_codes"] == ["C"])
    graph = json.loads(
        retain(
            f"{GRAPH}/review.json",
            "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e",
        ).read_text()
    )
    source_file = retain(
        "data/interim/firms_combined_candidates_2018_2024.csv", graph["source_sha256"]
    )
    rows, skipped = [], 0
    with source_file.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            year = row["detection_timestamp_utc"][:4]
            if year == "2024":
                skipped += 1
            else:
                rows.append(row)
    require(skipped == graph["validation_rows_excluded"], "Validation exclusion count")
    source = training_detections(pd.DataFrame(rows))
    require(len(source) == graph["training_detection_count"], "Training catalogue size")
    matches = source.loc[source.detection_id.eq(case["point_ids"][0])]
    require(len(matches) == 1, "Unique C catalogue record")
    anchor = matches.iloc[0]
    require(
        anchor.grid_id == case["grid_id"]
        and anchor.timestamp.isoformat() in case["first_times_utc"]
        and anchor.timestamp.strftime("%Y-%m-%d") == "2021-08-15",
        "C case identity",
    )
    membership = scenario_membership(graph, anchor, retain)
    earlier = prior_neighbourhood(source, anchor)
    observation = scan_history(anchor.grid_id, retain)
    code_files = [
        Path(__file__).relative_to(ROOT).as_posix(),
        "src/wildfire_risk_prediction/event_review.py",
        "src/wildfire_risk_prediction/observation_window.py",
        "src/wildfire_risk_prediction/observation_window_source.py",
    ]
    for name in code_files:
        retain(name, sha(ROOT / name))
    result = {
        "status": "single_candidate_catalogue_and_observation_context",
        "case_code": "C",
        "detection_id": anchor.detection_id,
        "grid_id": anchor.grid_id,
        "scenario_membership": membership,
        "preceding_catalogue_context": earlier,
        "validation_rows_skipped_by_date_before_scientific_processing": skipped,
        "observation_context": observation,
        "source_sha256": pins,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "target": None,
        "labels_created": False,
        "final_merge_performed": False,
    }
    for name, expected in pins.items():
        require(sha(ROOT / name) == expected, "Input changed during check")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    path = ROOT / BASE / "pu_candidate_timeline_v1" / stamp / "readback.json"
    path.parent.mkdir(parents=True, exist_ok=False)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == result, "JSON readback")
    print(path.relative_to(ROOT).as_posix(), sha(path))
    print("pins", len(pins), "scenarios", len(membership), "members", membership[0]["member_count"])
    print(json.dumps(earlier))
    for row in observation["daily_windows"]:
        print(
            row["prediction_timestamp_utc"],
            row["loaded_inside_scan_rows"],
            row["loaded_nominal_land_center_longest_envelope_gap_seconds"],
            row["loaded_thermal_center_definite_count"],
            row["loaded_thermal_center_boundary_count"],
        )


if __name__ == "__main__":
    main()
