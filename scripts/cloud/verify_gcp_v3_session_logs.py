"""Offline V3 log/catalogue readback; no product acceptance or cloud operations."""

import argparse
import calendar
import csv
import hashlib
import io
import json
import math
import re
import statistics
import tarfile
from collections import Counter
from datetime import date
from pathlib import Path

from diagnose_gcp_production_manifest import verify_package

ROOT = Path(__file__).resolve().parents[2]
SCOPE = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
CONTROLLER = "102c9e4ab16e4450d0d94eb3511dfdbf360fd6b6292809c5457efc93d2be5837"
WRAPPER = "792d774f53c2a7249a10f4111f2f785e08d5bd2a8153e1151c73efe493b5942e"
ADAPTER = "e729c56aced66feb6b3a461773c7d694e43d4f35b586d6060f8cabceee968a39"
PROOF = "edfba0a8a87cdbf642e9cfd31a9d7d3115ac3281003b844135e1b127369621ea"
REGISTRY = "6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d"
MEMBERS = {
    "progress.json",
    "acceleration_run_summary.json",
    "continuation_summary.json",
    "resource_samples.csv",
    "gcp_source_aware_launcher_v3.log",
}
LIMIT = 30_000_000


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def contents(source):
    require(not source.is_symlink() and 0 < source.stat().st_size < LIMIT, "Archive size/path")
    result, total = {}, 0
    with tarfile.open(source, "r|gz") as archive:
        for member in archive:
            require(
                member.name in MEMBERS and member.name not in result and member.isfile(),
                "Archive member boundary",
            )
            total += member.size
            require(0 < member.size < LIMIT and total < LIMIT, "Expanded byte bound")
            with archive.extractfile(member) as stream:
                data = stream.read()
            require(len(data) == member.size, "Archive short read")
            result[member.name] = data
    require(set(result) == MEMBERS, "Archive population")
    return result


def days(month):
    first = date.fromisoformat(month + "-01")
    require(2018 <= first.year <= 2023, "Training calendar")
    return {
        f"{month}-{d:02d}" for d in range(1, calendar.monthrange(first.year, first.month)[1] + 1)
    }


def state(files):
    values = [
        json.loads(files[name])
        for name in ("progress.json", "acceleration_run_summary.json", "continuation_summary.json")
    ]
    require(values[0] == values[1] == values[2], "Final snapshots differ")
    value = values[0]
    for key, expected in {
        "status": "paused_at_runtime_reserve",
        "queue_manifest_sha256": SCOPE,
        "controller_manifest_sha256": CONTROLLER,
        "continuation_wrapper_sha256": WRAPPER,
        "scan_time_adapter_sha256": ADAPTER,
        "scan_time_adapter_proof_sha256": PROOF,
        "scan_time_parser_protocol": "strict_utc_iso8601_ns_v1",
        "source_block_registry_sha256": REGISTRY,
        "daily_observation_status": "unknown",
        "deferred_days": ["2023-12-31"],
        "deferred_months": ["2023-12"],
        "blocked_pairs": ["SNPP:2023365.0106", "SNPP:2023365.1048"],
    }.items():
        require(value.get(key) == expected, "V3 final identity/policy")
    require(
        value.get("negative_label_permitted") is False
        and value.get("full_training_complete") is False
        and "error_type" not in value,
        "Reserve status and scientific limits",
    )
    require(
        (value["cpu_count"], value["pair_workers"], value["daily_workers"]) == (32, 24, 4),
        "Measured worker gate",
    )
    for key in ("pairs_processed_this_invocation", "pairs_reused_this_invocation"):
        require(type(value[key]) is int and 0 <= value[key] <= 18711, "Counter bound")
    for key in ("existing_months", "days_verified_this_invocation"):
        require(value[key] == sorted(set(value[key])), "Calendar ordering/duplicates")
    for month in value["existing_months"]:
        days(month)
    for day in value["days_verified_this_invocation"]:
        require(day in days(day[:7]) and day != "2023-12-31", "Verified day calendar")
    require("2023-12" not in value["existing_months"], "Deferred month remains incomplete")
    return value


def log_check(data, saved, nominal):
    pair_rows, committed, reused, complete, phases = [], [], [], [], []
    history = data.decode("utf-8").splitlines()
    starts = [
        i
        for i, line in enumerate(history)
        if line == "CONTINUATION PHASE december_safe_days deferred day 2023-12-31"
    ]
    require(starts, "V3 invocation start")
    # The launcher appends across restarts; counters cover only the latest invocation.
    lines = history[starts[-1] :]
    require(lines and lines[-1] == "Guest poweroff requested: True", "Successful shutdown request")
    for line in lines:
        if match := re.fullmatch(
            r"(\d{4}-\d{2}) pair saved/verified ((?:SNPP|N20):\d{7}\.\d{4})", line
        ):
            month, identity = match.groups()
            require(
                identity in nominal and nominal[identity][:7] == month, "Logged source catalogue"
            )
            pair_rows.append(identity)
        elif match := re.fullmatch(r"DAY COMMITTED (\d{4}-\d{2}-\d{2})", line):
            committed.append(match[1])
        elif match := re.fullmatch(r"Month verified/reused: (\d{4}-\d{2})", line):
            reused.append(match[1])
        elif match := re.fullmatch(r"MONTH NOMINAL DIAGNOSTICS COMPLETE: (\d{4}-\d{2})", line):
            complete.append(match[1])
        elif match := re.fullmatch(
            r"CONTINUATION PHASE (december_safe_days|remaining_months) deferred day 2023-12-31",
            line,
        ):
            phases.append(match[1])
        else:
            require(
                line in {"Reviewed V2 diagnostics preserved: 15", "Guest poweroff requested: True"}
                or re.fullmatch(r"Preparing verified metadata: \d{4}-\d{2} sources: \d+", line),
                "Unexpected log line; review without exposing external text",
            )
    require(phases == ["december_safe_days", "remaining_months"], "Single V3 invocation phases")
    for values in (pair_rows, committed, reused, complete):
        require(len(values) == len(set(values)), "Duplicate log identity")
    require(set(reused).isdisjoint(complete), "Month completion counted twice")
    require(
        set(saved["existing_months"]) == {"2023-07", *reused, *complete}, "Month log/state union"
    )
    reported = set(saved["days_verified_this_invocation"])
    require(set(committed) <= reported, "Committed day absent from state")
    for month in complete:
        require(days(month) <= reported, "Incomplete new month days")
    require(len(pair_rows) == saved["pairs_processed_this_invocation"], "New pair log counter")
    logged = set(pair_rows)
    missing = {i for i, d in nominal.items() if d in committed} - logged
    require(
        len(missing) == saved["pairs_reused_this_invocation"],
        "Committed catalogue/reuse accounting",
    )
    pending = Counter(nominal[i] for i in pair_rows if nominal[i] not in committed)
    require(all(d not in reported for d in pending), "Pending day reported complete")
    return {
        "new_months": complete,
        "prior_log_lines_excluded": starts[-1],
        "reused_months": reused,
        "day_commit_lines": len(committed),
        "days_only_in_state": sorted(reported - set(committed)),
        "new_pair_lines": len(pair_rows),
        "catalogue_inferred_reused_pairs": sorted(missing),
        "pending_days": {
            d: {
                "saved_pair_lines": count,
                "nominal_pairs": sum(x == d for x in nominal.values()),
                "daily_committed": False,
            }
            for d, count in sorted(pending.items())
        },
        "shutdown_request": True,
        "limitation": (
            "Reuse is inferred from catalogue accounting; product/completion bytes are absent."
        ),
    }


def telemetry(data):
    rows = list(csv.DictReader(io.StringIO(data.decode())))
    require(1 < len(rows) < 20000, "Telemetry population")
    for row in rows:
        for key, value in row.items():
            if key not in {"arm", "phase"}:
                require(
                    value == "" or math.isfinite(float(value)) and float(value) >= 0,
                    "Telemetry numbers",
                )
        require(row["cpu_busy_pct"] == "" or float(row["cpu_busy_pct"]) <= 100, "CPU percentage")
    times = [float(r["seconds"]) for r in rows]
    require(times == sorted(set(times)), "Telemetry time order")
    return {
        "samples": len(rows),
        "last_seconds": times[-1],
        "min_disk_free_gib": min(int(r["disk_free_bytes"]) for r in rows) / 2**30,
        "min_mem_available_gib": min(int(r["mem_available_bytes"]) for r in rows) / 2**30,
        "peak_process_tree_rss_gib": max(int(r["process_tree_rss_bytes"]) for r in rows) / 2**30,
        "mean_cpu_busy_pct": statistics.mean(
            float(r["cpu_busy_pct"]) for r in rows if r["cpu_busy_pct"]
        ),
        "sampled_reserve_breach": any(
            int(r["disk_free_bytes"]) < 4 * 2**30 or int(r["mem_available_bytes"]) < 4 * 2**30
            for r in rows
        ),
        "limitation": (
            "Samples do not cover every instant; CPU mean includes restore and metadata phases."
        ),
    }


def verify(source, output):
    files = contents(source)
    saved = state(files)
    package = ROOT / "outputs/gcp_production/package"
    spec = verify_package(package)
    controller = ROOT / "outputs/gcp_acceleration/package"
    raw = (controller / "acceleration_manifest.json").read_bytes()
    require(sha(raw) == CONTROLLER, "Pinned controller manifest")
    for name, checksum in json.loads(raw)["files"].items():
        require(
            Path(name).name == name and sha((controller / name).read_bytes()) == checksum,
            "Pinned controller member",
        )
    require(
        sha((ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v3.py").read_bytes())
        == WRAPPER,
        "Prepared wrapper SHA",
    )
    require(set(saved["existing_months"]) <= {*spec["months"], "2023-07"}, "Frozen month scope")
    with (package / "pairs.csv").open(encoding="utf-8", newline="") as stream:
        nominal = {
            r["sensor"] + ":" + r["pair_key"]: r["day"]
            for r in csv.DictReader(stream)
            if r["pair_status"] == "nominal_unique_pair"
        }
    require(len(nominal) == 18711, "Frozen nominal population")
    result = {
        "status": "v3_session_log_catalogue_readback_passed",
        "received_bytes": source.stat().st_size,
        "received_sha256": sha(source.read_bytes()),
        "member_sha256": {n: sha(b) for n, b in sorted(files.items())},
        "final_snapshots_equal": True,
        "final_state": saved,
        "log_catalogue": log_check(files["gcp_source_aware_launcher_v3.log"], saved, nominal),
        "telemetry": telemetry(files["resource_samples.csv"]),
        "scientific_product_readback": False,
        "live_drive_readback": False,
        "network_requests": 0,
        "production_writes": 0,
    }
    require(not output.exists(), "Readback report collision")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    folder = ROOT / "outputs/gcp_acceleration/source_aware_v3_2026-10-10"
    parser.add_argument(
        "--received", type=Path, default=folder / "received/gcp_v3_session_2026-10-10_logs.tar.gz"
    )
    parser.add_argument("--out", type=Path, default=folder / "session_log_readback.json")
    args = parser.parse_args()
    result = verify(args.received, args.out)
    print(result["status"], "months", len(result["final_state"]["existing_months"]), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("V3 log readback failed:", type(error).__name__, "; archive retained", flush=True)
        raise SystemExit(1) from None
