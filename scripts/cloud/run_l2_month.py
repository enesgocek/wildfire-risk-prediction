"""Approved July 2023 diagnostics, 264 new pairs and verified July-16 bootstrap.

Pair journals keep full geometry for recovery/audit. Daily compact results use
spatial unions, never area sums. No final labels; no automatic runtime restart.
"""

import argparse
import importlib.util
import json
import math
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "month_compact", Path(__file__).with_name("l2_daily_compact.py")
)
compact = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compact)
summer = compact.summer
require, digest, atomic_json = summer.require, summer.digest, summer.atomic_json
DAYS = [f"2023-07-{n:02d}" for n in range(1, 32)]
STORE = Path("/content/drive/MyDrive/wildfire-risk-prediction/colab_checkpoints/month_2023_07")


def configure(day):
    summer.ROOT = ROOT
    summer.OUTPUT = ROOT / "month/work" / day / "results"
    summer.OUTPUT.mkdir(parents=True, exist_ok=True)
    return summer.OUTPUT


def manifest_read():
    path = ROOT / "month/manifest.json"
    manifest = json.loads(path.read_text())
    require(manifest["scope"] == "2023-07" and manifest["days"] == DAYS, "Unapproved month")
    require(manifest["negative_label_permitted"] is False, "Labels forbidden")
    require(len(manifest["pairs"]) == 264, "Expected 264 new pairs")
    for name, checksum in manifest["bundle_files"].items():
        target = (ROOT / name).resolve()
        require(target.is_relative_to(ROOT.resolve()), "Bundle path escapes root")
        require(digest(target) == checksum, f"Bundle changed: {name}")
    catalog = pd.read_csv(ROOT / "month/catalogue_new.csv", dtype={"pair_key": str})
    require(
        len(catalog) == 528 and not catalog.duplicated(["sensor", "pair_key", "role"]).any(),
        "New catalogue",
    )
    require(
        set(catalog.sensor + ":" + catalog.pair_key) == {p["sample_id"] for p in manifest["pairs"]},
        "Pair set",
    )
    require(len({p["sample_id"] for p in manifest["pairs"]}) == 264, "Duplicate pair")
    for pair in manifest["pairs"]:
        day = pair["start_utc"][:10]
        require(day in DAYS and day != "2023-07-16", "Bootstrap must not be redownloaded")
        require(
            pair["sample_id"] == f"{pair['sensor']}:{pair['key']}"
            and pair["stem"] == summer.audit.sample_stem(pair["sensor"], pair["key"]),
            "Pair identity",
        )
        require(
            len(pair["sources"]) == 2
            and {s["role"] for s in pair["sources"]} == {"fire", "geolocation"},
            "Pair roles",
        )
        for source in pair["sources"]:
            url = urlsplit(source["url"])
            require(
                url.scheme == "https"
                and url.hostname in summer.base.pilot.DATA_HOSTS
                and url.path.rsplit("/", 1)[-1] == source["filename"],
                "Expected NASA data host/filename",
            )
            require(
                summer.audit.product_identity(source["filename"])[:3]
                == (pair["sensor"], source["role"], pair["key"]),
                "Training source identity",
            )
            row = catalog.loc[catalog.filename.eq(source["filename"])]
            require(
                len(row) == 1 and row.iloc[0].data_url == source["url"], "Source catalog identity"
            )
            require(
                source["bytes"] > 0
                and digest(ROOT / pair["metadata"][source["role"]]) == source["metadata_sha256"],
                "Source metadata",
            )
    require(
        digest(ROOT / "month/bootstrap_results.zip") == manifest["bootstrap_results_sha256"],
        "Bootstrap changed",
    )
    require(
        sum(s["bytes"] for p in manifest["pairs"] for s in p["sources"])
        == manifest["new_source_bytes"],
        "Source total differs",
    )
    return manifest, digest(path)


def context(manifest_sha, day):
    return {
        "month_manifest_sha256": manifest_sha,
        "month_worker_sha256": digest(Path(__file__)),
        "source_kind": "verified_B_bootstrap" if day == "2023-07-16" else "new_month_day",
    }


def check_budget(store, manifest_sha, budget_bytes, addition):
    require(
        isinstance(budget_bytes, int) and budget_bytes > 0 and addition >= 0,
        "Invalid storage budget",
    )
    total = 0
    for kind in ("pairs", "days"):
        folder = store.resolve() / kind / manifest_sha
        for path in folder.glob("*"):
            require(path.resolve().is_relative_to(folder.resolve()), "Store path escapes job")
            if path.is_file():
                total += path.stat().st_size
    require(total + addition <= budget_bytes, "Selected job storage budget exceeded; raw kept")
    return total


def save_day(day, output, store, manifest_sha, pairs, budget_bytes):
    report = compact.validate_day(
        output, day, [p["sample_id"] for p in pairs], context(manifest_sha, day)
    )
    local = ROOT / "month" / f"day_{day}.zip"
    with zipfile.ZipFile(local, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in compact.NAMES:
            archive.write(output / name, name)
    checksum = digest(local)
    folder = store.resolve() / "days" / manifest_sha
    folder.mkdir(parents=True, exist_ok=True)
    basename = f"day_{day}_{checksum}"
    payload = folder / f"{basename}.zip"
    check_budget(
        store, manifest_sha, budget_bytes, 65536 + (0 if payload.exists() else local.stat().st_size)
    )
    summer.storage.copy_verified(summer.base, local, payload, checksum)
    with tempfile.TemporaryDirectory(dir=ROOT) as directory:
        restore_day_zip(payload, Path(directory), day, pairs, context(manifest_sha, day))
    record = {
        "protocol": "month_daily_v1",
        "manifest_sha256": manifest_sha,
        "worker_sha256": digest(Path(__file__)),
        "day": day,
        "payload_name": payload.name,
        "payload_sha256": checksum,
        "payload_bytes": payload.stat().st_size,
        "pair_ids": report["pair_ids"],
        "negative_label_permitted": False,
    }
    marker = folder / f"{basename}.commit.json"
    if marker.exists():
        require(json.loads(marker.read_text()) == record, "Day commit differs")
    else:
        atomic_json(marker, record)
    require(json.loads(marker.read_text()) == record, "Day commit readback")
    return record


def restore_day_zip(payload, output, day, pairs, lineage):
    with zipfile.ZipFile(payload) as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        require(
            len(names) == len(set(names)) and set(names) == set(compact.NAMES),
            "Unexpected daily ZIP",
        )
        require(
            all(0 < i.file_size < 100_000_000 for i in infos)
            and sum(i.file_size for i in infos) < 250_000_000,
            "Daily ZIP size",
        )
        require(archive.testzip() is None, "Daily ZIP CRC")
        output.mkdir(parents=True, exist_ok=True)
        for name in names:
            target = output / name
            data = archive.read(name)
            if target.exists():
                require(target.read_bytes() == data, "Existing daily result differs")
            else:
                target.write_bytes(data)
    return compact.validate_day(output, day, [p["sample_id"] for p in pairs], lineage)


def restore_day(day, pairs, store, manifest_sha, output):
    folder = store.resolve() / "days" / manifest_sha
    markers = list(folder.glob(f"day_{day}_*.commit.json"))
    require(len(markers) <= 1, "Multiple day commits; review required")
    if not markers:
        return None
    record = json.loads(markers[0].read_text())
    checksum = record["payload_sha256"]
    require(len(checksum) == 64 and all(c in "0123456789abcdef" for c in checksum), "Day SHA")
    basename = f"day_{day}_{checksum}"
    require(
        markers[0].name == f"{basename}.commit.json"
        and record["payload_name"] == f"{basename}.zip",
        "Day filename",
    )
    require(
        record["manifest_sha256"] == manifest_sha
        and record["worker_sha256"] == digest(Path(__file__))
        and record["day"] == day
        and record["protocol"] == "month_daily_v1"
        and record["negative_label_permitted"] is False,
        "Day commit identity",
    )
    require(set(record["pair_ids"]) == {p["sample_id"] for p in pairs}, "Committed day pairs")
    payload = folder / record["payload_name"]
    require(
        payload.stat().st_size == record["payload_bytes"] and digest(payload) == checksum,
        "Day payload changed",
    )
    restore_day_zip(payload, output, day, pairs, context(manifest_sha, day))
    return record


def bootstrap(manifest):
    source = json.loads((ROOT / "month/bootstrap_manifest.json").read_text())
    require(source["day"] == "2023-07-16" and len(source["pairs"]) == 6, "Bootstrap scope")
    output = configure("2023-07-16")
    with zipfile.ZipFile(ROOT / "month/bootstrap_results.zip") as archive:
        expected = {"summer_summary.json"} | {
            f"{p['stem']}_{s}"
            for p in source["pairs"]
            for s in (*summer.SUFFIXES, "checkpoint.json")
        }
        require(
            set(archive.namelist()) == expected and len(archive.namelist()) == len(expected),
            "Bootstrap members",
        )
        require(archive.testzip() is None, "Bootstrap CRC")
        for name in expected:
            target = output / name
            data = archive.read(name)
            if target.exists():
                require(target.read_bytes() == data, "Existing bootstrap output changed")
            else:
                target.write_bytes(data)
    old_sha = digest(ROOT / "month/bootstrap_manifest.json")
    for pair in source["pairs"]:
        require(
            summer.checkpoint_read(pair, output, old_sha) is not None,
            "Incomplete verified bootstrap",
        )
    return source["pairs"], output


def save_pair(pair, output, store, manifest_sha, budget_bytes):
    # Upper bound for new compressed journal: uncompressed validated files plus ZIP overhead.
    size = sum(
        (output / f"{pair['stem']}_{s}").stat().st_size
        for s in (*summer.SUFFIXES, "checkpoint.json")
    )
    check_budget(store, manifest_sha, budget_bytes, size + 65536)
    summer.OUTPUT = output
    return summer.save_pair(pair, store / "pairs", manifest_sha)


def validate_cloud(store):
    require(
        platform.system() == "Linux"
        and ROOT.resolve() == Path("/content/wildfire_l2_month_202307")
        and store.resolve() == STORE
        and Path("/content/drive/MyDrive").is_dir(),
        "Expected monthly Colab/Drive paths",
    )


def clean_work(day, pairs, inputs):
    # Only listed local intermediate files, after daily commit. No Drive deletion.
    require(
        inputs.resolve().is_relative_to((ROOT / "month/work").resolve()),
        "Cleanup outside month work",
    )
    for pair in pairs:
        for suffix in (*summer.SUFFIXES, "checkpoint.json", "memory.json"):
            target = inputs / f"{pair['stem']}_{suffix}"
            if target.exists():
                require(
                    target.resolve().is_relative_to(inputs.resolve()), "Work path escapes directory"
                )
                target.unlink()
        local = inputs.parent / f"{pair['stem']}.zip"
        if local.exists():
            require(
                local.resolve().is_relative_to((ROOT / "month/work").resolve()), "Local ZIP path"
            )
            local.unlink()


def export_summary(manifest, manifest_sha, records):
    summary = {
        "scope": "2023-07",
        "status": "complete_month_diagnostics" if len(records) == 31 else "partial",
        "completed_days": len(records),
        "days_expected": 31,
        "new_pairs_expected": 264,
        "manifest_sha256": manifest_sha,
        "worker_sha256": digest(Path(__file__)),
        "daily_commits": records,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "bootstrap_not_redownloaded": True,
        "new_source_bytes": manifest["new_source_bytes"],
    }
    atomic_json(ROOT / "month/month_summary.json", summary)
    archive_path = ROOT / "l2_month_2023_07_results.zip"
    with zipfile.ZipFile(
        archive_path.with_suffix(".zip.tmp"), "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        archive.write(ROOT / "month/month_summary.json", "month_summary.json")
        for record in records:
            for name in compact.NAMES:
                archive.write(
                    ROOT / "month/daily" / record["day"] / name, f"{record['day']}/{name}"
                )
    archive_path.with_suffix(".zip.tmp").replace(archive_path)
    print(
        f"Month progress: {len(records)}/31 days; "
        f"compact ZIP {archive_path.stat().st_size / 1e6:.2f} MB",
        flush=True,
    )


def run(store, budget_bytes, verify_only=False, stop_after=None):
    manifest, manifest_sha = manifest_read()
    validate_cloud(store)
    records = []
    b = json.loads((ROOT / "month/bootstrap_manifest.json").read_text())
    # Bootstrap is first: the approved original day is reused, never redownloaded.
    order = ["2023-07-16", *[d for d in DAYS if d != "2023-07-16"]]
    processed = 0
    for day in order:
        pairs = (
            b["pairs"]
            if day == "2023-07-16"
            else [p for p in manifest["pairs"] if p["start_utc"].startswith(day)]
        )
        output = ROOT / "month/daily" / day
        record = restore_day(day, pairs, store, manifest_sha, output)
        if record is None:
            require(not verify_only, f"Day incomplete: {day}")
            if day == "2023-07-16":
                pairs, inputs = bootstrap(manifest)
            else:
                inputs = configure(day)
                for pair in pairs:
                    print(f"Processing {day}: {pair['sample_id']}", flush=True)
                    recovered = summer.restore_store(pair, store / "pairs", manifest_sha)
                    existing = summer.checkpoint_read(pair, inputs, manifest_sha)
                    raw = ROOT / "summer/raw" / pair["stem"]
                    if existing is None:
                        started = time.perf_counter()
                        with summer.base.DiskSampler(ROOT) as disk:
                            require(
                                shutil.disk_usage(ROOT).free
                                > sum(s["bytes"] for s in pair["sources"]) + 3 * 2**30,
                                "Source size plus 3 GiB scratch required",
                            )
                            # Only incomplete-size copies in this job's scratch may be retried.
                            raw.mkdir(parents=True, exist_ok=True)
                            for source in pair["sources"]:
                                target = raw / source["filename"]
                                if target.exists() and target.stat().st_size != source["bytes"]:
                                    require(
                                        target.resolve().is_relative_to(
                                            (ROOT / "summer/raw").resolve()
                                        ),
                                        "Partial scratch path",
                                    )
                                    target.unlink()
                            transferred = summer.download_pair(pair, raw)
                            subprocess.run(
                                [
                                    sys.executable,
                                    str(Path(__file__)),
                                    "--child",
                                    pair["sample_id"],
                                    "--source-directory",
                                    str(raw),
                                ],
                                check=True,
                            )
                            summer.compare_pair(pair, inputs)
                        memory = json.loads((inputs / f"{pair['stem']}_memory.json").read_text())
                        require(memory["child_peak_rss_bytes"] > 0, "Memory metric")
                        existing = {
                            "sample_id": pair["sample_id"],
                            "manifest_sha256": manifest_sha,
                            "worker_sha256": digest(Path(summer.__file__)),
                            "outputs": {
                                f"{pair['stem']}_{s}": digest(inputs / f"{pair['stem']}_{s}")
                                for s in summer.SUFFIXES
                            },
                            "metrics": {
                                "elapsed_seconds": time.perf_counter() - started,
                                "downloaded_payload_bytes": transferred,
                                "pair_source_bytes": sum(s["bytes"] for s in pair["sources"]),
                                **memory,
                                "sampled_disk_increase_bytes": disk.before - disk.minimum,
                            },
                        }
                        atomic_json(inputs / f"{pair['stem']}_checkpoint.json", existing)
                    if not recovered:
                        save_pair(pair, inputs, store, manifest_sha, budget_bytes)
                    summer.cleanup_pair(pair, raw)
            compact.reduce_day(
                day, pairs, inputs, output, context(manifest_sha, day), verify_geometry=False
            )
            record = save_day(day, output, store, manifest_sha, pairs, budget_bytes)
            clean_work(day, pairs, inputs)
            processed += 1
        records.append(record)
        export_summary(manifest, manifest_sha, records)
        if stop_after is not None and processed >= stop_after:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-root", type=Path)
    parser.add_argument("--budget-gb", type=float, default=20.0)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--stop-after-days", type=int, choices=range(1, 32))
    parser.add_argument("--child")
    parser.add_argument("--source-directory", type=Path)
    args = parser.parse_args()
    if args.child:
        manifest, _ = manifest_read()
        matches = [p for p in manifest["pairs"] if p["sample_id"] == args.child]
        require(len(matches) == 1 and args.source_directory is not None, "Invalid month child")
        pair = matches[0]
        configure(pair["start_utc"][:10])
        require(
            args.source_directory.resolve() == (ROOT / "summer/raw" / pair["stem"]).resolve(),
            "Child scratch path",
        )
        summer.child_audit(pair, args.source_directory)
    else:
        require(
            args.store_root is not None
            and math.isfinite(args.budget_gb)
            and 0 < args.budget_gb <= 20,
            "Store and 0–20 GB job budget required",
        )
        run(args.store_root, round(args.budget_gb * 1e9), args.verify_only, args.stop_after_days)
