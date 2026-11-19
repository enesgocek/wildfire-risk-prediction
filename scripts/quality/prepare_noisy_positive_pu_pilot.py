"""Prepare review-only L ambiguity and uniform U key tables; never fit a PU model."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
POLICY = ROOT / "configs/noisy_positive_pu_pilot_v1.json"
SCOPE = ROOT / "configs/cell_scope_direction_v1.json"
ROLES = ROOT / "configs/imbalance_calibration_plan_v1.json"
WATER = BASE / "water_scope_v1/20261014T185242Z_f2e469bd/readback.json"
WATER_SHA = "7b5d296bae6c3744790817409db4bce3a947e92919a06abde9271eac07814cae"
PREFIX = BASE / "salur_prefix_quality_v1/20261119T120007Z_42e00153/readback.json"
PREFIX_SHA = "69c361554207695fbaa20d28a46ee04372860dbdf0ad4635ee8e5c98ac3f716c"
METHOD = BASE / "noisy_positive_pu_review_v1/20261119T120556Z_7e0c19bb/readback.json"
METHOD_SHA = "3b7b785f9363f91b903f34358d9cdba59cee1b187daf7e604ddf4877b2c012ad"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    require(not path.exists(), "No output overwrite")
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    require(json.loads(path.read_text()) == value, "JSON readback")


def main():
    pins = {WATER: WATER_SHA, PREFIX: PREFIX_SHA, METHOD: METHOD_SHA}
    require(all(sha(p) == h for p, h in pins.items()), "Pinned source reports")
    policy, scope, roles = [json.loads(p.read_text()) for p in (POLICY, SCOPE, ROLES)]
    pins.update({p: sha(p) for p in (POLICY, SCOPE, ROLES)})
    require(
        policy["version"] == "noisy_positive_pu_pilot_v1"
        and policy["decision_source"]
        == "explicit_user_selection_A_prepare_noisy_positive_PU_feasibility_pilot",
        "Research direction, not training approval",
    )
    require(
        scope["candidate_cells_retained"] == policy["candidate_cells"] == 2889
        and not scope["fraction_cut_applied"],
        "Same mixed-cell population",
    )
    require(
        roles["data_role_direction"] == "fit_2018_2022_calibration_2023_selection_2024",
        "Existing data roles",
    )
    for k in (
        "method_accepted",
        "positive_label_permitted",
        "negative_label_permitted",
        "training_authorized",
        "model_ready",
        "final_merge_permitted",
        "2023_calibration_values_read_permitted",
        "2024_comparison_values_read_permitted",
        "2025_final_values_read_permitted",
    ):
        require(policy[k] is False, "No scientific execution or heldout access approval")
    require(policy["daily_observation_status"] == "unknown", "Observation state")
    water = json.loads(WATER.read_text())
    csv = WATER.parent / "grid_water_scope.csv"
    pins[csv] = water["artifact_sha256"][csv.name]
    require(sha(csv) == pins[csv], "Retained water scope table")
    cells = pd.read_csv(csv)
    require(
        cells.grid_id.is_unique and len(cells) == 2899 and cells.water_scope_included.dtype == bool,
        "Cell keys",
    )
    grids = sorted(cells.loc[cells.water_scope_included, "grid_id"])
    require(len(grids) == 2889, "No extra minimum cover cut")
    sampling = policy["U_sampling"]
    require(
        not any(
            sampling[k]
            for k in (
                "filter_on_fire_records",
                "filter_on_observation_coverage",
                "remove_candidate_L_overlaps",
                "unknown_rows_are_negative",
                "size_is_statistical_sufficiency_claim",
            )
        ),
        "No outcome/coverage-based U selection",
    )
    require(
        sampling["sample_count"] == 2048 and sampling["seed"] == 20261119,
        "Bounded preparation design",
    )
    dates = pd.date_range(sampling["start_T_utc"], sampling["end_T_utc_inclusive"], freq="D")
    endpoints = pd.to_datetime(dates.as_unit("ns").asi8 + 86_400_000_000_000, unit="ns", utc=True)
    require(
        len(dates) == 1825
        and (endpoints < pd.Timestamp(sampling["all_target_endpoints_strictly_before"])).all(),
        "All endpoints before calibration, including right-closed midnight",
    )
    require(dates.year.min() == 2018 and dates.year.max() == 2022, "Fit-role metadata only")
    population = len(grids) * len(dates)
    require(population == 5272425, "Declared finite review population")

    def sample():
        rng = np.random.Generator(np.random.PCG64(sampling["seed"]))
        return np.sort(rng.choice(population, size=sampling["sample_count"], replace=False))

    indices = sample()
    require(
        np.array_equal(indices, sample()) and len(np.unique(indices)) == len(indices),
        "Deterministic sampling without replacement",
    )
    u = pd.DataFrame(
        {
            "population_index": indices,
            "grid_id": np.asarray(grids)[indices // len(dates)],
            "prediction_timestamp_utc": dates[indices % len(dates)].map(pd.Timestamp.isoformat),
        }
    )
    u["target_end_inclusive_utc"] = endpoints[indices % len(dates)].map(pd.Timestamp.isoformat)
    u["review_role"] = "U_unknown_not_negative"
    u["sampling_probability"] = len(indices) / population
    u["sampling_weight"] = population / len(indices)
    u["daily_observation_status"] = "unknown"
    u["target"] = float("nan")
    require(not u.duplicated(["grid_id", "prediction_timestamp_utc"]).any(), "Unique U keys")
    prefix = json.loads(PREFIX.read_text())
    first_cells = prefix["summary"]["catalog_first_cells"]
    require(
        len(first_cells) == 4 and set(first_cells) <= set(grids), "Preserved four-cell ambiguity"
    )
    require(
        policy["candidate_L"]["mapping"]
        == "four_first_cells_one_ambiguity_set_no_cell_label_assigned"
        and not policy["candidate_L"]["candidate_set_membership_accepted"],
        "No selected L membership yet",
    )
    candidate = pd.DataFrame({"source_case_id": ["salur_2021_07_28"] * 4, "grid_id": first_cells})
    candidate["prediction_timestamp_utc"] = "2021-07-28T00:00:00+00:00"
    candidate["target_end_inclusive_utc"] = "2021-07-29T00:00:00+00:00"
    candidate["reference_marker_cell_match"] = candidate.grid_id.eq("E6933_5K_V1_C605_R879")
    candidate["first_prefix_native_centers"] = candidate.grid_id.map(prefix["counts_by_cell"])
    candidate["review_role"] = "L_membership_ambiguity_review_not_assigned"
    candidate["independent_positive_label"] = False
    candidate["target"] = float("nan")
    require(
        candidate.first_prefix_native_centers.sum() == 74
        and candidate.source_case_id.nunique() == 1,
        "One case, not four fires or 74 positives",
    )
    overlaps = u.merge(
        candidate[["grid_id", "prediction_timestamp_utc"]],
        on=["grid_id", "prediction_timestamp_utc"],
        how="inner",
    )
    out = (
        BASE
        / "noisy_positive_pu_pilot_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (("U_key_sample.csv", u), ("L_case_cell_ambiguity.csv", candidate)):
        path = out / name
        frame.to_csv(path, index=False, mode="x")
        pd.testing.assert_frame_equal(frame, pd.read_csv(path), check_dtype=False)
        require(pd.read_csv(path).target.isna().all(), "No labels in review tables")
        artifacts[name] = sha(path)
    blockers = [
        "Case-to-cell L membership and event novelty not scientifically admitted",
        "One source case, not an independent positive cohort",
        "Positive enrichment and shared class-conditional selection remain unsupported",
        "Semantic class identifiability or justified alpha/beta bounds remain open",
        "Native quality warnings are not label-noise measurements",
        "Fold-specific missingness, feature availability and evaluation protocol "
        "required before fitting",
    ]
    result = {
        "status": "review_inputs_prepared_estimation_not_authorized",
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "script_sha256": sha(Path(__file__)),
        "numpy_version": np.__version__,
        "artifact_sha256": artifacts,
        "U_population_cell_days": population,
        "U_sample_rows": len(u),
        "U_year_counts": pd.to_datetime(u.prediction_timestamp_utc)
        .dt.year.value_counts()
        .sort_index()
        .to_dict(),
        "candidate_L_cases": 1,
        "candidate_L_cell_possibilities": 4,
        "candidate_L_membership_assigned": False,
        "candidate_L_U_key_overlaps": len(overlaps),
        "overlaps_silently_removed": False,
        "sampling_uses_detection_or_quality_values": False,
        "sample_size_claims_statistical_sufficiency": False,
        "estimation_blockers": blockers,
        "source_noise_or_prior_estimated": False,
        "gate": specification(),
        "feature_values_joined": False,
        "labels_created": False,
        "model_trained": False,
        "calibrator_fitted": False,
        "final_merge_performed": False,
        "heldout_values_read": False,
    }
    result = json.loads(json.dumps(result))
    require(all(sha(p) == h for p, h in pins.items()), "Input closure")
    write_json(out / "readback.json", result)
    print((out / "readback.json").relative_to(ROOT), sha(out / "readback.json"))
    print(
        "PASS uniform U key sample and one unresolved four-cell case; "
        "no labels, features or fitting"
    )


if __name__ == "__main__":
    main()
