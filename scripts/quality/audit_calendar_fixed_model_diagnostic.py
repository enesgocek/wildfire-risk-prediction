"""Independently read fixed calendar scores, scalar rank credits and provincial support."""

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import joblib
import matplotlib
import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require
from wildfire_risk_prediction.feature_partition import parse_csv

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "source_calendar_fixed_model_run_v1/20261121T171148Z_91ab9c78"
RUN_SHA = "ff51e4790f92eeca51b1db107c38c876a5a2b6ea34d54d4a3451d32754e28f4f"
PLAN = BASE / "source_calendar_fixed_model_plan_v1/20261121T165748Z_848be12d/readback.json"
REVIEW = BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896"
PROV_CONTEXT = BASE / "satellite_PU_ranking_audit_v1/20261120T013224Z_b8a45358"
PROV_SHA = "19f67bcfecf918804a7365ee1c7d7bfc53da3e9956a87004ac275aa29f2f8f47"
INDICATOR = "existing_scenario_proposal_context"
VARIANTS = ("full_27_features", "weather_only", "static_cover_terrain_only")


def scalar_credit(frame, score, *, within, quality):
    allowed = {"all", "complete_weather_both", "complete_27_features_both"}
    require(quality in allowed, "Declared quality profile")
    retained = frame
    if quality != "all":
        field = "weather_complete" if quality == "complete_weather_both" else "complete_27_features"
        retained = frame.loc[frame[field]]
    groups = defaultdict(list)
    for row in retained.to_dict("records"):
        group = (row["grid_id"], row["prediction_timestamp_utc"][:7]) if within else ("all", "all")
        groups[group].append(row)
    pairs, doubled = 0, 0
    source_keys, other_keys = set(), set()
    for group in groups.values():
        source = [r for r in group if r[INDICATOR]]
        other = [r for r in group if not r[INDICATOR]]
        if not source or not other:
            continue
        pairs += len(source) * len(other)
        source_keys.update(tuple(a[k] for k in KEYS) for a in source)
        other_keys.update(tuple(b[k] for k in KEYS) for b in other)
        if within:
            doubled += sum(
                2 if a[score] > b[score] else 1 if a[score] == b[score] else 0
                for a in source
                for b in other
            )
        else:
            # Independent rank-sum identity avoids enumerating millions of broad pairs.
            ranks = pd.Series([r[score] for r in group]).rank(method="average")
            total = sum(ranks.iloc[i] for i, row in enumerate(group) if row[INDICATOR])
            doubled += int(2 * total - len(source) * (len(source) + 1))
    return {
        "pairs": pairs,
        "doubled_credit": doubled,
        "auxiliary_S_pair_AUC": doubled / (2 * pairs) if pairs else None,
        "source_keys_with_comparator": len(source_keys),
        "U_keys_with_comparator": len(other_keys),
    }


def main():
    require(
        digest(RUN / "readback.json") == RUN_SHA
        and digest(PROV_CONTEXT / "readback.json") == PROV_SHA,
        "Exact completed diagnostics",
    )
    report = json.loads((RUN / "readback.json").read_bytes())
    plan = json.loads(PLAN.read_bytes())
    pins = {RUN / "readback.json": RUN_SHA, PROV_CONTEXT / "readback.json": PROV_SHA}
    pins.update({ROOT / p: h for p, h in report["input_sha256"].items()})
    pins.update({RUN / p: h for p, h in report["artifact_sha256"].items()})
    context_report = json.loads((PROV_CONTEXT / "readback.json").read_bytes())
    p = PROV_CONTEXT / "assessment_context.csv"
    pins[p] = context_report["artifact_sha256"][p.name]
    require(
        all(digest(p) == h for p, h in pins.items()), "Current X, fixed models, context and scores"
    )
    review = json.loads((REVIEW / "readback.json").read_bytes())
    snapshot = REVIEW / review["snapshot_directory"]
    features = parse_csv((snapshot / "features.csv").read_bytes()).set_index(KEYS)
    roles = parse_csv((snapshot / "review_roles.csv").read_bytes())
    expected = (
        roles.loc[roles.review_temporal_role.eq("proposed_assessment_2022")]
        .sort_values(KEYS)[KEYS]
        .reset_index(drop=True)
    )
    context = parse_csv(p.read_bytes())
    mapping = context[["grid_id", "province_support"]].drop_duplicates()
    require(mapping.grid_id.is_unique, "Consistent area-support signature by grid")
    province = mapping.set_index("grid_id").province_support.to_dict()
    frames, provincial, checks = {}, [], []
    metric_index = {
        (m["scenario"], m["variant"], m["scheme"], m["quality_profile"]): m
        for m in report["metrics"]
    }
    for scenario in sorted(plan["scenario_counts"]):
        frame = parse_csv((RUN / (scenario + "_calendar_scores.csv")).read_bytes())
        pd.testing.assert_frame_equal(frame[KEYS], expected, check_exact=True)
        require(
            len(frame) == 6573
            and frame.true_Y.isna().all()
            and frame.accepted_L_membership.isna().all()
            and frame.daily_observation_status.eq("unknown").all(),
            "Same calendar keys and unknown real labels",
        )
        frame["province_support"] = frame.grid_id.map(province)
        require(
            frame.province_support.notna().all(),
            "All 2022 grid areas have frozen provincial support",
        )
        x = features.loc[list(frame[KEYS].itertuples(index=False, name=None))]
        for spec in [m for m in plan["fixed_models"] if m["scenario"] == scenario]:
            saved = joblib.load(ROOT / spec["path"])
            model, names = saved["model"], saved["retained_features"]
            state = joblib.hash(model)
            score_name = spec["variant"] + "_auxiliary_source_score"
            np.testing.assert_array_equal(model.predict_proba(x[names])[:, 1], frame[score_name])
            require(joblib.hash(model) == state, "Separate inference cannot update a fitted model")
            for within in (False, True):
                scheme = "within_grid_year_month" if within else "all_pairs"
                for quality in ("all", "complete_weather_both", "complete_27_features_both"):
                    result = scalar_credit(frame, score_name, within=within, quality=quality)
                    recorded = metric_index[(scenario, spec["variant"], scheme, quality)]
                    for field in (
                        "pairs",
                        "doubled_credit",
                        "source_keys_with_comparator",
                        "U_keys_with_comparator",
                    ):
                        require(
                            result[field] == recorded[field],
                            "Independent scalar pair count/credit/support",
                        )
                    require(
                        result["auxiliary_S_pair_AUC"] == recorded["auxiliary_S_pair_AUC"],
                        "Independent pair AUC",
                    )
                    checks.append(
                        {
                            "scenario": scenario,
                            "variant": spec["variant"],
                            "scheme": scheme,
                            "quality_profile": quality,
                            "passed": True,
                        }
                    )
            for name in ("Antalya", "Izmir", "Mersin", "Mugla"):
                block = frame.loc[
                    frame.province_support.map(lambda value, prov=name: prov in value.split("|"))
                ]
                provincial.append(
                    {
                        "scenario": scenario,
                        "variant": spec["variant"],
                        "province": name,
                        **scalar_credit(
                            block, score_name, within=True, quality="complete_weather_both"
                        ),
                    }
                )
        frames[scenario] = frame
    require(len(checks) == 162, "All declared fixed-score metrics verified independently")
    out = (
        BASE
        / "source_calendar_fixed_model_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    pd.DataFrame(provincial).to_csv(out / "province_within_calendar_support.csv", index=False)
    render(pd.DataFrame(report["metrics"]), out)
    result = {
        "status": "fixed_calendar_predictions_and_scalar_metrics_rechecked_not_fire_validation",
        "parent_readback_sha256": RUN_SHA,
        "models_reloaded_and_predictions_exact": 27,
        "independent_metric_checks": len(checks),
        "independent_methods": ["average_rank_sum_for_all_pairs", "scalar_within_grid_year_month"],
        "province_within_grid_month_weather_complete": provincial,
        "provincial_area_memberships_can_overlap": True,
        "new_models_fitted": 0,
        "true_Y_or_accepted_L_created": 0,
        "causal_explanation_or_physical_event_independence_established": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {
            name: digest(out / name)
            for name in ("province_within_calendar_support.csv", "within_calendar_comparison.png")
        },
        "producer_sha256": digest(Path(__file__)),
    }
    require(all(digest(p) == h for p, h in pins.items()), "Current inputs unchanged after audit")
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


def render(metrics, out):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.7))
    scenarios = sorted(metrics.scenario.unique())
    for ax, quality, title in zip(
        axes,
        ("all", "complete_weather_both"),
        ("Aynı hücre ve ay • bütün girdiler", "Aynı hücre ve ay • meteoroloji tam çiftler"),
        strict=True,
    ):
        for variant, label in zip(
            VARIANTS, ("Tam RF", "Yalnız meteoroloji", "Yalnız örtü/arazi"), strict=True
        ):
            block = metrics.loc[
                metrics.variant.eq(variant)
                & metrics.scheme.eq("within_grid_year_month")
                & metrics.quality_profile.eq(quality)
            ].set_index("scenario")
            ax.plot(range(9), block.loc[scenarios, "auxiliary_S_pair_AUC"], marker="o", label=label)
        ax.set(
            xticks=range(9),
            xticklabels=[
                s.replace("d", "").replace("m_t", "m / ").replace("h", "saat") for s in scenarios
            ],
            ylim=(0.4, 0.8),
            ylabel="Kaynak adayı göstergesi için yardımcı çift AUC",
            title=title,
        )
        ax.axhline(0.5, color="gray", linewidth=1, linestyle="--")
        ax.tick_params(axis="x", rotation=55, labelsize=8)
        ax.legend(fontsize=8)
    fig.suptitle(
        "Sabit RF'ler • 2022 kaynak koşullu takvim • Gerçek yangın başarımı değil", fontsize=13
    )
    fig.text(
        0.5,
        0.015,
        "Yeni fit yok; diğer günler gerçek negatif değil. "
        "2022 daha önce görüldü; bağımsız final test sayılmaz.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(out / "within_calendar_comparison.png", dpi=150, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
