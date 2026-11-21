"""Quantify a proposed within-grid calendar control; no new X, U sample, labels or fitting."""

import calendar
import csv
import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
POLICY = ROOT / "configs/source_calendar_control_proposal_v1.json"
PROPOSALS = BASE / "satellite_PU_L_proposals_v1/20261120T005519Z_62f3f815"
PROPOSALS_SHA = "679a5ad9eab6342fa153c46cbbcc8f1e494b92256b592ba84f24823d0c0a4a85"
FEATURES = BASE / "satellite_PU_feature_review_v1/20261120T010533Z_6d61c80e"
FEATURES_SHA = "64262888976fe43530897f9c069eb73866dea42003ffc4fd31fcfa17ddd74138"
U = BASE / "noisy_positive_pu_pilot_v1/20261119T121014Z_122b22c7/U_key_sample.csv"
U_SHA = "fd77c27454083e45f625e7e94ef0a14e5ace7d65636cace59b92261666c4d19f"
INDEX = BASE / "waiting_features_v1/20261017T010902Z_2aa6320b/verified_daily_files.csv"
INDEX_SHA = "fcc2be794e41707271d4423fba113a2660f7625a131f9c075682999400509783"


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def key(row):
    return row["grid_id"], row["prediction_timestamp_utc"]


def validate_policy(policy):
    require(
        all(
            policy[name] is False
            for name in (
                "exclude_days_because_a_candidate_or_detection_exists",
                "source_conditioning_makes_this_a_population_representative_U_sample",
                "source_conditioned_calendar_is_an_operational_or_blind_test",
                "original_2048_U_keys_or_design_weights_changed",
                "method_direction_selected",
                "new_feature_extraction_authorized",
                "new_model_fitting_authorized",
                "accepted_L_or_Y_assignment_permitted",
                "negative_label_permitted",
                "final_merge_permitted",
                "scientific_values_2023_2024_2025_read_permitted",
            )
        )
        and policy["daily_observation_status"] == "unknown",
        "This is an unselected metadata proposal; no scientific admission",
    )


def calendar_keys(anchors):
    strata = set()
    for grid, value in anchors:
        t = datetime.fromisoformat(value)
        require(
            isinstance(grid, str)
            and grid
            and t.tzinfo is not None
            and t.utcoffset() == timedelta(0)
            and t.time().replace(tzinfo=None) == datetime.min.time()
            and 2018 <= t.year <= 2022,
            "Only 2018-2022 midnight UTC anchor metadata",
        )
        strata.add((grid, t.year, t.month))
    result = {}
    for grid, year, month in strata:
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            t = datetime(year, month, day, tzinfo=UTC)
            limit = datetime(2022 if year <= 2021 else 2023, 1, 1, tzinfo=UTC)
            if t + timedelta(days=1) < limit:
                result[(grid, t.isoformat())] = (
                    "proposed_fit_2018_2021" if year <= 2021 else "proposed_assessment_2022"
                )
    return result, strata


def main():
    pins = {
        POLICY: digest(POLICY),
        PROPOSALS / "readback.json": PROPOSALS_SHA,
        FEATURES / "readback.json": FEATURES_SHA,
        U: U_SHA,
        INDEX: INDEX_SHA,
    }
    require(
        all(digest(p) == h for p, h in pins.items()), "Frozen proposal, X keys, U and file index"
    )
    policy = json.loads(POLICY.read_bytes())
    validate_policy(policy)
    for folder, names in (
        (PROPOSALS, ("proposal_key_union.csv",)),
        (FEATURES, ("review_roles.csv",)),
    ):
        report = json.loads((folder / "readback.json").read_bytes())
        pins.update({folder / name: report["artifact_sha256"][name] for name in names})
    require(all(digest(p) == h for p, h in pins.items()), "Exact metadata snapshots")
    proposed = read_rows(PROPOSALS / "proposal_key_union.csv")
    require(
        len(proposed) == 1670
        and all(not r["target"] and not r["accepted_L_membership"] for r in proposed),
        "Unaccepted proposal anchors",
    )
    anchors = {key(row) for row in proposed}
    universe, strata = calendar_keys(anchors)
    require(anchors <= set(universe), "All actual proposal keys retained in the calendar proposal")
    old_u = {key(r) for r in read_rows(U)}
    existing_x = {key(r) for r in read_rows(FEATURES / "review_roles.csv")}
    require(
        len(old_u) == 2048 and len(existing_x) == 3718, "Unchanged original U and X key snapshots"
    )
    days = {value[:10] for grid, value in universe}
    indexed = [r for r in read_rows(INDEX) if r["day"] in days]
    require(
        len(indexed) == 2 * len(days)
        and {(r["day"], r["kind"]) for r in indexed}
        == {(d, k) for d in days for k in ("features", "provenance")},
        "Both indexed parts for every proposed day",
    )
    for row in indexed:
        p = ROOT / row["path"]
        require(
            p.resolve().is_relative_to(ROOT / "outputs/reports/dataset")
            and p.is_file()
            and p.stat().st_size == int(row["bytes"]),
            "Local daily file presence/size only; no new content read",
        )
    out = (
        BASE
        / "source_calendar_control_proposal_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    columns = (
        "grid_id",
        "prediction_timestamp_utc",
        "proposed_temporal_role",
        "known_proposal_key_in_union",
        "original_U_sample_key_present",
        "previous_feature_review_key_present",
        "target",
        "accepted_L_membership",
        "daily_observation_status",
    )
    p = out / "proposed_calendar_keys.csv"
    with p.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for (grid, value), role in sorted(universe.items()):
            k = (grid, value)
            writer.writerow(
                {
                    "grid_id": grid,
                    "prediction_timestamp_utc": value,
                    "proposed_temporal_role": role,
                    "known_proposal_key_in_union": k in anchors,
                    "original_U_sample_key_present": k in old_u,
                    "previous_feature_review_key_present": k in existing_x,
                    "target": "",
                    "accepted_L_membership": "",
                    "daily_observation_status": "unknown",
                }
            )
    restored = read_rows(p)
    require(
        len(restored) == len(universe) and {key(r) for r in restored} == set(universe),
        "Exact metadata CSV key readback",
    )
    require(
        all(
            not r["target"]
            and not r["accepted_L_membership"]
            and r["daily_observation_status"] == "unknown"
            for r in restored
        ),
        "No Y, L or observation admission",
    )
    report = {
        "status": "source_conditioned_calendar_extent_proposed_not_selected_or_feature_accepted",
        "decision": policy,
        "calendar_grid_year_month_strata": len(strata),
        "possible_proposal_anchor_keys": len(anchors),
        "proposed_calendar_keys": len(universe),
        "temporal_role_counts": dict(Counter(universe.values())),
        "year_key_counts": dict(sorted(Counter(t[:4] for g, t in universe).items())),
        "original_U_keys_retained_in_parent": 2048,
        "original_U_keys_also_in_proposed_calendar": len(old_u & set(universe)),
        "already_feature_reviewed_keys_in_proposed_calendar": len(existing_x & set(universe)),
        "additional_X_key_reviews_if_selected": len(set(universe) - existing_x),
        "distinct_feature_days_if_selected": len(days),
        "indexed_daily_files_present": len(indexed),
        "indexed_source_bytes_upper_bound_if_all_days_read": sum(int(r["bytes"]) for r in indexed),
        "daily_file_contents_rehashed_or_parsed_in_this_proposal": False,
        "new_X_extracted": False,
        "new_U_sample_or_weights_created": False,
        "new_models_fitted": 0,
        "Y_or_accepted_L_created": 0,
        "final_merge_performed": False,
        "source_conditioned_selection_is_a_population_or_operational_test": False,
        "artifact_sha256": {p.name: digest(p)},
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    require(all(digest(p) == h for p, h in pins.items()), "Original metadata unchanged")
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)
    print(
        "proposed_calendar_keys",
        len(universe),
        "additional_X_key_reviews",
        report["additional_X_key_reviews_if_selected"],
        flush=True,
    )
    print("PROPOSAL ONLY; no new X, U population, labels, fitting or final merge", flush=True)


if __name__ == "__main__":
    main()
