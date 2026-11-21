"""Read fitted temporal pilot artifacts separately; never refit or accept real fire labels."""

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import KEYS, require
from wildfire_risk_prediction.feature_partition import parse_csv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CALENDAR = BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896"
PROPOSALS = BASE / "satellite_PU_L_proposals_v1/20261120T005519Z_62f3f815"
FIT = "proposed_fit_2018_2021"
HELD = "proposed_assessment_2022"


def independent_pairs(metadata, valid, source, role):
    groups = defaultdict(lambda: [[], []])
    for i, row in enumerate(metadata.to_dict("records")):
        if row["review_temporal_role"] == role and valid[i]:
            key = tuple(row[k] for k in KEYS)
            groups[(key[0], key[1][:7])][0 if key in source else 1].append(i)
    return {(a, b) for positive, other in groups.values() for a in positive for b in other}


def independent_credit(scores, pairs):
    doubled = sum(
        2 if scores[a] > scores[b] else 1 if scores[a] == scores[b] else 0 for a, b in pairs
    )
    return doubled / (2 * len(pairs))


def main(run):
    require(run.parent == BASE / "temporal_pairwise_run_v1", "Local temporal pilot folder")
    report = json.loads((run / "readback.json").read_bytes())
    require(
        report["new_models_fitted"] == 9 and report["true_Y_or_accepted_L_created"] == 0,
        "Exactly auxiliary A pilot",
    )
    pins = {run / "readback.json": digest(run / "readback.json")}
    pins.update({ROOT / p: h for p, h in report["input_sha256"].items()})
    pins.update({run / p: h for p, h in report["artifact_sha256"].items()})
    require(all(digest(p) == h for p, h in pins.items()), "Current trusted artifacts and producers")
    calendar = json.loads((CALENDAR / "readback.json").read_bytes())
    snapshot = CALENDAR / calendar["snapshot_directory"]
    x = parse_csv((snapshot / "features.csv").read_bytes())
    metadata = parse_csv((snapshot / "review_roles.csv").read_bytes())
    pd.testing.assert_frame_equal(x[KEYS], metadata[KEYS], check_exact=True)
    proposals = parse_csv((PROPOSALS / "all_first_cells_with_proposal_flags.csv").read_bytes())
    proposals = proposals.loc[proposals.possible_L_proposal]
    checks = []
    for summary in report["scenario_summaries"]:
        scenario = summary["scenario"]
        folder = run / scenario
        saved = joblib.load(folder / "pairwise_linear.joblib")
        model, scaler, names = saved["model"], saved["scaler"], saved["retained_features"]
        state = joblib.hash(saved)
        valid = np.isfinite(x[names].to_numpy()).all(axis=1)
        fit_indices = np.flatnonzero(metadata.review_temporal_role.eq(FIT).to_numpy() & valid)
        np.testing.assert_array_equal(saved["fit_scaler_calendar_rows"], fit_indices)
        fit_x = x.loc[fit_indices, names].to_numpy()
        np.testing.assert_allclose(scaler.mean_, np.mean(fit_x, axis=0), rtol=1e-10, atol=1e-10)
        scale = np.std(fit_x, axis=0)
        scale[scale == 0] = 1
        np.testing.assert_allclose(scaler.scale_, scale, rtol=1e-10, atol=1e-10)
        require(
            not model.fit_intercept
            and model.C == 1
            and model.n_iter_[0] < 1000
            and model.coef_.shape == (1, 15),
            "Fixed converged linear model and dynamic feature count",
        )
        values = (x[names].to_numpy() - scaler.mean_) / scaler.scale_
        scores = values @ model.coef_[0]
        np.testing.assert_allclose(
            model.decision_function(values[valid]), scores[valid], rtol=1e-12, atol=1e-12
        )
        held_indices = np.flatnonzero(metadata.review_temporal_role.eq(HELD))
        frame = parse_csv((folder / "assessment_scores.csv").read_bytes())
        pd.testing.assert_frame_equal(
            frame[KEYS], metadata.loc[held_indices, KEYS].reset_index(drop=True), check_exact=True
        )
        require(
            frame.true_Y.isna().all()
            and frame.accepted_L_membership.isna().all()
            and frame.daily_observation_status.eq("unknown").all(),
            "Real target and daily observation remain unknown",
        )
        np.testing.assert_array_equal(frame.dynamic_15_complete, valid[held_indices])
        np.testing.assert_allclose(
            frame.temporal_pairwise_linear_score_not_probability,
            scores[held_indices],
            rtol=1e-12,
            atol=1e-12,
            equal_nan=True,
        )
        source = set(
            proposals.loc[proposals.scenario.eq(scenario), KEYS].itertuples(index=False, name=None)
        )
        for role, filename in (
            (FIT, "fit_pair_indices.csv"),
            (HELD, "assessment_pair_indices.csv"),
        ):
            expected = independent_pairs(metadata, valid, source, role)
            pairs = parse_csv((folder / filename).read_bytes())
            actual = set(pairs.itertuples(index=False, name=None))
            require(
                actual == expected and len(actual) == len(pairs),
                "Independent exact role/grid/month/source/quality pair identities",
            )
            if role == HELD:
                for variant, recorded in summary["comparison_same_complete_dynamic_pairs"].items():
                    if variant == "pairwise_linear":
                        vector = np.full(len(x), np.nan)
                        vector[held_indices] = frame.temporal_pairwise_linear_score_not_probability
                    else:
                        column = variant.removeprefix("fixed_") + "_auxiliary_source_score"
                        vector = np.full(len(x), np.nan)
                        vector[held_indices] = frame[column]
                    value = independent_credit(vector, expected)
                    require(
                        len(expected) == recorded["pairs"]
                        and value == recorded["auxiliary_pair_AUC"],
                        "Independent scalar matched score credit",
                    )
        require(joblib.hash(saved) == state, "Audit does not update fitted state")
        checks.append(
            {
                "scenario": scenario,
                "scaler_unique_fit_rows": len(fit_indices),
                "complete_assessment_rows": int(valid[held_indices].sum()),
                "fit_pairs_rechecked": summary["fit_pairs"],
                "assessment_pairs_rechecked": len(expected),
                "metric_checks": 4,
                "model_and_linear_scores_verified": True,
            }
        )
    require(
        len(checks) == 9 and all(digest(p) == h for p, h in pins.items()),
        "All nine checks and unchanged inputs",
    )
    out = (
        BASE
        / "temporal_pairwise_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    result = {
        "status": "nine_pairwise_models_scalers_pair_identities_scores_and_36_metrics_rechecked",
        "parent_readback": (run / "readback.json").relative_to(ROOT).as_posix(),
        "parent_readback_sha256": digest(run / "readback.json"),
        "scenario_checks": checks,
        "new_models_fitted": 0,
        "true_fire_validation_established": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(p), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    main(parser.parse_args().run.resolve())
