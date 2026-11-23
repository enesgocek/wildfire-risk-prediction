"""Build an offline inspection prototype from existing audited 2022 values only."""

import json
import math
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CONFIG = ROOT / "configs/research_prototype_direction_v1.json"
REVIEW = BASE / "evaluation_review_package_v1/20261123T141815Z_be04a5fe"
QA = BASE / "weather_score_support_review_v1/20261123T142800Z_8725a867"
RUN = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"
CLOSURE = BASE / "dataset_support_review_closure_v1/20261123T143653Z_f90b45fa"
DICTIONARY = (
    BASE / "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1/feature_dictionary.json"
)


def validate(policy):
    require(
        policy["decision_source"] == "explicit_researcher_A_conditional_research_prototype"
        and policy["scope"] == "local_offline_inspection_of_existing_2022_results_and_features"
        and policy["conditional_research_workflow_selected"] is True,
        "Explicit A offline prototype scope",
    )
    require(
        all(
            policy[k] is False
            for k in (
                "main_fire_risk_method_scientifically_validated",
                "source_context_scores_are_verified_fire_risk",
                "new_training_authorized",
                "scientific_years_2023_2024_2025_open_authorized",
                "true_Y_or_accepted_L_created",
                "negative_label_permitted",
                "probability_or_validated_risk_colors_authorized",
                "live_forecast_authorized",
                "external_publication_or_raw_data_upload_authorized",
                "final_merge_authorized",
            )
        )
        and policy["daily_observation_status"] == "unknown",
        "No promotion to validated risk or labels",
    )


def finite(value):
    return float(value) if math.isfinite(float(value)) else None


def main():
    policy = json.loads(CONFIG.read_bytes())
    validate(policy)
    require(
        digest(CLOSURE / "readback.json")
        == "a85c9f271e93776ca377df99c6c7b66ed7575cf452831349d8fd73a5adef0592",
        "Frozen full dataset-support closure",
    )
    closure = json.loads((CLOSURE / "readback.json").read_bytes())
    pins = {ROOT / p: h for p, h in closure["input_sha256"].items()}
    pins[CLOSURE / "readback.json"] = digest(CLOSURE / "readback.json")
    scripts = Path(__file__).parent
    assets = {
        "inceleme.html": scripts / "research_prototype_template.html",
        "research-core.js": scripts / "research_prototype_core.js",
        "research-app.js": scripts / "research_prototype_app.js",
    }
    for p in (CONFIG, DICTIONARY, *assets.values()):
        pins[p] = digest(p)
    require(all(digest(p) == h for p, h in pins.items()), "Current audited source and code hashes")
    records = pd.read_csv(REVIEW / "record_memberships.csv")
    origins = pd.read_csv(REVIEW / "record_provenance.csv")
    x = pd.read_csv(REVIEW / "features.csv", float_precision="round_trip")
    quality = pd.read_csv(QA / "record_quality_context.csv", float_precision="round_trip")
    existing = pd.read_csv(REVIEW / "score_review.csv", float_precision="round_trip")
    dictionary = json.loads(DICTIONARY.read_bytes())
    names = [r["name"] for r in dictionary]
    require(
        x.columns.tolist() == KEYS + names and len(names) == 27, "Exact source feature dictionary"
    )
    require(
        records.target.isna().all()
        and records.accepted_L_membership.isna().all()
        and records.daily_observation_status.eq("unknown").all()
        and records.prediction_timestamp_utc.str.startswith("2022-").all(),
        "Existing unknown-target 2022 records only",
    )
    cohort_keys = ["cohort"] + KEYS
    for table in (origins, quality):
        pd.testing.assert_frame_equal(records[cohort_keys], table[cohort_keys], check_exact=True)
    scenarios = sorted(existing.scenario.unique())
    require(len(scenarios) == 9, "All nine scenarios, none production-selected")
    lookup = {
        tuple(row[:2]): [finite(v) for v in row[2:]] for row in x.itertuples(index=False, name=None)
    }
    paths = sorted(set(origins.original_features_csv) | set(origins.original_metadata_csv))
    path_ids = {p: i for i, p in enumerate(paths)}
    by_cohort = {}
    for cohort in records.cohort.unique():
        by_cohort[cohort] = {
            s: pd.read_csv(RUN / s / (cohort + "_scores.csv"), float_precision="round_trip")
            for s in scenarios
        }
        expected = records.loc[records.cohort.eq(cohort), KEYS].reset_index(drop=True)
        for frame in by_cohort[cohort].values():
            pd.testing.assert_frame_equal(frame[KEYS], expected, check_exact=True)
    flags = existing.pivot(
        index=cohort_keys, columns="scenario", values="existing_source_context_not_true_Y"
    )
    counters = {cohort: 0 for cohort in by_cohort}
    packed = []
    for i, record in enumerate(records.to_dict("records")):
        key = (record["grid_id"], record["prediction_timestamp_utc"])
        cohort = record["cohort"]
        j = counters[cohort]
        counters[cohort] += 1
        q, origin = quality.iloc[i], origins.iloc[i]
        eligible = bool(q.primary_full_area_and_dynamic_15_complete)
        score_rows = [by_cohort[cohort][s].iloc[j] for s in scenarios]
        require(
            all(bool(r.primary_weather_and_dynamic_15_eligible) == eligible for r in score_rows),
            "Eligibility identical across all fixed models",
        )
        values = [
            [
                finite(r.new_primary_weather_source_score_not_probability),
                finite(r.previous_broad_xgboost_source_score_not_probability),
                finite(r.previous_broad_frozen_linear_source_score_not_probability),
            ]
            for r in score_rows
        ]
        require(
            all((row[0] is not None) == eligible for row in values), "No unsupported primary score"
        )
        bitmask = sum(
            (1 << k) for k, s in enumerate(scenarios) if bool(flags.loc[(cohort, *key), s])
        )
        packed.append(
            {
                "cohort": cohort,
                "grid": key[0],
                "time": key[1],
                "province": record["province_area_intersections"],
                "eligible": eligible,
                "flags": bitmask,
                "x": lookup[key],
                "scores": values,
                "quality": [
                    float(q.weather_min_valid_area_fraction),
                    bool(q.vegetation_30d_missing),
                    bool(q.vegetation_60d_missing),
                ],
                "origin": [
                    path_ids[origin.original_features_csv],
                    path_ids[origin.original_metadata_csv],
                    int(origin.original_zero_based_calendar_row),
                ],
            }
        )
    payload = {
        "version": "historical_research_prototype_v1",
        "records": packed,
        "scenarios": scenarios,
        "dictionary": dictionary,
        "paths": paths,
        "model_run": RUN.relative_to(ROOT).as_posix(),
        "model_run_sha256": digest(RUN / "readback.json"),
        "scientific_state": {
            "target": None,
            "accepted_L_membership": None,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "fire_risk_validated": False,
        },
    }
    require(
        len(packed) == 8956 and sum(r["eligible"] for r in packed) == 6770,
        "Exact existing membership and score counts",
    )
    out = (
        BASE
        / "historical_research_prototype_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    for name, source in assets.items():
        shutil.copyfile(source, out / name)
    (out / "review_data.js").write_text(
        "globalThis.RESEARCH_DATA="
        + json.dumps(payload, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + ";\n",
        encoding="utf-8",
    )
    (out / "README.txt").write_text(
        "inceleme.html dosyasini tarayicida acin. Dort HTML/JS dosyasi ayni klasorde kalmali.\n"
        "6573 dort il / 2383 ayri Mersin uyeligi; 4841 / 1929 ana kalite puani.\n"
        "Bu yerel ve gecmis 2022 sonuc incelemesidir; "
        "yangin olasiligi veya canli risk urunu degildir.\n"
        "Gercek Y/L yok, eksikler korunur. Yeni tahmin veya model kurma yapmaz.\n",
        encoding="utf-8",
    )
    require(all(digest(p) == h for p, h in pins.items()), "Original outputs preserved")
    report = {
        "status": "explicit_A_local_historical_prototype_built_pending_data_and_logic_audit",
        "decision": policy,
        "memberships": len(packed),
        "primary_weather_scored_memberships": 6770,
        "unique_feature_keys": len(x),
        "model_scenarios": scenarios,
        "browser_render_or_manual_usability_verified": False,
        "new_model_or_prediction_calls": 0,
        "new_Y_or_accepted_L": 0,
        "closed_year_values_opened": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


if __name__ == "__main__":
    main()
