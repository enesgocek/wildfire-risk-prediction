"""Separate source-marker and first-detection cover context; never admit labels."""

import hashlib
import json
from datetime import UTC, datetime
from math import pi
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import rasterio
from exactextract import exact_extract
from measure_corine_review_supports import class_areas
from pyproj import Transformer
from shapely.geometry import Point
from shapely.ops import transform

from wildfire_risk_prediction.native_cover_context import overlap_reference_map
from wildfire_risk_prediction.point_cover_context import cover_group
from wildfire_risk_prediction.target_admission import specification

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCE = BASE / "public_start_geometry_v1/forestry_chamber_2021"
MARKER = SOURCE / "salur_marker_v1/20261108T194701Z_a7895f19/readback.json"
CONTEXT = BASE / "salur_event_context_v1/20261118T230221Z_cab0c9e1"
DELIVERY = BASE / "corine_delivery_review_v1/20261103T212921Z_3cc30ebb"
CGLS = ROOT / "data/raw/landcover/landcover_copernicus_2017.tif"
CORINE = DELIVERY / "source/DATA/U2018_CLC2018_V2020_20u1.tif"
VISUAL = SOURCE / "pre_event_ortho/visual.tif"
PINS = {
    MARKER: "fa15c440eb6a025aada777cab58544c23ba5083302ede626adb45a222da788d8",
    CONTEXT / "readback.json": "89ffb290079ae4167cbf3b577e9787cbbde5092118acaab0d43d704189dad846",
    CONTEXT
    / "local_detections.csv": "2b28fed54408fd32495d3f925efa33c25f0145c0793284bb8afe6ebe87379199",
    DELIVERY / "readback.json": "be52cf11729cec66f84a8abf8d45c3ac9bfaf8d764f68255f2c5ab4ae3b4313f",
    CGLS: "ee8bd6c9f742dbbdfcdcbbb6ecc446499f05d676eaeb202c4345c11ea6006470",
    CORINE: "69057d527b4338b89f58cf15693effcf18017611ff48144e5c491d083cf1b004",
    VISUAL: "1dbcd7837402476f7ed7029550a3ac7cf034a6ea98efc9b12740981ad41f37bd",
    SOURCE / "pre_event_ortho/metadata.json": (
        "bc04f228a5acb078705ec02ffd5db62d94e639b10fc8778af3b449cec541ebc2"
    ),
}
WOODY = {311, 312, 313, 322, 323, 324}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sample(ds, xy):
    x, y = Transformer.from_crs(4326, ds.crs, always_xy=True).transform(*xy)
    row, col = ds.index(x, y)
    require(0 <= row < ds.height and 0 <= col < ds.width, "Point outside retained raster")
    value = next(ds.sample([(x, y)], masked=True))[0]
    require(not np.ma.is_masked(value), "Unmapped center; preserve before interpreting")
    return int(value)


def render(out, centers, detections):
    with rasterio.open(VISUAL) as ds:
        require(ds.count == 3 and ds.crs.to_epsg() == 32636, "Retained RGB CRS")
        rgb = ds.read().transpose(1, 2, 0)
        require(rgb.dtype == np.uint8, "Use retained true-color bytes without stretching")
        extent = (ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top)
        project = Transformer.from_crs(4326, ds.crs, always_xy=True).transform
        area_to_rgb = Transformer.from_crs(6933, ds.crs, always_xy=True).transform
        marker, first = centers[0], centers[2]
        fig, axes = plt.subplots(1, 3, figsize=(15, 6.1))
        xy = np.array([project(r.longitude, r.latitude) for r in detections.itertuples()])
        for ax in axes:
            ax.imshow(rgb, extent=extent, origin="upper", interpolation="nearest")
            ax.scatter(*xy.T, s=14, facecolors="none", edgecolors="white", linewidths=0.7)
            for label, record, color in [("A", marker, "yellow"), ("B", first, "cyan")]:
                x, y = project(*record["lon_lat"])
                ax.scatter(x, y, marker="+", color=color, s=120, linewidths=1.5)
                ax.text(
                    x + 25, y + 25, label, color=color, weight="bold", fontsize=12, clip_on=True
                )
                polygon = transform(
                    area_to_rgb, Point(record["xy_6933"]).buffer(250, quad_segs=128)
                )
                ax.plot(*polygon.exterior.xy, color=color, linewidth=1.0)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
        mx, my = project(*marker["lon_lat"])
        bx, by = project(*first["lon_lat"])
        frames = [(mx, my, 1300), (mx, my, 500), (bx, by, 500)]
        for ax, (x, y, half) in zip(axes, frames, strict=True):
            require(
                ds.bounds.left <= x - half < x + half <= ds.bounds.right
                and ds.bounds.bottom <= y - half < y + half <= ds.bounds.top,
                "Crop would exceed image; no silent padding",
            )
            ax.set_xlim(x - half, x + half)
            ax.set_ylim(y - half, y + half)
            ax.plot(
                [x - half * 0.8, x - half * 0.8 + 200], [y - half * 0.8] * 2, color="white", lw=3
            )
            ax.text(x - half * 0.8, y - half * 0.8 + 25, "200 m", color="white", fontsize=9)
        for ax, title in zip(
            axes,
            [
                "Salur: konum bağlamı",
                "A: rapor işareti çevresi",
                "B: ilk yerel tespit merkezi çevresi",
            ],
            strict=True,
        ):
            ax.set_title(title, fontsize=11)
        fig.suptitle("Olay öncesi Sentinel-2B • 20 Temmuz 2021 • 10 m RGB", fontsize=14)
        fig.text(
            0.5,
            0.1,
            "A: iki harita uyumundan biri • B: 28 Temmuz 10.12 UTC, NOAA-20\n"
            "Çemberler: 250 m inceleme çevresi; "
            "piksel sınırı veya doğrulanmış konum hatası değil.\n"
            "Beyaz halkalar: aynı gün 1 km çevredeki 11 katalog merkezi. "
            "İnsan örtü incelemesi bekleniyor.",
            ha="center",
            fontsize=10,
        )
        fig.subplots_adjust(top=0.87, bottom=0.23, wspace=0.08)
        path = out / "salur_cover_review.png"
        fig.savefig(path, dpi=160, facecolor="white")
        plt.close(fig)
        return path


def main():
    for path, expected in PINS.items():
        require(sha(path) == expected, f"Changed pinned input: {path.name}")
    marker = json.loads(MARKER.read_text())
    context = json.loads((CONTEXT / "readback.json").read_text())
    delivery = json.loads((DELIVERY / "readback.json").read_text())
    detections = pd.read_csv(CONTEXT / "local_detections.csv")
    require(len(detections) == 11 and detections.detection_id.is_unique, "Local identities")
    require(detections.target.isna().all(), "No admitted labels")
    dates = pd.to_datetime(detections.detection_timestamp_utc, utc=True)
    require(
        dates.between(
            pd.Timestamp("2021-07-28", tz="UTC"),
            pd.Timestamp("2021-07-29", tz="UTC"),
            inclusive="left",
        ).all(),
        "Case day only",
    )
    first = detections.loc[dates.eq(dates.min())]
    require(
        len(first) == 1 and list(first.detection_id) == context["first_local_ids"],
        "First local identity",
    )
    project = Transformer.from_crs(4326, 6933, always_xy=True).transform
    centers = [
        {"id": key, "role": "source_marker_fit", "lon_lat": value["marker_lon_lat"]}
        for key, value in marker["estimates"].items()
    ]
    require(len(centers) == 2, "Two alternative fits, not two events")
    centers.append(
        {
            "id": first.iloc[0].detection_id,
            "role": "first_local_catalog_center",
            "lon_lat": [float(first.iloc[0].longitude), float(first.iloc[0].latitude)],
        }
    )
    records, polygons = [], []
    with rasterio.open(CGLS) as cgls, rasterio.open(CORINE) as corine:
        require(corine.crs.to_wkt() == delivery["raster"]["wkt"], "Original CORINE CRS")
        to_corine = Transformer.from_crs(6933, corine.crs, always_xy=True).transform
        for center in centers:
            center["xy_6933"] = list(project(*center["lon_lat"]))
            center["cgls_2017_center_group"] = cover_group(sample(cgls, center["lon_lat"]))
            value = sample(corine, center["lon_lat"])
            require(str(value) in delivery["legend"], "CORINE center class translation")
            center["corine_2018_center"] = delivery["legend"][str(value)]
            for radius in (100, 250, 500):
                circle = Point(center["xy_6933"]).buffer(radius, quad_segs=256)
                require(abs(circle.area / (pi * radius**2) - 1) < 1e-5, "Circle approximation")
                old_map = overlap_reference_map(circle, cgls)
                polygon = transform(to_corine, circle)
                require(abs(polygon.area / circle.area - 1) < 1e-4, "Equal-area projection")
                areas = class_areas(corine, polygon)
                require(
                    all(str(v) in delivery["legend"] for v in areas),
                    "Unknown map area; preserve before interpreting",
                )
                classes = [
                    {
                        **delivery["legend"][str(v)],
                        "raster_value": v,
                        "area_m2": a,
                        "fraction_of_circle": a / polygon.area,
                    }
                    for v, a in sorted(areas.items())
                ]
                records.append(
                    {
                        "center_id": center["id"],
                        "radius_m": radius,
                        "geometry_is_sensitivity_circle_only": True,
                        "radius_is_measured_location_error_bound": False,
                        "official_detection_footprint": False,
                        "cgls_2017": old_map,
                        "corine_2018": {
                            "area_m2": polygon.area,
                            "classes": classes,
                            "woody_code_fraction": sum(
                                r["fraction_of_circle"] for r in classes if r["clc_code"] in WOODY
                            ),
                        },
                        "natural_cover_verified": False,
                        "target": None,
                    }
                )
                polygons.append(polygon)
        frame = gpd.GeoDataFrame({"geometry": polygons}, crs=corine.crs)
        independent = exact_extract(corine, frame, ["unique", "frac", "count"])
        checks = []
        for record, actual in zip(records, independent, strict=True):
            reference = {
                r["raster_value"]: r["fraction_of_circle"] for r in record["corine_2018"]["classes"]
            }
            actual = actual["properties"]
            fractions = dict(
                zip(map(int, actual["unique"]), map(float, actual["frac"]), strict=True)
            )
            require(set(fractions) == set(reference), "Independent class set")
            error = max(abs(fractions[k] - reference[k]) for k in fractions)
            area_error = abs(
                actual["count"]
                * abs(corine.transform.a * corine.transform.e)
                / record["corine_2018"]["area_m2"]
                - 1
            )
            require(error < 1e-6 and area_error < 1e-6, "Independent area check")
            checks.append({"max_fraction_error": error, "relative_area_error": area_error})
    gate = specification()
    require(
        gate["daily_observation_status"] == "unknown"
        and not any(
            gate[k] for k in ("positive_label_permitted", "negative_label_permitted", "model_ready")
        ),
        "Closed gate",
    )
    out = (
        BASE
        / "salur_local_cover_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    figure = render(out, centers, detections)
    code = [
        Path(__file__),
        ROOT / "scripts/quality/measure_corine_review_supports.py",
        ROOT / "src/wildfire_risk_prediction/native_cover_context.py",
        ROOT / "src/wildfire_risk_prediction/point_cover_context.py",
    ]
    result = {
        "scope": "one_2021_case_pre_event_cover_review_only",
        "input_sha256": {p.relative_to(ROOT).as_posix(): s for p, s in PINS.items()},
        "code_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in code},
        "artifact_sha256": {figure.name: sha(figure)},
        "centers": centers,
        "records": records,
        "independent_corine_checks": checks,
        "rgb_quality_limit": "Retained RGB only; no per-pixel SCL/cloud/shadow clearance claimed",
        "human_review": "pending",
        "habitat_admission": "undecided",
        "gate": gate,
        "labels_created": False,
        "model_trained": False,
        "final_merge_performed": False,
        "heldout_data_read": False,
    }
    for path, expected in PINS.items():
        require(sha(path) == expected, "Source changed during run")
    report = out / "readback.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(json.loads(report.read_text(encoding="utf-8")) == result, "JSON readback")
    print(out.relative_to(ROOT))
    print("report_sha256", sha(report))
    for r in records:
        print(
            r["center_id"],
            r["radius_m"],
            "CGLS",
            round(r["cgls_2017"]["forest_shrub_fraction_of_entire_support"], 4),
            "CORINE",
            round(r["corine_2018"]["woody_code_fraction"], 4),
        )
    print("PASS nine independent CORINE area checks; human review pending, no labels")


if __name__ == "__main__":
    main()
