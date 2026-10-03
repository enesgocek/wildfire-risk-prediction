"""Compare audited training swaths by grid; no area or daily-negative inference."""

import argparse
import importlib.util
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/reports/observation_coverage"
SPEC = importlib.util.spec_from_file_location(
    "sample_audit", Path(__file__).with_name("inspect_l2_observation_sample.py")
)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def compare_frames(frames):
    audit.require(len(frames) >= 2, "At least two distinct swaths required")
    reference = set(next(iter(frames.values())).grid_id)
    result = pd.DataFrame(index=pd.Index(sorted(reference), name="grid_id"))
    for key, frame in frames.items():
        audit.require(
            frame.grid_id.is_unique and set(frame.grid_id) == reference,
            "Sample grid keys differ or repeat",
        )
        audit.require(
            frame.daily_observation_status.eq("unknown").all()
            and frame.negative_label_permitted.eq(False).all(),
            "Sample is not an unresolved diagnostic",
        )
        audit.require(
            (frame.land_nominal_input_no_residual >= 0).all()
            and (frame.land_nominal_input_no_residual <= frame.land).all(),
            "Invalid diagnostic land count",
        )
        indexed = frame.set_index("grid_id")
        result[f"{key}_has_nominal_land_center"] = indexed.land_nominal_input_no_residual.gt(0)
    flags = result.columns.tolist()
    result["any_sample_has_nominal_land_center"] = result[flags].any(axis=1)
    result["all_samples_have_nominal_land_center"] = result[flags].all(axis=1)
    result["daily_observation_status"] = "unknown"
    result["negative_label_permitted"] = False
    return result.reset_index()


def parse_sample_key(value):
    match = re.fullmatch(r"(?:(SNPP|N20):)?(\d{7}\.\d{4})", value)
    audit.require(match is not None, "Invalid sensor/sample key")
    return match[1] or "SNPP", match[2]


def compare(keys):
    parsed = [parse_sample_key(value) for value in keys]
    audit.require(len(set(parsed)) == len(parsed), "Repeated sample key")
    frames, sources, summaries, dates = {}, {}, [], set()
    sensors = [s for s in ("SNPP", "N20") if any(sensor == s for sensor, _ in parsed)]
    for sensor, key in parsed:
        stem = audit.sample_stem(sensor, key)
        sample_id = f"{sensor}:{key}"
        report_path = OUTPUT / f"{stem}_audit.json"
        csv_path = OUTPUT / f"{stem}_grid_centers.csv"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        fire_path = ROOT / report["sources"]["fire"]["path"]
        file_key, stamp = audit.training_key(fire_path.name)
        audit.require(file_key == key == report["pair_key"], "Sample identity mismatch")
        audit.require(
            report["sensor"] == sensor == audit.product_identity(fire_path.name)[0],
            "Sample sensor mismatch",
        )
        dates.add(stamp.date().isoformat())
        for source in report["sources"].values():
            audit.require(
                audit.digest(ROOT / source["path"]) == source["sha256"],
                "Sample source changed since audit",
            )
        for field, path in [
            ("aoi_sha256", ROOT / "data/aoi/aoi.geojson"),
            ("grid_sha256", ROOT / "data/aoi/grid_5km.geojson"),
            ("script_sha256", Path(audit.__file__)),
        ]:
            audit.require(audit.digest(path) == report[field], "Audit provenance changed")
        frame = pd.read_csv(csv_path)
        audit.require(len(frame) == report["pilot_grid_count"], "Grid row count mismatch")
        audit.require(
            frame.pixel_center_count.sum() == report["spatial_counts"]["pilot_centers"],
            "Pixel-center total mismatch",
        )
        for label, count in report["pilot_class_counts"].items():
            audit.require(frame[label].sum() == count, "Class count mismatch")
        audit.require(
            frame.land_nominal_input_no_residual.sum()
            == report["pilot_land_nominal_input_no_residual"],
            "Land count mismatch",
        )
        frames[sample_id] = frame
        sources[sample_id] = {
            "audit_sha256": audit.digest(report_path),
            "grid_counts_sha256": audit.digest(csv_path),
        }
        summaries.append(
            {
                "pair_key": key,
                "sensor": sensor,
                "sample_id": sample_id,
                "start_utc": report["start_utc"],
                "end_utc": report["end_utc"],
                "pilot_class_counts": report["pilot_class_counts"],
                "nominal_land_centers": report["pilot_land_nominal_input_no_residual"],
                "grids_with_nominal_land_center": int(
                    frame.land_nominal_input_no_residual.gt(0).sum()
                ),
            }
        )
    audit.require(len(dates) == 1, "Comparison must concern one training UTC date")
    result = compare_frames(frames)
    day = next(iter(dates))
    sensor_counts = {
        sensor: int(
            result[[f"{s}:{key}_has_nominal_land_center" for s, key in parsed if s == sensor]]
            .any(axis=1)
            .sum()
        )
        for sensor in sensors
    }
    sensor_label = "_".join(sensors)
    report = {
        "day_utc": day,
        "sensor": sensor_label,
        "sensors": sensors,
        "sample_count": len(keys),
        "sample_keys": [f"{s}:{key}" for s, key in parsed],
        "samples": summaries,
        "sources": sources,
        "script_sha256": audit.digest(Path(__file__)),
        "grid_count": len(result),
        "grids_with_nominal_land_center_by_sensor": sensor_counts,
        "grids_with_nominal_land_center_in_any_sample": int(
            result.any_sample_has_nominal_land_center.sum()
        ),
        "grids_with_nominal_land_center_in_all_samples": int(
            result.all_samples_have_nominal_land_center.sum()
        ),
        "grids_without_nominal_land_center_in_these_samples": int(
            (~result.any_sample_has_nominal_land_center).sum()
        ),
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "limitations": [
            "Only listed swaths, not all day/sensor observations",
            "Any center does not mean fully observed grid",
            "Counts do not measure area or establish daily negatives",
        ],
    }
    prefix = OUTPUT / f"l2_comparison_{day}_{sensor_label}_{len(keys)}samples"
    result.to_csv(prefix.with_suffix(".csv"), index=False)
    prefix.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {prefix.with_suffix('.json')}")
    print(report["grids_with_nominal_land_center_in_any_sample"], "grids with at least one center")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair-keys", nargs="+", default=["2019014.0042", "2019014.1024"])
    compare(parser.parse_args().pair_keys)
