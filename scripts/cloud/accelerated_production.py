"""All 71 remaining training months, legacy scientific checkpoint identities retained."""

import hashlib
import json
import shutil
import tempfile
import time
import zipfile
from pathlib import Path

import run_gcp_acceleration as control
from accelerated_checkpoint_store import AcceleratedCheckpointStore


def month_validator(runner, core, month, plan, month_sha, scope, worker):
    expected = {"receipt.json", *[day + ".zip" for day in plan["days"]]}

    def check(path):
        with zipfile.ZipFile(path) as archive:
            control.require(
                set(archive.namelist()) == expected
                and len(archive.namelist()) == len(expected)
                and archive.testzip() is None,
                "Monthly payload members/CRC",
            )
            receipt = json.loads(archive.read("receipt.json"))
            control.require(
                receipt["month"] == month
                and receipt["month_manifest_sha256"] == month_sha
                and receipt["days"] == plan["days"]
                and receipt["unpaired_catalogue_records"] == plan["unpaired_catalogue_records"]
                and receipt["negative_label_permitted"] is False
                and receipt["daily_observation_status"] == "unknown"
                and set(receipt["day_records"]) == set(plan["days"]),
                "Monthly lineage/policy",
            )
            for day in plan["days"]:
                record = receipt["day_records"][day]
                content = archive.read(day + ".zip")
                task = "day:" + day
                prefix = f"jobs/{scope}/{hashlib.sha256(task.encode()).hexdigest()}"
                control.require(
                    set(record)
                    == {
                        "protocol",
                        "task_id",
                        "manifest_sha256",
                        "worker_sha256",
                        "payload_sha256",
                        "payload_bytes",
                        "payload_key",
                        "negative_label_permitted",
                        "daily_observation_status",
                    }
                    and record["protocol"] == "verified_job_checkpoint_v1"
                    and record["task_id"] == task
                    and record["manifest_sha256"] == scope
                    and record["worker_sha256"] == worker
                    and record["negative_label_permitted"] is False
                    and record["daily_observation_status"] == "unknown"
                    and record["payload_bytes"] == len(content)
                    and record["payload_sha256"] == hashlib.sha256(content).hexdigest()
                    and record["payload_key"] == prefix + "/" + record["payload_sha256"] + ".zip",
                    "Monthly nested completion",
                )
                pairs = [p for p in plan["pairs"] if p["start_utc"].startswith(day)]
                lineage = {
                    "production_month_manifest_sha256": month_sha,
                    "catalogue_gap_records": [
                        r for r in plan["unpaired_catalogue_records"] if r["day"] == day
                    ],
                }
                with tempfile.TemporaryDirectory(dir=core) as directory:
                    nested = Path(directory) / "day.zip"
                    nested.write_bytes(content)
                    runner.restore_daily(nested, core, day, pairs, lineage)
                runner.owned_remove(core / ("restored_" + day), core)

    return expected, check


def run(args, runner, spec, controller_scope, auth, reference, deadline, sampler, work):
    require = control.require
    gate = control.read_gate(args, controller_scope)
    slots, reducers = gate["pair_slots"], gate["daily_slots"]
    original_spec, scientific_scope, catalogue, sources = runner.read_scope(control.ORIGINAL)
    require(scientific_scope == control.ORIGINAL_SCOPE, "Legacy resume scope")
    adapter = control.backend(args, scientific_scope)
    store = AcceleratedCheckpointStore(
        adapter, scientific_scope, original_spec["files"]["run_gcp_production.py"], 200_000_000_000
    )
    core = work / "accelerated_core"
    runner.template(control.ORIGINAL, core)
    state = {
        "status": "running",
        "queue_manifest_sha256": scientific_scope,
        "controller_manifest_sha256": controller_scope,
        "cpu_count": args.cpus,
        "pair_workers": slots,
        "daily_workers": reducers,
        "existing_months": ["2023-07"],
        "days_verified_this_invocation": [],
        "pairs_processed_this_invocation": 0,
        "pairs_reused_this_invocation": 0,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "actual_vm_termination_timestamp": args.termination,
    }
    control.atomic(work / "progress.json", state)

    def update(kind, identity, record):
        if kind in {"day_saved", "day_reused"}:
            require(
                identity not in state["days_verified_this_invocation"], "Duplicate production day"
            )
            state["days_verified_this_invocation"].append(identity)
        else:
            field = (
                "pairs_processed_this_invocation"
                if kind == "pair_saved"
                else "pairs_reused_this_invocation"
            )
            state[field] += 1
        control.atomic(work / "progress.json", state)

    try:
        for month in original_spec["months"]:
            if sampler.failed or time.monotonic() + 1200 >= deadline:
                break
            sampler.arm, sampler.phase = month, "metadata"
            rows = sources.loc[sources.day.str.startswith(month)]
            directory = work / "months" / month
            directory.mkdir(exist_ok=True, parents=True)
            meta = directory / "metadata"

            def metadata_check(path, month=month, rows=rows, meta=meta):
                return runner.validate_month(path, month, rows, catalogue, meta)

            prior = store.restore("manifest:" + month, runner.month_names(rows), metadata_check)
            if prior is None:
                cache = directory / "public_cache"
                cache.mkdir(exist_ok=True)
                print("Preparing verified metadata:", month, "sources:", len(rows), flush=True)
                runner.build_month(month, rows, catalogue, cache, meta)
                runner.pack_flat(meta, runner.month_names(rows), directory / "manifest.zip")
                store.save(
                    "manifest:" + month,
                    directory / "manifest.zip",
                    runner.month_names(rows),
                    metadata_check,
                )
            plan_path = meta / "month.json"
            plan = json.loads(plan_path.read_text())
            month_sha = control.digest(plan_path)
            month_core = directory / "accelerated_science"
            runner.ensure_root(month_core, core, meta, plan["pairs"])
            names, check = month_validator(
                runner, month_core, month, plan, month_sha, scientific_scope, store.worker_sha
            )
            prior = store.restore("month:" + month, names, check)
            if prior:
                state["existing_months"].append(month)
                for pair in plan["pairs"]:
                    runner.cleanup_committed_task(work, pair["sample_id"])
                control.atomic(work / "progress.json", state)
                runner.owned_remove(month_core, directory)
                print("Month verified/reused:", month, flush=True)
                continue
            scratch = directory / "accelerated_run"
            scratch.mkdir(exist_ok=True)
            result = control.pipeline(
                runner,
                reference,
                scratch,
                core,
                meta,
                plan_path,
                plan,
                plan["days"],
                store,
                auth,
                deadline,
                sampler,
                month,
                slots,
                reducers,
                progress=update,
            )
            archives = directory / "daily_archives"
            archives.mkdir(exist_ok=True)
            for day in result["day_records"]:
                shutil.copyfile(scratch / (day + ".zip"), archives / (day + ".zip"))
            if result["status"] != "complete" or time.monotonic() + 300 >= deadline:
                break
            control.atomic(
                archives / "receipt.json",
                {
                    "month": month,
                    "month_manifest_sha256": month_sha,
                    "days": plan["days"],
                    "day_records": result["day_records"],
                    "unpaired_catalogue_records": plan["unpaired_catalogue_records"],
                    "negative_label_permitted": False,
                    "daily_observation_status": "unknown",
                },
            )
            runner.pack_flat(archives, names, directory / "month_results.zip")
            store.save("month:" + month, directory / "month_results.zip", names, check)
            state["existing_months"].append(month)
            control.atomic(work / "progress.json", state)
            runner.owned_remove(month_core, directory)
            print("MONTH NOMINAL DIAGNOSTICS COMPLETE:", month, flush=True)
        state["status"] = (
            "all_training_months_verified"
            if len(state["existing_months"]) == 72
            else "paused_at_runtime_reserve"
        )
    except Exception as error:
        reference.kill_active()
        state.update(
            status="failed_checkpoints_retained",
            error_type=type(error).__name__,
            failed_phase=sampler.phase,
            failed_month=sampler.arm,
        )
        raise
    finally:
        control.atomic(work / "progress.json", state)
        control.atomic(work / "acceleration_run_summary.json", state)
