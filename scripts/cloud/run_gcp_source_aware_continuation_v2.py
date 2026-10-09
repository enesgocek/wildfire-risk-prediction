"""Resume frozen production while explicitly deferring one unresolved source day.

Scheduling and safe diagnostics are external to immutable scientific packages.
No scientific checks, scope data, checkpoint keys or readiness gate are changed.
"""

import argparse
import ast
import contextlib
import getpass
import hashlib
import importlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

DIAGNOSTIC_SHA = "e1402d4cb28263fe8d05c474656ed64094cd069ca77040ed09e6d0a7296a9c63"

ORIGINAL_SCOPE = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
CONTROLLER_SCOPE = "102c9e4ab16e4450d0d94eb3511dfdbf360fd6b6292809c5457efc93d2be5837"
MONTH_SHA = "7f44606b19aab60fe75392f8df7e6951143892caf94e58eb6b23b2bfc5f19685"
GATE_SHA = "ac1f974daaf97a0a8392e9d6b225b4a7753147a9e527ec05caca4e6ea1cac3ef"
BLOCKED_DAY = "2023-12-31"
EXPECTED = {
    "SNPP:2023365.0106": "VNP03IMG.A2023365.0106.002.2023365074552.nc",
    "SNPP:2023365.1048": "VNP03IMG.A2023365.1048.002.2023365174608.nc",
}


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def registry(path, checksum):
    require(
        not path.is_symlink() and 0 < path.stat().st_size < 65536 and sha(path) == checksum,
        "Pinned source-block registry",
    )
    value = json.loads(path.read_bytes())
    require(
        value["protocol"] == "gcp_unresolved_source_registry_v1"
        and value["original_scope_sha256"] == ORIGINAL_SCOPE
        and value["controller_scope_sha256"] == CONTROLLER_SCOPE
        and value["month_plan_sha256"] == MONTH_SHA
        and value["deferred_days"] == [BLOCKED_DAY]
        and value["negative_label_permitted"] is False
        and value["daily_observation_status"] == "unknown"
        and value["full_training_complete"] is False,
        "Source-block scope and policy",
    )
    require(
        {r["sample_id"]: r["required_geolocation"] for r in value["blocked_pairs"]} == EXPECTED
        and len(value["blocked_pairs"]) == 2,
        "Exactly two proven source blocks",
    )
    return value


class RunnerPhase:
    """Validate the full sealed catalogue first; only change month scheduling."""

    def __init__(self, runner, phase):
        self.runner, self.phase = runner, phase

    def __getattr__(self, name):
        return getattr(self.runner, name)

    def read_scope(self, package):
        spec, scope, catalogue, sources = self.runner.read_scope(package)
        require(scope == ORIGINAL_SCOPE, "Unchanged scientific resume scope")
        months = spec["months"]
        require(
            len(months) == 71
            and months[:5] == ["2023-08", "2023-09", "2023-10", "2023-11", "2023-12"],
            "Sealed month order",
        )
        chosen = months[:5] if self.phase == "december_safe_days" else months[5:]
        return {**spec, "months": chosen}, scope, catalogue, sources


def filtered_pipeline(original, *args, **kwargs):
    """The deferred day never reaches reduction or a daily/monthly completion."""
    plan, days = args[6], args[7]
    if plan["month"] != "2023-12":
        return original(*args, **kwargs)
    require(
        plan["negative_label_permitted"] is False
        and sha(args[5]) == MONTH_SHA
        and BLOCKED_DAY in days,
        "Exact December day filter",
    )
    changed = list(args)
    changed[7] = [d for d in days if d != BLOCKED_DAY]
    result = original(*changed, **kwargs)
    require(BLOCKED_DAY not in result["day_records"], "Deferred day must remain uncommitted")
    if result["status"] == "complete":
        result["status"] = "deferred_source_lineage"
    return result


def merged(states, current, phase, registry_sha, wrapper_sha):
    rows = [*states, current]
    value = dict(current)
    value["existing_months"] = sorted({m for s in rows for m in s["existing_months"]})
    value["days_verified_this_invocation"] = sorted(
        {d for s in rows for d in s["days_verified_this_invocation"]}
    )
    for key in ("pairs_processed_this_invocation", "pairs_reused_this_invocation"):
        value[key] = sum(s[key] for s in rows)
    require(
        BLOCKED_DAY not in value["days_verified_this_invocation"]
        and "2023-12" not in value["existing_months"],
        "Unresolved December cannot be complete",
    )
    if len(value["existing_months"]) == 71 and value["status"] != "failed_checkpoints_retained":
        value["status"] = "processable_months_verified_source_resolution_pending"
    value.update(
        continuation_phase=phase,
        deferred_days=[BLOCKED_DAY],
        deferred_months=["2023-12"],
        blocked_pairs=sorted(EXPECTED),
        source_block_registry_sha256=registry_sha,
        continuation_wrapper_sha256=wrapper_sha,
        full_training_complete=False,
    )
    return value


def run_phases(
    control, original_run, args, runner, spec, scope, auth, reference, deadline, sampler, work
):
    states = []
    control.atomic(work / "source_blocks.json", registry(args.registry, args.registry_sha))
    for phase in ("december_safe_days", "remaining_months"):
        if sampler.failed or time.monotonic() + 1200 >= deadline:
            break
        print("CONTINUATION PHASE", phase, "deferred day", BLOCKED_DAY, flush=True)
        # This is a scheduling wrapper, not a change to native science or stored code.
        original_pipeline, original_atomic = control.pipeline, control.atomic
        control.pipeline = lambda *a, _pipeline=original_pipeline, **k: filtered_pipeline(
            _pipeline, *a, **k
        )
        latest = {}

        def live_atomic(path, value, _phase=phase, _latest=latest, _atomic=original_atomic):
            if path in {work / "progress.json", work / "acceleration_run_summary.json"}:
                _latest["state"] = json.loads(json.dumps(value))
                value = merged(states, value, _phase, args.registry_sha, sha(Path(__file__)))
            _atomic(path, value)

        control.atomic = live_atomic
        current = None
        try:
            original_run(
                args,
                RunnerPhase(runner, phase),
                spec,
                scope,
                auth,
                reference,
                deadline,
                sampler,
                work,
            )
        except Exception as error:
            parent_failure(control, error, phase, sampler, work)
            raise
        finally:
            control.pipeline, control.atomic = original_pipeline, original_atomic
            if "state" in latest:
                current = latest["state"]
                combined = merged(states, current, phase, args.registry_sha, sha(Path(__file__)))
                control.atomic(work / "progress.json", combined)
                control.atomic(work / "acceleration_run_summary.json", combined)
                control.atomic(work / "continuation_summary.json", combined)
        states.append(current)
        if phase == "december_safe_days":
            required = {f"2023-12-{d:02d}" for d in range(1, 31)}
            if not required <= set(current["days_verified_this_invocation"]):
                break  # Runtime reserve reached; next invocation resumes the same work.


def safe_failure(error, root, original):
    labels = set()
    for directory, manifest, field in (
        (original, original / "production_manifest.json", "files"),
        (root, root / "summer/manifest.json", "bundle_files"),
    ):
        for name in json.loads(manifest.read_bytes())[field]:
            if not name.endswith(".py"):
                continue
            path = directory / name
            require(
                not path.is_symlink() and path.resolve().is_relative_to(directory.resolve()),
                "Guard source boundary",
            )
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call) and len(node.args) > 1:
                    fn, value = node.func, node.args[1]
                    if (
                        (
                            (isinstance(fn, ast.Name) and fn.id == "require")
                            or (isinstance(fn, ast.Attribute) and fn.attr == "require")
                        )
                        and isinstance(value, ast.Constant)
                        and isinstance(value.value, str)
                    ):
                        labels.add(value.value)
    value = error.args[0] if len(error.args) == 1 else None
    return {
        "error_type": type(error).__name__,
        "guard": value if isinstance(value, str) and value in labels else "CLASS_ONLY",
    }


def child(args, control, runner):
    require(
        args.root.resolve().is_relative_to(control.PRODUCTION.resolve())
        and not args.root.is_symlink(),
        "Continuation child root",
    )
    failure = args.root / "continuation_failure.json"
    try:
        if args.child == "pair":
            require(args.sample not in EXPECTED, "Blocked pair cannot be launched")
            runner.child_pair(args)
        else:
            require(args.day != BLOCKED_DAY, "Blocked day cannot be reduced")
            runner.child_day(args)
    except Exception as error:
        value = safe_failure(error, args.root, control.ORIGINAL)
        value["safe_error"] = diagnostic_helper().safe_error(error)
        value.update(
            sample_id=args.sample if args.child == "pair" else args.day, child_kind=args.child
        )
        if args.child == "pair" and value["guard"] == "Not the actual geolocation input":
            try:
                plan = json.loads(args.plan.read_bytes())
                pair = next(p for p in plan["pairs"] if p["sample_id"] == args.sample)
                _, native = runner.science(args.root)
                fire = next(s for s in pair["sources"] if s["role"] == "fire")
                raw = args.root / "summer/raw" / pair["stem"] / fire["filename"]
                with contextlib.ExitStack() as stack:
                    tags = native.audit.layer(stack, raw, "fire_mask").tags()
                pattern = r"(?:VNP03IMG|VJ103IMG)\.A\d{7}\.\d{4}\.\d{3}\.\d{13}\.nc"
                value["declared_geolocation_filenames"] = sorted(
                    {
                        name
                        for key in ("VNP03IMG", "VJ103IMG", "InputPointer")
                        for name in re.findall(pattern, tags.get(key, "")[:8192])
                    }
                )
                value["selected_geolocation_filename"] = next(
                    s["filename"] for s in pair["sources"] if s["role"] == "geolocation"
                )
            except Exception:
                value["header_detail"] = "UNAVAILABLE"
        control.atomic(failure, value)
        raise


def diagnostic_launcher(control, reference, args):
    def launch(runner, kind, root, plan, identity, auth, deadline, sampler):
        failure = root / "continuation_failure.json"
        require(not failure.exists(), "Retained child failure requires review")
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            kind,
            "--root",
            str(root),
            "--plan",
            str(plan),
            "--sample" if kind == "pair" else "--day",
            identity,
            "--registry",
            str(args.registry.resolve()),
            "--registry-sha",
            args.registry_sha,
        ]
        started = time.monotonic()
        env = runner.environment(auth)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )
        with reference.ACTIVE_LOCK:
            reference.ACTIVE[process.pid] = process
        try:
            while process.poll() is None:
                if sampler.failed or time.monotonic() >= min(
                    deadline, started + reference.CHILD_LIMIT
                ):
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=30)
                    raise TimeoutError("Continuation child resource/deadline guard")
                time.sleep(0.25)
            if process.returncode != 0:
                if not failure.exists():
                    control.atomic(
                        failure,
                        {
                            "sample_id": identity,
                            "child_kind": kind,
                            "error_type": "RuntimeError",
                            "guard": "CLASS_ONLY",
                            "exit_code": process.returncode,
                            "termination_kind": "nonzero_exit_without_python_diagnostic",
                        },
                    )
                    print("CHILD_EXIT", identity, process.returncode, flush=True)
                if (
                    failure.is_file()
                    and not failure.is_symlink()
                    and failure.stat().st_size < 65536
                ):
                    value = json.loads(failure.read_bytes())
                    require(
                        value.get("sample_id") == identity and value.get("child_kind") == kind,
                        "Diagnostic child identity",
                    )
                    # File is written solely by the pinned wrapper; no HTTP/stdout text.
                    print("CHILD FAILED", identity, value["error_type"], value["guard"], flush=True)
                raise RuntimeError("Frozen scientific child failed; diagnostic retained")
            return time.monotonic() - started
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            raise
        finally:
            with reference.ACTIVE_LOCK:
                reference.ACTIVE.pop(process.pid, None)

    return launch


def diagnostic_helper():
    path = Path.home() / "diagnose_gcp_production_manifest.py"
    require(
        not path.is_symlink() and path.is_file() and sha(path) == DIAGNOSTIC_SHA,
        "Pinned HTTP diagnostic helper",
    )
    spec = importlib.util.spec_from_file_location("continuation_http_diagnostic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parent_failure(control, error, phase, sampler, work):
    """Keep only code-defined guards or sanitized HTTP classes, never traceback or auth."""
    try:
        helper = diagnostic_helper()
        labels = set()
        for package, manifest in (
            (control.ORIGINAL, "production_manifest.json"),
            (Path(control.__file__).parent, "acceleration_manifest.json"),
        ):
            spec = json.loads((package / manifest).read_bytes())
            for name, digest in spec["files"].items():
                if not name.endswith(".py"):
                    continue
                path = package / name
                require(
                    not path.is_symlink() and Path(name).name == name and sha(path) == digest,
                    "Parent guard source",
                )
                for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                    if isinstance(node, ast.Call) and len(node.args) > 1:
                        function, label = node.func, node.args[1]
                        if (isinstance(function, ast.Name) and function.id == "require") or (
                            isinstance(function, ast.Attribute) and function.attr == "require"
                        ):
                            if isinstance(label, ast.Constant) and isinstance(label.value, str):
                                labels.add(label.value)
        text = error.args[0] if len(error.args) == 1 else None
        value = {
            "protocol": "continuation_parent_failure_v2",
            "recorded_at_utc": datetime.now(UTC).isoformat(),
            "continuation_phase": phase,
            "error": helper.safe_error(error),
            "guard": text if isinstance(text, str) and text in labels else "CLASS_ONLY",
        }
        month = getattr(sampler, "arm", "")
        step = getattr(sampler, "phase", "")
        value["last_recorded_month"] = (
            month if re.fullmatch(r"20(?:18|19|2[0-3])-\d{2}", month) else "UNKNOWN"
        )
        value["last_recorded_stage"] = (
            step
            if step in {"metadata", "prepare_day", "pair_publication", "daily_publication"}
            else "UNKNOWN"
        )
        name = "parent_failure_v2_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
        control.atomic(work / "diagnostics" / name, value)
        print("PARENT_FAILURE", value["error"], value["guard"], flush=True)
    except Exception:
        print("PARENT_FAILURE diagnostic_unavailable; no external text logged", flush=True)


def instrument_backend(control, helper):
    original = control.backend

    def backend(*args, **kwargs):
        # Wrap the opener before the existing backend performs token/quota checks.
        from accelerated_checkpoint_store import IndexedDriveStore

        method = IndexedDriveStore.from_file.__func__

        def from_file(cls, path):
            store = method(cls, path)
            store.api.opener = helper.diagnostic_opener(store.api.opener)
            return store

        previous = IndexedDriveStore.__dict__.get("from_file")
        IndexedDriveStore.from_file = classmethod(from_file)
        try:
            return original(*args, **kwargs)
        finally:
            if previous is None:
                del IndexedDriveStore.from_file
            else:
                IndexedDriveStore.from_file = previous

    control.backend = backend


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--registry-sha", required=True)
    parser.add_argument("--termination")
    parser.add_argument(
        "--connection", type=Path, default=Path.home() / ".config/wildfire/drive_connection.json"
    )
    parser.add_argument("--gate", type=Path, default=Path.home() / "production_readiness.json")
    parser.add_argument("--gate-sha", default=GATE_SHA)
    parser.add_argument("--cpus", type=int, default=32, choices=[32])
    parser.add_argument("--poweroff", action="store_true")
    parser.add_argument("--supervise", action="store_true")
    parser.add_argument("--auth-fd", type=int)
    parser.add_argument("--child", choices=["pair", "day"])
    parser.add_argument("--root", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--sample")
    parser.add_argument("--day")
    args = parser.parse_args()
    registry(args.registry, args.registry_sha)
    package = Path.home() / "wildfire-gcp-acceleration-package"
    require(
        sha(package / "acceleration_manifest.json") == CONTROLLER_SCOPE, "Pinned base controller"
    )
    sys.path.insert(0, str(package))
    control = importlib.import_module("run_gcp_acceleration")
    require(
        Path(control.__file__).resolve() == (package / "run_gcp_acceleration.py").resolve(),
        "Base controller import identity",
    )
    spec, scope, runner = control.checked()
    http = diagnostic_helper()
    if args.supervise and not args.child:
        instrument_backend(control, http)
    if args.child:
        child(args, control, runner)
        return
    require(
        sys.platform == "linux"
        and sys.version_info[:2] == (3, 12)
        and sys.prefix != sys.base_prefix,
        "Existing Linux Python venv",
    )
    runner.vm_identity()
    require(os.cpu_count() == args.cpus, "Actual CPU count")
    require(
        control.memory_values(Path("/proc/meminfo").read_text())[0] >= 64 * 2**30,
        "Actual memory reserve",
    )
    seconds = control.budget(args.termination, False)
    control.read_gate(args, scope)
    require(args.poweroff, "Automatic shutdown required")
    if not args.supervise:
        with control.production_lock():
            pass
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
        require(
            args.poweroff
            and subprocess.run(
                ["sudo", "-n", "true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).returncode
            == 0,
            "Automatic shutdown required",
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
            str(Path(__file__).resolve()),
            "--supervise",
            "--registry",
            str(args.registry.resolve()),
            "--registry-sha",
            args.registry_sha,
            "--termination",
            args.termination,
            "--connection",
            str(args.connection.resolve()),
            "--gate",
            str(args.gate.resolve()),
            "--gate-sha",
            args.gate_sha,
            "--auth-fd",
            str(read_fd),
            "--poweroff",
        ]
        with (Path.home() / "gcp_source_aware_launcher_v2.log").open("ab") as log:
            process = subprocess.Popen(
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
        print("Detached continuation requested; PID:", process.pid)
        print("Check:", Path.home() / "gcp_source_aware_launcher_v2.log")
        return
    auth = runner.read_auth(args.auth_fd)
    reference = control.reference_driver()
    reference.run_child = diagnostic_launcher(control, reference, args)
    production = importlib.import_module("accelerated_production")
    original_run = production.run
    production.run = lambda *values: run_phases(control, original_run, *values)
    args.mode = "production"
    control.supervise(args, runner, spec, scope, auth, reference, seconds, control.PRODUCTION)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    os.umask(0o077)
    try:
        main()
    except Exception as error:
        print(
            "Continuation stopped:",
            type(error).__name__,
            "; safe child diagnostics retained",
            flush=True,
        )
        raise SystemExit(1) from None
