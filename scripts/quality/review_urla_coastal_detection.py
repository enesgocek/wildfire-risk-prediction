"""Audit one coastal FIRMS centre with rotation sensitivity and dated optical windows."""

import csv
import json
from collections import defaultdict
from datetime import UTC, datetime
from math import hypot
from pathlib import Path
from uuid import uuid4

import rasterio
import requests
from numpy.ma import is_masked
from pyproj import Transformer
from rasterio.plot import plotting_extent
from rasterio.windows import Window
from review_public_event_cover import catalogue, plt, sha
from shapely.affinity import rotate
from shapely.geometry import Point, box
from shapely.ops import transform, unary_union

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.point_cover_context import cover_group
from wildfire_risk_prediction.preevent_imagery import utc_time
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows

ROOT = Path(__file__).resolve().parents[2]
BASE = "outputs/reports/dataset"
PARENT = f"{BASE}/public_event_cover_v1/20261107T233443Z_6e504fcb/readback.json"
ID = "SNPP_815579_146706"
UTM = 32635


def raster_patches(ds, xy, radius, crs, classify):
    """Convert native raster cells to local metric polygons, retaining unmapped cells."""
    projected = Transformer.from_crs(UTM, crs, always_xy=True)
    back = Transformer.from_crs(crs, UTM, always_xy=True)
    native = transform(projected.transform, Point(xy).buffer(radius, quad_segs=64))
    x0, y0, x1, y1 = native.bounds
    r0, c0 = ds.index(x0, y1)
    r1, c1 = ds.index(x1, y0)
    window = Window(c0 - 1, r0 - 1, c1 - c0 + 3, r1 - r0 + 3)
    require(
        0 <= window.col_off < window.col_off + window.width <= ds.width
        and 0 <= window.row_off < window.row_off + window.height <= ds.height,
        "Complete raster neighborhood",
    )
    raster = ds.read(1, window=window, masked=True)
    affine = ds.window_transform(window)
    patches = defaultdict(list)
    for i in range(raster.shape[0]):
        for j in range(raster.shape[1]):
            value = raster[i, j]
            code = "unknown" if is_masked(value) else classify(int(value))
            x0, y0 = affine * (j, i)
            x1, y1 = affine * (j + 1, i + 1)
            patches[code].append(transform(back.transform, box(x0, y1, x1, y0)))
    x, y = projected.transform(*xy)
    value = next(ds.sample([(x, y)], masked=True))[0]
    center = "unknown" if is_masked(value) else classify(int(value))
    return center, {code: unary_union(cells) for code, cells in patches.items()}


def measure(ds, xy, scan, track, crs, classify):
    center, patches = raster_patches(ds, xy, hypot(scan, track) / 2 + 30, crs, classify)
    east, north = xy
    point = Point(xy)
    rectangle = box(east - scan / 2, north - track / 2, east + scan / 2, north + track / 2)
    rows = []
    for angle in range(180):
        shape = rotate(rectangle, angle, origin=xy)
        fractions = {
            code: shape.intersection(area).area / shape.area for code, area in patches.items()
        }
        require(abs(sum(fractions.values()) - 1) < 1e-7, "Raster area conservation")
        rows.append(
            {
                "angle_deg_ccw_from_east": angle,
                "land_fraction": sum(
                    v for k, v in fractions.items() if k not in {"water", "unknown"}
                ),
                "water_fraction": fractions.get("water", 0),
                "unknown_fraction": fractions.get("unknown", 0),
            }
        )
    land = unary_union([p for key, p in patches.items() if key not in {"water", "unknown"}])
    water = patches.get("water")
    return {
        "center": center,
        "nearest_mapped_land_m": None if land.is_empty else point.distance(land),
        "nearest_mapped_water_m": None if water is None else point.distance(water),
        "rotation_rows": rows,
    }


def plot_windows(out, images, xy, inner, outer):
    fig, panels = plt.subplots(1, len(images), figsize=(5 * len(images), 5), squeeze=False)
    for ax, plan in zip(panels[0], images, strict=True):
        with rasterio.open(out / plan["folder"] / "visual.tif") as ds:
            ax.imshow(ds.read().transpose(1, 2, 0), extent=plotting_extent(ds))
            project = Transformer.from_crs(UTM, ds.crs, always_xy=True).transform
            for radius, color in ((inner, "#ffdd33"), (outer, "#ff715c")):
                circle = transform(project, Point(xy).buffer(radius, quad_segs=64))
                ax.plot(*circle.exterior.xy, color=color, linewidth=1.3)
            ax.scatter(*project(*xy), marker="+", color="white")
        ax.set_title(plan["acquired_utc"][:10])
        ax.set_axis_off()
    fig.suptitle("Urla kıyısı | VIIRS merkezli iç (sarı) ve dış (turuncu) daireler")
    fig.savefig(out / "cover_review.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    pins = {}

    def retain(name, expected):
        path = ROOT / name
        require(path.resolve(strict=True).is_relative_to(ROOT), "Contained input")
        require(sha(path) == expected, "Input hash mismatch")
        pins[name] = expected
        return path

    parent = json.loads(
        retain(
            PARENT, "aa0ad0e753d04be890837c7f5e46f7d2ac03ba1ecf9c6e183016946f30bfe38e"
        ).read_text()
    )
    (point,) = (p for p in parent["first_points"] if p["id"] == ID)
    path = "data/interim/firms_combined_candidates_2018_2024.csv"
    with retain(path, parent["source_sha256"][path]).open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        (row,) = (r for r in csv.DictReader(stream) if r["detection_id"] == ID)
    lonlat = float(row["longitude"]), float(row["latitude"])
    require(lonlat == (point["longitude"], point["latitude"]), "Coordinate identity")
    stamp = utc_time(row["detection_timestamp_utc"])
    require(
        stamp == utc_time("2021-08-14T10:44:00Z") and row["source_sensor"] == "SNPP",
        "Case identity",
    )
    scan, track = float(row["scan"]) * 1000, float(row["track"]) * 1000
    require(0 < scan < 2000 and 0 < track < 2000, "Plausible reported dimensions")
    xy = Transformer.from_crs(4326, UTM, always_xy=True).transform(*lonlat)
    clc = next(name for name in parent["source_sha256"] if name.endswith("20u1.tif"))
    delivery = next(
        name
        for name in parent["source_sha256"]
        if "/corine_delivery_review_v1/" in name and name.endswith("readback.json")
    )
    legend = json.loads(retain(delivery, parent["source_sha256"][delivery]).read_text())["legend"]

    def classify_clc(value):
        if not 1 <= value <= 44:
            return "unknown"
        code = int(legend[str(value)]["clc_code"])
        return "water" if 500 <= code < 600 else str(code)

    def classify_cgls(value):
        group = cover_group(value)
        if group in {"water", "ocean"}:
            return "water"
        return "unknown" if group == "unknown_or_unmapped" else str(value)

    cgls = "data/raw/landcover/landcover_copernicus_2017.tif"
    with rasterio.open(retain(clc, parent["source_sha256"][clc])) as ds:
        corine = measure(ds, xy, scan, track, 3035, classify_clc)
    with rasterio.open(
        retain(cgls, "ee8bd6c9f742dbbdfcdcbbb6ecc446499f05d676eaeb202c4345c11ea6006470")
    ) as ds:
        cgls_result = measure(ds, xy, scan, track, ds.crs, classify_cgls)
    support = transform(
        Transformer.from_crs(UTM, 4326, always_xy=True).transform,
        Point(xy).buffer(250, quad_segs=64),
    )
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = ROOT / BASE / "urla_coastal_detection_v1" / run
    out.mkdir(parents=True, exist_ok=False)
    reader, images, windows, failures = PublicWindows(), [], [], []
    try:
        with requests.Session() as session:
            session.trust_env = False
            _, selected = catalogue(session, support, stamp.replace(hour=0, minute=0))
        if len(selected) != 2:
            failures.append("FewerThanTwoDates")
        for i, (item, meta) in enumerate(selected):
            folder = out / f"date{i + 1}"
            folder.mkdir()
            projected = transform(
                Transformer.from_crs(
                    4326, item["properties"]["proj:epsg"], always_xy=True
                ).transform,
                support,
            )
            assets, quality = reader.read(item, projected, folder)
            scl_path = folder / "SCL.tif"
            require(sha(scl_path) == assets["SCL"]["sha256"], "Unchanged SCL")
            with rasterio.open(scl_path) as ds:

                def classify_scl(value):
                    if value == 6:
                        return "water"
                    return str(value) if value in {4, 5} else "unknown"

                scl = measure(ds, xy, scan, track, ds.crs, classify_scl)
            plan = {**meta, "folder": folder.name, "grid": point["grid"]}
            windows.append({**plan, "assets": assets, "quality": quality, "support": scl})
            images.append(plan)
    except Exception as exc:
        failures.append(type(exc).__name__)
    finally:
        reader.close()
    inner, outer = min(scan, track) / 2, hypot(scan, track) / 2
    if images:
        plot_windows(out, images, xy, inner, outer)
    for name in (
        Path(__file__).relative_to(ROOT).as_posix(),
        "scripts/quality/review_public_event_cover.py",
        "src/wildfire_risk_prediction/public_sentinel_windows.py",
    ):
        pins[name] = sha(ROOT / name)
    require(all(sha(ROOT / name) == value for name, value in pins.items()), "Inputs changed")
    report = {
        "source_sha256": pins,
        "point_id": ID,
        "timestamp_utc": stamp.isoformat(),
        "reported_dimensions_m": [scan, track],
        "inner_radius_m": inner,
        "outer_radius_m": outer,
        "corine_2018": corine,
        "cgls_2017": cgls_result,
        "sentinel_windows": windows,
        "failures": failures,
        "image_sha256": sha(out / "cover_review.png") if images else None,
        "native_pixel_geometry_verified": False,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
    }
    receipt = out / "readback.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    require(json.loads(receipt.read_text()) == report, "Readback identity")
    print(
        receipt.relative_to(ROOT).as_posix(),
        sha(receipt),
        "windows",
        len(windows),
        "failures",
        failures,
    )


if __name__ == "__main__":
    main()
