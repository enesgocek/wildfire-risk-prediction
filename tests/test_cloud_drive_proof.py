"""Reject misleading returned Drive proofs even when they claim success."""

import importlib.util
import io
import json
import zipfile
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "drive_proof_test",
    Path(__file__).resolve().parents[1] / "scripts/cloud/verify_l2_drive_proof.py",
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


@pytest.fixture
def proof_fixture(tmp_path, monkeypatch):
    source = b"known-result-payload"
    inner = io.BytesIO()
    manifest_bytes = json.dumps(
        {"bundle_files": {"scripts/cloud/run_l2_day.py": "frozen-worker"}}
    ).encode()
    with zipfile.ZipFile(inner, "w") as archive:
        archive.writestr("day/manifest.json", manifest_bytes)
    files = {
        "storage/l2_day_bundle.zip": inner.getvalue(),
        "storage/received_day_results.zip": source,
        "scripts/cloud/run_l2_day_persistent.py": b"known-wrapper",
    }
    recipe = {
        "protocol": "validated_zip_v1",
        "bootstrap_results_sha256": validator.sha(source),
        "files": {name: validator.sha(data) for name, data in files.items()},
    }
    raw_recipe = json.dumps(recipe).encode()
    bundle = tmp_path / "bundle.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("storage/manifest.json", raw_recipe)
        for name, data in files.items():
            archive.writestr(name, data)
    manifest_sha = validator.sha(manifest_bytes)
    name = "checkpoint_8_" + validator.sha(source)
    folder = "/content/drive/MyDrive/wildfire-risk-prediction/colab_checkpoints/" + manifest_sha
    proof = {
        "status": "persistent_checkpoint_roundtrip_verified",
        "environment": "mounted_google_drive",
        "checked_after_drive_remount": True,
        "protocol": "validated_zip_v1",
        "manifest_sha256": manifest_sha,
        "storage_recipe_sha256": validator.sha(raw_recipe),
        "wrapper_sha256": validator.sha(files["scripts/cloud/run_l2_day_persistent.py"]),
        "bootstrap_results_sha256": validator.sha(source),
        "selected_payload_sha256": validator.sha(source),
        "restored_pairs": 8,
        "raw_downloads_requested": False,
        "raw_files_uploaded": False,
        "negative_label_permitted": False,
        "limitations": [],
        "published": {
            "protocol": "validated_zip_v1",
            "manifest_sha256": manifest_sha,
            "worker_sha256": "frozen-worker",
            "payload_sha256": validator.sha(source),
            "payload_bytes": len(source),
            "completed_pairs": 8,
            "payload_name": name + ".zip",
            "saved_at_utc": "2026-10-05T00:00:00+00:00",
            "store_payload": folder + "/" + name + ".zip",
            "store_commit": folder + "/" + name + ".commit.json",
        },
    }
    calls = []

    def full_check(result, bundle, cloud):
        assert cloud and result.read_bytes() == source and bundle.read_bytes() == inner.getvalue()
        calls.append(True)
        return {"all_audits_and_csv_columns_equal": True}

    monkeypatch.setattr(validator.day_check, "verify", full_check)

    def write(case):
        selected = source
        if case == "no_remount":
            proof["checked_after_drive_remount"] = False
        elif case == "raw_upload":
            proof["raw_files_uploaded"] = True
        elif case == "wrong_folder":
            proof["published"]["store_payload"] = "/content/drive/MyDrive/private.zip"
        elif case == "payload":
            selected = b"changed"
        elif case == "local":
            proof["environment"] = "local_filesystem_rehearsal"
        result = tmp_path / "proof.zip"
        with zipfile.ZipFile(result, "w") as archive:
            archive.writestr("drive_storage_proof.json", json.dumps(proof))
            archive.writestr("l2_day_results.zip", selected)
        return result, bundle, calls

    return write


@pytest.mark.parametrize(
    "case", ["valid", "no_remount", "raw_upload", "wrong_folder", "payload", "local"]
)
def test_storage_proof_requires_scope_remount_and_full_data_validation(proof_fixture, case):
    result, bundle, calls = proof_fixture(case)
    if case == "valid":
        report = validator.verify(result, bundle)
        assert report["restored_pairs"] == 8 and calls == [True]
    else:
        with pytest.raises(ValueError):
            validator.verify(result, bundle)
        assert not calls
