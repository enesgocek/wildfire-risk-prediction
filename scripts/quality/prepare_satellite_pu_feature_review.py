"""Read X for the fixed satellite proposal union and original U; no S/Y fitting or final merge."""

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
PROPOSALS = BASE / "satellite_PU_L_proposals_v1/20261120T005519Z_62f3f815/readback.json"
PROPOSALS_SHA = "679a5ad9eab6342fa153c46cbbcc8f1e494b92256b592ba84f24823d0c0a4a85"
U_REPORT = BASE / "full_U_feature_review_v1/20261120T000956Z_1a58d019/readback.json"
U_REPORT_SHA = "5aa2791fd0c810d669df003f7481f52350be5bf3091db590b6bddf254f3f4cd2"


def combine_exact(first, second):
    """Preserve one physical feature row per key, requiring exact equality on overlaps."""
    require = join.require
    for table in (first, second):
        require(not table.duplicated(join.KEYS).any(), "Unique input feature keys")
    a, b = first.set_index(join.KEYS), second.set_index(join.KEYS)
    common = a.index.intersection(b.index)
    if len(common):
        pd.testing.assert_frame_equal(
            a.loc[common], b.loc[common], check_dtype=False, check_exact=True
        )
    return (
        pd.concat(
            [first, second.loc[~second.set_index(join.KEYS).index.isin(a.index)]], ignore_index=True
        )
        .sort_values(join.KEYS)
        .reset_index(drop=True)
    )


def roles_table(features, u_keys, proposal_keys):
    metadata = features[join.KEYS].copy()
    keys = list(metadata.itertuples(index=False, name=None))
    metadata["original_U_sample_present"] = [k in u_keys for k in keys]
    metadata["possible_L_proposal_present"] = [k in proposal_keys for k in keys]
    # CSV readers represent an entirely blank numeric target as float NaN.
    metadata["target"] = float("nan")
    metadata["accepted_L_membership"] = float("nan")
    metadata["daily_observation_status"] = "unknown"
    return metadata


def main():
    started = monotonic()
    store = source_review.SOURCE_FEATURES
    pins = {
        PROPOSALS: PROPOSALS_SHA,
        U_REPORT: U_REPORT_SHA,
        store / "readback.json": source_review.FEATURE_REPORT_SHA,
        Path(source_review.__file__): digest(Path(source_review.__file__)),
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "Pinned proposals and unchanged U")
    proposals, u_report, old = [
        json.loads(p.read_bytes()) for p in (PROPOSALS, U_REPORT, store / "readback.json")
    ]
    for report_path, report, names in (
        (
            PROPOSALS,
            proposals,
            ("proposal_key_union.csv", "all_first_cells_with_proposal_flags.csv"),
        ),
        (U_REPORT, u_report, ("features.csv", "provenance.csv", "inspection.csv")),
        (store / "readback.json", old, ("verified_daily_files.csv", "input_manifest.json")),
    ):
        pins.update({report_path.parent / n: report["artifact_sha256"][n] for n in names})
    pins.update({ROOT / p: h for p, h in proposals["input_sha256"].items()})
    join.require(
        all(digest(p) == h for p, h in pins.items()), "Current source and proposal snapshots"
    )
    selected = parse_csv((PROPOSALS.parent / "proposal_key_union.csv").read_bytes())
    join.require(
        len(selected) == 1670
        and selected.target.isna().all()
        and selected.accepted_L_membership.isna().all(),
        "Proposals not accepted L/Y",
    )
    keys = {
        source_review.review_key(g, t)
        for g, t in selected[join.KEYS].itertuples(index=False, name=None)
    }
    days, index = defaultdict(set), defaultdict(dict)
    for grid, stamp in keys:
        days[stamp[:10]].add(grid)
    with (store / "verified_daily_files.csv").open(encoding="utf-8", newline="") as f:
        for entry in csv.DictReader(f):
            if entry["day"] in days:
                join.require(entry["kind"] not in index[entry["day"]], "Unique indexed daily part")
                index[entry["day"]][entry["kind"]] = entry
    join.require(
        set(index) == set(days)
        and all(set(x) == {"features", "provenance"} for x in index.values()),
        "Both parts for proposal days",
    )
    manifest = json.loads((store / "input_manifest.json").read_bytes())
    pins[source_review.STATIC] = manifest[source_review.STATIC.relative_to(ROOT).as_posix()]
    for module in (
        "feature_join",
        "feature_partition",
        "feature_readiness",
        "landscape",
        "weather_policy",
    ):
        p = ROOT / f"src/wildfire_risk_prediction/{module}.py"
        pins[p] = manifest.get(p.relative_to(ROOT).as_posix(), digest(p))
    join.require(all(digest(p) == h for p, h in pins.items()), "Original checker/static identities")
    static = parse_csv(source_review.STATIC.read_bytes())
    values, qa, checks = [], [], []
    for number, day in enumerate(sorted(days), 1):
        tables = {}
        for kind in ("features", "provenance"):
            entry = index[day][kind]
            p, full = source_review.selected_file(ROOT, entry, day, kind)
            pins[p] = entry["sha256"]
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
        qa.append(tables["provenance"])
        if number % 100 == 0:
            print(f"SATELLITE PROPOSAL FEATURE DAYS {number}/{len(days)}", flush=True)
    candidate_x = pd.concat(values, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
    candidate_qa = pd.concat(qa, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
    join.require(
        set(candidate_x[join.KEYS].itertuples(index=False, name=None)) == keys
        and len(candidate_x) == len(candidate_qa) == 1670,
        "All proposal keys",
    )
    u_x = parse_csv((U_REPORT.parent / "features.csv").read_bytes())
    u_qa = parse_csv((U_REPORT.parent / "provenance.csv").read_bytes())
    features, provenance = combine_exact(u_x, candidate_x), combine_exact(u_qa, candidate_qa)
    u_keys = set(u_x[join.KEYS].itertuples(index=False, name=None))
    metadata = roles_table(features, u_keys, keys)
    out = (
        BASE
        / "satellite_PU_feature_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    artifacts = {}
    for name, frame in (
        ("features.csv", features),
        ("provenance.csv", provenance),
        ("review_roles.csv", metadata),
    ):
        p = out / name
        frame.to_csv(p, index=False)
        pd.testing.assert_frame_equal(
            frame, parse_csv(p.read_bytes()), check_dtype=False, check_exact=True
        )
        artifacts[name] = digest(p)
    report = {
        "status": "satellite_proposal_and_U_X_review_ready_not_L_Y_or_training_dataset",
        "original_U_keys": 2048,
        "possible_L_proposal_keys": 1670,
        "overlap_keys_preserved": len(keys & u_keys),
        "unique_feature_keys": len(features),
        "new_proposal_days_read": len(days),
        "new_daily_files_hash_verified": 2 * len(days),
        "feature_columns": join.feature_names(),
        "profiles": {
            "proposal_union": source_review.describe(features, keys),
            "original_U": source_review.describe(features, u_keys),
        },
        "proposal_daily_checks": checks,
        "accepted_L_and_Y_remain_unassigned": True,
        "scenario_selected": None,
        "new_imputation_applied": False,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "artifact_sha256": artifacts,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "elapsed_seconds": round(monotonic() - started, 3),
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "Original feature inputs unchanged")
    p = out / "readback.json"
    p.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    print("unique_feature_keys", len(features), "readback_sha256", digest(p), flush=True)


if __name__ == "__main__":
    main()
