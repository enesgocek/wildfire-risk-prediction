"""Read-only Drive check after the exact reviewed V5 failure; never resume production."""

import csv
import hashlib
import importlib.util
import json
import os
import re
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path

SCOPE = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
CONTROLLER = "102c9e4ab16e4450d0d94eb3511dfdbf360fd6b6292809c5457efc93d2be5837"
WRAPPER = "f168692eb4aeda1eb7e00e72340a81d35f1a6701617a13da237e9376495ebf45"
FINAL = "b9c5de20486ae2ddebc0db2696a9625a219f19d0d38656d1cf5b6fadf00c1249"
HELPER = "e1402d4cb28263fe8d05c474656ed64094cd069ca77040ed09e6d0a7296a9c63"
MARKER_FIELDS = {
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


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path, owner, limit=20_000_000):
    require(path.resolve().is_relative_to(owner.resolve()), "Local file boundary")
    current = path
    while current != owner.parent:
        require(not current.is_symlink(), "Local file symlink")
        if current == owner:
            break
        current = current.parent
    require(path.is_file() and 0 < path.stat().st_size <= limit, "Local byte bound")
    return path.read_bytes()


def checked_helper(home):
    path = home / "diagnose_gcp_production_manifest.py"
    require(sha(read(path, home)) == HELPER, "Pinned HTTP helper")
    spec = importlib.util.spec_from_file_location("checked_v5_http_helper", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def readonly_requests(api):
    original = api.request

    def request(path, method="GET", data=None, content_type=None, upload=False):
        require(method == "GET" and data is None and not upload, "Probe write forbidden")
        return original(path, method=method, data=data, content_type=content_type, upload=upload)

    api.request = request


def check_pair(backend, identity, local, worker, stage):
    prefix = f"jobs/{SCOPE}/{sha(identity.encode())}"
    digest = sha(local)
    key = prefix + "/" + digest + ".zip"
    marker = stage("candidate_marker", lambda: backend.get(prefix + "/completed.json"))
    if marker is not None:
        require(0 < len(marker) < 65536, "Completion byte bound")
        value = json.loads(marker)
        require(
            set(value) == MARKER_FIELDS
            and value["protocol"] == "verified_job_checkpoint_v1"
            and value["task_id"] == identity
            and value["manifest_sha256"] == SCOPE
            and value["worker_sha256"] == worker
            and value["payload_sha256"] == digest
            and type(value["payload_bytes"]) is int
            and value["payload_bytes"] == len(local)
            and value["payload_key"] == key
            and value["negative_label_permitted"] is False
            and value["daily_observation_status"] == "unknown",
            "Completion differs from retained pair",
        )
    remote = stage("candidate_payload", lambda: backend.get(key))
    require(remote is None or remote == local, "Retained immutable bytes differ")
    require(marker is None or remote is not None, "Completed payload missing")
    return {
        "sample_id": identity,
        "local_sha256": digest,
        "local_bytes": len(local),
        "state": "completed_matches_local"
        if marker is not None
        else ("payload_without_completion" if remote is not None else "not_published"),
    }


def retained_pairs(work, original):
    plan = json.loads(read(work / "months/2020-07/metadata/month.json", work, 2_000_000))
    require(plan["month"] == "2020-07" and plan["negative_label_permitted"] is False, "Month plan")
    with (original / "pairs.csv").open(encoding="utf-8", newline="") as stream:
        nominal = {
            r["sensor"] + ":" + r["pair_key"]
            for r in csv.DictReader(stream)
            if r["pair_status"] == "nominal_unique_pair" and r["day"].startswith("2020-07-")
        }
    ids = [p["sample_id"] for p in plan["pairs"]]
    require(len(ids) == len(set(ids)) and set(ids) == nominal, "Frozen July pair population")
    pairs = {sha(identity.encode()): identity for identity in ids}
    task_root = work / "months/2020-07/accelerated_run/tasks"
    require(task_root.is_dir() and not task_root.is_symlink(), "Retained task directory")
    roots = sorted(task_root.iterdir())
    require(len(roots) <= 64, "Retained task bound")
    candidates, preserved, failures, total = [], {}, [], 0
    for root in roots:
        require(root.is_dir() and not root.is_symlink() and root.name in pairs, "Retained identity")
        failure = root / "continuation_failure.json"
        if failure.exists():
            data = read(failure, work, 65536)
            value = json.loads(data)
            shared = {"sample_id": pairs[root.name], "child_kind": "pair", "guard": "CLASS_ONLY"}
            timeout = {**shared, "error_type": "ReadTimeout", "safe_error": "UNCLASSIFIED_ERROR"}
            killed = {
                **shared,
                "error_type": "RuntimeError",
                "exit_code": -9,
                "termination_kind": "nonzero_exit_without_python_diagnostic",
            }
            require(value.get("sample_id") == pairs[root.name], "Child diagnostic identity")
            preserved[failure] = sha(data)
            failures.append(
                {
                    "path": failure.relative_to(work).as_posix(),
                    "sha256": sha(data),
                    "reviewed_schema": "read_timeout"
                    if value == timeout
                    else ("cancelled_exit_minus_9" if value == killed else "OTHER_UNREVIEWED"),
                }
            )
        path = root / "pair.zip"
        if path.exists():
            data = read(path, work, 100_000_000)
            total += len(data)
            require(total <= 250_000_000, "Candidate total byte bound")
            preserved[path] = sha(data)
            candidates.append((pairs[root.name], data))
    require(candidates, "Retained payload candidates required")
    return candidates, preserved, failures


def parent_diagnostic(work):
    folder = work / "diagnostics"
    require(folder.is_dir() and not folder.is_symlink(), "Diagnostic directory")
    paths = sorted(folder.glob("parent_failure_v3_*.json"))
    require(0 < len(paths) <= 64, "Parent diagnostic bound")
    path = paths[-1]
    require(re.fullmatch(r"parent_failure_v3_\d{8}T\d{12}Z\.json", path.name), "Parent basename")
    data = read(path, work, 65536)
    value = json.loads(data)
    expected = {
        "protocol": "continuation_parent_failure_v3",
        "continuation_phase": "remaining_months",
        "error": "GOOGLE_HTTP_404",
        "guard": "CLASS_ONLY",
        "last_recorded_month": "2020-07",
        "last_recorded_stage": "pair_publication",
    }
    require(set(value) == {*expected, "recorded_at_utc"}, "Parent schema")
    require(all(value[k] == v for k, v in expected.items()), "Reviewed parent failure")
    when = datetime.fromisoformat(value["recorded_at_utc"].replace("Z", "+00:00"))
    require(when.tzinfo is not None and when.date().isoformat() == "2026-10-11", "Parent date")
    return {
        "path": path.relative_to(work).as_posix(),
        "sha256": sha(data),
        **expected,
        "recorded_at_utc": when.astimezone(UTC).isoformat(),
    }, {path: sha(data)}


def main():
    home = Path.home()
    helper = checked_helper(home)
    work = home / "wildfire-gcp-production-v1"
    target = home / (
        "gcp_v5_drive_probe_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
    )
    require(not target.exists(), "Probe report collision")
    report = {
        "protocol": "gcp_v5_drive_readonly_probe_v1",
        "status": "failed",
        "reviewed_final_sha256": FINAL,
        "production_writes": 0,
        "drive_object_writes": 0,
        "raw_processing": False,
        "historical_exception_identified": False,
        "scientific_product_acceptance": False,
        "pairs": [],
    }
    current = "setup"
    protected = {}

    def stage(name, action):
        nonlocal current
        current = name
        result = action()
        print("PASS", name, flush=True)
        return result

    def deadline(_signum, _frame):
        raise RuntimeError("Read-only probe deadline")

    try:
        signal.signal(signal.SIGALRM, deadline)
        signal.alarm(230)
        with helper.exclusive_work(work):
            for name in (
                "progress.json",
                "acceleration_run_summary.json",
                "continuation_summary.json",
            ):
                path = work / name
                require(sha(read(path, work, 65536)) == FINAL, "Reviewed V5 final pin")
                protected[path] = FINAL
            wrapper = home / "run_gcp_source_aware_continuation_v5.py"
            require(sha(read(wrapper, home)) == WRAPPER, "V5 wrapper pin")
            original = home / "wildfire-gcp-production-package"
            spec = stage("original_package", lambda: helper.verify_package(original))
            controller = home / "wildfire-gcp-acceleration-package"
            raw = read(controller / "acceleration_manifest.json", controller)
            require(sha(raw) == CONTROLLER, "Controller manifest pin")
            for name, digest in json.loads(raw)["files"].items():
                require(Path(name).name == name and "\\" not in name, "Controller basename")
                require(sha(read(controller / name, controller)) == digest, "Controller member pin")
            parent, local = stage("parent_diagnostic", lambda: parent_diagnostic(work))
            protected.update(local)
            report["parent_diagnostic"] = parent
            candidates, local, failures = stage(
                "retained_candidates", lambda: retained_pairs(work, original)
            )
            protected.update(local)
            report["child_diagnostics"] = failures
            report["retained_candidates"] = len(candidates)
            report["retained_bytes"] = sum(len(data) for _, data in candidates)
            helper.load_modules(original)
            sys.path.insert(0, str(controller))
            from accelerated_checkpoint_store import IndexedDriveStore

            backend = stage(
                "private_connection",
                lambda: IndexedDriveStore.from_file(
                    home / ".config/wildfire/drive_connection.json"
                ),
            )
            readonly_requests(backend.api)
            backend.api.opener = helper.diagnostic_opener(backend.api.opener)
            stage("oauth_refresh", backend.api.token)
            folder = stage(
                "drive_folder_access",
                lambda: json.loads(
                    backend.api.request(f"/files/{backend.folder_id}?fields=mimeType,trashed")
                ),
            )
            require(
                folder.get("mimeType") == "application/vnd.google-apps.folder"
                and folder.get("trashed") is False,
                "Checkpoint folder unavailable",
            )
            report["quota"] = stage(
                "drive_quota",
                lambda: helper.quota_values(
                    backend.api.request("/about?fields=storageQuota(limit,usage)")
                ),
            )
            objects = stage("production_listing", lambda: backend.populate(SCOPE))
            report["object_count"] = len(objects)
            report["saved_bytes"] = sum(int(v["size"]) for v in objects.values())
            worker = spec["files"]["run_gcp_production.py"]
            for identity, data in candidates:
                report["checking_sample_id"] = identity
                report["pairs"].append(check_pair(backend, identity, data, worker, stage))
            report.pop("checking_sample_id", None)
            report["status"] = "readonly_checks_passed"
    except Exception as error:
        report["failed_stage"] = current
        report["error"] = helper.safe_error(error)
        print("FAIL", current, report["error"], flush=True)
    finally:
        signal.alarm(0)
    # A diagnostic must not modify the final states or any retained candidate.
    report["protected_files_unchanged"] = all(
        sha(read(path, work, 100_000_000)) == digest for path, digest in protected.items()
    )
    require(report["protected_files_unchanged"], "Protected production bytes changed")
    with target.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("Download:", target, flush=True)
    print("Stop VM after downloading; this probe does not shut it down.", flush=True)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except Exception as error:
        print("Probe setup failed:", type(error).__name__, "; no external text logged", flush=True)
        raise SystemExit(1) from None
