"""Offline controller bundle; frozen original worker and validated tuning sources required."""

import json
import zipfile

from build_gcp_tuning_bundle import ORIGINAL_SCOPE, ROOT, encoded, sha, verified_inputs


def build():
    plan, metadata, month_sha, source_bytes = verified_inputs()
    result = json.loads((ROOT / "outputs/gcp_tuning/readback/tuning_readback.json").read_text())
    if result["status"] != "independent_matched_tuning_readback_passed":
        raise ValueError("Real tuning readback required")
    names = [
        "run_gcp_acceleration.py",
        "accelerated_production.py",
        "accelerated_pipeline.py",
        "accelerated_checkpoint_store.py",
        "gcp_tuning_resources.py",
    ]
    files = {name: (ROOT / "scripts/cloud" / name).read_bytes() for name in names}
    with zipfile.ZipFile(ROOT / "outputs/gcp_tuning/wildfire_gcp_tuning.zip") as reference:
        files["reference_tuning.py"] = reference.read("run_gcp_tuning.py")
    files.update({"proof_plan.json": encoded(plan), "month_manifest.zip": metadata})
    manifest = {
        "protocol": "gcp_acceleration_controller_v1",
        "files": {n: sha(b) for n, b in files.items()},
        "training_scope_sha256": ORIGINAL_SCOPE,
        "month_manifest_sha256": month_sha,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "target_cpus": 32,
        "proof_profile_pairs": 28,
        "proof_days": plan["days"],
        "source_bytes_per_profile": source_bytes,
        "raw_bytes_four_profiles": source_bytes * 4,
        "original_controller_identity_immutable": True,
        "external_controller_identity_recorded_separately": True,
        "proof_seconds": 5400,
        "vm_proof_limit_seconds": 7200,
        "production_requires_independently_verified_gate": True,
    }
    files["acceleration_manifest.json"] = encoded(manifest)
    output = ROOT / "outputs/gcp_acceleration"
    output.mkdir(parents=True, exist_ok=True)
    (output / "received").mkdir(exist_ok=True)
    target = output / "wildfire_gcp_acceleration.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 8, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == 9
        assert all(archive.read(name) == data for name, data in files.items())
    package = output / "package"
    package.mkdir(exist_ok=True)
    for name, data in files.items():
        (package / name).write_bytes(data)
    report = {
        "status": "prepared_not_vm_executed",
        "package": str(target),
        "package_sha256": sha(target.read_bytes()),
        "package_bytes": target.stat().st_size,
        "controller_manifest_sha256": sha(files["acceleration_manifest.json"]),
        "nominal_proof_raw_bytes": source_bytes * 4,
        "vm_actions": 0,
        "original_production_package_modified": False,
        "speedup_2x_3x_proven": False,
    }
    (output / "preparation.json").write_bytes(encoded(report))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
