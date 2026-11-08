"""Compare historical CORINE centres, retained supports and nominal rotated rectangles."""

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import rasterio
from measure_corine_review_supports import class_areas, require, sha
from pyproj import Transformer
from shapely.affinity import rotate
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
BASE = "outputs/reports/dataset"
PUBLIC = f"{BASE}/public_event_cover_v1/20261107T233443Z_6e504fcb/readback.json"
FIXED = f"{BASE}/corine_support_review_v1/20261103T214155Z_635f0789/readback.json"
SOURCE = "data/interim/firms_combined_candidates_2018_2024.csv"
WOODY = {311, 312, 313, 322, 323, 324}
WATER = {511, 512, 521, 522, 523}
CUTS = (0.01, 0.10, 0.50)


def rotation_ranges(ds, x, y, width, height, codes):
    rectangle = box(x - width / 2, y - height / 2, x + width / 2, y + height / 2)
    woody, water, unknown = [], [], []
    for angle in range(180):
        shape = rotate(rectangle, angle, origin=(x, y))
        classes = class_areas(ds, shape)
        require(
            all(value in codes or value in {48, ds.nodata} for value in classes), "Raster class"
        )
        woody.append(
            sum(a for value, a in classes.items() if codes.get(value) in WOODY) / shape.area
        )
        water.append(
            sum(a for value, a in classes.items() if codes.get(value) in WATER) / shape.area
        )
        unknown.append(sum(a for value, a in classes.items() if value not in codes) / shape.area)
    return {
        "woody_fraction": [min(woody), max(woody)],
        "water_fraction": [min(water), max(water)],
        "unknown_fraction": [min(unknown), max(unknown)],
    }


def summarize(rows):
    center = sum(row["center_clc"] in WOODY for row in rows)
    result = {"points": len(rows), "woody_center": center, "cuts": {}}
    for cut in CUTS:
        counts = Counter()
        for row in rows:
            lo, hi = row["nominal"]["woody_fraction"]
            key = (
                "all_directions"
                if lo >= cut
                else "some_directions"
                if hi >= cut
                else "no_direction"
            )
            counts[key] += 1
            if key == "all_directions" and row["center_clc"] not in WOODY:
                counts["center_nonwoody_but_all_directions"] += 1
            if key == "no_direction" and row["center_clc"] in WOODY:
                counts["center_woody_but_no_direction"] += 1
            fixed = row["retained_woody_fraction"]
            if fixed is not None:
                counts["retained_at_or_above"] += int(fixed >= cut)
                counts["center_vs_retained_disagreement"] += int(
                    (row["center_clc"] in WOODY) != (fixed >= cut)
                )
                counts["retained_vs_all_nominal_disagreement"] += int(
                    (fixed < cut and key == "all_directions")
                    or (fixed >= cut and key == "no_direction")
                )
        result["cuts"][str(cut)] = dict(sorted(counts.items()))
    return result


def main():
    pins = {}

    def retain(name, expected=None):
        path = ROOT / name
        require(path.resolve(strict=True).is_relative_to(ROOT), "Contained input")
        actual = sha(path)
        require(expected is None or actual == expected, "Changed input")
        pins[name] = actual
        return path

    def read(name, expected):
        return json.loads(retain(name, expected).read_text(encoding="utf-8"))

    public = read(PUBLIC, "aa0ad0e753d04be890837c7f5e46f7d2ac03ba1ecf9c6e183016946f30bfe38e")
    fixed = read(FIXED, "20fcc8abd28f541c60fbba7c4dbc9ade10dcf66b976d63ddbfaf33954fd87230")
    public_rows = {p["id"]: p for p in public["first_points"]}
    fixed_rows = {p["detection_id"]: p for p in fixed["records"]}
    require(len(public_rows) == 46 and len(fixed_rows) == 25, "Point denominators")
    ids = public_rows.keys() | fixed_rows.keys()
    require(len(ids) == 71, "Disjoint point cohorts")
    with retain(SOURCE, public["source_sha256"][SOURCE]).open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        source = {}
        for record in csv.DictReader(stream):
            key = record["detection_id"]
            if key in ids:
                require(
                    key not in source and "2018" <= record["acq_date"][:4] <= "2023",
                    "Source identity and split",
                )
                source[key] = record
    require(source.keys() == ids, "Complete original centres")
    delivery = next(
        name
        for name in public["source_sha256"]
        if name.endswith("/readback.json") and "/corine_delivery_review_v1/" in name
    )
    raster = next(name for name in public["source_sha256"] if name.endswith("20u1.tif"))
    require(
        fixed["source_sha256"][raster] == public["source_sha256"][raster], "Common CORINE raster"
    )
    legend = read(delivery, public["source_sha256"][delivery])["legend"]
    codes = {int(k): int(v["clc_code"]) for k, v in legend.items() if 1 <= int(k) <= 44}
    project = Transformer.from_crs(4326, 3035, always_xy=True)
    rows = []
    with rasterio.open(retain(raster, public["source_sha256"][raster])) as ds:
        for key in sorted(ids):
            original = source[key]
            lon, lat = float(original["longitude"]), float(original["latitude"])
            x, y = project.transform(lon, lat)
            scan, track = float(original["scan"]) * 1000, float(original["track"]) * 1000
            require(0 < scan < 2000 and 0 < track < 2000, "Finite reported dimensions")
            center_clc = codes[int(next(ds.sample([(x, y)]))[0])]
            retained = fixed_rows.get(key)
            if retained is None:
                point = public_rows[key]
                require(
                    (lon, lat) == (point["longitude"], point["latitude"])
                    and original["grid_id"] == point["grid"]
                    and original["acq_date"] == point["day"]
                    and center_clc == point["corine_2018"]["clc_code"],
                    "Public point identity",
                )
                cohort, code, fraction = point["case"], None, None
            else:
                require(
                    retained["target"] is None and not retained["official_footprint"],
                    "Review-only input",
                )
                cohort, code = "method_pilot", retained["code"]
                fraction = retained["mapped_woody_code_fraction"]
            nominal = rotation_ranges(ds, x, y, scan, track, codes)
            rows.append(
                {
                    "id": key,
                    "cohort": cohort,
                    "code": code,
                    "day": original["acq_date"],
                    "grid": original["grid_id"],
                    "center_clc": center_clc,
                    "retained_center_clc": retained["center_clc_code"] if retained else None,
                    "retained_woody_fraction": fraction,
                    "nominal": nominal,
                }
            )
    for name in (
        Path(__file__).relative_to(ROOT).as_posix(),
        "scripts/quality/measure_corine_review_supports.py",
    ):
        retain(name)
    require(all(sha(ROOT / name) == expected for name, expected in pins.items()), "Inputs changed")
    result = {
        "source_sha256": pins,
        "angle_step_deg": 1,
        "angles_per_point": 180,
        "fraction_denominator": "entire_nominal_rectangle_in_epsg3035",
        "descriptive_cuts": list(CUTS),
        "cohorts": {
            cohort: summarize([r for r in rows if r["cohort"] == cohort])
            for cohort in sorted({r["cohort"] for r in rows})
        },
        "points": rows,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "positive_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = ROOT / BASE / "candidate_center_footprint_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    receipt = out / "readback.json"
    receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(receipt.read_text(encoding="utf-8")) == result, "Readback identity")
    print(receipt.relative_to(ROOT).as_posix(), sha(receipt))
    print(json.dumps(result["cohorts"], indent=2))


if __name__ == "__main__":
    main()
