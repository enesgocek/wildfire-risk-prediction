"""Validate returned proof summary. Does not independently access remote Drive."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_package(path, preparation):
    data = path.read_bytes()
    require(
        sha(data) == preparation["package_sha256"] and len(data) == preparation["package_bytes"],
        "Prepared package changed",
    )
    with zipfile.ZipFile(path) as archive:
        manifest_bytes = archive.read("proof_manifest.json")
        require(sha(manifest_bytes) == preparation["manifest_sha256"], "Package manifest checksum")
        manifest = json.loads(manifest_bytes)
        expected = {
            "summer.zip",
            "pair.zip",
            "run_gcp_benchmark.py",
            "verified_job_store.py",
            "drive_job_store.py",
            "run_gcp_drive_proof.py",
        }
        if "diagnose_gcp_drive_proof.py" in manifest["files"]:
            expected.add("diagnose_gcp_drive_proof.py")
        require(set(manifest["files"]) == expected, "Prepared package files")
        require(
            len(archive.namelist()) == len(expected) + 1
            and set(archive.namelist()) == expected | {"proof_manifest.json"},
            "Prepared package members",
        )
        require(archive.testzip() is None, "Prepared package CRC")
        require(
            manifest["protocol"] == "gcp_drive_real_pair_proof_v1"
            and manifest["sample_id"] == "SNPP:2023197.0018"
            and manifest["negative_label_permitted"] is False
            and type(manifest["raw_downloads"]) is int
            and manifest["raw_downloads"] == 0,
            "Prepared package scope",
        )
        for name, checksum in manifest["files"].items():
            require(sha(archive.read(name)) == checksum, "Prepared package file checksum")
        payload = archive.read("pair.zip")
        require(
            len(payload) == preparation["payload_bytes"]
            and sha(payload) == preparation["payload_sha256"],
            "Prepared scientific payload",
        )


def verify(summary, preparation):
    require(summary["status"] == "drive_real_pair_persistence_passed", "Proof status")
    require(summary["manifest_sha256"] == preparation["manifest_sha256"], "Proof manifest")
    require(summary["negative_label_permitted"] is False, "Proof policy")
    require(summary["production_months_processed"] == 0, "Proof scope")
    require(summary["off_vm_persistence_proven"] is True, "Remote proof absent")
    saved, restored = summary["save"], summary["restore"]
    for phase, kind in ((saved, "save"), (restored, "restore")):
        require(phase["status"] == "passed" and phase["phase"] == kind, "Phase status")
        require(phase["manifest_sha256"] == summary["manifest_sha256"], "Phase identity")
        require(phase["filesystem_only"] is False, "Local rehearsal is not Drive proof")
        require(
            phase["negative_label_permitted"] is False and phase["raw_downloads"] == 0,
            "Phase scope",
        )
        require(
            type(phase["scientific_readbacks"]) is int and phase["scientific_readbacks"] > 0,
            "Scientific readback absent",
        )
        require(type(phase["process_id"]) is int and phase["process_id"] > 0, "Process identity")
        require(phase["sample_id"] == "SNPP:2023197.0018", "Unapproved pair")
        require(phase["payload_bytes"] == preparation["payload_bytes"], "Payload bytes")
    require(saved["process_id"] != restored["process_id"], "Restore process not distinct")
    require(
        saved["payload_sha256"] == restored["payload_sha256"] == preparation["payload_sha256"],
        "Payload checksum",
    )
    require(restored["existing_completion_reused"] is True, "Completion not restored")
    require(
        saved["interruption_exercised"] is True or saved["existing_completion_reused"] is True,
        "Interruption/reuse absent",
    )
    return {
        "status": "returned_drive_proof_summary_validated",
        "remote_payload_independently_downloaded": False,
        "negative_label_permitted": False,
        "production_months_processed": 0,
    }


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("summary", type=Path)
    parser.add_argument("--revision", choices=("original", "v2"), default="original")
    args = parser.parse_args()
    folder = "gcp_drive_proof" if args.revision == "original" else "gcp_drive_proof_v2"
    preparation = json.loads((root / "outputs" / folder / "preparation.json").read_text())
    package_name = (
        "wildfire_gcp_drive_proof.zip"
        if args.revision == "original"
        else "wildfire_gcp_drive_proof_v2.zip"
    )
    verify_package(root / "outputs" / folder / package_name, preparation)
    report = verify(json.loads(args.summary.read_text()), preparation)
    summary = json.loads(args.summary.read_text())
    report.update(
        {
            "revision": args.revision,
            "summary_sha256": sha(args.summary.read_bytes()),
            "package_sha256": preparation["package_sha256"],
            "manifest_sha256": preparation["manifest_sha256"],
            "payload_sha256": preparation["payload_sha256"],
            "payload_bytes": preparation["payload_bytes"],
            "vm_reported_scientific_readbacks": sum(
                summary[k]["scientific_readbacks"] for k in ("save", "restore")
            ),
            "vm_reported_process_ids": [summary[k]["process_id"] for k in ("save", "restore")],
            "vm_reported_interruption_exercised": summary["save"]["interruption_exercised"],
            "vm_reported_off_vm_persistence_passed": summary["off_vm_persistence_proven"],
            "prepared_package_independently_rechecked": True,
            "ssh_disconnect_or_vm_restart_exercised": False,
        }
    )
    filename = (
        "gcp_drive_returned_proof.json"
        if args.revision == "original"
        else "gcp_drive_returned_proof_v2.json"
    )
    out = root / "outputs/reports/observation_coverage" / filename
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
