"""Measure local center geometry in audited training swaths; never certify footprints.

All sparse thermal detections are retained, including unreconstructable edges.
The three existing FIRMS controls remain the only archived size references.
Other detections broaden angle/terrain diagnostics, not ground-truth validation.
"""

import argparse
import importlib.util
import json
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Geod, Transformer
from rasterio.windows import Window

SPEC = importlib.util.spec_from_file_location(
    "area", Path(__file__).with_name("estimate_l2_observed_area.py")
)
area = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(area)
audit = area.audit
GEOD = Geod(ellps="WGS84")
PROJECT = Transformer.from_crs(4326, 6933, always_xy=True)
UNPROJECT = Transformer.from_crs(6933, 4326, always_xy=True)
# Zero-based boundaries from the NASA geolocation ATBD, pp. 55–56.
AGGREGATION_BOUNDARIES = np.array([1280, 2016, 4384, 5120])


def aggregation_count(column):
    audit.require(int(column) == column and 0 <= column < 6400, "Invalid native column")
    return int((1, 2, 3, 2, 1)[np.searchsorted(AGGREGATION_BOUNDARIES, column, side="right")])


def decoded(dataset, window):
    """Apply native scale/offset only after removing the raw fill value."""
    raw = dataset.read(1, window=window).astype("float64")
    valid = np.isfinite(raw)
    if dataset.nodata is not None:
        valid &= raw != dataset.nodata
    scale, offset = dataset.scales[0], dataset.offsets[0]
    audit.require(np.isfinite(scale) and scale > 0 and np.isfinite(offset), "Bad field scaling")
    return np.where(valid, raw * scale + offset, np.nan)


def dimension_metrics(corners):
    audit.require(np.asarray(corners).shape == (4, 2), "Expected four projected corners")
    polygon = shapely.Polygon(corners)
    audit.require(polygon.is_valid and polygon.area > 0, "Invalid local polygon")
    lon, lat = UNPROJECT.transform(corners[:, 0], corners[:, 1])
    _, _, edges = GEOD.inv(lon, lat, np.roll(lon, -1), np.roll(lat, -1))
    scan_km, track_km = float(edges[[0, 2]].mean() / 1000), float(edges[[1, 3]].mean() / 1000)
    geodesic_area, _ = GEOD.polygon_area_perimeter(lon, lat)
    return {
        "estimated_scan_km": scan_km,
        "estimated_track_km": track_km,
        "geodesic_area_km2": abs(float(geodesic_area)) / 1e6,
        "equal_area_km2": polygon.area / 1e6,
    }


def neighborhood_metrics(lon, lat, height):
    """Asymmetry and terrain range are diagnostics, not error bounds or corrections."""
    audit.require(lon.shape == lat.shape == height.shape == (3, 3), "Expected local 3x3 patch")

    def distance(a, b):
        return float(GEOD.inv(lon[a], lat[a], lon[b], lat[b])[2])

    left, right = distance((1, 0), (1, 1)), distance((1, 1), (1, 2))
    above, below = distance((0, 1), (1, 1)), distance((1, 1), (2, 1))
    audit.require(min(left, right, above, below) > 0, "Repeated local centers")
    return {
        "left_spacing_m": left,
        "right_spacing_m": right,
        "above_spacing_m": above,
        "below_spacing_m": below,
        "scan_spacing_asymmetry": abs(right - left) / ((right + left) / 2),
        "track_spacing_asymmetry": abs(below - above) / ((below + above) / 2),
        "terrain_neighborhood_complete": bool(np.isfinite(height).all()),
        "terrain_height_range_m": float(np.ptp(height)) if np.isfinite(height).all() else None,
        "terrain_center_height_m": float(height[1, 1]) if np.isfinite(height[1, 1]) else None,
    }


def rounded_difference(estimated, reported):
    audit.require(np.isfinite(estimated) and estimated > 0, "Invalid estimated dimension")
    audit.require(np.isfinite(reported) and reported > 0, "Invalid reported dimension")
    # FIRMS dimensions in these controls have two decimal places in km.
    return {
        "relative_difference_percent": 100 * (estimated / reported - 1),
        "within_archive_rounding_interval": bool(abs(estimated - reported) <= 0.005 + 1e-12),
    }


def archive_reference(pilot, match):
    sensor, request, number = match["detection_id"].split("_")
    audit.require(sensor == "SNPP" and request == "815579", "Wrong control archive")
    selected = pilot.loc[pilot.source_record_number.eq(number)]
    audit.require(len(selected) == 1, "Missing or repeated control record")
    record = selected.iloc[0]
    audit.require(
        float(record["latitude"]) == match["archive_latitude"]
        and float(record["longitude"]) == match["archive_longitude"]
        and pd.Timestamp(record["detection_timestamp_utc"])
        == pd.Timestamp(match["archive_timestamp_utc"]),
        "Control coordinate/time mismatch",
    )
    return {
        "detection_id": match["detection_id"],
        "archive_scan_km": float(record["scan"]),
        "archive_track_km": float(record["track"]),
    }


def inspect(sensor, key, controls):
    path = audit.OUTPUT / f"{audit.sample_stem(sensor, key)}_audit.json"
    previous = json.loads(path.read_text(encoding="utf-8"))
    audit.require(previous["sensor"] == sensor and previous["pair_key"] == key, "Wrong audit")
    audit.require(previous["script_sha256"] == audit.digest(Path(audit.__file__)), "Stale audit")
    for name, file in [("aoi", "data/aoi/aoi.geojson"), ("grid", "data/aoi/grid_5km.geojson")]:
        audit.require(
            audit.digest(audit.ROOT / file) == previous[f"{name}_sha256"], "Geography changed"
        )
    for source in previous["sources"].values():
        audit.require(
            audit.digest(audit.ROOT / source["path"]) == source["sha256"], "Source changed"
        )
    fire, geo = (audit.ROOT / previous["sources"][role]["path"] for role in ("fire", "geolocation"))
    records = []
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask, qa = (audit.layer(stack, fire, n) for n in ("fire_mask", "algorithm_QA"))
        fields = {
            name: audit.layer(stack, geo, f"geolocation_data/{name}")
            for name in ("longitude", "latitude", "height", "sensor_zenith")
        }
        audit.validate_pair(fire, geo, mask.tags(), fields["latitude"].tags())
        audit.require(mask.width == 6400 and mask.height % 32 == 0, "Invalid imagery dimensions")
        audit.require(all(d.shape == mask.shape for d in [qa, *fields.values()]), "Shape mismatch")
        count = previous["sparse_fire_count"]
        sparse = audit.read_sparse(stack, fire, count)
        audit.require(
            ((sparse["FP_line"] >= 0) & (sparse["FP_line"] < mask.height)).all(),
            "Sparse row out of range",
        )
        view = audit.layer(stack, fire, "FP_ViewZenAng").read(1).ravel() if count else np.array([])
        audit.require(len(view) == count, "Sparse view length mismatch")
        for scan in np.unique(sparse["FP_line"].astype(int) // 32):
            window = Window(0, int(scan) * 32, 6400, 32)
            data = {name: decoded(d, window) for name, d in fields.items()}
            lon, lat = data["longitude"], data["latitude"]
            valid = np.isfinite(lon) & np.isfinite(lat) & (abs(lon) <= 180) & (abs(lat) <= 90)
            x, y = PROJECT.transform(np.where(valid, lon, np.nan), np.where(valid, lat, np.nan))
            corners, eligible = area.interior_corners(x, y)
            classes, quality = mask.read(1, window=window), qa.read(1, window=window)
            for index in np.flatnonzero(sparse["FP_line"].astype(int) // 32 == scan):
                row, col = int(sparse["FP_line"][index]), int(sparse["FP_sample"][index])
                local = row % 32
                audit.require(0 <= col < 6400, "Sparse column out of range")
                audit.require(
                    abs(lon[local, col] - sparse["FP_longitude"][index]) <= 1e-5
                    and abs(lat[local, col] - sparse["FP_latitude"][index]) <= 1e-5,
                    "Sparse/native coordinate mismatch",
                )
                audit.require(
                    classes[local, col] == sparse["FP_confidence"][index], "Class mismatch"
                )
                zenith = data["sensor_zenith"][local, col]
                audit.require(np.isfinite(zenith) and 0 <= zenith <= 90, "Invalid view zenith")
                audit.require(
                    abs(zenith - float(view[index])) < 0.011, "Native/sparse zenith mismatch"
                )
                q = int(quality[local, col])
                record = {
                    "sample_id": f"{sensor}:{key}",
                    "sensor": sensor,
                    "sparse_index": int(index),
                    "native_row": row,
                    "native_column": col,
                    "scan_index": int(scan),
                    "latitude": float(lat[local, col]),
                    "longitude": float(lon[local, col]),
                    "view_zenith_degrees": float(zenith),
                    "aggregation_count": aggregation_count(col),
                    "aggregation_boundary_neighbor": bool(
                        np.any(abs(AGGREGATION_BOUNDARIES - col) <= 1)
                    ),
                    "residual_bowtie": bool(q & (1 << 22)),
                    "input_non_nominal": bool(q & 127),
                    "geometry_status": "scan_or_swath_edge",
                    "negative_label_permitted": False,
                }
                if 0 < local < 31 and 0 < col < 6399:
                    record["geometry_status"] = "invalid_neighborhood"
                    if eligible[local - 1, col - 1]:
                        record["geometry_status"] = "reconstructed"
                        record.update(dimension_metrics(corners[local - 1, col - 1]))
                        patch = np.s_[local - 1 : local + 2, col - 1 : col + 2]
                        record.update(
                            neighborhood_metrics(lon[patch], lat[patch], data["height"][patch])
                        )
                reference = controls.get((f"{sensor}:{key}", row, col))
                if reference:
                    record.update(reference)
                    if record["geometry_status"] == "reconstructed":
                        for direction in ("scan", "track"):
                            diff = rounded_difference(
                                record[f"estimated_{direction}_km"],
                                reference[f"archive_{direction}_km"],
                            )
                            record.update({f"{direction}_{k}": v for k, v in diff.items()})
                records.append(record)
    audit.require(len(records) == count, "Sparse accounting mismatch")
    for source in previous["sources"].values():
        audit.require(
            audit.digest(audit.ROOT / source["path"]) == source["sha256"],
            "Source changed during read",
        )
    return records, {
        "audit_path": str(path.relative_to(audit.ROOT)),
        "audit_sha256": audit.digest(path),
        "sources": previous["sources"],
    }


def run(values):
    keys = [area.parse_key(value) for value in values]
    audit.require(len(keys) == len(set(keys)) and len(keys) > 0, "Expected distinct swaths")
    control_path = audit.OUTPUT / "l2_sample_2019013.0100_firms_control.json"
    control = json.loads(control_path.read_text(encoding="utf-8"))
    audit.require(
        control["source_hashes"]["script"]
        == audit.digest(Path(__file__).with_name("check_l2_firms_control.py")),
        "Stale control checker",
    )
    pilot_path = audit.ROOT / "data/interim/firms_pilot_2018_2024.csv"
    audit.require(
        audit.digest(pilot_path) == control["source_hashes"]["pilot_csv"], "Control CSV changed"
    )
    audit.require(
        audit.digest(audit.OUTPUT / "l2_sample_2019013.0100_audit.json")
        == control["source_hashes"]["audit"],
        "Control audit changed",
    )
    pilot = pd.read_csv(pilot_path, dtype=str, keep_default_na=False)
    controls = {}
    for match in control["matched_records"]:
        controls[("SNPP:2019013.0100", match["native_row"], match["native_column"])] = (
            archive_reference(pilot, match)
        )
    records, sources = [], {}
    for sensor, key in keys:
        rows, provenance = inspect(sensor, key, controls)
        records.extend(rows)
        sources[f"{sensor}:{key}"] = provenance
        print(f"Geometry diagnosis: {sensor}:{key}, sparse records={len(rows)}", flush=True)
    frame = pd.DataFrame(records)
    audit.require(len(frame) > 0, "No sparse detections in listed swaths")
    groups = []
    for (sensor, aggregation), subset in frame.groupby(["sensor", "aggregation_count"]):
        measured = subset.loc[subset.geometry_status.eq("reconstructed")]
        groups.append(
            {
                "sensor": sensor,
                "aggregation_count": int(aggregation),
                "count": len(subset),
                "reconstructed": len(measured),
                "metrics": {
                    field: {
                        "min": float(measured[field].min()),
                        "median": float(measured[field].median()),
                        "max": float(measured[field].max()),
                    }
                    for field in (
                        "view_zenith_degrees",
                        "estimated_scan_km",
                        "estimated_track_km",
                        "scan_spacing_asymmetry",
                        "terrain_height_range_m",
                    )
                    if len(measured) and measured[field].notna().any()
                },
            }
        )
    stem = audit.OUTPUT / "l2_geometry_diagnosis"
    csv_path = stem.with_suffix(".csv")
    frame.to_csv(csv_path, index=False)
    summary = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "diagnosis_only_physical_accuracy_unresolved",
        "area_method": area.METHOD,
        "script_sha256": audit.digest(Path(__file__)),
        "area_script_sha256": audit.digest(Path(area.__file__)),
        "inspector_script_sha256": audit.digest(Path(audit.__file__)),
        "control_sha256": audit.digest(control_path),
        "pilot_sha256": audit.digest(pilot_path),
        "sources": sources,
        "records_csv_sha256": audit.digest(csv_path),
        "sparse_record_count": len(frame),
        "geometry_status_counts": frame.geometry_status.value_counts().to_dict(),
        "groups": groups,
        "archive_control_count": int(frame.detection_id.notna().sum())
        if "detection_id" in frame
        else 0,
        "physical_accuracy_certified": False,
        "negative_label_permitted": False,
        "scope": (
            "All global sparse thermal pixels in explicitly listed local training swaths; "
            "not a representative pilot/year sample"
        ),
        "limitations": [
            "Center-cell edges are not calibrated sensor IFOV boundaries",
            "Only three archived scan/track control references; others are geometry diagnostics",
            "Terrain/asymmetry correlation does not prove a causal error model",
            "Outer scan rows/columns retained as unreconstructed",
            "No pixel area, size correction, label threshold or sampling policy selected",
        ],
    }
    stem.with_suffix(".json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Report: {stem.with_suffix('.json')}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair-keys", nargs="+", required=True)
    run(parser.parse_args().pair_keys)
