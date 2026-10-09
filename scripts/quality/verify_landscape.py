"""Offline hash and integral readback for the actual landscape tables."""

import hashlib
import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/interim/landscape/v1"
RAW = ROOT / "data/raw/terrain/srtm_v1"
REPORT = ROOT / "outputs/reports/landscape"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    manifest = json.loads((OUT / "manifest.json").read_text())
    for file, key in [
        (ROOT / "data/aoi/grid_5km.geojson", "grid_sha256"),
        (ROOT / "data/interim/grid_aoi_parts.geojson", "parts_sha256"),
        (ROOT / "data/raw/landcover/landcover_copernicus_2017.tif", "landcover_source_sha256"),
        (ROOT / "data/interim/grid_landcover_2017.csv", "landcover_table_sha256"),
    ]:
        require(sha(file) == manifest[key], f"Changed source: {key}")
    require(sha(ROOT / manifest["table"]) == manifest["table_sha256"], "Static table hash")
    frame = pd.read_csv(ROOT / manifest["table"]).set_index("grid_id")
    original = pd.read_csv(ROOT / "data/interim/grid_landcover_2017.csv").set_index("grid_id")
    require(len(frame) == 2899 and frame.index.is_unique, "Static keys")
    pd.testing.assert_frame_equal(
        original.sort_index(), frame[original.columns].sort_index(), check_dtype=False
    )
    require(frame.historical_available_at.isna().all(), "Historical availability invented")
    require(not frame.landcover_suitability_decided.any(), "Habitat decision invented")
    require(frame.usage.eq("retrospective_candidate_features_only").all(), "Static use")
    source = json.loads((RAW / "source.json").read_text())
    require(source == manifest["terrain_contract"], "Terrain source contract")
    raw_rows = {}
    for name, digest in manifest["terrain_batch_sha256"].items():
        path = RAW / name
        require(sha(path) == digest, "Terrain batch changed")
        batch = json.loads(path.read_text())
        require(batch["contract"] == source, "Terrain batch provenance")
        for row in batch["properties"]:
            if row["grid_id"] in raw_rows:
                require(row == raw_rows[row["grid_id"]], "Terrain duplicates conflict")
            raw_rows[row["grid_id"]] = row
    require(set(raw_rows) == set(frame.index), "Raw terrain coverage")
    for key, row in raw_rows.items():
        saved = frame.loc[key]
        area = row.get("support_m2") or 0
        require(np.isclose(saved.terrain_valid_area_m2, area), "Terrain support readback")
        if not area:
            require(pd.isna(saved.elevation_mean_m), "Unsupported elevation filled")
            continue
        mu = row["elevation_m_m2"] / area
        variance = max(0, row["elevation2_m2_m2"] / area - mu**2)
        for name, value in [
            ("elevation_mean_m", mu),
            ("elevation_std_m", np.sqrt(variance)),
            ("slope_mean_deg", row["slope_deg_m2"] / area),
        ]:
            require(np.isclose(saved[name], value, rtol=1e-9, atol=1e-8), "Terrain mean readback")
        oriented = row.get("aspect_support_m2") or 0
        for name, integral in [
            ("northness_mean", "northness_m2"),
            ("eastness_mean", "eastness_m2"),
        ]:
            if oriented:
                require(
                    np.isclose(saved[name], row[integral] / oriented, atol=1e-9),
                    "Circular aspect readback",
                )
            else:
                require(pd.isna(saved[name]), "Flat aspect filled")
    vegetation = []
    for report_path in REPORT.glob("vegetation_pilot_*.json"):
        report = json.loads(report_path.read_text())
        stem = report_path.stem.removeprefix("vegetation_pilot_")
        raw_path = ROOT / f"data/raw/vegetation/landsat_pilot_v1/{stem}.json"
        csv_path = ROOT / f"data/interim/vegetation/pilot_v1/{stem}.csv"
        require(sha(raw_path) == report["raw_sha256"], "Vegetation source hash")
        require(sha(csv_path) == report["table_sha256"], "Vegetation table hash")
        raw = json.loads(raw_path.read_text())
        require(raw["parts_sha256"] == manifest["parts_sha256"], "Vegetation geometry")
        require(raw["source"] == "LANDSAT/LC08/C02/T1_L2", "Vegetation source")
        require(
            raw["reflectance_scale"] == 0.0000275 and raw["reflectance_offset"] == -0.2,
            "Reflectance scaling",
        )
        require(
            raw["qa_excluded_bits"] == [0, 1, 2, 3, 4, 5, 7] and raw["qa_radsat"] == "must be zero",
            "Vegetation QA",
        )
        target = pd.Timestamp(raw["prediction_timestamp_utc"])
        require(target.year <= 2023, "Vegetation pilot outside training")
        times = pd.to_datetime(raw["scene_acquisition_utc"], utc=True)
        table = pd.read_csv(csv_path).set_index("grid_id")
        start = target.to_pydatetime() - timedelta(days=60)
        require((times < target).all() and (times >= start).all(), "Vegetation temporal leakage")
        require(
            table.source_window_start_utc.eq(start.isoformat()).all(), "Vegetation window start"
        )
        require(
            table.source_window_end_exclusive_utc.eq(target.isoformat()).all(),
            "Vegetation window end",
        )
        require(
            table.index.is_unique and set(table.index) == set(raw["grid_ids"]), "Vegetation keys"
        )
        require(table.available_at.isna().all(), "Vegetation availability invented")
        for row in raw["properties"]:
            area = row.get("vegetation_support_m2") or 0
            for name, integral in [
                ("ndvi_past60_median_mean", "ndvi_m2"),
                ("ndmi_past60_median_mean", "ndmi_m2"),
                ("valid_observation_count_mean", "observation_count_m2"),
            ]:
                if area:
                    require(
                        np.isclose(table.loc[row["grid_id"], name], row[integral] / area),
                        "Vegetation integral readback",
                    )
                else:
                    require(pd.isna(table.loc[row["grid_id"], name]), "Missing vegetation filled")
        vegetation.append({"cells": len(table), "target": target.isoformat()})
    report = {
        "status": "passed_local_integral_readback",
        "static_cells": len(frame),
        "terrain_batches": len(manifest["terrain_batch_sha256"]),
        "vegetation_pilots": vegetation,
        "source_and_output_hashes_verified": True,
        "original_landcover_columns_preserved": True,
        "final_test_accessed": False,
        "limits": "Recomputes summaries from EE raw integrals; not an independent DEM or QA truth",
    }
    (REPORT / "local_readback.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
