"""Fixed approved summer day: six sequential pairs, persistent per-pair commits.

Uses the unchanged native inspector/area/scan routines. New sources have no
frozen local raw reference: CMR identity/size/checksum and native input headers
are checked, and new SHA values are recorded; no golden-reference claim.
"""

import argparse
import importlib.metadata
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "summer/results"
DAY = "2023-07-16"
KEYS = {
    "SNPP:2023197.0018",
    "N20:2023197.0106",
    "SNPP:2023197.1000",
    "N20:2023197.1048",
    "SNPP:2023197.1136",
    "N20:2023197.2306",
}
SUFFIXES = (
    "audit.json",
    "grid_centers.csv",
    "area_estimate.json",
    "area_estimate.csv",
    "area_estimate.gpkg",
    "scan_times.csv",
    "scan_grid.csv",
    "all_scans.csv",
    "scan_provenance.json",
)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load("summer_io", ROOT / "scripts/cloud/run_l2_day.py")
storage = load("summer_copy", ROOT / "scripts/cloud/checkpoint_store.py")
timing = load("summer_native", ROOT / "scripts/firms/audit_l2_observation_timing.py")
area, audit = timing.area, timing.audit
require, digest, atomic_json = audit.require, audit.digest, base.atomic_json


def manifest_read():
    path = ROOT / "summer/manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    require(manifest["day"] == DAY and manifest["option"] == "B_one_day", "Unapproved scope")
    require(manifest["negative_label_permitted"] is False, "Labels forbidden")
    pairs = manifest["pairs"]
    require(len(pairs) == 6 and {p["sample_id"] for p in pairs} == KEYS, "Wrong six pairs")
    for name, checksum in manifest["bundle_files"].items():
        target = (ROOT / name).resolve()
        require(target.is_relative_to(ROOT.resolve()), "Bundle path escapes root")
        require(digest(target) == checksum, f"Bundle changed: {name}")
    for pair in pairs:
        require(pair["stem"] == audit.sample_stem(pair["sensor"], pair["key"]), "Wrong stem")
        require(pair["sample_id"] == f"{pair['sensor']}:{pair['key']}", "Wrong sample identity")
        require(pair["start_utc"].startswith(DAY), "Wrong day")
        require({s["role"] for s in pair["sources"]} == {"fire", "geolocation"}, "Wrong roles")
        require(len(pair["sources"]) == 2, "Duplicate role")
        for source in pair["sources"]:
            require(
                audit.product_identity(source["filename"])[:3]
                == (pair["sensor"], source["role"], pair["key"]),
                "Source identity differs",
            )
            url = urlsplit(source["url"])
            require(url.scheme == "https" and url.hostname in base.pilot.DATA_HOSTS, "NASA host")
            require(url.path.rsplit("/", 1)[-1] == source["filename"], "URL filename")
            require(source["bytes"] > 0, "Invalid size")
            metadata_path = ROOT / pair["metadata"][source["role"]]
            require(digest(metadata_path) == source["metadata_sha256"], "Metadata changed")
    return manifest, digest(path)


def source_check(pair, source, path):
    require(path.stat().st_size == source["bytes"], "Downloaded size differs")
    return audit.verify_cmr(
        path, ROOT / pair["metadata"][source["role"]], source["filename"].split(".")[0]
    )


def download_pair(pair, directory):
    import earthaccess

    directory.mkdir(parents=True, exist_ok=True)
    auth = earthaccess.login(strategy="environment", persist=False)
    require(auth.authenticated, "Earthdata login failed")
    transferred = 0
    for source in pair["sources"]:
        target = directory / source["filename"]
        if target.exists():
            source_check(pair, source, target)
            continue
        earthaccess.download(
            [source["url"]],
            local_path=directory,
            provider=source["provider"],
            threads=1,
            show_progress=False,
        )
        require(target.exists(), "Expected NASA filename not downloaded")
        source_check(pair, source, target)
        transferred += target.stat().st_size
    return transferred


def child_audit(pair, directory):
    area.OUTPUT = area.audit.OUTPUT = audit.OUTPUT = timing.OUTPUT = OUTPUT
    inspector = load("summer_inspector", ROOT / "scripts/firms/inspect_l2_observation_sample.py")
    inspector.OUTPUT = OUTPUT
    inspector.inspect(
        directory, ROOT / pair["metadata"]["fire"], ROOT / pair["metadata"]["geolocation"]
    )
    parts_path, parts = area.load_parts()
    area.estimate(pair["sensor"], pair["key"], parts_path, parts)
    aoi = gpd.read_file(ROOT / "data/aoi/aoi.geojson").to_crs(4326).geometry.union_all()
    shapely.prepare(aoi)
    centers, scans, provenance, _ = timing.source_scans(
        pair["sensor"],
        pair["key"],
        aoi,
        timing.Transformer.from_crs(4326, 6933, always_xy=True),
        set(parts.grid_id),
    )
    centers.to_csv(OUTPUT / f"{pair['stem']}_scan_grid.csv", index=False)
    scans.to_csv(OUTPUT / f"{pair['stem']}_all_scans.csv", index=False)
    atomic_json(OUTPUT / f"{pair['stem']}_scan_provenance.json", provenance)
    peak = None
    if platform.system() == "Linux":
        import resource

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    atomic_json(OUTPUT / f"{pair['stem']}_memory.json", {"child_peak_rss_bytes": peak})


def compare_pair(pair, output):
    """Readback invariants and geometry/count consistency, not a golden raw comparison."""
    stem = pair["stem"]
    report = json.loads((output / f"{stem}_audit.json").read_text())
    require(report["sample_id"] == pair["sample_id"], "Audit identity")
    require(report["negative_label_permitted"] is False, "Labels forbidden")
    for name, field in (
        ("scripts/firms/inspect_l2_observation_sample.py", "script_sha256"),
        ("data/aoi/aoi.geojson", "aoi_sha256"),
        ("data/aoi/grid_5km.geojson", "grid_sha256"),
    ):
        require(report[field] == digest(ROOT / name), "Audit provenance")
    for source in pair["sources"]:
        reported = report["sources"][source["role"]]
        require(
            reported["bytes"] == source["bytes"]
            and reported["cmr_metadata_sha256"] == source["metadata_sha256"],
            "Source provenance",
        )
        require(len(reported["sha256"]) == 64, "Source SHA absent")
        metadata = json.loads((ROOT / pair["metadata"][source["role"]]).read_text())
        expected_checksum = metadata["DataGranule"]["ArchiveAndDistributionInformation"][0].get(
            "Checksum"
        )
        require(
            reported["cmr_checksum"] == expected_checksum
            and reported["cmr_checksum_verified"] == bool(expected_checksum),
            "CMR checksum status",
        )
        interval = reported["cmr_interval"]
        require(
            pd.Timestamp(interval["BeginningDateTime"]) == pd.Timestamp(pair["start_utc"])
            and pd.Timestamp(interval["EndingDateTime"]) == pd.Timestamp(pair["end_utc"]),
            "Source interval",
        )
    grids = set(gpd.read_file(ROOT / "data/aoi/grid_5km.geojson").grid_id)
    counts = pd.read_csv(output / f"{stem}_grid_centers.csv").set_index("grid_id").sort_index()
    require(
        len(counts) == 2899 and counts.index.is_unique and set(counts.index) == grids, "Grid keys"
    )
    require(
        counts.daily_observation_status.eq("unknown").all()
        and counts.negative_label_permitted.eq(False).all(),
        "Daily policy",
    )
    require(
        list(counts.columns)
        == [*timing.COUNTS, "daily_observation_status", "negative_label_permitted"],
        "Count schema",
    )
    values = counts[timing.COUNTS].to_numpy()
    require(
        np.isfinite(values).all() and (values >= 0).all() and (values == np.floor(values)).all(),
        "Invalid counts",
    )
    require(
        np.array_equal(counts[list(audit.CLASSES)].sum(axis=1), counts.pixel_center_count),
        "Class sum",
    )
    require(
        counts[list(audit.CLASSES)].sum().astype(int).to_dict() == report["pilot_class_counts"],
        "Report class counts",
    )
    require(
        int(counts.pixel_center_count.sum()) == report["spatial_counts"]["pilot_centers"],
        "Pilot total",
    )
    for field in ("input_non_nominal", "geo_non_nominal", "residual_bowtie"):
        require(int(counts[field].sum()) == report["pilot_qa_counts"][field], "QA report total")
        require(
            sum(report["pilot_class_qa_counts"][name][field] for name in audit.CLASSES)
            == report["pilot_qa_counts"][field],
            "Per-class QA report",
        )
    require(
        int(counts.land_nominal_input_no_residual.sum())
        == report["pilot_land_nominal_input_no_residual"],
        "Land diagnostic total",
    )
    scan_grid = pd.read_csv(output / f"{stem}_scan_grid.csv", dtype={"pair_key": str})
    summed = scan_grid.groupby("grid_id")[timing.COUNTS].sum().reindex(counts.index, fill_value=0)
    require(np.array_equal(summed.to_numpy(), values), "Independent native scan counts differ")
    require(not scan_grid.duplicated(["grid_id", "scan_index"]).any(), "Duplicate scan/grid")
    require(
        scan_grid.sensor.eq(pair["sensor"]).all() and scan_grid.pair_key.eq(pair["key"]).all(),
        "Scan identity",
    )
    estimate = json.loads((output / f"{stem}_area_estimate.json").read_text())
    for field, suffix in (
        ("previous_audit_sha256", "audit.json"),
        ("area_csv_sha256", "area_estimate.csv"),
        ("geometry_sha256", "area_estimate.gpkg"),
        ("scan_times_sha256", "scan_times.csv"),
    ):
        require(
            estimate["sources"][field] == digest(output / f"{stem}_{suffix}"),
            "Area reference changed",
        )
    require(
        estimate["negative_label_permitted"] is False and estimate["method"] == area.METHOD,
        "Area policy",
    )
    require(
        estimate["sources"]["script_sha256"] == digest(Path(area.__file__))
        and estimate["sources"]["aoi_parts_sha256"]
        == digest(ROOT / "data/interim/grid_aoi_parts.geojson"),
        "Area source provenance",
    )
    table = pd.read_csv(output / f"{stem}_area_estimate.csv").set_index("grid_id").sort_index()
    require(table.index.equals(counts.index), "Area keys")
    require(
        table.daily_observation_status.eq("unknown").all()
        and table.negative_label_permitted.eq(False).all(),
        "Area labels",
    )
    for group in area.GROUPS:
        geometry = (
            gpd.read_file(output / f"{stem}_area_estimate.gpkg", layer=group)
            .set_index("grid_id")
            .sort_index()
        )
        require(
            geometry.index.equals(counts.index) and geometry.crs.to_epsg() == 6933,
            "Geometry keys/CRS",
        )
        require(geometry.geometry.is_valid.all(), "Invalid saved geometry")
        measured = geometry.geometry.area.to_numpy()
        require(
            (measured >= 0).all() and (measured <= table.aoi_area_m2 + 0.1).all(), "Area bounds"
        )
        require(
            np.allclose(measured, table[f"{group}_area_estimate_m2"], rtol=1e-9, atol=1e-4),
            "Geometry area",
        )
        require(
            np.allclose(
                measured / table.aoi_area_m2,
                table[f"{group}_fraction_estimate"],
                rtol=1e-9,
                atol=1e-12,
            ),
            "Area fraction",
        )
    scans = pd.read_csv(output / f"{stem}_all_scans.csv", dtype={"pair_key": str})
    original = pd.read_csv(output / f"{stem}_scan_times.csv")
    for column in original.columns:
        pd.testing.assert_series_equal(original[column], scans[column], check_exact=True)
    provenance = json.loads((output / f"{stem}_scan_provenance.json").read_text())
    require(provenance["native_grid_counts_exact_match"] is True, "Native recount absent")
    require(provenance["sources"] == report["sources"], "Scan sources")
    require(provenance["whole_swath_scan_count"] == len(scans), "Scan count")


def checkpoint_read(pair, output, manifest_sha):
    path = output / f"{pair['stem']}_checkpoint.json"
    if not path.exists():
        return None
    record = json.loads(path.read_text())
    require(
        record["manifest_sha256"] == manifest_sha
        and record["worker_sha256"] == digest(Path(__file__)),
        "Checkpoint code/manifest",
    )
    require(record["sample_id"] == pair["sample_id"], "Checkpoint identity")
    require(
        set(record["outputs"]) == {f"{pair['stem']}_{s}" for s in SUFFIXES}, "Checkpoint outputs"
    )
    for name, checksum in record["outputs"].items():
        require(digest(output / name) == checksum, "Checkpoint output changed")
    compare_pair(pair, output)
    return record


def restore_pair(payload, pair, manifest_sha, output):
    expected = {f"{pair['stem']}_{s}" for s in (*SUFFIXES, "checkpoint.json")}
    with zipfile.ZipFile(payload) as archive, tempfile.TemporaryDirectory(dir=ROOT) as directory:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        require(len(names) == len(set(names)) and set(names) == expected, "Unexpected pair ZIP")
        require(
            all(0 < i.file_size < 150_000_000 for i in infos)
            and sum(i.file_size for i in infos) < 300_000_000,
            "Result ZIP size",
        )
        require(archive.testzip() is None, "ZIP CRC")
        staging = Path(directory)
        for name in names:
            (staging / name).write_bytes(archive.read(name))
        require(checkpoint_read(pair, staging, manifest_sha) is not None, "Incomplete ZIP")
        output.mkdir(parents=True, exist_ok=True)
        for name in names:
            destination = output / name
            if destination.exists():
                require(digest(destination) == digest(staging / name), "Existing output differs")
            else:
                shutil.copyfile(staging / name, destination)


def save_pair(pair, store_root, manifest_sha):
    record = checkpoint_read(pair, OUTPUT, manifest_sha)
    require(record is not None, "Cannot save incomplete pair")
    local = OUTPUT.parent / f"{pair['stem']}.zip"
    local.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(local, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in [*record["outputs"], f"{pair['stem']}_checkpoint.json"]:
            archive.write(OUTPUT / name, name)
    checksum = digest(local)
    folder = store_root.resolve() / manifest_sha
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{pair['stem']}_{checksum}"
    destination = folder / f"{name}.zip"
    storage.copy_verified(base, local, destination, checksum)
    with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
        restore_pair(destination, pair, manifest_sha, Path(temporary) / "readback")
    commit = {
        "protocol": "summer_pair_v1",
        "manifest_sha256": manifest_sha,
        "worker_sha256": digest(Path(__file__)),
        "sample_id": pair["sample_id"],
        "payload_sha256": checksum,
        "payload_bytes": destination.stat().st_size,
        "payload_name": destination.name,
    }
    marker = folder / f"{name}.commit.json"
    if marker.exists():
        require(json.loads(marker.read_text()) == commit, "Existing commit differs")
    else:
        atomic_json(marker, commit)
    require(json.loads(marker.read_text()) == commit, "Commit readback")
    return commit


def restore_store(pair, store_root, manifest_sha):
    folder = store_root.resolve() / manifest_sha
    markers = list(folder.glob(f"{pair['stem']}_*.commit.json"))
    require(len(markers) <= 1, "Multiple committed versions; review required")
    if not markers:
        return False
    record = json.loads(markers[0].read_text())
    checksum = record["payload_sha256"]
    name = f"{pair['stem']}_{checksum}"
    require(len(checksum) == 64 and all(c in "0123456789abcdef" for c in checksum), "Commit SHA")
    require(
        markers[0].name == f"{name}.commit.json" and record["payload_name"] == f"{name}.zip",
        "Commit filename",
    )
    require(
        record["manifest_sha256"] == manifest_sha
        and record["worker_sha256"] == digest(Path(__file__))
        and record["sample_id"] == pair["sample_id"]
        and record["protocol"] == "summer_pair_v1",
        "Commit identity",
    )
    payload = folder / record["payload_name"]
    require(
        digest(payload) == checksum and payload.stat().st_size == record["payload_bytes"],
        "Saved ZIP changed",
    )
    restore_pair(payload, pair, manifest_sha, OUTPUT)
    return True


def cleanup_pair(pair, directory):
    scratch = (ROOT / "summer/raw").resolve()
    require(directory.resolve().is_relative_to(scratch), "Cleanup outside summer scratch")
    report = json.loads((OUTPUT / f"{pair['stem']}_audit.json").read_text())
    for source in pair["sources"]:
        path = directory / source["filename"]
        if path.exists():
            require(path.resolve().is_relative_to(scratch), "Source escapes scratch")
            require(digest(path) == report["sources"][source["role"]]["sha256"], "Raw changed")
            path.unlink()


def write_summary(manifest, manifest_sha, processed, reused):
    records = [checkpoint_read(p, OUTPUT, manifest_sha) for p in manifest["pairs"]]
    records = [r for r in records if r is not None]
    summary = {
        "status": "complete_native_diagnostics" if len(records) == 6 else "partial",
        "day": DAY,
        "manifest_sha256": manifest_sha,
        "worker_sha256": digest(Path(__file__)),
        "completed_pairs": len(records),
        "processed_this_invocation": processed,
        "reused_this_invocation": reused,
        "records": records,
        "python": platform.python_version(),
        "dependencies": {
            n: importlib.metadata.version(n)
            for n in ("rasterio", "geopandas", "numpy", "pandas", "shapely", "pyproj")
        },
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "golden_raw_reference_available": False,
    }
    atomic_json(OUTPUT / "summer_summary.json", summary)
    destination = ROOT / "l2_summer_results.zip"
    with zipfile.ZipFile(
        destination.with_suffix(".zip.tmp"), "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        archive.write(OUTPUT / "summer_summary.json", "summer_summary.json")
        for pair, record in zip(
            manifest["pairs"],
            [checkpoint_read(p, OUTPUT, manifest_sha) for p in manifest["pairs"]],
            strict=True,
        ):
            if record is not None:
                for name in [*record["outputs"], f"{pair['stem']}_checkpoint.json"]:
                    archive.write(OUTPUT / name, name)
    destination.with_suffix(".zip.tmp").replace(destination)
    print(f"Completed {len(records)}/6; processed {processed}, reused {reused}", flush=True)


def validate_store_root(store_root):
    allowed = Path("/content/drive/MyDrive/wildfire-risk-prediction/colab_checkpoints/summer_B")
    require(
        platform.system() == "Linux"
        and store_root.resolve() == allowed
        and Path("/content/drive/MyDrive").is_dir(),
        "Mount selected Drive directory",
    )


def run(store_root, verify_only=False, stop_after=None):
    manifest, manifest_sha = manifest_read()
    validate_store_root(store_root)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    processed, reused = 0, 0
    for pair in manifest["pairs"]:
        recovered = restore_store(pair, store_root, manifest_sha)
        existing = checkpoint_read(pair, OUTPUT, manifest_sha)
        raw = ROOT / "summer/raw" / pair["stem"]
        if existing is not None:
            # Local results without a Drive commit are retried for saving before raw cleanup.
            if not recovered:
                require(not verify_only, "Saved commit absent")
                save_pair(pair, store_root, manifest_sha)
            reused += 1
            cleanup_pair(pair, raw)
            continue
        require(not verify_only, "Drive result incomplete")
        started = time.perf_counter()
        with base.DiskSampler(ROOT) as disk:
            require(
                shutil.disk_usage(ROOT).free > sum(s["bytes"] for s in pair["sources"]) + 3 * 2**30,
                "Need source size plus 3 GiB scratch headroom",
            )
            transferred = download_pair(pair, raw)
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
            compare_pair(pair, OUTPUT)
        memory = json.loads((OUTPUT / f"{pair['stem']}_memory.json").read_text())
        require(memory["child_peak_rss_bytes"] > 0, "Linux memory metric absent")
        record = {
            "sample_id": pair["sample_id"],
            "manifest_sha256": manifest_sha,
            "worker_sha256": digest(Path(__file__)),
            "outputs": {
                f"{pair['stem']}_{s}": digest(OUTPUT / f"{pair['stem']}_{s}") for s in SUFFIXES
            },
            "metrics": {
                "elapsed_seconds": time.perf_counter() - started,
                "downloaded_payload_bytes": transferred,
                "pair_source_bytes": sum(s["bytes"] for s in pair["sources"]),
                **memory,
                "sampled_disk_increase_bytes": disk.before - disk.minimum,
            },
        }
        atomic_json(OUTPUT / f"{pair['stem']}_checkpoint.json", record)
        save_pair(pair, store_root, manifest_sha)
        cleanup_pair(pair, raw)
        processed += 1
        write_summary(manifest, manifest_sha, processed, reused)
        if stop_after is not None and processed >= stop_after:
            break
    write_summary(manifest, manifest_sha, processed, reused)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-root", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--stop-after", type=int, choices=range(1, 7))
    parser.add_argument("--child")
    parser.add_argument("--source-directory", type=Path)
    args = parser.parse_args()
    if args.child:
        manifest, _ = manifest_read()
        selected = [p for p in manifest["pairs"] if p["sample_id"] == args.child]
        require(len(selected) == 1 and args.source_directory is not None, "Invalid child")
        child_audit(selected[0], args.source_directory)
    else:
        require(args.store_root is not None, "Drive store required")
        run(args.store_root, args.verify_only, args.stop_after)
