"""Read pre-cutoff Sentinel-2 and historical CORINE context for the Anamur case."""

import csv
import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import rasterio
import requests
from measure_corine_review_supports import DELIVERY, DELIVERY_SHA, class_areas
from pyproj import Transformer
from rasterio.plot import plotting_extent
from review_public_event_cover import QA_FLAGS, catalogue, plt, require, sha
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json
from shapely.geometry import Point
from shapely.ops import transform, unary_union

from wildfire_risk_prediction.event_review import GEOD
from wildfire_risk_prediction.preevent_imagery import utc_time
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows

CASE_RECEIPT = BASE / "july_2023_start_context_v1/20261108T031417Z_6fa7cc62/readback.json"
CASE_SHA = "8532ad7435abca375bf546d3ebb916ac84264d931c80ce932b51d63019d64d45"
CATALOG = "data/interim/firms_combined_candidates_2018_2024.csv"
GROUP = "data/interim/event_grouping/d500m_t24h_assignments.csv"
GRID = "E6933_5K_V1_C632_R864"
UTM = 32636
RADIUS = 250


def detection_points(belensazak, start, end):
    candidates = []
    with (ROOT / CATALOG).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if not row["detection_timestamp_utc"].startswith(("2023-07-10", "2023-07-11")):
                continue
            stamp = utc_time(row["detection_timestamp_utc"])
            coords = float(row["longitude"]), float(row["latitude"])
            if start < stamp <= end and GEOD.inv(*belensazak, *coords)[2] <= 2000:
                require(row["grid_id"] == GRID, "Anamur catalogue cell")
                candidates.append((stamp, row["detection_id"], row["source_sensor"], coords))
    require(len(candidates) == 5, "Five retained candidate detections")
    candidates.sort()
    require(candidates[0][0] < candidates[1][0], "One earliest detection")
    with (ROOT / GROUP).open(encoding="utf-8-sig", newline="") as stream:
        assignments = list(csv.DictReader(stream))
    ids = {row[1] for row in candidates}
    selected = {row["cluster_id"] for row in assignments if row["detection_id"] in ids}
    require(
        len(selected) == 1
        and {r["detection_id"] for r in assignments if r["cluster_id"] in selected} == ids,
        "Exact membership of the existing Anamur cluster",
    )
    return {
        f"tespit_{index}": {"time_utc": stamp.isoformat(), "sensor": sensor, "lon_lat": coords}
        for index, (stamp, _, sensor, coords) in enumerate(candidates, 1)
    }


def historic_cover(ds, circle, legend):
    support = transform(Transformer.from_crs(UTM, ds.crs, always_xy=True).transform, circle)
    fractions = {}
    for value, area in class_areas(ds, support).items():
        code = str(legend[str(value)]["clc_code"]) if 1 <= value <= 44 else "unmapped"
        fractions[code] = fractions.get(code, 0) + area / support.area
    return dict(sorted(fractions.items()))


def fetch_images(out, circles, cutoff):
    project = Transformer.from_crs(UTM, 4326, always_xy=True).transform
    footprint = transform(project, unary_union(list(circles.values())).envelope)
    reader = PublicWindows()
    images = {key: [] for key in circles}
    try:
        with requests.Session() as session:
            session.trust_env = False
            count, choices = catalogue(session, footprint, cutoff)
        for item, meta in choices:
            epsg = item["properties"]["proj:epsg"]
            acquired = utc_time(meta["acquired_utc"])
            require(acquired < cutoff, "Pre-cutoff scene")
            for key, polygon in circles.items():
                support = transform(
                    Transformer.from_crs(UTM, epsg, always_xy=True).transform, polygon
                )
                folder = out / key / acquired.date().isoformat()
                folder.mkdir(parents=True, exist_ok=False)
                row = {
                    "item_id": item["id"],
                    "acquired_utc": acquired.isoformat(),
                    "scene_cloud_percent": meta["scene_cloud_percent"],
                }
                try:
                    assets, quality = reader.read(item, support, folder)
                    row.update(
                        state="read",
                        assets=assets,
                        quality=quality,
                        selected_flag_fraction=sum(quality[k] for k in QA_FLAGS),
                        crop_directory=folder.relative_to(ROOT).as_posix(),
                    )
                except Exception as exc:
                    row.update(state="read_failed", error_type=type(exc).__name__)
                images[key].append(row)
                print(key, acquired.date().isoformat(), row["state"], flush=True)
    finally:
        reader.close()
    return images, count


def plot(path, images, circles):
    names = {
        "tespit_1": "İlk VIIRS tespiti",
        "belensazak": "Belensazak",
        "asagi_kukur": "Aşağı Kükür",
    }
    fig, panels = plt.subplots(3, 2, figsize=(8, 11), layout="constrained")
    for key, axes in zip(circles, panels, strict=True):
        for ax, row in zip(axes, images[key], strict=False):
            ax.set_axis_off()
            if row["state"] != "read":
                ax.set_title(names[key] + " | Kesit okunamadı")
                continue
            with rasterio.open(ROOT / row["crop_directory"] / "visual.tif") as ds:
                ax.imshow(ds.read().transpose(1, 2, 0), extent=plotting_extent(ds))
                outline = transform(
                    Transformer.from_crs(UTM, ds.crs, always_xy=True).transform, circles[key]
                )
                x, y = outline.centroid.coords[0]
                ax.plot(*outline.exterior.xy, color="#ffdf32", linewidth=1.6)
                ax.scatter(x, y, marker="+", color="white", s=90)
                ax.set(xlim=(x - 490, x + 490), ylim=(y - 490, y + 490))
            ax.set_title(f"{names[key]} | {row['acquired_utc'][:10]}")
        for ax in axes[len(images[key]) :]:
            ax.set_axis_off()
    fig.suptitle(
        "Anamur | Olay öncesi Sentinel-2\nSarı çevre 250 m · Artı işareti inceleme merkezi"
    )
    fig.savefig(path, dpi=145)
    plt.close(fig)


def main():
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    require(sha(CASE_RECEIPT) == CASE_SHA and sha(DELIVERY) == DELIVERY_SHA, "Frozen receipts")
    receipt, delivery = read_json(CASE_RECEIPT), read_json(DELIVERY)
    case = receipt["cases"]["anamur_belensazak_approximate"]
    anchors = case["anchors"]
    belensazak = anchors["belensazak_locality"]["approximate_lon_lat"]
    cutoff = utc_time(case["target_window_start_utc"])
    end = utc_time(case["target_window_end_utc"])
    pins = {name: receipt["source_sha256"][name] for name in (CATALOG, GROUP)}
    raster = next(name for name in delivery["source_sha256"] if name.endswith("20u1.tif"))
    pins[raster] = delivery["source_sha256"][raster]
    require(all(sha(ROOT / k) == v for k, v in pins.items()), "Frozen evidence")
    points = detection_points(belensazak, cutoff, end + (end - cutoff))
    points["belensazak"] = {"lon_lat": belensazak}
    points["asagi_kukur"] = {"lon_lat": anchors["asagi_kukur_hgm"]["approximate_lon_lat"]}
    project = Transformer.from_crs(4326, UTM, always_xy=True)
    circles = {
        key: Point(*project.transform(*p["lon_lat"])).buffer(RADIUS) for key, p in points.items()
    }
    with rasterio.open(ROOT / raster) as ds:
        covers = {
            key: historic_cover(ds, circle, delivery["legend"]) for key, circle in circles.items()
        }
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "anamur_preevent_cover_v1" / run
    out.mkdir(parents=True, exist_ok=False)
    view = {key: circles[key] for key in ("tespit_1", "belensazak", "asagi_kukur")}
    try:
        images, count = fetch_images(out, view, cutoff)
        plot(out / "cover_review.png", images, view)
        image_sha = sha(out / "cover_review.png")
        access = "reviewed_windows"
    except (ValueError, requests.RequestException) as exc:
        images, count, image_sha, access = {}, None, None, type(exc).__name__
    report = {
        "source_sha256": {
            **pins,
            CASE_RECEIPT.relative_to(ROOT).as_posix(): CASE_SHA,
            DELIVERY.relative_to(ROOT).as_posix(): DELIVERY_SHA,
            Path(__file__).resolve().relative_to(ROOT).as_posix(): sha(Path(__file__)),
        },
        "cutoff_utc": cutoff.isoformat(),
        "radius_m": RADIUS,
        "points": {k: {**p, "lon_lat": list(p["lon_lat"])} for k, p in points.items()},
        "corine_2018_area_fractions": covers,
        "images": images,
        "metadata_candidates": count,
        "access": access,
        "cover_review_png_sha256": image_sha,
        "original_ignition_verified": False,
        "daily_observation_status": "unknown",
        "habitat_admission": "undecided",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "target": None,
    }
    result = out / "readback.json"
    write_json(result, report)
    print(result.relative_to(ROOT).as_posix(), sha(result), access, flush=True)


if __name__ == "__main__":
    main()
