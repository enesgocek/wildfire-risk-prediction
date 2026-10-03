"""Review training weather policy, then explicitly prepare derived daily tables."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import prepare_era5_land as met

from wildfire_risk_prediction import weather_policy as policy

ROOT = met.ROOT
OUTPUT = met.INTERIM / "model_v1"
MANIFEST = OUTPUT / "policy_manifest.json"
REVIEW = ROOT / "outputs/reports/meteorology/weather_policy_training_review.json"
PROFILES = [
    "weather_primary_eligible",
    "weather_sensitivity90_eligible",
    "weather_observed_eligible",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_audit(year):
    path = ROOT / f"outputs/reports/quality/project_audit_{year}-01-01_{year + 1}-01-01.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    require(
        report["status"] == "passed_with_open_gates" and not report["errors"], "Source audit failed"
    )
    hashes = {k.replace("\\", "/"): v for k, v in report["code_sha256"].items()}
    require(
        hashes["scripts/meteorology/prepare_era5_land.py"] == met.sha(Path(met.__file__)),
        "Source method changed",
    )
    weather = report["checks"]["meteorology"]
    expected = [str(d) for d in met.days(f"{year}-01-01", f"{year + 1}-01-01")]
    require([d["date"] for d in weather["days"]] == expected, "Source audit date gaps")
    return {d["date"]: d for d in weather["days"]}, {
        "path": str(path.relative_to(ROOT)),
        "sha256": met.sha(path),
    }


def read_day(day, audit, grid_ids):
    path = met.INTERIM / "daily" / f"{day}.csv"
    require(met.sha(path) == audit["csv_sha256"], f"Source changed since audit: {day}")
    frame = pd.read_csv(path)
    require(
        frame.grid_id.tolist() == grid_ids and len(frame) == audit["rows"], "Grid order/count drift"
    )
    times = pd.to_datetime(frame.prediction_timestamp_utc, utc=True)
    require(times.eq(pd.Timestamp(str(day), tz="UTC")).all(), "Source date mismatch")
    return frame


def review():
    """Inspect only 2018-2023; candidate retention is diagnostic, not an event label."""
    met.read_weights()
    require(policy.RAW_FEATURES == met.FEATURES, "Feature schema mismatch")
    grid_ids = pd.read_csv(met.INTERIM / "era5_land_grid_areas.csv").grid_id.tolist()
    candidate_path = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
    candidates = pd.read_csv(
        candidate_path, usecols=["detection_id", "grid_id", "detection_timestamp_utc"]
    )
    require(candidates.detection_id.is_unique, "Duplicate candidate ID")
    times = pd.to_datetime(candidates.detection_timestamp_utc, utc=True)
    candidates = candidates.loc[times.ge("2018-01-01") & times.lt("2024-01-01")].copy()
    # Diagnostic match to right-closed prediction window; midnight belongs to preceding T.
    candidate_ns = (
        pd.to_datetime(candidates.detection_timestamp_utc, utc=True)
        .dt.as_unit("ns")
        .astype("int64")
    )
    candidates["weather_day"] = pd.to_datetime(candidate_ns - 1, utc=True).dt.strftime("%Y-%m-%d")
    outside = int(candidates.weather_day.lt("2018-01-01").sum())
    groups = {k: v for k, v in candidates.groupby("weather_day") if k >= "2018-01-01"}
    yearly, audit_sources = [], []
    low = np.full(len(grid_ids), np.inf)
    high = np.zeros(len(grid_ids))
    total_candidates = 0
    rain_minima = {f"rain_{h}h_raw_mm": None for h in policy.RAIN_HOURS}
    for year in range(2018, 2024):
        audits, source = load_audit(year)
        audit_sources.append(source)
        totals, retained = {}, dict.fromkeys(PROFILES, 0)
        n = 0
        for day, audit in audits.items():
            frame = read_day(day, audit, grid_ids)
            transformed = policy.transform(frame)
            for key, value in policy.counts(transformed).items():
                totals[key] = totals.get(key, 0) + value
            coverage = transformed.weather_min_valid_area_fraction.to_numpy()
            low, high = np.minimum(low, coverage), np.maximum(high, coverage)
            for feature in rain_minima:
                value = float(frame[feature].min())
                rain_minima[feature] = (
                    value if rain_minima[feature] is None else min(rain_minima[feature], value)
                )
            group = groups.get(day)
            if group is not None:
                require(group.grid_id.isin(grid_ids).all(), "Unknown candidate grid")
                matched = transformed.set_index("grid_id").loc[group.grid_id, PROFILES]
                n += len(group)
                for profile in PROFILES:
                    retained[profile] += int(matched[profile].sum())
        total_candidates += n
        yearly.append(
            {
                "year": year,
                "counts": totals,
                "candidate_detections": n,
                "candidate_weather_retention": retained,
            }
        )
        print(f"Training policy reviewed: {year}", flush=True)
    require(total_candidates + outside == len(candidates), "Unmatched training candidates")
    grid_report = pd.DataFrame(
        {"grid_id": grid_ids, "training_min_coverage": low, "training_max_coverage": high}
    )
    grid_path = OUTPUT / "training_grid_coverage.csv"
    grid_path.parent.mkdir(parents=True, exist_ok=True)
    grid_report.to_csv(grid_path, index=False)
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "policy": policy.specification(),
        "selection_period": [2018, 2023],
        "validation_used_for_rule_selection": False,
        "rule_kind": (
            "Prespecified conservative baseline and sensitivity; no fitted threshold "
            "or fire-performance optimization."
        ),
        "yearly": yearly,
        "training_raw_rain_minima_mm": rain_minima,
        "training_candidates": len(candidates),
        "candidates_outside_weather_window": outside,
        "candidate_limit": (
            "Provisional detections, not independent fires; source Type/event rules remain open."
        ),
        "source_audits": audit_sources,
        "candidate_source_sha256": met.sha(candidate_path),
        "grid_coverage_sha256": met.sha(grid_path),
        "constant_coverage_all_training_days": bool(
            np.isclose(low, high, rtol=0, atol=1e-12).all()
        ),
        "counts": {key: sum(y["counts"][key] for y in yearly) for key in yearly[0]["counts"]},
        "candidate_weather_retention": {
            p: sum(y["candidate_weather_retention"][p] for y in yearly) for p in PROFILES
        },
        "model_ready": False,
        "final_test_accessed": False,
    }
    met.write_json(REVIEW, report)
    met.write_json(
        MANIFEST,
        {
            "policy": policy.specification(),
            "policy_code_sha256": met.sha(Path(policy.__file__)),
            "source_processing_code_sha256": met.sha(Path(met.__file__)),
            "review": str(REVIEW.relative_to(ROOT)),
            "review_sha256": met.sha(REVIEW),
            "selection_period": [2018, 2023],
            "source_audits": audit_sources,
        },
    )
    print(
        json.dumps(
            {
                "counts": report["counts"],
                "candidate_weather_retention": report["candidate_weather_retention"],
            },
            indent=2,
        )
    )
    print(f"Report: {REVIEW}")


def prepare(start, end):
    requested = list(met.days(start, end))  # Final-test guard before file reads.
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(manifest["policy"] == policy.specification(), "Policy changed; review required")
    require(manifest["policy_code_sha256"] == met.sha(Path(policy.__file__)), "Policy code changed")
    require(
        manifest["source_processing_code_sha256"] == met.sha(Path(met.__file__)),
        "Source method changed",
    )
    require(manifest["review_sha256"] == met.sha(REVIEW), "Training review changed")
    require(manifest["selection_period"] == [2018, 2023], "Invalid policy selection period")
    for source in manifest["source_audits"]:
        require(met.sha(ROOT / source["path"]) == source["sha256"], "Training audit changed")
    met.read_weights()
    grid_ids = pd.read_csv(met.INTERIM / "era5_land_grid_areas.csv").grid_id.tolist()
    audits = {y: load_audit(y)[0] for y in sorted({d.year for d in requested})}
    summaries = []
    for day in requested:
        audit = audits[day.year][str(day)]
        frame = read_day(day, audit, grid_ids)
        result = policy.transform(frame)
        output = OUTPUT / "daily" / f"{day}.csv"
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(".csv.part")
        result.to_csv(temporary, index=False)
        reread = pd.read_csv(temporary)
        pd.testing.assert_frame_equal(
            reread[frame.columns],
            frame,
            check_dtype=False,
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )
        for profile in PROFILES:
            require(
                reread.loc[reread[profile], policy.MODEL_FEATURES].notna().all().all(),
                "Eligible row has missing model feature",
            )
        for h in policy.RAIN_HOURS:
            require(
                reread[f"rain_{h}h_nonnegative_mm"].dropna().ge(0).all(), "Negative model rainfall"
            )
        temporary.replace(output)
        require(
            met.sha(met.INTERIM / "daily" / f"{day}.csv") == audit["csv_sha256"], "Source modified"
        )
        summaries.append(
            {
                "date": str(day),
                "split": "train" if day.year <= 2023 else "validation",
                "source_sha256": audit["csv_sha256"],
                "output_sha256": met.sha(output),
                **policy.counts(result),
            }
        )
        print(f"Model weather prepared and verified: {day} rows: {len(result)}", flush=True)
    report_path = ROOT / f"outputs/reports/meteorology/model_weather_{start}_{end}.json"
    met.write_json(
        report_path,
        {
            "prepared_at_utc": datetime.now(UTC).isoformat(),
            "preparation_code_sha256": met.sha(Path(__file__)),
            "start": start,
            "end_exclusive": end,
            "total_rows": sum(d["rows"] for d in summaries),
            "policy_manifest_sha256": met.sha(MANIFEST),
            "days": summaries,
            "all_rows_retained": True,
            "model_ready": False,
            "labels_created": False,
            "final_test_accessed": False,
        },
    )
    print(f"Report: {report_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["review", "prepare"])
    parser.add_argument("--start")
    parser.add_argument("--end", help="Exclusive; at most 2025-01-01")
    args = parser.parse_args()
    if args.command == "review":
        if args.start or args.end:
            parser.error("review always uses only the fixed 2018-2023 training period")
        review()
    else:
        if not args.start or not args.end:
            parser.error("prepare requires explicit --start and --end")
        prepare(args.start, args.end)


if __name__ == "__main__":
    main()
