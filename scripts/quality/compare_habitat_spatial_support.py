"""Compare frozen 2017 cover at center, approximate footprint and AOI-cell scales.

Offline descriptive analysis of a purpose-selected cohort, never an admission rule.
"""

import csv
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCES = {
    "native": (
        "native_candidate_cover_v1/20261023T143656Z_90c1c93b",
        "65443618bddc95f01a453f0186473891112d9712b50289e3c4613ac71470568b",
    ),
    "context": (
        "linked_candidate_context_v1/20261022T210339Z_23e2e5a4",
        "58363f7e1640af945195ecf9d13144a5ec4951fb259a30816274c12956710de8",
    ),
    "queue": (
        "habitat_decision_queue_v1/20261027T183748Z_e1e64136",
        "6cd6b2bbe0dc9ac026219541283af5f339557d2a3e7063fedffa5734337fd236",
    ),
    "human": (
        "habitat_researcher_notes_v2/20261027T184619Z_c71bd189",
        "8bf261ccf2c3b9677dc3970b1c1af06c22411dc4b8b36cf24d9bef30f603389e",
    ),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fraction(value):
    number = float(value)
    require(math.isfinite(number) and 0 <= number <= 1, "Invalid cover fraction")
    return number


def index(rows, key):
    result = {r[key]: r for r in rows}
    require(len(result) == len(rows) and all(result), "Duplicate or empty keys")
    return result


def main():
    pins, reports = {}, {}

    def pin(path, expected):
        require(sha(path) == expected, "Changed input: " + path.name)
        pins[path.relative_to(ROOT).as_posix()] = expected

    for role, (folder, expected) in SOURCES.items():
        path = BASE / folder / "readback.json"
        pin(path, expected)
        reports[role] = json.loads(path.read_text(encoding="utf-8"))
    pin(Path(__file__), sha(Path(__file__)))

    def table(role, filename):
        path = BASE / SOURCES[role][0] / filename
        pin(path, reports[role]["artifact_sha256"][filename])
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    native = index(table("native", "native_point_context.csv"), "detection_id")
    cases = index(table("context", "case_cover_reference_context.csv"), "review_unit_id")
    queue = index(reports["queue"]["records"], "detection_id")
    require(set(queue) == set(native) and len(native) == 25, "Point coverage changed")
    require(len(cases) == 21, "Case coverage changed")
    human = {r["detection_id"] for r in queue.values() if r["human_note_history"]}
    human.update(r["detection_id"] for r in reports["human"]["records"])
    require(len(human) == 10 and human <= set(native), "Human note coverage changed")
    for r in native.values():
        require(r["reference_year"] == "2017" and not r["target"], "Native scope")
        for key in (
            "habitat_label_accepted",
            "positive_label_permitted",
            "negative_label_permitted",
        ):
            require(r[key] == "False", "Native acceptance changed")
    for r in cases.values():
        require(r["reference_year"] == "2017" and not r["target"], "Case scope")
        require(r["daily_observation_status"] == "unknown", "Observation state changed")
        for key in (
            "habitat_eligibility_accepted",
            "positive_label_permitted",
            "negative_label_permitted",
        ):
            require(r[key] == "False", "Case acceptance changed")

    points = []
    for identity, r in sorted(native.items()):
        q = queue[identity]
        require(len(q["linked_review_units"]) == 1, "Explicit multi-case handling required")
        case_id = q["linked_review_units"][0]
        require(case_id in cases and cases[case_id]["grid_id"] == r["grid_id"], "Spatial join")
        c = cases[case_id]
        require(
            r["detection_timestamp_utc"][:4] in {str(y) for y in range(2018, 2024)}, "Training only"
        )
        support = fraction(r["forest_shrub_fraction_of_entire_support"])
        grid = fraction(float(c["forest_fraction"]) + float(c["shrub_fraction"]))
        support_area = float(r["approximate_support_area_m2"])
        cover_area = float(r["forest_shrub_reference_area_m2"])
        require(math.isfinite(support_area) and support_area > 0, "Support area")
        require(
            math.isclose(support, cover_area / support_area, abs_tol=1e-9), "Denominator mismatch"
        )
        points.append(
            {
                "detection_id": identity,
                "code": q["code"],
                "review_unit_id": case_id,
                "grid_id": r["grid_id"],
                "year": int(r["detection_timestamp_utc"][:4]),
                "center_cover_2017": r["center_cover_group_2017"],
                "center_forest_shrub": r["center_cover_group_2017"] in ("forest", "shrub"),
                "support_forest_shrub_fraction": support,
                "aoi_cell_forest_shrub_fraction": grid,
                "aoi_cell_mapped_area_km2": float(c["covered_area_km2"]),
                "aoi_cell_area_km2": float(c["aoi_area_km2"]),
                "researcher_preliminary_note_present": identity in human,
                "habitat_admission": "undecided",
                "target": None,
            }
        )
    case_rows = []
    for identity, case in sorted(cases.items()):
        members = [r for r in points if r["review_unit_id"] == identity]
        require(len(members) == int(case["unique_first_detection_points"]), "Member coverage")
        require(bool(members), "Empty case")
        case_rows.append(
            {
                "review_unit_id": identity,
                "point_codes": [r["code"] for r in members],
                "any_center_forest_shrub": any(r["center_forest_shrub"] for r in members),
                "all_centers_forest_shrub": all(r["center_forest_shrub"] for r in members),
                "any_support_overlap": any(r["support_forest_shrub_fraction"] > 0 for r in members),
                "all_supports_overlap": all(
                    r["support_forest_shrub_fraction"] > 0 for r in members
                ),
                "any_support_majority": any(
                    r["support_forest_shrub_fraction"] >= 0.5 for r in members
                ),
                "aoi_cell_forest_shrub_fraction": members[0]["aoi_cell_forest_shrub_fraction"],
            }
        )
    summary = {
        "point_count": len(points),
        "case_count": len(case_rows),
        "unique_grid_count": len({r["grid_id"] for r in points}),
        "center_forest_shrub_points": sum(r["center_forest_shrub"] for r in points),
        "support_overlap_points": sum(r["support_forest_shrub_fraction"] > 0 for r in points),
        "support_majority_points": sum(r["support_forest_shrub_fraction"] >= 0.5 for r in points),
        "cell_overlap_cases": sum(r["aoi_cell_forest_shrub_fraction"] > 0 for r in case_rows),
        "cell_majority_cases": sum(r["aoi_cell_forest_shrub_fraction"] >= 0.5 for r in case_rows),
        "cell_overlap_without_any_point_overlap_cases": sum(
            r["aoi_cell_forest_shrub_fraction"] > 0 and not r["any_support_overlap"]
            for r in case_rows
        ),
        "cell_majority_without_any_point_overlap_cases": sum(
            r["aoi_cell_forest_shrub_fraction"] >= 0.5 and not r["any_support_overlap"]
            for r in case_rows
        ),
        **{
            key + "_cases": sum(r[key] for r in case_rows)
            for key in (
                "any_center_forest_shrub",
                "all_centers_forest_shrub",
                "any_support_overlap",
                "all_supports_overlap",
                "any_support_majority",
            )
        },
    }
    result = {
        "version": "habitat_spatial_comparison_v1",
        "reference_year": 2017,
        "summary": summary,
        "points": points,
        "cases": case_rows,
        "source_sha256": pins,
        "denominators": {
            "support": "entire_approximate_native_support",
            "cell": "mapped_area_of_grid_intersection_with_study_AOI",
        },
        "diagnostic_cuts": {"overlap": "> 0", "majority": ">= 0.5"},
        "thresholds_are_admission_rules": False,
        "purpose_selected_cohort": True,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "rows_excluded": 0,
        "final_merge_performed": False,
    }
    out = (
        BASE
        / "habitat_spatial_comparison_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == result, "Readback mismatch")
    for name, expected in list(pins.items()):
        pin(ROOT / name, expected)
    print(out.relative_to(ROOT))
    print(sha(path))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
