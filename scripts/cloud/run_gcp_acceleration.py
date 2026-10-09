"""Pinned external controller; unchanged scientific children and legacy resume namespace."""

import argparse
import contextlib
import datetime as dt
import getpass
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ORIGINAL_SCOPE = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
ORIGINAL = Path.home() / "wildfire-gcp-production-package"
PRODUCTION = Path.home() / "wildfire-gcp-production-v1"
PACKAGE = Path(__file__).resolve().parent


def require(ok, label):
    if not ok:
        raise ValueError(label)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".pending")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def checked():
    global \
        AcceleratedCheckpointStore, \
        IndexedDriveStore, \
        pair_validator, \
        execute, \
        Sampler, \
        memory_values
    spec = json.loads((PACKAGE / "acceleration_manifest.json").read_text())
    require(
        spec["protocol"] == "gcp_acceleration_controller_v1"
        and spec["training_scope_sha256"] == ORIGINAL_SCOPE
        and spec["negative_label_permitted"] is False,
        "Controller scope/policy",
    )
    expected = {
        "run_gcp_acceleration.py",
        "accelerated_production.py",
        "accelerated_pipeline.py",
        "accelerated_checkpoint_store.py",
        "gcp_tuning_resources.py",
        "reference_tuning.py",
        "proof_plan.json",
        "month_manifest.zip",
    }
    require(set(spec["files"]) == expected, "Controller member population")
    for name, checksum in spec["files"].items():
        require(
            not (PACKAGE / name).is_symlink() and digest(PACKAGE / name) == checksum,
            "Controller member SHA",
        )
    require(
        digest(ORIGINAL / "production_manifest.json") == ORIGINAL_SCOPE, "Frozen original scope"
    )
    original = json.loads((ORIGINAL / "production_manifest.json").read_text())
    require(len(original["files"]) == 11, "Original member count")
    for name, checksum in original["files"].items():
        require(
            Path(name).name == name
            and not (ORIGINAL / name).is_symlink()
            and digest(ORIGINAL / name) == checksum,
            "Frozen original member SHA",
        )
    sys.path.insert(0, str(ORIGINAL))
    from accelerated_checkpoint_store import (
        AcceleratedCheckpointStore,
        IndexedDriveStore,
        pair_validator,
    )
    from accelerated_pipeline import execute
    from gcp_tuning_resources import Sampler, memory_values

    worker = importlib.import_module("run_gcp_production")
    require(
        Path(worker.__file__).resolve() == (ORIGINAL / "run_gcp_production.py").resolve(),
        "Frozen worker import identity",
    )
    return (
        spec,
        digest(PACKAGE / "acceleration_manifest.json"),
        worker,
    )


@contextlib.contextmanager
def production_lock():
    import fcntl

    path = PRODUCTION / "job.lock"
    require(path.is_file() and not path.is_symlink(), "Original production lock")
    with path.open("r+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def budget(value, proof, now=None):
    now = now or dt.datetime.now(dt.UTC)
    finish = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(finish.tzinfo is not None, "Deadline timezone")
    require(finish < dt.datetime(2026, 10, 24, tzinfo=dt.UTC), "Trial cutoff")
    remaining = (finish - now).total_seconds()
    require(4200 <= remaining <= (7260 if proof else 28860), "Actual two/eight-hour deadline")
    return min(5400, remaining - 900) if proof else remaining - 300


def reference_driver():
    module = importlib.import_module("reference_tuning")
    module.ORIGINAL = ORIGINAL
    return module


def backend(args, scope):
    store = IndexedDriveStore.from_file(args.connection)
    store.api.token()
    quota = json.loads(store.api.request("/about?fields=storageQuota(limit,usage)"))["storageQuota"]
    require(
        "limit" not in quota or int(quota["limit"]) - int(quota["usage"]) > 5 * 2**30,
        "Drive storage reserve",
    )
    store.used_bytes("jobs/" + scope)
    return store


def read_gate(args, scope):
    require(
        args.gate is not None and args.gate_sha is not None and digest(args.gate) == args.gate_sha,
        "Verified production gate required",
    )
    gate = json.loads(args.gate.read_text())
    require(
        gate["protocol"] == "gcp_acceleration_ready_v1"
        and gate["controller_manifest_sha256"] == scope
        and gate["status"] == "independent_acceleration_readback_passed"
        and gate["cpus"] == args.cpus
        and gate["baseline_stable"] is True
        and gate["negative_label_permitted"] is False
        and gate["daily_observation_status"] == "unknown"
        and gate["verified_daily_payloads"] == 12,
        "Production gate identity/measurement",
    )
    slots, reducers = gate["pair_slots"], gate["daily_slots"]
    require(
        type(slots) is int
        and type(reducers) is int
        and 1 <= slots <= 24
        and 1 <= reducers <= 4
        and slots + reducers + 1 <= args.cpus,
        "Production worker CPU budget",
    )
    return gate


def export_proof(work):
    target = Path.home() / "gcp_acceleration_results.zip"
    require(not target.exists(), "Proof export collision")
    pending = target.with_suffix(".pending")
    require(not pending.exists(), "Pending proof export collision")
    with zipfile.ZipFile(pending, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in ("result_summary.json", "resource_samples.csv"):
            z.write(work / name, name)
        for name in ("acceleration_manifest.json", "proof_plan.json", "month_manifest.zip"):
            z.write(PACKAGE / name, name)
        for root in sorted(
            p for p in work.iterdir() if p.is_dir() and p.name.startswith(("baseline", "pipeline"))
        ):
            for path in sorted(root.glob("*.zip")):
                z.write(path, root.name + "/" + path.name)
            if (root / "arm_summary.json").is_file():
                z.write(root / "arm_summary.json", root.name + "/arm_summary.json")
    require(pending.stat().st_size < 150_000_000, "Proof export byte bound")
    with zipfile.ZipFile(pending) as archive:
        require(archive.testzip() is None, "Proof export CRC")
    pending.replace(target)
    print("Download:", target, flush=True)


def supervise(args, runner, spec, scope, auth, reference, seconds, work):
    # Shutdown also runs if telemetry, integrity recheck or export fails.
    # The lock must be acquired first: a rejected duplicate never stops the owner.
    with production_lock():
        sampler, cancel = None, None
        try:
            work.mkdir(mode=0o700, exist_ok=args.mode == "production")
            deadline = time.monotonic() + seconds
            sampler = Sampler(work)
            sampler.begin()
            cancel = reference.install_alarm(deadline)
            if args.mode == "proof":
                proof(args, runner, spec, scope, auth, reference, deadline, sampler, work)
            else:
                module = importlib.import_module("accelerated_production")
                module.run(args, runner, spec, scope, auth, reference, deadline, sampler, work)
        except Exception as error:
            if args.mode == "proof" and not (work / "result_summary.json").exists():
                atomic(
                    work / "result_summary.json",
                    {
                        "status": "partial_proof_retained",
                        "arms": [],
                        "controller_manifest_sha256": scope,
                        "original_scope_sha256": ORIGINAL_SCOPE,
                        "cpus": args.cpus,
                        "failed_phase": "preparation",
                        "error_type": type(error).__name__,
                        "negative_label_permitted": False,
                        "daily_observation_status": "unknown",
                        "production_months_added": 0,
                        "production_progress_unchanged": False,
                        "resource_guard_hit": sampler.failed if sampler else True,
                    },
                )
            raise
        finally:
            try:
                try:
                    if cancel:
                        cancel()
                finally:
                    try:
                        reference.kill_active()
                    finally:
                        if sampler:
                            sampler.close()
                checked()
                if args.mode == "proof":
                    export_proof(work)
            finally:
                if args.poweroff:
                    result = subprocess.run(
                        ["sudo", "-n", "shutdown", "-h", "now"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=30,
                    )
                    print("Guest poweroff requested:", result.returncode == 0, flush=True)


def pipeline(
    runner,
    reference,
    work,
    core,
    meta,
    plan_path,
    plan,
    days,
    store,
    auth,
    deadline,
    sampler,
    label,
    pair_slots,
    day_slots,
    references=None,
    progress=None,
):
    month_sha = digest(plan_path)
    records, daily, publication = [], [], 0.0
    started = time.monotonic()

    def prepare(day):
        sampler.phase = "prepare_day"
        pairs = [p for p in plan["pairs"] if p["start_utc"].startswith(day)]
        require(pairs, "Day with no nominal pairs")
        root = work / "days" / day
        runner.ensure_root(root, core, meta, pairs)
        lineage = {
            "production_month_manifest_sha256": month_sha,
            "catalogue_gap_records": [
                r for r in plan["unpaired_catalogue_records"] if r["day"] == day
            ],
        }
        state = {"day": day, "pairs": pairs, "root": root, "lineage": lineage, "pending": []}

        def day_check(path):
            return runner.restore_daily(path, root, day, pairs, lineage)

        state["check"] = day_check
        compact, _ = runner.science(root)
        state["names"] = set(compact.NAMES)
        if references is None:
            prior = store.restore("day:" + day, state["names"], day_check)
            if prior:
                payload = store.backend.get(prior["payload_key"])
                require(
                    payload is not None
                    and hashlib.sha256(payload).hexdigest() == prior["payload_sha256"],
                    "Reused daily bytes",
                )
                (work / (day + ".zip")).write_bytes(payload)
                state["reused"] = prior
                if progress:
                    progress("day_reused", day, prior)
                runner.owned_remove(root, work / "days")
                return state
        for pair in pairs:
            native, check = pair_validator(runner, root, pair, month_sha)
            prior = (
                None
                if references
                else store.restore(pair["sample_id"], runner.pair_names(pair, native), check)
            )
            if prior:
                if progress:
                    progress("pair_reused", pair["sample_id"], prior)
            else:
                state["pending"].append(pair)
        return state

    def launch_pair(state, pair):
        root = work / "tasks" / hashlib.sha256(pair["sample_id"].encode()).hexdigest()
        require(
            shutil.disk_usage(work).free
            > 6 * 2**30 + sum(s["bytes"] for s in pair["sources"]) + 300_000_000,
            "Pair scratch reserve",
        )
        # Directory preparation is data copying, never a scientific module call.
        runner.ensure_root(root, core, meta, [pair])
        seconds = reference.run_child(
            runner, "pair", root, plan_path, pair["sample_id"], auth, deadline, sampler
        )
        return root, seconds

    def publish_pair(state, pair, value):
        nonlocal publication
        sampler.phase = "pair_publication"
        root, child_seconds = value
        native, scientific = pair_validator(runner, state["root"], pair, month_sha)

        def check(path):
            result = scientific(path)
            if references is not None:
                expected = references[pair["sample_id"]]
                require(
                    result["metrics"]["downloaded_payload_bytes"]
                    == sum(s["bytes"] for s in pair["sources"]),
                    "Proof cold source bytes",
                )
                audit = json.loads(
                    (state["root"] / "inputs" / (pair["stem"] + "_audit.json")).read_text()
                )
                require(
                    all(
                        audit["sources"][role]["sha256"] == checksum
                        for role, checksum in expected["source_sha256"].items()
                    ),
                    "Proof raw SHA",
                )
                require(
                    all(
                        digest(state["root"] / "inputs" / (pair["stem"] + "_" + suffix)) == checksum
                        for suffix, checksum in expected["exact_csv_sha256"].items()
                    ),
                    "Proof native CSV SHA",
                )
            return result

        task = label + ":" + pair["sample_id"] if references is not None else pair["sample_id"]
        tick = time.monotonic()
        marker = store.save(task, root / "pair.zip", runner.pair_names(pair, native), check)
        publication += time.monotonic() - tick
        checkpoint = json.loads(
            (state["root"] / "inputs" / (pair["stem"] + "_checkpoint.json")).read_text()
        )
        records.append(
            {
                "sample_id": pair["sample_id"],
                "child_wall_seconds": child_seconds,
                "metrics": checkpoint["metrics"],
                "completion": marker,
            }
        )
        if progress:
            progress("pair_saved", pair["sample_id"], marker)
        runner.owned_remove(root, work / "tasks")
        print(label, "pair saved/verified", pair["sample_id"], flush=True)

    def launch_day(state):
        seconds = reference.run_child(
            runner, "day", state["root"], plan_path, state["day"], None, deadline, sampler
        )
        return seconds

    def publish_day(state, seconds):
        nonlocal publication
        sampler.phase = "daily_publication"
        day = state["day"]
        task = label + ":day:" + day if references is not None else "day:" + day
        tick = time.monotonic()
        marker = store.save(task, state["root"] / "day.zip", state["names"], state["check"])
        elapsed = time.monotonic() - tick
        publication += elapsed
        shutil.copyfile(state["root"] / "day.zip", work / (day + ".zip"))
        daily.append(
            {
                "day": day,
                "reduce_seconds": seconds,
                "publish_seconds": elapsed,
                "completion": marker,
            }
        )
        if progress:
            progress("day_saved", day, marker)
        runner.owned_remove(state["root"], work / "days")
        print("DAY COMMITTED", day, flush=True)
        return marker

    result = execute(
        days,
        prepare,
        launch_pair,
        publish_pair,
        launch_day,
        publish_day,
        pair_slots,
        day_slots,
        deadline,
        lambda: not sampler.failed,
        reference.kill_active,
        reserve=1200,
        window=min(6, max(3, day_slots + 1)),
    )
    result.update(
        arm=label,
        workers=pair_slots,
        daily_workers=day_slots,
        pair_count=len(records),
        day_count=len(result["day_records"]),
        wall_seconds=time.monotonic() - started,
        total_publication_seconds=publication,
        pair_publication_seconds=publication - sum(d["publish_seconds"] for d in daily),
        pairs=records,
        days=daily,
        resources=sampler.summary(label),
    )
    result["pairs_per_hour"] = len(records) * 3600 / result["wall_seconds"]
    atomic(work / "arm_summary.json", result)
    return result


def proof(args, runner, spec, scope, auth, reference, deadline, sampler, work):
    old_progress = digest(PRODUCTION / "progress.json")
    _, _, catalogue, sources = runner.read_scope(ORIGINAL)
    meta = work / "metadata"
    plan = runner.validate_month(
        PACKAGE / "month_manifest.zip",
        "2023-10",
        sources.loc[sources.day.str.startswith("2023-10")],
        catalogue,
        meta,
    )
    approved = json.loads((PACKAGE / "proof_plan.json").read_text())
    selected = [p for p in plan["pairs"] if p["sample_id"] in approved["sample_ids"]]
    require(
        [p["sample_id"] for p in selected] == approved["sample_ids"] and len(selected) == 28,
        "Matched proof population",
    )
    require(digest(meta / "month.json") == spec["month_manifest_sha256"], "Proof month SHA")
    core = work / "core"
    runner.template(ORIGINAL, core)
    fast_backend = backend(args, scope)
    require(fast_backend.used_bytes("jobs/" + scope) == 0, "Existing proof namespace")
    scaled, day_slots = {8: (6, 1), 16: (12, 2), 32: (24, 4)}[args.cpus]
    profiles = [
        ("baseline_before", 8),
        ("pipeline_eight", 8),
        ("pipeline_scaled", scaled),
        ("baseline_after", 8),
    ]
    arms = []
    summary = {
        "status": "running",
        "arms": arms,
        "profiles": profiles,
        "cpus": args.cpus,
        "controller_manifest_sha256": scope,
        "original_scope_sha256": ORIGINAL_SCOPE,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "production_months_added": 0,
        "actual_vm_termination_timestamp": args.termination,
    }
    try:
        for label, slots in profiles:
            require(
                time.monotonic() + 1500 < deadline and not sampler.failed, "Proof admission reserve"
            )
            sampler.arm, sampler.phase = label, "profile_setup"
            root = work / label
            root.mkdir()
            print("PROFILE START", label, "workers", slots, flush=True)
            if label.startswith("baseline"):
                legacy_backend = runner.ProductionDriveStore.from_file(args.connection)
                reference.WORK = work
                root.rmdir()  # The pinned reference engine insists on a fresh root.
                store = runner.VerifiedJobStore(
                    legacy_backend, scope, spec["files"]["run_gcp_acceleration.py"], 2 * 2**30
                )
                result = reference.execute_arm(
                    label,
                    slots,
                    runner,
                    core,
                    meta,
                    meta / "month.json",
                    plan,
                    selected,
                    approved["references"],
                    store,
                    auth,
                    deadline,
                    sampler,
                )
            else:
                fast_backend.index.pop(scope, None)  # Earlier profiles used another adapter.
                store = AcceleratedCheckpointStore(
                    fast_backend, scope, spec["files"]["run_gcp_acceleration.py"], 2 * 2**30
                )
                result = pipeline(
                    runner,
                    reference,
                    root,
                    core,
                    meta,
                    meta / "month.json",
                    plan,
                    approved["days"],
                    store,
                    auth,
                    deadline,
                    sampler,
                    label,
                    slots,
                    1 if label == "pipeline_eight" else day_slots,
                    approved["references"],
                )
                require(result["status"] == "complete", "Partial proof profile")
            arms.append(result)
            print("PROFILE COMPLETE", label, round(result["wall_seconds"], 2), flush=True)
        summary["status"] = "all_profiles_completed"
    except Exception as error:
        reference.kill_active()
        summary.update(
            status="partial_proof_retained",
            error_type=type(error).__name__,
            failed_arm=sampler.arm,
            failed_phase=sampler.phase,
        )
    finally:
        summary["production_progress_unchanged"] = (
            digest(PRODUCTION / "progress.json") == old_progress
        )
        summary["resource_guard_hit"] = sampler.failed
        atomic(work / "result_summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["proof", "production"], required=True)
    parser.add_argument("--cpus", type=int, choices=[8, 16, 32], required=True)
    parser.add_argument("--connection", type=Path, required=True)
    parser.add_argument("--termination", required=True)
    parser.add_argument("--poweroff", action="store_true")
    parser.add_argument("--supervise", action="store_true")
    parser.add_argument("--auth-fd", type=int)
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--gate-sha")
    args = parser.parse_args()
    spec, scope, runner = checked()
    require(
        sys.platform == "linux"
        and sys.version_info[:2] == (3, 12)
        and sys.prefix != sys.base_prefix,
        "Existing Linux Python venv",
    )
    runner.vm_identity()
    require(os.cpu_count() == args.cpus, "Actual CPU count")
    require(
        memory_values(Path("/proc/meminfo").read_text())[0] >= max(24, args.cpus * 2) * 2**30,
        "Actual memory reserve",
    )
    seconds = budget(args.termination, args.mode == "proof")
    if args.mode == "production":
        read_gate(args, scope)
    work = (
        (Path.home() / "wildfire-gcp-acceleration-proof-v1") if args.mode == "proof" else PRODUCTION
    )
    if not args.supervise:
        with production_lock():
            pass
        require(args.mode != "proof" or not work.exists(), "Existing proof; refuse cold repeat")
        require(
            subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60,
            ).returncode
            == 0,
            "Dependencies",
        )
        import rasterio

        with rasterio.Env() as environment:
            require("HDF5" in environment.drivers(), "HDF5 driver")
        require(
            not args.poweroff
            or subprocess.run(
                ["sudo", "-n", "true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).returncode
            == 0,
            "Shutdown privilege",
        )
        auth = {
            "username": getpass.getpass("Earthdata kullanıcı adı (gizli): "),
            "password": getpass.getpass("Earthdata parola (gizli): "),
        }
        require(
            all(isinstance(v, str) and 0 < len(v) <= 2048 for v in auth.values()),
            "Credentials required",
        )
        data = json.dumps(auth).encode()
        require(len(data) <= 8192, "Credential pipe bound")
        read_fd, write_fd = os.pipe()
        command = [
            sys.executable,
            str(Path(__file__)),
            "--supervise",
            "--mode",
            args.mode,
            "--cpus",
            str(args.cpus),
            "--connection",
            str(args.connection.resolve()),
            "--termination",
            args.termination,
            "--auth-fd",
            str(read_fd),
        ]
        if args.poweroff:
            command.append("--poweroff")
        if args.mode == "production":
            command.extend(["--gate", str(args.gate.resolve()), "--gate-sha", args.gate_sha])
        with (Path.home() / "gcp_acceleration_launcher.log").open("ab") as log:
            proc = subprocess.Popen(
                command,
                pass_fds=(read_fd,),
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                env=runner.environment(),
            )
        os.close(read_fd)
        os.write(write_fd, data)
        os.close(write_fd)
        print("Detached acceleration launch requested; PID:", proc.pid)
        return
    auth = runner.read_auth(args.auth_fd)
    reference = reference_driver()
    supervise(args, runner, spec, scope, auth, reference, seconds, work)


if __name__ == "__main__":
    sys.modules["run_gcp_acceleration"] = sys.modules[__name__]
    os.umask(0o077)
    try:
        main()
    except Exception as error:
        print(
            "Acceleration stopped:",
            type(error).__name__,
            "; no external/credential text logged",
            flush=True,
        )
        raise SystemExit(1) from None
