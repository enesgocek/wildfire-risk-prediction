"""Audit the two manually supplied refresh ZIPs without replacing frozen sources."""

import csv
import hashlib
import io
import json
import socket
import stat
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from uuid import uuid4
from zipfile import ZipFile

from wildfire_risk_prediction.firms_refresh import FIELDS, categories, compare, read_delivery

ROOT = Path(__file__).resolve().parents[2]
RECEIVED = "outputs/verification/firms_refresh_2026-10-21/received"
SOURCES = (
    (
        "SNPP",
        "2018-01-01",
        "815579",
        "SV",
        "828284",
        "346d9e4e09d49d21166e98049635d64326c9330cd42b15b2f44c19456b54d5d2",
    ),
    (
        "N20",
        "2018-04-01",
        "815590",
        "J1V",
        "828274",
        "f3b0a716c335e89976fcc2620cc29dc871938411c6ad5b7f8737a4e55c6e46ec",
    ),
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline comparison")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    out = (
        ROOT
        / "outputs/reports/dataset/firms_refresh_comparison_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    pins = {}

    def retain(name, expected=None):
        path = ROOT / name
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError("Contained regular input required")
        digest = sha(path)
        if expected and digest != expected:
            raise ValueError("Pinned source changed")
        pins[name] = {"sha256": digest, "bytes": path.stat().st_size}
        return path

    retain(
        "outputs/verification/firms_refresh_2026-10-21/expected_requests.json",
        "cb7c4e02c509b5fdbcce36e951858667a185cfde1e5fb04b882ad9ce207df8b8",
    )
    for name in (
        "scripts/firms/compare_firms_refresh.py",
        "src/wildfire_risk_prediction/firms_refresh.py",
        "src/wildfire_risk_prediction/target_admission.py",
    ):
        retain(name)
    results, artifacts = [], []
    for sensor, start, old_id, code, new_id, old_sha in SOURCES:
        old_path = retain(f"data/raw/firms/{old_id}/fire_archive_{code}-C2_{old_id}.csv", old_sha)
        folder = "SNPP" if sensor == "SNPP" else "NOAA20"
        package = retain(f"{RECEIVED}/{folder}/DL_FIRE_{code}-C2_{new_id}.zip")
        with old_path.open(encoding="utf-8-sig", newline="") as stream:
            old = read_delivery(stream, start, "2023-12-31", sensor, allow_later=True)
        members = []
        with ZipFile(package) as archive:
            infos = archive.infolist()
            expected_csv = f"fire_archive_{code}-C2_{new_id}.csv"
            if len(infos) != 2 or {i.filename for i in infos} != {expected_csv, "Readme.txt"}:
                raise ValueError("Unexpected ZIP members")
            if sum(i.file_size for i in infos) > 100_000_000:
                raise ValueError("ZIP size limit")
            for info in infos:
                mode = info.external_attr >> 16
                if (
                    PurePosixPath(info.filename).name != info.filename
                    or info.flag_bits & 1
                    or stat.S_ISLNK(mode)
                ):
                    raise ValueError("Unsafe ZIP entry")
                with archive.open(info) as member:
                    digest = hashlib.file_digest(member, "sha256").hexdigest()
                members.append({"name": info.filename, "bytes": info.file_size, "sha256": digest})
            with archive.open(expected_csv) as binary:
                with io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as stream:
                    new = read_delivery(stream, start, "2023-12-31", sensor)
        result = compare(old, new)
        result.update(
            {
                "sensor": sensor,
                "start": start,
                "end_inclusive": "2023-12-31",
                "zip_members_crc_and_sha256_read": members,
                "old_categories": categories(old),
                "new_categories": categories(new),
            }
        )
        residual = out / f"{sensor}_residual_full_rows.csv"
        with residual.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("side", "multiplicity", *FIELDS))
            for side, rows in (
                ("old", old["rows"] - new["rows"]),
                ("new", new["rows"] - old["rows"]),
            ):
                for row, count in sorted(rows.items()):
                    writer.writerow((side, count, *row))
        artifacts.append(residual)
        results.append(result)
        print(
            sensor,
            "training rows",
            result["old_rows"],
            result["new_rows"],
            "multiset equal",
            result["canonical_multiset_equal"],
            flush=True,
        )
    for name, pin in pins.items():
        if sha(ROOT / name) != pin["sha256"]:
            raise ValueError("Input changed during run")
    input_manifest = out / "input_manifest.json"
    input_manifest.write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")
    artifacts.append(input_manifest)
    report = {
        "version": "firms_refresh_comparison_v1",
        "client_date": "2026-10-21",
        "audit_completed_utc": datetime.now(UTC).isoformat(),
        "status": "training_deliveries_compared_no_source_replacement",
        "scope": "Turkey request; training period only; country boundary not independently tested",
        "request_settings_evidence": "researcher screenshots and expected_requests.json",
        "exact_download_timestamp_verified": False,
        "monthly_production_version_confirmed": False,
        "network_requests": 0,
        "old_validation_rows_date_filtered_only": True,
        "final_2025_accessed": False,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "source_replaced": False,
        "cloud_job_started": False,
        "final_merge_performed": False,
        "results": results,
        "artifact_sha256": {p.name: sha(p) for p in artifacts},
    }
    report_path = out / "readback.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    loaded = json.loads(report_path.read_text(encoding="utf-8"))
    if loaded != report or any(
        sha(out / name) != digest for name, digest in report["artifact_sha256"].items()
    ):
        raise ValueError("Readback mismatch")
    closure = {
        "report_sha256": sha(report_path),
        "input_files": len(pins),
        "artifacts": len(artifacts),
        "all_inputs_rehashed_unchanged": True,
        "artifact_readback_passed": True,
        "scientific_acceptance_granted": False,
    }
    (out / "completion_readback.json").write_text(json.dumps(closure, indent=2) + "\n")
    print("Result:", out.relative_to(ROOT).as_posix())
    print("Readback SHA256:", sha(report_path))


if __name__ == "__main__":
    main()
