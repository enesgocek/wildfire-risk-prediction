"""Prepare explicitly chosen 2022 source-calendar X with immutable monthly receipts."""

import argparse
import csv
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from uuid import uuid4

import pandas as pd
import prepare_source_calendar_features as checkpoints
import prepare_source_pu_feature_review as source_review

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv
from wildfire_risk_prediction.feature_readiness import inspect_day

ROOT, BASE = source_review.ROOT, source_review.BASE
CONFIG = ROOT / "configs/cross_source_calendar_execution_v1.json"
PROPOSAL = BASE / "cross_source_calendar_support_v1/20261121T175954Z_4ad955e7"
PROPOSAL_SHA = "07c0430bba04db18303767882fd5bdf9eae1f1233f7743977c90d48bd10dbfb7"
OLD = BASE / "source_pu_feature_review_v1/20261119T210151Z_3e99d4a1"
CALENDAR = BASE / "source_calendar_feature_review_v1/20261121T164603Z_741c2896"
PARTITION = BASE / "conditional_rank_partition_v1/20261119T210609Z_511e5d9f"
OUTPUT = BASE / "cross_source_calendar_feature_review_v1"


def validate(config):
    join.require(
        config["decision_source"]
        == "researcher_explicit_A_separate_Mersin_calendar_and_fixed_model_diagnostic"
        and config["proposal_sha256"] == PROPOSAL_SHA
        and config["calendar_keys"] == 2383
        and config["exploratory_year"] == 2022
        and config["local_chunk_limit_seconds"] == 900
        and config["local_X_preparation_authorized"] is True,
        "Explicit separate-source calendar A scope",
    )
    join.require(
        all(
            config[k] is False
            for k in (
                "new_model_fitting_authorized",
                "original_U_or_weights_changed",
                "new_Y_or_accepted_L_authorized",
                "negative_label_permitted",
                "scientific_values_2023_2024_2025_read_permitted",
                "download_or_cloud_permitted",
                "risk_probability_or_validated_colors_authorized",
                "final_merge_permitted",
            )
        )
        and config["daily_observation_status"] == "unknown",
        "No new fit, true labels, closed years or final merge",
    )


def main(resume=None):
    start = monotonic()
    config = json.loads(CONFIG.read_bytes())
    validate(config)
    store = source_review.SOURCE_FEATURES
    pins = {
        CONFIG: digest(CONFIG),
        Path(__file__): digest(Path(__file__)),
        Path(checkpoints.__file__): digest(Path(checkpoints.__file__)),
        Path(source_review.__file__): digest(Path(source_review.__file__)),
        PROPOSAL / "readback.json": PROPOSAL_SHA,
        store / "readback.json": source_review.FEATURE_REPORT_SHA,
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "Choice and prepared metadata")
    proposal = json.loads((PROPOSAL / "readback.json").read_bytes())
    pins.update({ROOT / p: h for p, h in proposal["input_sha256"].items()})
    pins.update({PROPOSAL / p: h for p, h in proposal["artifact_sha256"].items()})
    store_report = json.loads((store / "readback.json").read_bytes())
    for name in ("verified_daily_files.csv", "input_manifest.json"):
        pins[store / name] = store_report["artifact_sha256"][name]
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
        all(digest(p) == h for p, h in pins.items()),
        "Current source, prior X and checker identities",
    )
    requested = parse_csv((PROPOSAL / "proposed_2022_source_calendar_keys.csv").read_bytes())
    keys = checkpoints.frame_keys(requested)
    join.require(len(keys) == len(requested) == 2383, "Unique proposed 2383 keys")
    days, months = defaultdict(set), defaultdict(set)
    for grid, stamp in keys:
        source_review.review_key(grid, stamp)
        join.require(
            stamp.startswith("2022-") and stamp[:10] != "2022-12-31",
            "Only 2022 and target before 2023",
        )
        days[stamp[:10]].add(grid)
        months[stamp[:7]].add((grid, stamp))
    indexed = defaultdict(dict)
    with (store / "verified_daily_files.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["day"] in days:
                join.require(row["kind"] not in indexed[row["day"]], "Unique daily part index")
                indexed[row["day"]][row["kind"]] = row
    join.require(
        set(indexed) == set(days)
        and all(set(v) == {"features", "provenance"} for v in indexed.values()),
        "Complete local day index",
    )
    frozen = {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()}
    if resume is None:
        out = OUTPUT / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
        out.mkdir(parents=True)
        checkpoints.save_json(out / "input_pins.json", frozen)
        progress = {"status": "running_cross_source_X_only", "months": {}}
    else:
        out = resume.resolve()
        join.require(
            out.parent == OUTPUT.resolve() and not (out / "readback.json").exists(),
            "Incomplete same-store resume only",
        )
        join.require(
            json.loads((out / "input_pins.json").read_bytes()) == frozen,
            "Unchanged producer, decision and parent files",
        )
        progress = json.loads((out / "runtime_progress.json").read_bytes())
    print(out.relative_to(ROOT).as_posix(), flush=True)
    static = parse_csv(source_review.STATIC.read_bytes())
    for month in sorted(months):
        if month in progress["months"]:
            item = progress["months"][month]
            receipt, _ = checkpoints.read_month(out / item["path"], item["sha256"], months[month])
            pins.update({ROOT / p: h for p, h in receipt["source_sha256"].items()})
            continue
        values, qa, checks, source_pins = [], [], [], {}
        for day in sorted(d for d in days if d.startswith(month)):
            if monotonic() - start >= 900:
                progress["status"] = "paused_local_chunk_immutable_months_retained"
                checkpoints.save_json(out / "runtime_progress.json", progress)
                print("PAUSED; no completed review accepted", flush=True)
                return
            tables = {}
            for kind in ("features", "provenance"):
                entry = indexed[day][kind]
                p, frame = source_review.selected_file(ROOT, entry, day, kind)
                pins[p] = entry["sha256"]
                source_pins[p.relative_to(ROOT).as_posix()] = entry["sha256"]
                tables[kind] = frame.loc[frame.grid_id.isin(days[day])].copy()
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
            qa.append(tables["provenance"])
        x = pd.concat(values, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
        q = pd.concat(qa, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
        receipt = checkpoints.seal_month(out, month, x, q, checks, months[month], source_pins)
        progress["months"][month] = {
            "path": receipt.relative_to(out).as_posix(),
            "sha256": digest(receipt),
        }
        checkpoints.save_json(out / "runtime_progress.json", progress)
        print("MERSIN CALENDAR MONTH", month, "rows", len(x), "sealed", flush=True)
    values, qa, checks = [], [], []
    for month, item in sorted(progress["months"].items()):
        receipt, frames = checkpoints.read_month(out / item["path"], item["sha256"], months[month])
        values.append(frames[0])
        qa.append(frames[1])
        checks.extend(receipt["daily_checks"])
    x = pd.concat(values, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
    q = pd.concat(qa, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
    checkpoints.verify_frames(x, q, keys)
    common_union, common_counts = set(), {}
    cal_report = json.loads((CALENDAR / "readback.json").read_bytes())
    for folder in (OLD, CALENDAR / cal_report["snapshot_directory"]):
        old_x, old_q = [
            parse_csv((folder / name).read_bytes()) for name in ("features.csv", "provenance.csv")
        ]
        common = keys & checkpoints.frame_keys(old_x)
        for fresh, prior in ((x, old_x), (q, old_q)):
            pd.testing.assert_frame_equal(
                fresh.set_index(join.KEYS).loc[sorted(common)],
                prior.set_index(join.KEYS).loc[sorted(common)],
                check_exact=True,
            )
        common_union.update(common)
        common_counts[folder.relative_to(ROOT).as_posix()] = len(common)
    join.require(len(common_union) == 318, "All 318 previous X/QA records match exactly")
    partitions = pd.DataFrame(
        json.loads((PARTITION / "readback.json").read_bytes())["proposed_key_partitions"]
    )
    held = partitions.loc[partitions.proposed_partition.eq("proposed_assessment_2022")]
    source = checkpoints.frame_keys(held.loc[held.review_population.eq("source_center_hypothesis")])
    original_U = checkpoints.frame_keys(held.loc[held.review_population.eq("U_geographic_slice")])
    metadata = x[join.KEYS].copy()
    metadata["original_source_record_key_present"] = [
        k in source for k in metadata[join.KEYS].itertuples(index=False, name=None)
    ]
    metadata["original_U_key_present"] = [
        k in original_U for k in metadata[join.KEYS].itertuples(index=False, name=None)
    ]
    metadata["target"] = metadata["accepted_L_membership"] = float("nan")
    metadata["daily_observation_status"] = "unknown"
    metadata["role"] = "separate_source_exploratory_assessment_2022"
    join.require(
        int(metadata.original_source_record_key_present.sum()) == 81,
        "All original source anchors retained",
    )
    snapshot = out / ("snapshot_" + uuid4().hex[:8])
    snapshot.mkdir()
    artifacts = {}
    for name, frame in (("features.csv", x), ("provenance.csv", q), ("review_roles.csv", metadata)):
        p = snapshot / name
        frame.to_csv(p, index=False)
        pd.testing.assert_frame_equal(
            frame, parse_csv(p.read_bytes()), check_dtype=False, check_exact=True
        )
        artifacts[p.relative_to(out).as_posix()] = digest(p)
    report = {
        "status": "separate_source_2022_calendar_X_verified_not_true_label_or_fit_acceptance",
        "decision": config,
        "snapshot_directory": snapshot.name,
        "keys": len(keys),
        "source_anchor_keys": 81,
        "original_U_and_weights_unchanged": True,
        "months": len(months),
        "days": len(days),
        "daily_files_verified": 2 * len(days),
        "complete_27_features": int(x[join.feature_names()].notna().all(axis=1).sum()),
        "prior_X_and_QA_exact_by_snapshot": common_counts,
        "prior_X_and_QA_exact_union": len(common_union),
        "daily_checks": checks,
        "month_receipts": progress["months"],
        "new_Y_or_accepted_L_created": 0,
        "model_fitted": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "artifact_sha256": artifacts,
        "producer_sha256": digest(Path(__file__)),
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "All consumed sources unchanged")
    checkpoints.save_json(out / "readback.json", report)
    progress["status"] = "completed_X_only"
    checkpoints.save_json(out / "runtime_progress.json", progress)
    print(
        "COMPLETE",
        len(keys),
        "source-calendar X; no model fit",
        "readback_sha256",
        digest(out / "readback.json"),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", type=Path)
    main(parser.parse_args().resume)
