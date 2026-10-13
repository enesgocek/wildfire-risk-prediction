"""Pinned, offline V6 lineage snapshot; no credentials, raw reads or production writes."""

import hashlib
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

FINAL_SHA = "4bdaf1626e02194cd862e15a5bb4d7e500560b9661020720d892b42b0ca9031d"
WRAPPER_SHA = "3e68a8088e2af1b0b6d1e247c72b26caa066e45143f11b52b8bd634ca7a8320c"
SCOPE = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
CONTROLLER = "102c9e4ab16e4450d0d94eb3511dfdbf360fd6b6292809c5457efc93d2be5837"
REGISTRY = "6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d"
FOCUS = tuple(f"N20:2018164.{time}" for time in ("0018", "0024", "1000", "1142", "2218", "2224"))
SOURCE = re.compile(r"(?:VNP|VJ1)(?:03|14)IMG\.A\d{7}\.\d{4}\.\d{3}\.\d{13}\.nc")


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def boundary(path, owner):
    require(path.resolve().is_relative_to(owner.resolve()), "Source boundary")
    for part in (path, *path.parents):
        require(not part.is_symlink(), "Source symlink")
        if part == owner:
            return
    require(False, "Owner boundary")


def read(path, owner, limit=65536):
    boundary(path, owner)
    require(path.is_file() and 0 < path.stat().st_size <= limit, "Source byte bound")
    return path.read_bytes()


def pinned(package, filename, checksum):
    raw = read(package / filename, package, 2_000_000)
    require(sha(raw) == checksum, "Package manifest identity")
    for name, digest in json.loads(raw)["files"].items():
        require(Path(name).name == name and "\\" not in name, "Pinned package basename")
        require(sha(read(package / name, package, 20_000_000)) == digest, "Package member identity")
    return raw


def safe_failure(value, identity, selected):
    require(
        value.get("sample_id") == identity
        and value.get("child_kind") == "pair"
        and value.get("error_type") == "ValueError"
        and value.get("guard") == "Not the actual geolocation input",
        "Reviewed child failure identity",
    )
    result = {
        "sample_id": identity,
        "error_type": "ValueError",
        "guard": "Not the actual geolocation input",
    }
    if value.get("header_detail") == "UNAVAILABLE":
        result["header_detail"] = "UNAVAILABLE"
        return result
    declared = value.get("declared_geolocation_filenames")
    require(
        isinstance(declared, list)
        and len(declared) <= 10
        and all(isinstance(name, str) and SOURCE.fullmatch(name) for name in declared)
        and value.get("selected_geolocation_filename") == selected,
        "Public lineage filename boundary",
    )
    result.update(declared_geolocation_filenames=declared, selected_geolocation_filename=selected)
    return result


def snapshot(home):
    work = home / "wildfire-gcp-production-v1"
    protected = {}

    def remember(path, owner, limit=65536):
        raw = read(path, owner, limit)
        protected[path] = (owner, limit, sha(raw))
        return raw

    finals = [
        remember(work / name, work)
        for name in ("progress.json", "acceleration_run_summary.json", "continuation_summary.json")
    ]
    require(all(sha(raw) == FINAL_SHA for raw in finals), "Exact reviewed final snapshots")
    state = json.loads(finals[0])
    require(
        state["status"] == "failed_checkpoints_retained"
        and state["failed_month"] == "2018-06"
        and state["failed_phase"] == "pair_publication"
        and state["continuation_wrapper_sha256"] == WRAPPER_SHA
        and state["queue_manifest_sha256"] == SCOPE
        and state["controller_manifest_sha256"] == CONTROLLER
        and state["source_block_registry_sha256"] == REGISTRY
        and state["negative_label_permitted"] is False
        and state["daily_observation_status"] == "unknown"
        and state["full_training_complete"] is False
        and len(state["existing_months"]) == 65,
        "Reviewed failure policy",
    )
    require(
        sha(remember(home / "run_gcp_source_aware_continuation_v6.py", home, 200000))
        == WRAPPER_SHA,
        "V6 wrapper identity",
    )
    require(sha(remember(home / "source_blocks.json", home)) == REGISTRY, "Source block identity")
    for folder, filename, digest in (
        ("wildfire-gcp-production-package", "production_manifest.json", SCOPE),
        ("wildfire-gcp-acceleration-package", "acceleration_manifest.json", CONTROLLER),
    ):
        package = home / folder
        pinned(package, filename, digest)
        remember(package / filename, package, 2_000_000)
    plan_raw = remember(work / "months/2018-06/metadata/month.json", work, 2_000_000)
    plan = json.loads(plan_raw)
    require(
        plan["month"] == "2018-06" and plan["negative_label_permitted"] is False,
        "Month plan identity",
    )
    pairs = {pair["sample_id"]: pair for pair in plan["pairs"]}
    require(
        len(pairs) == len(plan["pairs"]) <= 1000 and set(FOCUS) <= set(pairs), "Pair population"
    )
    rows = []
    for identity in FOCUS:
        pair = pairs[identity]
        require(pair["stem"] == "l2_sample_" + identity.replace(":", "_"), "Pair stem")
        root = work / "months/2018-06/accelerated_run/tasks" / sha(identity.encode())
        failure = json.loads(remember(root / "continuation_failure.json", work))
        sources = pair["sources"]
        require(
            len(sources) == 2 and {s["role"] for s in sources} == {"fire", "geolocation"},
            "Source roles",
        )
        selected = next(s["filename"] for s in sources if s["role"] == "geolocation")
        row = safe_failure(failure, identity, selected)
        row["raw_source_stats"] = []
        for source in sources:
            name = source["filename"]
            require(isinstance(name, str) and SOURCE.fullmatch(name), "Public source basename")
            require(
                type(source["bytes"]) is int and 0 < source["bytes"] < 2**31, "Source size bound"
            )
            raw = root / "summer/raw" / pair["stem"] / name
            boundary(raw, work)
            row["raw_source_stats"].append(
                {
                    "role": source["role"],
                    "filename": name,
                    "expected_bytes": source["bytes"],
                    "present": raw.is_file(),
                    "actual_bytes": raw.stat().st_size if raw.is_file() else None,
                }
            )
        rows.append(row)
    require(
        all(
            sha(read(path, owner, limit)) == digest
            for path, (owner, limit, digest) in protected.items()
        ),
        "Protected evidence changed",
    )
    return {
        "protocol": "gcp_v6_geolocation_snapshot_v1",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "reviewed_final_sha256": FINAL_SHA,
        "wrapper_sha256": WRAPPER_SHA,
        "source_registry_sha256": REGISTRY,
        "month_plan_sha256": sha(plan_raw),
        "complete_month_count": 65,
        "failures": rows,
        "protected_file_sha256": {
            str(path.relative_to(home)).replace("\\", "/"): entry[2]
            for path, entry in protected.items()
        },
        "protected_files_unchanged": True,
        "credentials_read": False,
        "raw_source_contents_read": False,
        "network_requests": 0,
        "production_writes": 0,
    }


def main():
    import fcntl

    require(sys.platform == "linux", "Linux snapshot environment")
    home = Path.home()
    lock = home / "wildfire-gcp-production-v1/job.lock"
    boundary(lock, home)
    require(lock.is_file(), "Existing production lock")
    with lock.open("r") as stream:
        fcntl.flock(stream, fcntl.LOCK_SH | fcntl.LOCK_NB)
        result = snapshot(home)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    target = home / f"gcp_v6_geolocation_snapshot_{stamp}.json"
    with target.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("Snapshot collected; source failures:", len(result["failures"]))
    print("Download:", target)
    print("Stop VM after downloading; no production started.")


if __name__ == "__main__":
    os.umask(0o077)
    sys.dont_write_bytecode = True
    try:
        main()
    except Exception as error:
        print("Snapshot failed:", type(error).__name__, "; no external text logged")
        raise SystemExit(1) from None
