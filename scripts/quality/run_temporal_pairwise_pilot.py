"""Bounded, explicitly chosen same-grid/month linear source-context ranking pilot."""

import argparse
import json
import os
import subprocess
import sys
import warnings
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CONFIG = ROOT / "configs/temporal_pairwise_execution_v1.json"
CALENDAR = BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896"
PROPOSALS = BASE / "satellite_PU_L_proposals_v1/20261120T005519Z_62f3f815"
SPLIT = BASE / "source_calendar_temporal_split_audit_v1/20261121T173542Z_11d5b339"
FIXED = BASE / "source_calendar_fixed_model_run_v1/20261121T171148Z_91ab9c78"
INDICATOR = "existing_scenario_proposal_context"
FIT = "proposed_fit_2018_2021"
HELD = "proposed_assessment_2022"


def validate(config):
    join.require(
        config["decision_source"]
        == "researcher_explicit_A_same_cell_month_daily_difference_ranking_pilot"
        and config["direction"] == "A_pairwise_linear_only"
        and config["new_models_authorized"] == 9
        and config["local_time_limit_seconds"] == 900
        and config["fit_years"] == [2018, 2019, 2020, 2021]
        and config["exploratory_comparison_year"] == 2022,
        "Explicit A scope and fixed temporal roles",
    )
    join.require(
        all(
            config[f] is False
            for f in (
                "scientific_values_2023_2024_2025_read_permitted",
                "original_U_or_weights_changed",
                "true_Y_or_accepted_L_assignment_authorized",
                "negative_label_permitted",
                "hyperparameter_or_production_scenario_selection_authorized",
                "fire_probabilities_or_validated_risk_colors_authorized",
                "cloud_permitted",
                "final_merge_permitted",
                "fit_intercept",
            )
        )
        and config["daily_observation_status"] == "unknown"
        and (config["C"], config["solver"], config["max_iter"], config["seed"])
        == (1.0, "lbfgs", 1000, 20261121),
        "No widening from auxiliary pair ranking to fire labels, future years or main product",
    )


def pair_indices(metadata, complete, source, role):
    """Global frozen calendar row indices; other context is not a fire negative."""
    frame = metadata.loc[metadata.review_temporal_role.eq(role) & complete, join.KEYS].copy()
    frame["month"] = frame.prediction_timestamp_utc.str[:7]
    frame["source"] = [k in source for k in frame[join.KEYS].itertuples(index=False, name=None)]
    a, b = [], []
    for _, group in frame.groupby(["grid_id", "month"], sort=True):
        positive = group.index[group.source].to_numpy(dtype=np.int64)
        other = group.index[~group.source].to_numpy(dtype=np.int64)
        if len(positive) and len(other):
            a.append(np.repeat(positive, len(other)))
            b.append(np.tile(other, len(positive)))
    join.require(bool(a), "Both contexts have same-grid/year/month support")
    return np.concatenate(a), np.concatenate(b)


def credit(scores, a, b):
    difference = scores[a] - scores[b]
    join.require(np.isfinite(difference).all(), "All declared pair scores finite")
    wins, ties = int((difference > 0).sum()), int((difference == 0).sum())
    return {
        "pairs": len(a),
        "wins": wins,
        "ties": ties,
        "auxiliary_pair_AUC": (wins + ties / 2) / len(a),
        "source_keys_with_comparator": len(set(a)),
        "other_keys_with_comparator_not_true_negatives": len(set(b)),
    }


def run():
    config = json.loads(CONFIG.read_bytes())
    validate(config)
    pins = {
        CALENDAR
        / "readback.json": "b718ed5d7ff492ddaf6d5217e7f88b3f62a6024a9d2138f4225154b3e3576040",
        PROPOSALS
        / "readback.json": "679a5ad9eab6342fa153c46cbbcc8f1e494b92256b592ba84f24823d0c0a4a85",
        SPLIT / "readback.json": "7634d30483c7e6bc5dcb3c7315631242f7109001776afc244bdfdced86bd7920",
        FIXED / "readback.json": "ff51e4790f92eeca51b1db107c38c876a5a2b6ea34d54d4a3451d32754e28f4f",
        CONFIG: digest(CONFIG),
        Path(__file__): digest(Path(__file__)),
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "Frozen choices and input receipts")
    reports = {
        p: json.loads((p / "readback.json").read_bytes())
        for p in (CALENDAR, PROPOSALS, SPLIT, FIXED)
    }
    for folder in (CALENDAR, PROPOSALS, FIXED):
        pins.update({folder / name: h for name, h in reports[folder]["artifact_sha256"].items()})
    pins.update({ROOT / p: h for p, h in reports[SPLIT]["input_sha256"].items()})
    join.require(
        reports[SPLIT]["shared_observed_graph_blocks_between_calendar_roles"] == 0
        and all(digest(p) == h for p, h in pins.items()),
        "Current input hashes and observed graph separation",
    )
    snapshot = CALENDAR / reports[CALENDAR]["snapshot_directory"]
    x = parse_csv((snapshot / "features.csv").read_bytes())
    metadata = parse_csv((snapshot / "review_roles.csv").read_bytes())
    pd.testing.assert_frame_equal(x[join.KEYS], metadata[join.KEYS], check_exact=True)
    join.require(
        metadata.target.isna().all()
        and metadata.accepted_L_membership.isna().all()
        and metadata.daily_observation_status.eq("unknown").all(),
        "Unknown real labels retained",
    )
    years = pd.to_datetime(metadata.prediction_timestamp_utc, utc=True).dt.year
    join.require(
        years.loc[metadata.review_temporal_role.eq(FIT)].isin(config["fit_years"]).all()
        and years.loc[metadata.review_temporal_role.eq(HELD)].eq(2022).all()
        and not metadata.prediction_timestamp_utc.str[:10].isin(["2021-12-31", "2022-12-31"]).any(),
        "Strict historical fit/2022 exploratory roles",
    )
    names = reports[SPLIT]["dynamic_feature_names"]
    join.require(len(names) == 15 and set(names) <= set(join.feature_names()), "Dynamic allowlist")
    complete = x[names].notna().all(axis=1)
    fit_rows = metadata.index[metadata.review_temporal_role.eq(FIT) & complete].to_numpy()
    held_rows = metadata.index[metadata.review_temporal_role.eq(HELD)].to_numpy()
    scaler = StandardScaler().fit(x.loc[fit_rows, names])
    z = np.full((len(x), len(names)), np.nan)
    z[complete] = scaler.transform(x.loc[complete, names])
    groups = parse_csv((PROPOSALS / "all_first_cells_with_proposal_flags.csv").read_bytes())
    groups = groups.loc[groups.possible_L_proposal]
    out = (
        BASE
        / "temporal_pairwise_run_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    print(out.relative_to(ROOT).as_posix(), flush=True)
    artifacts, summaries = {}, []
    supports = {r["scenario"]: r for r in reports[SPLIT]["scenario_summaries"]}
    for scenario, block in groups.groupby("scenario", sort=True):
        source = set(block[join.KEYS].itertuples(index=False, name=None))
        a, b = pair_indices(metadata, complete, source, FIT)
        ha, hb = pair_indices(metadata, complete, source, HELD)
        expected = supports[scenario]["potential_complete_dynamic_pair_support_not_training"]
        join.require(
            len(a) == expected[FIT]["potential_same_grid_year_month_pairs"]
            and len(ha) == expected[HELD]["potential_same_grid_year_month_pairs"],
            "Exact reviewed pair counts",
        )
        differences = z[a] - z[b]
        estimator = LogisticRegression(
            C=config["C"],
            solver=config["solver"],
            fit_intercept=False,
            max_iter=config["max_iter"],
            random_state=config["seed"],
        )
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            estimator.fit(
                np.vstack([differences, -differences]), np.r_[np.ones(len(a)), np.zeros(len(a))]
            )
        scores = np.full(len(x), np.nan)
        scores[complete] = estimator.decision_function(z[complete])
        fixed = parse_csv((FIXED / (scenario + "_calendar_scores.csv")).read_bytes())
        pd.testing.assert_frame_equal(
            fixed[join.KEYS],
            metadata.loc[held_rows, join.KEYS].reset_index(drop=True),
            check_exact=True,
        )
        frame = fixed.copy()
        frame["dynamic_15_complete"] = complete.loc[held_rows].to_numpy()
        frame["temporal_pairwise_linear_score_not_probability"] = scores[held_rows]
        comparison = {"pairwise_linear": credit(scores, ha, hb)}
        for variant in ("full_27_features", "weather_only", "static_cover_terrain_only"):
            reference = np.full(len(x), np.nan)
            reference[held_rows] = frame[variant + "_auxiliary_source_score"]
            comparison["fixed_" + variant] = credit(reference, ha, hb)
        folder = out / scenario
        folder.mkdir()
        frame.to_csv(folder / "assessment_scores.csv", index=False)
        for name, left, right in (
            ("fit_pair_indices.csv", a, b),
            ("assessment_pair_indices.csv", ha, hb),
        ):
            pd.DataFrame({"source_calendar_row": left, "other_calendar_row": right}).to_csv(
                folder / name, index=False
            )
        pd.DataFrame(
            {
                "feature": names,
                "fit_mean": scaler.mean_,
                "fit_scale": scaler.scale_,
                "coefficient": estimator.coef_[0],
            }
        ).to_csv(folder / "coefficients.csv", index=False)
        joblib.dump(
            {
                "model": estimator,
                "scaler": scaler,
                "retained_features": names,
                "fit_scaler_calendar_rows": fit_rows,
                "meaning": "within_cell_month_auxiliary_source_ranking_not_fire_probability",
            },
            folder / "pairwise_linear.joblib",
        )
        summaries.append(
            {
                "scenario": scenario,
                "fit_pairs": len(a),
                "fit_scaler_unique_rows": len(fit_rows),
                "fit_iterations": estimator.n_iter_.tolist(),
                "comparison_same_complete_dynamic_pairs": comparison,
            }
        )
        for p in folder.iterdir():
            artifacts[p.relative_to(out).as_posix()] = digest(p)
        print(
            scenario,
            "fit complete; paired 2022 AUC",
            comparison["pairwise_linear"]["auxiliary_pair_AUC"],
            flush=True,
        )
    join.require(
        len(summaries) == 9 and all(digest(p) == h for p, h in pins.items()),
        "Exactly nine fits and immutable inputs",
    )
    report = {
        "status": "nine_temporal_pairwise_pilots_complete_pending_separate_audit",
        "decision": config,
        "scenario_summaries": summaries,
        "fit_scaler_rows": len(fit_rows),
        "assessment_rows_retained_per_scenario": len(held_rows),
        "assessment_complete_dynamic_rows": int(complete.loc[held_rows].sum()),
        "new_models_fitted": 9,
        "true_Y_or_accepted_L_created": 0,
        "original_U_or_weights_changed": False,
        "fire_risk_validated": False,
        "final_merge_performed": False,
        "producer_sha256": digest(Path(__file__)),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": artifacts,
    }
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("readback_sha256", digest(p), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        run()
    else:
        config = json.loads(CONFIG.read_bytes())
        validate(config)
        environment = os.environ | {
            k: "2"
            for k in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        }
        try:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--worker"],
                cwd=ROOT,
                env=environment,
                timeout=900,
                check=False,
            )
            raise SystemExit(result.returncode)
        except subprocess.TimeoutExpired:
            print(
                "15-minute limit; partial outputs retained; no completed pilot acceptance",
                flush=True,
            )
            raise SystemExit(124) from None
