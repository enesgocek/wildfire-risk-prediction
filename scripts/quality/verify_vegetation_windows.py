"""Independent offline hash/integral/temporal readback of seasonal and as-of tables."""

import hashlib
import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/interim/vegetation/seasonal_v1"
RAW = ROOT / "data/raw/vegetation/seasonal_v1"
REPORT = ROOT / "outputs/reports/landscape/seasonal_v1"
VALUES = {
    "ndvi_median_mean": "ndvi_m2",
    "ndmi_median_mean": "ndmi_m2",
    "valid_observation_count_mean": "observation_count_m2",
    "latest_pixel_age_mean_days": "latest_age_days_m2",
    "median_pixel_age_mean_days": "median_age_days_m2",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    manifest_path = OUT / "manifest_32cells.json"
    manifest = json.loads(manifest_path.read_text())
    spec = manifest["contract"]
    require(
        sha(ROOT / "data/interim/grid_aoi_parts.geojson") == spec["parts_sha256"], "Geometry hash"
    )
    require(
        sha(ROOT / "src/wildfire_risk_prediction/vegetation.py") == spec["helper_sha256"],
        "Code hash",
    )
    require(spec["source"] == "LANDSAT/LC08/C02/T1_L2", "Source collection")
    require(
        spec["qa_excluded_bits"] == [0, 1, 2, 3, 4, 5, 7] and spec["qa_radsat_zero"], "QA policy"
    )
    require(
        spec["reflectance_scale"] == 0.0000275 and spec["reflectance_offset"] == -0.2, "Scaling"
    )
    table = pd.read_csv(ROOT / manifest["table"])
    require(sha(ROOT / manifest["table"]) == manifest["table_sha256"], "Snapshot hash")
    require(
        len(table) == 384
        and not table.duplicated(["grid_id", "snapshot_cutoff_utc", "window_days"]).any(),
        "Snapshot keys",
    )
    require(table.available_at.isna().all(), "Release invented")
    areas = {
        f["properties"]["grid_id"]: f["properties"]["aoi_area_km2"] * 1e6
        for f in json.loads((ROOT / "data/interim/grid_aoi_parts.geojson").read_text())["features"]
    }
    seen = set()
    for name, digest in manifest["raw_sha256"].items():
        path = RAW / name
        require(sha(path) == digest, "Raw file hash")
        raw = json.loads(path.read_text())
        require(raw["contract"] == spec and raw["available_at"] is None, "Raw contract")
        end = pd.Timestamp(raw["date"], tz="UTC").to_pydatetime()
        require(2018 <= end.year <= 2023, "Training-only source")
        start = end - timedelta(days=raw["window_days"])
        times = pd.to_datetime(raw["scene_acquisition_utc"], utc=True)
        require(
            len(times) == len(raw["scene_ids"]) and len(set(raw["scene_ids"])) == len(times),
            "Source catalog keys",
        )
        require((times >= start).all() and (times < end).all(), "Future/old source")
        rows = table[
            table.snapshot_cutoff_utc.eq(end.isoformat()) & table.window_days.eq(raw["window_days"])
        ].set_index("grid_id")
        require(set(rows.index) == set(spec["grid_ids"]) and len(rows) == 32, "Spatial coverage")
        for r in raw["properties"]:
            key = (r["grid_id"], end.isoformat(), raw["window_days"])
            require(key not in seen, "Duplicate raw summary")
            seen.add(key)
            saved = rows.loc[r["grid_id"]]
            area = r.get("vegetation_support_m2") or 0
            require(np.isclose(saved.valid_area_m2, area), "Support integral readback")
            require(np.isclose(saved.aoi_area_m2, areas[r["grid_id"]]), "AOI area readback")
            require(
                np.isclose(saved.support_to_aoi_ratio, area / areas[r["grid_id"]]), "Area ratio"
            )
            require(saved.window_start_utc == start.isoformat(), "Window start")
            if len(times):
                require(
                    pd.Timestamp(saved.source_acquisition_latest_utc) == times.max(), "Source age"
                )
            for column, integral in VALUES.items():
                require(
                    np.isclose(saved[column], r[integral] / area, rtol=1e-9, atol=1e-8)
                    if area
                    else pd.isna(saved[column]),
                    "Integral/missing value readback",
                )
    require(len(seen) == len(table), "Raw keys incomplete")
    asof = json.loads((REPORT / "daily_asof_pilot.json").read_text())
    require(asof["snapshot_manifest_sha256"] == sha(manifest_path), "As-of input changed")
    snapshots = table.set_index(["grid_id", "snapshot_cutoff_utc", "window_days"])
    eligible_sources = {}
    for r in table.itertuples():
        if r.valid_area_m2 > 0:
            eligible_sources.setdefault((r.grid_id, r.window_days), []).append(
                pd.Timestamp(r.snapshot_cutoff_utc).to_pydatetime()
            )
    checked = 0
    for name, digest in asof["table_sha256"].items():
        path = ROOT / name
        require(sha(path) == digest, "As-of table hash")
        frame = pd.read_csv(path)
        require(
            len(frame) == 4224
            and not frame.duplicated(["grid_id", "prediction_timestamp_utc", "window_days"]).any(),
            "As-of keys",
        )
        require(set(frame.grid_id) == set(spec["grid_ids"]), "As-of grids")
        require(frame.available_at.isna().all(), "As-of release invented")
        if frame.selection_mode.eq("operational").all():
            require(not frame.vegetation_present.any(), "Unknown release passed operational gate")
        for r in frame.itertuples():
            t = pd.Timestamp(r.prediction_timestamp_utc).to_pydatetime()
            require(t.year <= 2023, "As-of training scope")
            eligible = [
                cutoff
                for cutoff in eligible_sources.get((r.grid_id, r.window_days), [])
                if t - timedelta(days=8) <= cutoff <= t
            ]
            if r.selection_mode == "operational":
                eligible = []  # Every recorded historical release is unknown.
            require(bool(eligible) == r.vegetation_present, "As-of completeness")
            if not r.vegetation_present:
                require(
                    all(
                        pd.isna(getattr(r, c))
                        for c in VALUES
                        if c != "valid_observation_count_mean"
                    ),
                    "Missing as-of filled",
                )
                continue
            cutoff = pd.Timestamp(r.snapshot_cutoff_utc).to_pydatetime()
            require(cutoff == max(eligible), "As-of did not choose latest eligible snapshot")
            lag = (t - cutoff).total_seconds() / 86400
            require(0 <= lag <= 8 and np.isclose(lag, r.snapshot_age_days), "As-of future/expiry")
            saved = snapshots.loc[(r.grid_id, r.snapshot_cutoff_utc, r.window_days)]
            require(saved.valid_area_m2 > 0, "Unsupported as-of selection")
            for column in ["ndvi_median_mean", "ndmi_median_mean"]:
                require(np.isclose(getattr(r, column), saved[column]), "As-of value changed")
            for column in ["latest_pixel_age_mean_days", "median_pixel_age_mean_days"]:
                require(
                    np.isclose(getattr(r, column), saved[column] + lag), "Pixel age not advanced"
                )
            checked += 1
    report = {
        "status": "passed_seasonal_and_asof_readback",
        "raw_files": len(manifest["raw_sha256"]),
        "snapshot_rows": len(table),
        "asof_rows": 8448,
        "asof_supported_rows_checked": checked,
        "final_test_accessed": False,
        "historical_availability_verified": False,
        "limits": "Independent formulas from same EE integrals; no separate QA/field truth",
    }
    (REPORT / "local_readback.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
