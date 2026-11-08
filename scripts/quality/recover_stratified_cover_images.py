"""Retry unread pilot windows with shared public access and keep the original receipt."""

import argparse
import logging
from collections import Counter
from datetime import UTC, datetime
from uuid import uuid4

import rasterio
import requests
from pyproj import Transformer
from rasterio.plot import plotting_extent
from review_public_event_cover import QA_FLAGS, catalogue, plt, require, sha
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json
from shapely.geometry import Point
from shapely.ops import transform

from wildfire_risk_prediction.preevent_imagery import prediction_time, utc_time
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows

SAFE_ERRORS = {
    "Expected local UTM",
    "Public token unavailable",
    "Asset headers",
    "Raster identity",
    "Transform",
    "Native encoding",
    "Unexpected public asset",
    "Approximate support crosses raster boundary",
    "Catalogue HTTP 429",
    "Catalogue HTTP 503",
}


def retry_image(row, out, session, reader):
    key = {"slot": row["slot"], "id": row["id"]}
    stage = "catalogue"
    try:
        lon, lat = row["longitude"], row["latitude"]
        zone = 32635 if lon < 30 else 32636
        projection = Transformer.from_crs(4326, zone, always_xy=True)
        circle = Point(*projection.transform(lon, lat)).buffer(250)
        support = transform(Transformer.from_crs(zone, 4326, always_xy=True).transform, circle)
        count, scenes = catalogue(session, support, prediction_time(row["detected_utc"]))
        if not scenes:
            return {**key, "state": "no_scene"}
        item, meta = scenes[0]
        stage = "asset"
        target = transform(
            Transformer.from_crs(4326, item["properties"]["proj:epsg"], always_xy=True).transform,
            support,
        )
        folder = out / row["slot"]
        folder.mkdir()
        assets, quality = reader.read(item, target, folder)
        return {
            **key,
            "state": "read",
            "acquired_utc": meta["acquired_utc"],
            "item_id": item["id"],
            "metadata_candidates": count,
            "assets": assets,
            "quality": quality,
            "zero_selected_flags": all(quality[k] == 0 for k in QA_FLAGS),
        }
    except Exception as exc:
        reason = str(exc)
        return {
            **key,
            "state": "failed",
            "stage": stage,
            "error_type": type(exc).__name__,
            "safe_reason": reason if reason in SAFE_ERRORS else None,
        }


def sheets(out, points, records):
    artifacts = {}
    for start in range(0, len(points), 6):
        fig, axes = plt.subplots(2, 3, figsize=(12, 8.4), layout="constrained")
        for ax in axes.flat:
            ax.set_axis_off()
        for ax, point, result in zip(
            axes.flat, points[start : start + 6], records[start : start + 6], strict=True
        ):
            date = "Kesit yok"
            if result["state"] == "read":
                with rasterio.open(ROOT / result["crop_directory"] / "visual.tif") as ds:
                    ax.imshow(ds.read().transpose(1, 2, 0), extent=plotting_extent(ds))
                    x, y = Transformer.from_crs(4326, ds.crs, always_xy=True).transform(
                        point["longitude"], point["latitude"]
                    )
                    ax.plot(*Point(x, y).buffer(250).exterior.xy, color="#ffe13b", linewidth=1.5)
                    ax.scatter(x, y, marker="+", color="white")
                    ax.set(xlim=(x - 380, x + 380), ylim=(y - 380, y + 380))
                date = result["acquired_utc"][:10]
            ax.set_title(f"{point['slot']} | {date}")
        fig.suptitle("Olay öncesi Sentinel-2 | Sarı: 250 m çevre")
        path = out / f"sheet_{points[start]['slot']}.png"
        fig.savefig(path, dpi=140)
        plt.close(fig)
        artifacts[path.name] = sha(path)
    return artifacts


def main(plan_path, plan_sha, image_sha):
    require(plan_path.resolve(strict=True).is_relative_to(BASE), "Contained plan")
    first_path = plan_path.parent / "images/readback.json"
    require(sha(plan_path) == plan_sha and sha(first_path) == image_sha, "Frozen source reports")
    plan, first = read_json(plan_path), read_json(first_path)
    require(first["plan_sha256"] == plan_sha, "Image plan identity")
    points = plan["selected"]
    require(len(points) == len(first["records"]) == 24, "Pilot denominator")
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = plan_path.parent / f"recovery_{run}"
    out.mkdir(exist_ok=False)
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    reader, records = PublicWindows(), []
    try:
        with requests.Session() as session:
            session.trust_env = False
            for point, original in zip(points, first["records"], strict=True):
                slot = point["slot"]
                require(slot == original["slot"] and point["id"] == original["id"], "Exact slot")
                record, directory = original, first_path.parent
                if original["state"] == "failed":
                    record, directory = retry_image(point, out, session, reader), out
                if record["state"] == "read":
                    folder = directory / slot
                    require(
                        all(
                            sha(folder / f"{k}.tif") == v["sha256"]
                            for k, v in record["assets"].items()
                        ),
                        "Unchanged crop bytes",
                    )
                    require(
                        utc_time(record["acquired_utc"]) < prediction_time(point["detected_utc"]),
                        "Temporal cutoff",
                    )
                    record = {**record, "crop_directory": folder.relative_to(ROOT).as_posix()}
                records.append(record)
                print(slot, record["state"], record.get("safe_reason"), flush=True)
    finally:
        reader.close()
    require(
        sha(plan_path) == plan_sha and sha(first_path) == image_sha,
        "Unchanged plan and images receipt",
    )
    report = {
        "plan_sha256": plan_sha,
        "first_image_receipt_sha256": image_sha,
        "recovery_script_sha256": sha(ROOT / "scripts/quality/recover_stratified_cover_images.py"),
        "records": records,
        "outcomes": dict(Counter(r["state"] for r in records)),
        "artifact_sha256": sheets(out, points, records),
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    write_json(out / "readback.json", report)
    print(
        (out / "readback.json").relative_to(ROOT).as_posix(),
        sha(out / "readback.json"),
        report["outcomes"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan")
    parser.add_argument("plan_sha")
    parser.add_argument("image_sha")
    args = parser.parse_args()
    main(ROOT / args.plan, args.plan_sha, args.image_sha)
