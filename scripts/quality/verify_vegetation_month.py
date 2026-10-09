"""Independent daily as-of readback from weekly full-grid sources, without labels."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
VALUES = ["ndvi_median_mean", "ndmi_median_mean"]
AGES = ["latest_pixel_age_mean_days", "median_pixel_age_mean_days"]
PROVENANCE = [
    "window_start_utc",
    "processing_version",
    "source_acquisition_latest_utc",
    "source_batch",
    "snapshot_manifest_sha256",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, name):
    if not condition:
        raise ValueError(name)


def verify(month):
    directory = ROOT / "data/interim/vegetation/month_v1" / month
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    first = pd.Timestamp(month + "-01", tz="UTC")
    require(2018 <= first.year <= 2023, "Training-only month")
    dates = pd.date_range(first, periods=first.days_in_month, freq="D")
    cutoffs = dates[::7]
    require(
        manifest["month"] == month
        and manifest["version"] == "vegetation_training_month_v1"
        and manifest["days"] == len(dates)
        and manifest["grid_count"] == 2899
        and manifest["cutoffs"] == [t.isoformat() for t in cutoffs]
        and manifest["windows"] == [30, 60]
        and manifest["cadence_days"] == 7
        and manifest["max_snapshot_age_days"] == 8,
        "Calendar/policy contract",
    )
    require(
        all(
            manifest[name] is False
            for name in (
                "historical_availability_verified",
                "final_test_accessed",
                "fire_labels_created",
            )
        ),
        "Scope flags",
    )
    require(
        sha(ROOT / "src/wildfire_risk_prediction/vegetation_series.py")
        == manifest["series_helper_sha256"]
        and sha(ROOT / "scripts/landcover/prepare_vegetation_month.py")
        == manifest["builder_sha256"],
        "Code hashes",
    )
    table_path = directory / "daily_candidates.csv"
    require(manifest["table"] == table_path.relative_to(ROOT).as_posix(), "Table path")
    require(sha(table_path) == manifest["table_sha256"], "Daily hash")
    frame = pd.read_csv(table_path)
    require(len(frame) == manifest["rows"] == 2899 * len(dates) * 2, "Daily rows")
    require(
        not frame.duplicated(["grid_id", "prediction_timestamp_utc", "window_days"]).any(),
        "Duplicate keys",
    )
    require(
        frame.available_at.isna().all() and frame.usage.eq("retrospective_candidate_only").all(),
        "Availability/usage",
    )
    require(
        frame.selection_mode.eq("retrospective").all()
        and frame.series_version.eq(manifest["version"]).all(),
        "Version/mode",
    )
    parts = json.loads((ROOT / "data/interim/grid_aoi_parts.geojson").read_text())["features"]
    ids = sorted(f["properties"]["grid_id"] for f in parts)
    require(len(ids) == len(set(ids)) == 2899, "Unique grid")
    source_names = {
        f"data/interim/vegetation/full_grid_v1/{t.date().isoformat()}_b64/manifest.json"
        for t in cutoffs
    }
    require(set(manifest["snapshot_manifests"]) == source_names, "Source manifest scope")
    spec = importlib.util.spec_from_file_location(
        "full_readback", ROOT / "scripts/quality/verify_vegetation_full_grid.py"
    )
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    snapshots = []
    for name, digest in sorted(manifest["snapshot_manifests"].items()):
        path = ROOT / name
        require(sha(path) == digest, "Snapshot manifest hash")
        checker.verify(path.parent)
        source = json.loads(path.read_text())
        snapshot = pd.read_csv(ROOT / source["table"])
        snapshot["snapshot_manifest_sha256"] = digest
        snapshots.append(snapshot)
    source = pd.concat(snapshots, ignore_index=True)
    source["cutoff"] = pd.to_datetime(source.snapshot_cutoff_utc, utc=True)
    verified = 0
    for window in (30, 60):
        for date in dates:
            saved = frame[
                frame.window_days.eq(window) & frame.prediction_timestamp_utc.eq(date.isoformat())
            ].set_index("grid_id")
            require(
                len(saved) == 2899 and set(saved.index) == set(ids), "Date/window grid coverage"
            )
            saved = saved.loc[ids]
            eligible = source[
                source.window_days.eq(window)
                & source.valid_area_m2.gt(0)
                & source.cutoff.le(date)
                & source.cutoff.ge(date - pd.Timedelta(days=8))
            ]
            chosen = (
                eligible.sort_values("cutoff")
                .drop_duplicates("grid_id", keep="last")
                .set_index("grid_id")
                .reindex(ids)
            )
            present = chosen.cutoff.notna()
            require(
                saved.vegetation_present.equals(present.rename("vegetation_present")),
                "Daily support choice",
            )
            require(
                saved.loc[
                    ~present,
                    [
                        "snapshot_cutoff_utc",
                        "snapshot_age_days",
                        "support_to_aoi_ratio",
                        *VALUES,
                        *AGES,
                        *PROVENANCE,
                    ],
                ]
                .isna()
                .all()
                .all(),
                "Missing remains missing",
            )
            require(
                (
                    saved.loc[present, "snapshot_cutoff_utc"]
                    == chosen.loc[present, "snapshot_cutoff_utc"]
                ).all(),
                "Most recent past snapshot",
            )
            delta = (date - chosen.loc[present, "cutoff"]).dt.total_seconds() / 86400
            require(
                np.allclose(saved.loc[present, "snapshot_age_days"], delta, rtol=1e-9, atol=1e-9),
                "Snapshot age",
            )
            for column in ["support_to_aoi_ratio", *VALUES]:
                require(
                    np.allclose(
                        saved.loc[present, column],
                        chosen.loc[present, column],
                        rtol=1e-9,
                        atol=1e-9,
                    ),
                    "Carried value",
                )
            for column in AGES:
                require(
                    np.allclose(
                        saved.loc[present, column],
                        chosen.loc[present, column] + delta,
                        rtol=1e-9,
                        atol=1e-9,
                    ),
                    "Advanced pixel age",
                )
            for column in PROVENANCE:
                require(
                    (saved.loc[present, column] == chosen.loc[present, column]).all(),
                    "Daily provenance",
                )
            verified += len(saved)
    require(verified == len(frame), "Complete daily readback")
    return {
        "status": "monthly_daily_readback_passed",
        "month": month,
        "verified_daily_rows": verified,
        "snapshot_cutoffs": len(cutoffs),
        "verified_snapshot_rows": len(source),
        "manifest_sha256": sha(manifest_path),
        "final_test_accessed": False,
        "historical_availability_verified": False,
        "independent_source_or_field_validation": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", default="2018-08")
    args = parser.parse_args()
    report = verify(args.month)
    path = ROOT / "outputs/reports/landscape/month_v1" / args.month / "local_readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
