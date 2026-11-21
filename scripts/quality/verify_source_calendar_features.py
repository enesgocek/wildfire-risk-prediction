"""Separate calendar X/QA readback and temporal support counts; no labels or model fitting."""

import argparse
import csv
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import landscape, weather_policy
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PROPOSAL = BASE / "source_calendar_control_proposal_v1/20261121T160611Z_9e76a4ab"
PROPOSAL_SHA = "ee08ef36aefab7ae66b2c2c7ff87f0cc5d10d8d077e1cafad61c5d202ca9a6e5"
PREVIOUS = BASE / "satellite_PU_feature_review_v1/20261120T010533Z_6d61c80e"
PREVIOUS_SHA = "64262888976fe43530897f9c069eb73866dea42003ffc4fd31fcfa17ddd74138"


def keys(frame):
    return set(frame[join.KEYS].itertuples(index=False, name=None))


def check_metadata(metadata):
    join.require(
        metadata.target.isna().all() and metadata.accepted_L_membership.isna().all(),
        "No true labels or accepted L",
    )
    join.require(
        metadata.daily_observation_status.eq("unknown").all()
        and metadata.role_is_model_training_permission.eq(False).all(),
        "Feature roles cannot authorize training",
    )


def temporal_support(features, metadata):
    check_metadata(metadata)
    frame = features.merge(
        metadata[join.KEYS + ["known_proposal_key_in_union", "review_temporal_role"]],
        on=join.KEYS,
        validate="one_to_one",
    )
    join.require(
        len(frame) == len(features) == len(metadata), "All feature rows have review metadata"
    )
    frame["year_month"] = frame.prediction_timestamp_utc.str[:7]
    static = landscape.COVER_FEATURES + landscape.TERRAIN_FEATURES
    groups = []
    for (grid, month), block in frame.groupby(["grid_id", "year_month"], sort=True):
        join.require(
            block[static].nunique(dropna=False).eq(1).all(),
            "Static fields constant within a grid-month",
        )
        weather_complete = block[weather_policy.MODEL_FEATURES].notna().all(axis=1)
        anchors = block.known_proposal_key_in_union
        n, count, complete_days = len(block), int(anchors.sum()), int(weather_complete.sum())
        groups.append(
            {
                "grid_id": grid,
                "year_month": month,
                "review_temporal_role": block.review_temporal_role.iloc[0],
                "calendar_days": n,
                "known_proposal_context_days": count,
                "complete_weather_days": complete_days,
                "complete_27_feature_days": int(
                    block[join.feature_names()].notna().all(axis=1).sum()
                ),
                "distinct_weather_vectors_including_missing": len(
                    block[weather_policy.MODEL_FEATURES].drop_duplicates()
                ),
                "anchor_other_date_context_pairs": count * (n - 1),
                "weather_complete_anchor_other_date_context_pairs": int(
                    (anchors & weather_complete).sum()
                )
                * max(complete_days - 1, 0),
                "pairs_are_verified_opposite_fire_labels": False,
            }
        )
    return pd.DataFrame(groups)


def main(report_path, expected_sha):
    report_path = report_path.resolve()
    join.require(
        report_path.is_relative_to((BASE / "source_calendar_feature_review_v1").resolve())
        and digest(report_path) == expected_sha,
        "Pinned completed calendar review",
    )
    report = json.loads(report_path.read_bytes())
    join.require(
        report["unique_feature_keys"] == 44082
        and report["new_S_Y_or_accepted_L_assignments"] == 0
        and report["model_fitted"] is False,
        "X preparation scope only",
    )
    folder = report_path.parent
    consumed = {
        report_path: expected_sha,
        PROPOSAL / "readback.json": PROPOSAL_SHA,
        PREVIOUS / "readback.json": PREVIOUS_SHA,
    }
    for name, sha in report["artifact_sha256"].items():
        p = folder / name
        join.require(
            p.resolve().is_relative_to(folder) and digest(p) == sha, "Current snapshot artifact"
        )
        consumed[p] = sha
    snapshot = folder / report["snapshot_directory"]
    features, qa, metadata = [
        parse_csv((snapshot / n).read_bytes())
        for n in ("features.csv", "provenance.csv", "review_roles.csv")
    ]
    parent = json.loads((PROPOSAL / "readback.json").read_bytes())
    calendar_file = PROPOSAL / "proposed_calendar_keys.csv"
    consumed[calendar_file] = parent["artifact_sha256"][calendar_file.name]
    planned = parse_csv(calendar_file.read_bytes())
    expected_keys = keys(planned)
    join.require(
        features.columns.tolist() == join.KEYS + join.feature_names(), "Whitelisted X schema"
    )
    for frame in (features, qa, metadata):
        join.require(
            len(frame) == 44082
            and not frame.duplicated(join.KEYS).any()
            and keys(frame) == expected_keys,
            "Exact full calendar key conservation",
        )
    check_metadata(metadata)
    expected_metadata = (
        planned.rename(columns={"proposed_temporal_role": "review_temporal_role"})
        .sort_values(join.KEYS)
        .reset_index(drop=True)
    )
    expected_metadata["role_is_model_training_permission"] = False
    pd.testing.assert_frame_equal(metadata, expected_metadata, check_exact=True)
    # Independently parse variable-precision ISO timestamps with the standard library.
    with (snapshot / "provenance.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            t = datetime.fromisoformat(row["prediction_timestamp_utc"])
            end = datetime(2022 if t.year <= 2021 else 2023, 1, 1, tzinfo=UTC)
            join.require(
                2018 <= t.year <= 2022 and t + timedelta(days=1) < end,
                "No sealed-year or target role-boundary rows",
            )
            for field in ("weather_source_last_timestamp_utc", "weather_rain_interval_end_utc"):
                join.require(
                    datetime.fromisoformat(row[field]) == t - timedelta(hours=1),
                    "Weather acquisition strictly past",
                )
            for w in (30, 60):
                prefix = f"vegetation_{w}d_"
                if row[prefix + "vegetation_present"] == "True":
                    acquired = datetime.fromisoformat(row[prefix + "source_acquisition_latest_utc"])
                    cutoff = datetime.fromisoformat(row[prefix + "snapshot_cutoff_utc"])
                    lower = datetime.fromisoformat(row[prefix + "window_start_utc"])
                    join.require(
                        lower <= acquired < cutoff <= t and cutoff - lower == timedelta(days=w),
                        "Past vegetation acquisition and full window",
                    )
                join.require(
                    row[prefix + "available_at"] == "", "Publication availability stays unknown"
                )
            join.require(
                row["static_reference_year"] == "2017"
                and row["operational_eligible"] == "False"
                and row["weather_available_at"] == "",
                "Historical context is not operational admission",
            )
    previous = json.loads((PREVIOUS / "readback.json").read_bytes())
    for name, fresh in (("features.csv", features), ("provenance.csv", qa)):
        p = PREVIOUS / name
        consumed[p] = previous["artifact_sha256"][name]
        old = parse_csv(p.read_bytes()).set_index(join.KEYS)
        common = expected_keys & set(old.index)
        join.require(len(common) == 1689, "Exact unchanged previous overlap")
        pd.testing.assert_frame_equal(
            fresh.set_index(join.KEYS).loc[sorted(common)],
            old.loc[sorted(common)],
            check_exact=True,
        )
    monthly = []
    for month, item in sorted(report["month_receipts"].items()):
        p = folder / item["path"]
        join.require(digest(p) == item["sha256"], "Sealed month receipt")
        body = json.loads(p.read_bytes())
        join.require(body["month"] == month, "Receipt belongs to its recorded calendar month")
        for name, sha in body["artifact_sha256"].items():
            join.require(digest(p.parent / name) == sha, "Sealed month X artifact")
        monthly.append(body)
    join.require(
        len(monthly) == 60
        and sum(r["rows"] for r in monthly) == 44082
        and sum(r["days"] for r in monthly) == 1824,
        "Month/day/row conservation",
    )
    coverage = temporal_support(features, metadata)
    join.require(
        len(coverage) == 1443 and coverage.known_proposal_context_days.sum() == 1670,
        "Full source-conditioned calendar strata",
    )
    summaries = {}
    for role, group in metadata.groupby("review_temporal_role", sort=True):
        selected = features.set_index(join.KEYS).loc[list(keys(group))]
        by_stratum = coverage.loc[coverage.review_temporal_role.eq(role)]
        summaries[role] = {
            "rows": len(group),
            "calendar_strata": len(by_stratum),
            "complete_27_features": int(selected[join.feature_names()].notna().all(axis=1).sum()),
            "complete_weather": int(
                selected[weather_policy.MODEL_FEATURES].notna().all(axis=1).sum()
            ),
            "anchor_other_date_context_pairs": int(
                by_stratum.anchor_other_date_context_pairs.sum()
            ),
            "weather_complete_anchor_other_date_context_pairs": int(
                by_stratum.weather_complete_anchor_other_date_context_pairs.sum()
            ),
        }
    out = (
        BASE
        / "source_calendar_feature_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    p = out / "calendar_stratum_feature_support.csv"
    coverage.to_csv(p, index=False)
    pd.testing.assert_frame_equal(coverage, parse_csv(p.read_bytes()), check_exact=True)
    result = {
        "status": "separate_calendar_feature_readback_passed_not_fire_or_training_acceptance",
        "parent_readback_sha256": expected_sha,
        "unique_keys": 44082,
        "prior_overlap_X_and_QA_exact": 1689,
        "calendar_strata": len(coverage),
        "role_summaries": summaries,
        "strata_with_changing_weather_vectors": int(
            coverage.distinct_weather_vectors_including_missing.gt(1).sum()
        ),
        "original_U_or_weights_changed": False,
        "new_S_Y_or_accepted_L_created": 0,
        "model_fitted": False,
        "final_merge_performed": False,
        "context_pairs_may_include_other_candidate_days": True,
        "context_pairs_are_verified_case_control_pairs": False,
        "raw_daily_contents_rehashed_in_this_separate_audit": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in consumed.items()},
        "artifact_sha256": {p.name: digest(p)},
        "producer_sha256": digest(Path(__file__)),
    }
    join.require(
        all(digest(p) == h for p, h in consumed.items()), "Snapshots unchanged at separate close"
    )
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print(json.dumps(summaries), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    arguments = parser.parse_args()
    main(arguments.report, arguments.sha256)
