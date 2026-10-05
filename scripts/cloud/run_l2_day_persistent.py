"""Drive storage proof for already verified data; optional bounded day wrapper."""

import argparse
import importlib.util
import json
import platform
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deploy():
    import hashlib

    recipe = json.loads((ROOT / "storage/manifest.json").read_text())
    for name, checksum in recipe["files"].items():
        target = (ROOT / name).resolve()
        if (
            not target.is_relative_to(ROOT.resolve())
            or hashlib.sha256(target.read_bytes()).hexdigest() != checksum
        ):
            raise ValueError("Storage bundle changed")
    destination = ROOT / "day_job"
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(ROOT / "storage/l2_day_bundle.zip") as archive:
        for name in archive.namelist():
            target = (destination / name).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError("Nested bundle escapes root")
            content = archive.read(name)
            if target.exists():
                if target.read_bytes() != content:
                    raise ValueError("Existing job code/reference changed")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
    return load("persistent_day", destination / "scripts/cloud/run_l2_day.py"), recipe


def run(store_root, proof_only=True, local_rehearsal=False, after_remount=False):
    day, recipe = deploy()
    store = load("snapshot_store", ROOT / "scripts/cloud/checkpoint_store.py")
    if not local_rehearsal:
        allowed = Path("/content/drive/MyDrive/wildfire-risk-prediction/colab_checkpoints")
        day.require(
            platform.system() == "Linux" and store_root.resolve() == allowed,
            "Expected the selected mounted Drive project directory",
        )
        day.require(Path("/content/drive/MyDrive").is_dir(), "Mount Drive first")
    manifest, manifest_sha = day.manifest_read()
    source = ROOT / "storage/received_day_results.zip"
    day.require(
        day.digest(source) == recipe["bootstrap_results_sha256"], "Bootstrap result changed"
    )
    published = store.save_snapshot(day, source, store_root, manifest, manifest_sha)
    selected = store.latest_snapshot(day, store_root, manifest, manifest_sha)
    day.require(selected is not None, "No committed checkpoint found")
    # A fresh output directory models a new session without deleting any existing result.
    with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
        recovered = Path(temporary) / "results"
        local_copy = Path(temporary) / "recovered.zip"
        shutil.copyfile(selected, local_copy)
        day.require(day.digest(local_copy) == day.digest(selected), "Recovered copy differs")
        day.restore_results(local_copy, manifest, manifest_sha, recovered)
        restored_count = sum(
            day.checkpoint_read(pair, recovered, manifest_sha) is not None
            for pair in manifest["pairs"]
        )
        day.require(restored_count == 8, "Storage proof requires all eight known records")
    if not proof_only:
        original_export = store.attach_store(day, store_root, manifest, manifest_sha)
        try:
            day.run(restore=selected)
        finally:
            day.export_results = original_export
    report = {
        "status": "persistent_checkpoint_roundtrip_verified",
        "environment": "local_filesystem_rehearsal" if local_rehearsal else "mounted_google_drive",
        "protocol": store.PROTOCOL,
        "manifest_sha256": manifest_sha,
        "storage_recipe_sha256": day.digest(ROOT / "storage/manifest.json"),
        "wrapper_sha256": day.digest(Path(__file__)),
        "bootstrap_results_sha256": recipe["bootstrap_results_sha256"],
        "published": published,
        "selected_payload_sha256": day.digest(selected),
        "restored_pairs": restored_count,
        "checked_after_drive_remount": after_remount,
        "raw_downloads_requested": not proof_only,
        "raw_files_uploaded": False,
        "negative_label_permitted": False,
        "limitations": [
            "Filesystem copy/readback; server durability is not guaranteed by SHA alone",
            "Proof uses existing complete data; not a new full-period processing run",
            "One writer per job; no concurrent Colab sessions in this project folder",
        ],
    }
    output = ROOT / "storage/results"
    output.mkdir(exist_ok=True)
    destination = output / "drive_storage_proof.json"
    day.atomic_json(destination, report)
    shutil.copyfile(selected, output / "l2_day_results.zip")
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-root", type=Path, required=True)
    parser.add_argument("--run-day", action="store_true")
    parser.add_argument("--local-rehearsal", action="store_true")
    parser.add_argument("--after-remount", action="store_true")
    args = parser.parse_args()
    run(
        args.store_root,
        proof_only=not args.run_day,
        local_rehearsal=args.local_rehearsal,
        after_remount=args.after_remount,
    )
