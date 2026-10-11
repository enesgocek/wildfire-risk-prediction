"""Bounded offline readback of the received V5 Drive metadata failure session."""

import argparse
import csv
import json
import tarfile
from pathlib import Path

import verify_gcp_v3_session_logs as base

WRAPPER = "f168692eb4aeda1eb7e00e72340a81d35f1a6701617a13da237e9376495ebf45"
FINAL = "b9c5de20486ae2ddebc0db2696a9625a219f19d0d38656d1cf5b6fadf00c1249"
MEMBERS = (base.MEMBERS - {"gcp_source_aware_launcher_v3.log"}) | {
    "gcp_source_aware_launcher_v5.log"
}
TAIL = [
    "HTTP_DIAGNOSTIC FILE_METADATA 404 notFound",
    "PARENT_FAILURE GOOGLE_HTTP_404 CLASS_ONLY",
    "Guest poweroff requested: True",
    "Continuation stopped: RuntimeError ; safe child diagnostics retained",
]


def contents(source):
    base.require(not source.is_symlink() and 0 < source.stat().st_size < base.LIMIT, "Archive size")
    files, total = {}, 0
    with tarfile.open(source, "r|gz") as archive:
        for member in archive:
            base.require(
                member.isfile() and member.name in MEMBERS and member.name not in files,
                "Archive boundary",
            )
            total += member.size
            base.require(0 < member.size < base.LIMIT and total < base.LIMIT, "Expanded bound")
            with archive.extractfile(member) as stream:
                data = stream.read()
            base.require(len(data) == member.size, "Archive short read")
            files[member.name] = data
    base.require(set(files) == MEMBERS, "Archive population")
    return files


def final_state(files):
    names = ("progress.json", "acceleration_run_summary.json", "continuation_summary.json")
    base.require(all(base.sha(files[n]) == FINAL for n in names), "Reviewed V5 final bytes")
    value = json.loads(files["progress.json"])
    base.require(
        value["status"] == "failed_checkpoints_retained"
        and value["continuation_wrapper_sha256"] == WRAPPER
        and value["error_type"] == "RuntimeError"
        and value["failed_month"] == "2020-07"
        and value["failed_phase"] == "pair_publication"
        and value["continuation_phase"] == "remaining_months",
        "Reviewed V5 failure identity",
    )
    normalized = {
        **value,
        "status": "paused_at_runtime_reserve",
        "continuation_wrapper_sha256": base.WRAPPER,
    }
    normalized.pop("error_type")
    base.state({n: json.dumps(normalized).encode() for n in names})
    return value


def verify(source, output):
    files = contents(source)
    saved = final_state(files)
    package = base.ROOT / "outputs/gcp_production/package"
    spec = base.verify_package(package)
    controller = base.ROOT / "outputs/gcp_acceleration/package"
    raw = (controller / "acceleration_manifest.json").read_bytes()
    base.require(base.sha(raw) == base.CONTROLLER, "Controller pin")
    for name, checksum in json.loads(raw)["files"].items():
        base.require(
            Path(name).name == name and base.sha((controller / name).read_bytes()) == checksum,
            "Controller member pin",
        )
    base.require(
        base.sha((base.ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v5.py").read_bytes())
        == WRAPPER,
        "V5 wrapper pin",
    )
    base.require(set(saved["existing_months"]) <= {*spec["months"], "2023-07"}, "Frozen scope")
    with (package / "pairs.csv").open(encoding="utf-8", newline="") as stream:
        nominal = {
            r["sensor"] + ":" + r["pair_key"]: r["day"]
            for r in csv.DictReader(stream)
            if r["pair_status"] == "nominal_unique_pair"
        }
    base.require(len(nominal) == 18711, "Catalogue population")
    lines = files["gcp_source_aware_launcher_v5.log"].decode().splitlines()
    base.require(lines[-4:] == TAIL, "Reviewed Drive failure tail")
    log = base.log_check("\n".join([*lines[:-4], TAIL[2]]).encode(), saved, nominal)
    result = {
        "status": "v5_failure_log_catalogue_readback_passed",
        "received_sha256": base.sha(source.read_bytes()),
        "received_bytes": source.stat().st_size,
        "member_sha256": {n: base.sha(b) for n, b in sorted(files.items())},
        "final_snapshots_equal": True,
        "final_state": saved,
        "failure_tail": TAIL,
        "log_catalogue": log,
        "telemetry": base.telemetry(files["resource_samples.csv"]),
        "historical_file_or_call_site_identified": False,
        "scientific_product_readback": False,
        "live_drive_readback": False,
        "network_requests": 0,
        "production_writes": 0,
    }
    base.require(not output.exists(), "Report collision")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
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
        print("V5 readback failed:", type(error).__name__, "; no external text logged", flush=True)
        raise SystemExit(1) from None
