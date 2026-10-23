"""Bounded anonymous STAC inventory for the frozen 25 training points.

Downloads metadata only. No Earth Engine tasks, signed asset access or raster reads.
All scenes are retained; cloud percentage ranks review candidates, not acceptance.
"""

import argparse
import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform

from wildfire_risk_prediction.preevent_imagery import inspect_item, prediction_time

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://planetarycomputer.microsoft.com/api/stac/v1"
PARENT = ROOT / "outputs/reports/dataset/native_candidate_cover_v1/20261023T143656Z_90c1c93b"
PARENT_SHA = "65443618bddc95f01a453f0186473891112d9712b50289e3c4613ac71470568b"


def digest(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-cache", type=Path)
    args = parser.parse_args()
    cache = args.metadata_cache.resolve() if args.metadata_cache else None
    if cache is not None:
        require(
            cache.is_relative_to(ROOT / "outputs/reports/dataset/preevent_imagery_inventory_v1"),
            "Cache must be a retained inventory",
        )
        require((cache / "metadata").is_dir(), "Metadata cache missing")
    pins = {}

    def pin(path, expected=None):
        actual = digest(path)
        require(expected is None or actual == expected, "Input hash mismatch")
        pins[path.relative_to(ROOT).as_posix()] = actual
        return path

    parent = json.loads(pin(PARENT / "readback.json", PARENT_SHA).read_text())
    require(not parent["labels_created"], "Parent must remain unlabelled")
    points = pd.read_csv(
        pin(
            PARENT / "native_point_context.csv",
            parent["artifact_sha256"]["native_point_context.csv"],
        )
    )
    geometry = json.loads(
        pin(
            PARENT / "approximate_support_geometry.json",
            parent["artifact_sha256"]["approximate_support_geometry.json"],
        ).read_text()
    )
    require(geometry["crs"] == "EPSG:6933" and not geometry["official_corners"], "Support CRS")
    geometries = {p["detection_id"]: p for p in geometry["points"]}
    require(len(points) == 25 and points.detection_id.is_unique, "Frozen 25 points")
    require(set(geometries) == set(points.detection_id), "All support geometries required")
    pin(Path(__file__).resolve())
    pin(ROOT / "src/wildfire_risk_prediction/preevent_imagery.py")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/preevent_imagery_inventory_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    raw = out / "metadata"
    raw.mkdir()
    session = requests.Session()
    # No Earthdata/Google credentials, proxies or netrc credentials are used.
    session.trust_env = False
    requests_made = 0

    def get(url, params, destination):
        nonlocal requests_made
        parsed = urlparse(url)
        require(
            parsed.scheme == "https"
            and parsed.netloc == "planetarycomputer.microsoft.com"
            and parsed.path.startswith("/api/stac/v1/"),
            "Public catalog origin only",
        )
        if cache is not None:
            cached = pin(cache / "metadata" / destination.name)
            destination.write_bytes(cached.read_bytes())
            return json.loads(destination.read_bytes())
        requests_made += 1
        response = session.get(url, params=params, timeout=(15, 45), allow_redirects=False)
        require(response.status_code == 200, "Catalog HTTP request failed")
        require(len(response.content) < 25_000_000, "Metadata response size bound")
        destination.write_bytes(response.content)
        return json.loads(destination.read_bytes())

    try:
        collection = get(BASE + "/collections/sentinel-2-l2a", None, raw / "collection.json")
        require(collection["id"] == "sentinel-2-l2a", "Collection identity")
        projector = Transformer.from_crs(6933, 4326, always_xy=True).transform
        rows, summaries = [], []
        for point in points.itertuples(index=False):
            cutoff = prediction_time(point.detection_timestamp_utc)
            support = transform(
                projector, Polygon(geometries[point.detection_id]["approximate_corners_6933"])
            )
            require(support.is_valid and not support.is_empty, "Valid support")
            params = {
                "collections": "sentinel-2-l2a",
                "bbox": ",".join(map(str, support.bounds)),
                "datetime": (cutoff - timedelta(days=60)).isoformat() + "/" + cutoff.isoformat(),
                "limit": 100,
            }
            query = {
                "detection_id": point.detection_id,
                "prediction_utc": cutoff.isoformat(),
                "params": params,
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
            }
            if cache is not None:
                previous = json.loads(
                    pin(cache / "metadata" / f"{point.detection_id}_query.json").read_text()
                )
                require(
                    previous["params"] == params
                    and previous["prediction_utc"] == cutoff.isoformat(),
                    "Cache query mismatch",
                )
                query["retrieved_at_utc"] = previous["retrieved_at_utc"]
            (raw / f"{point.detection_id}_query.json").write_text(json.dumps(query, indent=2))
            url, seen_ids, local = BASE + "/search", set(), []
            for page in range(5):
                data = get(url, params, raw / f"{point.detection_id}_page{page}.json")
                require(data["type"] == "FeatureCollection", "STAC collection response")
                for item in data["features"]:
                    require(item["id"] not in seen_ids, "Repeated item across pages")
                    seen_ids.add(item["id"])
                    inspected = inspect_item(item, support, cutoff)
                    inspected.update(
                        detection_id=point.detection_id,
                        prediction_utc=cutoff.isoformat(),
                        grid_id=point.grid_id,
                    )
                    local.append(inspected)
                next_links = [link for link in data.get("links", []) if link["rel"] == "next"]
                require(len(next_links) <= 1, "Ambiguous pagination")
                if not next_links:
                    break
                require(page < 4, "Pagination bound exceeded; inventory incomplete")
                require(next_links[0].get("method", "GET") == "GET", "Unsupported pagination")
                url, params = next_links[0]["href"], None
            rows.extend(local)
            candidates = [r for r in local if r["metadata_candidate"]]
            ranked = sorted(
                candidates,
                key=lambda r: (
                    r["scene_cloud_percent"] is None,
                    r["scene_cloud_percent"] if r["scene_cloud_percent"] is not None else 101,
                    r["days_before_prediction"],
                    r["item_id"],
                ),
            )
            for rank, row in enumerate(ranked, 1):
                row["review_rank_scene_cloud_then_recency"] = rank
            best = ranked[0] if ranked else {}
            summaries.append(
                {
                    "detection_id": point.detection_id,
                    "prediction_utc": cutoff.isoformat(),
                    "items_returned": len(local),
                    "metadata_candidates_60d": len(candidates),
                    "metadata_candidates_30d": sum(
                        r["days_before_prediction"] <= 30 for r in candidates
                    ),
                    "distinct_acquisition_times": len({r["acquired_utc"] for r in candidates}),
                    "first_review_item": best.get("item_id"),
                    "first_review_scene_cloud_percent": best.get("scene_cloud_percent"),
                    "first_review_age_days": best.get("days_before_prediction"),
                    "first_review_generated_after_prediction": best.get(
                        "product_generated_after_prediction"
                    ),
                    "pixel_quality_checked": False,
                    "habitat_accepted": False,
                }
            )
            print(point.detection_id, "metadata_candidates", len(candidates), flush=True)
        for name, values in (("scene_inventory.csv", rows), ("point_summary.csv", summaries)):
            frame = pd.DataFrame(values)
            frame.to_csv(out / name, index=False)
            pd.testing.assert_frame_equal(
                frame,
                pd.read_csv(
                    out / name,
                    float_precision="round_trip",
                    dtype={"processing_baseline": str} if name == "scene_inventory.csv" else None,
                ),
                check_dtype=False,
            )
        for path, expected in pins.items():
            require(digest(ROOT / path) == expected, "Input changed")
        (out / "input_manifest.json").write_text(json.dumps(pins, indent=2))
        artifacts = {
            p.relative_to(out).as_posix(): digest(p) for p in out.rglob("*") if p.is_file()
        }
        report = {
            "version": "preevent_imagery_inventory_v1",
            "status": "metadata_inventory_only",
            "source_points": len(points),
            "scene_point_rows": len(rows),
            "unique_items": len({r["item_id"] for r in rows}),
            "points_with_60d_candidates": sum(s["metadata_candidates_60d"] > 0 for s in summaries),
            "points_with_30d_candidates": sum(s["metadata_candidates_30d"] > 0 for s in summaries),
            "first_review_generated_after_prediction": sum(
                s["first_review_generated_after_prediction"] is True for s in summaries
            ),
            "lookback_days_exploratory": 60,
            "cloud_threshold_applied": False,
            "network_requests": requests_made,
            "cloud_jobs_started": 0,
            "raster_bytes_downloaded": 0,
            "daily_observation_status": "unknown",
            "positive_label_permitted": False,
            "negative_label_permitted": False,
            "labels_created": False,
            "final_merge_performed": False,
            "validation_or_final_test_accessed": False,
            "historical_available_at_verified": False,
            "artifact_sha256": artifacts,
        }
        (out / "readback.json").write_text(json.dumps(report, indent=2))
        require(json.loads((out / "readback.json").read_text()) == report, "Report roundtrip")
        (out / "completion_readback.json").write_text(
            json.dumps(
                {
                    "report_sha256": digest(out / "readback.json"),
                    "all_inputs_unchanged": True,
                    "csv_full_roundtrip_passed": True,
                    "scientific_label_acceptance": False,
                },
                indent=2,
            )
        )
        print("Result:", out.relative_to(ROOT).as_posix())
        print("Readback SHA256:", digest(out / "readback.json"))
    except Exception as error:
        (out / "failure.json").write_text(
            json.dumps(
                {
                    "status": "incomplete_outputs_retained",
                    "error_type": type(error).__name__,
                    "network_requests": requests_made,
                    "scientific_label_acceptance": False,
                },
                indent=2,
            )
        )
        print("Incomplete inventory retained:", out.relative_to(ROOT).as_posix())
        raise


if __name__ == "__main__":
    main()
