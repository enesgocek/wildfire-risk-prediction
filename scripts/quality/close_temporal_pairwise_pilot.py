"""Close audited temporal pilot with diagnostic slices and exact local experiment recording."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib
import numpy as np
import pandas as pd
from mlflow import MlflowClient

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require
from wildfire_risk_prediction.feature_partition import parse_csv

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
RUN = BASE / "temporal_pairwise_run_v1/20261121T174415Z_5a77b21e"
AUDIT = BASE / "temporal_pairwise_audit_v1/20261121T174613Z_2feb2bbd"
PROVINCE = BASE / "satellite_PU_ranking_audit_v1/20261120T013224Z_b8a45358"
VARIANTS = {
    "pairwise_linear": "temporal_pairwise_linear_score_not_probability",
    "fixed_full_27_features": "full_27_features_auxiliary_source_score",
    "fixed_weather_only": "weather_only_auxiliary_source_score",
    "fixed_static_cover_terrain_only": "static_cover_terrain_only_auxiliary_source_score",
}


def date_slices(dates, a, b):
    left = dates.iloc[a].reset_index(drop=True)
    right = dates.iloc[b].reset_index(drop=True)
    delta = (left - right).dt.total_seconds().to_numpy() / 86400
    return {
        "all_same_grid_month": np.ones(len(a), dtype=bool),
        "other_day_before_source_day": delta > 0,
        "other_day_after_source_day": delta < 0,
        "gap_1_to_3_days": (np.abs(delta) >= 1) & (np.abs(delta) <= 3),
        "gap_4_to_30_days": (np.abs(delta) >= 4) & (np.abs(delta) <= 30),
    }


def main():
    pins = {
        RUN / "readback.json": "b8e847f8d510721ce84b788161ae40ac5f3bfa098154b0e56a013fc380f83d82",
        AUDIT / "readback.json": "7faff2ad4721a8984b3a4e34aae3ebdbe8c61dde3c5568477bd257ed3d68d086",
        PROVINCE
        / "readback.json": "19f67bcfecf918804a7365ee1c7d7bfc53da3e9956a87004ac275aa29f2f8f47",
    }
    require(all(digest(p) == h for p, h in pins.items()), "Audited pilot and frozen area mapping")
    report = json.loads((RUN / "readback.json").read_bytes())
    audit = json.loads((AUDIT / "readback.json").read_bytes())
    for data in (report, audit):
        pins.update({ROOT / p: h for p, h in data["input_sha256"].items()})
    pins.update({RUN / p: h for p, h in report["artifact_sha256"].items()})
    province_report = json.loads((PROVINCE / "readback.json").read_bytes())
    p = PROVINCE / "assessment_context.csv"
    pins[p] = province_report["artifact_sha256"][p.name]
    require(
        all(digest(p) == h for p, h in pins.items()), "Current model, metadata and score hashes"
    )
    mapping = parse_csv(p.read_bytes())[["grid_id", "province_support"]].drop_duplicates()
    require(mapping.grid_id.is_unique, "Unambiguous frozen area membership signature")
    provinces = mapping.set_index("grid_id").province_support
    snapshot = (
        BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896/snapshot_8914be77"
    )
    metadata = parse_csv((snapshot / "review_roles.csv").read_bytes())
    held_indices = metadata.index[metadata.review_temporal_role.eq("proposed_assessment_2022")]
    out = (
        BASE
        / "temporal_pairwise_closure_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    rows, coefficients = [], []
    for summary in report["scenario_summaries"]:
        scenario = summary["scenario"]
        frame = parse_csv((RUN / scenario / "assessment_scores.csv").read_bytes())
        pd.testing.assert_frame_equal(
            frame[KEYS], metadata.loc[held_indices, KEYS].reset_index(drop=True), check_exact=True
        )
        frame.index = held_indices
        frame["province"] = frame.grid_id.map(provinces)
        require(frame.province.notna().all(), "All calendar cells mapped to area context")
        pairs = parse_csv((RUN / scenario / "assessment_pair_indices.csv").read_bytes())
        a, b = pairs.source_calendar_row.to_numpy(), pairs.other_calendar_row.to_numpy()
        dates = pd.to_datetime(metadata.prediction_timestamp_utc, utc=True)
        slices = date_slices(dates, a, b)
        for province in ("Antalya", "İzmir", "Mersin", "Muğla"):
            slices["area_" + province] = (
                frame.loc[a, "province"]
                .str.split("|")
                .map(lambda xs, name=province: name in xs)
                .to_numpy()
            )
        for name, mask in slices.items():
            for variant, column in VARIANTS.items():
                difference = (
                    frame.loc[a[mask], column].to_numpy() - frame.loc[b[mask], column].to_numpy()
                )
                require(np.isfinite(difference).all(), "Complete-dynamic diagnostic pairs")
                wins, ties = int((difference > 0).sum()), int((difference == 0).sum())
                value = (wins + ties / 2) / len(difference) if len(difference) else None
                if name == "all_same_grid_month":
                    require(
                        value
                        == summary["comparison_same_complete_dynamic_pairs"][variant][
                            "auxiliary_pair_AUC"
                        ],
                        "Same reviewed pair metrics",
                    )
                rows.append(
                    {
                        "scenario": scenario,
                        "slice": name,
                        "variant": variant,
                        "pairs": len(difference),
                        "source_keys_with_comparator": len(set(a[mask])),
                        "other_keys_with_comparator": len(set(b[mask])),
                        "auxiliary_pair_AUC": value,
                    }
                )
        coef = parse_csv((RUN / scenario / "coefficients.csv").read_bytes())
        coef.insert(0, "scenario", scenario)
        coefficients.append(coef)
    slices = pd.DataFrame(rows)
    slices.to_csv(out / "context_slices.csv", index=False)
    pd.concat(coefficients, ignore_index=True).to_csv(out / "coefficient_context.csv", index=False)
    render(slices, out)
    tracking = ROOT / "outputs/mlflow"
    database = tracking / "mlflow.db"
    backup = tracking / (
        "before-temporal-pairwise-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".db"
    )
    require(database.is_file() and not backup.exists(), "Unique local database backup")
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as source:
        with sqlite3.connect(backup) as destination:
            source.backup(destination)
    client = MlflowClient(tracking_uri="sqlite:///" + database.as_posix())
    experiment = client.get_experiment_by_name("satellite-source-ranking-pilot")
    require(
        experiment is not None and experiment.artifact_location.startswith(tracking.as_uri()),
        "Existing local experiment only",
    )
    run_id = client.create_run(
        experiment.experiment_id,
        tags={
            "mlflow.runName": "same-cell-month-nine-linear-pairwise-pilots",
            "run_type": "auxiliary_source_ranking_not_true_fire_validation",
            "readback_sha256": digest(RUN / "readback.json"),
        },
    ).info.run_id
    metrics = {
        s["scenario"] + "_" + v + "_matched_context_AUC": m["auxiliary_pair_AUC"]
        for s in report["scenario_summaries"]
        for v, m in s["comparison_same_complete_dynamic_pairs"].items()
    }
    try:
        for key, value in {
            "new_models_fitted": 9,
            "fit_years": "2018-2021",
            "exploratory_year": 2022,
            "final_merge": False,
            "true_fire_validation": False,
        }.items():
            client.log_param(run_id, key, value)
        for key, value in metrics.items():
            client.log_metric(run_id, key, value)
        for folder, area in ((RUN, "pilot"), (AUDIT, "separate_audit"), (out, "closure")):
            client.log_artifacts(run_id, str(folder), artifact_path=area)
        client.set_terminated(run_id, status="FINISHED")
    except Exception:
        client.set_terminated(run_id, status="FAILED")
        raise
    restored = client.get_run(run_id)
    require(
        restored.info.status == "FINISHED" and restored.data.metrics == metrics,
        "Exact local experiment metric values read back",
    )
    require(
        all(digest(p) == h for p, h in pins.items()),
        "Original models and scientific artifacts unchanged",
    )
    result = {
        "status": "audited_pilot_context_slices_and_local_record_complete",
        "parent_readback_sha256": digest(RUN / "readback.json"),
        "audit_sha256": digest(AUDIT / "readback.json"),
        "new_models_fitted_in_this_closure": 0,
        "recorded_approved_pilot_model_count": 9,
        "mlflow_run_id": run_id,
        "metrics_read_back_exact": len(metrics),
        "database_backup": backup.relative_to(ROOT).as_posix(),
        "database_backup_sha256": digest(backup),
        "slices_are_exploratory_not_true_fire_or_independent_events": True,
        "true_Y_or_accepted_L_created": 0,
        "model_registry_entry_created": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


def render(slices, out):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    scenarios = sorted(slices.scenario.unique())
    for variant, label in (
        ("pairwise_linear", "Gün çifti doğrusal"),
        ("fixed_full_27_features", "Sabit tam RF"),
        ("fixed_weather_only", "Sabit meteoroloji RF"),
        ("fixed_static_cover_terrain_only", "Sabit örtü/arazi RF"),
    ):
        frame = slices.loc[
            slices["slice"].eq("all_same_grid_month") & slices.variant.eq(variant)
        ].set_index("scenario")
        axes[0].plot(range(9), frame.loc[scenarios, "auxiliary_pair_AUC"], marker="o", label=label)
    for name, label in (
        ("other_day_before_source_day", "Karşı tarih adaydan önce"),
        ("other_day_after_source_day", "Karşı tarih adaydan sonra"),
        ("gap_1_to_3_days", "1–3 gün aralıklı çift"),
    ):
        frame = slices.loc[
            slices["slice"].eq(name) & slices.variant.eq("pairwise_linear")
        ].set_index("scenario")
        axes[1].plot(range(9), frame.loc[scenarios, "auxiliary_pair_AUC"], marker="o", label=label)
    for ax in axes:
        ax.set(
            xticks=range(9),
            xticklabels=[s.replace("d", "").replace("m_t", "m/") for s in scenarios],
            ylim=(0.35, 0.8),
            ylabel="Yardımcı kaynak-bağlamı çift AUC",
        )
        ax.tick_params(axis="x", rotation=55, labelsize=8)
        ax.axhline(0.5, linestyle="--", color="gray", linewidth=1)
        ax.legend(fontsize=8)
    axes[0].set_title("Aynı tam 15-alanlı gün çiftleri")
    axes[1].set_title("Doğrusal model • tarih yönü ve yakınlığı")
    fig.suptitle("2022 keşif tanısı • Gerçek yangın başarımı veya olasılığı değil")
    fig.text(
        0.5,
        0.015,
        "Diğer günler yangın negatifi değil; bu kapanışta yeni fit yok.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(out / "temporal_pairwise_comparison.png", dpi=150, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
