"""Read fixed feature ablations and measure spatial/temporal comparison support; never refit."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import joblib
import matplotlib
import numpy as np
import pandas as pd
from audit_satellite_pu_ranking_run import SCORE, S, comparison_masks, pair_credit

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import landscape, weather_policy
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv
from wildfire_risk_prediction.target_admission import specification

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "satellite_PU_ablation_run_v1/20261120T014426Z_44c25642/readback.json"
RUN_SHA = "fa9321e6268ffba478c6250d6cc32b0d5516ce3b872b9a8271920edb9d1d3324"
PARENT = BASE / "satellite_PU_ranking_run_v1/20261120T012805Z_04789b23/readback.json"
PARENT_SHA = "971b85def11809d0d48f4a3618233588e6a7022e7ddea5861fb94054cbcb84a1"
CONTEXT = BASE / "satellite_PU_ranking_audit_v1/20261120T013224Z_b8a45358"
CONTEXT_SHA = "19f67bcfecf918804a7365ee1c7d7bfc53da3e9956a87004ac275aa29f2f8f47"
FEATURES = BASE / "satellite_PU_feature_review_v1/20261120T010533Z_6d61c80e/features.csv"
ROLES = BASE / "satellite_PU_partition_v1/20261120T010148Z_74c8eee5/proposed_key_roles.csv"
FIELDS = {
    "weather_only": weather_policy.MODEL_FEATURES,
    "static_cover_terrain_only": landscape.COVER_FEATURES + landscape.TERRAIN_FEATURES,
}


def time_masks(frame):
    """No row removal or matched resampling; comparisons use the existing fixed scores."""
    result = comparison_masks(frame)
    source, unlabelled = frame.loc[frame[S].eq(1)], frame.loc[frame[S].eq(0)]
    same_grid = source.grid_id.to_numpy()[:, None] == unlabelled.grid_id.to_numpy()[None, :]
    same_month = result["same_month"]
    result["same_month_shared_province"] = same_month & result["shared_province_area"]
    result["same_grid"] = same_grid
    result["same_month_same_grid"] = same_month & same_grid
    return result


def static_score_check(frame):
    values = frame.groupby("grid_id")[SCORE].nunique()
    join.require(values.eq(1).all(), "Static model must give one score per unchanged grid X")
    return {
        "distinct_grids": len(values),
        "grids_with_multiple_key_days": int(frame.groupby("grid_id").size().gt(1).sum()),
        "grids_with_variable_static_scores": 0,
    }


def main():
    pins = {RUN: RUN_SHA, PARENT: PARENT_SHA, CONTEXT / "readback.json": CONTEXT_SHA}
    join.require(all(digest(p) == h for p, h in pins.items()), "Frozen auxiliary runs and context")
    run, parent, context = [
        json.loads(p.read_bytes()) for p in (RUN, PARENT, CONTEXT / "readback.json")
    ]
    for p, h in run["input_sha256"].items():
        pins[ROOT / p] = h
    for report, folder in ((run, RUN.parent), (parent, PARENT.parent), (context, CONTEXT)):
        pins.update({folder / p: h for p, h in report["artifact_sha256"].items()})
    helper = ROOT / "scripts/quality/audit_satellite_pu_ranking_run.py"
    pins[helper] = digest(helper)
    join.require(
        all(digest(p) == h for p, h in pins.items()), "All current models, scores, X and context"
    )
    features, roles = parse_csv(FEATURES.read_bytes()), parse_csv(ROLES.read_bytes())
    ctx = parse_csv((CONTEXT / "assessment_context.csv").read_bytes())
    join.require(
        roles.target.isna().all() and roles.accepted_L_membership.isna().all(),
        "Real Y and accepted L remain blank",
    )
    x_index = features.set_index(join.KEYS)
    comparisons, model_checks, static_checks, snapshots = [], [], [], []
    for metric in run["metrics"]:
        scenario, variant = metric["scenario"], metric["variant"]
        source = roles.proposed_scenarios_json.map(lambda value, s=scenario: s in json.loads(value))
        fit_roles = roles.loc[
            roles.proposed_partition.eq("proposed_fit_2018_2021")
            & (source | roles.original_U_sample_present)
        ]
        held_roles = roles.loc[
            roles.proposed_partition.eq("proposed_assessment_2022")
            & (source | roles.original_U_sample_present)
        ]
        fit_keys = list(fit_roles[join.KEYS].itertuples(index=False, name=None))
        held_keys = list(held_roles[join.KEYS].itertuples(index=False, name=None))
        train, held = x_index.loc[fit_keys], x_index.loc[held_keys]
        pred = parse_csv((RUN.parent / scenario / (variant + "_assessment.csv")).read_bytes())
        pd.testing.assert_frame_equal(
            pred[join.KEYS], held.reset_index()[join.KEYS], check_exact=True
        )
        np.testing.assert_array_equal(pred[S], source.loc[held_roles.index].to_numpy(int))
        join.require(
            pred.true_Y.isna().all() and pred.daily_observation_status.eq("unknown").all(),
            "Unchanged unknown targets",
        )
        saved = joblib.load(RUN.parent / scenario / (variant + ".joblib"))
        model, retained = saved["model"], saved["retained_features"]
        expected = [name for name in FIELDS[variant] if train[name].notna().any()]
        join.require(retained == expected, "Only the declared feature group enters the model")
        state = joblib.hash(model)
        imputer = model.named_steps["impute"]
        medians = np.nanmedian(train[retained].to_numpy(), axis=0)
        np.testing.assert_array_equal(imputer.statistics_, medians)
        np.testing.assert_array_equal(
            imputer.indicator_.features_, np.flatnonzero(train[retained].isna().any().to_numpy())
        )
        np.testing.assert_array_equal(model.predict_proba(held[retained])[:, 1], pred[SCORE])
        join.require(joblib.hash(model) == state, "Inference did not update model state")
        join.require(model.named_steps["model"].n_jobs == 1, "Ordered fixed-model inference")
        a, b = pred.loc[pred[S].eq(1), SCORE].tolist(), pred.loc[pred[S].eq(0), SCORE].tolist()
        scalar = sum(2 if x > y else 1 if x == y else 0 for x in a for y in b) / (
            2 * len(a) * len(b)
        )
        join.require(
            abs(scalar - metric["auxiliary_S_ROC_AUC"]) < 1e-14, "Independent scalar pair AUC"
        )
        snapshots.append(
            {
                "scenario": scenario,
                "variant": variant,
                "fit_medians": dict(zip(retained, medians.tolist(), strict=True)),
                "fit_missing_indices": imputer.indicator_.features_.tolist(),
            }
        )
        model_checks.append(
            {
                "scenario": scenario,
                "variant": variant,
                "prediction_and_fit_medians_exact": True,
                "scalar_AUC": scalar,
            }
        )
        original_context = ctx.loc[ctx.scenario.eq(scenario)].drop(columns=["scenario", SCORE])
        frame = pred.merge(
            original_context, on=join.KEYS + [S], validate="one_to_one", indicator=True
        )
        join.require(
            len(frame) == len(pred) and frame._merge.eq("both").all(),
            "Identical fixed assessment context",
        )
        for scheme, mask in time_masks(frame).items():
            comparisons.append(
                {
                    "scenario": scenario,
                    "variant": variant,
                    "scheme": scheme,
                    "source_keys": len(a),
                    "U_keys": len(b),
                    **pair_credit(a, b, mask),
                }
            )
        if variant == "static_cover_terrain_only":
            static_checks.append({"scenario": scenario, **static_score_check(frame)})
    # Reuse the earlier full RF: no full-model retraining or score normalization.
    for scenario, frame in ctx.groupby("scenario", sort=True):
        a, b = frame.loc[frame[S].eq(1), SCORE], frame.loc[frame[S].eq(0), SCORE]
        for scheme, mask in time_masks(frame).items():
            comparisons.append(
                {
                    "scenario": scenario,
                    "variant": "full_27_features",
                    "scheme": scheme,
                    "source_keys": len(a),
                    "U_keys": len(b),
                    **pair_credit(a, b, mask),
                }
            )
    join.require(
        len(model_checks) == 18 and len(static_checks) == 9,
        "All authorized fixed ablations verified",
    )
    out = (
        BASE
        / "satellite_PU_ablation_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    table = pd.DataFrame(comparisons)
    p = out / "fixed_score_comparisons.csv"
    table.to_csv(p, index=False)
    pd.testing.assert_frame_equal(
        table, parse_csv(p.read_bytes()), check_dtype=False, check_exact=True
    )
    render(table, out)
    report = {
        "status": "18_ablations_reloaded_and_temporal_support_described_not_fire_validation",
        "run_readback_sha256": RUN_SHA,
        "models_and_fit_medians_rechecked": 18,
        "model_checks": model_checks,
        "fit_preprocessing_snapshots": snapshots,
        "static_model_grid_invariance_checks": static_checks,
        "diagnostics": comparisons,
        "full_models_refitted": 0,
        "additional_models_fitted": 0,
        "new_Y_or_accepted_L_created": 0,
        "true_fire_AP_or_AUC_computed": False,
        "causal_feature_contribution_estimated": False,
        "new_sampling_or_U_weights_changed": False,
        "final_merge_performed": False,
        "gate": specification(),
        "producer_sha256": digest(Path(__file__)),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {
            name: digest(out / name)
            for name in ("fixed_score_comparisons.csv", "feature_group_comparison.png")
        },
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "Consumed snapshots unchanged")
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)


def render(frame, out):
    scenarios = sorted(frame.scenario.unique())
    variants = (
        ("weather_only", "Yalnız meteoroloji"),
        ("static_cover_terrain_only", "Yalnız örtü/arazi"),
        ("full_27_features", "Tam RF: önceki kayıt"),
    )
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.7))
    for ax, scheme, title in zip(
        axes,
        ("all_pairs", "same_month_shared_province"),
        ("Bütün aday–U çiftleri", "Aynı ay ve ortak il alanı"),
        strict=True,
    ):
        for variant, label in variants:
            block = frame.loc[frame.variant.eq(variant) & frame.scheme.eq(scheme)].set_index(
                "scenario"
            )
            ax.plot(range(9), block.loc[scenarios, "auxiliary_S_pair_AUC"], marker="o", label=label)
        ax.set(
            xticks=range(9),
            xticklabels=[
                s.replace("d", "").replace("m_t", "m / ").replace("h", "saat") for s in scenarios
            ],
            ylim=(0.4, 0.9),
            title=title,
            ylabel="Yardımcı aday üyeliği çift AUC",
        )
        ax.axhline(0.5, color="gray", linestyle="--", linewidth=1)
        ax.tick_params(axis="x", rotation=55, labelsize=8)
        ax.legend(fontsize=8)
    fig.suptitle(
        "2022 tanısı • Gerçek yangın başarımı veya nedensel özellik katkısı değil", fontsize=13
    )
    fig.text(
        0.5,
        0.015,
        "Aynı kayıtlar ve RF ayarları; U gerçek negatif değildir. "
        "Dar karşılaştırmada destek ayrıca raporlanır.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(out / "feature_group_comparison.png", dpi=150, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
