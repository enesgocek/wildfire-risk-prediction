"""No-fit post-hoc QA subsets using three weather profiles defined on 3 October."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from wildfire_risk_prediction import nonlinear_rank as ranking
from wildfire_risk_prediction import weather_policy
from wildfire_risk_prediction import weather_support_review as weather
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
BUNDLE = BASE / "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1"
MERSIN = BASE / "cross_source_calendar_feature_review_v1/20261121T180737Z_c322d93c"
RUN = BASE / "nonlinear_rank_run_v1/20261123T132502Z_6193ac44"
REVIEW = BASE / "evaluation_review_package_v1/20261123T141815Z_be04a5fe"
AUDIT = BASE / "evaluation_review_audit_v1/20261123T142016Z_d7e03899"
TIME_SLICES = {
    "all_same_grid_month",
    "gap_1_to_3_days",
    "gap_4_to_30_days",
    "other_day_before_source_day",
    "other_day_after_source_day",
}


def pair_frame(meta, source, eligible):
    work = meta[KEYS].copy()
    work["source"] = source
    work["month"] = work.prediction_timestamp_utc.str[:7]
    a, b = [], []
    for _, group in work.loc[eligible].groupby(["grid_id", "month"], sort=True):
        s, u = group.index[group.source].to_numpy(), group.index[~group.source].to_numpy()
        a.extend(np.repeat(s, len(u)))
        b.extend(np.tile(u, len(s)))
    return pd.DataFrame({"source_calendar_row": a, "other_calendar_row": b}, dtype="int64")


def main():
    pins = {
        REVIEW
        / "readback.json": "4c1ddd5be410efd3d7dfe1f44324db4046f2dfb2fc4058b718519d654473e05e",
        AUDIT / "readback.json": "a380b44c870f999924a66cc4adfe9a07fbc4d01ab83eb2b76d3970e8c1a0f5b3",
    }
    require(all(digest(p) == h for p, h in pins.items()), "Audited existing-score export")
    ar = json.loads((AUDIT / "readback.json").read_bytes())
    pins.update({ROOT / p: sha for p, sha in ar["input_sha256"].items()})
    for p in (Path(weather.__file__), Path(weather_policy.__file__), Path(ranking.__file__)):
        pins[p] = digest(p)
    require(
        all(digest(p) == h for p, h in pins.items()),
        "Current source provenance and score identities",
    )
    full_x, full_q, full_m = [
        pd.read_csv(BUNDLE / name, float_precision="round_trip")
        for name in ("features.csv", "provenance.csv", "inspection_memberships.csv")
    ]
    full_support = weather.inspect(full_x, full_q)
    held = full_m.review_temporal_role.eq("proposed_assessment_2022")
    mr = json.loads((MERSIN / "readback.json").read_bytes())
    snap = MERSIN / mr["snapshot_directory"]
    mx, mq, mm = [
        pd.read_csv(snap / name, float_precision="round_trip")
        for name in ("features.csv", "provenance.csv", "review_roles.csv")
    ]
    msupport = weather.inspect(mx, mq)
    out = (
        BASE
        / "weather_score_support_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    contexts, summaries, metrics, pairs_out, fit_support = [], [], [], [], []
    scenarios = sorted(
        r["scenario"]
        for r in json.loads((RUN / "readback.json").read_bytes())["scenario_summaries"]
    )
    for scenario in scenarios:
        layout = pd.read_csv(RUN / scenario / "fit_layout.csv")
        original = full_support.iloc[layout.calendar_row].copy()
        original["source"] = layout.relevance_source_context_not_Y.to_numpy()
        original["qid"] = layout.qid.to_numpy()
        for profile in weather.PROFILES:
            retained = original.loc[original[profile + "_and_dynamic_15_complete"]]
            mixed = retained.groupby("qid").source.nunique()
            fit_support.append(
                {
                    "scenario": scenario,
                    "profile": profile,
                    "original_fit_rows": len(original),
                    "original_fit_source_rows": int(original.source.sum()),
                    "fit_rows_meeting_profile": len(retained),
                    "fit_source_rows_meeting_profile": int(retained.source.sum()),
                    "informative_queries_after_profile_filter_without_refit": int(
                        mixed.eq(2).sum()
                    ),
                }
            )
    for cohort, metadata, support in (
        (
            "four_province",
            full_m.loc[held].reset_index(drop=True),
            full_support.loc[held].reset_index(drop=True),
        ),
        ("separate_Mersin", mm, msupport),
    ):
        context = support.copy()
        context.insert(0, "cohort", cohort)
        contexts.append(context)
        for scenario in scenarios:
            source = (
                metadata["S_candidate_context_" + scenario].to_numpy()
                if cohort == "four_province"
                else metadata.original_source_record_key_present.to_numpy()
            )
            scores = pd.read_csv(
                RUN / scenario / (cohort + "_scores.csv"), float_precision="round_trip"
            )
            pd.testing.assert_frame_equal(metadata[KEYS], scores[KEYS], check_exact=True)
            baseline_pairs = pair_frame(metadata, source, support.dynamic_15_complete.to_numpy())
            original_pair_set = set(map(tuple, baseline_pairs.to_numpy()))
            for profile in weather.PROFILES:
                eligible = support[profile + "_and_dynamic_15_complete"].to_numpy()
                pairs = pair_frame(metadata, source, eligible)
                require(
                    set(map(tuple, pairs.to_numpy())) <= original_pair_set,
                    "Only existing pairs; no new comparisons",
                )
                require(len(pairs) > 0, "Supported fixed QA subset")
                summaries.append(
                    {
                        "cohort": cohort,
                        "scenario": scenario,
                        "profile": profile,
                        "all_calendar_records_retained": len(metadata),
                        "dynamic_complete_records_before_profile": int(
                            support.dynamic_15_complete.sum()
                        ),
                        "records_meeting_profile": int(eligible.sum()),
                        "source_records_meeting_profile": int((eligible & source).sum()),
                        "same_cell_month_pairs": len(pairs),
                    }
                )
                p = pairs.assign(cohort=cohort, scenario=scenario, profile=profile)
                pairs_out.append(p)
                for variant, column in (
                    ("XGBoost", "xgboost_source_score_not_probability"),
                    ("frozen_linear", "frozen_linear_source_score_not_probability"),
                ):
                    for result in ranking.evaluate_slices(
                        metadata, pairs, scores[column].to_numpy()
                    ):
                        if result["slice"] in TIME_SLICES:
                            metrics.append(
                                {
                                    "cohort": cohort,
                                    "scenario": scenario,
                                    "profile": profile,
                                    "variant": variant,
                                    **result,
                                }
                            )
    pd.concat(contexts, ignore_index=True).to_csv(out / "record_quality_context.csv", index=False)
    pd.DataFrame(fit_support).to_csv(out / "original_fit_quality_support.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / "assessment_profile_support.csv", index=False)
    pd.DataFrame(metrics).to_csv(out / "assessment_profile_metrics.csv", index=False)
    pd.concat(pairs_out, ignore_index=True).to_csv(
        out / "assessment_profile_pair_indices.csv", index=False
    )
    require(
        all(digest(p) == h for p, h in pins.items()), "No previous source, model or result changed"
    )
    body = {
        "status": "fixed_score_weather_QA_subsets_and_missing_context_prepared_pending_audit",
        "weather_policy": weather_policy.specification(),
        "profiles_predefined_on": "2026-10-03",
        "analysis_date": "2026-11-23",
        "analysis_design": (
            "posthoc_diagnostic_on_frozen_broad_support_models_not_clean_QA_retraining"
        ),
        "new_model_or_prediction_calls": 0,
        "new_threshold_selected": False,
        "original_models_remain_trained_on_partial_area_rows": True,
        "true_Y_or_accepted_L_created": 0,
        "negative_label_permitted": False,
        "fire_risk_validated": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    path = out / "readback.json"
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)
    print("QA profile metric rows", len(metrics), "no model or prediction calls", flush=True)


if __name__ == "__main__":
    main()
