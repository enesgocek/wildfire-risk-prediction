"""Offline complete fixed-pilot scan-window audit; no resampling or target admission."""

import argparse
import hashlib
import json
import shutil
import socket
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.label_review import REVIEW_FIELDS
from wildfire_risk_prediction.observation_window import FIELDS, KEYS, review_window, source_schedule
from wildfire_risk_prediction.observation_window_pilot import append_diagnostics, stratum_impacts
from wildfire_risk_prediction.observation_window_source import deny, read_month_offline
from wildfire_risk_prediction.water_scope import attach_water_scope

ROOT = Path(__file__).resolve().parents[2]
PACKET = "outputs/reports/dataset/label_review_v1/20261014T153649Z_ca3fb92e"
OBS = "outputs/reports/dataset/observation_materialization_v1/20261014T145638Z_c0881064"
PRIOR = "outputs/reports/dataset/observation_windows_v1/20261014T190400Z_25bfc71a"
WATER = "outputs/reports/dataset/water_scope_v1/20261014T185242Z_f2e469bd"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def equal_values(left, right):
    left, right = left.reset_index(drop=True), right.reset_index(drop=True)
    pd.testing.assert_frame_equal(
        left.astype(object).where(left.notna(), None),
        right.astype(object).where(right.notna(), None),
        check_exact=True,
    )


def run(workers, hours):
    require(1 <= workers <= 4 and 0.05 <= hours <= 2, "Bounded local pilot resources")
    require(shutil.disk_usage(ROOT).free > 10 * 2**30, "Local disk reserve")
    started = time.monotonic()
    deadline = started + hours * 3600
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular pilot input")
        digest = sha(path)
        require(expected is None or digest == expected, "Pilot input hash changed")
        pins[name] = digest
        return path

    def report(name, expected):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    packet = report(
        PACKET + "/readback.json",
        "36ce8565a452efbf2a4f1e69fe3254ae33ccdd818eb08584f57b41a9eaf28037",
    )
    files = {n: retained(PACKET + "/" + n, h) for n, h in packet["artifact_sha256"].items()}
    sample = pd.read_csv(files["random_grid_days.csv"], float_precision="round_trip")
    forms = pd.read_csv(files["review_decisions_template.csv"])
    require(
        len(sample) == 400
        and len(forms) == 453
        and forms.review_status.eq("not_reviewed").all()
        and forms[REVIEW_FIELDS].isna().all().all(),
        "Fixed pilot; unreviewed forms",
    )
    prior = report(
        PRIOR + "/readback.json", "3be2b93d9fe3e048d6429d94380e49280f4b9e7b04546265ee501e59b7a1b689"
    )
    prior_files = {n: retained(PRIOR + "/" + n, h) for n, h in prior["artifact_sha256"].items()}
    for n, h in prior["input_sha256"].items():
        if n.startswith("src/"):
            retained(n, h)
    water = report(
        WATER + "/readback.json", "7b5d296bae6c3744790817409db4bce3a947e92919a06abde9271eac07814cae"
    )
    scope = pd.read_csv(
        retained(WATER + "/grid_water_scope.csv", water["artifact_sha256"]["grid_water_scope.csv"])
    )
    master = report(
        OBS + "/accepted_readback.json",
        "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14",
    )
    registry = report(
        "configs/gcp_source_blocks_2026-10-13.json",
        "c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95",
    )
    deferred = set(registry["deferred_days"])
    schedules, requested = {}, {}
    for row in sample.itertuples():
        schedule = source_schedule(row.prediction_timestamp_utc[:10], deferred)
        schedules[row.review_unit_id] = schedule
        for day in schedule.loc[
            schedule.source_status.eq("available_training_packet"), "source_nominal_day"
        ]:
            requested.setdefault(day[:7], {}).setdefault(day, set()).add(row.grid_id)
    monthly = {r["month"]: r for r in master["reports"]}
    for month in requested:
        current = json.loads(retained(OBS + "/" + month + "/readback.json").read_text())
        require(current == monthly[month], "Monthly report equals accepted master")
    cache, inner = {}, {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(read_month_offline, str(ROOT), monthly[m], days, deadline)
            for m, days in sorted(requested.items())
        ]
        try:
            for index, future in enumerate(as_completed(futures), start=1):
                result = future.result()
                require(time.monotonic() < deadline, "Pilot runtime reserve")
                cache.update(result["frames"])
                inner.update(result["inner"])
                for name, digest in result["inputs"].items():
                    require(name not in pins or pins[name] == digest, "Shared source pin agrees")
                    pins[name] = digest
                print(f"Source month checked {index}/{len(futures)}: {result['month']}", flush=True)
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    all_scans, summaries, schedule_rows = [], [], []
    for row in sample.itertuples():
        require(time.monotonic() < deadline, "Pilot window runtime reserve")
        schedule = schedules[row.review_unit_id]
        pieces = [
            cache[d].loc[cache[d].grid_id.eq(row.grid_id)]
            for d in schedule.source_nominal_day
            if d in cache
        ]
        frame = (
            pd.concat(pieces, ignore_index=True)
            if pieces
            else pd.DataFrame(columns=FIELDS + ["source_nominal_day"])
        )
        scans, summary = review_window(
            frame, row.prediction_timestamp_utc[:10], row.grid_id, schedule
        )
        scans["review_unit_id"] = row.review_unit_id
        all_scans.append(scans)
        summaries.append(summary)
        schedule_rows.append(
            schedule.assign(review_unit_id=row.review_unit_id, grid_id=row.grid_id)
        )
    summaries = pd.DataFrame(summaries)
    audited = append_diagnostics(sample, summaries, scope)
    strata = stratum_impacts(audited)
    require(
        len(strata) == 200 and strata.population_n.sum() == 6351709, "Original pilot population"
    )
    scans = pd.concat(all_scans, ignore_index=True)
    schedule = pd.concat(schedule_rows, ignore_index=True)

    # Reproduce every overlapping purpose-selected witness without changing that accepted packet.
    old = pd.read_csv(prior_files["window_summary.csv"], float_precision="round_trip")
    fresh = attach_water_scope(summaries, scope)
    keys = ["grid_id", "prediction_timestamp_utc"]
    overlap = old.merge(fresh[keys], on=keys, validate="one_to_one")
    compare = fresh.merge(overlap[keys], on=keys, validate="one_to_one")
    columns = [c for c in overlap if c != "window_id"]
    equal_values(overlap.sort_values(keys)[columns], compare.sort_values(keys)[columns])
    require(len(overlap) >= 6, "All six original witnesses reproduced")
    boundary = scans.loc[scans.window_classification.eq("boundary_unknown")].copy()
    if not boundary.empty:
        links = boundary.groupby(KEYS, sort=True).review_unit_id.agg(
            lambda x: json.dumps(sorted(set(x)))
        )
        boundary = boundary.drop_duplicates(KEYS).drop(
            columns=["review_unit_id", "prediction_timestamp_utc"]
        )
        boundary["sample_review_units_json"] = [links.loc[tuple(x)] for x in boundary[KEYS].values]

    for name in (
        "src/wildfire_risk_prediction/observation_window_source.py",
        "src/wildfire_risk_prediction/observation_window_pilot.py",
        "src/wildfire_risk_prediction/observation_review.py",
        "scripts/quality/review_window_pilot.py",
        PROTECTED,
    ):
        retained(name)
    protected = json.loads((ROOT / PROTECTED).read_text())
    for name, digest in protected.items():
        retained(name, digest)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/window_pilot_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("pilot_window_audit.csv", audited),
        ("window_scan_rows.csv", scans),
        ("source_day_schedule.csv", schedule),
        ("stratum_impacts.csv", strata),
        ("boundary_source_review.csv", boundary),
    ):
        path = out / name
        frame.to_csv(path, index=False, mode="x")
        strings = {
            c: str
            for c in frame
            if not frame[c].dropna().empty
            and frame[c].dropna().map(lambda v: isinstance(v, str)).all()
        }
        reread = pd.read_csv(path, dtype=strings, float_precision="round_trip")
        equal_values(frame, reread)
        artifacts[name] = sha(path)
    thermal = audited.window_loaded_thermal_center_definite_count
    result = {
        "status": "full_fixed_pilot_window_readback_passed",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha256": pins,
        "inner_daily_sha256": inner,
        "artifact_sha256": artifacts,
        "sample_units": len(audited),
        "strata": len(strata),
        "population_grid_days": 6351709,
        "sample_signal_counts": audited.signal_stratum.value_counts().to_dict(),
        "distinct_target_days": audited.prediction_timestamp_utc.nunique(),
        "source_days_read": len(cache),
        "source_months_read": len(requested),
        "units_with_incomplete_packet_set": int(audited.window_incomplete_packet_set.sum()),
        "units_with_boundary_scans": int(audited.window_boundary_scan_present.sum()),
        "units_with_boundary_thermal_centers": int(audited.window_boundary_thermal_present.sum()),
        "distinct_boundary_source_grid_scan_rows": len(boundary),
        "units_with_loaded_definite_thermal_centers": int(thermal.gt(0).sum()),
        "units_with_changed_loaded_vs_nominal_thermal_counts": int(
            audited.loaded_window_vs_nominal_thermal_count_delta.fillna(0).ne(0).sum()
        ),
        "source_schedule_status_counts": schedule.source_status.value_counts().to_dict(),
        "excluded_water_scope_units_preserved": int((~audited.water_scope_included).sum()),
        "prior_purpose_windows_reproduced": len(overlap),
        "human_forms_not_reviewed": len(forms),
        "protected_inputs_verified": len(protected),
        "workers": workers,
        "seconds": round(time.monotonic() - started, 3),
        "daily_observation_status": "unknown",
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "model_ready": False,
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "limits": [
            "The same frozen 400 sampled units; no resampling or changed N/n",
            "Raw sample counts are not population rates; expanded stratum counts are estimates",
            "Expanded counts have no confidence interval; rare boundary cases need a larger audit",
            "Scope filtering is a domain indicator; original sample weights are not renormalized",
            "Loaded definite/boundary centers are not independent fires or admitted targets",
            "Missing packet counts are not completed by the loaded neighbours",
            "No pixel time reconstruction, area re-clipping or observation sufficiency acceptance",
        ],
    }
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Pilot report readback")
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Artifact closure")
    (out / "completion_readback.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "report_sha256": sha(path),
                "input_files_verified": len(pins),
                "artifacts_verified": len(artifacts),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Full window pilot result:", out.relative_to(ROOT).as_posix(), flush=True)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--hours-limit", type=float, default=2)
    args = parser.parse_args()
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run(args.workers, args.hours_limit)
