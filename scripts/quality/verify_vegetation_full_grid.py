"""Offline independent integral readback and matched pilot comparison for a full snapshot."""

import argparse
import hashlib
import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
VALUES = {
    "ndvi_median_mean": "ndvi_m2",
    "ndmi_median_mean": "ndmi_m2",
    "valid_observation_count_mean": "observation_count_m2",
    "latest_pixel_age_mean_days": "latest_age_days_m2",
    "median_pixel_age_mean_days": "median_age_days_m2",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, name):
    if not condition:
        raise ValueError(name)


def verify(directory):
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    spec = manifest["contract"]
    parts = ROOT / "data/interim/grid_aoi_parts.geojson"
    require(sha(parts) == spec["parts_sha256"], "Grid hash")
    require(
        sha(ROOT / "src/wildfire_risk_prediction/vegetation.py") == spec["helper_sha256"]
        and sha(ROOT / "scripts/landcover/prepare_vegetation_full_grid.py")
        == spec["runner_sha256"],
        "Code hashes",
    )
    require(
        spec["source"] == "LANDSAT/LC08/C02/T1_L2"
        and spec["windows"] == [30, 60]
        and spec["scale_m"] == 30
        and spec["crs"] == "EPSG:6933"
        and spec["qa_excluded_bits"] == [0, 1, 2, 3, 4, 5, 7]
        and spec["qa_radsat_zero"]
        and spec["reflectance_scale"] == 0.0000275
        and spec["reflectance_offset"] == -0.2,
        "Scientific contract",
    )
    require(
        manifest["final_test_accessed"] is False
        and manifest["historical_availability_verified"] is False,
        "Scope flags",
    )
    target = pd.Timestamp(spec["target"], tz="UTC")
    require(2018 <= target.year <= 2023 and target.hour == 0, "Training-only cutoff")
    table_path = ROOT / manifest["table"]
    require(sha(table_path) == manifest["table_sha256"], "Table hash")
    table = pd.read_csv(table_path)
    require(len(table) == manifest["rows"] == 5798, "Rows")
    require(not table.duplicated(["grid_id", "window_days"]).any(), "Duplicate keys")
    require(table.available_at.isna().all(), "Release unknown")
    require(table.usage.eq("retrospective_candidate_only").all(), "Usage flags")
    require(table.processing_version.eq("landsat_seasonal_window_v1").all(), "Math version")
    areas = {
        f["properties"]["grid_id"]: f["properties"]["aoi_area_km2"] * 1e6
        for f in json.loads(parts.read_text())["features"]
    }
    require(len(areas) == 2899, "Unique full grid")
    for days, window in table.groupby("window_days"):
        require(days in (30, 60) and set(window.grid_id) == set(areas), "Grid/window completeness")
    lookup = table.set_index(["grid_id", "window_days"])
    seen = set()
    for name, digest in manifest["raw_sha256"].items():
        path = ROOT / name
        require(sha(path) == digest, "Raw hash")
        raw = json.loads(path.read_text())
        require(raw["contract"] == spec and raw["available_at"] is None, "Raw contract")
        days = raw["window_days"]
        require(days in (30, 60), "Window")
        start = target - timedelta(days=days)
        times = pd.to_datetime(raw["scene_acquisition_utc"], utc=True)
        require(
            len(times) == len(raw["scene_ids"]) == len(set(raw["scene_ids"]))
            and (times >= start).all()
            and (times < target).all(),
            "Acquisition window and identities",
        )
        require(
            len(raw["properties"]) == len(raw["grid_ids"])
            and len(set(raw["grid_ids"])) == len(raw["grid_ids"])
            and {r["grid_id"] for r in raw["properties"]} == set(raw["grid_ids"]),
            "Batch identities",
        )
        for r in raw["properties"]:
            key = (r["grid_id"], days)
            require(key not in seen, "Overlapping batches")
            seen.add(key)
            saved = lookup.loc[key]
            area = r.get("vegetation_support_m2") or 0.0
            require(np.isfinite(area) and area >= 0, "Support area")
            require(np.isclose(saved.valid_area_m2, area), "Support readback")
            require(np.isclose(saved.aoi_area_m2, areas[key[0]]), "AOI readback")
            require(np.isclose(saved.support_to_aoi_ratio, area / areas[key[0]]), "Support ratio")
            require(saved.snapshot_cutoff_utc == target.isoformat(), "Cutoff")
            require(saved.window_start_utc == start.isoformat(), "Start")
            require(saved.source_batch == path.name, "Batch provenance")
            require(
                pd.Timestamp(saved.source_acquisition_latest_utc) == times.max()
                if len(times)
                else pd.isna(saved.source_acquisition_latest_utc),
                "Latest acquisition",
            )
            for column, integral in VALUES.items():
                require(
                    np.isclose(saved[column], r[integral] / area, rtol=1e-9, atol=1e-8)
                    if area
                    else pd.isna(saved[column]) and r.get(integral) in (None, 0),
                    "Integral/missingness readback",
                )
            if area:
                require(
                    abs(saved.ndvi_median_mean) <= 1 + 1e-7
                    and abs(saved.ndmi_median_mean) <= 1 + 1e-7
                    and saved.valid_observation_count_mean >= 1 - 1e-7
                    and 0
                    <= saved.latest_pixel_age_mean_days
                    <= saved.median_pixel_age_mean_days
                    <= days + 1e-7,
                    "Index/age/count bounds",
                )
    require(len(seen) == len(table), "Raw completeness")
    comparison = None
    if spec["target"] == "2018-08-01":
        pilot_dir = ROOT / "data/interim/vegetation/seasonal_v1"
        old_manifest = json.loads((pilot_dir / "manifest_32cells.json").read_text())
        pilot_path = ROOT / old_manifest["table"]
        require(sha(pilot_path) == old_manifest["table_sha256"], "Accepted pilot hash")
        require(
            old_manifest["contract"]["helper_sha256"] == spec["helper_sha256"]
            and old_manifest["contract"]["parts_sha256"] == spec["parts_sha256"],
            "Matched pilot math/grid",
        )
        pilot = pd.read_csv(pilot_path)
        pilot = pilot[
            pilot.snapshot_cutoff_utc.eq(target.isoformat()) & pilot.window_days.isin((30, 60))
        ]
        joined = pilot.merge(table, on=["grid_id", "window_days"], validate="one_to_one")
        columns = ["valid_area_m2", "support_to_aoi_ratio", *VALUES]
        differences = {}
        for column in columns:
            left, right = joined[f"{column}_x"], joined[f"{column}_y"]
            require(np.allclose(left, right, equal_nan=True, rtol=1e-6, atol=1e-7), "Pilot match")
            differences[column] = float((left - right).abs().max())
        comparison = {"rows": len(joined), "maximum_absolute_differences": differences}
        require(len(joined) == 64, "Pilot coverage")
    return {
        "status": "full_grid_integral_readback_passed",
        "rows": len(table),
        "raw_files": len(manifest["raw_sha256"]),
        "manifest_sha256": sha(manifest_path),
        "matched_prior_pilot": comparison,
        "independent_source_or_field_validation": False,
        "final_test_accessed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2018-08-01")
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    name = f"{args.date}_b{args.batch_size}"
    report = verify(ROOT / "data/interim/vegetation/full_grid_v1" / name)
    path = ROOT / "outputs/reports/landscape/full_grid_v1" / name / "local_readback.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
