"""Prepare a frozen 25-point request frame; do not acquire or accept land-cover data."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
BASE = "outputs/reports/dataset/"
SOURCES = {
    "product": (
        BASE + "corine_source_discovery_v1/20261027T191433Z_140ee9d2/product.bin",
        "927ee9f99a45e922694ee89dc0243239800bf7a6907301364e5f526b0e2aef2a",
    ),
    "catalog": (
        BASE + "corine_source_discovery_v1/20261027T191433Z_140ee9d2/catalog.bin",
        "417673dc464e2f5c02b0e108577a32779d18f6c8e513d6f4d61e1ca9148be595",
    ),
    "geometry": (
        BASE + "native_candidate_cover_v1/20261023T143656Z_90c1c93b/"
        "approximate_support_geometry.json",
        "67a39a83836bbc93bb62bed74ad01af67ce55abd10435789167af21fac813e16",
    ),
    "queue": (
        BASE + "habitat_decision_queue_v1/20261027T183748Z_e1e64136/readback.json",
        "6cd6b2bbe0dc9ac026219541283af5f339557d2a3e7063fedffa5734337fd236",
    ),
    "time": (
        BASE + "habitat_temporal_evidence_audit_v1/20261027T190350Z_207a4734/readback.json",
        "38e03a124e6c5da221ae545941997cb6f34cfd0ff3700bb412b25effc458dda9",
    ),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    pins, source = {}, {}
    for key, (relative, expected) in SOURCES.items():
        path = ROOT / relative
        require(sha(path) == expected, "Changed source: " + key)
        pins[relative] = expected
        if key != "catalog":
            source[key] = json.loads(path.read_text(encoding="utf-8"))
    config_path = ROOT / "configs/corine_2018_review_intake_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    pins[config_path.relative_to(ROOT).as_posix()] = sha(config_path)
    pins[Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__))
    require(source["product"]["UID"] == config["dataset_uid"], "Wrong dataset")
    matches = [
        r
        for r in source["product"]["downloadable_files"]["items"]
        if r["@id"] == config["downloadable_file_id"]
    ]
    require(len(matches) == 1, "Ambiguous catalog file")
    for key, configured in (("file", "file_stem"), ("version", "version"), ("format", "format")):
        require(matches[0][key] == config[configured], "Catalog mismatch: " + key)
    require(source["geometry"]["crs"] == "EPSG:6933", "Unexpected native CRS")
    geometry = {r["detection_id"]: r for r in source["geometry"]["points"]}
    queue = {r["detection_id"]: r for r in source["queue"]["records"]}
    require(len(geometry) == len(source["geometry"]["points"]) == 25, "Duplicate geometry")
    require(len(queue) == len(source["queue"]["records"]) == 25, "Duplicate queue")
    require(set(geometry) == set(queue), "Point membership changed")
    times = {}
    for row in source["time"]["image_evidence"]:
        times.setdefault(row["detection_id"], set()).add(row["prediction_utc"])
    require(set(times) == set(queue), "Time membership changed")
    forward = Transformer.from_crs(6933, 4326, always_xy=True)
    backward = Transformer.from_crs(4326, 6933, always_xy=True)
    features, residuals = [], []
    for identity, point in sorted(geometry.items()):
        require(len(times[identity]) == 1, "Ambiguous prediction time")
        prediction = next(iter(times[identity]))
        require(2018 <= datetime.fromisoformat(prediction).year <= 2023, "Closed split")
        record = queue[identity]
        require(record["target"] is None, "Unexpected target")
        require(record["habitat_admission"] == "undecided", "Unexpected acceptance")
        x, y = point["native_center_6933"]
        lon, lat = forward.transform(x, y)
        require(25 < lon < 37 and 35 < lat < 40, "Outside study-region envelope")
        rx, ry = backward.transform(lon, lat)
        residuals.append(max(abs(x - rx), abs(y - ry)))
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "detection_id": identity,
                    "code": record["code"],
                    "prediction_utc": prediction,
                    "linked_review_units": record["linked_review_units"],
                    "cover_reference_2017": record["reference_cover_2017"],
                    "corine_class": None,
                    "habitat_admission": "undecided",
                    "target": None,
                },
            }
        )
    require(max(residuals) < 0.01, "Coordinate roundtrip failed")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    output = ROOT / BASE / "corine_review_intake_v1" / stamp
    output.mkdir(parents=True, exist_ok=False)
    frame = {"type": "FeatureCollection", "features": features}
    frame_path = output / "review_points.geojson"
    frame_path.write_text(json.dumps(frame, indent=2), encoding="utf-8")
    for relative, expected in pins.items():
        require(sha(ROOT / relative) == expected, "Source changed during run")
    result = {
        "purpose": config["purpose"],
        "source_sha256": pins,
        "artifact_sha256": {frame_path.name: sha(frame_path)},
        "point_count": len(features),
        "review_unit_count": len({c for r in queue.values() for c in r["linked_review_units"]}),
        "max_coordinate_roundtrip_error_m": max(residuals),
        "corine_class_count": 0,
        "raster_received": False,
        "human_notes_reinterpreted": False,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    report = output / "readback.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(json.loads(frame_path.read_text()) == frame, "Frame readback failed")
    require(json.loads(report.read_text()) == result, "Report readback failed")
    (ROOT / config["incoming_directory"]).mkdir(parents=True, exist_ok=True)
    print(output.relative_to(ROOT))
    print("points", len(features), "classes", 0, "report_sha256", sha(report))


if __name__ == "__main__":
    main()
