"""Separate X, source-role, UTC-window and observed graph readback for the Mersin calendar."""

import argparse
import csv
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PROPOSAL = BASE / "cross_source_calendar_support_v1/20261121T175954Z_4ad955e7"
OLD = BASE / "source_pu_feature_review_v1/20261119T210151Z_3e99d4a1"
CALENDAR = BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896"
PARTITION = BASE / "conditional_rank_partition_v1/20261119T210609Z_511e5d9f"
LINEAGE = BASE / "satellite_PU_lineage_v1/20261120T003414Z_a21f7422"


def check_past(row):
    t = datetime.fromisoformat(row["prediction_timestamp_utc"])
    join.require(
        t.year == 2022
        and t.utcoffset() == timedelta(0)
        and t.hour == t.minute == t.second == 0
        and t + timedelta(days=1) < datetime(2023, 1, 1, tzinfo=UTC),
        "Strict 2022 midnight target",
    )
    for name in ("weather_source_last_timestamp_utc", "weather_rain_interval_end_utc"):
        join.require(
            datetime.fromisoformat(row[name]) == t - timedelta(hours=1), "Past weather acquisition"
        )
    for w in (30, 60):
        prefix = f"vegetation_{w}d_"
        if row[prefix + "vegetation_present"] == "True":
            acquired = datetime.fromisoformat(row[prefix + "source_acquisition_latest_utc"])
            lower = datetime.fromisoformat(row[prefix + "window_start_utc"])
            cutoff = datetime.fromisoformat(row[prefix + "snapshot_cutoff_utc"])
            join.require(
                lower <= acquired < cutoff <= t and cutoff - lower == timedelta(days=w),
                "Past vegetation and complete window",
            )
        join.require(row[prefix + "available_at"] == "", "Unknown vegetation publication time")
    join.require(
        row["weather_available_at"] == ""
        and row["static_reference_year"] == "2017"
        and row["operational_eligible"] == "False",
        "Retrospective context only",
    )


def main(folder, expected_sha):
    folder = folder.resolve()
    join.require(
        folder.parent == (BASE / "cross_source_calendar_feature_review_v1").resolve(),
        "Local review folder",
    )
    p = folder / "readback.json"
    join.require(digest(p) == expected_sha, "Pinned complete separate-source X receipt")
    report = json.loads(p.read_bytes())
    join.require(
        report["keys"] == 2383
        and report["model_fitted"] is False
        and report["new_Y_or_accepted_L_created"] == 0,
        "X preparation only",
    )
    pins = {p: expected_sha}
    # Daily raw files were freshly hashed by preparation; this separate readback checks snapshots.
    for name, h in report["artifact_sha256"].items():
        pins[folder / name] = h
    for parent in (PROPOSAL, OLD, CALENDAR, PARTITION):
        path = parent / "readback.json"
        pins[path] = report["input_sha256"][path.relative_to(ROOT).as_posix()]
    lineage = json.loads((LINEAGE / "readback.json").read_bytes())
    pins[LINEAGE / "readback.json"] = (
        "b13d15d640f51662bd75fc65a25769ca02ceb69c80836c4fe2b99e788ae2e530"
    )
    pins[LINEAGE / "d2000m_t72h/detections.csv"] = lineage["artifact_sha256"][
        "d2000m_t72h/detections.csv"
    ]
    snapshot = folder / report["snapshot_directory"]
    x, q, metadata = [
        parse_csv((snapshot / name).read_bytes())
        for name in ("features.csv", "provenance.csv", "review_roles.csv")
    ]
    proposal = json.loads((PROPOSAL / "readback.json").read_bytes())
    path = PROPOSAL / "proposed_2022_source_calendar_keys.csv"
    pins[path] = proposal["artifact_sha256"][path.name]
    expected = parse_csv(path.read_bytes())

    def keyset(frame):
        return set(frame[join.KEYS].itertuples(index=False, name=None))

    keys = keyset(expected)
    for frame in (x, q, metadata):
        join.require(
            len(frame) == 2383 and not frame.duplicated(join.KEYS).any() and keyset(frame) == keys,
            "Exact requested key universe",
        )
    pd.testing.assert_frame_equal(x[join.KEYS], metadata[join.KEYS], check_exact=True)
    join.require(
        x.columns.tolist() == join.KEYS + join.feature_names()
        and metadata.target.isna().all()
        and metadata.accepted_L_membership.isna().all()
        and metadata.daily_observation_status.eq("unknown").all(),
        "Whitelisted X and unknown targets",
    )
    original_roles = pd.DataFrame(
        json.loads((PARTITION / "readback.json").read_bytes())["proposed_key_partitions"]
    )
    original_roles = original_roles.loc[
        original_roles.proposed_partition.eq("proposed_assessment_2022")
    ]
    original_source = keyset(
        original_roles.loc[original_roles.review_population.eq("source_center_hypothesis")]
    )
    original_U = keyset(
        original_roles.loc[original_roles.review_population.eq("U_geographic_slice")]
    )
    join.require(
        keyset(metadata.loc[metadata.original_source_record_key_present]) == original_source
        and keyset(metadata.loc[metadata.original_U_key_present]) == keys & original_U,
        "Exact original membership provenance; no new source selection",
    )
    with (snapshot / "provenance.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            check_past(row)
    calendar_report = json.loads((CALENDAR / "readback.json").read_bytes())
    common_union = set()
    for parent, parent_snapshot in (
        (OLD, OLD),
        (CALENDAR, CALENDAR / calendar_report["snapshot_directory"]),
    ):
        parent_report = json.loads((parent / "readback.json").read_bytes())
        for name, fresh in (("features.csv", x), ("provenance.csv", q)):
            path = parent_snapshot / name
            pins[path] = parent_report["artifact_sha256"][path.relative_to(parent).as_posix()]
            old = parse_csv(path.read_bytes())
            common = keys & keyset(old)
            pd.testing.assert_frame_equal(
                fresh.set_index(join.KEYS).loc[sorted(common)],
                old.set_index(join.KEYS).loc[sorted(common)],
                check_exact=True,
            )
            common_union.update(common)
    join.require(len(common_union) == 318, "All overlapping prior X and QA equal")
    monthly_rows, monthly_days = 0, 0
    for month, item in report["month_receipts"].items():
        path = folder / item["path"]
        pins[path] = item["sha256"]
        receipt = json.loads(path.read_bytes())
        join.require(receipt["month"] == month, "Correct monthly receipt identity")
        monthly_rows += receipt["rows"]
        monthly_days += receipt["days"]
        for name, h in receipt["artifact_sha256"].items():
            pins[path.parent / name] = h
    join.require(
        monthly_rows == 2383 and monthly_days == report["days"], "Month row/day conservation"
    )
    cal_roles = parse_csv(
        (CALENDAR / calendar_report["snapshot_directory"] / "review_roles.csv").read_bytes()
    )
    fit_keys = keyset(cal_roles.loc[cal_roles.review_temporal_role.eq("proposed_fit_2018_2021")])
    graph_roles = defaultdict(set)
    detected = parse_csv((LINEAGE / "d2000m_t72h/detections.csv").read_bytes())
    for row in detected.itertuples():
        t = datetime.fromisoformat(row.timestamp_utc) - timedelta(microseconds=1)
        key = (row.grid_id, t.replace(hour=0, minute=0, second=0, microsecond=0).isoformat())
        if key in keys:
            graph_roles[row.final_graph_membership_sha256].add("held")
        if key in fit_keys:
            graph_roles[row.final_graph_membership_sha256].add("fit")
    shared = sum(len(v) > 1 for v in graph_roles.values())
    dynamic = [
        f
        for f in join.feature_names()
        if f.startswith(("temperature_", "dewpoint_", "wind_", "soil_", "rain_", "vegetation_"))
    ]
    valid = x[dynamic].notna().all(axis=1)
    support = metadata[join.KEYS + ["original_source_record_key_present"]].copy()
    support["dynamic_complete"] = valid
    support["month"] = support.prediction_timestamp_utc.str[:7]
    strata = []
    for (grid, month), frame in support.groupby(["grid_id", "month"], sort=True):
        n = int(frame.dynamic_complete.sum())
        s = int((frame.dynamic_complete & frame.original_source_record_key_present).sum())
        strata.append(
            {
                "grid_id": grid,
                "month": month,
                "calendar_rows": len(frame),
                "complete_dynamic_rows": n,
                "complete_source_rows": s,
                "complete_same_grid_month_pairs": s * (n - s),
            }
        )
    require = join.require
    require(
        all(digest(p) == h for p, h in pins.items()),
        "Current separate snapshot, prior and monthly artifacts",
    )
    out = (
        BASE
        / "cross_source_calendar_feature_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    pd.DataFrame(strata).to_csv(out / "source_calendar_support.csv", index=False)
    result = {
        "status": "separate_source_X_metadata_time_overlap_and_observed_graph_readback_complete",
        "parent_readback_sha256": expected_sha,
        "keys": 2383,
        "source_keys": 81,
        "prior_X_QA_exact_union": len(common_union),
        "complete_dynamic_rows": int(valid.sum()),
        "complete_source_rows": int((valid & metadata.original_source_record_key_present).sum()),
        "calendar_strata": len(strata),
        "complete_same_grid_month_pairs": sum(r["complete_same_grid_month_pairs"] for r in strata),
        "shared_observed_graph_blocks_with_old_fit": shared,
        "graph_is_physical_event_identity": False,
        "raw_daily_files_rehashed_by_this_second_reader": False,
        "new_models_or_true_Y_or_accepted_L_created": 0,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {
            "source_calendar_support.csv": digest(out / "source_calendar_support.csv")
        },
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print(
        "source complete",
        result["complete_source_rows"],
        "pairs",
        result["complete_same_grid_month_pairs"],
        "shared graphs",
        shared,
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()
    main(args.review, args.expected_sha256)
