"""Read-only Drive probe of the retained November failure; no production writes or launch."""

import importlib.util
import json
import os
import re
import signal
import sys
from pathlib import Path

CAPTURE_SHA = "8e0419b0f4060a3cdec9c167efa08054fd34c60ef9d290d43a6e038f9fa32e0d"
DIAGNOSTIC_SHA = "e1402d4cb28263fe8d05c474656ed64094cd069ca77040ed09e6d0a7296a9c63"
MONTH_SHA = "eef25617a86cd9f5ab41def17d50975f6d4cb521a517a1317a7c696931fb5858"


def require(ok, label):
    if not ok:
        raise ValueError(label)


def helper(home, name, digest):
    import hashlib

    path = home / name
    require(path.is_file() and not path.is_symlink(), "Diagnostic helper missing")
    require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, "Diagnostic helper hash")
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def readonly_requests(api):
    original = api.request

    def request(path, method="GET", data=None, content_type=None, upload=False):
        require(method == "GET" and data is None and not upload, "Probe write forbidden")
        return original(path, method=method, data=data, content_type=content_type, upload=upload)

    api.request = request


def probe_pairs(backend, candidates, scope, worker_sha, sha, stage):
    """Read existing markers/payloads; neither create nor repair any object."""
    results = []
    for identity, local in candidates:
        prefix = f"jobs/{scope}/{sha(identity.encode())}"
        digest = sha(local)
        payload_key = f"{prefix}/{digest}.zip"
        marker = stage(
            "retained_pair_marker", lambda key=prefix: backend.get(key + "/completed.json")
        )
        if marker is not None:
            require(len(marker) < 65536, "Completion byte bound")
            value = json.loads(marker)
            require(
                set(value)
                == {
                    "protocol",
                    "task_id",
                    "manifest_sha256",
                    "worker_sha256",
                    "payload_sha256",
                    "payload_bytes",
                    "payload_key",
                    "negative_label_permitted",
                    "daily_observation_status",
                },
                "Completion schema",
            )
            require(
                value["protocol"] == "verified_job_checkpoint_v1"
                and value["task_id"] == identity
                and value["manifest_sha256"] == scope
                and value["worker_sha256"] == worker_sha
                and value["payload_sha256"] == digest
                and value["payload_key"] == payload_key
                and value["payload_bytes"] == len(local)
                and value["negative_label_permitted"] is False
                and value["daily_observation_status"] == "unknown",
                "Completion differs from local pair",
            )
        remote = stage("retained_pair_payload", lambda key=payload_key: backend.get(key))
        require(remote is None or remote == local, "Immutable retained payload differs")
        require(marker is None or remote is not None, "Completed payload missing")
        results.append(
            {
                "sample_id": identity,
                "local_sha256": digest,
                "local_bytes": len(local),
                "state": "completed_matches_local"
                if marker
                else ("payload_without_completion" if remote is not None else "not_published"),
            }
        )
    return results


def main():
    home = Path.home()
    capture = helper(home, "collect_gcp_source_aware_failure.py", CAPTURE_SHA)
    diagnostic = helper(home, "diagnose_gcp_production_manifest.py", DIAGNOSTIC_SHA)
    work = home / "wildfire-gcp-production-v1"
    target = home / "gcp_continuation_publication_probe_2026-10-09.json"
    require(not target.exists() and not target.is_symlink(), "Probe report already exists")
    report = {
        "protocol": "gcp_continuation_readonly_probe_v1",
        "status": "failed",
        "production_writes": 0,
        "drive_object_writes": 0,
        "raw_processing": False,
        "historical_exception_identified": False,
    }
    current = "lock"

    def stage(name, action):
        nonlocal current
        current = name
        result = action()
        print("PASS", name, flush=True)
        return result

    try:
        if hasattr(signal, "SIGALRM"):

            def deadline(_signal, _frame):
                raise RuntimeError("Read-only probe deadline")

            signal.signal(signal.SIGALRM, deadline)
            signal.alarm(230)
        with diagnostic.exclusive_work(work):
            original = home / "wildfire-gcp-production-package"
            controller = home / "wildfire-gcp-acceleration-package"
            spec = stage("original_package", lambda: diagnostic.verify_package(original))
            stage(
                "controller_package",
                lambda: capture.pinned(
                    controller, "acceleration_manifest.json", capture.CONTROLLER
                ),
            )
            stage(
                "continuation_wrapper",
                lambda: require(
                    capture.sha(capture.read(home / "run_gcp_source_aware_continuation.py", home))
                    == capture.WRAPPER,
                    "Pinned wrapper changed",
                ),
            )
            state = stage(
                "failed_invocation",
                lambda: capture.state(capture.read(work / "progress.json", work, 65536)),
            )
            require(
                state["failed_month"] == "2022-11"
                and state["pairs_processed_this_invocation"] == 1989,
                "Probe invocation changed",
            )
            meta = work / "months/2022-11/metadata/month.json"
            plan_bytes = capture.read(meta, work, 2_000_000)
            require(capture.sha(plan_bytes) == MONTH_SHA, "Failed month plan changed")
            plan = json.loads(plan_bytes)
            task_root = work / "months/2022-11/accelerated_run/tasks"
            pairs = {capture.sha(p["sample_id"].encode()): p for p in plan["pairs"]}
            roots = sorted(task_root.iterdir())
            require(len(roots) <= 100, "Retained task bound")
            candidates = []
            for root in roots:
                require(
                    root.is_dir() and not root.is_symlink() and root.name in pairs,
                    "Retained task identity",
                )
                if (root / "pair.zip").exists():
                    candidates.append(
                        (
                            pairs[root.name]["sample_id"],
                            capture.read(root / "pair.zip", work, 100_000_000),
                        )
                    )
            require(
                len(candidates) == 19 and sum(len(v) for _, v in candidates) < 150_000_000,
                "Retained pair population changed",
            )
            diagnostic.load_modules(original)
            sys.path.insert(0, str(controller))
            from accelerated_checkpoint_store import IndexedDriveStore

            backend = stage(
                "private_connection",
                lambda: IndexedDriveStore.from_file(
                    home / ".config/wildfire/drive_connection.json"
                ),
            )
            backend.api.opener = diagnostic.diagnostic_opener(backend.api.opener)
            readonly_requests(backend.api)
            stage("oauth_refresh", backend.api.token)
            quota = stage(
                "drive_quota",
                lambda: diagnostic.quota_values(
                    backend.api.request("/about?fields=storageQuota(limit,usage)")
                ),
            )
            report["quota"] = quota
            objects = stage("production_listing", lambda: backend.populate(capture.SCOPE))
            report["object_count"] = len(objects)
            report["saved_bytes"] = sum(int(v["size"]) for v in objects.values())
            manifest = probe_pairs(
                backend,
                [("manifest:2022-11", capture.read(work / "months/2022-11/manifest.zip", work))],
                capture.SCOPE,
                spec["files"]["run_gcp_production.py"],
                capture.sha,
                stage,
            )
            require(manifest[0]["state"] == "completed_matches_local", "Remote manifest missing")
            report["manifest_readback"] = manifest[0]
            report["pairs"] = probe_pairs(
                backend,
                candidates,
                capture.SCOPE,
                spec["files"]["run_gcp_production.py"],
                capture.sha,
                stage,
            )
            report["status"] = "readonly_checks_passed"
    except Exception as error:
        report["failed_stage"] = current
        report["error"] = diagnostic.safe_error(error)
        print("FAIL", current, report["error"], flush=True)
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
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
        name = type(error).__name__
        print(
            "Probe setup failed:",
            name if re.fullmatch(r"[A-Za-z]+", name) else "CLASS_ONLY",
            "; no external text logged",
            flush=True,
        )
        raise SystemExit(1) from None
