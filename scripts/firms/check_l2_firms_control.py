"""Check an audited training swath against archived pilot detections; never label fires."""

import argparse
import importlib.util
import json
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Geod, Transformer
from rasterio.windows import Window

SPEC = importlib.util.spec_from_file_location(
    "sample_audit", Path(__file__).with_name("inspect_l2_observation_sample.py")
)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)
ROOT, OUTPUT = audit.ROOT, audit.OUTPUT
CONFIDENCE = {"l": 7, "n": 8, "h": 9}
# Each FIRMS coordinate is rounded to five decimal places. No nearest-pixel fallback.
ROUNDING_HALF_WIDTH = 0.000005000001


def coordinate_match(latitude, longitude, sparse):
    lat = np.asarray(sparse["FP_latitude"], dtype="float64")
    lon = np.asarray(sparse["FP_longitude"], dtype="float64")
    audit.require(
        np.isfinite(latitude)
        and np.isfinite(longitude)
        and abs(latitude) <= 90
        and abs(longitude) <= 180,
        "Invalid archived coordinate",
    )
    matches = np.flatnonzero(
        (np.abs(lat - latitude) <= ROUNDING_HALF_WIDTH)
        & (np.abs(lon - longitude) <= ROUNDING_HALF_WIDTH)
    )
    audit.require(len(matches) == 1, "Missing or ambiguous rounded-coordinate match")
    return int(matches[0])


def check(selection_path):
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    anchor = selection["anchor"]
    stamp = pd.Timestamp(anchor["detection_timestamp_utc"])
    audit.require(2018 <= stamp.year <= 2023, "Only training controls allowed")
    sensor = anchor["source_sensor"]
    audit.require(sensor in {"SNPP", "N20"}, "Unsupported control sensor")
    candidates_path = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
    audit.require(
        audit.digest(candidates_path) == selection["candidate_source_sha256"],
        "Control candidate source changed",
    )
    candidates = pd.read_csv(candidates_path, dtype=str, keep_default_na=False)
    selected = candidates.loc[candidates.detection_id.eq(anchor["detection_id"])]
    audit.require(len(selected) == 1, "Missing or duplicate control candidate")
    audit.require(
        all(selected.iloc[0][field] == value for field, value in anchor.items()),
        "Control anchor fields changed",
    )
    metadata = {}
    for concept, record in selection["records"].items():
        path = OUTPUT / f"{concept}_metadata.json"
        audit.require(audit.digest(path) == record["metadata_sha256"], "Metadata changed")
        entry = json.loads(path.read_text(encoding="utf-8"))
        product = entry["CollectionReference"]["ShortName"]
        role = audit.PRODUCTS[product][1]
        audit.require(role not in metadata, "Repeated metadata role")
        metadata[role] = path
    fire_meta = json.loads(metadata["fire"].read_text(encoding="utf-8"))
    # Use the actual CMR data URL basename, not an assumed GranuleUR suffix.
    filenames = {
        u["URL"].rsplit("/", 1)[-1] for u in fire_meta["RelatedUrls"] if u["URL"].endswith(".nc")
    }
    audit.require(len(filenames) == 1, "Ambiguous fire filename in metadata")
    filename = filenames.pop()
    file_sensor, _, key, _ = audit.product_identity(filename)
    audit.require(sensor == file_sensor, "Anchor/swath sensor mismatch")
    stem = audit.sample_stem(sensor, key)
    report_path = OUTPUT / f"{stem}_audit.json"
    counts_path = OUTPUT / f"{stem}_grid_centers.csv"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    audit.require(report["script_sha256"] == audit.digest(Path(audit.__file__)), "Audit changed")
    start, end = pd.Timestamp(report["start_utc"]), pd.Timestamp(report["end_utc"])
    audit.require(start <= stamp < end, "Anchor outside swath interval")
    audit.require(report["sensor"] == sensor and report["pair_key"] == key, "Wrong audit")
    audit.require(not report["negative_label_permitted"], "Unexpected label permission")
    for role, source in report["sources"].items():
        path = ROOT / source["path"]
        audit.require(audit.digest(path) == source["sha256"], "Audited source changed")
        audit.require(
            audit.digest(metadata[role]) == source["cmr_metadata_sha256"], "Wrong audit metadata"
        )
    aoi_path, grid_path = ROOT / "data/aoi/aoi.geojson", ROOT / "data/aoi/grid_5km.geojson"
    audit.require(audit.digest(aoi_path) == report["aoi_sha256"], "AOI changed")
    audit.require(audit.digest(grid_path) == report["grid_sha256"], "Grid changed")
    counts = pd.read_csv(counts_path)
    audit.require(
        len(counts) == report["pilot_grid_count"]
        and counts.grid_id.is_unique
        and counts.daily_observation_status.eq("unknown").all()
        and counts.negative_label_permitted.eq(False).all(),
        "Invalid audited grid table",
    )
    for label, total in report["pilot_class_counts"].items():
        audit.require(int(counts[label].sum()) == total, "Grid/audit class mismatch")
    pilot_path = ROOT / (
        "data/interim/firms_pilot_2018_2024.csv"
        if sensor == "SNPP"
        else "data/interim/firms_noaa20_pilot_2018_2024.csv"
    )
    pilot_hash = audit.digest(pilot_path)
    pilot = pd.read_csv(pilot_path, dtype=str, keep_default_na=False)
    times = pd.to_datetime(pilot.detection_timestamp_utc, utc=True)
    records = pilot.loc[(times >= start) & (times < end)].copy()
    audit.require(len(records) > 0 and records.source_record_number.is_unique, "Invalid records")
    aoi = gpd.read_file(aoi_path).to_crs(4326).geometry.union_all()
    shapely.prepare(aoi)
    transformer = Transformer.from_crs(4326, 6933, always_xy=True)
    geod = Geod(ellps="WGS84")
    fire = ROOT / report["sources"]["fire"]["path"]
    geo = ROOT / report["sources"]["geolocation"]["path"]
    matches, used = [], set()
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask, qa = (audit.layer(stack, fire, name) for name in ("fire_mask", "algorithm_QA"))
        latds, londs = (
            audit.layer(stack, geo, f"geolocation_data/{name}")
            for name in ("latitude", "longitude")
        )
        audit.validate_pair(fire, geo, mask.tags(), latds.tags())
        sparse = audit.read_sparse(stack, fire, report["sparse_fire_count"])
        _, _, inside = audit.pilot_selection(sparse["FP_longitude"], sparse["FP_latitude"], aoi)
        pilot_indices = set(np.flatnonzero(inside).tolist())
        audit.require(
            len(pilot_indices) == sum(report["pilot_class_counts"][c] for c in audit.CLASSES[7:]),
            "Pilot sparse/mask count mismatch",
        )
        for record in records.to_dict(orient="records"):
            lat, lon = float(record["latitude"]), float(record["longitude"])
            i = coordinate_match(lat, lon, sparse)
            audit.require(i in pilot_indices and i not in used, "Outside pilot or repeated match")
            used.add(i)
            row, col = int(sparse["FP_line"][i]), int(sparse["FP_sample"][i])
            window = Window(col, row, 1, 1)
            actual_class = int(mask.read(1, window=window).item())
            quality = int(qa.read(1, window=window).item())
            native_lat, native_lon = (
                float(ds.read(1, window=window).item()) for ds in (latds, londs)
            )
            audit.require(
                actual_class == int(sparse["FP_confidence"][i]) == CONFIDENCE[record["confidence"]],
                "Archive/native confidence mismatch",
            )
            audit.require(
                abs(native_lat - float(sparse["FP_latitude"][i])) <= 1e-5
                and abs(native_lon - float(sparse["FP_longitude"][i])) <= 1e-5,
                "Sparse/native coordinate mismatch",
            )
            x, y = transformer.transform(native_lon, native_lat)
            grid_id = f"E6933_5K_V1_C{int(np.floor(x / 5000))}_R{int(np.floor(y / 5000))}"
            audit.require(grid_id == record["grid_id"], "Archive/native grid mismatch")
            matches.append(
                {
                    "detection_id": (
                        f"{sensor}_{anchor['source_request_id']}_{record['source_record_number']}"
                    ),
                    "archive_type_unverified": record["type"],
                    "archive_timestamp_utc": record["detection_timestamp_utc"],
                    "archive_latitude": lat,
                    "archive_longitude": lon,
                    "native_latitude": native_lat,
                    "native_longitude": native_lon,
                    "coordinate_difference_m": float(geod.inv(lon, lat, native_lon, native_lat)[2]),
                    "sparse_index": i,
                    "native_row": row,
                    "native_column": col,
                    "grid_id": grid_id,
                    "fire_mask_class": actual_class,
                    "algorithm_qa": quality,
                    "input_non_nominal": bool(quality & 127),
                    "geo_non_nominal": bool(quality & (1 << 5)),
                    "residual_bowtie": bool(quality & (1 << 22)),
                    "confirmed_wildfire": False,
                    "final_label_assigned": False,
                }
            )
        audit.require(used == pilot_indices, "Unmatched pilot sparse fires in control")
    audit.require(
        any(m["detection_id"] == anchor["detection_id"] for m in matches), "Anchor absent"
    )
    audit.require(audit.digest(pilot_path) == pilot_hash, "Pilot source changed during check")
    for source in report["sources"].values():
        audit.require(audit.digest(ROOT / source["path"]) == source["sha256"], "Source changed")
    destination = OUTPUT / f"{stem}_firms_control.json"
    result = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "thermal_control_matched",
        "sensor": sensor,
        "pair_key": key,
        "anchor_detection_id": anchor["detection_id"],
        "source_hashes": {
            "selection": audit.digest(selection_path),
            "audit": audit.digest(report_path),
            "grid_counts": audit.digest(counts_path),
            "pilot_csv": pilot_hash,
            "candidate_csv": selection["candidate_source_sha256"],
            "script": audit.digest(Path(__file__)),
        },
        "archive_pilot_records_in_swath": len(records),
        "matched_records": matches,
        "unmatched_pilot_sparse_fires": len(pilot_indices - used),
        "negative_label_permitted": False,
        "final_labels_assigned": False,
        "limitations": [
            "Coordinate/confidence match does not validate fire Type or vegetation wildfire",
            "Archive minute lies in granule interval; exact pixel acquisition second not checked",
            "QA flags reported without selecting a new exclusion rule",
            "Single training control; not full-day coverage or validation-period assessment",
        ],
    }
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {destination}")
    print(f"Matched {len(matches)} pilot records; no final labels assigned")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--selection", type=Path, default=OUTPUT / "control_l2_sample_selection.json"
    )
    check(parser.parse_args().selection)
