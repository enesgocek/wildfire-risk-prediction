"""Read historical cover context for all first points and dated images for five fixed windows."""

import csv
import json
import logging
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import matplotlib
import numpy as np
import pandas as pd
import rasterio
import requests
from pyproj import Transformer
from rasterio.plot import plotting_extent
from review_pu_candidate_timeline import sha
from shapely.geometry import Point
from shapely.ops import transform

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.preevent_imagery import inspect_item, utc_time
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = "outputs/reports/dataset"
EVENT = f"{BASE}/public_reference_cases_v1/20261107T231732Z_424d1731/readback.json"
CORINE = f"{BASE}/corine_delivery_review_v1/20261103T212921Z_3cc30ebb"
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
QA_FLAGS = (
    "cloud_cirrus_fraction",
    "cloud_shadow_fraction",
    "dark_or_cast_shadow_fraction",
    "nodata_defective_fraction",
    "unclassified_fraction",
    "snow_ice_fraction",
)


def first_points(report, retain):
    assignments = {
        Path(name).stem.removesuffix("_assignments"): pd.read_csv(retain(name, expected))
        for name, expected in report["source_sha256"].items()
        if name.endswith("_assignments.csv")
    }
    require(len(assignments) == 9, "All assignment scenarios")
    catalogue = "data/interim/firms_combined_candidates_2018_2024.csv"
    with retain(catalogue, report["source_sha256"][catalogue]).open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        source = {
            row["detection_id"]: row
            for row in csv.DictReader(stream)
            if row["detection_timestamp_utc"].startswith("2021-")
        }
    result = []
    for code, case in report["cases"].items():
        sets = []
        for scenario in case["scenarios"]:
            table = assignments[scenario["scenario"]]
            first_ids = set()
            for group in scenario["groups"]:
                members = table.loc[table.cluster_id.eq(group["cluster_id"])].copy()
                times = pd.to_datetime(members.timestamp, utc=True, format="ISO8601")
                require(len(members) == group["member_count"], "Membership denominator")
                first = members.loc[times.eq(pd.Timestamp(group["first_utc"]))]
                require(
                    times.min() == pd.Timestamp(group["first_utc"])
                    and set(first.grid_id) == set(group["first_cells"]),
                    "Exact first cells",
                )
                first_ids.update(first.detection_id)
            sets.append(first_ids)
        union = set().union(*sets)
        inside = set(case["first_in_perimeter_ids"])
        require(len(sets) == 9 and inside <= union, "Complete first-point union")
        for identity in sorted(union):
            row = source[identity]
            require(
                utc_time(row["detection_timestamp_utc"])
                == utc_time(case["first_in_perimeter_utc"]),
                "Source first timestamp",
            )
            result.append(
                {
                    "case": code,
                    "id": identity,
                    "grid": row["grid_id"],
                    "day": case["day"],
                    "longitude": float(row["longitude"]),
                    "latitude": float(row["latitude"]),
                    "scenario_count": sum(identity in ids for ids in sets),
                    "inside_final_perimeter": identity in inside,
                }
            )
    require(
        len(result) == 46 and len({row["id"] for row in result}) == 46, "46 unique first points"
    )
    return result


def representative_supports(points):
    cells = defaultdict(list)
    for row in points:
        cells[row["case"], row["grid"]].append(row)
    require(len(cells) == 5, "All five first cells")
    supports = []
    for (case, grid), rows in sorted(cells.items()):
        epsg = 32635 if case == "urla_karaburun" else 32636
        project = Transformer.from_crs(4326, epsg, always_xy=True).transform
        coords = np.asarray([project(row["longitude"], row["latitude"]) for row in rows])
        center = coords.mean(axis=0)
        index = min(
            range(len(rows)), key=lambda i: (np.linalg.norm(coords[i] - center), rows[i]["id"])
        )
        support = Point(*coords[index]).buffer(250)
        ll = transform(Transformer.from_crs(epsg, 4326, always_xy=True).transform, support)
        supports.append((grid, rows[index], ll, len(rows)))
    return supports


def catalogue(session, support, cutoff):
    params = {
        "collections": "sentinel-2-l2a",
        "bbox": ",".join(str(v) for v in support.bounds),
        "datetime": f"{(cutoff - timedelta(days=30)).isoformat()}/{cutoff.isoformat()}",
        "limit": 100,
    }
    response = session.get(STAC, params=params, timeout=(12, 30), allow_redirects=False)
    require(response.status_code == 200, f"Catalogue HTTP {response.status_code}")
    require(len(response.content) <= 20_000_000, "Catalogue size cap")
    payload = response.json()
    require(not any(link.get("rel") == "next" for link in payload["links"]), "Catalogue cap")
    items = []
    for item in payload["features"]:
        check = inspect_item(item, support, cutoff, lookback_days=30)
        if check["metadata_candidate"] and "visual" in item["assets"]:
            items.append((item, check))
    items.sort(
        key=lambda pair: (
            pair[1]["scene_cloud_percent"] is None or float(pair[1]["scene_cloud_percent"]) > 20,
            pair[1]["days_before_prediction"],
            pair[0]["id"],
        )
    )
    selected = {}
    for item, check in items:
        selected.setdefault(check["acquired_utc"][:10], (item, check))
    return len(items), list(selected.values())[:2]


def plot(out, images):
    fig, axes = plt.subplots(5, 2, figsize=(10, 21), layout="constrained")
    for panel in axes.flat:
        panel.set_axis_off()
    for row, col, plan, support in images:
        path = out / plan["folder"] / "visual.tif"
        with rasterio.open(path) as src:
            axes[row, col].imshow(src.read().transpose(1, 2, 0), extent=plotting_extent(src))
            projected = transform(
                Transformer.from_crs(4326, src.crs, always_xy=True).transform, support
            )
            axes[row, col].plot(*projected.exterior.xy, color="#ffe800", linewidth=1.7)
            axes[row, col].scatter(
                projected.centroid.x, projected.centroid.y, marker="+", color="#ff4950"
            )
        grid = plan["grid"].removeprefix("E6933_5K_V1_")
        axes[row, col].set_title(f"{grid} | {plan['acquired_utc'][:10]}")
    fig.suptitle(
        "Olay öncesi Sentinel-2 kesitleri\nSarı: 250 m inceleme çevresi · Kırmızı: tespit merkezi"
    )
    fig.savefig(out / "cover_review.png", dpi=125)
    plt.close(fig)


def main():
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    pins = {}

    def retain(name, expected=None):
        path = ROOT / name
        require(path.resolve(strict=True).is_relative_to(ROOT), "Contained input")
        actual = sha(path)
        require(expected is None or actual == expected, f"Input changed: {name}")
        pins[name] = actual
        return path

    event = json.loads(
        retain(
            EVENT, "b1aac4c4bec040d0446dc64a99f3312a3ba9c86e90a1c478a3c4b0782984596c"
        ).read_text()
    )
    corine = json.loads(
        retain(
            f"{CORINE}/readback.json",
            "be52cf11729cec66f84a8abf8d45c3ac9bfaf8d764f68255f2c5ab4ae3b4313f",
        ).read_text()
    )
    points = first_points(event, retain)
    raster = f"{CORINE}/source/DATA/U2018_CLC2018_V2020_20u1.tif"
    project = Transformer.from_crs(4326, 3035, always_xy=True).transform
    coords = [project(row["longitude"], row["latitude"]) for row in points]
    with rasterio.open(retain(raster, corine["source_sha256"][raster])) as src:
        for row, value in zip(points, src.sample(coords, masked=True), strict=True):
            require(
                not np.ma.is_masked(value[0]) and 1 <= int(value[0]) <= 44, "Mapped CORINE centre"
            )
            row["corine_2018"] = corine["legend"][str(int(value[0]))]
    for name in (
        Path(__file__).relative_to(ROOT).as_posix(),
        "src/wildfire_risk_prediction/imagery_review.py",
        "src/wildfire_risk_prediction/preevent_imagery.py",
        "src/wildfire_risk_prediction/public_sentinel_windows.py",
    ):
        retain(name)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = ROOT / BASE / "public_event_cover_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    session = requests.Session()
    session.trust_env = False
    reader = PublicWindows()
    jobs, failed, images, receipts = [], [], [], []
    try:
        for row, (grid, point, support, population) in enumerate(representative_supports(points)):
            cutoff = utc_time(point["day"] + "T00:00:00Z")
            try:
                n, selected = catalogue(session, support, cutoff)
            except Exception as exc:
                failed.append(
                    {"grid": grid, "stage": "catalogue", "error_type": type(exc).__name__}
                )
                continue
            if not selected:
                failed.append({"grid": grid, "stage": "catalogue", "error_type": "NoMatchingScene"})
            for col, (item, check) in enumerate(selected):
                plan = {
                    **check,
                    "folder": f"cell{row + 1}_date{col + 1}",
                    "grid": grid,
                    "point_id": point["id"],
                    "first_points_in_cell": population,
                    "catalogue_candidates": n,
                }
                jobs.append((row, col, plan, item, support))
        plan_path = out / "selection_plan.json"
        plan_path.write_text(json.dumps([job[2] for job in jobs], indent=2), encoding="utf-8")
        plan_digest = sha(plan_path)
        for row, col, plan, item, support in jobs:
            folder = out / plan["folder"]
            folder.mkdir()
            try:
                projected = transform(
                    Transformer.from_crs(
                        4326, item["properties"]["proj:epsg"], always_xy=True
                    ).transform,
                    support,
                )
                assets, quality = reader.read(item, projected, folder)
                receipts.append(
                    {
                        **plan,
                        "assets": assets,
                        "quality": quality,
                        "selected_quality_flags_zero": all(quality[key] == 0 for key in QA_FLAGS),
                    }
                )
                images.append((row, col, plan, support))
                print("Read", plan["folder"], plan["acquired_utc"], flush=True)
            except Exception as exc:
                failed.append(
                    {"grid": plan["grid"], "stage": "crop", "error_type": type(exc).__name__}
                )
    finally:
        session.close()
        reader.close()
    require(sha(plan_path) == plan_digest, "Frozen selection changed")
    require(all(sha(ROOT / name) == expected for name, expected in pins.items()), "Inputs changed")
    if images:
        plot(out, images)
    result = {
        "source_sha256": pins,
        "selection_plan_sha256": plan_digest,
        "first_points": points,
        "corine_counts": dict(Counter(str(row["corine_2018"]["clc_code"]) for row in points)),
        "successful_windows": receipts,
        "failures": failed,
        "visual_sha256": sha(out / "cover_review.png") if images else None,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == result, "JSON readback")
    print(path.relative_to(ROOT).as_posix(), sha(path), "pins", len(pins))
    print("CORINE", result["corine_counts"], "windows", len(receipts), "failures", len(failed))


if __name__ == "__main__":
    main()
