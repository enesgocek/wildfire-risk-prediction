"""Describe comparability of fixed auxiliary S scores; never fit, relabel, or select models."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "conditional_pu_ranking_run_v1/20261119T211947Z_fa2feb18/readback.json"
RUN_SHA = "a0b049c3e70042a97df40c5b13afc31c06fc35c5a027be5613fc96ba4cf63940"
REVIEW = BASE / "source_pu_feature_review_v1/20261119T210151Z_3e99d4a1/readback.json"
REVIEW_SHA = "ccc9086c505e22028a670ab9451e2323f429cd8048b83b4c2361519ec2916405"
POLICY = ROOT / "configs/source_ranking_comparability_v1.json"
KEYS = ["grid_id", "prediction_timestamp_utc"]
MEMBER = "S_observed_source_membership"
MODELS = ("logistic_regression", "random_forest", "missingness_control")
SCHEMES = ("quarter", "month", "woody_half", "quarter_woody_half", "month_woody_half")


def assignments(scores, features):
    require(
        not scores.duplicated(KEYS).any() and not features.duplicated(KEYS).any(),
        "Unique review keys",
    )
    require(
        scores.Y_true_fire_target.isna().all()
        and scores.daily_observation_status.eq("unknown").all()
        and scores[MEMBER].isin([0, 1]).all(),
        "Unknown fire Y and observed S only",
    )
    stamps = [datetime.fromisoformat(x) for x in scores.prediction_timestamp_utc]
    require(
        all(
            t.year == 2022
            and t.utcoffset() == UTC.utcoffset(t)
            and t.hour == t.minute == t.second == t.microsecond == 0
            for t in stamps
        ),
        "Only 2022 midnight UTC assessment keys",
    )
    frame = scores.merge(
        features[KEYS + ["forest_fraction", "shrub_fraction"]],
        on=KEYS,
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    require(frame._merge.eq("both").all(), "Every fixed score has a feature key")
    frame = frame.drop(columns="_merge")
    cover = frame[["forest_fraction", "shrub_fraction"]]
    require(
        np.isfinite(cover).all().all()
        and cover.ge(0).all().all()
        and cover.sum(axis=1).le(1 + 1e-12).all(),
        "Measured historic cover fractions; no missing-to-zero conversion",
    )
    frame["woody_fraction_reference_2017"] = cover.sum(axis=1)
    frame["month"] = [f"M{t.month:02d}" for t in stamps]
    frame["quarter"] = [f"Q{(t.month - 1) // 3 + 1}" for t in stamps]
    frame["woody_half"] = np.where(
        frame.woody_fraction_reference_2017.ge(0.5), "woody_ge_0.5", "woody_lt_0.5"
    )
    for prefix in ("month", "quarter"):
        frame[prefix + "_woody_half"] = frame[prefix] + "|" + frame.woody_half
    for model in MODELS:
        values = frame[model + "_source_membership_score"]
        require(np.isfinite(values).all() and values.between(0, 1).all(), "Finite fixed S scores")
    return frame


def credit(source_scores, u_scores):
    delta = np.asarray(source_scores)[:, None] - np.asarray(u_scores)[None, :]
    pairs = int(delta.size)
    doubled = int(2 * (delta > 0).sum() + (delta == 0).sum())
    return {
        "pairs": pairs,
        "wins": int((delta > 0).sum()),
        "ties": int((delta == 0).sum()),
        "losses": int((delta < 0).sum()),
        "doubled_credit": doubled,
        "source_membership_pair_AUC": doubled / (2 * pairs) if pairs else None,
    }


def summarize(frame, scheme, model):
    require(scheme in SCHEMES and model in MODELS, "Declared diagnostic only")
    source = frame.loc[frame[MEMBER].eq(1)]
    unlabelled = frame.loc[frame[MEMBER].eq(0)]
    col = model + "_source_membership_score"
    total = credit(source[col], unlabelled[col])
    same = source[scheme].to_numpy()[:, None] == unlabelled[scheme].to_numpy()[None, :]
    delta = source[col].to_numpy()[:, None] - unlabelled[col].to_numpy()[None, :]
    points = 2 * (delta > 0).astype(int) + (delta == 0).astype(int)
    pieces = {}
    for name, mask in (("within_stratum", same), ("between_strata", ~same)):
        n, c = int(mask.sum()), int(points[mask].sum())
        pieces[name] = {
            "pairs": n,
            "doubled_credit": c,
            "source_membership_pair_AUC": c / (2 * n) if n else None,
            "pair_share": n / total["pairs"] if total["pairs"] else None,
        }
    require(
        sum(x["pairs"] for x in pieces.values()) == total["pairs"]
        and sum(x["doubled_credit"] for x in pieces.values()) == total["doubled_credit"],
        "Exact all-pair decomposition",
    )
    rows, comparable_source, comparable_u = [], 0, 0
    for label, block in frame.groupby(scheme, sort=True):
        s, u = block.loc[block[MEMBER].eq(1)], block.loc[block[MEMBER].eq(0)]
        result = credit(s[col], u[col])
        if len(s) and len(u):
            comparable_source += len(s)
            comparable_u += len(u)
        rows.append(
            {
                "scheme": scheme,
                "stratum": label,
                "model": model,
                "source_keys": len(s),
                "U_keys": len(u),
                **result,
            }
        )
    require(
        sum(r["pairs"] for r in rows) == pieces["within_stratum"]["pairs"]
        and sum(r["doubled_credit"] for r in rows) == pieces["within_stratum"]["doubled_credit"],
        "Within statistic weights pairs, not stratum means",
    )
    return {
        "scheme": scheme,
        "model": model,
        "all_pairs": total,
        **pieces,
        "source_keys_with_opposite_membership_in_stratum": comparable_source,
        "U_keys_with_opposite_membership_in_stratum": comparable_u,
        "one_membership_strata": sum(not (r["source_keys"] and r["U_keys"]) for r in rows),
        "strata": len(rows),
    }, rows


def render(frame, summaries, out):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.3))
    counts = pd.crosstab(frame.month, frame[MEMBER]).reindex(
        [f"M{i:02d}" for i in range(1, 13)], fill_value=0
    )
    x = np.arange(12)
    for code, label, shift in ((1, "Kaynak", -0.2), (0, "Belirsiz U", 0.2)):
        axes[0].bar(x + shift, counts[code], width=0.4, label=label)
    axes[0].set(
        xticks=x,
        xticklabels=range(1, 13),
        xlabel="2022 ayı",
        ylabel="Anahtar sayısı",
        title="Sabit inceleme örnekleminin mevsim dağılımı",
    )
    axes[0].legend()
    selected = [r for r in summaries if r["model"] == "random_forest"]
    values = [selected[0]["all_pairs"]["source_membership_pair_AUC"]] + [
        r["within_stratum"]["source_membership_pair_AUC"] for r in selected
    ]
    labels = [
        "Tüm çiftler",
        "Aynı çeyrek",
        "Aynı ay",
        "Aynı örtü bandı",
        "Çeyrek + örtü",
        "Ay + örtü",
    ]
    axes[1].barh(labels[::-1], values[::-1], color="steelblue")
    for y, value in enumerate(values[::-1]):
        axes[1].text(value + 0.01, y, f"{value:.3f}", va="center", fontsize=9)
    axes[1].set(
        xlim=(0, 1.06),
        xlabel="S üyeliği için çift ağırlıklı AUC",
        title="Aynı kaydedilmiş RF skorları • yeniden eğitim yok",
    )
    axes[1].axvline(0.5, color="gray", linestyle="--", linewidth=1)
    fig.suptitle(
        "Mevsim / eski örtü duyarlılığı • Gerçek yangın değerlendirmesi değil", fontsize=12
    )
    fig.text(
        0.5,
        0.015,
        "168 anahtar korunuyor. Alt karşılaştırmaların çiftleri farklı; "
        "farklar nedensel açıklama veya düzeltilmiş yangın başarımı değildir.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    fig.savefig(out / "comparability.png", dpi=140, facecolor="white")
    plt.close(fig)


def main():
    pins = {RUN: RUN_SHA, REVIEW: REVIEW_SHA, POLICY: digest(POLICY)}
    require(all(digest(p) == h for p, h in pins.items()), "Pinned completed run and review")
    run, review, policy = [json.loads(p.read_bytes()) for p in (RUN, REVIEW, POLICY)]
    require(
        policy["schemes"] == list(SCHEMES)
        and policy["woody_fraction_diagnostic_boundary"] == 0.5
        and policy["woody_fraction_columns"] == ["forest_fraction", "shrub_fraction"]
        and not policy["model_refitting_permitted"]
        and policy["Y_remains_null"]
        and not policy["final_merge_permitted"],
        "Declared posthoc support diagnostic; closed scientific gates",
    )
    score_path, feature_path = (
        RUN.parent / "assessment_source_scores.csv",
        REVIEW.parent / "features.csv",
    )
    pins[score_path] = run["artifact_sha256"][score_path.name]
    pins[feature_path] = review["artifact_sha256"][feature_path.name]
    require(all(digest(p) == h for p, h in pins.items()), "Current consumed bytes")
    frame = assignments(
        pd.read_csv(score_path, float_precision="round_trip"),
        pd.read_csv(feature_path, float_precision="round_trip"),
    )
    require(len(frame) == 168 and frame[MEMBER].sum() == 81, "All 81 source and 87 U keys retained")
    summaries, strata = [], []
    for scheme in SCHEMES:
        for model in MODELS:
            result, rows = summarize(frame, scheme, model)
            require(
                abs(
                    result["all_pairs"]["source_membership_pair_AUC"]
                    - run["metrics"][model]["assessment_source_membership_ROC_AUC"]
                )
                < 1e-15,
                "Fixed scores recover parent source AUC",
            )
            summaries.append(result)
            strata += rows
    out = (
        BASE
        / "source_ranking_comparability_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    frame.to_csv(out / "fixed_score_strata.csv", index=False)
    pd.DataFrame(strata).to_csv(out / "stratum_pair_statistics.csv", index=False)
    render(frame, summaries, out)
    report = {
        "status": "fixed_S_score_posthoc_comparability_diagnostic_complete_not_Y_acceptance",
        "assessment_keys": len(frame),
        "source_keys": 81,
        "U_keys": 87,
        "all_source_U_pairs": 7047,
        "diagnostic_policy": policy,
        "summaries": summaries,
        "models_refitted": 0,
        "new_features_or_years_loaded": False,
        "new_Y_labels_or_L_memberships": 0,
        "final_merge_performed": False,
        "common_class_conditionals_verified": False,
        "causal_bias_fraction_estimated": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {
            name: digest(out / name)
            for name in (
                "fixed_score_strata.csv",
                "stratum_pair_statistics.csv",
                "comparability.png",
            )
        },
    }
    require(all(digest(p) == h for p, h in pins.items()), "Original snapshots unchanged")
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == report, "Readback roundtrip")
    print(out.relative_to(ROOT).as_posix())
    print("PASS fixed_scores_only; no real fire evaluation or new labels")
    print("readback_sha256", digest(path))
    for row in summaries:
        if row["model"] == "random_forest":
            print(row["scheme"], json.dumps(row["within_stratum"]))


if __name__ == "__main__":
    main()
