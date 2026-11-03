"""Measure mapped CORINE classes within frozen approximate detection supports."""

import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from math import ceil, floor
from pathlib import Path
from uuid import uuid4

import rasterio
from pyproj import Transformer
from rasterio.windows import Window
from shapely import segmentize
from shapely.geometry import Polygon, box, mapping
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
DELIVERY = BASE / "corine_delivery_review_v1/20261103T212921Z_3cc30ebb/readback.json"
DELIVERY_SHA = "be52cf11729cec66f84a8abf8d45c3ac9bfaf8d764f68255f2c5ab4ae3b4313f"
GEOMETRY = BASE / "native_candidate_cover_v1/20261023T143656Z_90c1c93b/"
GEOMETRY = GEOMETRY / "approximate_support_geometry.json"
GEOMETRY_SHA = "67a39a83836bbc93bb62bed74ad01af67ce55abd10435789167af21fac813e16"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def class_areas(ds, polygon):
    """Intersect native raster cell squares; include edge-cell partial areas."""
    left, bottom, right, top = polygon.bounds
    inverse = ~ds.transform
    c0, r0 = inverse * (left, top)
    c1, r1 = inverse * (right, bottom)
    c0, r0, c1, r1 = floor(c0), floor(r0), ceil(c1), ceil(r1)
    require(0 <= c0 < c1 <= ds.width and 0 <= r0 < r1 <= ds.height, "Outside map")
    require((c1 - c0) * (r1 - r0) <= 10000, "Unexpected large support")
    values = ds.read(1, window=Window(c0, r0, c1 - c0, r1 - r0))
    areas = defaultdict(float)
    for i in range(values.shape[0]):
        for k in range(values.shape[1]):
            x0, y0 = ds.transform * (c0 + k, r0 + i)
            x1, y1 = ds.transform * (c0 + k + 1, r0 + i + 1)
            area = polygon.intersection(box(x0, y1, x1, y0)).area
            if area > 0:
                areas[int(values[i, k])] += area
    require(abs(sum(areas.values()) - polygon.area) <= max(1e-5, polygon.area * 1e-9), "Area sum")
    return areas


def main():
    require(sha(DELIVERY) == DELIVERY_SHA and sha(GEOMETRY) == GEOMETRY_SHA, "Changed input")
    delivery = json.loads(DELIVERY.read_text(encoding="utf-8"))
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    pins = dict(delivery["source_sha256"])
    pins.update(
        {
            DELIVERY.relative_to(ROOT).as_posix(): DELIVERY_SHA,
            GEOMETRY.relative_to(ROOT).as_posix(): GEOMETRY_SHA,
            Path(__file__).relative_to(ROOT).as_posix(): sha(Path(__file__)),
        }
    )
    for relative, expected in pins.items():
        require(sha(ROOT / relative) == expected, "Changed pinned source")
    require(
        geometry["crs"] == "EPSG:6933" and not geometry["official_corners"], "Support provenance"
    )
    supports = {r["detection_id"]: r for r in geometry["points"]}
    require(len(supports) == len(geometry["points"]) == 25, "Support identities")
    require(set(supports) == {r["detection_id"] for r in delivery["point_results"]}, "Membership")
    raster = next(ROOT / rel for rel in pins if rel.endswith("/" + "U2018_CLC2018_V2020_20u1.tif"))
    records, features = [], []
    with rasterio.open(raster) as ds:
        require(ds.crs.to_wkt() == delivery["raster"]["wkt"], "CRS changed")
        project = Transformer.from_crs(6933, ds.crs, always_xy=True).transform
        for center in delivery["point_results"]:
            identity = center["detection_id"]
            native = Polygon(supports[identity]["approximate_corners_6933"])
            require(native.is_valid and native.area > 0, "Invalid support; do not repair silently")
            coarse = transform(project, segmentize(native, 25))
            fine = transform(project, segmentize(native, 12.5))
            require(fine.is_valid and coarse.is_valid, "Invalid projected support")
            require(abs(fine.area / native.area - 1) < 1e-4, "Equal-area disagreement")
            a25, a12 = class_areas(ds, coarse), class_areas(ds, fine)
            convergence = sum(abs(a25.get(k, 0) - a12.get(k, 0)) for k in a25.keys() | a12.keys())
            convergence /= fine.area
            require(convergence < 5e-6, "Edge densification did not converge")
            classes = []
            unknown = 0
            for value, area in sorted(a12.items()):
                if value == ds.nodata or value == 48:
                    unknown += area
                    continue
                require(str(value) in delivery["legend"] and 1 <= value <= 44, "Unmapped code")
                entry = delivery["legend"][str(value)]
                classes.append({**entry, "raster_value": value, "area_m2": area})
            mapped_area = fine.area - unknown
            for entry in classes:
                entry["fraction_of_entire_support"] = entry["area_m2"] / fine.area
                entry["fraction_of_mapped_support"] = entry["area_m2"] / mapped_area
            dominant = max(classes, key=lambda r: r["area_m2"]) if classes else None
            records.append(
                {
                    "detection_id": identity,
                    "code": center["code"],
                    "prediction_utc": center["prediction_utc"],
                    "linked_review_units": center["linked_review_units"],
                    "center_clc_code": center["corine_class"]["clc_code"],
                    "native_support_area_m2": native.area,
                    "projected_support_area_m2": fine.area,
                    "unknown_area_m2": unknown,
                    "mapped_area_m2": mapped_area,
                    "classes": classes,
                    "dominant_clc_code": dominant["clc_code"] if dominant else None,
                    "mapped_woody_code_fraction": sum(
                        r["area_m2"]
                        for r in classes
                        if r["clc_code"] in {311, 312, 313, 322, 323, 324}
                    )
                    / fine.area,
                    "mapped_agricultural_code_fraction": sum(
                        r["area_m2"] for r in classes if 200 <= r["clc_code"] < 300
                    )
                    / fine.area,
                    "edge_convergence_fraction": convergence,
                    "official_footprint": False,
                    "natural_cover_verified": False,
                    "habitat_admission": "undecided",
                    "target": None,
                    "historical_predictor_use_permitted": False,
                }
            )
            features.append(
                {
                    "type": "Feature",
                    "geometry": mapping(fine),
                    "properties": {
                        "detection_id": identity,
                        "code": center["code"],
                    },
                }
            )
    result = {
        "source_sha256": pins,
        "method": "exact_projected_cell_intersections_with_25m_vs_12.5m_edge_convergence",
        "polygon_crs_wkt": delivery["raster"]["wkt"],
        "denominator": "entire_approximate_support_including_unknown_area",
        "mapped_woody_codes_are_not_natural_cover_acceptance": True,
        "records": records,
        "summary": {
            "points": len(records),
            "review_units": len({u for r in records for u in r["linked_review_units"]}),
            "multi_class_supports": sum(len(r["classes"]) > 1 for r in records),
            "center_differs_from_largest_area_class": sum(
                r["center_clc_code"] != r["dominant_clc_code"] for r in records
            ),
            "supports_with_unknown_area": sum(r["unknown_area_m2"] > 0 for r in records),
            "supports_with_any_mapped_woody_codes": sum(
                r["mapped_woody_code_fraction"] > 0 for r in records
            ),
            "dominant_class_counts": dict(Counter(str(r["dominant_clc_code"]) for r in records)),
            "max_edge_convergence_fraction": max(r["edge_convergence_fraction"] for r in records),
        },
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    for relative, expected in pins.items():
        require(sha(ROOT / relative) == expected, "Source modified during run")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = BASE / "corine_support_review_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    polygon_file = out / "supports.geojson"
    polygon_file.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8"
    )
    result["artifact_sha256"] = {"supports.geojson": sha(polygon_file)}
    report = out / "readback.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(json.loads(report.read_text()) == result, "JSON readback")
    print(out.relative_to(ROOT))
    print("report_sha256", sha(report))
    print(json.dumps(result["summary"]))
    for row in records:
        print(
            row["code"],
            [
                (r["clc_code"], round(r["fraction_of_entire_support"] * 100, 2))
                for r in row["classes"]
            ],
        )


if __name__ == "__main__":
    main()
