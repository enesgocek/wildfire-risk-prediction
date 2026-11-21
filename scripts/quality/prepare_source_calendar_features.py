"""Prepare calendar X with immutable monthly checkpoints; never assign S/Y or train."""

import argparse
import csv
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from uuid import uuid4

import pandas as pd
import prepare_source_pu_feature_review as source_review

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv
from wildfire_risk_prediction.feature_readiness import inspect_day
from wildfire_risk_prediction.target_admission import specification

ROOT, BASE = source_review.ROOT, source_review.BASE
POLICY = ROOT / "configs/source_calendar_feature_preparation_v1.json"
PROPOSAL = BASE / "source_calendar_control_proposal_v1/20261121T160611Z_9e76a4ab"
PROPOSAL_SHA = "ee08ef36aefab7ae66b2c2c7ff87f0cc5d10d8d077e1cafad61c5d202ca9a6e5"
PREVIOUS = BASE / "satellite_PU_feature_review_v1/20261120T010533Z_6d61c80e"
PREVIOUS_SHA = "64262888976fe43530897f9c069eb73866dea42003ffc4fd31fcfa17ddd74138"
OUTPUT_BASE = BASE / "source_calendar_feature_review_v1"


def validate_decision(policy):
    join.require(
        policy["decision_source"]
        == "user_followup_continue_after_recommended_calendar_feature_preparation"
        and policy["calendar_feature_preparation_selected"] is True
        and policy["new_feature_extraction_authorized"] is True
        and policy["proposal_readback_sha256"] == PROPOSAL_SHA,
        "Continuation authorizes the recommended X preparation only",
    )
    join.require(
        all(
            policy[k] is False
            for k in (
                "source_conditioning_is_population_representative",
                "original_U_keys_or_weights_changed",
                "new_U_sample_or_weights_created",
                "new_S_membership_assignment_permitted",
                "accepted_L_or_Y_assignment_permitted",
                "negative_label_permitted",
                "new_model_fitting_authorized",
                "scientific_values_2023_2024_2025_read_permitted",
                "final_merge_permitted",
            )
        )
        and policy["daily_observation_status"] == "unknown"
        and policy["local_only"] is True,
        "Preparation cannot open training, labels, closed years or final merge",
    )


def save_json(path, body):
    join.require(
        not path.exists() or path.name == "runtime_progress.json",
        "Scientific receipts are immutable",
    )
    temporary = path.with_name(path.name + ".tmp_" + uuid4().hex[:8])
    temporary.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def frame_keys(frame):
    return set(frame[join.KEYS].itertuples(index=False, name=None))


def verify_frames(features, provenance, keys):
    join.require(
        features.columns.tolist() == join.KEYS + join.feature_names(), "Exactly 27 X fields"
    )
    for frame in (features, provenance):
        join.require(
            not frame.duplicated(join.KEYS).any() and frame_keys(frame) == keys,
            "Exact unique requested key universe",
        )


def seal_month(out, month, features, qa, checks, keys, source_pins):
    verify_frames(features, qa, keys)
    folder = out / "parts" / (month + "_" + uuid4().hex[:8])
    folder.mkdir(parents=True)
    artifacts = {}
    for name, frame in (("features.csv", features), ("provenance.csv", qa)):
        p = folder / name
        frame.to_csv(p, index=False)
        pd.testing.assert_frame_equal(
            frame, parse_csv(p.read_bytes()), check_dtype=False, check_exact=True
        )
        artifacts[name] = digest(p)
    receipt = {
        "status": "month_X_checkpoint_verified_not_labeled_training_data",
        "month": month,
        "rows": len(features),
        "days": len(checks),
        "daily_checks": checks,
        "source_sha256": source_pins,
        "artifact_sha256": artifacts,
    }
    save_json(folder / "receipt.json", receipt)
    return folder / "receipt.json"


def read_month(path, expected_sha, keys):
    join.require(digest(path) == expected_sha, "Immutable month receipt")
    receipt = json.loads(path.read_bytes())
    frames = []
    for name in ("features.csv", "provenance.csv"):
        p = path.parent / name
        join.require(digest(p) == receipt["artifact_sha256"][name], "Immutable month X/QA")
        frames.append(parse_csv(p.read_bytes()))
    verify_frames(*frames, keys)
    join.require(len(frames[0]) == receipt["rows"], "Checkpoint row count")
    return receipt, frames


def main(resume=None, max_minutes=15):
    started = monotonic()
    policy = json.loads(POLICY.read_bytes())
    validate_decision(policy)
    store = source_review.SOURCE_FEATURES
    pins = {
        POLICY: digest(POLICY),
        Path(__file__): digest(Path(__file__)),
        Path(source_review.__file__): digest(Path(source_review.__file__)),
        PROPOSAL / "readback.json": PROPOSAL_SHA,
        PREVIOUS / "readback.json": PREVIOUS_SHA,
        store / "readback.json": source_review.FEATURE_REPORT_SHA,
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "Frozen decisions and parents")
    for folder, names in (
        (PROPOSAL, ("proposed_calendar_keys.csv",)),
        (PREVIOUS, ("features.csv", "provenance.csv")),
        (store, ("verified_daily_files.csv", "input_manifest.json")),
    ):
        report = json.loads((folder / "readback.json").read_bytes())
        pins.update({folder / n: report["artifact_sha256"][n] for n in names})
    proposal = json.loads((PROPOSAL / "readback.json").read_bytes())
    pins.update({ROOT / p: h for p, h in proposal["input_sha256"].items()})
    original = json.loads((store / "input_manifest.json").read_bytes())
    pins[source_review.STATIC] = original[source_review.STATIC.relative_to(ROOT).as_posix()]
    for name in (
        "feature_join",
        "feature_partition",
        "feature_readiness",
        "landscape",
        "weather_policy",
    ):
        p = ROOT / f"src/wildfire_risk_prediction/{name}.py"
        pins[p] = original.get(p.relative_to(ROOT).as_posix(), digest(p))
    join.require(
        all(digest(p) == h for p, h in pins.items()), "Current source and checker identities"
    )
    metadata = parse_csv((PROPOSAL / "proposed_calendar_keys.csv").read_bytes())
    join.require(
        len(metadata) == 44082
        and metadata.target.isna().all()
        and metadata.accepted_L_membership.isna().all(),
        "Frozen unknown calendar target metadata",
    )
    keys = frame_keys(metadata)
    days, months, indexed = defaultdict(set), defaultdict(set), defaultdict(dict)
    for grid, stamp in keys:
        source_review.review_key(grid, stamp)
        join.require(
            stamp[:10] not in {"2021-12-31", "2022-12-31"},
            "Role-boundary target window stays inside",
        )
        days[stamp[:10]].add(grid)
        months[stamp[:7]].add((grid, stamp))
    with (store / "verified_daily_files.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["day"] in days:
                join.require(row["kind"] not in indexed[row["day"]], "Unique daily index parts")
                indexed[row["day"]][row["kind"]] = row
    join.require(
        set(indexed) == set(days)
        and all(set(v) == {"features", "provenance"} for v in indexed.values()),
        "Complete source day index",
    )
    frozen = {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()}
    if resume is None:
        out = OUTPUT_BASE / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
        out.mkdir(parents=True)
        save_json(out / "input_pins.json", frozen)
        progress = {"status": "running_X_preparation_only", "months": {}}
    else:
        out = resume.resolve()
        join.require(
            out.is_relative_to(OUTPUT_BASE.resolve()) and out != OUTPUT_BASE.resolve(),
            "Resume stays inside this review store",
        )
        join.require(
            json.loads((out / "input_pins.json").read_bytes()) == frozen,
            "Same producer/config/data on resume",
        )
        join.require(not (out / "readback.json").exists(), "Completed review is immutable")
        progress = json.loads((out / "runtime_progress.json").read_bytes())
    print(out.relative_to(ROOT).as_posix(), flush=True)
    static = parse_csv(source_review.STATIC.read_bytes())
    for month in sorted(months):
        if month in progress["months"]:
            item = progress["months"][month]
            receipt, _ = read_month(out / item["path"], item["sha256"], months[month])
            pins.update({ROOT / p: h for p, h in receipt["source_sha256"].items()})
            continue
        values, qa_values, checks, source_pins = [], [], [], {}
        for day in sorted(d for d in days if d.startswith(month)):
            if monotonic() - started >= max_minutes * 60:
                progress["status"] = "paused_at_local_budget_coherent_months_retained"
                save_json(out / "runtime_progress.json", progress)
                print("PAUSED partial X review; no completed dataset receipt", flush=True)
                return
            tables = {}
            for kind in ("features", "provenance"):
                entry = indexed[day][kind]
                p, full = source_review.selected_file(ROOT, entry, day, kind)
                pins[p] = entry["sha256"]
                source_pins[p.relative_to(ROOT).as_posix()] = entry["sha256"]
                tables[kind] = full.loc[full.grid_id.isin(days[day])].copy()
            checks.append(
                inspect_day(
                    tables["features"],
                    tables["provenance"],
                    sorted(days[day]),
                    day,
                    static.loc[static.grid_id.isin(days[day])],
                )
            )
            values.append(tables["features"])
            qa_values.append(tables["provenance"])
        features = (
            pd.concat(values, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
        )
        qa = pd.concat(qa_values, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
        receipt_path = seal_month(out, month, features, qa, checks, months[month], source_pins)
        progress["months"][month] = {
            "path": receipt_path.relative_to(out).as_posix(),
            "sha256": digest(receipt_path),
        }
        save_json(out / "runtime_progress.json", progress)
        print(
            "CALENDAR MONTH",
            month,
            "rows",
            len(features),
            "sealed",
            len(progress["months"]),
            "/",
            len(months),
            flush=True,
        )
    all_x, all_qa, daily_checks = [], [], []
    for month, item in sorted(progress["months"].items()):
        receipt, frames = read_month(out / item["path"], item["sha256"], months[month])
        all_x.append(frames[0])
        all_qa.append(frames[1])
        daily_checks.extend(receipt["daily_checks"])
    features = pd.concat(all_x, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
    qa = pd.concat(all_qa, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
    verify_frames(features, qa, keys)
    previous_x, previous_qa = [
        parse_csv((PREVIOUS / n).read_bytes()) for n in ("features.csv", "provenance.csv")
    ]
    common = keys & frame_keys(previous_x)
    join.require(len(common) == 1689, "Exact overlap with original reviewed features")
    for fresh, old in ((features, previous_x), (qa, previous_qa)):
        pd.testing.assert_frame_equal(
            fresh.set_index(join.KEYS).loc[sorted(common)],
            old.set_index(join.KEYS).loc[sorted(common)],
            check_exact=True,
        )
    roles = (
        metadata.rename(columns={"proposed_temporal_role": "review_temporal_role"})
        .sort_values(join.KEYS)
        .reset_index(drop=True)
    )
    roles["role_is_model_training_permission"] = False
    artifacts = {}
    snapshot = out / ("snapshot_" + uuid4().hex[:8])
    snapshot.mkdir()
    for name, frame in (
        ("features.csv", features),
        ("provenance.csv", qa),
        ("review_roles.csv", roles),
    ):
        p = snapshot / name
        join.require(not p.exists(), "Never replace final snapshot files")
        frame.to_csv(p, index=False)
        pd.testing.assert_frame_equal(
            frame, parse_csv(p.read_bytes()), check_dtype=False, check_exact=True
        )
        artifacts[p.relative_to(out).as_posix()] = digest(p)
    report = {
        "status": (
            "source_conditioned_calendar_X_time_missingness_review_complete_not_training_or_labels"
        ),
        "snapshot_directory": snapshot.name,
        "decision": policy,
        "unique_feature_keys": len(features),
        "months": len(months),
        "daily_files_verified": 2 * len(days),
        "feature_days_verified": len(days),
        "unchanged_overlapping_prior_X_and_QA_keys": len(common),
        "complete_27_features": int(features[join.feature_names()].notna().all(axis=1).sum()),
        "role_profiles": {
            role: source_review.describe(features, frame_keys(group))
            for role, group in roles.groupby("review_temporal_role", sort=True)
        },
        "daily_checks": daily_checks,
        "month_receipts": progress["months"],
        "original_U_keys_and_weights_unchanged": True,
        "new_S_Y_or_accepted_L_assignments": 0,
        "model_fitted": False,
        "publication_availability_verified": False,
        "population_representativeness_established": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": artifacts,
        "producer_sha256": digest(Path(__file__)),
    }
    join.require(
        all(digest(p) == h for p, h in pins.items()), "All consumed sources unchanged at close"
    )
    save_json(out / "readback.json", report)
    progress["status"] = "completed_X_review_only"
    save_json(out / "runtime_progress.json", progress)
    print("COMPLETE", len(features), "X keys; no S/Y, training or final merge", flush=True)
    print("readback_sha256", digest(out / "readback.json"), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--max-minutes", type=float, default=15)
    args = parser.parse_args()
    join.require(0 < args.max_minutes <= 30, "Bounded local preparation chunk")
    main(args.resume, args.max_minutes)
