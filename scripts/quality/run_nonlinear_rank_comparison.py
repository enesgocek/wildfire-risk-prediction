"""Nine fixed CPU rankers, checkpointed under a hard 900-second child deadline."""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
import prepare_nonlinear_rank_comparison as prep
import xgboost as xgb

from wildfire_risk_prediction import nonlinear_rank as nr
from wildfire_risk_prediction import ranking_queries as queries
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require

ROOT, BASE = prep.ROOT, prep.BASE
CONFIG = ROOT / "configs/nonlinear_rank_execution_v1.json"
PREPARATION = BASE / "nonlinear_rank_preparation_v1/20261123T131121Z_14674f77"
MERSIN_SCORES = BASE / "cross_source_fixed_model_run_v1/20261121T181438Z_bc972c9e"


def dump(path, body):
    require(not path.exists(), "Never overwrite a scientific checkpoint")
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def verified_inputs(policy):
    pins = {
        prep.CONFIG: policy["proposal_sha256"],
        PREPARATION / "readback.json": policy["preparation_sha256"],
        prep.BUNDLE
        / "readback.json": "86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366",
        prep.LINEAR
        / "readback.json": "b8e847f8d510721ce84b788161ae40ac5f3bfa098154b0e56a013fc380f83d82",
        prep.MERSIN
        / "readback.json": "d32b99e6581c6a2412ba6013af727d4220d19d8e2d03666f8ebb48634d3ce0f6",
        MERSIN_SCORES
        / "readback.json": "a4fb83beea02226eca149c5ca8a0383326a1db0143b2ca395adbc50a1e6ab6f9",
    }
    require(all(digest(p) == h for p, h in pins.items()), "Exact preparation and frozen sources")
    for folder in (PREPARATION, prep.BUNDLE, prep.LINEAR, prep.MERSIN, MERSIN_SCORES):
        r = json.loads((folder / "readback.json").read_bytes())
        for name, sha in r["artifact_sha256"].items():
            if name.endswith(".csv"):
                pins[folder / name] = sha
    for p in (
        CONFIG,
        Path(__file__),
        Path(nr.__file__),
        Path(queries.__file__),
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
    ):
        pins[p] = digest(p)
    require(all(digest(p) == h for p, h in pins.items()), "Current original input hashes")
    return pins


def work(out):
    start = time.monotonic()
    policy, proposal = [json.loads(p.read_bytes()) for p in (CONFIG, prep.CONFIG)]
    nr.validate_execution(policy, proposal)
    require(xgb.__version__ == "3.4.1", "Exact chosen XGBoost version")
    pins = verified_inputs(policy)
    x = pd.read_csv(prep.BUNDLE / "features.csv", float_precision="round_trip")
    meta = pd.read_csv(prep.BUNDLE / "inspection_memberships.csv")
    mr = json.loads((prep.MERSIN / "readback.json").read_bytes())
    mx = pd.read_csv(
        prep.MERSIN / mr["snapshot_directory"] / "features.csv", float_precision="round_trip"
    )
    mm = pd.read_csv(prep.MERSIN / mr["snapshot_directory"] / "review_roles.csv")
    mm["review_temporal_role"] = "proposed_assessment_2022"
    for features, metadata in ((x, meta), (mx, mm)):
        pd.testing.assert_frame_equal(features[KEYS], metadata[KEYS], check_exact=True)
    complete, mc = nr.finite_features(x), nr.finite_features(mx)
    held = meta.review_temporal_role.eq("proposed_assessment_2022").to_numpy()
    support = pd.read_csv(PREPARATION / "scenario_support.csv").set_index("scenario")
    source_m = mm.original_source_record_key_present.to_numpy()
    mpairs = nr.matched_pairs(mm, source_m, mc, "proposed_assessment_2022")
    require(len(mpairs) == 2329, "Exact separate Mersin pair support")
    mpairs.to_csv(out / "Mersin_pair_indices.csv", index=False)
    all_metrics, checkpoints = [], []
    for scenario in sorted(support.index):
        source = meta["S_candidate_context_" + scenario].to_numpy()
        layout = nr.training_layout(meta, source, complete)
        fit_pairs = nr.matched_pairs(meta, source, complete, "proposed_fit_2018_2021")
        pairs = nr.matched_pairs(meta, source, complete, "proposed_assessment_2022")
        for name, table in (
            ("fit_pair_indices.csv", fit_pairs),
            ("assessment_pair_indices.csv", pairs),
        ):
            pd.testing.assert_frame_equal(
                table, pd.read_csv(prep.LINEAR / scenario / name), check_exact=True
            )
        require(
            len(layout) == support.loc[scenario, "informative_fit_rows"]
            and layout.qid.nunique() == support.loc[scenario, "informative_fit_queries"],
            "Frozen informative training layout",
        )
        folder = out / scenario
        folder.mkdir()
        layout.to_csv(folder / "fit_layout.csv", index=False)
        pairs.to_csv(folder / "assessment_pair_indices.csv", index=False)
        model = xgb.XGBRanker(
            objective=proposal["objective"], **proposal["fixed_parameters_proposed"]
        )
        model.fit(
            x.loc[layout.calendar_row, queries.DYNAMIC_FEATURES],
            layout.relevance_source_context_not_Y.astype(int).to_numpy(),
            qid=layout.qid.to_numpy(),
            verbose=False,
        )
        model.save_model(folder / "ranker.json")
        model.get_booster().save_config()
        dump(folder / "booster_config.json", json.loads(model.get_booster().save_config()))
        scores = np.full(len(x), np.nan)
        scores[held & complete] = model.predict(
            x.loc[held & complete, queries.DYNAMIC_FEATURES]
        ).astype(float)
        ms = np.full(len(mx), np.nan)
        ms[mc] = model.predict(mx.loc[mc, queries.DYNAMIC_FEATURES]).astype(float)
        old = pd.read_csv(
            prep.LINEAR / scenario / "assessment_scores.csv", float_precision="round_trip"
        )
        mold = pd.read_csv(
            MERSIN_SCORES / (scenario + "_source_calendar_scores.csv"), float_precision="round_trip"
        )
        pd.testing.assert_frame_equal(
            old[KEYS], meta.loc[held, KEYS].reset_index(drop=True), check_exact=True
        )
        pd.testing.assert_frame_equal(mold[KEYS], mm[KEYS], check_exact=True)
        linear = np.full(len(x), np.nan)
        linear[held] = old.temporal_pairwise_linear_score_not_probability.to_numpy()
        ml = mold.fixed_linear_source_score_not_fire_probability.to_numpy()
        for cohort, metadata, pair_table, score, old_score, mask in (
            ("four_province", meta, pairs, scores, linear, held),
            ("separate_Mersin", mm, mpairs, ms, ml, np.ones(len(mm), dtype=bool)),
        ):
            frame = metadata.loc[
                mask, KEYS + ["target", "accepted_L_membership", "daily_observation_status"]
            ].copy()
            frame["xgboost_source_score_not_probability"] = score[mask]
            frame["frozen_linear_source_score_not_probability"] = old_score[mask]
            frame.to_csv(folder / (cohort + "_scores.csv"), index=False)
            for variant, values in (("XGBoost", score), ("frozen_linear", old_score)):
                for metric in nr.evaluate_slices(metadata, pair_table, values):
                    all_metrics.append(
                        {"scenario": scenario, "cohort": cohort, "variant": variant, **metric}
                    )
        checkpoint = {
            "scenario": scenario,
            "new_models_fitted": 1,
            "fit_rows": len(layout),
            "fit_queries": int(layout.qid.nunique()),
            "fit_possible_pairs": len(fit_pairs),
            "elapsed_seconds_since_worker_start": time.monotonic() - start,
            "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
            "artifact_sha256": {p.name: digest(p) for p in folder.iterdir()},
        }
        dump(folder / "checkpoint.json", checkpoint)
        checkpoints.append(checkpoint)
        print(scenario, "checkpoint complete", flush=True)
    pd.DataFrame(all_metrics).to_csv(out / "metrics.csv", index=False)
    require(
        all(digest(p) == h for p, h in pins.items()), "Original inputs unchanged after nine fits"
    )
    report = {
        "status": "nine_fixed_rankers_complete_pending_independent_audit",
        "decision": policy,
        "fixed_proposal": proposal,
        "new_models_fitted": len(checkpoints),
        "elapsed_seconds": time.monotonic() - start,
        "environment": {
            "python": platform.python_version(),
            "xgboost": xgb.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "platform": platform.platform(),
        },
        "features": queries.DYNAMIC_FEATURES,
        "scenario_summaries": checkpoints,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {
            p.relative_to(out).as_posix(): digest(p) for p in out.rglob("*") if p.is_file()
        },
        "true_Y_or_accepted_L_created": 0,
        "negative_label_permitted": False,
        "closed_year_values_opened": False,
        "fire_risk_validated": False,
        "final_merge_performed": False,
    }
    dump(out / "readback.json", report)
    print("readback_sha256", digest(out / "readback.json"), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker-out", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker_out:
        work(args.worker_out)
        return
    policy = json.loads(CONFIG.read_bytes())
    nr.validate_execution(policy, json.loads(prep.CONFIG.read_bytes()))
    out = (
        BASE
        / "nonlinear_rank_run_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    print(out.relative_to(ROOT).as_posix(), flush=True)
    env = os.environ | {
        k: "4"
        for k in (
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        )
    }
    start = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__)), "--worker-out", str(out)],
            env=env,
            timeout=policy["local_time_limit_seconds"],
            check=False,
        )
        status = (
            "child_completed" if result.returncode == 0 else "child_failed_checkpoints_retained"
        )
    except subprocess.TimeoutExpired:
        status = "time_limit_reached_checkpoints_retained"
    dump(
        out / "launcher_receipt.json",
        {
            "status": status,
            "hard_limit_seconds": 900,
            "elapsed_seconds": time.monotonic() - start,
            "completed_checkpoints": len(list(out.glob("*/checkpoint.json"))),
            "producer_sha256": digest(Path(__file__)),
        },
    )
    print(status, flush=True)
    if status != "child_completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
