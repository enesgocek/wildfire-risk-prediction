"""Fixed two-date follow-up of six cloud-flagged supports, never label admission."""

import hashlib
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from pyproj import Transformer
from rasterio.warp import Resampling, reproject
from shapely.geometry import Polygon
from shapely.ops import transform

from wildfire_risk_prediction.preevent_imagery import inspect_item, prediction_time
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows, require
from wildfire_risk_prediction.temporal_imagery_review import alternative_dates

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
FIRST = BASE / "preevent_image_windows_v1/20261023T152456Z_e03ae61d"
INVENTORY = BASE / "preevent_imagery_inventory_v1/20261023T150758Z_56f8c769"
NATIVE = BASE / "native_candidate_cover_v1/20261023T143656Z_90c1c93b"
HUMAN = BASE / "preevent_researcher_review_v1/20261023T153234Z_ecee9147/readback.json"
COLORS = [
    "#000000",
    "#ff0000",
    "#333333",
    "#765033",
    "#269c39",
    "#dfc568",
    "#1255d4",
    "#999999",
    "#cccccc",
    "#ffffff",
    "#79dfff",
    "#e97bff",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def card(identity, sources, polygon6933, out):
    """Display all dates on the first crop's grid; native counts remain unresampled."""
    with rasterio.open(sources[0] / "visual.tif") as ref:
        grid, crs, shape = ref.transform, ref.crs, (ref.height, ref.width)
        bounds = ref.bounds
    polygon = transform(Transformer.from_crs(6933, crs, always_xy=True).transform, polygon6933)
    cx, cy = polygon.centroid.coords[0]
    extent = [bounds.left - cx, bounds.right - cx, bounds.bottom - cy, bounds.top - cy]
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    for col, folder in enumerate(sources):
        receipt = json.loads((folder / "receipt.json").read_text())
        quality = receipt["quality"]
        for row, band in enumerate(("visual", "SCL")):
            with rasterio.open(folder / f"{band}.tif") as src:
                dst = np.zeros((src.count, *shape), dtype="uint8")
                mask = np.zeros(shape, dtype="uint8")
                for i in range(src.count):
                    reproject(
                        rasterio.band(src, i + 1),
                        dst[i],
                        dst_transform=grid,
                        dst_crs=crs,
                        resampling=Resampling.nearest,
                    )
                reproject(
                    src.dataset_mask(),
                    mask,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=grid,
                    dst_crs=crs,
                    resampling=Resampling.nearest,
                )
            ax = axes[row, col]
            ax.set_facecolor("#bbbbbb")
            if band == "visual":
                rgba = np.dstack((np.moveaxis(dst, 0, -1), mask))
                ax.imshow(rgba, extent=extent, interpolation="nearest")
            else:
                ax.imshow(
                    np.ma.masked_where(mask == 0, dst[0]),
                    extent=extent,
                    cmap=ListedColormap(COLORS),
                    norm=BoundaryNorm(np.arange(-0.5, 12), 12),
                    interpolation="nearest",
                )
            x, y = polygon.exterior.xy
            ax.plot(np.asarray(x) - cx, np.asarray(y) - cy, color="#ffe900", linewidth=1.5)
            ax.set_xlabel("Doğu-batı (m)")
            ax.set_ylabel("Kuzey-güney (m)")
            if row == 0:
                role = "İlk görüntü" if col == 0 else f"Alternatif {col}"
                ax.set_title(
                    f"{role} | {receipt['acquired_utc'][:10]}\n"
                    f"Sahne bulutu %{receipt['scene_cloud_percent']:.2f}",
                    fontsize=11,
                )
            else:
                ax.set_title(
                    f"Yerel bulut/sirüs %{100 * quality['cloud_cirrus_fraction']:.2f}\n"
                    f"Gölge %{100 * quality['cloud_shadow_fraction']:.2f} | "
                    f"Koyu/gölge %{100 * quality['dark_or_cast_shadow_fraction']:.2f}",
                    fontsize=10,
                )
    fig.suptitle(f"{identity} — aynı alan, üç olay öncesi tarih", fontsize=15)
    fig.text(
        0.5,
        0.015,
        "Üst: TCI • Alt: otomatik SCL • Sarı sınır: yaklaşık piksel desteği\n"
        "Yeşil: bitki (orman ayrımı yok), sarı: bitkisiz, gri/beyaz: bulut, "
        "camgöbeği: sirüs, koyu: gölge. Yangın/örtü kabulü değildir.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    fig.savefig(out / f"{identity}.png", dpi=140)
    plt.close(fig)


def main():
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    pins = {}

    def pin(path, expected=None):
        actual = sha(path)
        require(expected is None or actual == expected, "Changed input")
        pins[path.relative_to(ROOT).as_posix()] = actual
        return path

    for folder, expected in (
        (FIRST, "a3d1378c3f13a2b1947b045aaa2f296426bdfb4246861160aa83adf3caa6a5f8"),
        (INVENTORY, "dedc117b117dca2b1751b54a044de648b1305672495e0c11d32703ae13e727dc"),
        (NATIVE, "65443618bddc95f01a453f0186473891112d9712b50289e3c4613ac71470568b"),
    ):
        parent = json.loads(pin(folder / "readback.json", expected).read_text())
        for name, value in parent["artifact_sha256"].items():
            pin(folder / name, value)
    pin(HUMAN, "36fac85b3d6fe2f288af7070b70cfed5b037f70bd5b0601646a2eeb38e184645")
    pin(Path(__file__).resolve())
    for module in (
        "imagery_review",
        "preevent_imagery",
        "public_sentinel_windows",
        "temporal_imagery_review",
    ):
        pin(ROOT / f"src/wildfire_risk_prediction/{module}.py")
    quality = pd.read_csv(FIRST / "quality.csv")
    flagged = quality.loc[quality.cloud_cirrus_fraction.gt(0), "detection_id"].tolist()
    require(len(flagged) == 6 and len(set(flagged)) == 6, "Fixed six flagged points")
    points = pd.read_csv(NATIVE / "native_point_context.csv").set_index("detection_id")
    geometries = {
        p["detection_id"]: Polygon(p["approximate_corners_6933"])
        for p in json.loads((NATIVE / "approximate_support_geometry.json").read_text())["points"]
    }
    plan, jobs = [], []
    for identity in flagged:
        items = []
        for path in sorted((INVENTORY / "metadata").glob(f"{identity}_page*.json")):
            items.extend(json.loads(path.read_text())["features"])
        original = json.loads((FIRST / identity / "receipt.json").read_text())
        original_item = next(item for item in items if item["id"] == original["item_id"])
        cutoff = prediction_time(points.loc[identity, "detection_timestamp_utc"])
        support = transform(
            Transformer.from_crs(6933, 4326, always_xy=True).transform, geometries[identity]
        )
        selected = alternative_dates(items, original_item, support, cutoff)
        for order, item in enumerate(selected, 1):
            record = {
                "detection_id": identity,
                "alternative": order,
                "original_item_id": original_item["id"],
                "prediction_utc": cutoff.isoformat(),
                **inspect_item(item, support, cutoff),
            }
            plan.append(record)
            jobs.append((record, item))
    out = (
        BASE
        / "preevent_date_comparison_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    write(
        out / "selection_plan.json",
        {
            "frozen_before_asset_reads_utc": datetime.now(UTC).isoformat(),
            "rule": (
                "cloud-positive original; two distinct UTC dates excluding original; "
                "scene cloud, recency, ID"
            ),
            "local_quality_used_for_alternative_selection": False,
            "jobs": plan,
        },
    )
    plan_sha = sha(out / "selection_plan.json")
    write(out / "input_manifest.json", pins)
    rows, failures = [], []
    deadline = time.monotonic() + 900
    client = PublicWindows()
    for record, item in jobs:
        identity, order = record["detection_id"], record["alternative"]
        folder = out / identity / str(order)
        folder.mkdir(parents=True)
        try:
            require(time.monotonic() < deadline, "Runtime limit")
            epsg = item["properties"]["proj:epsg"]
            polygon = transform(
                Transformer.from_crs(6933, epsg, always_xy=True).transform, geometries[identity]
            )
            assets, local_quality = client.read(item, polygon, folder)
            receipt = {
                **record,
                "epsg": epsg,
                "assets": assets,
                "quality": local_quality,
                "retrieved_utc": datetime.now(UTC).isoformat(),
                "selection_plan_sha256": plan_sha,
                "human_review_completed": False,
                "official_pixel_corners": False,
                "context_margin_utm_m": 500,
            }
            write(folder / "receipt.json", receipt)
            rows.append(
                {
                    "detection_id": identity,
                    "alternative": order,
                    "item_id": item["id"],
                    "acquired_utc": record["acquired_utc"],
                    **local_quality,
                }
            )
            print(identity, order, "windows_verified", flush=True)
        except Exception as error:
            # No exception text: raster/network errors can contain signed URLs.
            failure = {
                "detection_id": identity,
                "alternative": order,
                "error_type": type(error).__name__,
            }
            failures.append(failure)
            write(folder / "failure.json", failure)
            break
    client.close()
    complete = len(rows) == 12
    if complete:
        for identity in flagged:
            original = json.loads((FIRST / identity / "receipt.json").read_text())
            rows.append(
                {
                    "detection_id": identity,
                    "alternative": 0,
                    "item_id": original["item_id"],
                    "acquired_utc": original["acquired_utc"],
                    **original["quality"],
                }
            )
            card(
                identity,
                [FIRST / identity, out / identity / "1", out / identity / "2"],
                geometries[identity],
                out,
            )
    for row in rows:
        row["scl_counts"] = json.dumps(row["scl_counts"], sort_keys=True)
    if rows:
        frame = pd.DataFrame(rows).sort_values(["detection_id", "alternative"])
        frame.to_csv(out / "comparison.csv", index=False)
        pd.testing.assert_frame_equal(
            frame.reset_index(drop=True),
            pd.read_csv(out / "comparison.csv"),
            check_dtype=False,
            atol=1e-14,
            rtol=1e-14,
        )
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, "Changed input after run")
    require(sha(out / "selection_plan.json") == plan_sha, "Changed frozen plan")
    artifacts = {p.relative_to(out).as_posix(): sha(p) for p in out.rglob("*") if p.is_file()}
    report = {
        "version": "preevent_date_comparison_v1",
        "status": "comparison_only" if complete else "incomplete_retained",
        "new_dates_completed": min(len(rows), 12),
        "expected_new_dates": 12,
        "purpose_selected_points": 6,
        "failures": failures,
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "final_merge_performed": False,
        "human_review_completed": False,
        "prior_human_review_preserved": True,
        "cloud_jobs_started": 0,
        "validation_or_final_test_accessed": False,
        "network_transfer_bytes_measured": False,
        "artifact_sha256": artifacts,
    }
    write(out / "readback.json", report)
    print("Result:", out.relative_to(ROOT).as_posix())
    print("Readback SHA256:", sha(out / "readback.json"))
    return 0 if complete else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("Comparison incomplete:", type(error).__name__)
        sys.exit(1)
