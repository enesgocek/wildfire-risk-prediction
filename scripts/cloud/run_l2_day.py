"""Fixed two-sensor training day, one temporary pair at a time; no daily labels."""

import argparse
import importlib.metadata
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pilot = load("single_pilot", ROOT / "scripts/cloud/run_l2_pilot.py")
result_check = load("single_result", ROOT / "scripts/cloud/verify_l2_pilot_results.py")
require, digest = pilot.require, pilot.digest


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(path)


def manifest_read():
    path = ROOT / "day/manifest.json"
    manifest = json.loads(path.read_text())
    require(manifest["day"] == "2019-01-14", "Only the fixed training day is allowed")
    pairs = manifest["pairs"]
    require(len(pairs) == 8 and len({p["sample_id"] for p in pairs}) == 8, "Expected eight pairs")
    require({p["sensor"] for p in pairs} == {"SNPP", "N20"}, "Expected both sensors")
    for name, expected in manifest["bundle_files"].items():
        target = (ROOT / name).resolve()
        require(target.is_relative_to(ROOT.resolve()), "Bundle path escapes root")
        require(digest(target) == expected, f"Bundle changed: {name}")
    for pair in pairs:
        require(pair["key"].startswith("2019014."), "Wrong training date")
        require(len(pair["sources"]) == 2, "Expected fire/geolocation pair")
        for source in pair["sources"]:
            require(Path(source["filename"]).name == source["filename"], "Invalid filename")
    return manifest, digest(path)


def compare_pair(pair, output):
    stem = pair["stem"]
    expected = json.loads((ROOT / pair["reference_audit"]).read_text())
    actual = json.loads((output / f"{stem}_audit.json").read_text())
    require(
        result_check.normalized_audit(actual) == result_check.normalized_audit(expected),
        f"Full audit differs: {stem}",
    )
    for source in pair["sources"]:
        reported = actual["sources"][source["role"]]
        require(
            reported["sha256"] == source["sha256"] and reported["bytes"] == source["bytes"],
            "Source differs",
        )
    table = pd.read_csv(output / f"{stem}_grid_centers.csv").sort_values("grid_id")
    reference = pd.read_csv(ROOT / pair["reference_csv"]).sort_values("grid_id")
    pd.testing.assert_frame_equal(
        table.reset_index(drop=True), reference.reset_index(drop=True), check_exact=True
    )
    require(len(table) == 2899 and table.grid_id.is_unique, "Grid identity differs")
    require(actual["negative_label_permitted"] is False, "Labels forbidden")
    require(
        table.daily_observation_status.eq("unknown").all()
        and table.negative_label_permitted.eq(False).all(),
        "Daily labels/status changed",
    )


def checkpoint_read(pair, output, manifest_sha):
    path = output / f"{pair['stem']}_checkpoint.json"
    if not path.exists():
        return None
    record = json.loads(path.read_text())
    require(record["manifest_sha256"] == manifest_sha, "Checkpoint manifest differs")
    require(record["worker_sha256"] == digest(Path(__file__)), "Checkpoint worker differs")
    require(record["sample_id"] == pair["sample_id"], "Checkpoint pair differs")
    expected_names = {f"{pair['stem']}_audit.json", f"{pair['stem']}_grid_centers.csv"}
    require(set(record["outputs"]) == expected_names, "Checkpoint output list differs")
    for name, expected_sha in record["outputs"].items():
        require(digest(output / name) == expected_sha, "Completed output changed")
    compare_pair(pair, output)
    return record


def export_results(manifest, manifest_sha, output):
    destination = ROOT / "l2_day_results.zip"
    temporary = destination.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for pair in manifest["pairs"]:
            record = checkpoint_read(pair, output, manifest_sha)
            if record is not None:
                for name in [*record["outputs"], f"{pair['stem']}_checkpoint.json"]:
                    archive.write(output / name, name)
        if (output / "day_summary.json").exists():
            archive.write(output / "day_summary.json", "day_summary.json")
    temporary.replace(destination)


def restore_results(path, manifest, manifest_sha, output):
    allowed = {"day_summary.json"}
    for pair in manifest["pairs"]:
        allowed.update(
            f"{pair['stem']}_{suffix}"
            for suffix in ("audit.json", "grid_centers.csv", "checkpoint.json")
        )
    with zipfile.ZipFile(path) as archive, tempfile.TemporaryDirectory(dir=ROOT) as staging:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        require(len(names) == len(set(names)) and set(names) <= allowed, "Unexpected ZIP members")
        require(all(0 < i.file_size < 2_000_000 for i in infos), "Unexpected result size")
        require(archive.testzip() is None, "Result CRC failed")
        staged = Path(staging)
        for name in names:
            (staged / name).write_bytes(archive.read(name))
        complete_names = {"day_summary.json"} & set(names)
        for pair in manifest["pairs"]:
            record = checkpoint_read(pair, staged, manifest_sha)
            if record is not None:
                complete_names.update(record["outputs"])
                complete_names.add(f"{pair['stem']}_checkpoint.json")
        require(set(names) == complete_names, "Uncheckpointed outputs in ZIP")
        output.mkdir(parents=True, exist_ok=True)
        for name in names:
            target = output / name
            if target.exists():
                require(digest(target) == digest(staged / name), "Existing result differs")
            else:
                shutil.copyfile(staged / name, target)


class DiskSampler:
    """Sample free filesystem space, including downloads/child I/O, every 0.2 s."""

    def __init__(self, root):
        self.root = root
        self.before = self.minimum = shutil.disk_usage(root).free
        self.samples = 0
        self.done = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def sample(self):
        self.minimum = min(self.minimum, shutil.disk_usage(self.root).free)
        self.samples += 1

    def loop(self):
        while not self.done.wait(0.2):
            self.sample()

    def __enter__(self):
        self.sample()
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.done.set()
        self.thread.join()
        self.sample()


def source_check(source, path):
    require(
        path.stat().st_size == source["bytes"] and digest(path) == source["sha256"],
        "Source identity mismatch",
    )


def download_pair(pair, directory):
    directory.mkdir(parents=True, exist_ok=True)
    staging = directory / "staging"
    staging.mkdir(exist_ok=True)
    missing = []
    for source in pair["sources"]:
        target = directory / source["filename"]
        if target.exists():
            source_check(source, target)
            continue
        temporary = staging / source["filename"]
        if temporary.exists() and (
            temporary.stat().st_size != source["bytes"] or digest(temporary) != source["sha256"]
        ):
            # Only the fixed cloud staging copy can be discarded and retried.
            require(
                temporary.resolve().is_relative_to((ROOT / "day/raw").resolve()),
                "Staging path outside cloud scratch",
            )
            temporary.unlink()
        missing.append(source)
    transferred = 0
    if missing:
        transferred = pilot.download_sources({"sources": missing}, staging, "environment")
        for source in missing:
            temporary = staging / source["filename"]
            source_check(source, temporary)
            temporary.replace(directory / source["filename"])
    return transferred


def cleanup_pair(pair, directory):
    scratch = (ROOT / "day/raw").resolve()
    require(directory.resolve().is_relative_to(scratch), "Cleanup outside cloud scratch")
    # No recursive removal; never remove reference/local inputs or unlisted files.
    for source in pair["sources"]:
        path = directory / source["filename"]
        if path.exists():
            require(path.resolve().is_relative_to(scratch), "Source escapes scratch")
            source_check(source, path)
            path.unlink()


def child_audit(pair, directory, output):
    inspector = load("day_inspector", ROOT / "scripts/firms/inspect_l2_observation_sample.py")
    inspector.OUTPUT = output
    inspector.inspect(
        directory, ROOT / pair["metadata"]["fire"], ROOT / pair["metadata"]["geolocation"]
    )
    peak = None
    if platform.system() == "Linux":
        import resource

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    atomic_json(output / f"{pair['stem']}_memory.json", {"child_peak_rss_bytes": peak})


def run(local_files=None, stop_after=None, restore=None):
    manifest, manifest_sha = manifest_read()
    output = ROOT / "day/results"
    output.mkdir(parents=True, exist_ok=True)
    if restore:
        restore_results(restore, manifest, manifest_sha, output)
    records, processed, reused = [], 0, 0
    for pair in manifest["pairs"]:
        raw = ROOT / "day/raw" / pair["stem"]
        record = checkpoint_read(pair, output, manifest_sha)
        if record is not None:
            records.append(record)
            reused += 1
            if local_files is None:
                cleanup_pair(pair, raw)
            print(
                f"Verified checkpoint; skipped download/processing: {pair['sample_id']}", flush=True
            )
            continue
        directory = raw if local_files is None else local_files / pair["local_directory"]
        start = time.perf_counter()
        with DiskSampler(ROOT) as disk:
            require(
                shutil.disk_usage(ROOT).free > sum(s["bytes"] for s in pair["sources"]) + 2 * 2**30,
                "Insufficient disk headroom",
            )
            transferred = 0 if local_files else download_pair(pair, directory)
            for source in pair["sources"]:
                source_check(source, directory / source["filename"])
            subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__)),
                    "--child",
                    pair["sample_id"],
                    "--source-directory",
                    str(directory),
                ],
                check=True,
            )
            compare_pair(pair, output)
        memory_path = output / f"{pair['stem']}_memory.json"
        memory = json.loads(memory_path.read_text())
        require(
            platform.system() != "Linux" or memory["child_peak_rss_bytes"] > 0,
            "Missing Linux memory measurement",
        )
        record = {
            "sample_id": pair["sample_id"],
            "manifest_sha256": manifest_sha,
            "worker_sha256": digest(Path(__file__)),
            "outputs": {
                f"{pair['stem']}_{suffix}": digest(output / f"{pair['stem']}_{suffix}")
                for suffix in ("audit.json", "grid_centers.csv")
            },
            "metrics": {
                "elapsed_seconds": time.perf_counter() - start,
                "downloaded_payload_bytes": transferred,
                "pair_source_bytes": sum(s["bytes"] for s in pair["sources"]),
                "child_peak_rss_bytes": memory["child_peak_rss_bytes"],
                "free_disk_before_bytes": disk.before,
                "minimum_sampled_free_disk_bytes": disk.minimum,
                "sampled_disk_increase_bytes": disk.before - disk.minimum,
                "disk_samples": disk.samples,
            },
        }
        atomic_json(output / f"{pair['stem']}_checkpoint.json", record)
        records.append(record)
        processed += 1
        write_summary(manifest, manifest_sha, records, processed, reused, local_files, output)
        export_results(manifest, manifest_sha, output)
        if local_files is None:
            cleanup_pair(pair, raw)
        memory_path.unlink()
        print(f"Verified and checkpointed: {pair['sample_id']}", flush=True)
        if stop_after is not None and processed >= stop_after:
            break
    write_summary(manifest, manifest_sha, records, processed, reused, local_files, output)
    export_results(manifest, manifest_sha, output)


def write_summary(manifest, manifest_sha, records, processed, reused, local_files, output):
    names = ("rasterio", "geopandas", "numpy", "pandas", "shapely", "pyproj")
    if local_files is None:
        names += ("earthaccess",)
    value = {
        "status": "passed_all_eight_references" if len(records) == 8 else "checkpointed_partial",
        "environment": "local_rehearsal" if local_files else "authenticated_cloud_day",
        "day": manifest["day"],
        "manifest_sha256": manifest_sha,
        "worker_sha256": digest(Path(__file__)),
        "completed_pairs": len(records),
        "processed_pairs_this_invocation": processed,
        "reused_pairs_this_invocation": reused,
        "source_bytes_all_pairs": sum(s["bytes"] for p in manifest["pairs"] for s in p["sources"]),
        "python": platform.python_version(),
        "dependencies": {name: importlib.metadata.version(name) for name in names},
        "records": records,
        "negative_label_permitted": False,
        "limitations": [
            "Fixed catalogue day, not all-period capacity or daily coverage",
            "Pixel centers; physical footprint method remains unresolved",
            "Child RSS high-water mark; disk samples at 0.2 s may miss short peaks",
            "Colab session disk is temporary; download checkpoint ZIP for persistence",
            "Successful payload bytes exclude protocol traffic and failed retries",
        ],
    }
    atomic_json(output / "day_summary.json", value)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-files", type=Path)
    parser.add_argument("--stop-after", type=int, choices=range(1, 9))
    parser.add_argument("--restore-results", type=Path)
    parser.add_argument("--child")
    parser.add_argument("--source-directory", type=Path)
    args = parser.parse_args()
    if args.child:
        manifest, _ = manifest_read()
        matches = [p for p in manifest["pairs"] if p["sample_id"] == args.child]
        require(len(matches) == 1 and args.source_directory is not None, "Invalid child pair")
        child_audit(matches[0], args.source_directory, ROOT / "day/results")
    else:
        run(args.local_files, args.stop_after, args.restore_results)
