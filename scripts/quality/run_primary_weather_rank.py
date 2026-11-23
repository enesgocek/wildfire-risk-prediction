"""Nine fixed rankers aligned with the existing full-area weather QA rule."""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
import review_weather_support_on_frozen_scores as qa
import run_nonlinear_rank_comparison as previous
import xgboost as xgb

from wildfire_risk_prediction import primary_weather_rank as guard
from wildfire_risk_prediction import ranking_queries, weather_policy, weather_support_review
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require

ROOT, BASE = qa.ROOT, qa.BASE
CONFIG = ROOT / "configs/primary_weather_rank_execution_v1.json"
AUDIT = BASE / "weather_score_support_audit_v1/20261123T143011Z_0df65000"
QA = BASE / "weather_score_support_review_v1/20261123T142800Z_8725a867"


def work(out):
    start = time.monotonic()
    policy = json.loads(CONFIG.read_bytes())
    proposal = json.loads(previous.prep.CONFIG.read_bytes())
    guard.validate(policy, weather_policy.specification(), proposal)
    require(xgb.__version__ == "3.4.1", "Same fixed installed ranker version")
    require(
        digest(AUDIT / "readback.json") == policy["predefined_weather_support_audit_sha256"]
        and digest(previous.prep.CONFIG) == policy["parameter_source_proposal_sha256"],
        "Frozen quality and parameter choices",
    )
    audit = json.loads((AUDIT / "readback.json").read_bytes())
    pins = {ROOT / name: sha for name, sha in audit["input_sha256"].items()}
    pins[AUDIT / "readback.json"] = digest(AUDIT / "readback.json")
    for p in (
        CONFIG,
        Path(__file__),
        Path(guard.__file__),
        Path(weather_support_review.__file__),
        Path(weather_policy.__file__),
        Path(previous.__file__),
        Path(qa.__file__),
    ):
        pins[p] = digest(p)
    require(
        all(digest(p) == sha for p, sha in pins.items()),
        "All existing data, models and code unchanged",
    )
    x, meta, q = [
        pd.read_csv(qa.BUNDLE / name, float_precision="round_trip")
        for name in ("features.csv", "inspection_memberships.csv", "provenance.csv")
    ]
    mr = json.loads((qa.MERSIN / "readback.json").read_bytes())
    snap = qa.MERSIN / mr["snapshot_directory"]
    mx, mm, mq = [
        pd.read_csv(snap / name, float_precision="round_trip")
        for name in ("features.csv", "review_roles.csv", "provenance.csv")
    ]
    valid = weather_support_review.inspect(
        x, q
    ).primary_full_area_and_dynamic_15_complete.to_numpy()
    mvalid = weather_support_review.inspect(
        mx, mq
    ).primary_full_area_and_dynamic_15_complete.to_numpy()
    held = meta.review_temporal_role.eq("proposed_assessment_2022").to_numpy()
    old_support = pd.read_csv(QA / "original_fit_quality_support.csv")
    old_pairs = pd.read_csv(QA / "assessment_profile_pair_indices.csv")
    old_metrics = pd.read_csv(QA / "assessment_profile_metrics.csv", float_precision="round_trip")
    names = ranking_queries.DYNAMIC_FEATURES
    metrics, checkpoints = [], []
    for scenario in sorted(
        meta.columns[meta.columns.str.startswith("S_candidate_context_")].str.removeprefix(
            "S_candidate_context_"
        )
    ):
        source = meta["S_candidate_context_" + scenario].to_numpy()
        layout = previous.nr.training_layout(meta, source, valid)
        expected = old_support.loc[
            old_support.scenario.eq(scenario) & old_support.profile.eq("primary_full_area")
        ].iloc[0]
        require(
            len(layout) == expected.fit_rows_meeting_profile
            and int(layout.relevance_source_context_not_Y.sum())
            == expected.fit_source_rows_meeting_profile,
            "Pre-audited full-area learning support",
        )
        folder = out / scenario
        folder.mkdir()
        layout.to_csv(folder / "fit_layout.csv", index=False)
        model = xgb.XGBRanker(
            objective=proposal["objective"], **proposal["fixed_parameters_proposed"]
        )
        model.fit(
            x.loc[layout.calendar_row, names],
            layout.relevance_source_context_not_Y.astype(int).to_numpy(),
            qid=layout.qid.to_numpy(),
            verbose=False,
        )
        model.save_model(folder / "ranker.json")
        previous.dump(folder / "booster_config.json", json.loads(model.get_booster().save_config()))
        for cohort, features, metadata, eligible, s in (
            (
                "four_province",
                x.loc[held].reset_index(drop=True),
                meta.loc[held].reset_index(drop=True),
                valid[held],
                source[held],
            ),
            ("separate_Mersin", mx, mm, mvalid, mm.original_source_record_key_present.to_numpy()),
        ):
            old = pd.read_csv(
                qa.RUN / scenario / (cohort + "_scores.csv"), float_precision="round_trip"
            )
            pd.testing.assert_frame_equal(old[KEYS], metadata[KEYS], check_exact=True)
            score = np.full(len(metadata), np.nan)
            score[eligible] = model.predict(features.loc[eligible, names]).astype(float)
            frame = metadata[
                KEYS + ["target", "accepted_L_membership", "daily_observation_status"]
            ].copy()
            frame["primary_weather_and_dynamic_15_eligible"] = eligible
            frame["new_primary_weather_source_score_not_probability"] = score
            for column in (
                "xgboost_source_score_not_probability",
                "frozen_linear_source_score_not_probability",
            ):
                frame["previous_broad_" + column] = old[column]
            frame.to_csv(folder / (cohort + "_scores.csv"), index=False)
            pairs = qa.pair_frame(metadata, s, eligible)
            expected_pairs = old_pairs.loc[
                old_pairs.cohort.eq(cohort)
                & old_pairs.scenario.eq(scenario)
                & old_pairs.profile.eq("primary_full_area"),
                ["source_calendar_row", "other_calendar_row"],
            ].reset_index(drop=True)
            pd.testing.assert_frame_equal(pairs, expected_pairs, check_exact=True)
            pairs.to_csv(folder / (cohort + "_pair_indices.csv"), index=False)
            for variant, values in (
                ("primary_weather_XGBoost", score),
                ("broad_weather_XGBoost", old.xgboost_source_score_not_probability.to_numpy()),
                ("frozen_linear", old.frozen_linear_source_score_not_probability.to_numpy()),
            ):
                for result in previous.nr.evaluate_slices(metadata, pairs, values):
                    if result["slice"] not in qa.TIME_SLICES:
                        continue
                    if variant != "primary_weather_XGBoost":
                        label = "XGBoost" if variant == "broad_weather_XGBoost" else variant
                        saved = old_metrics.loc[
                            old_metrics.cohort.eq(cohort)
                            & old_metrics.scenario.eq(scenario)
                            & old_metrics.profile.eq("primary_full_area")
                            & old_metrics.variant.eq(label)
                            & old_metrics["slice"].eq(result["slice"])
                        ].iloc[0]
                        require(
                            all(saved[key] == value for key, value in result.items()),
                            "Unchanged baseline on identical QA pairs",
                        )
                    metrics.append(
                        {"cohort": cohort, "scenario": scenario, "variant": variant, **result}
                    )
        checkpoint = {
            "scenario": scenario,
            "fit_rows": len(layout),
            "fit_queries": int(layout.qid.nunique()),
            "fit_source_context_rows_not_true_positives": int(
                layout.relevance_source_context_not_Y.sum()
            ),
            "elapsed_seconds": time.monotonic() - start,
            "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
            "artifact_sha256": {p.name: digest(p) for p in folder.iterdir()},
        }
        previous.dump(folder / "checkpoint.json", checkpoint)
        checkpoints.append(checkpoint)
        print(scenario, "full-area quality-aligned checkpoint complete", flush=True)
    pd.DataFrame(metrics).to_csv(out / "metrics.csv", index=False)
    require(
        all(digest(p) == sha for p, sha in pins.items()),
        "No old model or original feature package modified",
    )
    body = {
        "status": "nine_fixed_primary_weather_rankers_complete_pending_audit",
        "decision": policy,
        "fixed_proposal": proposal,
        "features": names,
        "new_models_fitted": len(checkpoints),
        "elapsed_seconds": time.monotonic() - start,
        "scenario_summaries": checkpoints,
        "producer_sha256": digest(Path(__file__)),
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "artifact_sha256": {
            p.relative_to(out).as_posix(): digest(p) for p in out.rglob("*") if p.is_file()
        },
        "true_Y_or_accepted_L_created": 0,
        "fire_risk_validated": False,
        "closed_year_values_opened": False,
        "final_merge_performed": False,
    }
    previous.dump(out / "readback.json", body)
    print("readback_sha256", digest(out / "readback.json"), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker-out", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker_out:
        work(args.worker_out)
        return
    policy = json.loads(CONFIG.read_bytes())
    guard.validate(
        policy, weather_policy.specification(), json.loads(previous.prep.CONFIG.read_bytes())
    )
    out = (
        BASE
        / "primary_weather_rank_run_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    print(out.relative_to(ROOT).as_posix(), flush=True)
    start = time.monotonic()
    env = os.environ | {
        name: "4"
        for name in (
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        )
    }
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__)), "--worker-out", str(out)],
            env=env,
            timeout=900,
            check=False,
        )
        status = "child_completed" if result.returncode == 0 else "child_failed_outputs_retained"
    except subprocess.TimeoutExpired:
        status = "time_limit_checkpoints_retained"
    previous.dump(
        out / "launcher_receipt.json",
        {
            "status": status,
            "hard_limit_seconds": 900,
            "elapsed_seconds": time.monotonic() - start,
            "completed_models": len(list(out.glob("*/checkpoint.json"))),
            "producer_sha256": digest(Path(__file__)),
        },
    )
    print(status, flush=True)
    if status != "child_completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
