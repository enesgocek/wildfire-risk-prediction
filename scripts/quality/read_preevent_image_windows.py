"""Read small TCI/SCL windows for fixed first-review candidates; tokens stay in memory."""

import argparse
import hashlib
import json
import logging
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import numpy as np
import pandas as pd
import rasterio
import requests
from affine import Affine
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform

from wildfire_risk_prediction.imagery_review import bounded_window, support_quality
from wildfire_risk_prediction.preevent_imagery import inspect_item, prediction_time, utc_time

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "outputs/reports/dataset/preevent_imagery_inventory_v1/20261023T150758Z_56f8c769"
INVENTORY_SHA = "dedc117b117dca2b1751b54a044de648b1305672495e0c11d32703ae13e727dc"
NATIVE = ROOT / "outputs/reports/dataset/native_candidate_cover_v1/20261023T143656Z_90c1c93b"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse-report", type=Path)
    args = parser.parse_args()
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    pins = {}

    def pin(path, expected=None):
        actual = sha(path)
        require(expected is None or actual == expected, "Changed input")
        pins[path.relative_to(ROOT).as_posix()] = actual
        return path

    parent = json.loads(pin(INVENTORY / "readback.json", INVENTORY_SHA).read_text())
    for name, expected in parent["artifact_sha256"].items():
        pin(INVENTORY / name, expected)
    native = json.loads(
        pin(
            NATIVE / "readback.json",
            "65443618bddc95f01a453f0186473891112d9712b50289e3c4613ac71470568b",
        ).read_text()
    )
    shape_path = pin(
        NATIVE / "approximate_support_geometry.json",
        native["artifact_sha256"]["approximate_support_geometry.json"],
    )
    geometries = {p["detection_id"]: p for p in json.loads(shape_path.read_text())["points"]}
    points = pd.read_csv(
        pin(
            NATIVE / "native_point_context.csv",
            native["artifact_sha256"]["native_point_context.csv"],
        )
    )
    summaries = pd.read_csv(INVENTORY / "point_summary.csv")
    require(len(summaries) == 25 and summaries.detection_id.is_unique, "Fixed 25 points")
    pin(Path(__file__).resolve())
    pin(ROOT / "src/wildfire_risk_prediction/imagery_review.py")
    pin(ROOT / "src/wildfire_risk_prediction/preevent_imagery.py")
    reuse = args.reuse_report.resolve() if args.reuse_report else None
    if reuse:
        require(
            reuse.is_relative_to(ROOT / "outputs/reports/dataset/preevent_image_windows_v1"),
            "Expected retained window run",
        )
        old_report = json.loads(pin(reuse / "readback.json").read_text())
        require(
            old_report["version"] == "preevent_image_windows_v1"
            and not old_report["labels_created"],
            "Unlabelled reuse only",
        )
        for name, expected in old_report["artifact_sha256"].items():
            pin(reuse / name, expected)
        old_pins = json.loads((reuse / "input_manifest.json").read_text())
        for name, expected in old_pins.items():
            if name.startswith("outputs/"):
                pin(ROOT / name, expected)
    out = (
        ROOT
        / "outputs/reports/dataset/preevent_image_windows_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    session = requests.Session()
    session.trust_env = False
    tokens = {}
    results, failures = [], []
    deadline = time.monotonic() + 900

    def sign(href):
        u = urlsplit(href)
        require(
            u.scheme == "https"
            and u.hostname
            in ("sentinel2l2a01.blob.core.windows.net", "sentinel2l2a02.blob.core.windows.net")
            and not u.query
            and not u.fragment,
            "Unexpected public asset",
        )
        account, container = u.hostname.split(".")[0], u.path.split("/")[1]
        require(container == "sentinel2-l2", "Unexpected asset container")
        key = (account, container)
        if key not in tokens:
            response = session.get(
                f"https://planetarycomputer.microsoft.com/api/sas/v1/token/{account}/{container}",
                timeout=(15, 30),
                allow_redirects=False,
            )
            require(response.status_code == 200, "Public access token unavailable")
            tokens[key] = response.json()["token"]
        return href + "?" + tokens[key]

    def head(url):
        response = session.head(url, timeout=(15, 30), allow_redirects=False)
        require(response.status_code == 200 and response.headers.get("ETag"), "Asset header check")
        return {k: response.headers.get(k) for k in ("ETag", "Last-Modified", "Content-Length")}

    for summary in summaries.itertuples(index=False):
        identity = summary.detection_id
        if time.monotonic() > deadline:
            failures.append({"detection_id": identity, "error_type": "RuntimeLimit"})
            continue
        folder = out / identity
        folder.mkdir()
        stage = "metadata"
        try:
            items = []
            for path in sorted((INVENTORY / "metadata").glob(f"{identity}_page*.json")):
                items.extend(json.loads(path.read_text())["features"])
            selected = [f for f in items if f["id"] == summary.first_review_item]
            require(len(selected) == 1, "Unique frozen first-review item")
            item = selected[0]
            point = points.loc[points.detection_id.eq(identity)].iloc[0]
            cutoff = prediction_time(point.detection_timestamp_utc)
            require(cutoff == utc_time(summary.prediction_utc), "Prediction alignment")
            polygon6933 = Polygon(geometries[identity]["approximate_corners_6933"])
            ll = transform(Transformer.from_crs(6933, 4326, always_xy=True).transform, polygon6933)
            require(inspect_item(item, ll, cutoff)["metadata_candidate"], "Metadata admission")
            epsg = item["properties"]["proj:epsg"]
            require(epsg in (32635, 32636), "Expected local UTM CRS")
            polygon = transform(
                Transformer.from_crs(6933, epsg, always_xy=True).transform, polygon6933
            )
            assets = {}
            quality = None
            old_receipt = None
            if reuse and (reuse / identity / "receipt.json").is_file():
                old_receipt = json.loads((reuse / identity / "receipt.json").read_text())
                require(
                    old_receipt["item_id"] == item["id"]
                    and old_receipt["prediction_utc"] == cutoff.isoformat(),
                    "Reuse identity",
                )
            for band, count, resolution in (("SCL", 1, 20), ("visual", 3, 10)):
                asset = item["assets"][band]
                if old_receipt:
                    stage = band + "_verified_local_reuse"
                    old_file = reuse / identity / f"{band}.tif"
                    require(
                        sha(old_file) == old_receipt["assets"][band]["sha256"], "Reuse crop hash"
                    )
                    shutil.copyfile(old_file, folder / f"{band}.tif")
                    with rasterio.open(old_file) as src:
                        if band == "SCL":
                            quality = support_quality(
                                src.read(1), src.dataset_mask() > 0, src.transform, polygon
                            )
                            require(quality == old_receipt["quality"], "Recomputed reuse quality")
                    assets[band] = old_receipt["assets"][band]
                    continue
                stage = band + "_sign_and_header"
                signed = sign(asset["href"])
                before = head(signed)
                stage = band + "_window_read"
                with rasterio.Env(
                    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                    GDAL_PAM_ENABLED="NO",
                    GDAL_HTTP_TIMEOUT="30",
                    GDAL_HTTP_CONNECTTIMEOUT="15",
                    GDAL_HTTP_MAX_RETRY="0",
                    CPL_DEBUG=False,
                    CPL_CURL_VERBOSE=False,
                    CPL_LOG="NUL",
                    GDAL_TIFF_INTERNAL_MASK=True,
                ):
                    with rasterio.open(signed) as src:
                        require(src.crs.to_epsg() == epsg and src.count == count, "Raster identity")
                        require(
                            src.transform == Affine(*asset["proj:transform"]), "Metadata transform"
                        )
                        require(
                            src.res == (resolution, resolution)
                            and src.dtypes == ("uint8",) * count,
                            "Expected native TCI/SCL encoding",
                        )
                        window = bounded_window(
                            polygon.bounds, src.transform, src.width, src.height, clip_context=True
                        )
                        array = src.read(window=window)
                        valid = src.dataset_mask(window=window) > 0
                        affine = src.window_transform(window)
                    after = head(signed)
                    require(before == after, "Source changed during window read")
                    stage = band + "_local_roundtrip"
                    destination = folder / f"{band}.tif"
                    with rasterio.open(
                        destination,
                        "w",
                        driver="GTiff",
                        width=array.shape[2],
                        height=array.shape[1],
                        count=count,
                        dtype="uint8",
                        crs=epsg,
                        transform=affine,
                        compress="deflate",
                    ) as dst:
                        dst.write(array)
                        dst.write_mask(valid.astype("uint8") * 255)
                    with rasterio.open(destination) as check:
                        require(
                            np.array_equal(check.read(), array)
                            and np.array_equal(check.dataset_mask() > 0, valid),
                            "Crop roundtrip",
                        )
                    if band == "SCL":
                        quality = support_quality(array[0], valid, affine, polygon)
                assets[band] = {
                    "unsigned_href": asset["href"],
                    "headers": before,
                    "window": list(window.flatten()),
                    "transform": list(affine)[:6],
                    "shape": list(array.shape),
                    "context_bounds_utm": list(
                        rasterio.transform.array_bounds(array.shape[1], array.shape[2], affine)
                    ),
                    "sha256": sha(destination),
                }
                del signed
            receipt = {
                "detection_id": identity,
                "item_id": item["id"],
                "epsg": epsg,
                "prediction_utc": cutoff.isoformat(),
                "acquired_utc": item["properties"]["datetime"],
                "scene_cloud_percent": item["properties"].get("eo:cloud_cover"),
                "product_generated_utc": item["properties"].get("s2:generation_time"),
                "retrieved_utc": old_receipt["retrieved_utc"]
                if old_receipt
                else datetime.now(UTC).isoformat(),
                "reused_from_receipt": (
                    (reuse / identity / "receipt.json").relative_to(ROOT).as_posix()
                    if old_receipt
                    else None
                ),
                "assets": assets,
                "quality": quality,
                "human_review_completed": False,
                "historical_available_at_verified": False,
                "official_pixel_corners": False,
                "context_margin_utm_m": 500,
                "context_policy": "up to 500m, clipped at tile edge; support never clipped",
            }
            (folder / "receipt.json").write_text(json.dumps(receipt, indent=2))
            row = {"detection_id": identity, "item_id": item["id"], **quality}
            row["scl_counts"] = json.dumps(row["scl_counts"], sort_keys=True)
            results.append(row)
            print(identity, "local_windows_verified", flush=True)
        except Exception as error:
            # Exception messages may contain a temporary SAS URL: never serialize them.
            failure = {"detection_id": identity, "stage": stage, "error_type": type(error).__name__}
            failures.append(failure)
            (folder / "failure.json").write_text(json.dumps(failure))
            print(identity, "window_failed", type(error).__name__, flush=True)
            break
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, "Input changed during run")
    (out / "input_manifest.json").write_text(json.dumps(pins, indent=2))
    if results:
        pd.DataFrame(results).to_csv(out / "quality.csv", index=False)
    artifacts = {p.relative_to(out).as_posix(): sha(p) for p in out.rglob("*") if p.is_file()}
    report = {
        "version": "preevent_image_windows_v1",
        "status": "windows_read_method_review_only"
        if len(results) == 25
        else "incomplete_retained",
        "completed_points": len(results),
        "failures": failures,
        "expected_points": 25,
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "final_merge_performed": False,
        "cloud_jobs_started": 0,
        "validation_or_final_test_accessed": False,
        "human_review_completed": False,
        "network_transfer_bytes_measured": False,
        "artifact_sha256": artifacts,
    }
    (out / "readback.json").write_text(json.dumps(report, indent=2))
    print("Result:", out.relative_to(ROOT).as_posix())
    print("Readback SHA256:", sha(out / "readback.json"))
    return 0 if len(results) == 25 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("Window control incomplete:", type(error).__name__)
        sys.exit(1)
