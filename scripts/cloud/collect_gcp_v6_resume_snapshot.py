"""Capture reviewed cancellation diagnostics and retained ZIP hashes; no raw reads."""

import importlib.util
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

HELPER_SHA = "b321b30a2bf81dea0c64d6da9239fd43bfb7207a7199ea0d7e39341e03ea2268"
PROOF_NAME = "gcp_v6_geolocation_snapshot_20261013T125412909568Z.json"
PROOF_SHA = "506ec0451d26436c562ab31a5ab74c9fea4a100c860fc4a45fcd59d103b821bc"
PLAN_SHA = "9681b5509ee08f5b915e1bd3665589bfc415683ce4a4354f579f98e65a19e32d"
CANCELLED = (
    "N20:2018165.0000",
    "N20:2018165.0942",
    "N20:2018165.1124",
    "N20:2018165.2342",
    "SNPP:2018164.0112",
    "SNPP:2018164.1054",
    "SNPP:2018164.2312",
    "SNPP:2018165.0054",
    "SNPP:2018165.1036",
    "SNPP:2018165.1212",
    "SNPP:2018165.1218",
    "SNPP:2018165.2254",
)


def collect(home, helper, proof):
    current = helper.snapshot(home)
    helper.require(
        current["protected_file_sha256"] == proof["protected_file_sha256"]
        and current["month_plan_sha256"] == PLAN_SHA,
        "Same previously reviewed source evidence",
    )
    work = home / "wildfire-gcp-production-v1"
    plan_path = work / "months/2018-06/metadata/month.json"
    plan = json.loads(helper.read(plan_path, work, 2_000_000))
    pairs = {helper.sha(pair["sample_id"].encode()): pair for pair in plan["pairs"]}
    tasks = work / "months/2018-06/accelerated_run/tasks"
    helper.boundary(tasks, work)
    roots = sorted(tasks.iterdir())
    helper.require(
        0 < len(roots) <= 1000 and all(root.is_dir() and root.name in pairs for root in roots),
        "Retained task boundary",
    )
    protected = {}

    def remember(path, limit=65536):
        raw = helper.read(path, work, limit)
        protected[path] = (limit, helper.sha(raw))
        return raw

    failures, retained = [], []
    expected_ids = set(helper.FOCUS) | set(CANCELLED)
    for root in roots:
        helper.boundary(root, work)
        identity = pairs[root.name]["sample_id"]
        failure = root / "continuation_failure.json"
        if failure.exists():
            helper.require(identity in expected_ids, "Unreviewed child failure")
            raw = remember(failure)
            value = json.loads(raw)
            helper.require(
                value.get("sample_id") == identity and value.get("child_kind") == "pair",
                "Diagnostic identity",
            )
            if identity in helper.FOCUS:
                selected = next(
                    s["filename"] for s in pairs[root.name]["sources"] if s["role"] == "geolocation"
                )
                safe = helper.safe_failure(value, identity, selected)
                helper.require(
                    helper.sha(raw)
                    == proof["protected_file_sha256"][failure.relative_to(home).as_posix()],
                    "Same geolocation child diagnostic",
                )
            else:
                helper.require(
                    value.get("error_type") == "RuntimeError"
                    and value.get("guard") == "CLASS_ONLY"
                    and type(value.get("exit_code")) is int
                    and value["exit_code"] == -9
                    and value.get("termination_kind") == "nonzero_exit_without_python_diagnostic",
                    "Reviewed cancelled child diagnostic",
                )
                safe = {
                    "sample_id": identity,
                    "error_type": "RuntimeError",
                    "guard": "CLASS_ONLY",
                    "exit_code": -9,
                    "termination_kind": "nonzero_exit_without_python_diagnostic",
                }
            failures.append(
                {"path": failure.relative_to(work).as_posix(), "sha256": helper.sha(raw), **safe}
            )
        payload = root / "pair.zip"
        if payload.exists():
            raw = remember(payload, 20_000_000)
            retained.append(
                {
                    "sample_id": identity,
                    "path": payload.relative_to(work).as_posix(),
                    "bytes": len(raw),
                    "sha256": helper.sha(raw),
                }
            )
    helper.require(
        {row["sample_id"] for row in failures} == expected_ids,
        "Exactly reviewed failure population",
    )
    parents = []
    parent_paths = sorted((work / "diagnostics").glob("parent_failure_v3_*.json"))
    helper.require(0 < len(parent_paths) <= 100, "Parent diagnostic bound")
    for path in parent_paths:
        raw = remember(path)
        value = json.loads(raw)
        if value.get("last_recorded_month") != "2018-06":
            continue
        helper.require(
            value.get("protocol") == "continuation_parent_failure_v3"
            and value.get("continuation_phase") == "remaining_months"
            and value.get("error") == "RuntimeError"
            and value.get("guard") == "CLASS_ONLY"
            and value.get("last_recorded_stage") == "pair_publication",
            "Reviewed parent diagnostic",
        )
        parents.append(
            {
                "path": path.relative_to(work).as_posix(),
                "sha256": helper.sha(raw),
                "error_type": "RuntimeError",
                "guard": "CLASS_ONLY",
            }
        )
    helper.require(len(parents) == 1, "Exactly one reviewed June parent")
    helper.require(
        all(
            helper.sha(helper.read(path, work, limit)) == digest
            for path, (limit, digest) in protected.items()
        )
        and helper.snapshot(home)["protected_file_sha256"] == proof["protected_file_sha256"],
        "Protected resume evidence changed",
    )
    return {
        "protocol": "gcp_v6_resume_snapshot_v1",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "reviewed_final_sha256": helper.FINAL_SHA,
        "geolocation_snapshot_sha256": PROOF_SHA,
        "month_plan_sha256": PLAN_SHA,
        "child_diagnostics": failures,
        "parent_diagnostics": parents,
        "retained_pair_zips": retained,
        "retained_pair_zip_bytes": sum(row["bytes"] for row in retained),
        "protected_files_unchanged": True,
        "credentials_read": False,
        "raw_source_contents_read": False,
        "network_requests": 0,
        "production_writes": 0,
        "scientific_product_readback": False,
    }


def main():
    import fcntl

    if sys.platform != "linux":
        raise ValueError("Linux snapshot environment")
    home = Path.home()
    path = home / "collect_gcp_v6_geolocation_snapshot.py"
    if path.is_symlink() or not path.is_file():
        raise ValueError("Pinned helper path")
    import hashlib

    if hashlib.sha256(path.read_bytes()).hexdigest() != HELPER_SHA:
        raise ValueError("Pinned helper identity")
    spec = importlib.util.spec_from_file_location("checked_v6_geolocation", path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    proof_raw = helper.read(home / PROOF_NAME, home)
    helper.require(helper.sha(proof_raw) == PROOF_SHA, "Accepted geolocation snapshot")
    lock = home / "wildfire-gcp-production-v1/job.lock"
    helper.boundary(lock, home)
    helper.require(lock.is_file(), "Existing job lock")
    with lock.open("r") as stream:
        fcntl.flock(stream, fcntl.LOCK_SH | fcntl.LOCK_NB)
        result = collect(home, helper, json.loads(proof_raw))
    target = home / f"gcp_v6_resume_snapshot_{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}.json"
    with target.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("Resume snapshot collected; child diagnostics:", len(result["child_diagnostics"]))
    print("Download:", target)
    print("Stop VM after downloading; no production started.")


if __name__ == "__main__":
    os.umask(0o077)
    sys.dont_write_bytecode = True
    try:
        main()
    except Exception as error:
        print("Resume snapshot failed:", type(error).__name__, "; no external text logged")
        raise SystemExit(1) from None
