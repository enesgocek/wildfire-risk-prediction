"""Plan, resume and audit offline training candidate joins; scientific labels stay closed."""

import argparse
import hashlib
import json
import math
import os
import shutil
import socket
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from wildfire_risk_prediction import dataset_assembly as assembly
from wildfire_risk_prediction import dataset_batch as batch
from wildfire_risk_prediction import dataset_contract as contract
from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_month

ROOT = Path(__file__).resolve().parents[2]
BASE_INDEX = "outputs/reports/dataset/feature_month_v1/two_month_readback_20261012.json"
BASE_INDEX_SHA = "ba00e9b1b612094964a4b767b889b4699a477c72888fbcd4a71abe05fe2c98da"
METHODS = [
    "src/wildfire_risk_prediction/dataset_batch.py",
    "src/wildfire_risk_prediction/dataset_contract.py",
    "src/wildfire_risk_prediction/dataset_assembly.py",
    "src/wildfire_risk_prediction/feature_join.py",
    "src/wildfire_risk_prediction/feature_month.py",
    "src/wildfire_risk_prediction/feature_partition.py",
    "src/wildfire_risk_prediction/target_admission.py",
    "scripts/quality/verify_feature_month.py",
    "scripts/quality/prepare_dataset.py",
]
OBSERVATION_LOG_READBACK = (
    "outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/failure_readback.json"
)
OBSERVATION_LOG_SHA = "b98cad5bff82fed84e1ff17f1ff234da1de074606986211e453f903129158daa"


class DiskReserveError(OSError):
    """A controlled disk-reserve stop, separate from missing/corrupt source files."""


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def public_file(name, prefixes):
    path = ROOT / name
    join.require(
        isinstance(name, str)
        and name.replace("\\", "/").startswith(prefixes)
        and path.resolve().is_relative_to(ROOT)
        and path.is_file()
        and not path.is_symlink(),
        "Regular public project input",
    )
    join.require(
        not any(
            p.startswith(".")
            or any(
                word in p.lower()
                for word in ("credential", "oauth", "drive_connection", "password", "token")
            )
            for p in Path(name).parts
        ),
        "Private input name forbidden",
    )
    return path


def read_record(name, expected=None):
    path = public_file(name, ("outputs/reports/", "outputs/gcp_acceleration/", "data/interim/"))
    data = path.read_bytes()
    if expected is not None:
        join.require(
            hashlib.sha256(data).hexdigest() == batch.digest_value(expected), "Report hash"
        )
    return json.loads(data), hashlib.sha256(data).hexdigest()


def fingerprints():
    return {name: sha(ROOT / name) for name in METHODS}


def new_directory(kind):
    folder = (
        ROOT
        / f"outputs/reports/dataset/{kind}"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )
    folder.mkdir(parents=True, exist_ok=False)
    return folder


def write_record(path, value):
    temporary = path.with_suffix(".tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)


def index_references(name, expected):
    index, digest = read_record(name, expected)
    join.require(
        index["labels_created"] is False
        and index["model_ready"] is False
        and index["final_test_accessed"] is False,
        "Candidate index acceptance state",
    )
    previous = []
    if index.get("version") == batch.INDEX_VERSION:
        original, _ = read_record(index["plan"], index["plan_sha256"])
        batch.validate_plan(original)
        previous = [
            e["candidate_readback_reference"]
            for e in original["entries"]
            if e["candidate_readback_reference"] is not None
        ]
    # Keep old registered reports across bounded runs; do not imply they were audited this run.
    batch.candidate_inventory(index["reports"])
    batch.candidate_inventory(index.get("completed_builder_reports", []))
    merged = {r["month"]: batch.candidate_reference(r) for r in previous}
    for ref in index.get("completed_builder_reports", []):
        merged[ref["month"]] = batch.candidate_reference(ref)
    for ref in index["reports"]:
        merged[ref["month"]] = batch.candidate_reference(ref)
    return [merged[m] for m in sorted(merged)], digest


def candidate_report(ref):
    ref = batch.candidate_reference(ref)  # Reject held-out month before report/data access.
    report, _ = read_record(ref["path"], ref["sha256"])
    join.require(
        report["status"] == "complete_month_candidate_readback_passed"
        and report["version"] == feature_month.VERSION
        and report["month"] == ref["month"]
        and report["split"] == "train"
        and report["rows"] == ref["rows"]
        and report["manifest_sha256"] == ref["manifest_sha256"]
        and report["days"] == feature_month.calendar_days(ref["month"])
        and report["candidate_features"] == join.feature_names()
        and report["inputs_unchanged"] is True
        and report["daily_observation_status"] == "unknown"
        and all(report[f] is False for f in feature_month.FALSE_FLAGS),
        "Candidate readback identity/scope",
    )
    return report


def plan(source_progress, candidate_index, expected_index_sha256):
    methods = fingerprints()
    progress, progress_sha = read_record(source_progress)
    join.require(
        source_progress.startswith("outputs/reports/landscape/training_supervisor_v1/")
        and progress["final_test_accessed"] is False
        and progress["fire_labels_created"] is False,
        "Training source supervisor scope",
    )
    candidates, index_sha = index_references(candidate_index, expected_index_sha256)
    sources = []
    for entry in progress["verified_months"]:
        ref = batch.vegetation_reference(entry)
        readback, _ = read_record(ref["readback"], ref["readback_sha256"])
        join.require(
            readback["status"] == "monthly_daily_readback_passed"
            and readback["month"] == entry["month"]
            and readback["verified_daily_rows"] == ref["daily_rows"]
            and readback["manifest_sha256"] == ref["manifest_sha256"]
            and readback["final_test_accessed"] is False,
            "Source reference readback",
        )
        manifest, _ = read_record(
            f"data/interim/vegetation/month_v1/{entry['month']}/manifest.json",
            ref["manifest_sha256"],
        )
        join.require(
            manifest["table_sha256"] == ref["daily_table_sha256"]
            and manifest["rows"] == ref["daily_rows"]
            and manifest["month"] == entry["month"],
            "Source manifest reference",
        )
        sources.append({"month": entry["month"], **ref})
    for ref in candidates:
        candidate_report(ref)  # Metadata only here; CSV/leaf acceptance is a separate audit.
    value = batch.build_plan(sources, candidates, methods)
    batch.validate_plan(value)
    # Shared weather/static identities come from the accepted two-month source inventory.
    anchors, _ = read_record(BASE_INDEX, BASE_INDEX_SHA)
    weather_path = "outputs/reports/meteorology/model_weather_2018-01-01_2025-01-01.json"
    weather, _ = read_record(weather_path, anchors["inputs_sha256"][weather_path])
    expected_days = [
        (f"{e['month']}-{d:02}", e["split"])
        for split in ("train", "validation")
        for e in batch.calendar_inventory(split)
        for d in range(1, e["calendar_days"] + 1)
    ]
    join.require(
        [(e["date"], e["split"]) for e in weather["days"]] == expected_days
        and weather["final_test_accessed"] is False,
        "Complete prepared weather metadata calendar",
    )
    static_path = "data/interim/landscape/v1/manifest.json"
    static, _ = read_record(static_path, anchors["inputs_sha256"][static_path])
    join.require(static["grid_count"] == batch.GRID_COUNT, "Static metadata grid count")
    observation, _ = read_record(OBSERVATION_LOG_READBACK, OBSERVATION_LOG_SHA)
    join.require(
        observation["status"] == "v5_failure_log_catalogue_readback_passed"
        and observation["final_state"]["daily_observation_status"] == "unknown"
        and observation["final_state"]["negative_label_permitted"] is False,
        "Registered satellite log-only acceptance",
    )
    delivery = batch.delivery_inventory(value, observation["final_state"]["existing_months"])
    delivery["evidence_sources"] = {
        weather_path: anchors["inputs_sha256"][weather_path],
        static_path: anchors["inputs_sha256"][static_path],
        OBSERVATION_LOG_READBACK: OBSERVATION_LOG_SHA,
    }
    delivery["limits"] = [
        "Registered historical satellite readback; not current live VM progress "
        "or payload acceptance",
        "Weather metadata includes 2024; no validation feature CSV or final-test data read",
        "References do not prove final labels, habitat suitability or operational availability",
    ]
    folder = new_directory("preparation_v1")
    write_record(
        folder / "source_snapshot.json",
        {
            "source_progress": source_progress,
            "source_progress_sha256_at_snapshot": progress_sha,
            "source_updated_at_utc": progress.get("updated_at_utc"),
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "references": sources,
            "live_progress_may_advance": True,
            "leaf_table_bytes_verified": False,
        },
    )
    write_record(folder / "contract.json", contract.specification())
    write_record(folder / "delivery_inventory.json", delivery)
    write_record(folder / "plan.json", value)
    join.require(methods == fingerprints(), "Planning methods changed")
    write_record(
        folder / "readback.json",
        {
            "status": "candidate_batch_preparation_passed",
            "plan_sha256": sha(folder / "plan.json"),
            "contract_sha256": sha(folder / "contract.json"),
            "source_snapshot_sha256": sha(folder / "source_snapshot.json"),
            "delivery_inventory_sha256": sha(folder / "delivery_inventory.json"),
            "source_reference_months": len(sources),
            "candidate_reference_months": len(candidates),
            "source_index_sha256": index_sha,
            "labels_created": False,
            "model_ready": False,
            "final_test_accessed": False,
            "network_requests": 0,
            "scientific_acceptance_granted": False,
        },
    )
    print("Plan:", (folder / "plan.json").relative_to(ROOT).as_posix())
    print("Plan SHA256:", sha(folder / "plan.json"))
    return folder


def audit_candidate(ref, check_budget=lambda: None):
    report = candidate_report(ref)
    pins = report["inputs_sha256"]
    for name, digest in pins.items():
        path = public_file(name, ("data/interim/", "outputs/reports/", "src/", "scripts/"))
        join.require(sha(path) == digest, "Candidate source/method changed")
    grid_name = "data/interim/grid_aoi_parts.geojson"
    join.require(grid_name in pins, "Explicit grid source identity")
    grid, _ = read_record(grid_name, pins[grid_name])
    ids = sorted(f["properties"]["grid_id"] for f in grid["features"])
    join.require(len(ids) == len(set(ids)) == batch.GRID_COUNT, "Project grid inventory")
    folder = (ROOT / ref["path"]).parent
    missing = dict.fromkeys(join.feature_names(), 0)
    checked = []
    for day, features, qa in feature_month.iter_month(
        folder, expected_manifest_sha256=ref["manifest_sha256"], grid_ids=ids
    ):
        check_budget()
        preview, _, _ = assembly.assemble_day(
            features, qa, assembly.unassigned_targets(features), ids, day
        )
        join.require(preview.target.isna().all(), "Binary target unexpectedly generated")
        for field in missing:
            missing[field] += int(features[field].isna().sum())
        checked.append(day)
    join.require(
        checked == report["days"] and missing == report["missing_by_feature"],
        "Independent candidate calendar/missingness readback",
    )
    join.require(all(sha(ROOT / k) == v for k, v in pins.items()), "Candidate inputs changed")
    return ref


@contextmanager
def writer_lock():
    path = ROOT / "outputs/cache/dataset_candidate_batch.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump({"pid": os.getpid(), "scope": "candidate_feature_batch_only"}, handle)
    try:
        yield
    finally:
        path.unlink()


def execute(plan_path, expected_plan_sha256, months, hours_limit, build_missing=False):
    if months is not None:
        for month in months:
            feature_month.calendar_days(month)  # Scope gate before all plan/source reads.
        join.require(months and len(months) == len(set(months)), "Explicit unique selected months")
    join.require(math.isfinite(hours_limit) and 1 / 60 <= hours_limit <= 24, "Bounded runtime")
    value, _ = read_record(plan_path, expected_plan_sha256)
    batch.validate_plan(value)
    join.require(value["code_sha256"] == fingerprints(), "Batch methods changed; make a new plan")
    entries = {e["month"]: e for e in value["entries"]}
    if months is None:
        months = [e["month"] for e in value["entries"] if e["action"] != "await_source_reference"]
        join.require(months, "No ready source/candidate references")
    deadline = time.monotonic() + hours_limit * 3600
    folder = new_directory("candidate_batch_v1")
    result = {
        "version": batch.INDEX_VERSION,
        "status": "running",
        "plan": plan_path,
        "plan_sha256": expected_plan_sha256,
        "selected_months": months,
        "reports": [],
        "completed_builder_reports": [],
        "actions": [],
        "labels_created": False,
        "model_ready": False,
        "final_test_accessed": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "hours_limit": hours_limit,
        "build_missing_authorized_by_cli": build_missing,
        "error_type": None,
        "network_requests": 0,
    }

    def check_budget():
        if time.monotonic() >= deadline - 10:
            raise TimeoutError("Candidate batch runtime reserve")
        if shutil.disk_usage(ROOT).free < 10 * 2**30:
            raise DiskReserveError("Candidate batch disk reserve")

    with writer_lock():
        write_record(folder / "progress.json", result)
        try:
            for month in months:
                check_budget()
                entry = entries[month]
                ref = entry["candidate_readback_reference"]
                action = "verified_reused"
                if ref is None:
                    if not build_missing or entry["vegetation_source_reference"] is None:
                        result["status"] = "stopped_awaiting_source_or_build_request"
                        result["blocked_month"] = month
                        break
                    check_budget()
                    if deadline - time.monotonic() <= 60:
                        raise TimeoutError("Month build runtime reserve")
                    source = entry["vegetation_source_reference"]
                    process = subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / "scripts/quality/verify_feature_month.py"),
                            "--month",
                            month,
                            "--vegetation-readback",
                            source["readback"],
                            "--expected-readback-sha256",
                            source["readback_sha256"],
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        timeout=deadline - time.monotonic() - 10,
                    )
                    join.require(process.returncode == 0, "Month builder failed; outputs retained")
                    paths = [s[8:] for s in process.stdout.splitlines() if s.startswith("Report: ")]
                    join.require(len(paths) == 1, "Single completed month builder report")
                    report, digest = read_record(paths[0])
                    ref = batch.candidate_reference(
                        {
                            "month": month,
                            "path": paths[0],
                            "sha256": digest,
                            "rows": report["rows"],
                            "manifest_sha256": report["manifest_sha256"],
                        }
                    )
                    candidate_report(ref)
                    result["completed_builder_reports"].append(ref)
                    write_record(folder / "progress.json", result)
                    action = "built_and_verified"
                audit_candidate(ref, check_budget)
                join.require(value["code_sha256"] == fingerprints(), "Batch methods changed")
                result["reports"].append(ref)
                result["actions"].append({"month": month, "action": action})
                write_record(folder / "progress.json", result)
            else:
                result["status"] = "completed_selected_candidate_months"
        except (TimeoutError, subprocess.TimeoutExpired) as error:
            result.update(
                status="stopped_time_budget_results_retained", error_type=type(error).__name__
            )
        except KeyboardInterrupt:
            result.update(status="interrupted_results_retained", error_type="KeyboardInterrupt")
        except DiskReserveError:
            result.update(
                status="stopped_disk_reserve_results_retained", error_type="DiskReserveError"
            )
        except Exception as error:
            result.update(status="failed_results_retained", error_type=type(error).__name__)
        result.update(batch.candidate_inventory(result["reports"]))
        result["finished_at_utc"] = datetime.now(UTC).isoformat()
        write_record(folder / "progress.json", result)
    print("Result:", (folder / "progress.json").relative_to(ROOT).as_posix())
    print("Result SHA256:", sha(folder / "progress.json"))
    print("Status:", result["status"])
    return folder


def audit(index_path, expected_index_sha256, require_complete=False):
    refs, _ = index_references(index_path, expected_index_sha256)
    # Validate all metadata, including scope and duplicates, before the first CSV.
    inventory = batch.candidate_inventory(refs)
    if require_complete:
        join.require(
            inventory["candidate_calendar_complete"], "Complete training calendar required"
        )
    for ref in refs:
        audit_candidate(ref)
    folder = new_directory("candidate_audit_v1")
    result = {
        "status": "candidate_index_structural_readback_passed",
        "source_index": index_path,
        "source_index_sha256": expected_index_sha256,
        "reports": refs,
        **batch.candidate_inventory(refs),
        "scientific_acceptance_granted": False,
        "network_requests": 0,
        "checked_at_utc": datetime.now(UTC).isoformat(),
    }
    write_record(folder / "readback.json", result)
    print("Audit:", (folder / "readback.json").relative_to(ROOT).as_posix())
    print("Model ready:", result["model_ready"])
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("plan")
    p.add_argument("--source-progress", required=True)
    p.add_argument("--candidate-index", default=BASE_INDEX)
    p.add_argument("--expected-index-sha256", default=BASE_INDEX_SHA)
    e = commands.add_parser("execute")
    e.add_argument("--plan", required=True)
    e.add_argument("--expected-plan-sha256", required=True)
    selection = e.add_mutually_exclusive_group(required=True)
    selection.add_argument("--months", nargs="+")
    selection.add_argument("--all-ready", action="store_true")
    e.add_argument("--hours-limit", type=float, required=True)
    e.add_argument("--build-missing", action="store_true")
    a = commands.add_parser("audit")
    a.add_argument("--candidate-index", required=True)
    a.add_argument("--expected-index-sha256", required=True)
    a.add_argument("--require-complete-calendar", action="store_true")
    args = parser.parse_args()

    def deny_network(*args, **kwargs):
        raise RuntimeError("Network forbidden in dataset preparation")

    socket.socket.connect = deny_network
    socket.socket.connect_ex = deny_network
    socket.create_connection = deny_network
    if args.command == "plan":
        plan(args.source_progress, args.candidate_index, args.expected_index_sha256)
    elif args.command == "execute":
        folder = execute(
            args.plan, args.expected_plan_sha256, args.months, args.hours_limit, args.build_missing
        )
        state = json.loads((folder / "progress.json").read_text(encoding="utf-8"))["status"]
        return {
            "completed_selected_candidate_months": 0,
            "stopped_time_budget_results_retained": 2,
            "stopped_disk_reserve_results_retained": 2,
            "stopped_awaiting_source_or_build_request": 3,
            "interrupted_results_retained": 130,
        }.get(state, 1)
    else:
        audit(args.candidate_index, args.expected_index_sha256, args.require_complete_calendar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
