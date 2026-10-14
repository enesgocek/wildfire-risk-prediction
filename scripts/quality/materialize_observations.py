"""Offline training observation sidecars from already accepted compact ZIPs, without labels."""

import argparse
import hashlib
import io
import json
import os
import shutil
import socket
import sys
import time
import uuid
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cloud"))
from receive_gcp_products import ROOT, local_folder, marker, tasks_for

from wildfire_risk_prediction import dataset_batch as batch
from wildfire_risk_prediction import feature_month
from wildfire_risk_prediction import observation_table as obs
from wildfire_risk_prediction.feature_join import require

NATIVE = (
    "outputs/gcp_delivery/2026-10-14/compact/audit/20261014T120616395916Z/accepted_readback.json"
)
NATIVE_SHA = "52be7c3e8fb02798a1e21538607a4612a0c479c105b90157b195385eea4d6781"
DELIVERY = "outputs/gcp_delivery/2026-10-14/compact/receive_final_20261014T120535015447Z.json"
DELIVERY_SHA = "74827f6b182bc4acac4ab42651e7417daa9f1cbf974fd0c87aa52ab3e2eb9057"
JULY = "outputs/cloud_month/received/l2_month_2023_07_results.zip"
JULY_SHA = "d2c3fd4f057a093343da86eed2df78e205eed913fbd56878210361990f2e3857"
REGISTRY = "configs/gcp_source_blocks_2026-10-13.json"
REGISTRY_SHA = "c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95"
NAMES = {"area.csv", "centers.csv", "scan_grid.csv", "scans.csv", "report.json"}
COMPACT_SHA = "f09e73837732160a65cc059c382c2ed85a95de0985aa470c1ec5789f6dc17b54"
FEATURE_AUDIT = "outputs/reports/dataset/candidate_audit_v1/20261014T143254Z_0a72ff05/readback.json"
FEATURE_AUDIT_SHA = "c39536f74cf1b44dec1eec08b94941b495132e759d6ed0005a88110c1f46dbe8"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked(name, expected):
    data = (ROOT / name).read_bytes()
    require(sha(data) == expected, "Pinned observation input changed")
    return json.loads(data)


def deny(*args, **kwargs):
    raise RuntimeError("Offline observation materialization")


def tables(archive, day, prefix, parts_sha):
    report = json.loads(archive.read(prefix + "report.json"))
    require(
        report["day"] == day
        and report["parts_sha256"] == parts_sha
        and report["compact_code_sha256"] == COMPACT_SHA
        and report["negative_label_permitted"] is False
        and report["daily_observation_status"] == "unknown",
        "Accepted daily compact identity",
    )
    frames = []
    for name in ("area.csv", "centers.csv"):
        data = archive.read(prefix + name)
        require(sha(data) == report["outputs_sha256"][name], "Daily selected table hash")
        frames.append(pd.read_csv(io.BytesIO(data), float_precision="round_trip"))
    return frames


def materialize_month(month, context, out, deadline):
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    require(time.monotonic() < deadline, "Observation runtime reserve")
    days = feature_month.calendar_days(month)
    folder = out / month
    folder.mkdir(exist_ok=False)
    compact = ROOT / "outputs/gcp_delivery/2026-10-14/compact"
    inputs = {}

    def payload(task):
        record = context["tasks"][task]
        source = local_folder(compact, task)
        receipt = marker((source / "completed.json").read_bytes(), task, context["worker"])
        data = (source / "payload.zip").read_bytes()
        require(
            len(data) == record["bytes"] == receipt["payload_bytes"]
            and sha(data) == record["sha256"] == receipt["payload_sha256"],
            "Accepted delivery payload identity",
        )
        inputs[(source / "payload.zip").relative_to(ROOT).as_posix()] = record["sha256"]
        return data

    archive = None
    if month == "2023-07":
        data = (ROOT / JULY).read_bytes()
        require(sha(data) == JULY_SHA, "Separate July reference bytes")
        archive = zipfile.ZipFile(io.BytesIO(data))
        expected = {"month_summary.json"} | {d + "/" + n for d in days for n in NAMES}
        require(
            len(archive.infolist()) == len(expected) and set(archive.namelist()) == expected,
            "Exact July reference members",
        )
        inputs[JULY] = JULY_SHA
    elif month not in {d[:7] for d in context["deferred"]}:
        archive = zipfile.ZipFile(io.BytesIO(payload("month:" + month)))
        expected = {"receipt.json"} | {d + ".zip" for d in days}
        require(
            len(archive.infolist()) == len(expected) and set(archive.namelist()) == expected,
            "Exact monthly compact members",
        )
    frames = []
    try:
        for day in days:
            require(time.monotonic() < deadline, "Observation runtime reserve")
            require(shutil.disk_usage(ROOT).free > 10 * 2**30, "Observation disk reserve")
            require(not (out / "PAUSE").exists(), "Observation pause requested")
            require(not (out / "STOP_REQUESTED").exists(), "Sibling observation failure")
            if day in context["deferred"]:
                frame = obs.diagnostic_day(day, context["grid_ids"])
            else:
                if month == "2023-07":
                    areas, centers = tables(archive, day, day + "/", context["parts_sha"])
                else:
                    data = archive.read(day + ".zip") if archive else payload("day:" + day)
                    with zipfile.ZipFile(io.BytesIO(data)) as daily:
                        require(
                            len(daily.infolist()) == len(NAMES) and set(daily.namelist()) == NAMES,
                            "Exact daily compact members",
                        )
                        areas, centers = tables(daily, day, "", context["parts_sha"])
                frame = obs.diagnostic_day(day, context["grid_ids"], areas, centers)
            frames.append(frame)
    finally:
        if archive:
            archive.close()
    frame = pd.concat(frames, ignore_index=True)
    stats = obs.summarize(frame)
    target = folder / "observations.csv.gz"
    frame.to_csv(
        target,
        index=False,
        mode="x",
        compression={"method": "gzip", "compresslevel": 1, "mtime": 0},
    )
    reread = pd.read_csv(target, float_precision="round_trip")
    pd.testing.assert_frame_equal(frame, reread, check_dtype=False, rtol=1e-12, atol=1e-12)
    require(obs.summarize(reread) == stats, "Observation sidecar readback")
    report = {
        "status": "observation_month_materialization_passed",
        "version": obs.VERSION,
        "month": month,
        "days": days,
        **stats,
        "table_sha256": sha(target.read_bytes()),
        "table_bytes": target.stat().st_size,
        "input_payload_sha256": inputs,
        "missing_source_days": [d for d in days if d in context["deferred"]],
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "diagnostics_are_model_inputs": False,
        "raw_reprocessed": False,
        "geometry_union_recomputed": False,
        "network_requests": 0,
    }
    (folder / "readback.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run(months, workers, hours):
    selected = months or [m["month"] for m in batch.calendar_inventory()]
    for month in selected:
        feature_month.calendar_days(month)
    require(len(selected) == len(set(selected)) and selected, "Unique training selection")
    require(1 <= workers <= 4 and 0 < hours <= 4, "Bounded observation resources")
    native, delivery, registry = (
        checked(p, h)
        for p, h in ((NATIVE, NATIVE_SHA), (DELIVERY, DELIVERY_SHA), (REGISTRY, REGISTRY_SHA))
    )
    require(
        native["status"] == "delivered_compact_native_readback_passed"
        and native["days_checked"] == 2158
        and native["negative_label_permitted"] is False,
        "Accepted native observation evidence",
    )
    spec = json.loads(
        (ROOT / "outputs/gcp_production/package/production_manifest.json").read_bytes()
    )
    require(
        sha((ROOT / "outputs/gcp_production/package/production_manifest.json").read_bytes())
        == delivery["scope_sha256"],
        "Frozen production scope",
    )
    tasks = {t["task_id"]: t for t in delivery["tasks"]}
    require(
        len(tasks) == len(delivery["tasks"]) == 199 and set(tasks) == set(tasks_for(spec)),
        "Exact accepted delivery task inventory",
    )
    parts = ROOT / "data/interim/grid_aoi_parts.geojson"
    feature_audit = checked(FEATURE_AUDIT, FEATURE_AUDIT_SHA)
    require(
        feature_audit["candidate_calendar_complete"] is True
        and feature_audit["verified_candidate_rows"] == 6351709
        and feature_audit["model_ready"] is False
        and feature_audit["labels_created"] is False,
        "Accepted feature-key scope, without labels",
    )
    first = batch.candidate_reference(feature_audit["reports"][0])
    first_report = checked(first["path"], first["sha256"])
    require(
        first_report["inputs_sha256"]["data/interim/grid_aoi_parts.geojson"]
        == sha(parts.read_bytes()),
        "Feature/observation grid identity",
    )
    grid = json.loads(parts.read_bytes())
    ids = sorted(f["properties"]["grid_id"] for f in grid["features"])
    require(len(ids) == len(set(ids)) == 2899, "Observation grid scope")
    context = {
        "tasks": tasks,
        "worker": spec["files"]["run_gcp_production.py"],
        "deferred": registry["deferred_days"],
        "grid_ids": ids,
        "parts_sha": sha(parts.read_bytes()),
    }
    base = ROOT / "outputs/reports/dataset/observation_materialization_v1"
    out = base / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    lock = ROOT / "outputs/cache/observation_materialization.lock"
    with lock.open("x", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid()}, stream)
    started = time.monotonic()
    state = {
        "status": "running",
        "selected_months": selected,
        "reports": [],
        "labels_created": False,
        "model_ready": False,
        "final_test_accessed": False,
    }
    pins = {
        NATIVE: NATIVE_SHA,
        DELIVERY: DELIVERY_SHA,
        REGISTRY: REGISTRY_SHA,
        FEATURE_AUDIT: FEATURE_AUDIT_SHA,
        first["path"]: first["sha256"],
        "data/interim/grid_aoi_parts.geojson": sha(parts.read_bytes()),
        "scripts/quality/materialize_observations.py": sha(Path(__file__).read_bytes()),
        "src/wildfire_risk_prediction/observation_table.py": sha(
            (ROOT / "src/wildfire_risk_prediction/observation_table.py").read_bytes()
        ),
    }
    for name in ("feature_join.py", "feature_month.py", "dataset_batch.py"):
        relative = "src/wildfire_risk_prediction/" + name
        pins[relative] = sha((ROOT / relative).read_bytes())

    def save():
        temporary = out / "progress.pending"
        temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        temporary.replace(out / "progress.json")

    try:
        save()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(materialize_month, m, context, out, started + hours * 3600)
                for m in selected
            ]
            for future in as_completed(futures):
                try:
                    report = future.result()
                except Exception:
                    (out / "STOP_REQUESTED").touch(exist_ok=False)
                    for pending in futures:
                        pending.cancel()
                    raise
                state["reports"].append(report)
                save()
                print(
                    "OBSERVATION MONTH",
                    report["month"],
                    len(state["reports"]),
                    "/",
                    len(selected),
                    flush=True,
                )
        require(
            all(sha((ROOT / p).read_bytes()) == h for p, h in pins.items()), "Input pins changed"
        )
        require(
            sorted(r["month"] for r in state["reports"]) == sorted(selected),
            "Complete selected observation months",
        )
        totals = {
            field: sum(r[field] for r in state["reports"])
            for field in (
                "rows",
                "rows_with_product",
                "rows_missing_product",
                "rows_with_cloud_centers",
                "rows_with_nominal_land_centers",
                "rows_with_nominal_or_high_thermal_centers",
            )
        }
        expected_days = sum(len(feature_month.calendar_days(m)) for m in selected)
        missing_days = [d for d in registry["deferred_days"] if d[:7] in selected]
        require(
            totals["rows"] == expected_days * 2899
            and totals["rows_missing_product"] == len(missing_days) * 2899,
            "Full calendar with explicit source gaps",
        )
        state.update(
            status="selected_observation_months_materialized",
            seconds=time.monotonic() - started,
            source_and_method_sha256=pins,
            daily_observation_status="unknown",
            negative_label_permitted=False,
            diagnostics_are_model_inputs=False,
            network_requests=0,
            scope_is_full_training=months is None,
            totals=totals,
            missing_source_days=missing_days,
        )
        save()
        (out / "accepted_readback.json").write_text(
            json.dumps(state, indent=2) + "\n", encoding="utf-8"
        )
    except Exception as error:
        state.update(status="stopped_results_retained", error_type=type(error).__name__)
        save()
        raise
    finally:
        lock.unlink()
    print("Observation result:", out.relative_to(ROOT).as_posix(), flush=True)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", nargs="+")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--hours-limit", type=float, default=2)
    args = parser.parse_args()
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run(args.months, args.workers, args.hours_limit)


if __name__ == "__main__":
    main()
