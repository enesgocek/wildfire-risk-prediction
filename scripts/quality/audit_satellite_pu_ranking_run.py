"""Read fixed satellite S models and describe comparability; no fitting or label admission."""

import json
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import joblib
import matplotlib
import numpy as np
import pandas as pd
from prepare_full_u_feature_review import GRID, PROVINCES, province_support

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import landscape, weather_policy
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv
from wildfire_risk_prediction.target_admission import specification

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "satellite_PU_ranking_run_v1/20261120T012805Z_04789b23/readback.json"
RUN_SHA = "971b85def11809d0d48f4a3618233588e6a7022e7ddea5861fb94054cbcb84a1"
FEATURES = BASE / "satellite_PU_feature_review_v1/20261120T010533Z_6d61c80e/features.csv"
ROLES = BASE / "satellite_PU_partition_v1/20261120T010148Z_74c8eee5/proposed_key_roles.csv"
NAMES = ("logistic_regression", "random_forest", "missingness_control")
S = "observed_proposal_S"
SCORE = "auxiliary_source_score_not_fire_probability"


def pair_credit(source, unlabelled, mask=None):
    """Pair-weighted source/U rank credit, including ties; U is not a true negative."""
    a, b = np.asarray(source), np.asarray(unlabelled)
    join.require(np.isfinite(a).all() and np.isfinite(b).all(), "Finite fixed scores")
    delta = a[:, None] - b[None, :]
    mask = np.ones(delta.shape, dtype=bool) if mask is None else np.asarray(mask)
    join.require(mask.dtype == bool and mask.shape == delta.shape, "Aligned comparison mask")
    count = int(mask.sum())
    wins, ties = int(((delta > 0) & mask).sum()), int(((delta == 0) & mask).sum())
    return {
        "pairs": count,
        "wins": wins,
        "ties": ties,
        "doubled_credit": 2 * wins + ties,
        "auxiliary_S_pair_AUC": (2 * wins + ties) / (2 * count) if count else None,
        "source_keys_with_comparator": int(mask.any(axis=1).sum()),
        "U_keys_with_comparator": int(mask.any(axis=0).sum()),
    }


def family_flags(frame):
    families = {
        "weather": weather_policy.MODEL_FEATURES,
        "cover": landscape.COVER_FEATURES,
        "terrain": landscape.TERRAIN_FEATURES,
        **{
            f"vegetation{w}": [f"vegetation_{w}d_{f}" for f in join.VEGETATION_FEATURES]
            for w in (30, 60)
        },
    }
    return pd.DataFrame(
        {k: frame[v].isna().any(axis=1).astype(float) for k, v in families.items()},
        index=frame.index,
    )


def comparison_masks(frame):
    source, unlabelled = frame.loc[frame[S].eq(1)], frame.loc[frame[S].eq(0)]
    same_month = source.month.to_numpy()[:, None] == unlabelled.month.to_numpy()[None, :]
    same_cover = source.woody_half.to_numpy()[:, None] == unlabelled.woody_half.to_numpy()[None, :]
    same_province = np.array(
        [
            [bool(set(a.split("|")) & set(b.split("|"))) for b in unlabelled.province_support]
            for a in source.province_support
        ],
        dtype=bool,
    )
    complete = (
        source.complete_27_features.to_numpy()[:, None]
        & unlabelled.complete_27_features.to_numpy()[None, :]
    )
    return {
        "all_pairs": np.ones(same_month.shape, dtype=bool),
        "same_month": same_month,
        "same_2017_woody_half": same_cover,
        "shared_province_area": same_province,
        "same_month_woody_half_shared_province": same_month & same_cover & same_province,
        "both_complete_27_features": complete,
    }


def top_with_ties(scores, minimum_count=40):
    join.require(
        type(minimum_count) is int
        and 0 < minimum_count <= len(scores)
        and np.isfinite(scores).all(),
        "Bounded finite ranking",
    )
    threshold = scores.sort_values(ascending=False).iloc[minimum_count - 1]
    return set(scores.index[scores >= threshold])


def main():
    join.require(digest(RUN) == RUN_SHA, "Exact completed run")
    run = json.loads(RUN.read_bytes())
    join.require(
        run["models_fitted"] == 27 and run["true_Y_and_accepted_L_created"] == 0,
        "Authorized auxiliary experiment only",
    )
    pins = {RUN: RUN_SHA, **{ROOT / p: h for p, h in run["input_sha256"].items()}}
    pins.update({RUN.parent / p: h for p, h in run["artifact_sha256"].items()})
    pins[GRID] = "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9"
    pins[PROVINCES] = "ffb43d77b0e7cba1dbe3c605454e468eb46d4eaefdcc5d2ebd6612ea9e75d2fb"
    join.require(
        all(digest(p) == h for p, h in pins.items()),
        "Unchanged run, models, features and boundaries",
    )
    features, roles = parse_csv(FEATURES.read_bytes()), parse_csv(ROLES.read_bytes())
    join.require(
        roles.target.isna().all() and roles.accepted_L_membership.isna().all(), "No real labels"
    )
    grid = gpd.read_file(GRID).to_crs(6933)
    grid = grid.loc[grid.grid_id.isin(features.grid_id)]
    support = province_support(grid, gpd.read_file(PROVINCES).to_crs(6933))
    province = support.groupby("grid_id").province.agg(lambda x: "|".join(sorted(x)))
    x_index = features.set_index(join.KEYS)
    summaries, medians, contexts, province_counts, u_scores = [], [], [], [], {}
    for metric in run["metrics"]:
        scenario, name = metric["scenario"], metric["model"]
        source = roles.proposed_scenarios_json.map(lambda x, s=scenario: s in json.loads(x))
        chosen = roles.loc[roles.original_U_sample_present | source]
        expected = {}
        for phase in ("proposed_fit_2018_2021", "proposed_assessment_2022"):
            subset = chosen.loc[chosen.proposed_partition.eq(phase)]
            keys = list(subset[join.KEYS].itertuples(index=False, name=None))
            expected[phase] = (
                x_index.loc[keys].reset_index(),
                source.loc[subset.index].to_numpy(int),
            )
        train, s_fit = expected["proposed_fit_2018_2021"]
        held, s_held = expected["proposed_assessment_2022"]
        pred = parse_csv((RUN.parent / scenario / f"{name}_assessment.csv").read_bytes())
        pd.testing.assert_frame_equal(pred[join.KEYS], held[join.KEYS], check_exact=True)
        np.testing.assert_array_equal(pred[S], s_held)
        join.require(
            pred.true_Y.isna().all() and pred.daily_observation_status.eq("unknown").all(),
            "Prediction output preserves unknown Y",
        )
        join.require(pred[SCORE].between(0, 1).all(), "Finite bounded auxiliary scores")
        saved = joblib.load(RUN.parent / scenario / f"{name}.joblib")
        model, retained = saved["model"], saved["retained_features"]
        state = joblib.hash(model)
        if name == "missingness_control":
            model_train, model_held = family_flags(train), family_flags(held)
            join.require(retained == model_train.columns.tolist(), "Only family missing flags")
        else:
            expected_retained = [f for f in join.feature_names() if train[f].notna().any()]
            join.require(retained == expected_retained, "Fit-only retained columns")
            model_train, model_held = train[retained], held[retained]
            actual = model.named_steps["impute"]
            values = np.nanmedian(model_train.to_numpy(), axis=0)
            np.testing.assert_array_equal(actual.statistics_, values)
            np.testing.assert_array_equal(
                actual.indicator_.features_, np.flatnonzero(model_train.isna().any().to_numpy())
            )
            medians.append(
                {
                    "scenario": scenario,
                    "model": name,
                    "fit_medians": dict(zip(retained, values.tolist(), strict=True)),
                }
            )
        if "scale" in model.named_steps:
            transformed = (
                model.named_steps["impute"].transform(model_train)
                if "impute" in model.named_steps
                else model_train.to_numpy()
            )
            scale = model.named_steps["scale"]
            np.testing.assert_allclose(
                scale.mean_, np.asarray(transformed).mean(axis=0), rtol=1e-13, atol=1e-12
            )
            np.testing.assert_allclose(
                scale.var_, np.asarray(transformed).var(axis=0), rtol=1e-12, atol=1e-12
            )
        np.testing.assert_array_equal(model.predict_proba(model_held)[:, 1], pred[SCORE])
        join.require(joblib.hash(model) == state, "Readback prediction cannot update fitted state")
        # Independent scalar pair enumeration, separate from the vectorized diagnostic.
        positive = pred.loc[pred[S].eq(1), SCORE].tolist()
        unlabelled = pred.loc[pred[S].eq(0), SCORE].tolist()
        doubled = sum(2 if a > b else 1 if a == b else 0 for a in positive for b in unlabelled)
        scalar_auc = doubled / (2 * len(positive) * len(unlabelled))
        join.require(
            abs(scalar_auc - metric["assessment_proposal_membership_ROC_AUC"]) < 1e-14,
            "Independent tie-correct AUC",
        )
        frame = pred.merge(features, on=join.KEYS, validate="one_to_one")
        frame["month"] = [datetime.fromisoformat(t).month for t in frame.prediction_timestamp_utc]
        frame["woody_half"] = (frame.forest_fraction + frame.shrub_fraction).ge(0.5)
        frame["complete_27_features"] = frame[join.feature_names()].notna().all(axis=1)
        frame["province_support"] = frame.grid_id.map(province)
        join.require(frame.province_support.notna().all(), "All grid areas mapped")
        masks = comparison_masks(frame)
        for scheme, mask in masks.items():
            summaries.append(
                {
                    "scenario": scenario,
                    "model": name,
                    "scheme": scheme,
                    "source_keys": len(positive),
                    "U_keys": len(unlabelled),
                    **pair_credit(positive, unlabelled, mask),
                }
            )
        if name == "random_forest":
            contexts.append(
                frame[
                    join.KEYS
                    + [S, SCORE, "month", "woody_half", "complete_27_features", "province_support"]
                ].assign(scenario=scenario)
            )
            u = frame.loc[frame[S].eq(0)].set_index(join.KEYS)[SCORE].sort_index()
            join.require(len(u) == 400, "Same four hundred U in every setting")
            u_scores[scenario] = u
            for prov in sorted(support.province.unique()):
                block = frame.loc[frame.province_support.map(lambda x, p=prov: p in x.split("|"))]
                a, b = block.loc[block[S].eq(1), SCORE], block.loc[block[S].eq(0), SCORE]
                province_counts.append(
                    {
                        "scenario": scenario,
                        "province": prov,
                        "source_keys": len(a),
                        "U_keys": len(b),
                        **pair_credit(a, b),
                    }
                )
    stability = []
    for first, second in combinations(sorted(u_scores), 2):
        a, b = u_scores[first], u_scores[second]
        join.require(a.index.equals(b.index), "Identical U ranking universe")
        top_a, top_b = top_with_ties(a), top_with_ties(b)
        stability.append(
            {
                "first": first,
                "second": second,
                "same_400_U_score_spearman": float(
                    a.rank(method="average").corr(b.rank(method="average"))
                ),
                "top_minimum_40_with_all_boundary_ties_first": len(top_a),
                "top_minimum_40_with_all_boundary_ties_second": len(top_b),
                "top_intersection_keys": len(top_a & top_b),
                "top_union_keys": len(top_a | top_b),
                "top_Jaccard": len(top_a & top_b) / len(top_a | top_b),
            }
        )
    out = (
        BASE
        / "satellite_PU_ranking_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    artifacts = {}
    tables = {
        "comparison_pairs.csv": pd.DataFrame(summaries),
        "assessment_context.csv": pd.concat(contexts, ignore_index=True),
        "province_diagnostics.csv": pd.DataFrame(province_counts),
        "same_U_rank_stability.csv": pd.DataFrame(stability),
        "grid_province_support.csv": support,
    }
    for name, table in tables.items():
        p = out / name
        table.to_csv(p, index=False)
        pd.testing.assert_frame_equal(
            table, parse_csv(p.read_bytes()), check_dtype=False, check_exact=True
        )
        artifacts[name] = digest(p)
    render(pd.DataFrame(summaries), out)
    artifacts["auxiliary_diagnostics.png"] = digest(out / "auxiliary_diagnostics.png")
    report = {
        "status": "fixed_27_models_readback_and_comparability_described_not_fire_validation",
        "run_readback_sha256": RUN_SHA,
        "models_reloaded_and_predictions_exact": 27,
        "independent_scalar_pair_AUC_checks": 27,
        "fit_only_preprocessing_checks": 27,
        "fit_only_numeric_median_snapshots": medians,
        "diagnostics": summaries,
        "RF_province_diagnostics_memberships_can_overlap": province_counts,
        "same_U_Random_Forest_stability_pairs": stability,
        "ranking_stability_is_target_validity": False,
        "within_comparison_is_causal_adjustment": False,
        "model_refitted": False,
        "new_Y_or_accepted_L_created": 0,
        "class_conditional_assumptions_verified": False,
        "true_fire_AP_or_AUC_computed": False,
        "risk_probabilities_or_colors_created": False,
        "final_merge_performed": False,
        "gate": specification(),
        "producer_sha256": digest(Path(__file__)),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": artifacts,
    }
    join.require(
        all(digest(p) == h for p, h in pins.items()), "Consumed inputs unchanged after readback"
    )
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


def render(frame, out):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8))
    scenarios = sorted(frame.scenario.unique())
    for model, label in zip(NAMES, ("Lojistik", "Random Forest", "Yalnız eksiklik"), strict=True):
        block = frame.loc[frame.model.eq(model) & frame.scheme.eq("all_pairs")].set_index(
            "scenario"
        )
        axes[0].plot(
            range(9), block.loc[scenarios, "auxiliary_S_pair_AUC"], marker="o", label=label
        )
    for scheme, label in (
        ("all_pairs", "Tüm çiftler"),
        ("same_month", "Aynı ay"),
        ("same_month_woody_half_shared_province", "Ay + örtü + ortak il alanı"),
    ):
        block = frame.loc[frame.model.eq("random_forest") & frame.scheme.eq(scheme)].set_index(
            "scenario"
        )
        axes[1].plot(
            range(9), block.loc[scenarios, "auxiliary_S_pair_AUC"], marker="o", label=label
        )
    labels = [s.replace("d", "").replace("m_t", "m / ").replace("h", "saat") for s in scenarios]
    for ax in axes:
        ax.axhline(0.5, color="gray", linewidth=1, linestyle="--")
        ax.set(
            xticks=range(9),
            xticklabels=labels,
            ylim=(0.4, 0.9),
            ylabel="Yardımcı aday üyeliği için çift AUC",
        )
        ax.tick_params(axis="x", rotation=55, labelsize=8)
        ax.legend(fontsize=8)
    axes[0].set_title("2022 tanısı • sabit üç model / dokuz ayar")
    axes[1].set_title("Sabit RF skorları • karşılaştırma desteği değişiyor")
    fig.suptitle("Gerçek yangın başarımı veya risk olasılığı değildir", fontsize=13)
    fig.text(
        0.5,
        0.015,
        "S=1: olası uydu adayı; S=0: belirsiz U. Bu tanıda yeniden fit yok; Y boş. "
        "İl alanları kesişebilir.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(out / "auxiliary_diagnostics.png", dpi=150, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
