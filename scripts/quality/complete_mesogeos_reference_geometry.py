"""Complete context geometry from the authorized browser download; no HTTP retry."""

import argparse
import csv
import hashlib
import json
import shutil
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pyogrio
from pyproj import CRS
from shapely import wkt
from shapely.geometry import mapping, shape

from wildfire_risk_prediction.mesogeos_reference import shp_header

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "mesogeos_reference_pilot_run_v1/20261124T231948Z_e9a7e57e"
EXPECTED_SHAPE = "82c52d06cad0beb01e5c2cc4127e50875301f877eb2ea9309384fce0ebbbA22b".lower()


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def save(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def require(value, note):
    if not value:
        raise ValueError(note)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    original_start = datetime.strptime(RUN.name.split("_")[0], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    require(
        (datetime.now(UTC) - original_start).total_seconds() < 900, "Original pilot wall-time bound"
    )
    original = json.loads((RUN / "readback.json").read_bytes())
    require(
        original["status"] == "phase_one_complete_phase_two_stopped_outputs_retained",
        "Preserved first-stage outcome",
    )
    require(
        original["stop_code"] == "public_access_requires_manual_step",
        "No repeated HTTP file attempts",
    )
    original_raw = ROOT / original["source_directory"]
    for name, expected in original["raw_file_sha256"].items():
        require(digest(original_raw / name) == expected, "Preserved first-stage raw members")
    for name, expected in original["artifact_sha256"].items():
        if name != "child.log":
            require(digest(RUN / name) == expected, "Preserved first-stage artifacts")
    launcher = json.loads((RUN / "launcher_receipt.json").read_bytes())
    require(launcher["returncode"] == 0, "Completed first-stage child")
    source = args.download.resolve()
    require(
        source.name == "med_burned_areas_updated.shp" and source.stat().st_size == 107123300,
        "Browser-delivered public vector size/name",
    )
    require(digest(source) == EXPECTED_SHAPE, "Observed browser download snapshot")
    with source.open("rb") as handle:
        header = shp_header(handle.read(100))
    require(
        header["file_bytes_declared"] == source.stat().st_size and header["shape_type"] == 5,
        "Native polygon file header",
    )
    require(
        original["file_bytes_read"] + source.stat().st_size == 159822559,
        "Original complete file-transfer budget",
    )
    out = (
        BASE
        / "mesogeos_reference_geometry_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    raw = ROOT / "data/raw/external/mesogeos_reference_geometry_v1" / out.name
    raw.mkdir(parents=True, exist_ok=False)
    for item in original_raw.iterdir():
        require(
            item.is_file() and item.name in original["raw_file_sha256"],
            "Only verified prior members",
        )
        shutil.copyfile(item, raw / item.name)
    shutil.copyfile(source, raw / source.name)
    with (RUN / "point_context_review.csv").open(encoding="utf-8", newline="") as handle:
        points = list(csv.DictReader(handle))
    ids = [int(row["source_record_index"]) for row in points]
    require(len(ids) == len(set(ids)) == 92, "Exact preserved AOI context set")
    require(
        all(
            row["YEAR"] in {"2018", "2019", "2020", "2021", "2022"}
            and row["IGNITION_D"][:4] in {"2018", "2019", "2020", "2021", "2022"}
            and not row["target"]
            and not row["accepted_L_membership"]
            and row["negative_label_permitted"] == "False"
            for row in points
        ),
        "Preserved open-year unknown targets",
    )
    polygons = pyogrio.read_dataframe(
        raw / source.name, columns=[], fids=ids, fid_as_index=True, use_arrow=False
    )
    require(set(map(int, polygons.index)) == set(ids), "Exact open-year feature index set")
    require(
        polygons.crs == CRS.from_epsg(5643) and list(polygons.columns) == ["geometry"],
        "Only selected geometries, no unselected year attributes",
    )
    geographic, equal_area = polygons.to_crs(4326), polygons.to_crs(6933)
    aoi = shape(json.loads((ROOT / "data/aoi/aoi.geojson").read_bytes())["features"][0]["geometry"])
    rows, features = [], []
    for context in points:
        i = int(context["source_record_index"])
        native, point = polygons.loc[i].geometry, wkt.loads(context["geometry_h"])
        valid = native is not None and not native.is_empty and native.is_valid
        row = {
            "source_record_index": i,
            "source_id": context["id"],
            "YEAR": context["YEAR"],
            "IGNITION_D_native_unchanged": context["IGNITION_D"],
            "geometry_type": native.geom_type if native is not None else None,
            "geometry_valid": bool(valid),
            "native_point_covered_by_final_perimeter": bool(native.covers(point))
            if valid
            else None,
            "native_point_to_final_perimeter_distance_m": float(native.distance(point))
            if valid
            else None,
            "perimeter_intersects_AOI": bool(geographic.loc[i].geometry.intersects(aoi))
            if valid
            else None,
            "perimeter_equal_area_ha": float(equal_area.loc[i].geometry.area / 10000)
            if valid
            else None,
            "target": None,
            "accepted_L_membership": None,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
        }
        rows.append(row)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "source_record_index": i,
                    "source_id": context["id"],
                    "YEAR": context["YEAR"],
                    "source_role": "supplementary_satellite_context_not_independent_truth",
                },
                "geometry": mapping(geographic.loc[i].geometry) if native is not None else None,
            }
        )
    with (out / "perimeter_context_review.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    save(out / "selected_perimeters.geojson", {"type": "FeatureCollection", "features": features})
    require(
        (datetime.now(UTC) - original_start).total_seconds() < 900,
        "Total original pilot wall-time bound",
    )
    result = {
        "status": "bounded_supplementary_reference_review_complete_pending_separate_audit",
        "analysis_date": "2026-11-25",
        "first_stage_receipt_sha256": digest(RUN / "readback.json"),
        "first_stage_point_review_sha256": digest(RUN / "point_context_review.csv"),
        "source_directory": raw.relative_to(ROOT).as_posix(),
        "browser_acquisition": {
            "source_url": "https://drive.google.com/file/d/1gutT6YXYALaOxkStzvsCFS1ioie_wzj5/view",
            "filename": source.name,
            "bytes": source.stat().st_size,
            "sha256": digest(source),
            "workflow": (
                "authorized_specific_public_file_download_completed_via_normal_browser_"
                "after_HTTP_worker_stopped"
            ),
            "provider_checksum_independently_verified": False,
        },
        "total_original_file_bytes_received": original["file_bytes_read"] + source.stat().st_size,
        "elapsed_geometry_seconds": time.monotonic() - started,
        "elapsed_from_original_run_seconds": (datetime.now(UTC) - original_start).total_seconds(),
        "selected_rows": len(rows),
        "raw_year_counts": dict(Counter(row["YEAR"] for row in rows)),
        "first_stage_streaming_log": {
            "worker_time_hash_before_last_stdout": original["artifact_sha256"]["child.log"],
            "post_launcher_sha256": digest(RUN / "child.log"),
            "post_launcher_receipt_sha256": digest(RUN / "launcher_receipt.json"),
            "only_mutable_log_excluded_from_original_artifact_hash_check": True,
        },
        "valid_geometries": sum(r["geometry_valid"] for r in rows),
        "point_covered_rows": sum(
            r["native_point_covered_by_final_perimeter"] is True for r in rows
        ),
        "perimeters_intersecting_AOI": sum(r["perimeter_intersects_AOI"] is True for r in rows),
        "new_training_or_predictions": False,
        "new_Y_or_L": False,
        "source_absence_is_negative": False,
        "final_merge": False,
        "raw_file_sha256": {p.name: digest(p) for p in raw.iterdir()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    save(out / "readback.json", result)
    print(out.relative_to(ROOT).as_posix())
    print(
        "rows",
        len(rows),
        "valid",
        result["valid_geometries"],
        "point_covered",
        result["point_covered_rows"],
    )


if __name__ == "__main__":
    main()
