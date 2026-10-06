"""Offline VM benchmark package, using frozen summer sources/code and cloud proof."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMER_SHA = "0a90b93be0ed31fa468b6ecef61851612bcd255e34caf3ccdb6adf2d6d425f7e"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    bundle = ROOT / "outputs/cloud_summer/l2_summer_B_bundle.zip"
    results = ROOT / "outputs/cloud_summer/received/l2_summer_results.zip"
    proof = json.loads(
        (
            ROOT / "outputs/reports/observation_coverage/colab_summer_received_verification.json"
        ).read_text()
    )
    if (
        proof["status"] != "independent_summer_result_readback_passed"
        or sha(bundle.read_bytes()) != SUMMER_SHA
        or sha(results.read_bytes()) != proof["results_zip_sha256"]
    ):
        raise ValueError("Verified summer bundle and received result required")
    source_sha, csv_sha = {}, {}
    with zipfile.ZipFile(bundle) as archive, zipfile.ZipFile(results) as result:
        assert archive.testzip() is None and result.testzip() is None
        manifest = json.loads(archive.read("summer/manifest.json"))
        for name, expected in manifest["bundle_files"].items():
            assert sha(archive.read(name)) == expected
            if name.startswith("scripts/"):
                assert sha((ROOT / name).read_bytes()) == expected
        for pair in manifest["pairs"]:
            audit = json.loads(result.read(f"{pair['stem']}_audit.json"))
            source_sha[pair["sample_id"]] = {
                role: value["sha256"] for role, value in audit["sources"].items()
            }
            csv_sha[pair["sample_id"]] = {
                s: sha(result.read(f"{pair['stem']}_{s}"))
                for s in ("grid_centers.csv", "scan_times.csv", "scan_grid.csv", "all_scans.csv")
            }
    files = {
        "summer.zip": bundle.read_bytes(),
        "requirements.txt": (ROOT / "scripts/cloud/requirements_l2_pilot.txt").read_bytes(),
        "run_gcp_benchmark.py": (ROOT / "scripts/cloud/run_gcp_benchmark.py").read_bytes(),
    }
    spec = {
        "protocol": "gcp_summer_two_arm_v1",
        "arms": [1, 2],
        "files": {n: sha(b) for n, b in files.items()},
        "source_bytes_per_arm": sum(s["bytes"] for p in manifest["pairs"] for s in p["sources"]),
        "source_sha256": source_sha,
        "exact_csv_sha256": csv_sha,
        "colab_results_sha256": proof["results_zip_sha256"],
        "negative_label_permitted": False,
    }
    files["benchmark_manifest.json"] = json.dumps(spec, indent=2).encode()
    out = ROOT / "outputs/gcp_benchmark"
    out.mkdir(parents=True, exist_ok=True)
    target = out / "wildfire_gcp_benchmark.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == 4 and set(archive.namelist()) == set(files)
        assert all(archive.read(n) == b for n, b in files.items())
    report = {
        "status": "prepared_not_gcp_executed",
        "package": str(target),
        "package_bytes": target.stat().st_size,
        "package_sha256": sha(target.read_bytes()),
        "source_bytes_two_arms": spec["source_bytes_per_arm"] * 2,
        "raw_local_downloads": 0,
        "negative_label_permitted": False,
    }
    (out / "preparation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
