"""Apply nine frozen pilots to the chosen 2022 Mersin-source calendar; no fitting."""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import audit_temporal_pairwise_pilot as independent
import close_temporal_pairwise_pilot as context
import joblib
import numpy as np
import pandas as pd
import prepare_cross_source_calendar_features as preparation
import run_temporal_pairwise_pilot as pairs
from mlflow import MlflowClient

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require
from wildfire_risk_prediction.feature_partition import parse_csv

ROOT, BASE = preparation.ROOT, preparation.BASE
REVIEW = BASE / "cross_source_calendar_feature_review_v1/20261121T180737Z_c322d93c"
AUDIT = BASE / "cross_source_calendar_feature_audit_v1/20261121T181138Z_4f2974b7"
MODELS = BASE / "temporal_pairwise_run_v1/20261121T174415Z_5a77b21e"


def main():
    decision = json.loads(preparation.CONFIG.read_bytes())
    preparation.validate(decision)
    require(
        decision["fixed_nine_model_scoring_authorized"] is True
        and decision["existing_source_membership_auxiliary_indicator_authorized"] is True,
        "Explicit A frozen-model and source-context diagnostic",
    )
    pins = {
        REVIEW
        / "readback.json": "d32b99e6581c6a2412ba6013af727d4220d19d8e2d03666f8ebb48634d3ce0f6",
        AUDIT / "readback.json": "30e8a26839d83349e77f5dbed0f4059e912113b603a4a8fb9957e3bba9bcc163",
        MODELS
        / "readback.json": "b8e847f8d510721ce84b788161ae40ac5f3bfa098154b0e56a013fc380f83d82",
        preparation.CONFIG: digest(preparation.CONFIG),
        Path(__file__): digest(Path(__file__)),
    }
    for module in (preparation, pairs, independent, context):
        path = Path(module.__file__)
        pins[path] = digest(path)
    require(
        all(digest(p) == h for p, h in pins.items()),
        "Pinned A decision, X audit and trusted models",
    )
    report, audit, models = [
        json.loads((p / "readback.json").read_bytes()) for p in (REVIEW, AUDIT, MODELS)
    ]
    require(
        audit["shared_observed_graph_blocks_with_old_fit"] == 0 and audit["keys"] == 2383,
        "No observed shared graph with fit keys",
    )
    for folder, parent in ((REVIEW, report), (AUDIT, audit)):
        pins.update({folder / name: h for name, h in parent["artifact_sha256"].items()})
    pins.update({ROOT / name: h for name, h in audit["input_sha256"].items()})
    for summary in models["scenario_summaries"]:
        name = summary["scenario"] + "/pairwise_linear.joblib"
        pins[MODELS / name] = models["artifact_sha256"][name]
    require(
        all(digest(p) == h for p, h in pins.items()), "Current models and separate-source snapshots"
    )
    snapshot = REVIEW / report["snapshot_directory"]
    x, metadata = [
        parse_csv((snapshot / name).read_bytes()) for name in ("features.csv", "review_roles.csv")
    ]
    pd.testing.assert_frame_equal(x[KEYS], metadata[KEYS], check_exact=True)
    require(
        metadata.target.isna().all()
        and metadata.accepted_L_membership.isna().all()
        and metadata.daily_observation_status.eq("unknown").all()
        and metadata.prediction_timestamp_utc.str.startswith("2022-").all(),
        "Same unknown 2022 review roles",
    )
    source = set(
        metadata.loc[metadata.original_source_record_key_present, KEYS].itertuples(
            index=False, name=None
        )
    )
    require(len(source) == 81, "Original 81 source anchors, no satellite outcome conditioning")
    role = metadata.copy()
    role["review_temporal_role"] = pairs.HELD
    out = (
        BASE
        / "cross_source_fixed_model_run_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    artifacts, summaries, metrics, score_vectors = {}, [], [], []
    for summary in models["scenario_summaries"]:
        scenario = summary["scenario"]
        saved = joblib.load(MODELS / scenario / "pairwise_linear.joblib")
        state = joblib.hash(saved)
        model, scaler, names = saved["model"], saved["scaler"], saved["retained_features"]
        require(len(names) == 15 and not model.fit_intercept, "Frozen dynamic linear model")
        complete = x[names].notna().all(axis=1)
        score = np.full(len(x), np.nan)
        score[complete] = model.decision_function(scaler.transform(x.loc[complete, names]))
        manual = ((x.loc[complete, names].to_numpy() - scaler.mean_) / scaler.scale_) @ model.coef_[
            0
        ]
        np.testing.assert_allclose(score[complete], manual, rtol=1e-12, atol=1e-12)
        a, b = pairs.pair_indices(role, complete, source, pairs.HELD)
        expected = independent.independent_pairs(role, complete.to_numpy(), source, pairs.HELD)
        require(
            set(zip(a, b, strict=True)) == expected
            and len(a) == len(expected) == audit["complete_same_grid_month_pairs"],
            "Independent source/calendar/quality pair identities",
        )
        masks = context.date_slices(
            pd.to_datetime(metadata.prediction_timestamp_utc, utc=True), a, b
        )
        result = {}
        for name, mask in masks.items():
            if mask.any():
                value = pairs.credit(score, a[mask], b[mask])
                scalar = independent.independent_credit(
                    score, set(zip(a[mask], b[mask], strict=True))
                )
                require(
                    value["auxiliary_pair_AUC"] == scalar, "Independent scalar context score credit"
                )
            else:
                value = {"pairs": 0, "auxiliary_pair_AUC": None}
            result[name] = value
            metrics.append({"scenario": scenario, "slice": name, **value})
        require(joblib.hash(saved) == state, "Frozen model and fit-only scaler unchanged")
        frame = metadata.copy()
        frame["dynamic_15_complete"] = complete
        frame["fixed_linear_source_score_not_fire_probability"] = score
        path = out / (scenario + "_source_calendar_scores.csv")
        frame.to_csv(path, index=False)
        artifacts[path.name] = digest(path)
        score_vectors.append(score)
        summaries.append(
            {
                "scenario": scenario,
                "model_sha256": pins[MODELS / scenario / "pairwise_linear.joblib"],
                "model_state_hash_before_after": state,
                "rows": len(frame),
                "complete_dynamic_rows": int(complete.sum()),
                "complete_source_keys": int(
                    (complete & metadata.original_source_record_key_present).sum()
                ),
                "metric_slices": result,
            }
        )
        print(
            scenario,
            "fixed-source matched AUC",
            result["all_same_grid_month"]["auxiliary_pair_AUC"],
            flush=True,
        )
    pd.DataFrame(metrics).to_csv(out / "source_calendar_comparisons.csv", index=False)
    artifacts["source_calendar_comparisons.csv"] = digest(out / "source_calendar_comparisons.csv")
    np.testing.assert_array_equal(np.isnan(score_vectors[0]), ~complete.to_numpy())
    require(
        len(summaries) == 9 and all(digest(p) == h for p, h in pins.items()),
        "Exactly nine unchanged model scorings",
    )
    tracking = ROOT / "outputs/mlflow"
    database = tracking / "mlflow.db"
    backup = tracking / (
        "before-cross-source-fixed-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".db"
    )
    require(database.is_file() and not backup.exists(), "Unique local database backup")
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as src:
        with sqlite3.connect(backup) as dst:
            src.backup(dst)
    client = MlflowClient(tracking_uri="sqlite:///" + database.as_posix())
    experiment = client.get_experiment_by_name("satellite-source-ranking-pilot")
    require(
        experiment is not None and experiment.artifact_location.startswith(tracking.as_uri()),
        "Existing workspace local experiment",
    )
    run_id = client.create_run(
        experiment.experiment_id,
        tags={
            "mlflow.runName": "Mersin-2022-separate-source-nine-frozen-linear-models",
            "run_type": "cross_source_exploratory_context_not_verified_fire_test",
        },
    ).info.run_id
    values = {
        r["scenario"] + "_" + r["slice"] + "_auxiliary_AUC": r["auxiliary_pair_AUC"]
        for r in metrics
        if r["auxiliary_pair_AUC"] is not None
    }
    try:
        client.log_param(run_id, "new_models_fitted", 0)
        client.log_param(run_id, "source_record_keys", 81)
        client.log_param(run_id, "true_fire_validation", False)
        for key, value in values.items():
            client.log_metric(run_id, key, value)
        for folder, label in ((out, "diagnostic"), (AUDIT, "separate_feature_audit")):
            client.log_artifacts(run_id, str(folder), artifact_path=label)
        client.set_terminated(run_id, status="FINISHED")
    except Exception:
        client.set_terminated(run_id, status="FAILED")
        raise
    restored = client.get_run(run_id)
    require(
        restored.info.status == "FINISHED" and restored.data.metrics == values,
        "Exact local metric values read back",
    )
    body = {
        "status": (
            "separate_Mersin_source_calendar_frozen_scoring_and_independent_calculations_complete"
        ),
        "decision": decision,
        "rows_per_scenario": 2383,
        "source_anchors": 81,
        "scenario_summaries": summaries,
        "new_models_fitted": 0,
        "model_registry_entry_created": False,
        "source_and_true_fire_semantics_verified": False,
        "new_Y_or_accepted_L_created": 0,
        "negative_label_permitted": False,
        "original_U_or_weights_changed": False,
        "mlflow_run_id": run_id,
        "local_metrics_read_back_exact": len(values),
        "local_database_backup": backup.relative_to(ROOT).as_posix(),
        "local_database_backup_sha256": digest(backup),
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": artifacts,
        "producer_sha256": digest(Path(__file__)),
    }
    require(all(digest(p) == h for p, h in pins.items()), "Scientific inputs unchanged at close")
    path = out / "readback.json"
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        main()
    else:
        environment = os.environ | {
            k: "2" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
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
            print("Local limit; partial outputs retained; no acceptance", flush=True)
            raise SystemExit(124) from None
