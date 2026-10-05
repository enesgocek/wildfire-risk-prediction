"""Validate a returned storage proof without executing any received code."""

import argparse
import hashlib
import importlib.util
import io
import json
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "day_result_validator", Path(__file__).with_name("verify_l2_day_results.py")
)
day_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(day_check)
require = day_check.require


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(result, bundle, local=False):
    with zipfile.ZipFile(bundle) as archive:
        raw_recipe = archive.read("storage/manifest.json")
        recipe = json.loads(raw_recipe)
        require(
            set(archive.namelist()) == set(recipe["files"]) | {"storage/manifest.json"},
            "Unexpected storage bundle members",
        )
        require(len(archive.namelist()) == len(set(archive.namelist())), "Duplicate bundle members")
        for name, checksum in recipe["files"].items():
            require(sha(archive.read(name)) == checksum, "Storage bundle identity differs")
        frozen_bundle = archive.read("storage/l2_day_bundle.zip")
        bootstrap = archive.read("storage/received_day_results.zip")
    with zipfile.ZipFile(io.BytesIO(frozen_bundle)) as archive:
        raw_manifest = archive.read("day/manifest.json")
        frozen_manifest = json.loads(raw_manifest)
    manifest_sha = sha(raw_manifest)
    with zipfile.ZipFile(result) as archive:
        infos = archive.infolist()
        require(
            len(infos) == 2
            and {i.filename for i in infos} == {"drive_storage_proof.json", "l2_day_results.zip"},
            "Unexpected proof ZIP members",
        )
        require(all(0 < info.file_size < 5_000_000 for info in infos), "Unexpected proof size")
        require(archive.testzip() is None, "Proof CRC failed")
        proof = json.loads(archive.read("drive_storage_proof.json"))
        selected = archive.read("l2_day_results.zip")
    require(proof["status"] == "persistent_checkpoint_roundtrip_verified", "Storage proof failed")
    require(
        proof["environment"] == ("local_filesystem_rehearsal" if local else "mounted_google_drive"),
        "Storage environment differs",
    )
    require(
        local or proof["checked_after_drive_remount"] is True, "Remount readback not demonstrated"
    )
    require(proof["protocol"] == recipe["protocol"] == "validated_zip_v1", "Protocol differs")
    require(
        proof["manifest_sha256"] == manifest_sha
        and proof["storage_recipe_sha256"] == sha(raw_recipe),
        "Storage manifest/recipe differs",
    )
    require(
        proof["wrapper_sha256"] == recipe["files"]["scripts/cloud/run_l2_day_persistent.py"],
        "Storage wrapper identity differs",
    )
    require(
        proof["bootstrap_results_sha256"] == recipe["bootstrap_results_sha256"] == sha(bootstrap),
        "Bootstrap identity differs",
    )
    require(proof["selected_payload_sha256"] == sha(selected), "Recovered payload differs")
    require(
        proof["restored_pairs"] == 8
        and proof["raw_downloads_requested"] is False
        and proof["raw_files_uploaded"] is False
        and proof["negative_label_permitted"] is False,
        "Storage proof scope differs",
    )
    published = proof["published"]
    require(
        published["protocol"] == proof["protocol"]
        and published["manifest_sha256"] == manifest_sha
        and published["worker_sha256"]
        == frozen_manifest["bundle_files"]["scripts/cloud/run_l2_day.py"]
        and published["payload_sha256"] == sha(bootstrap)
        and published["payload_bytes"] == len(bootstrap)
        and published["completed_pairs"] == 8,
        "Published checkpoint identity differs",
    )
    name = f"checkpoint_8_{sha(bootstrap)}"
    require(published["payload_name"] == name + ".zip", "Saved payload name differs")
    saved_at = datetime.fromisoformat(published["saved_at_utc"])
    require(saved_at.tzinfo is not None, "Saved timestamp missing timezone")
    if not local:
        folder = "/content/drive/MyDrive/wildfire-risk-prediction/colab_checkpoints/" + manifest_sha
        require(
            published["store_payload"] == folder + "/" + name + ".zip"
            and published["store_commit"] == folder + "/" + name + ".commit.json",
            "Drive path differs from selected project folder",
        )
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "l2_day_results.zip"
        reference = root / "l2_day_bundle.zip"
        source.write_bytes(selected)
        reference.write_bytes(frozen_bundle)
        day_result = day_check.verify(source, reference, cloud=True)
    return {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "independent_persistent_storage_proof_verified",
        "environment": proof["environment"],
        "proof_zip_sha256": sha(result.read_bytes()),
        "bundle_sha256": sha(bundle.read_bytes()),
        "verifier_sha256": sha(Path(__file__).read_bytes()),
        "restored_pairs": 8,
        "all_audits_and_columns_equal": day_result["all_audits_and_csv_columns_equal"],
        "checked_after_drive_remount": proof["checked_after_drive_remount"],
        "saved_result_bytes": published["payload_bytes"],
        "negative_label_permitted": False,
        "limitations": proof["limitations"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proof_zip", type=Path)
    parser.add_argument(
        "--bundle", type=Path, default=ROOT / "outputs/cloud_drive/l2_drive_bundle.zip"
    )
    parser.add_argument("--local-rehearsal", action="store_true")
    args = parser.parse_args()
    report = verify(args.proof_zip, args.bundle, local=args.local_rehearsal)
    name = (
        "drive_storage_local_rehearsal.json"
        if args.local_rehearsal
        else "drive_storage_received_verification.json"
    )
    destination = ROOT / "outputs/reports/observation_coverage" / name
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
