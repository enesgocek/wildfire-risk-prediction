"""Training-only daily support/age comparison after independent full month readback."""

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.vegetation_series import month_schedule

ROOT = Path(__file__).resolve().parents[2]
COLUMNS = [
    "grid_id",
    "window_days",
    "vegetation_present",
    "support_to_aoi_ratio",
    "snapshot_age_days",
    "latest_pixel_age_mean_days",
    "median_pixel_age_mean_days",
    "ndvi_median_mean",
    "ndmi_median_mean",
]


def quantile(supported, column, fraction):
    return float(supported[column].quantile(fraction)) if len(supported) else None


def summarize(frame):
    if frame.vegetation_present.dtype != bool or set(frame.window_days) != {30, 60}:
        raise ValueError("Expected separate windows and explicit support flags")
    summaries = []
    for window, group in frame.groupby("window_days", sort=True):
        supported = group[group.vegetation_present]
        missing = group[~group.vegetation_present]
        if missing[COLUMNS[3:]].notna().any().any():
            raise ValueError("Missing vegetation must remain missing")
        if supported[COLUMNS[3:]].isna().any().any():
            raise ValueError("Incomplete supported summary")

        summaries.append(
            {
                "window_days": int(window),
                "rows": len(group),
                "supported_rows": len(supported),
                "missing_rows": len(missing),
                "missing_fraction": len(missing) / len(group),
                "cells_with_any_missing_day": int(missing.grid_id.nunique()),
                "rows_support_at_least_90pct": int(supported.support_to_aoi_ratio.ge(0.9).sum()),
                "support_ratio_p50_supported": quantile(supported, "support_to_aoi_ratio", 0.5),
                "snapshot_age_p95_days_supported": quantile(supported, "snapshot_age_days", 0.95),
                "latest_pixel_age_p50_days_supported": quantile(
                    supported, "latest_pixel_age_mean_days", 0.5
                ),
                "median_pixel_age_p50_days_supported": quantile(
                    supported, "median_pixel_age_mean_days", 0.5
                ),
            }
        )
    return summaries


def review(months):
    if not months or len(months) != len(set(months)):
        raise ValueError("Unique training months required")
    # Validate all requested scopes before importing a checker or accessing any source file.
    for month in months:
        month_schedule(month)
    spec = importlib.util.spec_from_file_location(
        "month_review_checker", ROOT / "scripts/quality/verify_vegetation_month.py"
    )
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    results = []
    for month in sorted(months):
        evidence = checker.verify(month)
        directory = ROOT / "data/interim/vegetation/month_v1" / month
        frame = pd.read_csv(directory / "daily_candidates.csv", usecols=COLUMNS)
        results.append(
            {
                "month": month,
                "manifest_sha256": evidence["manifest_sha256"],
                "verified_rows": evidence["verified_daily_rows"],
                "summaries": summarize(frame),
            }
        )
        print(f"MONTH SUPPORT REVIEWED {month}: {len(frame)} rows", flush=True)
    return {
        "status": "training_month_support_review_passed",
        "version": "vegetation_month_support_review_v1",
        "reviewer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "months": results,
        "historical_availability_verified": False,
        "fire_labels_created": False,
        "final_test_accessed": False,
        "limits": [
            "Daily carried values; age percentiles describe cell-days, not unique scenes",
            "90pct support is diagnostic, not model acceptance or habitat eligibility",
            "Selected training months; not a representative whole-period missingness estimate",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", nargs="+", required=True)
    parser.add_argument("--report-name", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9_]+\.json", args.report_name):
        raise ValueError("Report filename")
    report = review(args.months)
    path = ROOT / "outputs/reports/landscape/month_comparison_v1" / args.report_name
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != encoded:
            raise ValueError("Accepted review retained; use a new report name")
    else:
        temp = path.with_suffix(".tmp")
        temp.write_text(encoded, encoding="utf-8")
        temp.replace(path)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            f"MONTH REVIEW STOPPED: {type(error).__name__}; accepted records retained", flush=True
        )
        raise SystemExit(1) from None
