"""Build a separate 4/8/12/4 tuning package from independently verified products."""

import hashlib
import io
import json
import re
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIVED_SHA = "1801d0275ae82b6bb98fe7e3caff7ba7e3758c32ae481ecb9ad6e1ed7f769c33"
ORIGINAL_SCOPE = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
DAYS = ["2023-10-13", "2023-10-14", "2023-10-15"]
CSV_NAMES = ("grid_centers.csv", "scan_times.csv", "scan_grid.csv", "all_scans.csv")
ARMS = [["four_before", 4], ["eight", 8], ["twelve", 12], ["four_after", 4]]


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def reference(pair, audit, hashes):
    require(audit["sample_id"] == pair["sample_id"], "Reference identity")
    require(audit["negative_label_permitted"] is False, "Reference policy")
    source_sha = {}
    for source in pair["sources"]:
        actual = audit["sources"][source["role"]]
        require(actual["bytes"] == source["bytes"], "Reference source size")
        require(actual["cmr_metadata_sha256"] == source["metadata_sha256"], "Reference UMM")
        source_sha[source["role"]] = actual["sha256"]
    exact = {suffix: hashes[f"{pair['stem']}_{suffix}"] for suffix in CSV_NAMES}
    require(
        all(re.fullmatch(r"[a-f0-9]{64}", v) for v in [*source_sha.values(), *exact.values()]),
        "Reference SHA format",
    )
    return {"source_sha256": source_sha, "exact_csv_sha256": exact}


def verified_inputs():
    source = ROOT / "outputs/gcp_production/received/gcp_production_first_session_results.tar.gz"
    report = ROOT / (
        "outputs/gcp_production_diagnosis/session_2026-10-08/"
        "scientific_readback/scientific_readback_report.json"
    )
    proof = json.loads(report.read_text())
    require(
        proof["status"] == "independent_first_session_result_readback_passed"
        and proof["received_sha256"] == sha(source.read_bytes()) == RECEIVED_SHA
        and proof["queue_manifest_sha256"] == ORIGINAL_SCOPE,
        "Independent received-product proof required",
    )
    original = ROOT / "outputs/gcp_production/package"
    require(
        sha((original / "production_manifest.json").read_bytes()) == ORIGINAL_SCOPE,
        "Frozen original scope",
    )
    spec = json.loads((original / "production_manifest.json").read_text())
    for name, checksum in spec["files"].items():
        require(
            Path(name).name == name and sha((original / name).read_bytes()) == checksum,
            "Frozen original file",
        )
    with tarfile.open(source, "r:gz") as archive:

        def read(name):
            member = archive.getmember(name)
            require(member.isfile() and 0 < member.size < 10_000_000, "Reference member")
            return archive.extractfile(member).read()

        metadata = read("months/2023-10/manifest.zip")
        with zipfile.ZipFile(io.BytesIO(metadata)) as zipped:
            require(zipped.testzip() is None, "Metadata CRC")
            month_bytes = zipped.read("month.json")
            month = json.loads(month_bytes)
        selected = [p for p in month["pairs"] if p["start_utc"][:10] in DAYS]
        require(
            len(selected) == 28 and len({p["sample_id"] for p in selected}) == 28,
            "Complete matched population",
        )
        references = {}
        for day in DAYS[:2]:
            with zipfile.ZipFile(io.BytesIO(read(f"months/2023-10/daily_archives/{day}.zip"))) as z:
                require(z.testzip() is None, "Daily reference CRC")
                journals = {s["sample_id"]: s for s in json.loads(z.read("report.json"))["sources"]}
            pairs = [p for p in selected if p["start_utc"].startswith(day)]
            require(set(journals) == {p["sample_id"] for p in pairs}, "Full reference day")
            for pair in pairs:
                saved = journals[pair["sample_id"]]
                references[pair["sample_id"]] = reference(
                    pair, saved["audit"], saved["input_sha256"]
                )
        for pair in selected:
            if not pair["start_utc"].startswith(DAYS[-1]):
                continue
            prefix = f"days/{DAYS[-1]}/inputs/{pair['stem']}_"
            audit = json.loads(read(prefix + "audit.json"))
            checkpoint = json.loads(read(prefix + "checkpoint.json"))
            require(checkpoint["sample_id"] == pair["sample_id"], "Saved checkpoint identity")
            hashes = checkpoint["outputs"]
            for suffix in CSV_NAMES:
                require(
                    sha(read(prefix + suffix)) == hashes[f"{pair['stem']}_{suffix}"],
                    "Saved checkpoint CSV SHA",
                )
            references[pair["sample_id"]] = reference(pair, audit, hashes)
    plan = {
        "days": DAYS,
        "sample_ids": [p["sample_id"] for p in selected],
        "references": references,
        "reference_archive_sha256": RECEIVED_SHA,
        "independent_readback_report_sha256": sha(report.read_bytes()),
    }
    return plan, metadata, sha(month_bytes), sum(s["bytes"] for p in selected for s in p["sources"])


def build():
    plan, metadata, month_sha, source_bytes = verified_inputs()
    files = {
        name: (ROOT / "scripts/cloud" / name).read_bytes()
        for name in ("run_gcp_tuning.py", "gcp_tuning_resources.py")
    }
    files.update({"tuning_plan.json": encoded(plan), "month_manifest.zip": metadata})
    spec = {
        "protocol": "gcp_parallel_tuning_v1",
        "arms": ARMS,
        "files": {n: sha(b) for n, b in files.items()},
        "original_production_scope_sha256": ORIGINAL_SCOPE,
        "production_month_manifest_sha256": month_sha,
        "nominal_raw_download_bytes": source_bytes * len(ARMS),
        "source_bytes_per_arm": source_bytes,
        "matched_pairs_per_arm": 28,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "limits": {"vm_seconds": 7200, "benchmark_seconds": 5400, "min_free_bytes": 4 * 2**30},
        "production_months_added": 0,
    }
    files["tuning_manifest.json"] = encoded(spec)
    output = ROOT / "outputs/gcp_tuning"
    output.mkdir(parents=True, exist_ok=True)
    target = output / "wildfire_gcp_tuning.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 8, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(target) as archive:
        require(archive.testzip() is None and set(archive.namelist()) == set(files), "Bundle CRC")
        require(all(archive.read(n) == data for n, data in files.items()), "Bundle readback")
    (output / "received").mkdir(exist_ok=True)
    result = {
        "status": "prepared_not_vm_executed",
        "package": str(target),
        "package_sha256": sha(target.read_bytes()),
        "package_bytes": target.stat().st_size,
        "tuning_scope_sha256": sha(files["tuning_manifest.json"]),
        "raw_bytes_per_arm": source_bytes,
        "nominal_raw_download_bytes": source_bytes * len(ARMS),
        "raw_local_downloads": 0,
        "production_package_modified": False,
    }
    (output / "preparation.json").write_bytes(encoded(result))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    build()
