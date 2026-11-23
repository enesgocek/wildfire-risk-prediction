"""Independently read back existing-score review exports, without loading any model."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
BUNDLE = BASE / "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1"
MERSIN = BASE / "cross_source_calendar_feature_review_v1/20261121T180737Z_c322d93c"
RUN = BASE / "nonlinear_rank_run_v1/20261123T132502Z_6193ac44"


def check_positions(group, score_column, position_column, count_column):
    values = group[score_column].to_numpy(dtype=float)
    valid = np.isfinite(values)
    v = values[valid]
    positions = np.full(len(values), np.nan)
    positions[valid] = (
        1 + (v[None, :] > v[:, None]).sum(axis=1) + ((v[None, :] == v[:, None]).sum(axis=1) - 1) / 2
    )
    np.testing.assert_array_equal(positions, group[position_column])
    require(group[count_column].eq(len(v)).all(), "Same-cell/month finite comparator counts")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    folder = parser.parse_args().package.resolve()
    require(
        folder.parent == (BASE / "evaluation_review_package_v1").resolve(),
        "Workspace review package",
    )
    report = json.loads((folder / "readback.json").read_bytes())
    pins = {ROOT / p: sha for p, sha in report["input_sha256"].items()}
    pins[folder / "readback.json"] = digest(folder / "readback.json")
    pins.update({folder / p: sha for p, sha in report["artifact_sha256"].items()})
    require(all(digest(p) == sha for p, sha in pins.items()), "Current input/output bytes")
    require(
        report["new_models_or_inference_calls"] == report["true_Y_or_accepted_L_created"] == 0
        and not report["final_merge_performed"]
        and not report["fire_risk_validated"],
        "Inspection-only output",
    )
    features = pd.read_csv(folder / "features.csv", float_precision="round_trip")
    records = pd.read_csv(folder / "record_memberships.csv")
    provenance = pd.read_csv(folder / "record_provenance.csv")
    scores = pd.read_csv(folder / "score_review.csv", float_precision="round_trip")
    supports = pd.read_csv(folder / "support_summary.csv")
    positions = pd.read_csv(folder / "scenario_position_review.csv", float_precision="round_trip")
    missing = pd.read_csv(folder / "missing_dynamic_fields.csv")
    full_x = pd.read_csv(BUNDLE / "features.csv", float_precision="round_trip")
    full_m = pd.read_csv(BUNDLE / "inspection_memberships.csv")
    held = full_m.prediction_timestamp_utc.str[:4].eq("2022")
    mr = json.loads((MERSIN / "readback.json").read_bytes())
    snap = MERSIN / mr["snapshot_directory"]
    mx, mm = [
        pd.read_csv(snap / n, float_precision="round_trip")
        for n in ("features.csv", "review_roles.csv")
    ]
    names = features.columns[2:].tolist()
    require(len(names) == 27 and features.columns[:2].tolist() == KEYS, "Unchanged 27-field schema")
    expected = (
        pd.concat([full_x.loc[held], mx])
        .drop_duplicates(KEYS)
        .sort_values(KEYS)
        .reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(features, expected, check_exact=True)
    require(
        len(features) == 8711 and len(records) == len(provenance) == 8956,
        "Distinct features versus overlapping cohort memberships",
    )
    require(
        not records.duplicated(["cohort"] + KEYS).any()
        and not scores.duplicated(["cohort", "scenario"] + KEYS).any()
        and len(scores) == 80604,
        "Unique record/scenario identities",
    )
    require(
        records.target.isna().all()
        and records.accepted_L_membership.isna().all()
        and records.daily_observation_status.eq("unknown").all()
        and not records.negative_label_permitted.any(),
        "No target promotion",
    )
    shared = (
        full_x.loc[held, KEYS].merge(mx[KEYS], on=KEYS).sort_values(KEYS).reset_index(drop=True)
    )
    found = (
        pd.read_csv(folder / "shared_calendar_keys.csv").sort_values(KEYS).reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(shared, found, check_exact=True)
    require(len(shared) == 245, "No double-counted shared keys")
    for cohort, metadata, source_x, row_indices, fp, mp in (
        (
            "four_province",
            full_m.loc[held].reset_index(drop=True),
            full_x,
            np.flatnonzero(held),
            BUNDLE / "features.csv",
            BUNDLE / "inspection_memberships.csv",
        ),
        (
            "separate_Mersin",
            mm,
            mx,
            np.arange(len(mm)),
            snap / "features.csv",
            snap / "review_roles.csv",
        ),
    ):
        rows = records.loc[records.cohort.eq(cohort)].reset_index(drop=True)
        origin = provenance.loc[provenance.cohort.eq(cohort)].reset_index(drop=True)
        pd.testing.assert_frame_equal(rows[KEYS], metadata[KEYS], check_exact=True)
        np.testing.assert_array_equal(origin.original_zero_based_calendar_row, row_indices)
        require(
            origin.original_features_csv.eq(fp.relative_to(ROOT).as_posix()).all()
            and origin.original_metadata_csv.eq(mp.relative_to(ROOT).as_posix()).all(),
            "Exact source row links",
        )
        pd.testing.assert_frame_equal(
            rows[KEYS], source_x.iloc[row_indices][KEYS].reset_index(drop=True), check_exact=True
        )
        expected_x = source_x.iloc[row_indices].reset_index(drop=True)
        exported_x = rows[KEYS].merge(features, on=KEYS, how="left", validate="one_to_one")
        pd.testing.assert_frame_equal(exported_x, expected_x, check_exact=True)
        for field in missing.loc[missing.cohort.eq(cohort)].itertuples(index=False):
            require(
                field.records == len(expected_x)
                and field.missing_records == int((~np.isfinite(expected_x[field.feature])).sum()),
                "Independent per-feature missingness counts",
            )
        for scenario in sorted(scores.scenario.unique()):
            subset = scores.loc[
                scores.cohort.eq(cohort) & scores.scenario.eq(scenario)
            ].reset_index(drop=True)
            old = pd.read_csv(
                RUN / scenario / (cohort + "_scores.csv"), float_precision="round_trip"
            )
            pd.testing.assert_frame_equal(
                subset[
                    KEYS
                    + [
                        "xgboost_source_score_not_probability",
                        "frozen_linear_source_score_not_probability",
                    ]
                ],
                old[
                    KEYS
                    + [
                        "xgboost_source_score_not_probability",
                        "frozen_linear_source_score_not_probability",
                    ]
                ],
                check_exact=True,
            )
            fit = pd.read_csv(RUN / scenario / "fit_layout.csv")
            seen = set(fit.grid_id)
            np.testing.assert_array_equal(
                subset.cell_seen_in_this_model_fit, metadata.grid_id.isin(seen)
            )
            source = (
                metadata["S_candidate_context_" + scenario]
                if cohort == "four_province"
                else metadata.original_source_record_key_present
            )
            np.testing.assert_array_equal(source, subset.existing_source_context_not_true_Y)
            supported = subset.complete_dynamic_15.to_numpy()
            require(
                np.array_equal(np.isfinite(subset.xgboost_source_score_not_probability), supported),
                "No missing score filled",
            )
            count = supports.loc[supports.cohort.eq(cohort) & supports.scenario.eq(scenario)].iloc[
                0
            ]
            require(
                (count.records, count.cells, count.complete_dynamic_records, count.source_records)
                == (
                    len(metadata),
                    metadata.grid_id.nunique(),
                    int(supported.sum()),
                    int(source.sum()),
                ),
                "Independent cohort totals",
            )
            require(
                count.assessment_cells_seen_in_fit == len(set(metadata.grid_id) & seen)
                and count.assessment_cells_not_seen_in_fit == len(set(metadata.grid_id) - seen),
                "Independent cell support",
            )
            pairs = 0
            temp = subset.loc[supported].copy()
            temp["month"] = temp.prediction_timestamp_utc.str[:7]
            for _, group in temp.groupby(["grid_id", "month"]):
                s = int(group.existing_source_context_not_true_Y.sum())
                pairs += s * (len(group) - s)
            require(count.possible_comparison_pairs == pairs, "Same pair support")
    scores["month"] = scores.prediction_timestamp_utc.str[:7]
    for _, group in scores.groupby(["cohort", "scenario", "grid_id", "month"], sort=False):
        check_positions(
            group,
            "xgboost_source_score_not_probability",
            "XGBoost_position_in_available_cell_month_days",
            "XGBoost_available_days_in_cell_month",
        )
        check_positions(
            group,
            "frozen_linear_source_score_not_probability",
            "linear_position_in_available_cell_month_days",
            "linear_available_days_in_cell_month",
        )
    grouped_scores = {key: group for key, group in scores.groupby(["cohort"] + KEYS, sort=False)}
    for row in positions.itertuples(index=False):
        selected = grouped_scores[row.cohort, row.grid_id, row.prediction_timestamp_utc]
        require(len(selected) == 9, "Nine scenario records for every cohort key")
        values = selected.XGBoost_position_in_available_cell_month_days.dropna()
        require(
            row.scenarios_with_finite_score == len(values)
            and row.scenarios_with_existing_source_context
            == int(selected.existing_source_context_not_true_Y.sum()),
            "Scenario support totals",
        )
        if len(values):
            require(
                row.minimum_XGBoost_day_position == min(values)
                and row.maximum_XGBoost_day_position == max(values)
                and row.descriptive_day_position_spread_not_risk_uncertainty
                == max(values) - min(values),
                "Descriptive rank spread",
            )
        else:
            require(
                pd.isna(row.descriptive_day_position_spread_not_risk_uncertainty),
                "Missing stays missing",
            )
    require(
        all(digest(p) == sha for p, sha in pins.items()), "Original outputs unchanged during audit"
    )
    out = (
        BASE
        / "evaluation_review_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    body = {
        "status": "existing_scores_support_source_rows_and_local_positions_verified",
        "package": folder.relative_to(ROOT).as_posix(),
        "unique_feature_keys": len(features),
        "cohort_memberships": len(records),
        "shared_keys": len(shared),
        "score_rows_verified": len(scores),
        "local_position_fields_verified": len(scores) * 2,
        "new_model_or_prediction_calls": 0,
        "target_or_final_merge_acceptance": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    path = out / "readback.json"
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)


if __name__ == "__main__":
    main()
