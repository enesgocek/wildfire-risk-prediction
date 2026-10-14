"""Offline native readback of delivered monthly/daily compact products, without raw replay."""

import argparse
import io
import json
import os
import shutil
import tempfile
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import gcp_production_support as support
from receive_gcp_products import MIN_FREE, ROOT, digest, local_folder, marker, preserve
from verified_job_store import require
from verify_gcp_production_session_results import check_journal, check_marker
from verify_gcp_v7_session_logs import DEFERRED, PARTIAL_DAYS, SCOPE


def checked_local(root, task, worker):
    folder = local_folder(root, task)
    record = marker((folder / "completed.json").read_bytes(), task, worker)
    data = (folder / "payload.zip").read_bytes()
    require(
        len(data) == record["payload_bytes"] and digest(data) == record["payload_sha256"],
        "Delivered file changed",
    )
    return record, data


def flat_zip(data, names):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        require(
            len(infos) == len(names) and {i.filename for i in infos} == set(names),
            "Exact ZIP members",
        )
        require(
            all(0 < i.file_size < 150_000_000 for i in infos)
            and sum(i.file_size for i in infos) < 300_000_000,
            "ZIP expanded bound",
        )
        require(archive.testzip() is None, "ZIP CRC")
        return {name: archive.read(name) for name in names}


def month_audit(root, run, month, deadline=None):
    with (
        patch("socket.socket", side_effect=RuntimeError("Offline socket boundary")),
        patch("socket.create_connection", side_effect=RuntimeError("Offline connection boundary")),
    ):
        return month_audit_offline(root, run, month, deadline)


def month_audit_offline(root, run, month, deadline=None):
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("Audit runtime limit")
    require(shutil.disk_usage(root).free >= MIN_FREE, "Audit disk reserve")
    package = ROOT / "outputs/gcp_production/package"
    spec, scope, catalogue, sources = support.read_scope(package)
    require(scope == SCOPE and month in spec["months"], "Training scope")
    worker = spec["files"]["run_gcp_production.py"]
    work = run / month
    work.mkdir(parents=True, exist_ok=False)
    core = work / "science"
    support.template(package, core)
    rows = sources.loc[sources.day.str.startswith(month)]
    _, metadata = checked_local(root, "manifest:" + month, worker)
    flat_zip(metadata, support.month_names(rows))
    manifest = work / "manifest.zip"
    preserve(manifest, metadata)
    target = core / "production_metadata"
    plan = support.validate_month(manifest, month, rows, catalogue, target)
    month_sha = support.digest(target / "month.json")
    compact, _ = support.science(core)
    selected = [d for d in plan["days"] if d not in DEFERRED]
    receipt = None
    if month not in {d[:7] for d in DEFERRED}:
        _, payload = checked_local(root, "month:" + month, worker)
        monthly = flat_zip(payload, {"receipt.json", *[d + ".zip" for d in selected]})
        receipt = json.loads(monthly["receipt.json"])
        require(
            receipt["month"] == month
            and receipt["month_manifest_sha256"] == month_sha
            and receipt["days"] == plan["days"]
            and set(receipt["day_records"]) == set(selected)
            and receipt["unpaired_catalogue_records"] == plan["unpaired_catalogue_records"]
            and receipt["negative_label_permitted"] is False
            and receipt["daily_observation_status"] == "unknown",
            "Monthly lineage/policy",
        )
    checked = []
    for day in selected:
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("Audit runtime limit")
        require(not (root / "PAUSE").exists(), "Audit pause requested")
        require(shutil.disk_usage(root).free >= MIN_FREE, "Audit disk reserve")
        if receipt is None:
            record, data = checked_local(root, "day:" + day, worker)
        else:
            record = receipt["day_records"][day]
            data = monthly[day + ".zip"]
        with tempfile.TemporaryDirectory(dir=work) as temporary:
            daily = Path(temporary)
            path = daily / "day.zip"
            preserve(path, data)
            check_marker(record, day, path, scope, worker)
            for name, value in flat_zip(data, set(compact.NAMES)).items():
                preserve(daily / name, value)
            pairs = [p for p in plan["pairs"] if p["start_utc"].startswith(day)]
            context = {
                "production_month_manifest_sha256": month_sha,
                "catalogue_gap_records": [
                    r for r in plan["unpaired_catalogue_records"] if r["day"] == day
                ],
            }
            report = compact.validate_day(daily, day, [p["sample_id"] for p in pairs], context)
            check_journal(report, pairs, core, compact)
            checked.append({"day": day, "pairs": len(pairs), "grid_rows": 2899})
    result = {
        "month": month,
        "days": checked,
        "metadata_sha256": digest(metadata),
        "month_manifest_sha256": month_sha,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "geometry_union_recomputed": False,
        "network_requests": 0,
        "raw_reprocessed": False,
    }
    preserve(work / "readback.json", (json.dumps(result, indent=2) + "\n").encode())
    return result


def audit(root, months=None, workers=2, hours_limit=2):
    require(
        root.resolve().is_relative_to((ROOT / "outputs/gcp_delivery").resolve()),
        "Delivery workspace boundary",
    )
    spec = support.checked_spec(ROOT / "outputs/gcp_production/package")[0]
    selected = sorted(set(spec["months"]) if months is None else set(months))
    require(selected and set(selected) <= set(spec["months"]), "Training months only")
    require(1 <= workers <= 4, "Bounded audit workers")
    require(0 < hours_limit <= 4, "Bounded audit runtime")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run = root / "audit" / stamp
    run.mkdir(parents=True, exist_ok=False)
    lock = root / "audit.lock"
    with lock.open("x", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid()}, stream)
    started = time.monotonic()
    deadline = started + hours_limit * 3600
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "GDAL_NUM_THREADS"):
        os.environ[key] = "1"
    try:
        results = []
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(month_audit, root, run, month, deadline) for month in selected]
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                pending = run / "progress.pending"
                pending.write_text(
                    json.dumps(
                        {
                            "status": "running",
                            "months": len(results),
                            "expected_months": len(selected),
                            "last_month": result["month"],
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                pending.replace(run / "progress.json")
                print(
                    "NATIVE READBACK",
                    result["month"],
                    len(result["days"]),
                    "days",
                    len(results),
                    "/",
                    len(selected),
                    flush=True,
                )
        all_days = [r["day"] for month in results for r in month["days"]]
        require(
            len(all_days) == len(set(all_days)) and not set(all_days) & DEFERRED,
            "Unique nondeferred calendar",
        )
        if months is None:
            require(
                len(all_days) == 2158 and PARTIAL_DAYS <= set(all_days), "Full deliverable days"
            )
        report = {
            "status": "delivered_compact_native_readback_passed",
            "recorded_at_utc": datetime.now(UTC).isoformat(),
            "months": results,
            "days_checked": len(all_days),
            "source_pairs_checked": sum(d["pairs"] for month in results for d in month["days"]),
            "seconds": time.monotonic() - started,
            "audit_script_sha256": digest(Path(__file__).read_bytes()),
            "workers": workers,
            "hours_limit": hours_limit,
            "july_reference_included": False,
            "negative_label_permitted": False,
            "daily_observation_status": "unknown",
            "raw_source_downloads": 0,
            "geometry_union_recomputed": False,
            "network_requests": 0,
            "limitation": "Native compact numeric/source/time readback; "
            "full pair geometry union not recomputed. July reference is separate.",
        }
        preserve(run / "accepted_readback.json", (json.dumps(report, indent=2) + "\n").encode())
        print("NATIVE READBACK COMPLETE", len(all_days), "days", run, flush=True)
        return report
    except Exception as error:
        (run / "stopped.json").write_text(
            json.dumps(
                {
                    "status": "stopped",
                    "failure_type": type(error).__name__,
                    "accepted_months_preserved": True,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--months", nargs="+")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--hours-limit", type=float, default=2)
    args = parser.parse_args()
    audit(args.root, args.months, args.workers, args.hours_limit)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            "Compact readback stopped:",
            type(error).__name__,
            "; no external text logged",
            flush=True,
        )
        raise SystemExit(1) from None
