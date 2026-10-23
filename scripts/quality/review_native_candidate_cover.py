"""Offline, fixed 25-point native support/2017-map audit; no labels or new downloads."""

import csv
import hashlib
import importlib.util
import json
import socket
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
import rasterio
from pyproj import Geod, Transformer, network
from rasterio.windows import Window

from wildfire_risk_prediction.native_cover_context import (
    center_patch_polygon,
    overlap_reference_map,
    rounded_coordinate_matches,
)

ROOT = Path(__file__).resolve().parents[2]
POINTS = "outputs/reports/dataset/linked_candidate_context_v1/20261022T210339Z_23e2e5a4"
PILOT = "outputs/reports/dataset/observation_pilot_run_v1/20261015T134047Z_b6b84ca8"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline local native support audit")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    network.set_network_enabled(False)
    pins = {}

    def retain(name, expected=None):
        path = ROOT / name
        require(
            path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
            "Contained input",
        )
        actual = digest(path)
        require(expected is None or actual == expected, "Input hash mismatch")
        pins[path.relative_to(ROOT).as_posix()] = actual
        return path

    def read(name, expected=None):
        return json.loads(retain(name, expected).read_text(encoding="utf-8"))

    parent = read(
        POINTS + "/readback.json",
        "58363f7e1640af945195ecf9d13144a5ec4951fb259a30816274c12956710de8",
    )
    points = pd.read_csv(
        retain(
            POINTS + "/first_point_cover.csv", parent["artifact_sha256"]["first_point_cover.csv"]
        ),
        float_precision="round_trip",
    )
    require(len(points) == 25 and points.detection_id.is_unique, "Fixed 25 source points")
    run = read(
        PILOT + "/readback.json", "51e9f504ad2a6c6334ec37f5d5080b70185d1e35d9c4177c7906fa4032d65885"
    )
    require(
        run["all_planned_pairs_processed"] and run["labels_created"] is False,
        "Completed method pilot only",
    )
    source = retain(
        "data/interim/firms_combined_candidates_2018_2024.csv",
        "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5",
    )
    records = {}
    skipped = 0
    with source.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            year = int(row["detection_timestamp_utc"][:4])
            require(2018 <= year <= 2024, "Source period")
            if year == 2024:
                skipped += 1
                continue
            if row["detection_id"] in set(points.detection_id):
                require(row["detection_id"] not in records, "Unique source ID")
                records[row["detection_id"]] = row
    require(set(records) == set(points.detection_id), "Every point present in training source")
    audits = []
    for key, receipt in run["pair_receipts"].items():
        folder = receipt["path"]
        report = read(folder + "/readback.json", receipt["report_sha256"])
        require(report["sample_id"] == key, "Receipt identity")
        names = [n for n in report["artifact_sha256"] if n.endswith("_audit.json")]
        require(len(names) == 1, "Single native audit")
        audit = read(folder + "/" + names[0], report["artifact_sha256"][names[0]])
        audits.append((key, folder, report, audit))
    script = retain("scripts/firms/inspect_l2_observation_sample.py")
    spec = importlib.util.spec_from_file_location("retained_native_audit", script)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    for name in (
        "scripts/quality/review_native_candidate_cover.py",
        "src/wildfire_risk_prediction/native_cover_context.py",
        "src/wildfire_risk_prediction/point_cover_context.py",
        "src/wildfire_risk_prediction/landscape.py",
        "configs/habitat_scope_direction_v1.json",
    ):
        retain(name)
    raster = retain(
        "data/raw/landcover/landcover_copernicus_2017.tif",
        "ee8bd6c9f742dbbdfcdcbbb6ecc446499f05d676eaeb202c4345c11ea6006470",
    )
    out = (
        ROOT
        / "outputs/reports/dataset/native_candidate_cover_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    result, geometries, selected_pairs = [], [], set()
    with rasterio.open(raster) as reference, warnings.catch_warnings():
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        for point in points.itertuples():
            original = records[point.detection_id]
            stamp = pd.Timestamp(original["detection_timestamp_utc"])
            require(stamp == pd.Timestamp(point.detection_timestamp_utc), "Point time identity")
            require(
                float(original["longitude"]) == point.longitude
                and float(original["latitude"]) == point.latitude,
                "Point coordinate identity",
            )
            scan, track = float(original["scan"]), float(original["track"])
            require(
                np.isfinite([scan, track]).all() and min(scan, track) > 0,
                "Positive finite source dimensions",
            )
            row = {
                "detection_id": point.detection_id,
                "grid_id": point.grid_id,
                "detection_timestamp_utc": stamp.isoformat(),
                "center_cover_group_2017": point.center_cover_group_2017,
                "scan_km": scan,
                "track_km": track,
                "reference_year": 2017,
                "reference_age_calendar_years": stamp.year - 2017,
                "native_match_status": "unresolved",
                "support_status": "unresolved",
                "official_pixel_corners": False,
                "current_cover_verified": False,
                "habitat_label_accepted": False,
                "positive_label_permitted": False,
                "negative_label_permitted": False,
                "target": np.nan,
                "forest_shrub_reference_area_m2": np.nan,
                "reference_cover_groups": "[]",
                "archive_native_distance_m": np.nan,
            }
            candidates = [
                a
                for a in audits
                if a[3]["sensor"] == original["source_sensor"]
                and pd.Timestamp(a[3]["start_utc"]) <= stamp < pd.Timestamp(a[3]["end_utc"])
            ]
            if len(candidates) != 1:
                row["native_match_status"] = "missing_or_ambiguous_granule"
                result.append(row)
                continue
            key, folder, report, audit = candidates[0]
            paths = {
                role: retain(value["path"], value["sha256"])
                for role, value in audit["sources"].items()
            }
            selected_pairs.add(key)
            row["sample_id"] = key
            with ExitStack() as stack:
                fire = native.layer(stack, paths["fire"], "fire_mask")
                qa = native.layer(stack, paths["fire"], "algorithm_QA")
                latds, londs = [
                    native.layer(stack, paths["geolocation"], "geolocation_data/" + k)
                    for k in ("latitude", "longitude")
                ]
                native.validate_pair(paths["fire"], paths["geolocation"], fire.tags(), latds.tags())
                sparse = native.read_sparse(stack, paths["fire"], audit["sparse_fire_count"])
                matches = rounded_coordinate_matches(
                    point.latitude, point.longitude, sparse["FP_latitude"], sparse["FP_longitude"]
                )
                row["rounded_coordinate_matches"] = len(matches)
                if len(matches) != 1:
                    row["native_match_status"] = "missing_or_ambiguous_coordinate"
                    result.append(row)
                    continue
                index = matches[0]
                r, c = int(sparse["FP_line"][index]), int(sparse["FP_sample"][index])
                require(0 <= r < fire.height and 0 <= c < fire.width, "Native pixel range")
                window = Window(c, r, 1, 1)
                actual = int(fire.read(1, window=window).item())
                quality = int(qa.read(1, window=window).item())
                lon, lat = [float(ds.read(1, window=window).item()) for ds in (londs, latds)]
                require(
                    actual
                    == int(sparse["FP_confidence"][index])
                    == {"n": 8, "h": 9}[original["confidence"]],
                    "Native confidence agrees with archive",
                )
                require(
                    abs(lon - sparse["FP_longitude"][index]) <= 1e-5
                    and abs(lat - sparse["FP_latitude"][index]) <= 1e-5,
                    "Native orientation matches sparse coordinates",
                )
                row.update(
                    native_match_status="unique_coordinate_and_confidence_match",
                    native_row=r,
                    native_column=c,
                    input_non_nominal=bool(quality & 127),
                    residual_bowtie=bool(quality & (1 << 22)),
                    archive_native_distance_m=float(
                        Geod(ellps="WGS84").inv(point.longitude, point.latitude, lon, lat)[2]
                    ),
                )
                if r % 32 in (0, 31) or c in (0, fire.width - 1):
                    row["support_status"] = "scan_or_swath_edge_no_patch"
                    result.append(row)
                    continue
                patch = Window(c - 1, r - 1, 3, 3)
                try:
                    polygon = center_patch_polygon(
                        londs.read(1, window=patch), latds.read(1, window=patch), r
                    )
                except ValueError:
                    row["support_status"] = "invalid_native_patch"
                    result.append(row)
                    continue
                overlap = overlap_reference_map(polygon, reference)
                overlap["reference_cover_groups"] = json.dumps(overlap["reference_cover_groups"])
                row.update(overlap, support_status="approximate_native_center_support")
                geometries.append(
                    {
                        "detection_id": point.detection_id,
                        "native_center_6933": list(
                            Transformer.from_crs(4326, 6933, always_xy=True).transform(lon, lat)
                        ),
                        "approximate_corners_6933": list(polygon.exterior.coords),
                    }
                )
                result.append(row)
    frame = pd.DataFrame(result)
    require(
        len(frame) == 25 and frame.detection_id.is_unique and frame.target.isna().all(),
        "All points retained without labels",
    )
    csv_path = out / "native_point_context.csv"
    frame.to_csv(csv_path, index=False)
    pd.testing.assert_frame_equal(
        frame, pd.read_csv(csv_path, float_precision="round_trip"), check_dtype=False
    )
    (out / "approximate_support_geometry.json").write_text(
        json.dumps({"crs": "EPSG:6933", "official_corners": False, "points": geometries}, indent=2)
        + "\n"
    )
    for name, expected in pins.items():
        require(digest(ROOT / name) == expected, "Input changed during audit")
    (out / "input_manifest.json").write_text(json.dumps(pins, indent=2) + "\n")
    artifacts = {
        name: digest(out / name)
        for name in (
            "native_point_context.csv",
            "approximate_support_geometry.json",
            "input_manifest.json",
        )
    }
    valid = frame.support_status.eq("approximate_native_center_support")
    outside = ~frame.center_cover_group_2017.isin(["forest", "shrub"])
    report = {
        "version": "native_candidate_cover_v1",
        "client_date": "2026-10-23",
        "status": "native_match_and_reference_overlap_only",
        "source_points": len(frame),
        "selected_native_pairs": len(selected_pairs),
        "native_match_counts": frame.native_match_status.value_counts().to_dict(),
        "support_counts": frame.support_status.value_counts().to_dict(),
        "noncore_center_points": int(outside.sum()),
        "noncore_centers_with_reconstructed_support": int((outside & valid).sum()),
        "noncore_centers_with_forest_shrub_overlap": int(
            (outside & valid & frame.forest_shrub_reference_area_m2.gt(1e-6)).sum()
        ),
        "points_with_mixed_reference_classes": int(
            frame.loc[valid, "reference_cover_groups"].map(lambda x: len(json.loads(x)) > 1).sum()
        ),
        "reference_age_counts": {
            str(k): int(v)
            for k, v in frame.reference_age_calendar_years.value_counts().sort_index().items()
        },
        "scan_km_range": [frame.scan_km.min(), frame.scan_km.max()],
        "track_km_range": [frame.track_km.min(), frame.track_km.max()],
        "max_archive_native_distance_m": frame.archive_native_distance_m.max(),
        "validation_rows_date_filtered_only": skipped,
        "final_test_accessed": False,
        "network_requests": 0,
        "cloud_jobs_started": 0,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
        "input_count": len(pins),
        "artifact_sha256": artifacts,
    }
    (out / "readback.json").write_text(json.dumps(report, indent=2) + "\n")
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
        + "\n"
    )
    print(json.dumps(report, indent=2))
    print("Result:", out.relative_to(ROOT).as_posix())
    print("Readback SHA256:", digest(out / "readback.json"))


if __name__ == "__main__":
    main()
