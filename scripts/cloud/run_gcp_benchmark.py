"""Bounded one/two-worker comparison using the unchanged six-swath summer code.

Each process has its own extracted science bundle. Sources are downloaded again
in each arm; no cached work counts as a speed measurement. No VM/billing changes.
"""

import argparse
import concurrent.futures
import getpass
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

SUMMER_SHA = "0a90b93be0ed31fa468b6ecef61851612bcd255e34caf3ccdb6adf2d6d425f7e"
LIMIT_SECONDS = 2100
ARMS = (1, 2)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".json.pending")
    pending.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    pending.replace(path)


def clean_environment():
    env = os.environ.copy()
    for name in list(env):
        if name.startswith("EARTHDATA_") or name in {"PYTHONPATH", "PYTHONHOME"}:
            env.pop(name)
    env["PYTHONNOUSERSITE"] = "1"
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "GDAL_NUM_THREADS"):
        env[name] = "1"
    return env


def unpack(bundle, destination):
    require(digest(bundle) == SUMMER_SHA, "Frozen summer bundle changed")
    require(not destination.is_symlink(), "Symlink work root")
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read("summer/manifest.json"))
        expected = set(manifest["bundle_files"]) | {"summer/manifest.json"}
        require(len(names) == len(expected) and set(names) == expected, "Bundle members")
        require(sum(i.file_size for i in archive.infolist()) < 15_000_000, "Bundle size")
        require(archive.testzip() is None, "Bundle CRC")
        for name in names:
            target = (destination / name).resolve()
            require(target.is_relative_to(destination.resolve()), "Bundle path escapes root")
            target.parent.mkdir(parents=True, exist_ok=True)
            data = archive.read(name)
            if target.exists():
                require(target.read_bytes() == data, "Existing bundle file changed")
            else:
                target.write_bytes(data)
            if name in manifest["bundle_files"]:
                require(digest(target) == manifest["bundle_files"][name], "Science code changed")
    return manifest


def load_summer(root):
    path = root / "scripts/cloud/run_l2_summer.py"
    spec = importlib.util.spec_from_file_location("gcp_frozen_summer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def child(package, root, sample_id):
    spec = package_spec(package)
    unpack(package / "summer.zip", root)
    summer = load_summer(root)
    manifest, manifest_sha = summer.manifest_read()
    selected = [p for p in manifest["pairs"] if p["sample_id"] == sample_id]
    require(len(selected) == 1, "Unapproved pair")
    pair = selected[0]
    require(not summer.OUTPUT.exists(), "Cached pair would invalidate benchmark")
    summer.OUTPUT.mkdir(parents=True)
    raw = root / "summer/raw" / pair["stem"]
    started = time.perf_counter()
    transferred = summer.download_pair(pair, raw)
    require(transferred == sum(s["bytes"] for s in pair["sources"]), "Cold download required")
    summer.child_audit(pair, raw)
    summer.compare_pair(pair, summer.OUTPUT)
    report = json.loads((summer.OUTPUT / f"{pair['stem']}_audit.json").read_text())
    for role, expected in spec["source_sha256"][sample_id].items():
        require(report["sources"][role]["sha256"] == expected, "Source differs from Colab proof")
    for suffix, expected in spec["exact_csv_sha256"][sample_id].items():
        require(
            digest(summer.OUTPUT / f"{pair['stem']}_{suffix}") == expected, "Native CSV changed"
        )
    memory = json.loads((summer.OUTPUT / f"{pair['stem']}_memory.json").read_text())
    require(memory["child_peak_rss_bytes"] > 0, "Linux peak RSS absent")
    record = {
        "sample_id": sample_id,
        "manifest_sha256": manifest_sha,
        "worker_sha256": digest(Path(summer.__file__)),
        "outputs": {
            f"{pair['stem']}_{s}": digest(summer.OUTPUT / f"{pair['stem']}_{s}")
            for s in summer.SUFFIXES
        },
        "metrics": {
            "elapsed_seconds": time.perf_counter() - started,
            "downloaded_payload_bytes": transferred,
            "pair_source_bytes": transferred,
            **memory,
            # Legacy field: disk sampling is not enabled in this benchmark.
            "sampled_disk_increase_bytes": 0,
            "disk_sampling_enabled": False,
        },
    }
    atomic_json(summer.OUTPUT / f"{pair['stem']}_checkpoint.json", record)
    require(summer.checkpoint_read(pair, summer.OUTPUT, manifest_sha) == record, "Readback failed")
    # Only this isolated VM scratch pair is removed, after complete checked outputs.
    summer.cleanup_pair(pair, raw)
    print(f"Pair verified: {sample_id}", flush=True)


def package_spec(package):
    spec = json.loads((package / "benchmark_manifest.json").read_text())
    require(spec["protocol"] == "gcp_summer_two_arm_v1", "Protocol")
    require(spec["arms"] == list(ARMS) and spec["negative_label_permitted"] is False, "Scope")
    require(
        set(spec["files"]) == {"summer.zip", "requirements.txt", "run_gcp_benchmark.py"}, "Files"
    )
    for name, checksum in spec["files"].items():
        path = (package / name).resolve()
        require(
            path.is_relative_to(package.resolve()) and digest(path) == checksum, "Package changed"
        )
    require(digest(Path(__file__)) == spec["files"]["run_gcp_benchmark.py"], "Runner identity")
    require(spec["files"]["summer.zip"] == SUMMER_SHA, "Summer identity")
    return spec


def execute_arm(pairs, workers, task, deadline):
    require(workers in ARMS, "Worker count")
    start = time.perf_counter()
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(task, pair, deadline) for pair in pairs]
        try:
            for future in concurrent.futures.as_completed(
                futures, timeout=max(0.1, deadline - start)
            ):
                records.append(future.result())
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    return records, time.perf_counter() - start


def run(package, work):
    require(
        platform.system() == "Linux" and platform.machine() == "x86_64", "Linux x86_64 required"
    )
    require(
        sys.version_info[:2] == (3, 12) and sys.prefix != sys.base_prefix,
        "Use established Python 3.12 venv",
    )
    spec = package_spec(package)
    # Conservative boot-age gate; NOT a read of Google's exact termination time.
    uptime = float(Path("/proc/uptime").read_text().split()[0])
    require(uptime < 4200, "VM boot age exceeds 70 minutes; stop and review remaining runtime")
    require(
        not work.is_symlink() and not work.resolve().is_relative_to(package.resolve()), "Work path"
    )
    require(not work.exists(), "Benchmark directory already exists; do not reuse for timing")
    require(shutil.disk_usage(work.parent).free > 5 * 2**30, "Need 5 GiB headroom")
    for line in (package / "requirements.txt").read_text().splitlines():
        if line and not line.startswith("#"):
            name, version = line.split("==")
            require(importlib.metadata.version(name) == version, f"Pinned version differs: {name}")
    subprocess.run([sys.executable, "-m", "pip", "check"], check=True, timeout=60)
    work.mkdir()
    atomic_json(
        work / "started.json",
        {
            "protocol": spec["protocol"],
            "boot_age_seconds": uptime,
            "negative_label_permitted": False,
        },
    )
    env = clean_environment()
    arms = []
    try:
        env["EARTHDATA_USERNAME"] = getpass.getpass("Earthdata kullanici adi (gizli): ")
        env["EARTHDATA_PASSWORD"] = getpass.getpass("Earthdata parola (gizli): ")
        deadline = time.perf_counter() + LIMIT_SECONDS
        for workers in ARMS:
            arm_root = work / f"workers_{workers}"
            manifest = unpack(package / "summer.zip", arm_root / "aggregate")
            pairs = manifest["pairs"]
            require(
                len(pairs) == 6 and set(spec["source_sha256"]) == {p["sample_id"] for p in pairs},
                "Six pairs",
            )

            def task(pair, until, arm_root=arm_root, workers=workers):
                remaining = until - time.perf_counter()
                require(remaining > 0, "Benchmark deadline reached")
                root = arm_root / pair["stem"]
                root.mkdir(parents=True)
                with (root / "run.log").open("w", encoding="utf-8") as log:
                    subprocess.run(
                        [
                            sys.executable,
                            str(Path(__file__)),
                            "--child",
                            pair["sample_id"],
                            "--child-root",
                            str(root),
                        ],
                        env=env,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        check=True,
                        timeout=min(900, remaining),
                    )
                print(f"{workers} worker: {pair['sample_id']} complete", flush=True)
                return pair["sample_id"]

            completed, seconds = execute_arm(pairs, workers, task, deadline)
            require(set(completed) == {p["sample_id"] for p in pairs}, "Incomplete arm")
            summer = load_summer(arm_root / "aggregate")
            native_manifest, manifest_sha = summer.manifest_read()
            summer.OUTPUT.mkdir(parents=True)
            for pair in pairs:
                source = arm_root / pair["stem"] / "summer/results"
                for suffix in (*summer.SUFFIXES, "checkpoint.json"):
                    name = f"{pair['stem']}_{suffix}"
                    shutil.copyfile(source / name, summer.OUTPUT / name)
                summer.checkpoint_read(pair, summer.OUTPUT, manifest_sha)
            summer.write_summary(native_manifest, manifest_sha, 6, 0)
            payload = summer.ROOT / "l2_summer_results.zip"
            with zipfile.ZipFile(payload) as archive:
                require(archive.testzip() is None, "Arm result CRC")
            arms.append(
                {
                    "workers": workers,
                    "cold_pair_wall_seconds": seconds,
                    "result_zip_sha256": digest(payload),
                    "result_zip_bytes": payload.stat().st_size,
                    "completed_pairs": 6,
                    "downloaded_payload_bytes": spec["source_bytes_per_arm"],
                    "maximum_child_peak_rss_bytes": max(
                        summer.checkpoint_read(p, summer.OUTPUT, manifest_sha)["metrics"][
                            "child_peak_rss_bytes"
                        ]
                        for p in pairs
                    ),
                }
            )
            atomic_json(
                work / "partial_summary.json",
                {"completed_arms": arms, "negative_label_permitted": False},
            )
        require(
            all(
                math.isfinite(a["cold_pair_wall_seconds"]) and a["cold_pair_wall_seconds"] > 0
                for a in arms
            ),
            "Timing",
        )
        report = {
            "status": "gcp_two_arm_benchmark_completed",
            "arms": arms,
            "speedup_two_vs_one": arms[0]["cold_pair_wall_seconds"]
            / arms[1]["cold_pair_wall_seconds"],
            "package_manifest_sha256": digest(package / "benchmark_manifest.json"),
            "cold_source_bytes_total": sum(a["downloaded_payload_bytes"] for a in arms),
            "negative_label_permitted": False,
            "full_years_processed": False,
            "limits": [
                "Six completed training swaths; duplicate benchmark, no new production months",
                "Fixed serial-then-two order; network/server cache variation may influence speed",
                "Wall time includes startup/download/audit/readback/cleanup; excludes aggregation",
                "Child RSS is per process, not simultaneous VM RAM; disk peak not sampled",
                "Boot age is not Google's exact scheduled stop time; original VM cap unchanged",
            ],
        }
        atomic_json(work / "gcp_benchmark_summary.json", report)
        target = work / "gcp_benchmark_results.zip"
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(work / "gcp_benchmark_summary.json", "gcp_benchmark_summary.json")
            for workers in ARMS:
                payload = work / f"workers_{workers}/aggregate/l2_summer_results.zip"
                archive.write(payload, f"workers_{workers}.zip")
        with zipfile.ZipFile(target) as archive:
            require(archive.testzip() is None, "Final ZIP CRC")
        print(json.dumps(report, indent=2))
        print(f"Download: {target}", flush=True)
    finally:
        env.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child")
    parser.add_argument("--child-root", type=Path)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    if args.child:
        require(args.child_root is not None, "Child root required")
        child(package, args.child_root, args.child)
    else:
        run(package, Path.home() / "wildfire-gcp-benchmark-work")
