"""Export existing 2022 scores, source links and geographic support without fitting."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from wildfire_risk_prediction import evaluation_review as review
from wildfire_risk_prediction import ranking_queries
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
BUNDLE = BASE / "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1"
MERSIN = BASE / "cross_source_calendar_feature_review_v1/20261121T180737Z_c322d93c"
RUN = BASE / "nonlinear_rank_run_v1/20261123T132502Z_6193ac44"
CLOSURE = BASE / "nonlinear_rank_closure_v1/20261123T133013Z_64470446"


def main():
    pins = {
        BUNDLE
        / "readback.json": "86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366",
        MERSIN
        / "readback.json": "d32b99e6581c6a2412ba6013af727d4220d19d8e2d03666f8ebb48634d3ce0f6",
        CLOSURE
        / "readback.json": "f291058ddfbbbcc486bba01e128eae9c53cc600eede33161e74569835a3db466",
    }
    require(all(digest(p) == h for p, h in pins.items()), "Frozen experiment and source receipts")
    closure = json.loads((CLOSURE / "readback.json").read_bytes())
    pins.update({ROOT / p: h for p, h in closure["input_sha256"].items()})
    reports = {
        folder: json.loads((folder / "readback.json").read_bytes())
        for folder in (BUNDLE, MERSIN, RUN)
    }
    for folder in (BUNDLE, MERSIN):
        for name, sha in reports[folder]["artifact_sha256"].items():
            if name.endswith(".csv"):
                pins[folder / name] = sha
    pins[Path(review.__file__)] = digest(Path(review.__file__))
    require(all(digest(p) == h for p, h in pins.items()), "Current already-audited bytes")
    full_x = pd.read_csv(BUNDLE / "features.csv", float_precision="round_trip")
    full_m = pd.read_csv(BUNDLE / "inspection_memberships.csv")
    held = full_m.review_temporal_role.eq("proposed_assessment_2022")
    x, meta = full_x.loc[held].reset_index(drop=True), full_m.loc[held].reset_index(drop=True)
    snap = MERSIN / reports[MERSIN]["snapshot_directory"]
    mx = pd.read_csv(snap / "features.csv", float_precision="round_trip")
    mm = pd.read_csv(snap / "review_roles.csv")
    for a, b in ((x, meta), (mx, mm)):
        pd.testing.assert_frame_equal(a[KEYS], b[KEYS], check_exact=True)
    require((len(x), len(mx)) == (6573, 2383), "Only two existing explored calendars")
    union = review.checked_feature_union([x, mx])
    shared = x[KEYS].merge(mx[KEYS], on=KEYS)
    require(len(shared) == 245 and len(union) == 8711, "Known calendar overlap accounted once")
    map_frame = pd.read_csv(BUNDLE / "province_support.csv")
    area_map = (
        map_frame.groupby("grid_id").province.apply(lambda v: "|".join(sorted(set(v)))).to_dict()
    )
    mm["province_area_intersections"] = mm.grid_id.map(area_map).fillna(
        "not_in_original_package_area_mapping"
    )
    out = (
        BASE
        / "evaluation_review_package_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    union.to_csv(out / "features.csv", index=False)
    shared.to_csv(out / "shared_calendar_keys.csv", index=False)
    summaries, long_scores, record_tables, provenance, missingness = [], [], [], [], []
    main_flags = meta[KEYS + [c for c in meta if c.startswith("S_candidate_context_")]].copy()
    anchors = mm.loc[mm.original_source_record_key_present, KEYS].merge(
        main_flags, on=KEYS, how="left", indicator=True
    )
    anchors["also_in_four_province_calendar"] = anchors.pop("_merge").eq("both")
    anchors.to_csv(out / "Mersin_source_anchor_overlap.csv", index=False)
    for cohort, features, metadata, feature_path, metadata_path, original_rows in (
        (
            "four_province",
            x,
            meta,
            BUNDLE / "features.csv",
            BUNDLE / "inspection_memberships.csv",
            np.flatnonzero(held),
        ),
        (
            "separate_Mersin",
            mx,
            mm,
            snap / "features.csv",
            snap / "review_roles.csv",
            np.arange(len(mm)),
        ),
    ):
        complete = np.isfinite(
            features[ranking_queries.DYNAMIC_FEATURES].to_numpy(dtype=float)
        ).all(axis=1)
        record = metadata[
            KEYS
            + [
                "target",
                "accepted_L_membership",
                "daily_observation_status",
                "province_area_intersections",
            ]
        ].copy()
        record.insert(0, "cohort", cohort)
        record["complete_dynamic_15"] = complete
        record["negative_label_permitted"] = False
        record["scope"] = "experimental_2022_review_not_fire_risk_product_or_final_labelled_merge"
        record_tables.append(record)
        origin = record[["cohort"] + KEYS].copy()
        origin["original_zero_based_calendar_row"] = original_rows
        origin["original_features_csv"] = feature_path.relative_to(ROOT).as_posix()
        origin["original_metadata_csv"] = metadata_path.relative_to(ROOT).as_posix()
        provenance.append(origin)
        missingness.append(review.missingness_table(features, cohort))
        for scenario in sorted(r["scenario"] for r in reports[RUN]["scenario_summaries"]):
            layout = pd.read_csv(RUN / scenario / "fit_layout.csv")
            table = pd.read_csv(
                RUN / scenario / (cohort + "_scores.csv"), float_precision="round_trip"
            )
            pd.testing.assert_frame_equal(table[KEYS], metadata[KEYS], check_exact=True)
            source = (
                metadata["S_candidate_context_" + scenario].to_numpy()
                if cohort == "four_province"
                else metadata.original_source_record_key_present.to_numpy()
            )
            summary = review.support_counts(metadata, source, complete, layout)
            summaries.append({"cohort": cohort, "scenario": scenario, **summary})
            for field in (
                "xgboost_source_score_not_probability",
                "frozen_linear_source_score_not_probability",
            ):
                require(
                    np.array_equal(np.isfinite(table[field]), complete),
                    "Same finite support; no score imputation",
                )
            display = table[
                KEYS
                + [
                    "xgboost_source_score_not_probability",
                    "frozen_linear_source_score_not_probability",
                ]
            ].copy()
            display.insert(0, "cohort", cohort)
            display.insert(1, "scenario", scenario)
            display["existing_source_context_not_true_Y"] = source
            display["complete_dynamic_15"] = complete
            display["cell_seen_in_this_model_fit"] = metadata.grid_id.isin(
                set(layout.grid_id)
            ).to_numpy()
            for variant, column in (
                ("XGBoost", "xgboost_source_score_not_probability"),
                ("linear", "frozen_linear_source_score_not_probability"),
            ):
                positions = review.rank_positions(metadata, table[column].to_numpy())
                for name in positions:
                    display[variant + "_" + name] = positions[name].to_numpy()
            long_scores.append(display)
    scores = pd.concat(long_scores, ignore_index=True)
    keys = ["cohort"] + KEYS
    positions = (
        scores.groupby(keys, sort=True)
        .agg(
            scenarios_with_finite_score=("complete_dynamic_15", "sum"),
            scenarios_with_existing_source_context=("existing_source_context_not_true_Y", "sum"),
            minimum_XGBoost_day_position=("XGBoost_position_in_available_cell_month_days", "min"),
            maximum_XGBoost_day_position=("XGBoost_position_in_available_cell_month_days", "max"),
        )
        .reset_index()
    )
    positions["descriptive_day_position_spread_not_risk_uncertainty"] = (
        positions.maximum_XGBoost_day_position - positions.minimum_XGBoost_day_position
    )
    scores.to_csv(out / "score_review.csv", index=False)
    positions.to_csv(out / "scenario_position_review.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / "support_summary.csv", index=False)
    pd.concat(record_tables, ignore_index=True).to_csv(out / "record_memberships.csv", index=False)
    pd.concat(provenance, ignore_index=True).to_csv(out / "record_provenance.csv", index=False)
    pd.concat(missingness, ignore_index=True).to_csv(
        out / "missing_dynamic_fields.csv", index=False
    )
    (out / "README.txt").write_text(
        "Deneysel 2022 skor ve destek incelemesi. Yangin etiketi veya risk urunu degildir.\n"
        "6573 + 2383 = 8956 kohort uyeligi; 245 ortak anahtar, 8711 tekil hucre-gun.\n"
        "features.csv ortak degerleri bir kez korur; kohortlarin uyelikleri birlestirilmez.\n"
        "score_review.csv dokuz ayarin eski/yeni skor kopyalari ve "
        "hucre-ay ici sira konumlaridir.\n"
        "Sira 1 yuksek kaynak skoru, esitlikte ortalama konumdur; "
        "yuzde veya risk sinifi degildir.\n"
        "Ayrik model skor olcekleri toplanmaz/ortalama alinmaz; nihai ayar secilmez.\n"
        "Eksik skorlar korunur. Atamasiz gun yanginsiz degildir; Y/L bos, gozlem unknown.\n"
        "Kohort/hucre/gun anahtariyla record_provenance.csv uzerinden eski satira gidilebilir.\n"
        "Hucrenin ogrenmede gorulmesi tek basina sizinti gostermez; "
        "gorulmemesi bagimsiz saha dogrulamasi sayilmaz.\n"
        "Takvim kaynak/aday baglamina kosulludur; nufus paneli "
        "veya 2889 hucrede risk yayini degildir.\n",
        encoding="utf-8",
    )
    require(
        all(digest(p) == h for p, h in pins.items()), "Original package and model outputs unchanged"
    )
    report = {
        "status": "existing_two_calendar_scores_and_support_exported_for_review_pending_audit",
        "source_run": RUN.relative_to(ROOT).as_posix(),
        "cohort_memberships": len(x) + len(mx),
        "shared_keys": len(shared),
        "unique_keys": len(union),
        "score_rows": len(scores),
        "source_anchors_in_Mersin_calendar": len(anchors),
        "Mersin_source_anchors_also_in_other_calendar": int(
            anchors.also_in_four_province_calendar.sum()
        ),
        "support": summaries,
        "new_models_or_inference_calls": 0,
        "true_Y_or_accepted_L_created": 0,
        "fire_risk_validated": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)
    print(pd.DataFrame(summaries).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
