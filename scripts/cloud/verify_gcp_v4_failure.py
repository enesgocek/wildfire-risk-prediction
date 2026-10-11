"""Bounded offline readback of the reviewed V4 timeout session, without cloud access."""

import argparse
import csv
import json
import re
import tarfile
from collections import Counter
from pathlib import Path

import verify_gcp_v3_session_logs as base

WRAPPER = "30a6bd4f65830e612dae69102abe3a0802f009c4689f626a2e64a8f165f1b7ef"
FINAL = "58ff87f1e696740e602ea6e1ea340eaf64488b67510eabfcee82d0055da0d1b6"
BASE = (base.MEMBERS - {"gcp_source_aware_launcher_v3.log"}) | {"gcp_source_aware_launcher_v4.log"}
CHILD = r"months/2020-07/accelerated_run/tasks/[0-9a-f]{64}/continuation_failure\.json"
PARENT = r"diagnostics/parent_failure_v3_\d{8}T\d{12}Z\.json"


def contents(source):
    base.require(not source.is_symlink() and 0 < source.stat().st_size < base.LIMIT, "Archive size")
    files, total = {}, 0
    with tarfile.open(source, "r|gz") as archive:
        for member in archive:
            base.require(
                member.isfile()
                and member.name not in files
                and (
                    member.name in BASE
                    or re.fullmatch(CHILD, member.name)
                    or re.fullmatch(PARENT, member.name)
                ),
                "Archive boundary",
            )
            total += member.size
            base.require(
                0 < member.size < base.LIMIT and total < base.LIMIT and len(files) < 256,
                "Expanded bound",
            )
            if member.name not in BASE:
                base.require(member.size < 65536, "Diagnostic bound")
            with archive.extractfile(member) as stream:
                data = stream.read()
            base.require(len(data) == member.size, "Short archive read")
            files[member.name] = data
    base.require(BASE <= set(files), "Base members")
    return files


def diagnostics(files):
    result = []
    parents = []
    for name, data in files.items():
        if re.fullmatch(CHILD, name):
            value = json.loads(data)
            sample = value["sample_id"]
            base.require(
                re.fullmatch(r"(?:SNPP|N20):202018[345]\.\d{4}", sample)
                and name.split("/")[-2] == base.sha(sample.encode()),
                "Task identity",
            )
            shared = {"sample_id": sample, "child_kind": "pair", "guard": "CLASS_ONLY"}
            timeout = {**shared, "error_type": "ReadTimeout", "safe_error": "UNCLASSIFIED_ERROR"}
            killed = {
                **shared,
                "error_type": "RuntimeError",
                "exit_code": -9,
                "termination_kind": "nonzero_exit_without_python_diagnostic",
            }
            base.require(value in (timeout, killed), "Closed failure schema")
            result.append({"path": name, "sha256": base.sha(data), **value})
        elif re.fullmatch(PARENT, name):
            value = json.loads(data)
            base.require(
                value["protocol"] == "continuation_parent_failure_v3"
                and value["error"] == "RuntimeError"
                and value["guard"] == "CLASS_ONLY"
                and value["last_recorded_month"] == "2020-07"
                and value["last_recorded_stage"] == "prepare_day"
                and value["continuation_phase"] == "remaining_months",
                "Parent failure",
            )
            parents.append({"path": name, "sha256": base.sha(data), **value})
    base.require(
        len(result) == 24
        and len(parents) == 1
        and Counter(r["error_type"] for r in result) == {"ReadTimeout": 5, "RuntimeError": 19},
        "Reviewed batch population",
    )
    return sorted(result, key=lambda r: r["path"]), parents


def verify(source, output):
    files = contents(source)
    names = ("progress.json", "acceleration_run_summary.json", "continuation_summary.json")
    base.require(all(base.sha(files[n]) == FINAL for n in names), "Exact reviewed final bytes")
    value = json.loads(files["progress.json"])
    # Reuse calendar, counter, source identity and scientific policy gates, with
    # only the reviewed failure status/wrapper substituted for the V3 success gate.
    normalized = {
        **value,
        "status": "paused_at_runtime_reserve",
        "continuation_wrapper_sha256": base.WRAPPER,
    }
    normalized.pop("error_type")
    base.state({n: json.dumps(normalized).encode() for n in names})
    base.require(
        value["status"] == "failed_checkpoints_retained"
        and value["continuation_wrapper_sha256"] == WRAPPER
        and value["error_type"] == "RuntimeError"
        and value["failed_month"] == "2020-07"
        and value["failed_phase"] == "prepare_day",
        "Reviewed V4 failure state",
    )
    children, parents = diagnostics(files)
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
        base.sha((base.ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v4.py").read_bytes())
        == WRAPPER,
        "V4 wrapper pin",
    )
    base.require(set(value["existing_months"]) <= {*spec["months"], "2023-07"}, "Scope")
    with (package / "pairs.csv").open(encoding="utf-8", newline="") as stream:
        nominal = {
            r["sensor"] + ":" + r["pair_key"]: r["day"]
            for r in csv.DictReader(stream)
            if r["pair_status"] == "nominal_unique_pair"
        }
    base.require(len(nominal) == 18711, "Catalogue population")
    lines = files["gcp_source_aware_launcher_v4.log"].decode().splitlines()
    tail = "Continuation stopped: RuntimeError ; safe child diagnostics retained"
    base.require(lines[-2:] == ["Guest poweroff requested: True", tail], "Failure shutdown tail")
    cleaned, failures, exits = [], [], []
    for line in lines[:-1]:
        if match := re.fullmatch(
            r"CHILD FAILED ((?:SNPP|N20):\d{7}\.\d{4}) "
            r"(ReadTimeout|RuntimeError) CLASS_ONLY",
            line,
        ):
            failures.append(match.groups())
        elif match := re.fullmatch(r"CHILD_EXIT ((?:SNPP|N20):\d{7}\.\d{4}) -9", line):
            exits.append(match[1])
        elif line == "PARENT_FAILURE RuntimeError CLASS_ONLY":
            continue
        else:
            cleaned.append(line)
    base.require(
        Counter(failures) == Counter((r["sample_id"], r["error_type"]) for r in children)
        and Counter(exits)
        == Counter(r["sample_id"] for r in children if r["error_type"] == "RuntimeError"),
        "Diagnostic/log agreement",
    )
    log = base.log_check("\n".join(cleaned).encode(), value, nominal)
    result = {
        "status": "v4_failure_log_catalogue_readback_passed",
        "received_sha256": base.sha(source.read_bytes()),
        "member_sha256": {n: base.sha(b) for n, b in sorted(files.items())},
        "final_state": value,
        "child_failures": children,
        "parent_failures": parents,
        "log_catalogue": log,
        "telemetry": base.telemetry(files["resource_samples.csv"]),
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
    main()
