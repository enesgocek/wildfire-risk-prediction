"""Run the frozen one-swath pilot on a VM; no VM creation or date loops."""

import argparse
import getpass
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import venv
import zipfile
from pathlib import Path

PILOT_SHA = "bce362d01b5a5d204c5979910703e16f3be11b0568f12b5ac8e34790aee6bbac"
SOURCE_BYTES = 194702968
SOURCE_ID = "SNPP:2019013.0100"
RESULT_NAMES = {
    "cloud_pilot_verification.json",
    "l2_sample_2019013.0100_audit.json",
    "l2_sample_2019013.0100_grid_centers.csv",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def unpack(bundle, destination):
    require(digest(bundle) == PILOT_SHA, "Frozen pilot ZIP identity differs")
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle) as archive:
        infos = archive.infolist()
        require(len(infos) == 9 and len({i.filename for i in infos}) == 9, "ZIP members")
        require(sum(i.file_size for i in infos) <= 6_000_000, "ZIP size limit")
        for item in infos:
            path = (destination / item.filename).resolve()
            require(path.is_relative_to(destination.resolve()), "ZIP path escapes root")
            require(not stat.S_ISLNK(item.external_attr >> 16), "ZIP symlink")
            if path.exists():
                require(path.read_bytes() == archive.read(item), "Existing pilot file changed")
        require(archive.testzip() is None, "ZIP CRC")
        archive.extractall(destination)
    manifest = json.loads((destination / "pilot/manifest.json").read_text())
    require(manifest["sample_id"] == SOURCE_ID, "Only fixed training source allowed")
    require(sum(s["bytes"] for s in manifest["sources"]) == SOURCE_BYTES, "Source budget")
    for name, checksum in manifest["bundle_files"].items():
        path = (destination / name).resolve()
        require(path.is_relative_to(destination.resolve()), "Manifest path escapes root")
        require(digest(path) == checksum, "Extracted pilot file changed")
    return manifest


def clean_environment():
    result = os.environ.copy()
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "EARTHDATA_USERNAME",
        "EARTHDATA_PASSWORD",
        "EARTHDATA_TOKEN",
    ):
        result.pop(name, None)
    result["PYTHONNOUSERSITE"] = "1"
    return result


def create_environment(root, requirements, environment):
    target = root / ".venv"
    venv.EnvBuilder(with_pip=True, system_site_packages=False).create(target)
    python = target / "bin/python"
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "--isolated",
            "install",
            "--no-cache-dir",
            "--only-binary=:all:",
            "--timeout",
            "60",
            "--retries",
            "2",
            "-r",
            str(requirements),
        ],
        check=True,
        timeout=900,
        env=environment,
    )
    subprocess.run([str(python), "-m", "pip", "check"], check=True, timeout=60, env=environment)
    subprocess.run(
        [
            str(python),
            "-c",
            "import rasterio\nwith rasterio.Env() as e:\n"
            " assert 'HDF5' in e.drivers(), 'GDAL HDF5 driver missing'",
        ],
        check=True,
        timeout=60,
        env=environment,
    )
    return python


def link_local_sources(manifest, local_files, destination):
    """Preserve original sources; the frozen inspector requires in-root source paths."""
    local_files = local_files.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for source in manifest["sources"]:
        original = (local_files / source["filename"]).resolve()
        target = destination / source["filename"]
        require(original.is_relative_to(local_files), "Local source escapes directory")
        require(target.resolve().is_relative_to(destination.resolve()), "Local target escapes root")
        require(
            original.stat().st_size == source["bytes"] and digest(original) == source["sha256"],
            "Local source changed",
        )
        if not target.exists():
            os.link(original, target)
        require(
            target.stat().st_size == source["bytes"] and digest(target) == source["sha256"],
            "Local linked source changed",
        )
    return destination


def export_results(output, destination, manifest_sha):
    require({p.name for p in output.iterdir() if p.is_file()} == RESULT_NAMES, "Result members")
    summary = json.loads((output / "cloud_pilot_verification.json").read_text())
    require(summary["status"] == "passed_exact_local_reference_comparison", "Pilot failed")
    require(summary["sample_id"] == SOURCE_ID, "Result source differs")
    require(summary["manifest_sha256"] == manifest_sha, "Result manifest differs")
    require(summary["negative_label_permitted"] is False, "Labels forbidden")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".pending", delete=False) as f:
        pending = Path(f.name)
    try:
        with zipfile.ZipFile(pending, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(RESULT_NAMES):
                archive.write(output / name, name)
        with zipfile.ZipFile(pending) as archive:
            require(archive.testzip() is None, "Result ZIP CRC")
            require(set(archive.namelist()) == RESULT_NAMES, "Result ZIP members")
            for name in RESULT_NAMES:
                require(archive.read(name) == (output / name).read_bytes(), "ZIP readback")
        # The dedicated pilot path may be refreshed; no prior scientific inputs are removed.
        pending.replace(destination)
    finally:
        pending.unlink(missing_ok=True)
    return summary


def run(package, work, local_files=None):
    require(sys.version_info[:2] == (3, 12), "Python 3.12 required")
    rehearsal = local_files is not None
    require(
        rehearsal or (platform.system() == "Linux" and platform.machine() == "x86_64"),
        "Expected Linux x86_64 VM",
    )
    require(not work.is_symlink(), "Work directory is a symlink")
    work = work.resolve()
    package = package.resolve()
    require(not work.is_relative_to(package), "Work must be outside the package")
    require(work != Path(work.anchor) and not work.is_symlink(), "Dedicated work directory")
    manifest_path = package / "gcp_manifest.json"
    spec = json.loads(manifest_path.read_text())
    require(spec["protocol"] == "gcp_one_swath_v1", "Package protocol")
    require(spec["negative_label_permitted"] is False, "Labels forbidden")
    require(
        set(spec["files"]) == {"pilot.zip", "requirements.txt", "run_gcp_portability.py"},
        "Exact package files required",
    )
    for name, expected in spec["files"].items():
        path = (package / name).resolve()
        require(path.is_relative_to(package), "Package path escapes root")
        require(digest(path) == expected, "GCP package changed")
    require(
        spec["files"].get("run_gcp_portability.py") == digest(Path(__file__)), "Runner identity"
    )
    require(spec["files"].get("pilot.zip") == PILOT_SHA, "Frozen pilot identity")
    work.mkdir(parents=True, exist_ok=True)
    require(shutil.disk_usage(work).free > 5 * 2**30 + SOURCE_BYTES, "Need 5 GiB free headroom")
    start = time.perf_counter()
    native = work / "native"
    require(not native.is_symlink(), "Native directory is a symlink")
    manifest = unpack(package / "pilot.zip", native)
    environment = clean_environment()
    python = (
        Path(sys.executable)
        if rehearsal
        else create_environment(work, package / "requirements.txt", environment)
    )
    command = [str(python), str(native / "scripts/cloud/run_l2_pilot.py")]
    if rehearsal:
        linked = link_local_sources(
            manifest, local_files, native / "data/raw/firms_observation/sample_2019013_0100"
        )
        command += ["--local-files", str(linked.resolve())]
    else:
        command += ["--login-strategy", "environment"]
    try:
        if not rehearsal:
            environment["EARTHDATA_USERNAME"] = getpass.getpass("Earthdata kullanıcı adı: ")
            environment["EARTHDATA_PASSWORD"] = getpass.getpass("Earthdata parola: ")
        subprocess.run(command, check=True, timeout=900, env=environment)
    finally:
        environment.clear()
    destination = work / "gcp_pilot_results.zip"
    summary = export_results(
        native / "pilot/results", destination, digest(native / "pilot/manifest.json")
    )
    require(
        summary["environment"]
        == ("local_files_test" if rehearsal else "authenticated_cloud_pilot"),
        "Execution mode differs",
    )
    report = {
        "status": "local_portability_rehearsal_passed" if rehearsal else "gcp_portability_passed",
        "sample_id": SOURCE_ID,
        "source_bytes": SOURCE_BYTES,
        "result_zip_sha256": digest(destination),
        "result_zip_bytes": destination.stat().st_size,
        "package_manifest_sha256": digest(manifest_path),
        "elapsed_seconds_including_setup": time.perf_counter() - start,
        "raw_reprocessed": True,
        "network_download_requested": not rehearsal,
        "negative_label_permitted": False,
        "full_years_processed": False,
        "limitations": "One swath; no parallel speedup or full-period budget proof",
    }
    (work / "gcp_run_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Download these two files: {destination}, {work / 'gcp_run_summary.json'}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=Path.home() / "wildfire-gcp-work")
    parser.add_argument(
        "--local-files", type=Path, help="Local rehearsal; no install or NASA login"
    )
    args = parser.parse_args()
    run(Path(__file__).resolve().parent, args.work, args.local_files)
