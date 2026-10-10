"""Bounded offline V2 failure snapshot; no credentials, raw reads or production writes."""

import ast
import contextlib
import csv
import hashlib
import io
import json
import math
import os
import re
from datetime import UTC, datetime
from pathlib import Path

SCOPE = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
CONTROLLER = "102c9e4ab16e4450d0d94eb3511dfdbf360fd6b6292809c5457efc93d2be5837"
WRAPPER = "943878d4416ac5c6c42ab73070f420920208fadd62e08e4119eea76341b7a2ea"
REGISTRY = "6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d"
FOCUS = "SNPP:2022252.2230"
ERRORS = {
    "ValueError",
    "RuntimeError",
    "OSError",
    "PermissionError",
    "FileNotFoundError",
    "JSONDecodeError",
    "KeyError",
    "TimeoutError",
    "BlockingIOError",
}
PHASES = {"metadata", "prepare_day", "pair_publication", "daily_publication", "UNKNOWN"}
SOURCE_NAME = r"(?:VNP|VJ1)(?:14|03)IMG\.A\d{7}\.\d{4}\.\d{3}\.\d{13}\.nc"
NATIVE_SUFFIXES = {
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
}


class SnapshotCheck(ValueError):
    """Only this script's constant check labels may be printed."""


def require(ok, label):
    if not ok:
        raise SnapshotCheck(label)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def boundary(path, owner):
    require(path.resolve().is_relative_to(owner.resolve()), "File boundary")
    for current in (path, *path.parents):
        require(not current.is_symlink(), "File symlink")
        if current == owner:
            return
    require(False, "Owner boundary")


def read(path, owner, limit=2_000_000):
    boundary(path, owner)
    require(path.is_file() and 0 < path.stat().st_size <= limit, "File size")
    return path.read_bytes()


def pinned(package, name, digest):
    data = read(package / name, package)
    require(sha(data) == digest, "Package manifest hash")
    manifest = json.loads(data)
    labels = {"CLASS_ONLY"}
    for filename, checksum in manifest["files"].items():
        require(Path(filename).name == filename and "\\" not in filename, "Package basename")
        content = read(package / filename, package, 20_000_000)
        require(sha(content) == checksum, "Package member hash")
        if filename.endswith(".py"):
            labels.update(guards(content))
    return labels


def guards(data):
    result = set()
    for node in ast.walk(ast.parse(data.decode("utf-8"))):
        if not isinstance(node, ast.Call) or len(node.args) < 2:
            continue
        name, label = node.func, node.args[1]
        if (isinstance(name, ast.Name) and name.id == "require") or (
            isinstance(name, ast.Attribute) and name.attr == "require"
        ):
            if isinstance(label, ast.Constant) and isinstance(label.value, str):
                result.add(label.value)
    return result


def safe_error(value):
    return (
        value
        if isinstance(value, str)
        and (
            value
            in ERRORS
            | {"UNCLASSIFIED_ERROR", "GOOGLE_TRANSPORT_FAILURE", "GOOGLE_REDIRECT_REFUSED"}
            or re.fullmatch(r"GOOGLE_HTTP_[1-5][0-9]{2}", value)
        )
        else "UNCLASSIFIED_ERROR"
    )


def failure(value, labels):
    """Select enums/literal guards; never copy exception text, URLs or arbitrary keys."""
    result = {
        "error_type": safe_error(value.get("error_type", value.get("error"))),
        "safe_error": safe_error(value.get("safe_error", value.get("error"))),
        "guard": value.get("guard")
        if isinstance(value.get("guard"), str) and value.get("guard") in labels
        else "CLASS_ONLY",
    }
    code = value.get("exit_code")
    if type(code) is int and -255 <= code <= 255:
        result["exit_code"] = code
    if value.get("termination_kind") == "nonzero_exit_without_python_diagnostic":
        result["termination_kind"] = value["termination_kind"]
    for key in ("last_recorded_month", "last_recorded_stage"):
        candidate = value.get(key)
        if (
            key.endswith("month")
            and isinstance(candidate, str)
            and re.fullmatch(r"20(?:18|19|2[0-3])-\d{2}", candidate)
        ):
            result[key] = candidate
        elif key.endswith("stage") and isinstance(candidate, str) and candidate in PHASES:
            result[key] = candidate
    return result


def progress(data):
    value = json.loads(data)
    expected = {
        "status": "failed_checkpoints_retained",
        "failed_month": "2022-09",
        "queue_manifest_sha256": SCOPE,
        "controller_manifest_sha256": CONTROLLER,
        "continuation_wrapper_sha256": WRAPPER,
        "source_block_registry_sha256": REGISTRY,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "continuation_phase": "remaining_months",
        "full_training_complete": False,
        "blocked_pairs": ["SNPP:2023365.0106", "SNPP:2023365.1048"],
        "deferred_days": ["2023-12-31"],
        "deferred_months": ["2023-12"],
    }
    require(
        all(value.get(k) == v and type(value.get(k)) is type(v) for k, v in expected.items()),
        "Failed V2 September identity",
    )
    require(value.get("failed_phase") in PHASES - {"UNKNOWN"}, "Failure phase")
    require(value.get("error_type") in ERRORS, "Failure class")
    result = expected | {k: value[k] for k in ("failed_phase", "error_type")}
    for key in ("pairs_processed_this_invocation", "pairs_reused_this_invocation"):
        require(type(value[key]) is int and 0 <= value[key] <= 18711, "Counter bound")
        result[key] = value[key]
    for key, pattern, count in (
        ("existing_months", r"20(?:18|19|2[0-3])-(?:0[1-9]|1[0-2])", 72),
        ("days_verified_this_invocation", r"20(?:18|19|2[0-3])-\d{2}-\d{2}", 2191),
    ):
        require(
            isinstance(value[key], list)
            and len(value[key]) <= count
            and all(isinstance(x, str) and re.fullmatch(pattern, x) for x in value[key])
            and len(set(value[key])) == len(value[key]),
            "Calendar values",
        )
        for item in value[key]:
            datetime.fromisoformat(item + "-01" if key == "existing_months" else item)
        result[key] = value[key]
    return result


def telemetry(data):
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    require(0 < len(rows) < 20000, "Resource population")
    keys = ("disk_free_bytes", "mem_available_bytes", "process_tree_rss_bytes")
    values = {key: [] for key in keys}
    for row in rows:
        for key in keys:
            text = row[key]
            require(isinstance(text, str) and re.fullmatch(r"\d{1,20}", text), "Resource number")
            values[key].append(int(text))
    seconds = float(rows[-1]["seconds"])
    require(math.isfinite(seconds) and 0 <= seconds < 86400, "Resource time")
    return {
        "samples": len(rows),
        "last_sample_seconds": seconds,
        "min_disk_free_bytes": min(values[keys[0]]),
        "min_mem_available_bytes": min(values[keys[1]]),
        "peak_process_tree_rss_bytes": max(values[keys[2]]),
        "limitation": "Sampled values do not prove every instant or child memory limit",
    }


def collect(home):
    work = home / "wildfire-gcp-production-v1"
    labels = pinned(home / "wildfire-gcp-production-package", "production_manifest.json", SCOPE)
    labels.update(
        pinned(home / "wildfire-gcp-acceleration-package", "acceleration_manifest.json", CONTROLLER)
    )
    wrapper = read(home / "run_gcp_source_aware_continuation_v2.py", home)
    require(sha(wrapper) == WRAPPER, "V2 wrapper hash")
    labels.update(guards(wrapper))
    require(sha(read(home / "source_blocks.json", home, 65536)) == REGISTRY, "Registry hash")
    saved = progress(read(work / "progress.json", work, 65536))
    for name in ("acceleration_run_summary.json", "continuation_summary.json"):
        require(progress(read(work / name, work, 65536)) == saved, "Final snapshots differ")
    month = work / "months/2022-09"
    plan_data = read(month / "metadata/month.json", work)
    plan = json.loads(plan_data)
    require(
        plan["month"] == "2022-09" and plan["negative_label_permitted"] is False,
        "Month plan identity",
    )
    require(0 < len(plan["pairs"]) <= 1000, "Pair population")
    pairs = {sha(p["sample_id"].encode()): p for p in plan["pairs"]}
    require(len(pairs) == len(plan["pairs"]), "Duplicate pair identity")
    focus = [p for p in plan["pairs"] if p["sample_id"] == FOCUS]
    require(len(focus) == 1 and focus[0]["stem"] == "l2_sample_2022252.2230", "Focus identity")
    tasks = month / "accelerated_run/tasks"
    boundary(tasks, work)
    roots = sorted(tasks.iterdir())
    require(0 < len(roots) <= 100, "Task population")
    children, raw_sources, focus_outputs = [], [], []
    for root in roots:
        boundary(root, work)
        require(root.is_dir() and root.name in pairs, "Task identity")
        pair = pairs[root.name]
        require(re.fullmatch(r"(?:SNPP|N20):2022\d{3}\.\d{4}", pair["sample_id"]), "Pair scope")
        path = root / "continuation_failure.json"
        if path.exists():
            value = json.loads(read(path, work, 65536))
            require(
                value.get("sample_id") == pair["sample_id"] and value.get("child_kind") == "pair",
                "Child failure identity",
            )
            children.append({"sample_id": pair["sample_id"], **failure(value, labels)})
        if pair["sample_id"] == FOCUS:
            for source in pair["sources"]:
                require(
                    source["role"] in {"fire", "geolocation"}
                    and isinstance(source["filename"], str)
                    and re.fullmatch(SOURCE_NAME, source["filename"])
                    and type(source["bytes"]) is int
                    and 0 < source["bytes"] < 2**31,
                    "Public source fields",
                )
                raw = root / "summer/raw" / pair["stem"] / source["filename"]
                boundary(raw, work)
                raw_sources.append(
                    {
                        "role": source["role"],
                        "filename": source["filename"],
                        "expected_bytes": source["bytes"],
                        "present": raw.is_file(),
                        "actual_bytes": raw.stat().st_size if raw.is_file() else 0,
                    }
                )
            result = root / "summer/results"
            if result.exists():
                boundary(result, work)
                for path in result.iterdir():
                    boundary(path, work)
                    if (
                        path.is_file()
                        and path.name.startswith(pair["stem"] + "_")
                        and path.name[len(pair["stem"]) + 1 :] in NATIVE_SUFFIXES
                    ):
                        focus_outputs.append(
                            {
                                "suffix": path.name[len(pair["stem"]) + 1 :],
                                "bytes": path.stat().st_size,
                            }
                        )
            require(len(focus_outputs) <= 30, "Output population")
    require(any(c["sample_id"] == FOCUS for c in children), "Focus failure retained")
    parents = []
    directory = work / "diagnostics"
    if directory.exists():
        boundary(directory, work)
        paths = sorted(directory.glob("parent_failure_v2_*.json"))
        require(len(paths) <= 100, "Parent diagnostic population")
        for path in paths[-5:]:
            require(
                re.fullmatch(r"parent_failure_v2_\d{8}T\d{12}Z\.json", path.name), "Parent basename"
            )
            value = json.loads(read(path, work, 65536))
            require(value.get("protocol") == "continuation_parent_failure_v2", "Parent protocol")
            parents.append({"file": path.name, **failure(value, labels)})
    resources = work / "resource_samples.csv"
    return {
        "protocol": "gcp_v2_september_failure_snapshot_v1",
        "progress": saved,
        "focus_sample": FOCUS,
        "month_plan_sha256": sha(plan_data),
        "child_failures": children,
        "parent_failures": parents,
        "focus_raw_inventory": raw_sources,
        "focus_output_inventory": focus_outputs,
        "resources": telemetry(read(resources, work, 10_000_000)) if resources.exists() else None,
        "raw_files_read": False,
        "credentials_read": False,
        "network_requests": 0,
        "production_writes": 0,
        "limits": "Snapshot only; no source replay or scientific output acceptance",
    }


@contextlib.contextmanager
def stopped_lock(work):
    import fcntl

    path = work / "job.lock"
    boundary(path, work)
    require(path.is_file(), "Existing production lock")
    with path.open("r") as stream:
        fcntl.flock(stream, fcntl.LOCK_SH | fcntl.LOCK_NB)
        yield


def main():
    home = Path.home()
    with stopped_lock(home / "wildfire-gcp-production-v1"):
        report = collect(home)
        report["collected_at_utc"] = datetime.now(UTC).isoformat()
        data = (json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
        require(len(data) < 512000, "Snapshot byte bound")
        target = home / (
            "gcp_v2_failure_snapshot_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
        )
        with target.open("xb") as stream:
            stream.write(data)
    print("Offline snapshot collected; no raw processing")
    print("Download:", target)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except SnapshotCheck as error:
        print("Snapshot check failed:", str(error))
        raise SystemExit(1) from None
    except Exception as error:
        print("Snapshot stopped:", type(error).__name__, "; no external text logged")
        raise SystemExit(1) from None
