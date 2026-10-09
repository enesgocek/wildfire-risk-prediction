"""Collect source-aware failure evidence without network, raw data or job launch.

Reads a stopped invocation under its existing lock. Original/controller files
remain immutable. Writes only a new diagnostic ZIP next to the user's home.
"""

import argparse
import ast
import contextlib
import hashlib
import io
import json
import os
import re
import zipfile
from datetime import date, datetime
from pathlib import Path

SCOPE = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
CONTROLLER = "102c9e4ab16e4450d0d94eb3511dfdbf360fd6b6292809c5457efc93d2be5837"
WRAPPER = "b6abd44acf85c0cff5763d5da5463d3c24750f6b65371b04a28047f15f978bda"
REGISTRY = "6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d"
BLOCKED = ["SNPP:2023365.0106", "SNPP:2023365.1048"]
MAX_TOTAL = 150_000_000
SUFFIXES = (
    "audit.json",
    "grid_centers.csv",
    "area_estimate.json",
    "area_estimate.csv",
    "area_estimate.gpkg",
    "scan_times.csv",
    "scan_grid.csv",
    "all_scans.csv",
    "scan_provenance.json",
    "checkpoint.json",
    "memory.json",
)
PHASES = {"metadata", "prepare_day", "pair_publication", "daily_publication"}
ERRORS = {
    "ValueError",
    "RuntimeError",
    "TimeoutError",
    "OSError",
    "KeyError",
    "FileNotFoundError",
    "PermissionError",
    "JSONDecodeError",
}
LOG = re.compile(
    r"(?:Month verified/reused: 20(?:18|19|2[0-3])-\d{2}"
    r"|MONTH NOMINAL DIAGNOSTICS COMPLETE: 20(?:18|19|2[0-3])-\d{2}"
    r"|DAY COMMITTED 20(?:18|19|2[0-3])-\d{2}-\d{2}"
    r"|20(?:18|19|2[0-3])-\d{2} pair saved/verified (?:SNPP|N20):\d{7}\.\d{4}"
    r"|Guest poweroff requested: (?:True|False)"
    r"|Continuation stopped: [A-Za-z]+ ; safe child diagnostics retained"
    r"|CONTINUATION PHASE (?:december_safe_days|remaining_months) deferred day 2023-12-31)"
)


class CollectionCheck(ValueError):
    """Only constant collector labels may be shown to the user."""


def require(ok, label):
    if not ok:
        raise CollectionCheck(label)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path, owner, limit=20_000_000):
    require(path.resolve().is_relative_to(owner.resolve()), "Source boundary")
    current = path
    while current != owner.parent:
        require(not current.is_symlink(), "Source symlink")
        if current == owner:
            break
        current = current.parent
    require(path.is_file() and 0 < path.stat().st_size <= limit, "Source byte bound")
    return path.read_bytes()


def pinned(package, filename, expected):
    data = read(package / filename, package)
    require(sha(data) == expected, "Pinned manifest SHA")
    spec = json.loads(data)
    for name, checksum in spec["files"].items():
        require(Path(name).name == name and "\\" not in name, "Pinned basename")
        require(sha(read(package / name, package)) == checksum, "Pinned member SHA")
    return data


def state(data):
    value = json.loads(data)
    require(
        value["status"] == "failed_checkpoints_retained"
        and value["queue_manifest_sha256"] == SCOPE
        and value["controller_manifest_sha256"] == CONTROLLER
        and value["negative_label_permitted"] is False
        and value["daily_observation_status"] == "unknown"
        and value["error_type"] in ERRORS
        and value["failed_phase"] in PHASES
        and re.fullmatch(r"20(?:18|19|2[0-3])-(?:0[1-9]|1[0-2])", value["failed_month"]),
        "Failed invocation identity",
    )
    for key in ("pairs_processed_this_invocation", "pairs_reused_this_invocation"):
        require(type(value[key]) is int and 0 <= value[key] <= 18711, "Counter bound")
    for key, pattern, count in (
        ("existing_months", r"20(?:18|19|2[0-3])-(?:0[1-9]|1[0-2])", 72),
        ("days_verified_this_invocation", r"20(?:18|19|2[0-3])-\d{2}-\d{2}", 2191),
    ):
        require(
            len(value[key]) <= count
            and len(value[key]) == len(set(value[key]))
            and all(isinstance(x, str) and re.fullmatch(pattern, x) for x in value[key]),
            "Calendar boundary",
        )
    for day in value["days_verified_this_invocation"]:
        date.fromisoformat(day)
    require(
        value["continuation_phase"] == "remaining_months"
        and value["continuation_wrapper_sha256"] == WRAPPER
        and value["source_block_registry_sha256"] == REGISTRY
        and value["blocked_pairs"] == BLOCKED
        and value["deferred_days"] == ["2023-12-31"]
        and value["deferred_months"] == ["2023-12"]
        and value["full_training_complete"] is False,
        "Source-aware invocation identity",
    )
    finish = datetime.fromisoformat(value["actual_vm_termination_timestamp"].replace("Z", "+00:00"))
    require(finish.tzinfo is not None and finish.year == 2026, "Stop timestamp")
    # Unknown fields and free-form values are not copied into the public archive.
    fields = {
        "status",
        "error_type",
        "failed_phase",
        "failed_month",
        "existing_months",
        "days_verified_this_invocation",
        "pairs_processed_this_invocation",
        "pairs_reused_this_invocation",
        "queue_manifest_sha256",
        "controller_manifest_sha256",
        "negative_label_permitted",
        "daily_observation_status",
        "continuation_phase",
        "continuation_wrapper_sha256",
        "source_block_registry_sha256",
        "blocked_pairs",
        "deferred_days",
        "deferred_months",
        "full_training_complete",
        "actual_vm_termination_timestamp",
    }
    return {key: value[key] for key in fields}


def collect(work, original, controller, target):
    require(not target.exists() and not target.is_symlink(), "Export already exists")
    pending = target.with_suffix(".pending")
    require(not pending.exists() and not pending.is_symlink(), "Pending export exists")
    original_manifest = pinned(original, "production_manifest.json", SCOPE)
    controller_manifest = pinned(controller, "acceleration_manifest.json", CONTROLLER)
    wrapper_path = work.parent / "run_gcp_source_aware_continuation.py"
    require(sha(read(wrapper_path, work.parent)) == WRAPPER, "Pinned continuation wrapper")
    registry = read(work.parent / "source_blocks.json", work.parent, 65536)
    require(sha(registry) == REGISTRY, "Pinned source registry")
    summary = state(read(work / "progress.json", work, 65536))
    require(
        state(read(work / "acceleration_run_summary.json", work, 65536)) == summary,
        "Failure snapshots differ",
    )
    require(
        state(read(work / "continuation_summary.json", work, 65536)) == summary,
        "Continuation snapshot differs",
    )
    month = summary["failed_month"]
    directory = work / "months" / month
    metadata = directory / "metadata"
    plan_bytes = read(metadata / "month.json", work, 2_000_000)
    plan = json.loads(plan_bytes)
    require(
        plan["month"] == month and plan["negative_label_permitted"] is False, "Month plan identity"
    )
    pairs = plan["pairs"]
    require(0 < len(pairs) <= 1000, "Month pair bound")
    identities = {}
    metadata_names = {"month.json"}
    for pair in pairs:
        identity = pair["sample_id"]
        require(re.fullmatch(r"(?:SNPP|N20):\d{7}\.\d{4}", identity), "Pair identity")
        expected_stem = "l2_sample_" + (
            identity.split(":")[1] if identity.startswith("SNPP:") else identity.replace(":", "_")
        )
        require(pair["stem"] == expected_stem, "Pair stem")
        name = sha(identity.encode())
        require(name not in identities, "Duplicate pair identity")
        identities[name] = pair
        for value in pair["metadata"].values():
            base = Path(value).name
            require(re.fullmatch(r"G\d+-[A-Z0-9_]+\.json", base), "Metadata basename")
            metadata_names.add(base)
    # Preserve the original bytes and unpaired catalogue metadata too. Rebuilding
    # from pair references alone would omit scientifically relevant gap records.
    manifest_bytes = read(directory / "manifest.zip", work, 20_000_000)
    with zipfile.ZipFile(io.BytesIO(manifest_bytes)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and len(names) <= 2001, "Manifest member count")
        require(
            metadata_names <= set(names)
            and all(
                name == "month.json" or re.fullmatch(r"G\d+-[A-Z0-9_]+\.json", name)
                for name in names
            ),
            "Manifest member boundary",
        )
        require(
            sum(info.file_size for info in archive.infolist()) < 50_000_000,
            "Manifest expanded byte bound",
        )
        require(
            archive.testzip() is None and archive.read("month.json") == plan_bytes,
            "Persisted month plan differs",
        )
    files = {
        "progress.json": json.dumps(summary, sort_keys=True).encode(),
        "original_manifest.json": original_manifest,
        "controller_manifest.json": controller_manifest,
        "manifest.zip": manifest_bytes,
        "source_registry.json": registry,
    }
    log = read(work.parent / "gcp_source_aware_launcher.log", work.parent, 10_000_000)
    safe = [
        line for line in log.decode("utf-8", errors="replace").splitlines() if LOG.fullmatch(line)
    ]
    files["launcher_filtered.log"] = ("\n".join(safe[-500:]) + "\n").encode()
    if (work / "resource_samples.csv").exists():
        files["resource_samples.csv"] = read(work / "resource_samples.csv", work, 10_000_000)
    inventory = []
    labels = {"CLASS_ONLY"}
    for package in (original, controller):
        spec = json.loads(
            read(
                package
                / (
                    "production_manifest.json"
                    if package == original
                    else "acceleration_manifest.json"
                ),
                package,
            )
        )
        for name in spec["files"]:
            if name.endswith(".py"):
                labels.update(literal_guards(read(package / name, package)))
    labels.update(literal_guards(read(wrapper_path, work.parent)))
    tasks = directory / "accelerated_run/tasks"
    roots = sorted(tasks.iterdir()) if tasks.exists() else []
    require(len(roots) <= 100, "Retained task count")
    for root in roots:
        require(
            root.is_dir() and not root.is_symlink() and root.name in identities,
            "Retained task boundary",
        )
        pair = identities[root.name]
        capture_child_failure(
            root,
            pair["sample_id"],
            "pair",
            labels,
            work,
            files,
            "tasks/" + root.name + "/continuation_failure.json",
        )
        row = {
            "sample_id": pair["sample_id"],
            "pair_zip_present": (root / "pair.zip").exists(),
            "raw_sources": [],
            "native_outputs": [],
        }
        for source in pair["sources"]:
            require(
                re.fullmatch(
                    r"(?:VNP|VJ1)(?:14|03)IMG\.A\d{7}\.\d{4}\.\d{3}\.\d{13}\.nc", source["filename"]
                ),
                "Raw basename",
            )
            require(
                source["role"] in {"fire", "geolocation"}
                and type(source["bytes"]) is int
                and 0 < source["bytes"] < 2**31,
                "Raw source schema",
            )
            raw = root / "summer/raw" / pair["stem"] / source["filename"]
            require(not raw.is_symlink(), "Raw symlink")
            require(raw.resolve().is_relative_to(work.resolve()), "Raw source boundary")
            row["raw_sources"].append(
                {
                    "role": source["role"],
                    "expected_bytes": source["bytes"],
                    "present": raw.is_file(),
                    "actual_bytes": raw.stat().st_size if raw.is_file() else 0,
                }
            )  # Raw NASA files are neither read nor included.
        prefix = "tasks/" + root.name + "/"
        if row["pair_zip_present"]:
            files[prefix + "pair.zip"] = read(root / "pair.zip", work, 100_000_000)
        else:
            for suffix in SUFFIXES:
                source = root / "summer/results" / (pair["stem"] + "_" + suffix)
                if source.exists():
                    row["native_outputs"].append(suffix)
                    files[prefix + "native/" + source.name] = read(source, work, 30_000_000)
        if (root / "task_metrics.json").exists():
            files[prefix + "task_metrics.json"] = read(root / "task_metrics.json", work, 65536)
        inventory.append(row)
        require(sum(map(len, files.values())) < MAX_TOTAL, "Diagnostic total byte bound")
    days = directory / "accelerated_run/days"
    day_roots = sorted(days.iterdir()) if days.exists() else []
    require(len(day_roots) <= 6, "Retained day count")
    day_inventory = []
    for root in day_roots:
        require(root.name in plan["days"] and not root.is_symlink(), "Retained day boundary")
        capture_child_failure(
            root,
            root.name,
            "day",
            labels,
            work,
            files,
            "days/" + root.name + "/continuation_failure.json",
        )
        if (root / "day.zip").exists():
            files["days/" + root.name + ".zip"] = read(root / "day.zip", work, 20_000_000)
        day_inventory.append({"day": root.name, "day_zip_present": (root / "day.zip").exists()})
    report = {
        "protocol": "gcp_source_aware_failure_evidence_v1",
        "wrapper_sha256": WRAPPER,
        "source_registry_sha256": REGISTRY,
        "failed_month": month,
        "task_inventory": inventory,
        "source_raw_files_included": False,
        "day_inventory": day_inventory,
        "credentials_read": False,
        "network_requests": 0,
        "production_writes": 0,
        "files": {name: sha(data) for name, data in files.items()},
    }
    files["capture_manifest.json"] = json.dumps(report, sort_keys=True).encode()
    require(sum(map(len, files.values())) < MAX_TOTAL, "Diagnostic total byte bound")
    with zipfile.ZipFile(pending, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            archive.writestr(name, data)
    with zipfile.ZipFile(pending) as archive:
        require(archive.testzip() is None, "Diagnostic CRC")
    pending.replace(target)
    return report


def literal_guards(data):
    """Only literal require labels from already pinned source files may be exported."""
    labels = set()
    for node in ast.walk(ast.parse(data.decode("utf-8"))):
        if not isinstance(node, ast.Call) or len(node.args) < 2:
            continue
        function, label = node.func, node.args[1]
        if (isinstance(function, ast.Name) and function.id == "require") or (
            isinstance(function, ast.Attribute) and function.attr == "require"
        ):
            if isinstance(label, ast.Constant) and isinstance(label.value, str):
                labels.add(label.value)
    return labels


def capture_child_failure(root, identity, kind, labels, work, files, name):
    path = root / "continuation_failure.json"
    if not path.exists():
        return
    value = json.loads(read(path, work, 65536))
    require(
        value.get("sample_id") == identity and value.get("child_kind") == kind,
        "Child failure identity",
    )
    require(value.get("error_type") in ERRORS, "Child failure class")
    safe = {
        "sample_id": identity,
        "child_kind": kind,
        "error_type": value["error_type"],
        "guard": value["guard"] if value.get("guard") in labels else "CLASS_ONLY",
    }
    for key in ("declared_geolocation_filenames", "selected_geolocation_filename"):
        if key not in value:
            continue
        names = value[key] if isinstance(value[key], list) else [value[key]]
        require(
            len(names) <= 10
            and all(
                isinstance(v, str)
                and re.fullmatch(r"(?:VNP03IMG|VJ103IMG)\.A\d{7}\.\d{4}\.\d{3}\.\d{13}\.nc", v)
                for v in names
            ),
            "Public header filenames",
        )
        safe[key] = value[key]
    files[name] = json.dumps(safe, sort_keys=True).encode()


@contextlib.contextmanager
def lock(work):
    import fcntl

    path = work / "job.lock"
    require(path.is_file() and not path.is_symlink(), "Original job lock")
    with path.open("r") as stream:
        fcntl.flock(stream, fcntl.LOCK_SH | fcntl.LOCK_NB)
        yield


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=Path.home() / "wildfire-gcp-production-v1")
    args = parser.parse_args()
    target = Path.home() / "gcp_source_aware_failure_2026-10-09.zip"
    with lock(args.work):
        report = collect(
            args.work,
            Path.home() / "wildfire-gcp-production-package",
            Path.home() / "wildfire-gcp-acceleration-package",
            target,
        )
    print("Evidence collected; retained tasks:", len(report["task_inventory"]))
    print("Download:", target)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except CollectionCheck as error:
        print("Collection check failed:", str(error))
        raise SystemExit(1) from None
    except Exception as error:
        print("Collection stopped:", type(error).__name__, "; no external text logged")
        raise SystemExit(1) from None
