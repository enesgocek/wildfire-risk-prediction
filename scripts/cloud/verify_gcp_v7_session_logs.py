"""Offline V7 final log/catalogue audit; no product acceptance or cloud operations."""

import argparse
import csv
import json
import re
import tarfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from diagnose_gcp_production_manifest import verify_package
from verify_gcp_v3_session_logs import (
    ADAPTER,
    CONTROLLER,
    PROOF,
    SCOPE,
    days,
    require,
    sha,
    telemetry,
)

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = "37a4c4c904b49cac1bb4bc690b485fea19b41e922f24002526ca5ad9d6d0bc3b"
REGISTRY = "c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95"
DEFERRED = {"2018-06-13", "2023-12-31"}
MONTHS = {f"{y}-{m:02d}" for y in range(2018, 2024) for m in range(1, 13)}
COMPLETE = MONTHS - {d[:7] for d in DEFERRED}
PARTIAL_DAYS = (days("2018-06") | days("2023-12")) - DEFERRED
NEW_MONTHS = {f"2018-{m:02d}" for m in range(1, 6)}
VERIFIED_DAYS = PARTIAL_DAYS | set().union(*(days(m) for m in NEW_MONTHS))
PHASES = ["december_safe_days", "june_safe_days", "remaining_months"]
SUFFIX = " deferred days 2018-06-13,2023-12-31"
LOG = "gcp_source_aware_launcher_v7.log"
SNAPSHOTS = {"progress.json", "acceleration_run_summary.json", "continuation_summary.json"}
MEMBERS = SNAPSHOTS | {LOG, "resource_samples.csv"}
LIMIT = 30_000_000


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
                data = stream.read(member.size + 1)
            require(len(data) == member.size, "Archive short read")
            result[member.name] = data
    require(set(result) == MEMBERS, "Archive population")
    return result


def strict_json(data):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, "Duplicate JSON key")
            value[key] = item
        return value

    def nonfinite(_):
        raise ValueError("Nonfinite JSON number")

    return json.loads(data, object_pairs_hook=unique, parse_constant=nonfinite)


def state(files, blocked):
    values = [strict_json(files[name]) for name in sorted(SNAPSHOTS)]
    require(values[0] == values[1] == values[2], "Final snapshots differ")
    value = values[0]
    expected = {
        "status": "processable_months_verified_source_resolution_pending",
        "continuation_phase": "remaining_months",
        "queue_manifest_sha256": SCOPE,
        "controller_manifest_sha256": CONTROLLER,
        "continuation_wrapper_sha256": WRAPPER,
        "source_block_registry_sha256": REGISTRY,
        "scan_time_adapter_sha256": ADAPTER,
        "scan_time_adapter_proof_sha256": PROOF,
        "scan_time_parser_protocol": "strict_utc_iso8601_ns_v1",
        "actual_vm_termination_timestamp": "2026-10-14T13:35:01.727602Z",
        "cpu_count": 32,
        "pair_workers": 24,
        "daily_workers": 4,
        "daily_observation_status": "unknown",
        "deferred_days": sorted(DEFERRED),
        "deferred_months": sorted({d[:7] for d in DEFERRED}),
        "blocked_pairs": sorted(blocked),
    }
    extra = {
        "negative_label_permitted",
        "full_training_complete",
        "existing_months",
        "days_verified_this_invocation",
        "pairs_processed_this_invocation",
        "pairs_reused_this_invocation",
    }
    require(set(value) == set(expected) | extra, "Final field population")
    require(all(value.get(k) == v for k, v in expected.items()), "V7 identity/policy")
    require(
        value["negative_label_permitted"] is False and value["full_training_complete"] is False,
        "Scientific limits",
    )
    require(value["existing_months"] == sorted(COMPLETE), "Exact 70 training months")
    require(
        value["days_verified_this_invocation"] == sorted(VERIFIED_DAYS),
        "Exact 210 verified days including 59 safe partial days",
    )
    for key in ("pairs_processed_this_invocation", "pairs_reused_this_invocation"):
        require(type(value[key]) is int and 0 <= value[key] <= 18711, "Counter bound")
    return value


def log_check(data, saved, nominal):
    history = data.decode("utf-8").splitlines()
    start_line = "CONTINUATION PHASE december_safe_days" + SUFFIX
    starts = [i for i, line in enumerate(history) if line == start_line]
    require(starts and starts[-1] > 0, "V7 invocation start")
    start = starts[-1]
    require(
        history[start - 1]
        == "Reviewed V6 lineage evidence preserved; children: 18; retained ZIPs: 22",
        "Reviewed V6 archive receipt message",
    )
    lines = history[start:]
    require(lines[-1] == "Guest poweroff requested: True", "Shutdown request")
    pairs, committed, reused, complete, phases = [], [], [], [], []
    for line in lines:
        if match := re.fullmatch(
            r"(\d{4}-\d{2}) pair saved/verified ((?:SNPP|N20):\d{7}\.\d{4})", line
        ):
            month, identity = match.groups()
            require(
                identity in nominal
                and nominal[identity][:7] == month
                and nominal[identity] not in DEFERRED,
                "Logged nominal source and nondeferred day",
            )
            pairs.append(identity)
        elif match := re.fullmatch(r"DAY COMMITTED (\d{4}-\d{2}-\d{2})", line):
            committed.append(match[1])
        elif match := re.fullmatch(r"Month verified/reused: (\d{4}-\d{2})", line):
            reused.append(match[1])
        elif match := re.fullmatch(r"MONTH NOMINAL DIAGNOSTICS COMPLETE: (\d{4}-\d{2})", line):
            complete.append(match[1])
        elif line.startswith("CONTINUATION PHASE ") and line.endswith(SUFFIX):
            phases.append(line.removeprefix("CONTINUATION PHASE ").removesuffix(SUFFIX))
        else:
            require(
                line == "Guest poweroff requested: True"
                or re.fullmatch(r"Preparing verified metadata: \d{4}-\d{2} sources: \d+", line),
                "Unexpected current-invocation log line",
            )
    require(phases == PHASES, "Three V7 phases")
    require(lines.count("Guest poweroff requested: True") == 1, "Single shutdown request")
    for group in (pairs, committed, reused, complete):
        require(len(group) == len(set(group)), "Duplicate log identity")
    require(set(complete) == NEW_MONTHS, "Five newly completed months")
    require(set(reused).isdisjoint(complete), "Month counted twice")
    require(
        set(saved["existing_months"]) == {"2023-07", *reused, *complete},
        "Month log/state union",
    )
    reported = set(saved["days_verified_this_invocation"])
    require(set(committed) <= reported, "Committed day absent from state")
    require(all(days(m) <= set(committed) for m in complete), "New month day closures")
    require(len(pairs) == saved["pairs_processed_this_invocation"], "New pair log counter")
    require(all(nominal[i] in committed for i in pairs), "Uncommitted new pair")
    missing = {i for i, day in nominal.items() if day in committed} - set(pairs)
    require(len(missing) == saved["pairs_reused_this_invocation"], "Catalogue reuse counter")
    return {
        "prefix_lines_excluded": start,
        "invocations_detected": len(starts),
        "new_months": sorted(complete),
        "reused_months": sorted(reused),
        "new_pair_lines": len(pairs),
        "new_pairs_by_month": dict(sorted(Counter(nominal[i][:7] for i in pairs).items())),
        "day_commit_lines": len(committed),
        "days_only_in_state": sorted(reported - set(committed)),
        "catalogue_inferred_reused_pairs": sorted(missing),
        "shutdown_request": True,
        "limitation": (
            "Restored days and reused products are producer reports; payload bytes absent."
        ),
    }


def verify(source, output):
    require(not output.exists(), "Readback report collision")
    files = contents(source)
    protected = strict_json(
        (
            ROOT / "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
            "protected_inputs_readback_20261013.json"
        ).read_bytes()
    )
    for name, checksum in protected.items():
        path = ROOT / name.replace("\\", "/")
        require(
            path.resolve().is_relative_to(ROOT.resolve())
            and not path.is_symlink()
            and sha(path.read_bytes()) == checksum,
            "Protected input hash",
        )
    require(
        sha((ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v7.py").read_bytes())
        == WRAPPER,
        "V7 wrapper pin",
    )
    raw_registry = (ROOT / "configs/gcp_source_blocks_2026-10-13.json").read_bytes()
    require(sha(raw_registry) == REGISTRY, "Source registry pin")
    registry = strict_json(raw_registry)
    saved = state(files, [row["sample_id"] for row in registry["blocked_pairs"]])
    package = ROOT / "outputs/gcp_production/package"
    spec = verify_package(package)
    require(MONTHS == {*spec["months"], "2023-07"}, "Frozen training month scope")
    controller = ROOT / "outputs/gcp_acceleration/package"
    raw = (controller / "acceleration_manifest.json").read_bytes()
    require(sha(raw) == CONTROLLER, "Controller manifest pin")
    for name, checksum in strict_json(raw)["files"].items():
        require(
            Path(name).name == name
            and not (controller / name).is_symlink()
            and sha((controller / name).read_bytes()) == checksum,
            "Controller member pin",
        )
    with (package / "pairs.csv").open(encoding="utf-8", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["pair_status"] == "nominal_unique_pair"]
    nominal = {r["sensor"] + ":" + r["pair_key"]: r["day"] for r in rows}
    require(len(rows) == len(nominal) == 18711, "Nominal population and unique identities")
    catalogue = log_check(files[LOG], saved, nominal)
    resources = telemetry(files["resource_samples.csv"])
    require(resources["last_seconds"] <= 18 * 3600, "18-hour telemetry bound")
    require(not resources["sampled_reserve_breach"], "Sampled resource reserves")
    result = {
        "status": "v7_final_log_catalogue_readback_passed",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "received_bytes": source.stat().st_size,
        "received_sha256": sha(source.read_bytes()),
        "audit_script_sha256": sha(Path(__file__).read_bytes()),
        "member_sha256": {n: sha(b) for n, b in sorted(files.items())},
        "protected_inputs_unchanged": len(protected),
        "final_snapshots_equal": True,
        "final_state": saved,
        "log_catalogue": catalogue,
        "telemetry": resources,
        "safe_partial_days_verified": len(PARTIAL_DAYS),
        "scientific_product_readback": False,
        "live_drive_readback": False,
        "network_requests": 0,
        "production_writes": 0,
        "vm_stop_source": "user_confirmed_after_download",
        "limitation": "Offline log/catalogue closure; product/checkpoint bytes not supplied.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--received", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.received, args.out)
    print(result["status"], "months", len(result["final_state"]["existing_months"]))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("V7 final readback failed:", type(error).__name__, "; archive retained")
        raise SystemExit(1) from None
