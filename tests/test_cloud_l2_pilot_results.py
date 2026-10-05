"""Received cloud reports must match the actual table and trusted reference."""

import importlib.util
import json
import zipfile
from pathlib import Path

import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "pilot_results",
    Path(__file__).resolve().parents[1] / "scripts/cloud/verify_l2_pilot_results.py",
)
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


@pytest.fixture
def received_fixture(tmp_path):
    stem = "l2_sample_2019013.0100"
    table = pd.DataFrame(
        {
            "grid_id": range(2899),
            "land": [1] * 2899,
            "daily_observation_status": ["unknown"] * 2899,
            "negative_label_permitted": [False] * 2899,
        }
    )
    sources = {
        role: {"path": f"local/{role}.nc", "bytes": size, "sha256": role * 8}
        for role, size in (("fire", 10), ("geolocation", 20))
    }
    audit = {
        "checked_at_utc": "reference",
        "sources": sources,
        "qa": 3,
        "negative_label_permitted": False,
    }
    csv = table.to_csv(index=False).encode()
    files = {
        "scripts/cloud/run_l2_pilot.py": b"fixed-worker",
        "pilot/reference/audit.json": json.dumps(audit).encode(),
        "pilot/reference/grid_centers.csv": csv,
    }
    manifest = {
        "sample_id": "SNPP:2019013.0100",
        "stem": stem,
        "bundle_files": {name: verifier.sha(data) for name, data in files.items()},
        "sources": [{"role": role, **source} for role, source in sources.items()],
    }
    raw_manifest = json.dumps(manifest).encode()
    bundle = tmp_path / "bundle.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("pilot/manifest.json", raw_manifest)
        for name, data in files.items():
            archive.writestr(name, data)
    audit["checked_at_utc"] = "cloud"
    for role, source in audit["sources"].items():
        source["path"] = f"C:\\cloud\\{role}.nc"
    versions = dict(
        line.split("==")
        for line in (verifier.ROOT / "scripts/cloud/requirements_l2_pilot.txt")
        .read_text()
        .splitlines()
        if line and not line.startswith("#")
    )
    summary = {
        "status": "passed_exact_local_reference_comparison",
        "environment": "authenticated_cloud_pilot",
        "sample_id": manifest["sample_id"],
        "manifest_sha256": verifier.sha(raw_manifest),
        "pilot_script_sha256": verifier.sha(files["scripts/cloud/run_l2_pilot.py"]),
        "negative_label_permitted": False,
        "source_bytes": 30,
        "downloaded_payload_bytes": 30,
        "elapsed_seconds": 1.5,
        "python": "3.12.13",
        "dependencies": {
            name: versions[name]
            for name in (
                "rasterio",
                "geopandas",
                "numpy",
                "pandas",
                "shapely",
                "pyproj",
                "earthaccess",
            )
        },
        "free_disk_before_bytes": 10000,
        "free_disk_after_bytes": 9000,
    }

    def write(case="valid"):
        actual_csv = csv
        if case == "changed_count":
            changed = table.copy()
            changed.loc[0, "land"] = 2
            actual_csv = changed.to_csv(index=False).encode()
        elif case == "changed_qa":
            audit["qa"] = 4
        elif case == "changed_source":
            audit["sources"]["fire"]["sha256"] = "different"
        elif case == "local_result":
            summary["environment"] = "local_reference_test"
        elif case == "negative_permission":
            summary["negative_label_permitted"] = True
        elif case == "wrong_version":
            summary["dependencies"]["numpy"] = "0.0.0"
        audit_bytes = json.dumps(audit).encode()
        summary["result_bytes_before_summary"] = len(audit_bytes) + len(actual_csv)
        results = tmp_path / "received.zip"
        with zipfile.ZipFile(results, "w") as archive:
            archive.writestr(verifier.SUMMARY, json.dumps(summary))
            archive.writestr(f"{stem}_audit.json", audit_bytes)
            archive.writestr(f"{stem}_grid_centers.csv", actual_csv)
        return results, bundle

    return write


def test_received_cloud_table_passes_with_only_timestamp_and_path_differences(received_fixture):
    result = verifier.verify(*received_fixture())
    assert result["all_grid_columns_exactly_equal"] is True
    assert result["grid_rows"] == 2899
    assert result["negative_label_permitted"] is False


@pytest.mark.parametrize(
    "case",
    [
        "changed_count",
        "changed_qa",
        "changed_source",
        "local_result",
        "negative_permission",
        "wrong_version",
    ],
)
def test_success_summary_cannot_hide_changed_data_or_identity(received_fixture, case):
    with pytest.raises((ValueError, AssertionError)):
        verifier.verify(*received_fixture(case))


@pytest.mark.parametrize("case", ["missing", "duplicate", "unexpected"])
def test_received_zip_rejects_incomplete_or_ambiguous_members(tmp_path, case):
    path = tmp_path / "received.zip"
    names = [verifier.SUMMARY, "sample_audit.json", "sample_grid_centers.csv"]
    if case == "missing":
        names.pop()
    elif case == "duplicate":
        names[-1] = names[0]
    else:
        names.append("../other.json")
    with zipfile.ZipFile(path, "w") as archive:
        for index, name in enumerate(names):
            if case == "duplicate" and index == 2:
                with pytest.warns(UserWarning, match="Duplicate"):
                    archive.writestr(name, b"content")
            else:
                archive.writestr(name, b"content")
    with pytest.raises(ValueError, match="ZIP members"):
        verifier.read_received(path, "sample")
