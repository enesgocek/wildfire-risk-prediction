"""No-fit query inventory for a proposed nonlinear dynamic rank comparison."""

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction import ranking_queries as queries
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CONFIG = ROOT / "configs/nonlinear_rank_proposal_v1.json"
BUNDLE = BASE / "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1"
CLOSED = BASE / "experimental_SU_usability_receipt_v2/20261123T130043Z_0563772d/readback.json"
LINEAR = BASE / "temporal_pairwise_run_v1/20261121T174415Z_5a77b21e"
MERSIN = BASE / "cross_source_calendar_feature_review_v1/20261121T180737Z_c322d93c"


def validate_policy(policy):
    require(
        policy["status"] == "proposed_not_training_authorization"
        and policy["new_models_proposed"] == 9
        and policy["objective"] == "rank:pairwise"
        and policy["fit_years_proposed"] == [2018, 2019, 2020, 2021]
        and policy["exploratory_assessment_year_proposed"] == 2022,
        "No-fit proposal for existing pilot roles",
    )
    require(
        all(
            policy[k] is False
            for k in (
                "new_training_authorized",
                "closed_year_values_read_authorized",
                "true_Y_or_accepted_L_authorized",
                "negative_label_permitted",
                "main_PU_method_accepted",
                "risk_probabilities_or_validated_colors_authorized",
                "final_merge_authorized",
            )
        ),
        "Preparation does not grant execution or scientific acceptance",
    )


def main():
    proposal = json.loads(CONFIG.read_bytes())
    validate_policy(proposal)
    pins = {
        CONFIG: digest(CONFIG),
        Path(queries.__file__): digest(Path(queries.__file__)),
        BUNDLE
        / "readback.json": "86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366",
        CLOSED: "8dbadb81ebfd4537f620d8a571a46523c5e593cbd49ac6d68ec5665379978d06",
        LINEAR
        / "readback.json": "b8e847f8d510721ce84b788161ae40ac5f3bfa098154b0e56a013fc380f83d82",
        MERSIN
        / "readback.json": "d32b99e6581c6a2412ba6013af727d4220d19d8e2d03666f8ebb48634d3ce0f6",
    }
    require(
        all(digest(p) == h for p, h in pins.items()),
        "Exact closed package and existing model references",
    )
    reports = {p: json.loads((p / "readback.json").read_bytes()) for p in (BUNDLE, LINEAR, MERSIN)}
    for folder, names in (
        (BUNDLE, ["features.csv", "inspection_memberships.csv"]),
        (
            MERSIN,
            [
                reports[MERSIN]["snapshot_directory"] + "/features.csv",
                reports[MERSIN]["snapshot_directory"] + "/review_roles.csv",
            ],
        ),
    ):
        for name in names:
            pins[folder / name] = reports[folder]["artifact_sha256"][name]
    require(all(digest(p) == h for p, h in pins.items()), "Unchanged existing X and proposal flags")
    x = pd.read_csv(BUNDLE / "features.csv", float_precision="round_trip")
    meta = pd.read_csv(BUNDLE / "inspection_memberships.csv")
    pd.testing.assert_frame_equal(x[KEYS], meta[KEYS], check_exact=True)
    require(len(x) == 44082 and len(queries.DYNAMIC_FEATURES) == 15, "Exact existing 44082 X keys")
    complete = x[queries.DYNAMIC_FEATURES].notna().all(axis=1).to_numpy()
    old = {r["scenario"]: r for r in reports[LINEAR]["scenario_summaries"]}
    summaries, inventories = [], []
    for scenario in sorted(old):
        table = queries.query_inventory(
            meta, meta["S_candidate_context_" + scenario].to_numpy(), complete
        )
        table.insert(0, "scenario", scenario)
        inventories.append(table)
        fit = table.loc[table.pilot_role.eq("proposed_fit_2018_2021")]
        held = table.loc[table.pilot_role.eq("proposed_assessment_2022")]
        fit_pairs, held_pairs = (
            int(fit.possible_cross_context_pairs.sum()),
            int(held.possible_cross_context_pairs.sum()),
        )
        require(
            fit_pairs == old[scenario]["fit_pairs"]
            and held_pairs
            == old[scenario]["comparison_same_complete_dynamic_pairs"]["pairwise_linear"]["pairs"],
            "Same potential pair counts as frozen linear comparison",
        )
        summaries.append(
            {
                "scenario": scenario,
                "complete_fit_calendar_rows": int(fit.complete_dynamic_rows.sum()),
                "informative_fit_rows": int(
                    fit.loc[fit.informative_for_ordering].complete_dynamic_rows.sum()
                ),
                "informative_fit_queries": int(fit.informative_for_ordering.sum()),
                "fit_source_context_rows": int(fit.source_context_rows.sum()),
                "fit_possible_cross_context_pairs": fit_pairs,
                "complete_2022_assessment_rows": int(held.complete_dynamic_rows.sum()),
                "assessment_possible_cross_context_pairs": held_pairs,
                "maximum_query_complete_rows": int(table.complete_dynamic_rows.max()),
            }
        )
    source = MERSIN / reports[MERSIN]["snapshot_directory"]
    mx, mm = [
        pd.read_csv(source / name, float_precision="round_trip")
        for name in ("features.csv", "review_roles.csv")
    ]
    pd.testing.assert_frame_equal(mx[KEYS], mm[KEYS], check_exact=True)
    mm["review_temporal_role"] = "proposed_assessment_2022"
    mersin_queries = queries.query_inventory(
        mm,
        mm.original_source_record_key_present.to_numpy(),
        mx[queries.DYNAMIC_FEATURES].notna().all(axis=1).to_numpy(),
    )
    require(
        int(mersin_queries.possible_cross_context_pairs.sum()) == 2329,
        "Same existing separate Mersin calendar",
    )
    require(all(digest(p) == h for p, h in pins.items()), "Original data and models unchanged")
    out = (
        BASE
        / "nonlinear_rank_preparation_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    pd.DataFrame(summaries).to_csv(out / "scenario_support.csv", index=False)
    pd.concat(inventories, ignore_index=True).to_csv(out / "query_inventory.csv", index=False)
    mersin_queries.to_csv(out / "separate_Mersin_query_inventory.csv", index=False)
    (out / "dynamic_features.json").write_text(
        json.dumps(queries.DYNAMIC_FEATURES, indent=2) + "\n"
    )
    body = {
        "status": "nonlinear_dynamic_rank_proposal_and_query_support_prepared_no_fit",
        "proposal": proposal,
        "input_calendar_keys": len(x),
        "features": queries.DYNAMIC_FEATURES,
        "scenario_support": summaries,
        "existing_separate_Mersin_rows": len(mx),
        "existing_separate_Mersin_complete_rows": int(mersin_queries.complete_dynamic_rows.sum()),
        "existing_separate_Mersin_possible_pairs": int(
            mersin_queries.possible_cross_context_pairs.sum()
        ),
        "xgboost_installed": importlib.util.find_spec("xgboost") is not None,
        "packages_installed_or_downloaded": False,
        "new_models_or_scores_created": 0,
        "true_Y_or_accepted_L_created": 0,
        "closed_year_values_opened": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)
    print(pd.DataFrame(summaries).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
