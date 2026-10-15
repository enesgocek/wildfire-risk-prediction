"""Resume a pinned local method-pilot queue; default action requires no credentials."""

import argparse
import contextlib
import getpass
import io
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import requests

from wildfire_risk_prediction.core_pilot import (
    GROUPS,
    expected_pairs_for_day,
    source_progress,
    window_geometry,
)
from wildfire_risk_prediction.core_transfer import (
    check_file,
    digest,
    safe_error_details,
    transfer_one,
)
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.pilot_time_filter import required_pairs

ROOT = Path(__file__).resolve().parents[2]
PLANS = ROOT / "outputs/reports/dataset/observation_pilot_queue_v2"
JOBS = ROOT / "outputs/observation_pilot_v1"
RUNS = ROOT / "outputs/reports/dataset/observation_pilot_run_v1"


def write_json(path, value):
    require(not path.exists(), "No queue receipt overwrite")
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_queue(path):
    path = path.resolve()
    require(path.is_relative_to(PLANS) and path.name == "queue_plan.json", "Local queue plan")
    receipt = json.loads((path.parent / "readback.json").read_text(encoding="utf-8"))
    completion = json.loads((path.parent / "completion_readback.json").read_text(encoding="utf-8"))
    require(
        digest(path.parent / "readback.json") == completion["report_sha256"]
        and digest(path) == receipt["plan_sha256"],
        "Queue receipt closure",
    )
    plan = json.loads(path.read_text(encoding="utf-8"))
    require(
        plan["execution_scope"] == "fixed_calendar_core_156_units_native_time_filtered"
        and plan["reference_pair_count"] == 292
        and plan["required_geometry_pair_count"] == 98
        and plan["outside_by_time_witness_pair_count"] == 194
        and len(plan["pairs"]) == 98
        and len(plan["units"]) == 156
        and plan["pair_workers"] == 1
        and plan["hard_runtime_seconds"] == 14400
        and plan["raw_cache_limit_bytes"] == 20_000_000_000
        and plan["minimum_free_bytes"] == 20_000_000_000
        and plan["derived_disk_reserve_bytes"] == 10_000_000_000
        and plan["raw_eviction_permitted"] is False
        and plan["cloud_jobs_permitted"] is False
        and plan["negative_label_permitted"] is False
        and plan["daily_observation_status"] == "unknown"
        and plan["labels_created"] is False
        and plan["model_ready"] is False,
        "Fixed bounded method-pilot policy",
    )
    require(
        all(digest(ROOT / n) == h for n, h in plan["input_sha256"].items()), "Exact queue inputs"
    )
    require(
        len({p["sample_id"] for p in plan["pairs"]}) == 98
        and len({u["review_unit_id"] for u in plan["units"]}) == 156,
        "Unique fixed queue identities",
    )
    days = sorted({u["target_day"] for u in plan["units"]})
    require(
        len(days) == 12 and set(days) == set(plan["day_expected_pairs"]),
        "Fixed twelve-day calendar",
    )
    for day in days:
        require(
            expected_pairs_for_day(plan["pairs"], day) == plan["day_expected_pairs"][day],
            "Exact neighbour-day source schedule",
        )
    require(
        digest(ROOT / plan["time_witness_report"]) == plan["time_witness_sha256"],
        "Accepted time exclusion witness",
    )
    witness_path = ROOT / plan["time_witness_report"]
    witness = json.loads(witness_path.read_text(encoding="utf-8"))
    table_path = witness_path.parent / "pair_window_triage.csv"
    require(
        digest(table_path) == witness["artifact_sha256"][table_path.name], "Time decisions artifact"
    )
    source_path = ROOT / plan["reference_source_plan"]
    require(digest(source_path) == plan["reference_source_plan_sha256"], "Full reference plan")
    source_pairs = json.loads(source_path.read_text(encoding="utf-8"))["all_pairs_inventory_only"]
    table = pd.read_csv(table_path)
    require(required_pairs(source_pairs, table) == plan["pairs"], "Exact time-filtered raw scope")
    for day in days:
        expected_outside = set(
            table.loc[
                table.target_day.eq(day) & table.decision.eq("outside_by_full_scan_witness"),
                "sample_id",
            ]
        )
        require(
            expected_outside == set(plan["day_outside_pairs"][day]),
            "Explicit outside-window source accounting",
        )
    return plan


def verified_attempt(out, queue_sha):
    report = json.loads((out / "readback.json").read_text(encoding="utf-8"))
    completion = json.loads((out / "completion_readback.json").read_text(encoding="utf-8"))
    require(
        completion["report_sha256"] == digest(out / "readback.json")
        and report["queue_sha256"] == queue_sha,
        "Attempt receipt closure",
    )
    require(
        report["negative_label_permitted"] is False
        and report["labels_created"] is False
        and report["model_ready"] is False
        and report["daily_observation_status"] == "unknown",
        "Closed attempt science gates",
    )
    for name, sha in report["artifact_sha256"].items():
        require(digest(out / name) == sha, "Attempt artifact readback")
    require(report["completed_pair_count"] == len(report["pair_receipts"]), "Attempt pair count")
    for sample, receipt in report["pair_receipts"].items():
        folder = (ROOT / receipt["path"]).resolve()
        require(folder.is_relative_to(JOBS.resolve()), "Contained pair receipt")
        require(
            digest(folder / "readback.json") == receipt["report_sha256"], "Pair receipt unchanged"
        )
        pair_report = json.loads((folder / "readback.json").read_text(encoding="utf-8"))
        require(
            pair_report["sample_id"] == sample and pair_report["queue_sha256"] == queue_sha,
            "Pair attempt identity",
        )
    return report


def pair_name(pair):
    return pair["sample_id"].replace(":", "_").replace(".", "_")


def summarise(plan, completed, out):
    rows = []
    parts = gpd.read_file(ROOT / "data/interim/grid_aoi_parts.geojson").to_crs(6933)
    regions = parts.set_index("grid_id").geometry
    for day, units in pd.DataFrame(plan["units"]).groupby("target_day", sort=True):
        expected = plan["day_expected_pairs"][day]
        available = [s for s in expected if s in completed]
        progress = source_progress(expected, available)
        frames, geometry = [], {g: [] for g in GROUPS}
        for sample in available:
            folder = completed[sample]
            frame = pd.read_csv(folder / "scan_grid.csv", dtype={"pair_key": str})
            frames.append(frame)
            for group in GROUPS:
                saved = gpd.read_file(folder / "scan_geometries.gpkg", layer=group)
                require(
                    saved.grid_id.tolist() == frame.grid_id.tolist()
                    and saved.scan_id.tolist() == frame.scan_id.tolist(),
                    "Summary geometry keys",
                )
                geometry[group].extend(saved.geometry.to_numpy())
        frame = (
            pd.concat(frames, ignore_index=True)
            if frames
            else pd.DataFrame(columns=["grid_id", "scan_id", "orbit_id", "start_utc", "end_utc"])
        )
        for unit in units.to_dict("records"):
            chosen = frame.grid_id.eq(unit["grid_id"]).to_numpy()
            local = frame.loc[chosen].reset_index(drop=True)
            row = {
                **unit,
                **{k: v for k, v in progress.items() if k != "missing_pairs"},
                "missing_pairs_json": json.dumps(progress["missing_pairs"]),
                "loaded_scan_rows": len(local),
                "target": None,
                "full_daily_observation_proven": False,
                "labels_created": False,
                "reference_neighbour_pair_count": len(expected)
                + len(plan["day_outside_pairs"][day]),
                "outside_by_native_time_pair_count": len(plan["day_outside_pairs"][day]),
                "required_geometry_pair_count": len(expected),
            }
            for group in GROUPS:
                shapes = np.asarray(geometry[group], dtype=object)[chosen]
                metrics, _ = window_geometry(local, shapes, regions.loc[unit["grid_id"]], day)
                row[group + "_loaded_inside_m2"] = metrics["loaded_inside_area_m2"]
                row[group + "_loaded_boundary_m2"] = metrics["loaded_boundary_area_m2"]
                if group == "nominal_nonfire_land":
                    row.update(metrics)
            rows.append(row)
    table = pd.DataFrame(rows)
    require(
        len(table) == 156 and table.review_unit_id.is_unique and table.target.isna().all(),
        "Exact unlabelled pilot summary",
    )
    require(table.negative_label_permitted.eq(False).all(), "Closed summary rows")
    table.to_csv(out / "pilot_partial_summary.csv", index=False)
    back = pd.read_csv(out / "pilot_partial_summary.csv")
    require(
        back.review_unit_id.tolist() == table.review_unit_id.tolist()
        and back.target.isna().all()
        and back.negative_label_permitted.eq(False).all(),
        "Summary keys and unassigned targets",
    )
    for column in table.select_dtypes(include="number"):
        if column != "target":
            require(
                np.allclose(back[column], table[column], rtol=1e-10, atol=1e-7),
                "Summary numeric readback",
            )
    return table


def worker(path, out, allow_transfer):
    require(out.resolve().parent == RUNS.resolve() and out.is_dir(), "Local attempt output")
    logging.disable(logging.CRITICAL)
    pyproj.network.set_network_enabled(False)
    if not allow_transfer:

        def deny(*args, **kwargs):
            raise RuntimeError("Cache-only pilot queue")

        socket.socket.connect = deny
        socket.create_connection = deny
    plan = load_queue(path)
    from process_observation_pilot_pair import process, read_completed

    queue_sha = digest(path)
    job = JOBS / queue_sha[:16]
    job.mkdir(parents=True, exist_ok=True)
    raw = ROOT / "data/raw/observation_pilot_v1" / queue_sha[:16]
    lock = job / "writer.lock"
    require(not lock.exists(), "Prior writer lock requires process review")
    with lock.open("x", encoding="utf-8") as marker:
        marker.write(str(os.getpid()))
    completed, missing = {}, []
    deadline = time.monotonic() + plan["hard_runtime_seconds"] - 60
    state = "cache_review_complete_missing_private_transfer"
    session = requests.Session()
    session.headers.clear()
    session.auth, session.trust_env = None, False
    token = os.environ.pop("EARTHDATA_TOKEN", None) if allow_transfer else None
    require(not allow_transfer or bool(token), "Private transfer token")
    if token:
        session.headers["Authorization"] = "Bearer " + token
    parts = gpd.read_file(ROOT / "data/interim/grid_aoi_parts.geojson").to_crs(6933)
    units = pd.DataFrame(plan["units"])
    failure = None
    active = None
    network_bytes = 0
    try:
        for pair in plan["pairs"]:
            active = pair["sample_id"]
            if time.monotonic() > deadline - 900:
                state = "paused_at_local_runtime_reserve"
                break
            pair_root = job / "pairs" / pair_name(pair)
            receipts = sorted(pair_root.glob("*/completion_readback.json"))
            if receipts:
                folder = receipts[-1].parent
                read_completed(folder, pair, queue_sha)
                completed[active] = folder
                continue
            # Reuse the previously verified pair without duplicating or deleting it.
            locations = [
                ROOT / plan["existing_source_paths"].get(s["filename"], "__absent__")
                for s in pair["sources"]
            ]
            external = all(p.is_file() for p in locations)
            if external:
                require(locations[0].parent == locations[1].parent, "Co-located cached pair")
                cache = locations[0].parent
            else:
                cache = raw / pair_name(pair)
                present = all((cache / s["filename"]).is_file() for s in pair["sources"])
                if not present and not allow_transfer:
                    missing.append(active)
                    continue
                cache.mkdir(parents=True, exist_ok=True)
                require(
                    shutil.disk_usage(ROOT).free
                    >= plan["minimum_free_bytes"] + plan["derived_disk_reserve_bytes"],
                    "Queue disk reserve",
                )
                pair_deadline = min(deadline, time.monotonic() + 900)
                for source in pair["sources"]:
                    result = transfer_one(
                        session,
                        source,
                        cache,
                        deadline=pair_deadline,
                        cache_limit_bytes=pair["bytes"],
                        reserve_bytes=plan["minimum_free_bytes"]
                        + plan["derived_disk_reserve_bytes"],
                    )
                    network_bytes += result["network_bytes"]
                require(
                    sum(p.stat().st_size for p in raw.rglob("*") if p.is_file())
                    <= plan["raw_cache_limit_bytes"],
                    "Full raw cache budget",
                )
            for source in pair["sources"]:
                check_file(cache / source["filename"], source)
            days = [d for d, samples in plan["day_expected_pairs"].items() if active in samples]
            chosen = set(units.loc[units.target_day.isin(days), "grid_id"])
            selected = (
                parts.loc[parts.grid_id.isin(chosen)].sort_values("grid_id").reset_index(drop=True)
            )
            require(len(selected) == len(chosen) and bool(chosen), "Fixed selected pilot cells")
            folder = pair_root / (
                datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8]
            )
            process(pair, cache, folder, selected, queue_sha)
            completed[active] = folder
            progress = {
                "completed_pairs": len(completed),
                "expected_pairs": len(plan["pairs"]),
                "labels_created": False,
                "daily_observation_status": "unknown",
            }
            (out / "progress.json").write_text(json.dumps(progress) + "\n", encoding="utf-8")
            print(
                "PAIR VERIFIED "
                + active
                + " "
                + str(len(completed))
                + "/"
                + str(len(plan["pairs"])),
                flush=True,
            )
        if len(completed) == len(plan["pairs"]):
            state = "planned_pairs_processed_method_pilot_only"
    except Exception as error:
        state = "failed_checkpoints_retained"
        failure = {
            "error_type": type(error).__name__,
            "sample_id": active,
            **safe_error_details(error),
        }
    finally:
        session.close()
        token = None
        lock.unlink()
    table = summarise(plan, completed, out)
    require(
        all(digest(ROOT / n) == h for n, h in plan["input_sha256"].items()),
        "Queue final input closure",
    )
    result = {
        "status": state,
        "queue_sha256": queue_sha,
        "reference_pair_count": 292,
        "outside_by_native_time_pair_count": 194,
        "required_geometry_pair_count": len(plan["pairs"]),
        "time_witness_sha256": plan["time_witness_sha256"],
        "network_bytes": network_bytes if failure is None else None,
        "completed_file_transfer_bytes": network_bytes,
        "interrupted_transfer_bytes_fully_accounted": failure is None,
        **source_progress([p["sample_id"] for p in plan["pairs"]], list(completed)),
        "pair_receipts": {
            s: {
                "path": f.relative_to(ROOT).as_posix(),
                "report_sha256": digest(f / "readback.json"),
            }
            for s, f in completed.items()
        },
        "unit_count": len(table),
        "complete_source_units": int(table.all_planned_pairs_processed.sum()),
        "failure": failure,
        "artifact_sha256": {"pilot_partial_summary.csv": digest(out / "pilot_partial_summary.csv")},
        "labels_created": False,
        "model_ready": False,
        "cloud_jobs_started": 0,
        "raw_files_deleted": 0,
        "scope": "purpose_selected_method_pilot_not_population_error",
    }
    write_json(out / "readback.json", result)
    write_json(
        out / "completion_readback.json",
        {
            "status": "attempt_report_verified_not_daily_acceptance",
            "report_sha256": digest(out / "readback.json"),
        },
    )
    return 0 if failure is None else 1


def private_token():
    require(sys.stdin.isatty(), "Private login requires interactive terminal")
    import earthaccess

    old = {
        k: os.environ.get(k)
        for k in ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD", "EARTHDATA_TOKEN")
    }
    username = getpass.getpass("Earthdata kullanici adi (gizli): ")
    password = getpass.getpass("Earthdata sifre (gizli): ")
    try:
        os.environ.pop("EARTHDATA_TOKEN", None)
        os.environ["EARTHDATA_USERNAME"], os.environ["EARTHDATA_PASSWORD"] = username, password
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            auth = earthaccess.login(strategy="environment", persist=False)
            require(auth.authenticated, "Private Earthdata login")
            return auth.token["access_token"]
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        username = password = None


def run(path, prompt):
    plan = load_queue(path)
    logging.disable(logging.CRITICAL)
    print(
        "Sabit pilot: 156 hucre-gun; 292 ciftte zaman kaniti, 98 ciftte geometri. Etiket yok.",
        flush=True,
    )
    print("Ham aktarim ust kapsami: 18,00 GB; tek isci ve 4 saat ust sinir.", flush=True)
    print("Mod:", "ozel girisli aktarim" if prompt else "yalniz yerel onbellek", flush=True)
    token = private_token() if prompt else None
    out = RUNS / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    env = dict(os.environ)
    for name in ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD", "EARTHDATA_TOKEN"):
        env.pop(name, None)
    if token:
        env["EARTHDATA_TOKEN"] = token
    command = [sys.executable, str(Path(__file__)), "--plan", str(path), "--worker", str(out)]
    if prompt:
        command.append("--allow-transfer")
    state = "child_failed_outputs_retained"
    print("Sonuc klasoru:", out.relative_to(ROOT).as_posix(), flush=True)
    try:
        with (out / "worker.log").open("x", encoding="utf-8") as log:
            child = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                stdout=log,
                stderr=subprocess.DEVNULL,
                timeout=plan["hard_runtime_seconds"],
                check=False,
            )
        if child.returncode == 0:
            attempt = verified_attempt(out, digest(path))
            state = "child_completed"
            print("Yerel kuyruk durumu:", attempt["status"], flush=True)
    except subprocess.TimeoutExpired:
        state = "hard_timeout_outputs_and_writer_lock_retained"
    finally:
        env.pop("EARTHDATA_TOKEN", None)
        token = None
        write_json(
            out / "launcher_receipt.json",
            {
                "status": state,
                "credentials_written": False,
                "hard_runtime_seconds": plan["hard_runtime_seconds"],
                "queue_sha256": digest(path),
                "cloud_jobs_started": 0,
            },
        )
    print(state + "; bu mesaj gunluk gozlem/etiket kabulu degildir.", flush=True)
    return 0 if state == "child_completed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--plan", type=Path)
    source.add_argument("--latest-plan", action="store_true")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--cached-only", action="store_true")
    action.add_argument("--prompt-login", action="store_true")
    action.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--allow-transfer", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        plans = sorted(PLANS.glob("*/queue_plan.json"), reverse=True)
        path = plans[0] if args.latest_plan else args.plan.resolve()
        if args.worker:
            raise SystemExit(worker(path, args.worker, args.allow_transfer))
        require(not args.allow_transfer, "Transfer only through private parent")
        raise SystemExit(run(path, args.prompt_login))
    except Exception as error:
        if args.worker and not (args.worker / "failure.json").exists():
            write_json(
                args.worker / "failure.json",
                {
                    "error_type": type(error).__name__,
                    **safe_error_details(error),
                    "status": "failed_outputs_retained",
                    "exception_text_recorded": False,
                },
            )
        print("Kuyruk kontrolu tamamlanmadi:", type(error).__name__, flush=True)
        raise SystemExit(1) from None
