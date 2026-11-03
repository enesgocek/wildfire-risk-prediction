"""Independently verify local support areas with exactextract and render six cases."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET

import geopandas as gpd
import matplotlib
import rasterio
from exactextract import exact_extract
from matplotlib.colors import ListedColormap
from rasterio.windows import from_bounds
from shapely.geometry import shape

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCE = BASE / "corine_support_review_v1/20261103T214155Z_635f0789/readback.json"
EXPECTED = "20fcc8abd28f541c60fbba7c4dbc9ade10dcf66b976d63ddbfaf33954fd87230"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    require(sha(SOURCE) == EXPECTED, "Changed area report")
    source = json.loads(SOURCE.read_text())
    pins = dict(source["source_sha256"])
    pins[SOURCE.relative_to(ROOT).as_posix()] = EXPECTED
    polygons = SOURCE.parent / "supports.geojson"
    pins[polygons.relative_to(ROOT).as_posix()] = source["artifact_sha256"][polygons.name]
    pins[Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__))
    for relative, expected in pins.items():
        require(sha(ROOT / relative) == expected, "Changed source")
    features = json.loads(polygons.read_text())["features"]
    raster = next(ROOT / p for p in pins if p.endswith("U2018_CLC2018_V2020_20u1.tif"))
    qml = next(ROOT / p for p in pins if p.endswith("clc_legend_qgis_raster.qml"))
    colors = ["white"] * 128
    for entry in ET.parse(qml).findall(".//paletteEntry"):
        colors[int(entry.attrib["value"])] = entry.attrib["color"]
    records = {r["detection_id"]: r for r in source["records"]}
    checks = []
    with rasterio.open(raster) as ds:
        frame = gpd.GeoDataFrame.from_features(features, crs=ds.crs)
        independent = exact_extract(
            ds, frame, ["unique", "frac", "count"], include_cols=["detection_id"]
        )
        for feature in independent:
            row = feature["properties"]
            reference = records[row["detection_id"]]
            require(reference["unknown_area_m2"] == 0, "Unexpected unmapped area")
            expected = {r["raster_value"]: r for r in reference["classes"]}
            actual = dict(zip(map(int, row["unique"]), map(float, row["frac"]), strict=True))
            require(set(actual) == set(expected), "Class membership disagreement")
            error = max(
                abs(v - expected[k]["fraction_of_entire_support"]) for k, v in actual.items()
            )
            area_error = abs(row["count"] * 10000 - reference["projected_support_area_m2"])
            require(
                error < 1e-6 and area_error / reference["projected_support_area_m2"] < 1e-6,
                "Independent area disagreement",
            )
            checks.append(
                {
                    "detection_id": row["detection_id"],
                    "fraction_error": error,
                    "area_error_m2": area_error,
                }
            )
        require(len(checks) == len({r["detection_id"] for r in checks}) == 25, "Check identities")
        fig, axes = plt.subplots(2, 3, figsize=(14, 11.7))
        for ax, code in zip(axes.flat, ("C", "D", "E", "F", "R03", "R11"), strict=True):
            record = next(r for r in records.values() if r["code"] == code)
            polygon = shape(
                next(f["geometry"] for f in features if f["properties"]["code"] == code)
            )
            x, y = polygon.centroid.coords[0]
            # Center marker is the native observation center, not polygon centroid.
            delivery = next(
                ROOT / p
                for p in pins
                if "corine_delivery_review_v1" in p and p.endswith("readback.json")
            )
            center = next(
                r["raster_xy"]
                for r in json.loads(delivery.read_text())["point_results"]
                if r["code"] == code
            )
            extent = (
                max(
                    1000,
                    polygon.bounds[2] - polygon.bounds[0] + 300,
                    polygon.bounds[3] - polygon.bounds[1] + 300,
                )
                / 2
            )
            window = from_bounds(x - extent, y - extent, x + extent, y + extent, ds.transform)
            window = window.round_offsets().round_lengths()
            image = ds.read(1, window=window, masked=True)
            t = ds.window_transform(window)
            ax.imshow(
                image,
                cmap=ListedColormap(colors),
                vmin=0,
                vmax=127,
                extent=(t.c, t.c + image.shape[1] * 100, t.f - image.shape[0] * 100, t.f),
                interpolation="nearest",
            )
            ax.plot(*polygon.exterior.xy, color="black", linewidth=2)
            ax.plot(center[0], center[1], marker="x", color="blue", markersize=9)
            ax.set_title(
                code
                + " | "
                + ", ".join(
                    f"{r['clc_code']}: {r['fraction_of_entire_support'] * 100:.1f}%"
                    for r in sorted(record["classes"], key=lambda r: -r["area_m2"])
                    if r["fraction_of_entire_support"] >= 0.001
                ),
                fontsize=10,
            )
            ax.set_xticks([])
            ax.set_yticks([])
        fig.suptitle(
            "CORINE 2018 | black: approximate support | blue x: detection center\n"
            "Mapped context only; not a fire perimeter or accepted label",
            fontsize=13,
        )
        fig.subplots_adjust(left=0.02, right=0.98, bottom=0.03, top=0.88, wspace=0.07, hspace=0.18)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
        out = BASE / "corine_support_verification_v1" / stamp
        out.mkdir(parents=True, exist_ok=False)
        figure = out / "six_supports.png"
        fig.savefig(figure, dpi=160)
        plt.close(fig)
    result = {
        "source_sha256": pins,
        "method": "exactextract independent cell coverage",
        "checks": checks,
        "points": 25,
        "max_fraction_error": max(r["fraction_error"] for r in checks),
        "max_area_error_m2": max(r["area_error_m2"] for r in checks),
        "artifact_sha256": {figure.name: sha(figure)},
        "labels_created": False,
        "final_merge_performed": False,
    }
    for relative, expected in pins.items():
        require(sha(ROOT / relative) == expected, "Source changed during verification")
    report = out / "readback.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(json.loads(report.read_text()) == result, "JSON readback")
    print(out.relative_to(ROOT))
    print("report_sha256", sha(report))
    print(
        "max_fraction_error",
        result["max_fraction_error"],
        "max_area_error_m2",
        result["max_area_error_m2"],
    )


if __name__ == "__main__":
    main()
