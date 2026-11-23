"""Separate score reload, Cartesian pair identity and integer-credit audit; no fitting."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
import xgboost as xgb

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
BUNDLE = BASE / "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1"
MERSIN = BASE / "cross_source_calendar_feature_review_v1/20261121T180737Z_c322d93c"
LINEAR = BASE / "temporal_pairwise_run_v1/20261121T174415Z_5a77b21e"
MERSIN_SCORES = BASE / "cross_source_fixed_model_run_v1/20261121T181438Z_bc972c9e"


def cartesian(meta, source, supported, years):
    dates = pd.to_datetime(meta.prediction_timestamp_utc, utc=True, format="ISO8601")
    t = meta.loc[supported & dates.dt.year.isin(years), KEYS].copy()
    t["row"] = t.index
    t["month"] = dates.loc[t.index].dt.strftime("%Y-%m")
    t["s"] = np.asarray(source)[t.index]
    joined = t.loc[t.s].merge(t.loc[~t.s], on=["grid_id", "month"], suffixes=("_a", "_b"))
    return joined[["row_a", "row_b"]].to_numpy(dtype=int)


def checked_pairs(file, expected):
    found = pd.read_csv(file).to_numpy(dtype=int)
    require(len(found) == len(set(map(tuple, found))), "No duplicated evaluation pairs")
    require(
        set(map(tuple, expected)) == set(map(tuple, found)), "Independent Cartesian pair identities"
    )
    return found


def verify_metrics(metrics, metadata, pair_rows, new, old):
    a, b = pair_rows.T
    dates = pd.to_datetime(metadata.prediction_timestamp_utc, utc=True, format="ISO8601")
    delta = np.array([(dates.iloc[i] - dates.iloc[j]).days for i, j in pair_rows])
    for row in metrics.itertuples(index=False):
        name = row.slice
        if name == "all_same_grid_month":
            mask = np.ones(len(a), dtype=bool)
        elif name == "gap_1_to_3_days":
            mask = np.isin(abs(delta), [1, 2, 3])
        elif name == "gap_4_to_30_days":
            mask = (abs(delta) >= 4) & (abs(delta) <= 30)
        elif name == "other_day_before_source_day":
            mask = delta > 0
        elif name == "other_day_after_source_day":
            mask = delta < 0
        elif name.startswith("province_"):
            province = name.removeprefix("province_")
            mask = np.array(
                [
                    province in str(metadata.iloc[i].province_area_intersections).split("|")
                    for i in a
                ]
            )
        else:
            require(name.startswith("cell_"), "Known diagnostic slice")
            mask = metadata.grid_id.to_numpy()[a] == name.removeprefix("cell_")
        values = new if row.variant == "XGBoost" else old
        wins = sum(values[i] > values[j] for i, j in pair_rows[mask])
        ties = sum(values[i] == values[j] for i, j in pair_rows[mask])
        n = int(mask.sum())
        require(
            (row.pairs, row.wins, row.ties) == (n, wins, ties), "Separate integer win/tie counts"
        )
        if n:
            require(
                row.auxiliary_pair_AUC == (wins + ties / 2) / n,
                "Exact independently recomputed credit",
            )
        else:
            require(pd.isna(row.auxiliary_pair_AUC), "Unsupported slice is missing, not zero")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    folder = args.run.resolve()
    require(
        folder.parent == (BASE / "nonlinear_rank_run_v1").resolve(), "Workspace experiment only"
    )
    run = json.loads((folder / "readback.json").read_bytes())
    pins = {ROOT / p: sha for p, sha in run["input_sha256"].items()}
    pins[folder / "readback.json"] = digest(folder / "readback.json")
    pins.update({folder / p: sha for p, sha in run["artifact_sha256"].items()})
    require(all(digest(p) == h for p, h in pins.items()), "Run and current input bytes unchanged")
    require(
        run["new_models_fitted"] == 9
        and not run["final_merge_performed"]
        and not run["fire_risk_validated"]
        and run["true_Y_or_accepted_L_created"] == 0,
        "Exactly bounded source-context experiment",
    )
    launcher = json.loads((folder / "launcher_receipt.json").read_bytes())
    require(
        launcher["status"] == "child_completed"
        and launcher["completed_checkpoints"] == 9
        and launcher["elapsed_seconds"] <= 900,
        "Completed inside hard child deadline",
    )
    pins[folder / "launcher_receipt.json"] = digest(folder / "launcher_receipt.json")
    names = run["features"]
    require(
        len(names) == 15 and not set(names) & {"qid", "grid_id", "calendar_month", "target"},
        "Exactly 15 dynamic predictors",
    )
    features = pd.read_csv(BUNDLE / "features.csv", float_precision="round_trip")
    meta = pd.read_csv(BUNDLE / "inspection_memberships.csv")
    mr = json.loads((MERSIN / "readback.json").read_bytes())
    mx = pd.read_csv(
        MERSIN / mr["snapshot_directory"] / "features.csv", float_precision="round_trip"
    )
    mm = pd.read_csv(MERSIN / mr["snapshot_directory"] / "review_roles.csv")
    complete = np.isfinite(features[names].to_numpy(dtype=float)).all(axis=1)
    mc = np.isfinite(mx[names].to_numpy(dtype=float)).all(axis=1)
    held = meta.prediction_timestamp_utc.str.startswith("2022-").to_numpy()
    metrics = pd.read_csv(folder / "metrics.csv", float_precision="round_trip")
    source_m = mm.original_source_record_key_present.to_numpy()
    mpairs = checked_pairs(folder / "Mersin_pair_indices.csv", cartesian(mm, source_m, mc, [2022]))
    require(len(mpairs) == 2329, "Separate-source support unchanged")
    results = []
    for scenario in sorted(metrics.scenario.unique()):
        path = folder / scenario
        model = xgb.XGBRanker()
        model.load_model(path / "ranker.json")
        require(
            model.get_booster().feature_names == names
            and model.get_booster().num_boosted_rounds() == 100,
            "Saved model feature names and 100 fixed rounds",
        )
        cfg = json.loads((path / "booster_config.json").read_bytes())["learner"]
        require(
            cfg["objective"]["name"] == "rank:pairwise" and cfg["generic_param"]["device"] == "cpu",
            "Pairwise CPU objective",
        )
        tree = cfg["gradient_booster"]["tree_train_param"]
        require(
            int(tree["max_depth"]) == 3
            and float(tree["min_child_weight"]) == 5
            and abs(float(tree["learning_rate"]) - 0.05) < 1e-8
            and float(tree["reg_lambda"]) == 1
            and float(tree["subsample"]) == 1
            and float(tree["colsample_bytree"]) == 1
            and cfg["gradient_booster"]["gbtree_train_param"]["tree_method"] == "hist"
            and cfg["generic_param"]["nthread"] == "4"
            and cfg["generic_param"]["seed"] == "20261123",
            "Frozen tree parameters",
        )
        rank = cfg["objective"]["lambdarank_param"]
        require(
            all(
                rank[k] == v
                for k, v in {
                    "lambdarank_pair_method": "topk",
                    "lambdarank_num_pair_per_sample": "31",
                    "lambdarank_normalization": "1",
                    "lambdarank_score_normalization": "1",
                    "lambdarank_unbiased": "0",
                }.items()
            ),
            "Frozen pair generation and normalization",
        )
        source = meta["S_candidate_context_" + scenario].to_numpy()
        expected_fit = cartesian(meta, source, complete, [2018, 2019, 2020, 2021])
        layout = pd.read_csv(path / "fit_layout.csv")
        expected_rows = set(expected_fit.ravel())
        require(
            set(layout.calendar_row) == expected_rows and len(layout) == len(expected_rows),
            "Independent informative fit row set",
        )
        pd.testing.assert_frame_equal(
            layout[KEYS],
            meta.loc[layout.calendar_row, KEYS].reset_index(drop=True),
            check_exact=True,
        )
        require(
            np.array_equal(layout.relevance_source_context_not_Y, source[layout.calendar_row]),
            "Relevance is unchanged source proposal, not a true fire label",
        )
        require(layout.qid.is_monotonic_increasing, "Sorted qid")
        for _, group in layout.groupby("qid"):
            require(
                group.grid_id.nunique() == 1
                and group.prediction_timestamp_utc.str[:7].nunique() == 1
                and group.relevance_source_context_not_Y.nunique() == 2,
                "Each query is one mixed cell-month",
            )
        pair_rows = checked_pairs(
            path / "assessment_pair_indices.csv", cartesian(meta, source, complete, [2022])
        )
        require(
            set(map(tuple, pair_rows))
            == set(
                map(
                    tuple, pd.read_csv(LINEAR / scenario / "assessment_pair_indices.csv").to_numpy()
                )
            ),
            "Identical old linear assessment pairs",
        )
        for cohort, data, metadata, support, rowmask, pairs, reference, reference_column in (
            (
                "four_province",
                features,
                meta,
                held & complete,
                held,
                pair_rows,
                LINEAR / scenario / "assessment_scores.csv",
                "temporal_pairwise_linear_score_not_probability",
            ),
            (
                "separate_Mersin",
                mx,
                mm,
                mc,
                np.ones(len(mm), dtype=bool),
                mpairs,
                MERSIN_SCORES / (scenario + "_source_calendar_scores.csv"),
                "fixed_linear_source_score_not_fire_probability",
            ),
        ):
            scores = pd.read_csv(path / (cohort + "_scores.csv"), float_precision="round_trip")
            old = pd.read_csv(reference, float_precision="round_trip")
            pd.testing.assert_frame_equal(
                scores[KEYS], metadata.loc[rowmask, KEYS].reset_index(drop=True), check_exact=True
            )
            require(
                scores.target.isna().all()
                and scores.accepted_L_membership.isna().all()
                and scores.daily_observation_status.eq("unknown").all(),
                "No scientific target assigned",
            )
            restored = np.full(len(metadata), np.nan)
            restored[support] = model.predict(data.loc[support, names]).astype(float)
            np.testing.assert_array_equal(
                restored[rowmask], scores.xgboost_source_score_not_probability
            )
            np.testing.assert_array_equal(
                old[reference_column], scores.frozen_linear_source_score_not_probability
            )
            baseline = np.full(len(metadata), np.nan)
            baseline[rowmask] = old[reference_column]
            verify_metrics(
                metrics.loc[metrics.scenario.eq(scenario) & metrics.cohort.eq(cohort)],
                metadata,
                pairs,
                restored,
                baseline,
            )
        results.append(
            {
                "scenario": scenario,
                "fit_rows_independently_confirmed": len(expected_rows),
                "four_province_identical_pairs": len(pair_rows),
                "Mersin_identical_pairs": len(mpairs),
            }
        )
    require(
        len(results) == 9 and len(list(folder.glob("*/ranker.json"))) == 9,
        "Exactly nine saved models",
    )
    require(all(digest(p) == h for p, h in pins.items()), "Immutable bytes after no-fit audit")
    out = (
        BASE
        / "nonlinear_rank_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    report = {
        "status": "nine_saved_rankers_pairs_scores_and_metrics_independently_confirmed",
        "run_directory": folder.relative_to(ROOT).as_posix(),
        "scenarios": results,
        "metric_rows_independently_recomputed": len(metrics),
        "model_fits_during_audit": 0,
        "true_fire_validation": False,
        "final_merge_performed": False,
        "producer_sha256": digest(Path(__file__)),
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
    }
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print("independent metric rows", len(metrics), flush=True)


if __name__ == "__main__":
    main()
