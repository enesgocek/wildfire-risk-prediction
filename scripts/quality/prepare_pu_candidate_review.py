"""Link frozen pilot evidence and prepare a small, human cover review queue."""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
INPUTS = {
    "pilot": (
        "event_observation_link_v1/20261022T205236Z_797195a6",
        "9b4be7d301436840819d3a9d90ece3a5ede5f6bd257c364ef7d5cc9cc08cf6bf",
    ),
    "events": (
        "full_event_sensitivity_v1/20261022T204358Z_820d043d",
        "40818450ec28a2597eca1155bb6bb5896ce41fc65ec5fad2db6f1314d7229a86",
    ),
    "habitat": (
        "habitat_evidence_matrix_v1/20261103T215030Z_1106f3eb",
        "da877cc44c0626995dde7577892b2dbfbbc9f3a2efea5f226aa268569298366e",
    ),
}
STABLE = "all_presence_time_and_membership_equal"
REVIEW_CONTEXTS = ("built_context", "parcel_context", "mixed_unresolved")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(pins, path, expected):
    resolved = path.resolve(strict=True)
    relative = resolved.relative_to(ROOT).as_posix()
    require(digest(resolved) == expected, f"Hash mismatch: {relative}")
    pins[relative] = expected


def csv_rows(pins, role, receipt, name):
    path = BASE / INPUTS[role][0] / name
    pin(pins, path, receipt["artifact_sha256"][name])
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def event_key(row):
    return row["grid_id"], datetime.fromisoformat(row["prediction_timestamp_utc"])


def main():
    pins, receipts = {}, {}
    for role, (folder, sha) in INPUTS.items():
        path = BASE / folder / "readback.json"
        pin(pins, path, sha)
        record = json.loads(path.read_text(encoding="utf-8"))
        require(record["labels_created"] is False, f"Unexpected labels in {role}")
        receipts[role] = record
    pilot, events, habitat = (receipts[key] for key in INPUTS)
    observations = csv_rows(pins, "pilot", pilot, "pilot_evidence_links.csv")
    require(len(observations) == pilot["pilot_units"] == 156, "Changed pilot")
    require(len({row["review_unit_id"] for row in observations}) == 156, "Duplicate unit")
    joined = {
        row["review_unit_id"]: row
        for row in observations
        if row["first_candidate_present_in_catalog_union"] == "True"
    }
    cases = {case["review_unit_id"]: case for case in habitat["cases"]}
    points = {point["detection_id"]: point for point in habitat["rows"]}
    require(len(joined) == len(cases) == 21 and joined.keys() == cases.keys(), "Case mismatch")
    require(len(points) == len(habitat["rows"]) == 25, "Point mismatch")
    keys = {event_key(row) for row in joined.values()}
    require(len(keys) == 21, "Duplicate cell/day")

    candidates = {
        event_key(row): row
        for row in csv_rows(pins, "events", events, "candidate_units.csv")
        if event_key(row) in keys
    }
    components = defaultdict(list)
    for row in csv_rows(pins, "events", events, "component_cell_evidence.csv"):
        if event_key(row) in keys:
            components[event_key(row)].append(row)
    require(candidates.keys() == components.keys() == keys, "Event evidence mismatch")

    review = []
    for unit_id, case in sorted(cases.items()):
        observation = joined[unit_id]
        grid, prediction = event_key(observation)
        require(
            prediction.utcoffset() == timedelta(0) and 2018 <= prediction.year <= 2023,
            "Outside training window",
        )
        candidate = candidates[grid, prediction]
        require(
            candidate["review_category"] == observation["candidate_review_category"], "Category"
        )
        require(
            not observation["target"]
            and not candidate["target"]
            and case["target"] is None
            and observation["daily_observation_status"] == "unknown"
            and observation["positive_label_permitted"] == "False"
            and observation["negative_label_permitted"] == "False",
            "Unexpected target or acceptance",
        )
        records = components[grid, prediction]
        scenarios = {row["scenario"] for row in records}
        require(
            len(scenarios)
            == int(candidate["scenarios_with_candidate"])
            == float(observation["scenarios_with_candidate"]),
            "Scenario count",
        )
        first_times = sorted({row["first_detection_utc"] for row in records})
        require(
            all(
                prediction < datetime.fromisoformat(time) <= prediction + timedelta(days=1)
                for time in first_times
            ),
            "First time outside target window",
        )
        members = [points[point_id] for point_id in case["point_ids"]]
        require(
            sorted(point["code"] for point in members) == sorted(case["codes"])
            and all(
                unit_id in point["linked_review_units"]
                and point["target"] is None
                and point["event_date_cover_verified"] is False
                for point in members
            ),
            "Point membership or state",
        )
        review.append(
            {
                "review_unit_id": unit_id,
                "grid_id": grid,
                "prediction_utc": prediction.isoformat(),
                "province": observation["primary_province"],
                "season": observation["calendar_season"],
                "grouping": candidate["review_category"],
                "scenarios": len(scenarios),
                "first_times_utc": first_times,
                "first_cells_by_component_record": sorted(
                    {int(row["first_cell_count"]) for row in records}
                ),
                "review_flags": json.loads(candidate["review_flags_json"]),
                "point_ids": case["point_ids"],
                "point_codes": case["codes"],
                "first_point_sensors": sorted(
                    {point["detection_id"].split("_")[0] for point in members}
                ),
                "prior_human_note_points": sum(
                    bool(point["human_note_history"]) for point in members
                ),
                "cell_forest_shrub_fraction_2017": members[0]["prediction_cell_context_2017"][
                    "forest_shrub_fraction"
                ],
                "local_contexts": {point["code"]: point["local_context_2018"] for point in members},
                "observation": {
                    field: float(observation[field])
                    for field in (
                        "nominal_land_fraction",
                        "repeat_12h_fraction",
                        "nominal_land_all_four_bins_fraction",
                        "anypart_land_longest_envelope_gap_seconds",
                    )
                },
                "thermal_witness_count": int(observation["thermal_center_definite_count"]),
                "researcher_cover_review": None,
                "target": None,
            }
        )
    counts = Counter(row["grouping"] for row in review)
    require(counts[STABLE] == 15, "Stable count mismatch")
    require(sum(row["prior_human_note_points"] for row in review) == 10, "Prior notes mismatch")
    require(
        {point_id for row in review for point_id in row["point_ids"]} == points.keys(),
        "Incomplete point coverage",
    )

    # The small visual check spans contrasting contexts. Existing comments
    # guide case selection but do not prefill any researcher answers.
    queue = []
    for context in REVIEW_CONTEXTS:
        options = []
        for row in review:
            if row["grouping"] != STABLE or len(row["point_ids"]) != 1:
                continue
            point = points[row["point_ids"][0]]
            note = point["assistant_visual_note"]
            if point["human_note_history"] or not note or note.get("assistant_group") != context:
                continue
            options.append((row, point, note))
        require(bool(options), f"Missing review context: {context}")
        row, point, note = min(
            options,
            key=lambda item: (
                not any(
                    img["zero_all_selected_quality_flags"] for img in item[1]["image_evidence"]
                ),
                min(img["days_before_prediction"] for img in item[1]["image_evidence"]),
                item[1]["code"],
            ),
        )
        sheet = next(name for name in note["evidence_sha256"] if Path(name).name == note["sheet"])
        pin(pins, ROOT / sheet, note["evidence_sha256"][sheet])
        queue.append(
            {
                "code": point["code"],
                "review_unit_id": row["review_unit_id"],
                "image_sheet": sheet,
                "image_acquired_utc": note["acquired_utc"],
                "researcher_cover_review": None,
            }
        )
    pins[Path(__file__).relative_to(ROOT).as_posix()] = digest(Path(__file__))
    result = {
        "scope": "purpose_selected_pilot_cover_review_only",
        "source_sha256": pins,
        "case_count": len(review),
        "point_count": len(points),
        "grouping_counts": dict(counts),
        "stable_province_counts": dict(
            Counter(row["province"] for row in review if row["grouping"] == STABLE)
        ),
        "stable_season_counts": dict(
            Counter(row["season"] for row in review if row["grouping"] == STABLE)
        ),
        "review_cases": review,
        "human_visual_queue": queue,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    for relative, expected in pins.items():
        require(digest(ROOT / relative) == expected, "Source changed during review")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    path = BASE / "pu_candidate_review_v1" / stamp / "readback.json"
    path.parent.mkdir(parents=True, exist_ok=False)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == result, "JSON readback mismatch")
    print(path.relative_to(ROOT).as_posix(), digest(path))
    print("pins", len(pins), "cases", len(review), "points", len(points))
    print("human visual queue", " ".join(row["code"] for row in queue))


if __name__ == "__main__":
    main()
