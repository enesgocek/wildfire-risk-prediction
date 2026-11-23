"""Verify full-area fit rows, serialized models and common-support comparison credits."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import audit_nonlinear_rank_comparison as independent
import numpy as np
import pandas as pd
import xgboost as xgb

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require

ROOT, BASE = independent.ROOT, independent.BASE
BUNDLE, MERSIN, BROAD = (
    independent.BUNDLE,
    independent.MERSIN,
    BASE / "nonlinear_rank_run_v1/20261123T132502Z_6193ac44",
)


def mask(features, quality, names):
    return (
        np.isfinite(features[names].to_numpy(dtype=float)).all(axis=1)
        & quality.weather_min_valid_area_fraction.ge(1 - 1e-9).to_numpy()
        & ~quality.weather_missing_any.to_numpy()
        & ~quality.weather_large_negative_rain.to_numpy()
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    folder = parser.parse_args().run.resolve()
    require(
        folder.parent == (BASE / "primary_weather_rank_run_v1").resolve(),
        "Workspace primary-QA experiment",
    )
    run = json.loads((folder / "readback.json").read_bytes())
    pins = {ROOT / p: sha for p, sha in run["input_sha256"].items()}
    pins[folder / "readback.json"] = digest(folder / "readback.json")
    pins.update({folder / p: sha for p, sha in run["artifact_sha256"].items()})
    require(
        all(digest(p) == sha for p, sha in pins.items()),
        "Current complete scientific artifact chain",
    )
    launch = json.loads((folder / "launcher_receipt.json").read_bytes())
    require(
        run["new_models_fitted"] == launch["completed_models"] == 9
        and launch["status"] == "child_completed"
        and launch["elapsed_seconds"] <= 900,
        "Exactly nine completed models inside the hard deadline",
    )
    pins[folder / "launcher_receipt.json"] = digest(folder / "launcher_receipt.json")
    pins[Path(independent.__file__)] = digest(Path(independent.__file__))
    names = run["features"]
    full_x, full_m, full_q = [
        pd.read_csv(BUNDLE / name, float_precision="round_trip")
        for name in ("features.csv", "inspection_memberships.csv", "provenance.csv")
    ]
    held = full_m.prediction_timestamp_utc.str.startswith("2022-")
    mr = json.loads((MERSIN / "readback.json").read_bytes())
    snap = MERSIN / mr["snapshot_directory"]
    mx, mm, mq = [
        pd.read_csv(snap / name, float_precision="round_trip")
        for name in ("features.csv", "review_roles.csv", "provenance.csv")
    ]
    valid, mv = mask(full_x, full_q, names), mask(mx, mq, names)
    metrics = pd.read_csv(folder / "metrics.csv", float_precision="round_trip")
    require(len(metrics) == 270 and len(names) == 15, "Fixed feature and metric scope")
    scenarios = sorted(metrics.scenario.unique())
    checked = []
    for scenario in scenarios:
        path = folder / scenario
        source = full_m["S_candidate_context_" + scenario].to_numpy()
        layout = pd.read_csv(path / "fit_layout.csv")
        expected = independent.cartesian(full_m, source, valid, [2018, 2019, 2020, 2021])
        require(
            len(layout) == len(set(expected.ravel()))
            and set(layout.calendar_row) == set(expected.ravel()),
            "Independent complete mixed full-area fit layout",
        )
        pd.testing.assert_frame_equal(
            layout[KEYS],
            full_m.loc[layout.calendar_row, KEYS].reset_index(drop=True),
            check_exact=True,
        )
        require(
            valid[layout.calendar_row].all() and layout.qid.is_monotonic_increasing,
            "Every fitted row meets primary weather coverage; sorted qid",
        )
        np.testing.assert_array_equal(
            layout.relevance_source_context_not_Y, source[layout.calendar_row]
        )
        for _, group in layout.groupby("qid"):
            require(
                group.grid_id.nunique() == group.prediction_timestamp_utc.str[:7].nunique() == 1
                and group.relevance_source_context_not_Y.nunique() == 2,
                "Only mixed cell-month queries",
            )
        model = xgb.XGBRanker()
        model.load_model(path / "ranker.json")
        require(
            model.get_booster().feature_names == names
            and model.get_booster().num_boosted_rounds() == 100,
            "Saved model has exact 15 features and 100 rounds",
        )
        cfg = json.loads((path / "booster_config.json").read_bytes())["learner"]
        require(
            cfg["generic_param"]["device"] == "cpu"
            and cfg["generic_param"]["nthread"] == "4"
            and cfg["generic_param"]["seed"] == "20261123"
            and cfg["objective"]["name"] == "rank:pairwise"
            and cfg["gradient_booster"]["gbtree_train_param"]["tree_method"] == "hist",
            "Frozen CPU ranker setup",
        )
        tree = cfg["gradient_booster"]["tree_train_param"]
        require(
            int(tree["max_depth"]) == 3
            and float(tree["min_child_weight"]) == 5
            and abs(float(tree["learning_rate"]) - 0.05) < 1e-8
            and float(tree["reg_lambda"])
            == float(tree["subsample"])
            == float(tree["colsample_bytree"])
            == 1,
            "Frozen numerical parameters, no quality-profile tuning",
        )
        for cohort, features, meta, eligible, s in (
            (
                "four_province",
                full_x.loc[held].reset_index(drop=True),
                full_m.loc[held].reset_index(drop=True),
                valid[held],
                source[held],
            ),
            ("separate_Mersin", mx, mm, mv, mm.original_source_record_key_present.to_numpy()),
        ):
            saved = pd.read_csv(path / (cohort + "_scores.csv"), float_precision="round_trip")
            baseline = pd.read_csv(
                BROAD / scenario / (cohort + "_scores.csv"), float_precision="round_trip"
            )
            pd.testing.assert_frame_equal(saved[KEYS], meta[KEYS], check_exact=True)
            require(
                saved.target.isna().all()
                and saved.accepted_L_membership.isna().all()
                and saved.daily_observation_status.eq("unknown").all(),
                "No scientific target assigned",
            )
            np.testing.assert_array_equal(saved.primary_weather_and_dynamic_15_eligible, eligible)
            restored = np.full(len(meta), np.nan)
            restored[eligible] = model.predict(features.loc[eligible, names]).astype(float)
            np.testing.assert_array_equal(
                restored, saved.new_primary_weather_source_score_not_probability
            )
            pairs = independent.checked_pairs(
                path / (cohort + "_pair_indices.csv"),
                independent.cartesian(meta, s, eligible, [2022]),
            )
            for old_column in (
                "xgboost_source_score_not_probability",
                "frozen_linear_source_score_not_probability",
            ):
                np.testing.assert_array_equal(
                    baseline[old_column], saved["previous_broad_" + old_column]
                )
            subset = metrics.loc[metrics.scenario.eq(scenario) & metrics.cohort.eq(cohort)]
            part = subset.loc[
                subset.variant.isin(["primary_weather_XGBoost", "broad_weather_XGBoost"])
            ].copy()
            part["variant"] = part.variant.map(
                {"primary_weather_XGBoost": "XGBoost", "broad_weather_XGBoost": "frozen_linear"}
            )
            independent.verify_metrics(
                part,
                meta,
                pairs,
                restored,
                baseline.xgboost_source_score_not_probability.to_numpy(),
            )
            independent.verify_metrics(
                subset.loc[subset.variant.eq("frozen_linear")],
                meta,
                pairs,
                restored,
                baseline.frozen_linear_source_score_not_probability.to_numpy(),
            )
            checked.append(
                {
                    "scenario": scenario,
                    "cohort": cohort,
                    "rows": len(meta),
                    "primary_weather_scored_rows": int(eligible.sum()),
                    "common_pairs": len(pairs),
                }
            )
    require(
        len(scenarios) == 9
        and len(list(folder.glob("*/ranker.json"))) == 9
        and all(digest(p) == sha for p, sha in pins.items()),
        "Nine models and unchanged source artifacts",
    )
    out = (
        BASE
        / "primary_weather_rank_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    body = {
        "status": (
            "nine_primary_weather_rankers_fit_support_saved_scores_pairs_and_metrics_verified"
        ),
        "run": folder.relative_to(ROOT).as_posix(),
        "cohort_checks": checked,
        "models_loaded_and_verified": 9,
        "metric_rows_independently_recomputed": len(metrics),
        "new_models_fitted_in_audit": 0,
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
