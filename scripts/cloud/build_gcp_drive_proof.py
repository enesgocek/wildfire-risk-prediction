"""Offline deterministic bundle: frozen science + one verified received pair."""

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive_bytes(files):
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 6, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return result.getvalue()


def build(revision="original"):
    received = ROOT / "outputs/gcp_benchmark/received/gcp_benchmark_results.zip"
    proof = json.loads(
        (
            ROOT / "outputs/reports/observation_coverage/gcp_benchmark_received_verification.json"
        ).read_text()
    )
    if (
        proof["status"] != "independent_gcp_two_arm_readback_passed"
        or sha(received.read_bytes()) != proof["result_zip_sha256"]
    ):
        raise ValueError("Received benchmark proof changed")
    summer = (ROOT / "outputs/cloud_summer/l2_summer_B_bundle.zip").read_bytes()
    if sha(summer) != "0a90b93be0ed31fa468b6ecef61851612bcd255e34caf3ccdb6adf2d6d425f7e":
        raise ValueError("Frozen science changed")
    with zipfile.ZipFile(io.BytesIO(summer)) as archive:
        manifest = json.loads(archive.read("summer/manifest.json"))
    pair = manifest["pairs"][0]
    suffixes = (
        "audit.json",
        "grid_centers.csv",
        "area_estimate.json",
        "area_estimate.csv",
        "area_estimate.gpkg",
        "scan_times.csv",
        "scan_grid.csv",
        "all_scans.csv",
        "scan_provenance.json",
        "checkpoint.json",
    )
    with (
        zipfile.ZipFile(received) as outer,
        zipfile.ZipFile(io.BytesIO(outer.read("workers_1.zip"))) as arm,
    ):
        products = {f"{pair['stem']}_{s}": arm.read(f"{pair['stem']}_{s}") for s in suffixes}
    files = {"summer.zip": summer, "pair.zip": archive_bytes(products)}
    for name in (
        "run_gcp_benchmark.py",
        "verified_job_store.py",
        "drive_job_store.py",
        "run_gcp_drive_proof.py",
        "diagnose_gcp_drive_proof.py",
    ):
        files[name] = (ROOT / "scripts/cloud" / name).read_bytes()
    spec = {
        "protocol": "gcp_drive_real_pair_proof_v1",
        "sample_id": pair["sample_id"],
        "files": {n: sha(v) for n, v in files.items()},
        "raw_downloads": 0,
        "negative_label_permitted": False,
    }
    files["proof_manifest.json"] = json.dumps(spec, sort_keys=True, indent=2).encode()
    if revision not in {"original", "v2"}:
        raise ValueError("Unapproved package revision")
    out = ROOT / "outputs" / ("gcp_drive_proof" if revision == "original" else "gcp_drive_proof_v2")
    out.mkdir(parents=True, exist_ok=True)
    package = out / (
        "wildfire_gcp_drive_proof.zip"
        if revision == "original"
        else "wildfire_gcp_drive_proof_v2.zip"
    )
    if package.exists() and package.read_bytes() != archive_bytes(files):
        raise ValueError("Existing package is frozen; use a new revision")
    package.write_bytes(archive_bytes(files))
    # A convenient local rehearsal directory; never extracts untrusted members.
    extracted = out / "package"
    extracted.mkdir(exist_ok=True)
    for name, data in files.items():
        (extracted / name).write_bytes(data)
    report = {
        "status": "prepared_not_drive_executed",
        "package_sha256": sha(package.read_bytes()),
        "package_bytes": package.stat().st_size,
        "payload_bytes": len(files["pair.zip"]),
        "payload_sha256": sha(files["pair.zip"]),
        "manifest_sha256": sha(files["proof_manifest.json"]),
        "raw_downloads": 0,
    }
    (out / "preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", choices=("original", "v2"), default="original")
    build(parser.parse_args().revision)
