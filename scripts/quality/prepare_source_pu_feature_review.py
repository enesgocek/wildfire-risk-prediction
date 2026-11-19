"""Link existing features to frozen source/U review keys; no L, target, fit or final merge."""

import csv
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_partition import parse_csv
from wildfire_risk_prediction.feature_readiness import inspect_day
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PROTOCOL = BASE / "source_conditioned_pu_protocol_v1/20261119T200942Z_3bc1ded8/readback.json"
PROTOCOL_SHA = "c22b246a5f93563115a193de7022d63accdabb18938ac5a635f4916ff3951df9"
SOURCE_FEATURES = BASE / "waiting_features_v1/20261017T010902Z_2aa6320b"
FEATURE_REPORT_SHA = "a71675fa75d4176a80090be55519fef92aabcad3212e55e561278eb9ac4372fd"
STATIC = ROOT / "data/interim/landscape/v1/grid_static.csv"


def review_key(grid, stamp):
    target = datetime.fromisoformat(stamp)
    join.require(target.tzinfo is not None and target.utcoffset() == timedelta(0), "UTC review key")
    join.require(target.time().replace(tzinfo=None) == datetime.min.time(), "Midnight review key")
    join.require(
        datetime(2018, 1, 1, tzinfo=UTC) <= target
        and target + timedelta(days=1) < datetime(2023, 1, 1, tzinfo=UTC),
        "Fit-only review key before source access",
    )
    join.require(isinstance(grid, str) and grid.strip(), "Nonempty cell key")
    return grid, target.isoformat()


def collect_keys(cases, u_rows):
    sources, u_keys, mapping, ids = set(), set(), [], set()
    for case in cases:
        if not case["diagnostic_focus"]:
            continue
        join.require(
            not case["researcher_retained_outside_L"]
            and case["target"] is None
            and case["membership"] == "review_unassigned",
            "No source admission or retention override",
        )
        join.require(case["archive_row"] not in ids, "Unique source record")
        ids.add(case["archive_row"])
        join.require(
            len(case["conditional_center_grid_ids"])
            == len(case["conditional_target_window_starts"])
            == 1,
            "One conditional center key only",
        )
        key = review_key(
            case["conditional_center_grid_ids"][0], case["conditional_target_window_starts"][0]
        )
        sources.add(key)
        mapping.append(
            {
                "archive_row": case["archive_row"],
                "grid_id": key[0],
                "prediction_timestamp_utc": key[1],
                "target": None,
            }
        )
    for row in u_rows:
        key = review_key(row["grid_id"], row["prediction_timestamp_utc"])
        join.require(
            row["target"] in (None, "") and row["daily_observation_status"] == "unknown",
            "U remains unknown",
        )
        join.require(key not in u_keys, "Unique U key")
        u_keys.add(key)
    return sources, u_keys, mapping


def selected_file(root, entry, day, kind):
    # Validate role before resolving/opening a table from the metadata index.
    review_key("metadata_guard", day + "T00:00:00+00:00")
    path = (root / entry["path"]).resolve()
    join.require(
        path.is_relative_to((root / "outputs/reports/dataset/feature_month_v1").resolve()),
        "Partition stays in feature store",
    )
    join.require(
        path.name == f"{day}_{kind}.csv" and entry["day"] == day and entry["kind"] == kind,
        "Partition day and kind",
    )
    data = path.read_bytes()
    join.require(
        len(data) == int(entry["bytes"]) and digest(path) == entry["sha256"],
        "Partition bytes and content hash",
    )
    return path, parse_csv(data)


def describe(frame, keys):
    join.require(
        keys and not frame.duplicated(join.KEYS).any(), "Nonempty keys and unique feature rows"
    )
    subset = frame.set_index(join.KEYS).loc[sorted(keys)].reset_index()
    fields = join.feature_names()
    return {
        "key_rows": len(subset),
        "complete_27_feature_rows": int(subset[fields].notna().all(axis=1).sum()),
        "features": {
            name: {
                "present": int(subset[name].notna().sum()),
                "missing": int(subset[name].isna().sum()),
                "q25": float(subset[name].quantile(0.25)) if subset[name].notna().any() else None,
                "median": float(subset[name].median()) if subset[name].notna().any() else None,
                "q75": float(subset[name].quantile(0.75)) if subset[name].notna().any() else None,
            }
            for name in fields
        },
    }


def main():
    started = monotonic()
    pins = {PROTOCOL: PROTOCOL_SHA, SOURCE_FEATURES / "readback.json": FEATURE_REPORT_SHA}
    join.require(
        all(digest(p) == h for p, h in pins.items()), "Frozen source cohort and feature report"
    )
    parent = json.loads(PROTOCOL.read_bytes())
    previous = json.loads((SOURCE_FEATURES / "readback.json").read_bytes())
    pins.update({ROOT / p: h for p, h in parent["input_sha256"].items()})
    for name in ("verified_daily_files.csv", "input_manifest.json"):
        pins[SOURCE_FEATURES / name] = previous["artifact_sha256"][name]
    slice_path = PROTOCOL.parent / "U_Mersin_geographic_review_slice.csv"
    pins[slice_path] = parent["artifact_sha256"][slice_path.name]
    join.require(all(digest(p) == h for p, h in pins.items()), "Source and index pins")
    with slice_path.open(encoding="utf-8", newline="") as f:
        source_keys, u_keys, mapping = collect_keys(parent["cases"], list(csv.DictReader(f)))
    keys = source_keys | u_keys
    join.require(
        len(mapping) == 380 and len(source_keys) == 374 and len(u_keys) == 503 and len(keys) == 877,
        "Frozen center review populations; no silent overlap removal",
    )
    days = defaultdict(set)
    for grid, stamp in keys:
        days[stamp[:10]].add(grid)
    by_day = defaultdict(dict)
    with (SOURCE_FEATURES / "verified_daily_files.csv").open(encoding="utf-8", newline="") as f:
        for entry in csv.DictReader(f):
            if entry["day"] not in days:
                continue
            join.require(entry["kind"] not in by_day[entry["day"]], "Unique daily index entry")
            by_day[entry["day"]][entry["kind"]] = entry
    join.require(
        set(by_day) == set(days)
        and all(set(v) == {"features", "provenance"} for v in by_day.values()),
        "Both partition kinds for every requested day",
    )
    old_pins = json.loads((SOURCE_FEATURES / "input_manifest.json").read_bytes())
    pins[STATIC] = old_pins[STATIC.relative_to(ROOT).as_posix()]
    for name in (
        "feature_join",
        "feature_partition",
        "feature_readiness",
        "landscape",
        "weather_policy",
    ):
        path = ROOT / f"src/wildfire_risk_prediction/{name}.py"
        expected = old_pins.get(path.relative_to(ROOT).as_posix(), digest(path))
        pins[path] = expected
    join.require(all(digest(p) == h for p, h in pins.items()), "Static and checker identities")
    static = parse_csv(STATIC.read_bytes())
    features, provenance, daily_checks = [], [], []
    for number, day in enumerate(sorted(days), 1):
        tables = {}
        for kind in ("features", "provenance"):
            entry = by_day[day][kind]
            path, full = selected_file(ROOT, entry, day, kind)
            pins[path] = entry["sha256"]
            tables[kind] = full.loc[full.grid_id.isin(days[day])].copy()
        f, qa = tables["features"], tables["provenance"]
        result = inspect_day(
            f, qa, sorted(days[day]), day, static.loc[static.grid_id.isin(days[day])]
        )
        daily_checks.append(result)
        features.append(f)
        provenance.append(qa)
        if number % 100 == 0:
            print(f"REVIEW FEATURE DAYS {number}/{len(days)}", flush=True)
    f = pd.concat(features, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
    qa = pd.concat(provenance, ignore_index=True).sort_values(join.KEYS).reset_index(drop=True)
    actual = set(map(tuple, f[join.KEYS].to_numpy()))
    join.require(actual == keys and len(f) == len(qa) == 877, "All requested keys exactly once")
    out = (
        BASE
        / "source_pu_feature_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    artifacts = {}
    for name, frame in (("features.csv", f), ("provenance.csv", qa)):
        path = out / name
        frame.to_csv(path, index=False)
        pd.testing.assert_frame_equal(
            frame, parse_csv(path.read_bytes()), check_dtype=False, check_exact=True
        )
        artifacts[name] = digest(path)
    source_counts = defaultdict(int)
    for row in mapping:
        source_counts[(row["grid_id"], row["prediction_timestamp_utc"])] += 1
    inspection = f.copy()
    inspection.insert(
        2,
        "review_population",
        [
            "source_center_hypothesis" if k in source_keys else "U_geographic_slice"
            for k in map(tuple, f[join.KEYS].to_numpy())
        ],
    )
    inspection.insert(
        3, "source_records_at_key", [source_counts[k] for k in map(tuple, f[join.KEYS].to_numpy())]
    )
    inspection["target"] = pd.NA
    inspection["daily_observation_status"] = "unknown"
    inspection.to_csv(out / "inspection.csv", index=False)
    saved = parse_csv((out / "inspection.csv").read_bytes())
    join.require(
        saved.target.isna().all() and saved.daily_observation_status.eq("unknown").all(),
        "Inspection remains unlabeled",
    )
    pd.testing.assert_frame_equal(
        inspection.drop(columns="target"),
        saved.drop(columns="target"),
        check_dtype=False,
        check_exact=True,
    )
    artifacts["inspection.csv"] = digest(out / "inspection.csv")
    path = out / "source_case_mapping.json"
    path.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    join.require(json.loads(path.read_bytes()) == mapping, "Source mapping roundtrip")
    artifacts[path.name] = digest(path)
    report = {
        "status": "limited_unlabeled_source_U_feature_review_ready_not_model_dataset",
        "source_records_preserved": 380,
        "source_center_keys": len(source_keys),
        "U_keys": len(u_keys),
        "unique_feature_keys": len(keys),
        "feature_columns": join.feature_names(),
        "days_read": len(days),
        "daily_files_hash_verified": 2 * len(days),
        "source_key_overlap_with_U": len(source_keys & u_keys),
        "descriptive_profiles": {
            "source_center_hypotheses": describe(f, source_keys),
            "U_geographic_slice": describe(f, u_keys),
        },
        "joint_missingness_checks": daily_checks,
        "marginal_profiles_verify_shared_class_conditionals": False,
        "historical_publication_availability_verified": False,
        "review_feature_link_performed": True,
        "final_training_dataset_assembled": False,
        "new_imputation_applied": False,
        "new_L_memberships": 0,
        "binary_labels_created": 0,
        "rates_estimated": False,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "artifact_sha256": artifacts,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "elapsed_seconds": round(monotonic() - started, 3),
    }
    join.require(all(digest(p) == h for p, h in pins.items()), "Inputs unchanged at closure")
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    join.require(json.loads(path.read_bytes()) == report, "Review report roundtrip")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    print(
        {k: v["complete_27_feature_rows"] for k, v in report["descriptive_profiles"].items()},
        flush=True,
    )
    print("PASS limited_review_only; no L/target, training, probability or final merge", flush=True)
    print("readback_sha256", digest(path), flush=True)


if __name__ == "__main__":
    main()
