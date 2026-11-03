"""Link frozen review evidence without accepting cover, events, targets or exclusions."""

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCES = {
    "areas": (
        "corine_support_review_v1/20261103T214155Z_635f0789/readback.json",
        "20fcc8abd28f541c60fbba7c4dbc9ade10dcf66b976d63ddbfaf33954fd87230",
    ),
    "verification": (
        "corine_support_verification_v1/20261103T214408Z_8d199d94/readback.json",
        "a752caca18482d60b60cfac31def617137cae30bdd11c977a0cb86f318c887df",
    ),
    "images": (
        "habitat_temporal_evidence_audit_v1/20261027T190350Z_207a4734/readback.json",
        "38e03a124e6c5da221ae545941997cb6f34cfd0ff3700bb412b25effc458dda9",
    ),
    "queue": (
        "habitat_decision_queue_v1/20261027T183748Z_e1e64136/readback.json",
        "6cd6b2bbe0dc9ac026219541283af5f339557d2a3e7063fedffa5734337fd236",
    ),
    "new_notes": (
        "habitat_researcher_notes_v2/20261027T184619Z_c71bd189/readback.json",
        "8bf261ccf2c3b9677dc3970b1c1af06c22411dc4b8b36cf24d9bef30f603389e",
    ),
    "spatial": (
        "habitat_spatial_comparison_v1/20261027T185016Z_8d78e5a8/readback.json",
        "5a6de697874a697f7bc37afa7c2d6ddab478edf0d06934a9b2acd7b4fa397288",
    ),
}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def index(records):
    result = {r["detection_id"]: r for r in records}
    require(len(result) == len(records), "Duplicate point identities")
    return result


def main():
    sources, pins = {}, {}
    for role, (relative, digest) in SOURCES.items():
        path = BASE / relative
        require(sha(path) == digest, "Changed source: " + role)
        sources[role] = json.loads(path.read_text(encoding="utf-8"))
        pins[path.relative_to(ROOT).as_posix()] = digest
        labels = sources[role]["labels_created"]
        # The frozen queue reports a count; the other sources report a boolean.
        require(
            (role == "queue" and type(labels) is int and labels == 0)
            or (role != "queue" and labels is False),
            "Unexpected labels",
        )
        require(sources[role]["final_merge_performed"] is False, "Unexpected final merge")
    config = ROOT / "configs/habitat_spatial_review_design_v1.json"
    require(
        sha(config) == "e7ebdbc621aa6e2fc5945db0f86c0c0fc5aa2240fb9ca12c11d14a4dbde4f5f9",
        "Changed design",
    )
    pins[config.relative_to(ROOT).as_posix()] = sha(config)
    pins[Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__))
    areas = index(sources["areas"]["records"])
    queue = index(sources["queue"]["records"])
    spatial = index(sources["spatial"]["points"])
    times = index(sources["images"]["point_requirements"])
    notes = index(sources["new_notes"]["records"])
    require(
        len(areas) == 25 and set(areas) == set(queue) == set(spatial) == set(times), "Membership"
    )
    require(
        {r["detection_id"] for r in sources["verification"]["checks"]} == set(areas), "Area checks"
    )
    require(set(notes) <= set(areas), "Unlinked human note")
    rows = []
    for identity, area in areas.items():
        previous = queue[identity]
        history = previous["human_note_history"][:]
        if identity in notes:
            require(not history, "Expected newly reviewed point")
            history.append({"source": "new_notes", "record": notes[identity]})
        classes = {r["clc_code"] for r in area["classes"]}
        tags = []
        for tag, present in (
            ("mapped_woody_codes", bool(classes & {311, 312, 313, 322, 323, 324})),
            ("agricultural_codes", any(200 <= c < 300 for c in classes)),
            ("natural_agricultural_mosaic_code", bool(classes & {243, 244})),
            ("artificial_codes", any(100 <= c < 200 for c in classes)),
            ("wetland_water_codes", any(400 <= c < 600 for c in classes)),
            ("grass_open_other_codes", bool(classes & {321, 331, 332, 333, 334, 335})),
        ):
            if present:
                tags.append(tag)
        prediction = datetime.fromisoformat(area["prediction_utc"])
        require(2018 <= prediction.year <= 2023, "Closed split")
        image_rows = [
            r for r in sources["images"]["image_evidence"] if r["detection_id"] == identity
        ]
        require(
            {r["prediction_utc"] for r in image_rows} == {area["prediction_utc"]}, "Time alignment"
        )
        require(
            len({r["acquired_utc"] for r in image_rows}) == times[identity]["image_dates"], "Dates"
        )
        blockers = [
            "event_date_natural_vs_managed_cover_unverified",
            "approximate_support_position_uncertainty",
            "cell_and_local_admission_protocol_not_accepted",
        ]
        ref_end = datetime(2018, 12, 31, 23, 59, 59, tzinfo=UTC)
        if prediction <= ref_end:
            blockers.append("map_reference_period_extends_beyond_prediction")
        else:
            blockers.append("map_reference_older_than_prediction")
        if not history:
            blockers.append("researcher_preliminary_note_absent")
        require(previous["target"] is None and area["target"] is None, "Unexpected target")
        rows.append(
            {
                "detection_id": identity,
                "code": area["code"],
                "prediction_utc": area["prediction_utc"],
                "linked_review_units": area["linked_review_units"],
                "prediction_cell_context_2017": {
                    "grid_id": spatial[identity]["grid_id"],
                    "forest_shrub_fraction": spatial[identity]["aoi_cell_forest_shrub_fraction"],
                    "denominator": "study_AOI_intersection_not_assumed_full_25_km2",
                    "aoi_area_km2": spatial[identity]["aoi_cell_area_km2"],
                    "mapped_area_km2": spatial[identity]["aoi_cell_mapped_area_km2"],
                },
                "local_context_2018": {
                    "classes": area["classes"],
                    "center_code": area["center_clc_code"],
                    "largest_area_code": area["dominant_clc_code"],
                    "approximate_area_m2": area["projected_support_area_m2"],
                    "descriptive_tags": tags,
                    "tags_are_not_mutually_exclusive_or_admission": True,
                },
                "human_note_history": history,
                "assistant_visual_note": previous["assistant_note"],
                "image_evidence": image_rows,
                "map_reference_period_extends_beyond_prediction": prediction <= ref_end,
                "event_date_cover_verified": False,
                "open_requirements": blockers,
                "habitat_admission": "undecided",
                "target": None,
                "daily_observation_status": "unknown",
                "negative_label_permitted": False,
                "positive_label_permitted": False,
                "automatic_exclusion": False,
            }
        )
    require(sum(bool(r["human_note_history"]) for r in rows) == 10, "Human coverage")
    cases = []
    for case in sources["queue"]["cases"]:
        members = [r for r in rows if case["review_unit_id"] in r["linked_review_units"]]
        require({r["detection_id"] for r in members} == set(case["point_ids"]), "Case membership")
        cases.append(
            {
                "review_unit_id": case["review_unit_id"],
                "point_ids": case["point_ids"],
                "codes": [r["code"] for r in members],
                "local_contexts_retained_separately": True,
                "habitat_admission": "undecided",
                "target": None,
            }
        )
    result = {
        "version": "habitat_evidence_matrix_v1",
        "source_sha256": pins,
        "rows": rows,
        "cases": cases,
        "summary": {
            "points": len(rows),
            "review_units": len(cases),
            "multi_point_units": sum(len(c["point_ids"]) > 1 for c in cases),
            "human_note_points": sum(bool(r["human_note_history"]) for r in rows),
            "multiple_image_date_points": sum(len(r["image_evidence"]) > 1 for r in rows),
            "map_reference_period_not_fully_before_T_points": sum(
                r["map_reference_period_extends_beyond_prediction"] for r in rows
            ),
            "event_date_cover_verified_points": 0,
            "accepted_habitat_points": 0,
            "nonexclusive_tag_counts": dict(
                Counter(tag for r in rows for tag in r["local_context_2018"]["descriptive_tags"])
            ),
        },
        "historical_map_difference_is_not_land_use_change": True,
        "image_processing_time_is_not_acquisition_time": True,
        "labels_created": False,
        "rows_excluded": 0,
        "final_merge_performed": False,
    }
    require(len(cases) == 21, "Review unit count")
    for relative, expected in pins.items():
        require(sha(ROOT / relative) == expected, "Source changed")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = BASE / "habitat_evidence_matrix_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    report = out / "readback.json"
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    require(json.loads(report.read_text(encoding="utf-8")) == result, "JSON readback")
    print(out.relative_to(ROOT))
    print("report_sha256", sha(report))
    print(json.dumps(result["summary"]))


if __name__ == "__main__":
    main()
