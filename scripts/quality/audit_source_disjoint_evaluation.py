"""Independent direct enumeration from original score and overlap CSV exports."""

import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCE = BASE / "source_disjoint_frozen_assessment_v1/20261124T031245Z_91cd329d"
REVIEW = BASE / "evaluation_review_package_v1/20261123T141815Z_be04a5fe"
RUN = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"
GROUPS = [
    "original_source_calendar",
    "exclude_any_same_key_satellite_proposal",
    "absent_from_four_province_calendar",
]
SCORE_COLUMNS = [
    "new_primary_weather_source_score_not_probability",
    "previous_broad_xgboost_source_score_not_probability",
    "previous_broad_frozen_linear_source_score_not_probability",
]
VARIANTS = ["primary_weather_XGBoost", "broad_weather_XGBoost", "frozen_linear"]
KEYS = ["grid_id", "prediction_timestamp_utc"]


def main():
    receipt = json.loads((SOURCE / "readback.json").read_bytes())
    pins = {ROOT / name: sha for name, sha in receipt["input_sha256"].items()}
    pins.update({SOURCE / name: sha for name, sha in receipt["artifact_sha256"].items()})
    old_receipt = json.loads((REVIEW / "readback.json").read_bytes())
    if (
        digest(REVIEW / "readback.json")
        != "4c1ddd5be410efd3d7dfe1f44324db4046f2dfb2fc4058b718519d654473e05e"
    ):
        raise ValueError("Original overlap export receipt")
    overlap_path = REVIEW / "Mersin_source_anchor_overlap.csv"
    pins[overlap_path] = old_receipt["artifact_sha256"][overlap_path.name]
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("All assessment and original input bytes")
    source_days = pd.read_csv(overlap_path)
    flag_cols = [c for c in source_days if c.startswith("S_candidate_context_")]
    member_sets = {}
    for row in source_days.to_dict("records"):
        groups = [GROUPS[0]]
        if not any(row[c] is True for c in flag_cols):
            groups.append(GROUPS[1])
        if not row["also_in_four_province_calendar"]:
            groups.append(GROUPS[2])
        member_sets[(row["grid_id"], row["prediction_timestamp_utc"])] = groups
    actual = pd.read_csv(SOURCE / "metrics.csv", float_precision="round_trip")
    registry = pd.read_csv(SOURCE / "paired_day_registry.csv")
    expected_pairs = set()
    accumulators = defaultdict(lambda: [0, 0, 0])
    for scenario in sorted(actual.scenario.unique()):
        scores = pd.read_csv(
            RUN / scenario / "separate_Mersin_scores.csv", float_precision="round_trip"
        )
        dates = pd.to_datetime(scores.prediction_timestamp_utc, utc=True)
        if (
            not dates.dt.year.eq(2022).all()
            or not scores.target.isna().all()
            or not scores.accepted_L_membership.isna().all()
            or not scores.daily_observation_status.eq("unknown").all()
        ):
            raise ValueError("Only existing 2022 unknown-target scores")
        rows = scores.to_dict("records")
        controls = [
            (i, r)
            for i, r in enumerate(rows)
            if r["primary_weather_and_dynamic_15_eligible"]
            and (r["grid_id"], r["prediction_timestamp_utc"]) not in member_sets
        ]
        for i, source in enumerate(rows):
            key = (source["grid_id"], source["prediction_timestamp_utc"])
            if key not in member_sets or not source["primary_weather_and_dynamic_15_eligible"]:
                continue
            for j, other in controls:
                if (
                    source["grid_id"] != other["grid_id"]
                    or source["prediction_timestamp_utc"][:7]
                    != other["prediction_timestamp_utc"][:7]
                ):
                    continue
                delta = (
                    datetime.fromisoformat(other["prediction_timestamp_utc"])
                    - datetime.fromisoformat(source["prediction_timestamp_utc"])
                ).days
                sections = [
                    "all_same_grid_month",
                    "gap_1_to_3_days" if abs(delta) <= 3 else "gap_4_to_30_days",
                    "other_day_before_source_day" if delta < 0 else "other_day_after_source_day",
                ]
                for group in member_sets[key]:
                    expected_pairs.add(
                        (
                            scenario,
                            group,
                            source["grid_id"],
                            source["prediction_timestamp_utc"],
                            other["prediction_timestamp_utc"],
                            i,
                            j,
                            delta,
                        )
                    )
                    for variant, column in zip(VARIANTS, SCORE_COLUMNS, strict=True):
                        a, b = source[column], other[column]
                        if not math.isfinite(a) or not math.isfinite(b):
                            raise ValueError("Finite common-support scores")
                        for section in sections:
                            entry = accumulators[(group, scenario, variant, section)]
                            entry[0] += 1
                            entry[1] += int(a > b)
                            entry[2] += int(a == b)
    registry_columns = [
        "scenario",
        "source_group",
        "grid_id",
        "prediction_timestamp_utc_source",
        "prediction_timestamp_utc_other",
        "calendar_row_source",
        "calendar_row_other",
        "other_day_minus_source_day",
    ]
    observed_pairs = set(registry[registry_columns].itertuples(index=False, name=None))
    if len(registry) != len(observed_pairs) or observed_pairs != expected_pairs:
        raise ValueError("Exact unchanged comparison days; omitted sources never controls")
    metric_keys = ["source_group", "scenario", "variant", "slice"]
    if (
        len(actual) != 405
        or actual.duplicated(metric_keys).any()
        or set(actual[metric_keys].itertuples(index=False, name=None)) != set(accumulators)
    ):
        raise ValueError("All 405 metric identities")
    for row in actual.itertuples():
        key = (row.source_group, row.scenario, row.variant, row.slice)
        n, wins, ties = accumulators[key]
        value = float(Fraction(2 * wins + ties, 2 * n))
        if (row.pairs, row.wins, row.ties, row.auxiliary_pair_AUC) != (n, wins, ties, value):
            raise ValueError("Direct integer metric and exact rational ratio")
    original = pd.read_csv(RUN / "metrics.csv", float_precision="round_trip")
    old = original.loc[original.cohort.eq("separate_Mersin")].drop(columns="cohort")
    restored = actual.loc[actual.source_group.eq(GROUPS[0])].drop(columns="source_group")
    old_keys = ["scenario", "variant", "slice"]
    pd.testing.assert_frame_equal(
        old.sort_values(old_keys).reset_index(drop=True),
        restored.sort_values(old_keys).reset_index(drop=True),
        check_exact=True,
    )
    deltas = pd.read_csv(SOURCE / "group_vs_original_delta.csv", float_precision="round_trip")
    if len(deltas) != 270 or deltas.duplicated(metric_keys).any():
        raise ValueError("All 270 nested-subset deltas")
    reference = restored.set_index(old_keys)
    for row in deltas.itertuples():
        baseline = reference.loc[(row.scenario, row.variant, row.slice)]
        if (
            row.delta_from_original != row.auxiliary_pair_AUC - baseline.auxiliary_pair_AUC
            or row.original_pairs != baseline.pairs
        ):
            raise ValueError("Delta uses the same original scenario and model")
    if not all(digest(p) == sha for p, sha in pins.items()):
        raise ValueError("Inputs unchanged")
    out = (
        BASE
        / "source_disjoint_frozen_assessment_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    body = {
        "status": "independent_405_metrics_47889_pairs_135_reference_rows_verified",
        "metrics": len(actual),
        "pair_registry_rows": len(registry),
        "reference_rows_restored": len(old),
        "delta_rows": len(deltas),
        "new_training_or_prediction_calls": 0,
        "excluded_sources_relabelled": 0,
        "true_fire_validation": False,
        "final_merge": False,
        "source_readback_sha256": digest(SOURCE / "readback.json"),
        "auditor_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), body["status"], flush=True)


if __name__ == "__main__":
    main()
