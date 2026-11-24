"""Verify original vertices, existing example keys, result ranges and scientific bytes."""

import csv
import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCE = BASE / "historical_research_prototype_v3/20261124T173653Z_3a064f3e"
PARENT = BASE / "historical_research_prototype_v2/20261123T195053Z_aa61b349"
CASES = BASE / "frozen_rank_case_review_v1/20261124T024256Z_abeb3e00"
RUN = BASE / "source_disjoint_frozen_assessment_v1/20261124T031245Z_91cd329d"
PLAN = BASE / "source_disjoint_evaluation_preparation_v1/20261124T030406Z_9554fb98"


def check(condition, message):
    if not condition:
        raise ValueError(message)


def assignment(name, prefix):
    raw = (SOURCE / name).read_text(encoding="utf-8").strip()
    check(raw.startswith(prefix) and raw.endswith(";"), "Static data assignment")
    return json.loads(raw[len(prefix) : -1])


def rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def vertices(geometry):
    polygons = (
        [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    )
    return [point for polygon in polygons for ring in polygon for point in ring]


def check_path(svg, original, transform):
    check(
        re.fullmatch(r"[MLZ0-9.,\s\-]+", svg) is not None, "Only finite numeric SVG path commands"
    )
    points = [(float(a), float(b)) for a, b in re.findall(r"([-0-9.]+),([-0-9.]+)", svg)]
    expected = vertices(original)
    check(len(points) == len(expected), "All geometry vertices retained")
    maximum = 0.0
    for (x, y), reference in zip(points, expected, strict=True):
        lon = x / transform["x_scale"] + transform["west"]
        lat = transform["north"] - y / transform["y_scale"]
        maximum = max(maximum, abs(lon - reference[0]), abs(lat - reference[1]))
    check(maximum < 1e-7, "Display transform retains original coordinates")
    return len(points), maximum


def main():
    receipt = json.loads((SOURCE / "readback.json").read_bytes())
    pins = {ROOT / name: sha for name, sha in receipt["input_sha256"].items()}
    pins.update({SOURCE / name: sha for name, sha in receipt["artifact_sha256"].items()})
    check(all(digest(p) == sha for p, sha in pins.items()), "Current source and output bytes")
    for name in ("review_data.js", "research-core.js"):
        check(digest(SOURCE / name) == digest(PARENT / name), "Scientific byte copy")
    payload = assignment("review_data.js", "globalThis.RESEARCH_DATA=")
    geo = assignment("geography_data.js", "globalThis.RESEARCH_GEOGRAPHY=")
    context = assignment("research_context.js", "globalThis.RESEARCH_CONTEXT=")
    requested = {r["grid"] for r in payload["records"]}
    grid = json.loads((ROOT / "data/aoi/grid_5km.geojson").read_bytes())
    aoi = json.loads((ROOT / "data/aoi/aoi.geojson").read_bytes())
    by_id = {f["properties"]["grid_id"]: f for f in grid["features"]}
    check(set(geo["cells"]) == requested & set(by_id), "Exact requested grid IDs")
    check(geo["missing_grid_ids"] == sorted(requested - set(by_id)), "Unmapped records retained")
    transform = geo["display_transform"]
    all_points = [point for feature in aoi["features"] for point in vertices(feature["geometry"])]
    west, east = min(p[0] for p in all_points), max(p[0] for p in all_points)
    south, north = min(p[1] for p in all_points), max(p[1] for p in all_points)
    check(
        transform["west"] == west
        and transform["north"] == north
        and transform["x_scale"] == 960 / (east - west)
        and transform["y_scale"]
        == transform["x_scale"] / math.cos(math.radians((south + north) / 2)),
        "Display extent, aspect and north orientation",
    )
    checked_points, maximum_error = 0, 0.0
    for key, cell in geo["cells"].items():
        original = by_id[key]["geometry"]
        count, error = check_path(cell["path"], original, transform)
        checked_points += count
        maximum_error = max(maximum_error, error)
        points = vertices(original)
        b = [
            min(p[0] for p in points),
            min(p[1] for p in points),
            max(p[0] for p in points),
            max(p[1] for p in points),
        ]
        check(cell["wgs84_bounds"] == b, "Full source-cell bounds")
        expected = [
            (b[0] - west) * transform["x_scale"],
            (north - b[3]) * transform["y_scale"],
            (b[2] - west) * transform["x_scale"],
            (north - b[1]) * transform["y_scale"],
        ]
        check(cell["display_bounds"] == expected, "Zoom extent uses the same source cell")
    check(len(geo["areas"]) == len(aoi["features"]), "All existing study area features")
    for svg, original in zip(geo["areas"], aoi["features"], strict=True):
        count, error = check_path(svg, original["geometry"], transform)
        checked_points += count
        maximum_error = max(maximum_error, error)
    original_cases = rows(CASES / "illustrative_cases.csv")
    expected_cases = [
        {
            "case_id": r["case_id"],
            "cohort": r["cohort"],
            "grid": r["grid_id"],
            "time": r["source_prediction_timestamp_utc"],
            "illustrative_tier": r["illustrative_tier"],
        }
        for r in original_cases
    ]
    check(
        context["examples"] == expected_cases and len(expected_cases) == 12,
        "Exact previously selected examples",
    )
    metrics = rows(RUN / "metrics.csv")
    support = rows(PLAN / "planned_support.csv")
    for group in context["overlap_summary"]:
        expected_days = next(
            r
            for r in support
            if r["source_group"] == group["source_group"] and r["slice"] == "all_same_grid_month"
        )
        check(
            group["source_days"] == int(expected_days["eligible_source_anchors"]),
            "Existing source-day count",
        )
        for prefix, section in (("general", "all_same_grid_month"), ("near", "gap_1_to_3_days")):
            values = [
                float(r["auxiliary_pair_AUC"])
                for r in metrics
                if r["source_group"] == group["source_group"]
                and r["variant"] == "primary_weather_XGBoost"
                and r["slice"] == section
            ]
            check(
                len(values) == 9
                and group[prefix + "_min"] == min(values)
                and group[prefix + "_max"] == max(values),
                "Existing nine-scenario ranges",
            )
    for link in context["links"]:
        target = (SOURCE / link["path"]).resolve()
        check(
            target.is_relative_to(ROOT / "docs") and digest(target) == link["sha256"],
            "Local evidence target and hash",
        )
    check(all(digest(p) == sha for p, sha in pins.items()), "Original artifacts unchanged")
    out = (
        BASE
        / "geographic_research_prototype_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    body = {
        "status": "geography_existing_context_and_scientific_byte_copy_verified",
        "mapped_cells": len(geo["cells"]),
        "checked_vertices": checked_points,
        "maximum_inverse_display_error_degrees": maximum_error,
        "examples_verified": 12,
        "existing_range_values_verified": 12,
        "scientific_record_count_unchanged": len(payload["records"]),
        "new_models_predictions_labels_closed_years_or_final_merge": False,
        "actual_browser_visual_render_verified": False,
        "prototype_readback_sha256": digest(SOURCE / "readback.json"),
        "auditor_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), body["status"], flush=True)


if __name__ == "__main__":
    main()
