"""Separate no-fit validation of predefined weather-QA subset support and credits."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
BUNDLE = BASE / "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1"
MERSIN = BASE / "cross_source_calendar_feature_review_v1/20261121T180737Z_c322d93c"
RUN = BASE / "nonlinear_rank_run_v1/20261123T132502Z_6193ac44"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    folder = parser.parse_args().review.resolve()
    require(
        folder.parent == (BASE / "weather_score_support_review_v1").resolve(),
        "Workspace review only",
    )
    report = json.loads((folder / "readback.json").read_bytes())
    pins = {ROOT / p: sha for p, sha in report["input_sha256"].items()}
    pins[folder / "readback.json"] = digest(folder / "readback.json")
    pins.update({folder / name: sha for name, sha in report["artifact_sha256"].items()})
    require(
        all(digest(p) == sha for p, sha in pins.items()), "Current immutable source and QA outputs"
    )
    require(
        report["new_model_or_prediction_calls"] == report["true_Y_or_accepted_L_created"] == 0
        and not report["new_threshold_selected"]
        and not report["final_merge_performed"],
        "No widening to training or labels",
    )
    policy = report["weather_policy"]
    require(
        (
            policy["primary_minimum_valid_area_fraction"],
            policy["sensitivity_minimum_valid_area_fraction"],
            policy["area_numerical_tolerance"],
        )
        == (1, 0.9, 1e-9),
        "Original pre-existing thresholds",
    )
    quality = pd.read_csv(folder / "record_quality_context.csv")
    fit_summary = pd.read_csv(folder / "original_fit_quality_support.csv")
    summary = pd.read_csv(folder / "assessment_profile_support.csv")
    metrics = pd.read_csv(folder / "assessment_profile_metrics.csv", float_precision="round_trip")
    pairs = pd.read_csv(folder / "assessment_profile_pair_indices.csv")
    old_metrics = pd.read_csv(RUN / "metrics.csv", float_precision="round_trip")
    model_run = json.loads((RUN / "readback.json").read_bytes())
    names = model_run["features"]
    full_x, full_m, full_q = [
        pd.read_csv(BUNDLE / n, float_precision="round_trip")
        for n in ("features.csv", "inspection_memberships.csv", "provenance.csv")
    ]
    mr = json.loads((MERSIN / "readback.json").read_bytes())
    snap = MERSIN / mr["snapshot_directory"]
    mx, mm, mq = [
        pd.read_csv(snap / n, float_precision="round_trip")
        for n in ("features.csv", "review_roles.csv", "provenance.csv")
    ]
    held = full_m.prediction_timestamp_utc.str[:4].eq("2022")
    profiles = {
        "primary_full_area": 1 - 1e-9,
        "sensitivity_90_area": 0.9 - 1e-9,
        "observed_positive_area": 0,
    }
    require(
        len(quality) == 8956
        and len(summary) == 54
        and len(fit_summary) == 27
        and len(metrics) == 540,
        "All cohorts/scenarios/predefined QA profiles retained",
    )
    for row in fit_summary.itertuples(index=False):
        layout = pd.read_csv(RUN / row.scenario / "fit_layout.csv")
        q = full_q.iloc[layout.calendar_row]
        complete = np.isfinite(full_x.iloc[layout.calendar_row][names].to_numpy(dtype=float)).all(
            axis=1
        )
        threshold = profiles[row.profile]
        area = q.weather_min_valid_area_fraction.to_numpy()
        mask = (
            complete & ~q.weather_missing_any.to_numpy() & ~q.weather_large_negative_rain.to_numpy()
        )
        mask &= area > 0 if threshold == 0 else area >= threshold
        require(
            (
                row.original_fit_rows,
                row.fit_rows_meeting_profile,
                row.fit_source_rows_meeting_profile,
            )
            == (
                len(layout),
                int(mask.sum()),
                int(layout.relevance_source_context_not_Y.to_numpy()[mask].sum()),
            ),
            "Independent original-fit QA counts",
        )
    checked = []
    for cohort, x, meta, q in (
        (
            "four_province",
            full_x.loc[held].reset_index(drop=True),
            full_m.loc[held].reset_index(drop=True),
            full_q.loc[held].reset_index(drop=True),
        ),
        ("separate_Mersin", mx, mm, mq),
    ):
        c = quality.loc[quality.cohort.eq(cohort)].reset_index(drop=True)
        pd.testing.assert_frame_equal(c[KEYS], meta[KEYS], check_exact=True)
        complete = np.isfinite(x[names].to_numpy(dtype=float)).all(axis=1)
        np.testing.assert_array_equal(c.dynamic_15_complete, complete)
        for scenario in sorted(summary.scenario.unique()):
            values = pd.read_csv(
                RUN / scenario / (cohort + "_scores.csv"), float_precision="round_trip"
            )
            source = (
                meta["S_candidate_context_" + scenario].to_numpy()
                if cohort == "four_province"
                else meta.original_source_record_key_present.to_numpy()
            )
            for profile, threshold in profiles.items():
                coverage = q.weather_min_valid_area_fraction.to_numpy()
                mask = (
                    complete
                    & ~q.weather_missing_any.to_numpy()
                    & ~q.weather_large_negative_rain.to_numpy()
                )
                mask &= coverage > 0 if threshold == 0 else coverage >= threshold
                np.testing.assert_array_equal(c[profile + "_and_dynamic_15_complete"], mask)
                temp = meta.loc[mask, KEYS].copy()
                temp["original_row"] = temp.index
                temp["month"] = temp.prediction_timestamp_utc.str[:7]
                temp["source"] = source[temp.index]
                cart = temp.loc[temp.source].merge(
                    temp.loc[~temp.source], on=["grid_id", "month"], suffixes=("_a", "_b")
                )
                expected = set(zip(cart.original_row_a, cart.original_row_b, strict=True))
                saved = pairs.loc[
                    pairs.cohort.eq(cohort)
                    & pairs.scenario.eq(scenario)
                    & pairs.profile.eq(profile)
                ]
                indices = saved[["source_calendar_row", "other_calendar_row"]].to_numpy(dtype=int)
                require(
                    len(indices) == len(expected) and set(map(tuple, indices)) == expected,
                    "Independent filtered Cartesian pair identities",
                )
                support = summary.loc[
                    summary.cohort.eq(cohort)
                    & summary.scenario.eq(scenario)
                    & summary.profile.eq(profile)
                ].iloc[0]
                require(
                    support.records_meeting_profile == int(mask.sum())
                    and support.source_records_meeting_profile == int((mask & source).sum())
                    and support.same_cell_month_pairs == len(indices),
                    "Independent profile support counts",
                )
                dates = pd.to_datetime(meta.prediction_timestamp_utc, utc=True, format="ISO8601")
                gaps = np.array([(dates.iloc[a] - dates.iloc[b]).days for a, b in indices])
                cuts = {
                    "all_same_grid_month": np.ones(len(indices), dtype=bool),
                    "gap_1_to_3_days": np.isin(abs(gaps), [1, 2, 3]),
                    "gap_4_to_30_days": (abs(gaps) >= 4) & (abs(gaps) <= 30),
                    "other_day_before_source_day": gaps > 0,
                    "other_day_after_source_day": gaps < 0,
                }
                chosen = metrics.loc[
                    metrics.cohort.eq(cohort)
                    & metrics.scenario.eq(scenario)
                    & metrics.profile.eq(profile)
                ]
                for row in chosen.itertuples(index=False):
                    column = (
                        "xgboost_source_score_not_probability"
                        if row.variant == "XGBoost"
                        else "frozen_linear_source_score_not_probability"
                    )
                    v = values[column].to_numpy()
                    select = indices[cuts[row.slice]]
                    wins = sum(v[a] > v[b] for a, b in select)
                    ties = sum(v[a] == v[b] for a, b in select)
                    n = len(select)
                    require(
                        (row.pairs, row.wins, row.ties) == (n, wins, ties),
                        "Independent subset integer credits",
                    )
                    require(
                        row.auxiliary_pair_AUC == (wins + ties / 2) / n,
                        "Exact subset auxiliary AUC",
                    )
                    if profile == "observed_positive_area":
                        old = old_metrics.loc[
                            old_metrics.cohort.eq(cohort)
                            & old_metrics.scenario.eq(scenario)
                            & old_metrics.variant.eq(row.variant)
                            & old_metrics["slice"].eq(row.slice)
                        ].iloc[0]
                        require(
                            (row.pairs, row.wins, row.ties, row.auxiliary_pair_AUC)
                            == (old.pairs, old.wins, old.ties, old.auxiliary_pair_AUC),
                            "Broad observed profile restores original frozen result exactly",
                        )
                checked.append(
                    {
                        "cohort": cohort,
                        "scenario": scenario,
                        "profile": profile,
                        "pairs": len(indices),
                    }
                )
    require(all(digest(p) == sha for p, sha in pins.items()), "No original artifact changed")
    out = (
        BASE
        / "weather_score_support_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    body = {
        "status": "fixed_score_weather_QA_subset_support_and_all_credits_verified",
        "review": folder.relative_to(ROOT).as_posix(),
        "subsets": checked,
        "metric_rows_independently_verified": len(metrics),
        "original_fit_profile_rows_verified": len(fit_summary),
        "observed_profile_restores_frozen_original": True,
        "new_model_or_prediction_calls": 0,
        "weather_QA_filtered_models_retrained": False,
        "true_fire_validation": False,
        "final_merge_performed": False,
        "producer_sha256": digest(Path(__file__)),
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
    }
    path = out / "readback.json"
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)


if __name__ == "__main__":
    main()
