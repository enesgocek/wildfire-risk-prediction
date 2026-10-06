"""Package the immutable reference pilot for a short VM portability check, offline."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PILOT_SHA = "bce362d01b5a5d204c5979910703e16f3be11b0568f12b5ac8e34790aee6bbac"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    pilot = ROOT / "outputs/cloud_pilot/l2_pilot_isolated_bundle.zip"
    proof = json.loads(
        (
            ROOT / "outputs/reports/observation_coverage/colab_pilot_received_verification.json"
        ).read_text()
    )
    if (
        proof["status"] != "independent_received_cloud_pilot_verification_passed"
        or proof["bundle_zip_sha256"] != PILOT_SHA
        or sha(pilot.read_bytes()) != PILOT_SHA
    ):
        raise ValueError("Previously verified frozen pilot required")
    files = {
        "pilot.zip": pilot.read_bytes(),
        "requirements.txt": (ROOT / "scripts/cloud/requirements_l2_pilot.txt").read_bytes(),
        "run_gcp_portability.py": (ROOT / "scripts/cloud/run_gcp_portability.py").read_bytes(),
    }
    manifest = {
        "protocol": "gcp_one_swath_v1",
        "files": {n: sha(b) for n, b in files.items()},
        "negative_label_permitted": False,
        "full_years_processed": False,
    }
    files["gcp_manifest.json"] = json.dumps(manifest, indent=2).encode()
    directory = ROOT / "outputs/gcp_pilot"
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / "wildfire_gcp_pilot.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(files):
            raise ValueError("Prepared ZIP readback failed")
        if any(archive.read(name) != data for name, data in files.items()):
            raise ValueError("Prepared member differs")
    report = {
        "status": "prepared_not_cloud_executed",
        "package": str(destination),
        "package_sha256": sha(destination.read_bytes()),
        "package_bytes": destination.stat().st_size,
        "source_bytes": 194702968,
        "raw_local_downloads": 0,
        "negative_label_permitted": False,
        "full_years_processed": False,
    }
    (directory / "preparation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    build()
