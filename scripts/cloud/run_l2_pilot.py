"""One fixed training swath: cloud download, native audit, and exact local readback.

No date loops, negative labels, raw-file removal, or paid infrastructure creation.
The local-files mode only checks a pre-existing copy without contacting NASA.
"""

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import shutil
import time
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "pilot/manifest.json"
DATA_HOSTS = {"data.lpdaac.earthdatacloud.nasa.gov", "data.laadsdaac.earthdatacloud.nasa.gov"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_bundle(root):
    manifest = json.loads((root / "pilot/manifest.json").read_text(encoding="utf-8"))
    require(
        manifest["sample_id"] == "SNPP:2019013.0100", "Only the fixed training pilot is allowed"
    )
    require(len(manifest["sources"]) == 2, "Expected one fire/geolocation pair")
    for name, expected in manifest["bundle_files"].items():
        path = (root / name).resolve()
        require(path.is_relative_to(root.resolve()), "Bundle path escapes root")
        require(digest(path) == expected, f"Bundle changed: {name}")
    return manifest


def download_sources(manifest, directory, login_strategy="interactive"):
    import earthaccess

    # Interactive input remains in the cloud session; no credential files are created.
    require(login_strategy in {"interactive", "environment"}, "Unsupported login strategy")
    auth = earthaccess.login(strategy=login_strategy, persist=False)
    require(auth.authenticated, "Earthdata login failed")
    transferred = 0
    for source in manifest["sources"]:
        url = urlsplit(source["url"])
        require(
            url.scheme == "https" and url.hostname in DATA_HOSTS,
            "Expected official NASA data host",
        )
        require(url.path.rsplit("/", 1)[-1] == source["filename"], "URL identity mismatch")
        target = directory / source["filename"]
        if target.exists():
            require(
                target.stat().st_size == source["bytes"] and digest(target) == source["sha256"],
                "Existing source is incomplete or changed; stop for review",
            )
            continue
        earthaccess.download(
            [source["url"]],
            local_path=directory,
            provider=source["provider"],
            threads=1,
            show_progress=False,
        )
        require(target.exists(), "NASA download did not produce the expected filename")
        require(target.stat().st_size == source["bytes"], "Downloaded size differs")
        require(
            digest(target) == source["sha256"], "Downloaded source differs from local reference"
        )
        transferred += target.stat().st_size
    return transferred


def compare_result(manifest, output):
    reference = ROOT / "pilot/reference"
    expected = json.loads((reference / "audit.json").read_text(encoding="utf-8"))
    actual = json.loads((output / f"{manifest['stem']}_audit.json").read_text(encoding="utf-8"))
    for key in manifest["comparison_keys"]:
        require(actual[key] == expected[key], f"Cloud/local audit differs: {key}")
    for key in ("script_sha256", "aoi_sha256", "grid_sha256"):
        require(actual[key] == expected[key], f"Source provenance differs: {key}")
    expected_table = (
        pd.read_csv(reference / "grid_centers.csv").sort_values("grid_id").reset_index(drop=True)
    )
    actual_table = (
        pd.read_csv(output / f"{manifest['stem']}_grid_centers.csv")
        .sort_values("grid_id")
        .reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(actual_table, expected_table, check_exact=True)
    require(not actual["negative_label_permitted"], "Pilot must not produce labels")
    require(not actual_table.negative_label_permitted.any(), "Unexpected negative labels")
    require(
        actual_table.daily_observation_status.eq("unknown").all(), "Daily status must stay unknown"
    )


def run(local_files=None, login_strategy="interactive"):
    import rasterio

    start = time.perf_counter()
    manifest = verify_bundle(ROOT)
    directory = ROOT / "data/raw/firms_observation/sample_2019013_0100"
    if local_files is not None:
        directory = local_files.resolve()
    else:
        directory.mkdir(parents=True, exist_ok=True)
    required = sum(source["bytes"] for source in manifest["sources"])
    free_before = shutil.disk_usage(ROOT).free
    require(
        free_before > required + 2 * 2**30, "Pilot needs at least 2 GiB headroom beyond sources"
    )
    transferred = (
        0 if local_files is not None else download_sources(manifest, directory, login_strategy)
    )
    for source in manifest["sources"]:
        path = directory / source["filename"]
        require(
            path.stat().st_size == source["bytes"] and digest(path) == source["sha256"],
            "Source identity mismatch",
        )
    with rasterio.Env() as env:
        require(
            "HDF5" in env.drivers(), "GDAL HDF5 driver missing; do not substitute array orientation"
        )
    spec = importlib.util.spec_from_file_location(
        "sample_audit", ROOT / "scripts/firms/inspect_l2_observation_sample.py"
    )
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    audit.OUTPUT = ROOT / "pilot/results"
    metadata = manifest["metadata"]
    audit.inspect(directory, ROOT / metadata["fire"], ROOT / metadata["geolocation"])
    compare_result(manifest, audit.OUTPUT)
    versions = {
        name: importlib.metadata.version(name)
        for name in ("rasterio", "geopandas", "numpy", "pandas", "shapely", "pyproj")
    }
    if local_files is None:
        versions["earthaccess"] = importlib.metadata.version("earthaccess")
    result_bytes = sum(p.stat().st_size for p in audit.OUTPUT.iterdir() if p.is_file())
    result = {
        "status": "passed_exact_local_reference_comparison",
        "environment": "local_files_test"
        if local_files is not None
        else "authenticated_cloud_pilot",
        "sample_id": manifest["sample_id"],
        "manifest_sha256": digest(MANIFEST),
        "pilot_script_sha256": digest(Path(__file__)),
        "source_bytes": required,
        "downloaded_payload_bytes": transferred,
        "result_bytes_before_summary": result_bytes,
        "elapsed_seconds": time.perf_counter() - start,
        "free_disk_before_bytes": free_before,
        "free_disk_after_bytes": shutil.disk_usage(ROOT).free,
        "python": platform.python_version(),
        "dependencies": versions,
        "negative_label_permitted": False,
        "limitations": [
            "One swath; not a full-period capacity benchmark",
            "Counts are pixel centers, not physical footprints or daily labels",
            "Disk readings are before/after snapshots, not peak measurements",
            "Downloaded bytes count successful file payload, not protocol/retry traffic",
        ],
    }
    (audit.OUTPUT / "cloud_pilot_verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_MB": required / 1e6,
                "result_MB": result_bytes / 1e6,
                "seconds": result["elapsed_seconds"],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-files", type=Path)
    parser.add_argument(
        "--login-strategy", choices=["interactive", "environment"], default="interactive"
    )
    args = parser.parse_args()
    run(args.local_files, args.login_strategy)
