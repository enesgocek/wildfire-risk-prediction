"""Freeze a balanced historical cover sample and read bounded pre-event image windows."""

import argparse
import hashlib
import json
import logging
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
import rasterio
import requests
from pyproj import Transformer
from rasterio.plot import plotting_extent
from review_public_event_cover import QA_FLAGS, catalogue, plt, require, sha
from shapely.geometry import Point, shape
from shapely.ops import transform
from shapely.prepared import prep

from wildfire_risk_prediction.preevent_imagery import utc_time
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
EVENT = "public_reference_cases_v1/20261107T231732Z_424d1731/readback.json"
PREVIOUS = "candidate_center_footprint_v1/20261107T235952Z_cbc4f2b3/readback.json"
BOUNDARIES = "data/raw/boundaries/gaul2025/20261014T231843Z_2271840f/provinces.geojson"
SOURCE = "data/interim/firms_combined_candidates_2018_2024.csv"
ANCHOR = "d1000m_t48h_assignments.csv"
PROVINCES = ("Antalya", "Izmir", "Mersin", "Mugla")
STRATA = ("woody", "agriculture", "mixed_other")
WOODY = {311, 312, 313, 322, 323, 324}
SALT = "cover-pilot-v1-2026-11-08"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, record):
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(read_json(path) == record, "JSON roundtrip")


def first_sets(path):
    rows = pd.read_csv(path, usecols=["detection_id", "grid_id", "timestamp", "cluster_id"])
    require(rows.detection_id.is_unique, "Unique detection assignments")
    times = pd.to_datetime(rows.timestamp, utc=True, format="ISO8601")
    require(times.dt.year.between(2018, 2023).all(), "Training years")
    rows["time"] = times
    first = rows.loc[times.eq(rows.groupby("cluster_id").time.transform("min"))].copy()
    counts = first.groupby("cluster_id").detection_id.transform("size")
    return first.loc[counts.eq(1)].set_index("detection_id"), len(first), first.cluster_id.nunique()


def prepare():
    pins = {}

    def retain(path, expected=None):
        actual = sha(path)
        require(expected is None or actual == expected, "Input identity")
        pins[path.relative_to(ROOT).as_posix()] = actual
        return path

    event = read_json(
        retain(BASE / EVENT, "b1aac4c4bec040d0446dc64a99f3312a3ba9c86e90a1c478a3c4b0782984596c")
    )
    prior = read_json(
        retain(BASE / PREVIOUS, "159771b79506df43bdedf5f4004ecf3d6003384600c84fe4ba055fd8bfd21394")
    )
    prior_ids = {r["id"] for r in prior["points"]}
    tables, denominators = {}, {}
    for name, expected in event["source_sha256"].items():
        if name.endswith("_assignments.csv"):
            path = retain(ROOT / name, expected)
            tables[path.name], points, groups = first_sets(path)
            denominators[path.stem] = {
                "first_points": points,
                "groups": groups,
                "single": len(tables[path.name]),
            }
    require(len(tables) == 9, "Nine scenario assignments")
    stable = set.intersection(*(set(table.index) for table in tables.values()))
    pool = stable - prior_ids
    source = pd.read_csv(
        retain(ROOT / SOURCE, event["source_sha256"][SOURCE]), dtype={"detection_id": str}
    )
    source = source.loc[source.detection_id.isin(pool)].set_index("detection_id")
    require(source.index.is_unique and set(source.index) == pool, "Complete catalog identities")
    anchor = tables[ANCHOR].loc[source.index]
    for table in tables.values():
        members = table.loc[source.index]
        require(
            members.time.equals(anchor.time) and members.grid_id.equals(anchor.grid_id),
            "Stable time and grid",
        )
    require(
        pd.to_datetime(source.detection_timestamp_utc, utc=True, format="ISO8601").equals(
            anchor.time
        )
        and source.grid_id.equals(anchor.grid_id),
        "Catalog time and grid",
    )
    boundary = read_json(
        retain(
            ROOT / BOUNDARIES, "ffb43d77b0e7cba1dbe3c605454e468eb46d4eaefdcc5d2ebd6612ea9e75d2fb"
        )
    )
    province_polygons = {
        f["properties"]["GAUL1_NAME"]: prep(shape(f["geometry"])) for f in boundary["features"]
    }
    require(set(province_polygons) == set(PROVINCES), "Four province geometries")
    raster = next(k for k in prior["source_sha256"] if k.endswith("20u1.tif"))
    legend_path = next(
        k
        for k in prior["source_sha256"]
        if "corine_delivery_review_v1" in k and k.endswith("readback.json")
    )
    legend = read_json(retain(ROOT / legend_path, prior["source_sha256"][legend_path]))["legend"]
    codes = {int(k): int(v["clc_code"]) for k, v in legend.items() if 1 <= int(k) <= 44}
    xy = Transformer.from_crs(4326, 3035, always_xy=True)
    coords = list(zip(source.longitude, source.latitude, strict=True))
    cells, excluded = defaultdict(list), Counter()
    with rasterio.open(retain(ROOT / raster, prior["source_sha256"][raster])) as ds:
        classes = ds.sample([xy.transform(*pair) for pair in coords], masked=True)
        for (key, row), (lon, lat), value in zip(source.iterrows(), coords, classes, strict=True):
            provinces = [
                name for name, geom in province_polygons.items() if geom.covers(Point(lon, lat))
            ]
            if len(provinces) != 1:
                excluded["unassigned_or_multiple_provinces"] += 1
                continue
            if value.mask[0] or int(value[0]) not in codes:
                excluded["unmapped_center"] += 1
                continue
            code = codes[int(value[0])]
            stratum = (
                "woody"
                if code in WOODY
                else "agriculture"
                if 200 <= code < 300 and code != 243
                else "mixed_other"
            )
            year = anchor.loc[key, "time"].year
            record = {
                "id": key,
                "grid": row.grid_id,
                "detected_utc": anchor.loc[key, "time"].isoformat(),
                "province": provinces[0],
                "year": year,
                "center_clc": code,
                "stratum": stratum,
                "longitude": lon,
                "latitude": lat,
            }
            cells[provinces[0], year, stratum].append(record)
    require(
        sum(map(len, cells.values())) + sum(excluded.values()) == len(pool), "Frame denominator"
    )
    selected, slots = [], []
    for i, province in enumerate(PROVINCES):
        for j, year in enumerate(range(2018, 2024)):
            stratum = STRATA[(i + j) % len(STRATA)]
            cell = cells[province, year, stratum]
            slot = f"H{i * 6 + j + 1:02}"
            slots.append(
                {
                    "slot": slot,
                    "province": province,
                    "year": year,
                    "stratum": stratum,
                    "available": len(cell),
                }
            )
            if cell:
                record = min(
                    cell, key=lambda r: hashlib.sha256(f"{SALT}|{r['id']}".encode()).hexdigest()
                )
                selected.append({"slot": slot, **record})
    for path in (
        Path(__file__),
        Path(__file__).with_name("review_public_event_cover.py"),
        ROOT / "src/wildfire_risk_prediction/public_sentinel_windows.py",
        ROOT / "src/wildfire_risk_prediction/imagery_review.py",
    ):
        retain(path.resolve())
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()), "Unchanged inputs")
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "stratified_cover_pilot_v1" / run
    out.mkdir(parents=True, exist_ok=False)
    plan = {
        "source_sha256": pins,
        "scenarios": denominators,
        "stable_unique_first_points": len(stable),
        "previous_points_removed": len(stable & prior_ids),
        "excluded_from_sampling_frame": dict(excluded),
        "frame_cells": [
            {"province": p, "year": y, "stratum": s, "points": len(values)}
            for (p, y, s), values in sorted(cells.items())
        ],
        "selection_salt": SALT,
        "slots": slots,
        "selected": selected,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
    }
    path = out / "plan.json"
    write_json(path, plan)
    print(path.relative_to(ROOT).as_posix(), sha(path), len(selected), len(stable))


def get_image(out, row):
    base = {"slot": row["slot"], "id": row["id"]}
    zone = 32635 if row["longitude"] < 30 else 32636
    project = Transformer.from_crs(4326, zone, always_xy=True)
    local = Point(*project.transform(row["longitude"], row["latitude"])).buffer(250)
    support = transform(Transformer.from_crs(zone, 4326, always_xy=True).transform, local)
    cutoff = utc_time(row["detected_utc"]).replace(hour=0, minute=0, second=0, microsecond=0)
    reader = PublicWindows()
    try:
        with requests.Session() as session:
            session.trust_env = False
            count, selected = catalogue(session, support, cutoff)
        if not selected:
            return {**base, "state": "no_scene"}
        item, meta = selected[0]
        projected = transform(
            Transformer.from_crs(4326, item["properties"]["proj:epsg"], always_xy=True).transform,
            support,
        )
        folder = out / row["slot"]
        folder.mkdir()
        assets, quality = reader.read(item, projected, folder)
        return {
            **base,
            "state": "read",
            "acquired_utc": meta["acquired_utc"],
            "item_id": item["id"],
            "metadata_candidates": count,
            "assets": assets,
            "quality": quality,
            "zero_selected_flags": all(quality[k] == 0 for k in QA_FLAGS),
        }
    except Exception as exc:
        return {**base, "state": "failed", "error_type": type(exc).__name__}
    finally:
        reader.close()


def draw_sheet(out, points, records):
    fig, axes = plt.subplots(2, 3, figsize=(12, 8.4), layout="constrained")
    for ax, point, result in zip(axes.flat, points, records, strict=True):
        if result["state"] == "read":
            with rasterio.open(out / point["slot"] / "visual.tif") as ds:
                ax.imshow(ds.read().transpose(1, 2, 0), extent=plotting_extent(ds))
                x, y = Transformer.from_crs(4326, ds.crs, always_xy=True).transform(
                    point["longitude"], point["latitude"]
                )
                ax.plot(*Point(x, y).buffer(250).exterior.xy, color="#ffe13b", linewidth=1.5)
                ax.scatter(x, y, marker="+", color="white")
                ax.set(xlim=(x - 380, x + 380), ylim=(y - 380, y + 380))
            date = result["acquired_utc"][:10]
        else:
            date = "Kesit yok"
        ax.set_title(f"{point['slot']} | {date}")
        ax.set_axis_off()
    fig.suptitle("Olay öncesi Sentinel-2 | Sarı: 250 m çevre")
    path = out / f"sheet_{points[0]['slot']}.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def read_images(path, expected_sha):
    require(path.resolve(strict=True).is_relative_to(BASE), "Contained plan")
    require(sha(path) == expected_sha, "Plan identity")
    plan = read_json(path)
    require(
        all(sha(ROOT / p) == h for p, h in plan["source_sha256"].items()), "Plan sources changed"
    )
    out = path.parent / "images"
    out.mkdir(exist_ok=False)
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    points = plan["selected"]
    with ThreadPoolExecutor(max_workers=2) as workers:
        records = list(workers.map(lambda point: get_image(out, point), points))
    entries = {r["slot"]: r for r in records}
    artifacts = {}
    for i in range(0, 24, 6):
        slots = plan["slots"][i : i + 6]
        display_points = {p["slot"]: p for p in points}
        sheet = draw_sheet(
            out,
            [display_points.get(s["slot"], s) for s in slots],
            [entries.get(s["slot"], {"state": "empty"}) for s in slots],
        )
        artifacts[sheet.name] = sha(sheet)
    require(sha(path) == expected_sha, "Unchanged plan")
    write_json(
        out / "readback.json",
        {
            "plan_sha256": expected_sha,
            "records": records,
            "outcomes": dict(Counter(r["state"] for r in records)),
            "artifact_sha256": artifacts,
            "daily_observation_status": "unknown",
            "positive_label_permitted": False,
            "negative_label_permitted": False,
            "labels_created": False,
            "final_merge_performed": False,
        },
    )
    print((out / "readback.json").relative_to(ROOT).as_posix(), sha(out / "readback.json"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", nargs=2, metavar=("PLAN", "SHA256"))
    args = parser.parse_args()
    if args.images:
        read_images(ROOT / args.images[0], args.images[1])
    else:
        prepare()
