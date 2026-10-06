"""Offline full-period production package; never start a VM or download raw satellite data."""

import json
import zipfile
from pathlib import Path

from gcp_production_support import COMPACT_SHA, SUMMER_SHA, digest, json_bytes, read_scope
from verified_job_store import require

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/gcp_production"
REPORTS = ROOT / "outputs/reports/observation_coverage"


def build(destination=OUTPUT):
    destination.mkdir(parents=True, exist_ok=True)
    source = ROOT / "outputs/cloud_summer/l2_summer_B_bundle.zip"
    require(digest(source) == SUMMER_SHA, "Frozen summer changed")
    require(
        digest(ROOT / "scripts/cloud/l2_daily_compact.py") == COMPACT_SHA, "Frozen compact changed"
    )
    files = {
        "summer.zip": source.read_bytes(),
        "compact.py": (ROOT / "scripts/cloud/l2_daily_compact.py").read_bytes(),
        "pairs.csv": (REPORTS / "l2_training_catalogue_pairs.csv").read_bytes(),
        "sources.csv": (REPORTS / "l2_training_catalogue_granules.csv").read_bytes(),
        "july_verification.json": (REPORTS / "colab_month_received_verification.json").read_bytes(),
    }
    with zipfile.ZipFile(ROOT / "outputs/gcp_pilot/wildfire_gcp_pilot.zip") as archive:
        files["requirements.txt"] = archive.read("requirements.txt")
    for name in (
        "run_gcp_production.py",
        "gcp_production_support.py",
        "verified_job_store.py",
        "drive_job_store.py",
        "production_drive_store.py",
    ):
        files[name] = (ROOT / "scripts/cloud" / name).read_bytes()
    import hashlib

    months = [
        p.strftime("%Y-%m")
        for p in __import__("pandas").date_range("2018-01-01", "2023-12-01", freq="MS")
    ]
    front = [f"2023-{month:02d}" for month in range(8, 13)]
    order = front + sorted(set(months) - set(front) - {"2023-07"}, reverse=True)
    spec = {
        "protocol": "gcp_full_training_queue_v1",
        "training_start": "2018-01-01",
        "training_end_exclusive": "2024-01-01",
        "months": order,
        "completed_months": ["2023-07"],
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "local_raw_downloads": 0,
        "full_remaining_nominal_pairs": 18441,
        "initial_workers": 2,
        "workers_after_first_checked_day": 4,
        "four_worker_speedup_proven": False,
        "default_guest_poweroff": "explicit_cli_flag",
        "automatic_restart": False,
    }
    files["production_manifest.json"] = json_bytes(spec)
    staging = destination / "package"
    staging.mkdir(exist_ok=True)
    for name, data in files.items():
        (staging / name).write_bytes(data)
    read_scope(staging)
    pending = destination / "wildfire_gcp_production.zip.pending"
    with zipfile.ZipFile(pending, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 6, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100600 << 16
            archive.writestr(info, data)
    path = destination / "wildfire_gcp_production.zip"
    if path.exists():
        require(
            path.read_bytes() == pending.read_bytes(), "Existing production ZIP must stay frozen"
        )
        pending.unlink()
    else:
        pending.replace(path)
    with zipfile.ZipFile(path) as archive:
        require(
            archive.testzip() is None and set(archive.namelist()) == set(files),
            "Production ZIP readback",
        )
    report = {
        "status": "offline_package_checked_vm_run_pending",
        "zip_sha256": digest(path),
        "zip_bytes": path.stat().st_size,
        "manifest_sha256": digest(staging / "production_manifest.json"),
        "first_month": "2023-08",
        "queue_months": len(order),
        "negative_label_permitted": False,
        "new_raw_downloads": 0,
        "vm_started": False,
    }
    (destination / "package_report.json").write_bytes(json_bytes(report))
    print(json.dumps({**report, "package": str(path)}, indent=2))
    return path


if __name__ == "__main__":
    build()
