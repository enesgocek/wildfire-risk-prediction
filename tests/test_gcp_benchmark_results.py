"""Reject corrupted summaries, meaningful numeric changes and changed boundaries."""

import copy
import importlib.util
import io
import json
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parents[1]
module_spec = importlib.util.spec_from_file_location(
    "gcp_received_test", ROOT / "scripts/cloud/verify_gcp_benchmark_results.py"
)
check = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(check)


@pytest.fixture
def summary():
    received = {"workers_1.zip": b"first", "workers_2.zip": b"second"}
    arms = [
        {
            "workers": n,
            "result_zip_sha256": check.sha(received[f"workers_{n}.zip"]),
            "result_zip_bytes": len(received[f"workers_{n}.zip"]),
            "completed_pairs": 6,
            "downloaded_payload_bytes": 1000,
            "cold_pair_wall_seconds": 100 / n,
            "maximum_child_peak_rss_bytes": 1000,
        }
        for n in (1, 2)
    ]
    value = {
        "status": "gcp_two_arm_benchmark_completed",
        "negative_label_permitted": False,
        "full_years_processed": False,
        "arms": arms,
        "speedup_two_vs_one": 2,
        "cold_source_bytes_total": 2000,
    }
    return value, {"source_bytes_per_arm": 1000}, received


def test_summary_ratio_recomputed_from_verified_arms(summary):
    value, spec, received = summary
    assert check.validate_summary(value, spec, received) == 2


@pytest.mark.parametrize(
    "target,key,value",
    [
        (None, "negative_label_permitted", True),
        (None, "full_years_processed", True),
        (None, "speedup_two_vs_one", 4),
        (None, "cold_source_bytes_total", 1999),
        (0, "result_zip_sha256", "0" * 64),
        (0, "result_zip_bytes", 999),
        (0, "completed_pairs", 5),
        (0, "downloaded_payload_bytes", 0),
        (0, "cold_pair_wall_seconds", float("nan")),
        (0, "cold_pair_wall_seconds", True),
        (0, "maximum_child_peak_rss_bytes", 0),
        (1, "workers", 4),
    ],
)
def test_corrupted_summary_never_passes(summary, target, key, value):
    data, spec, received = summary
    data = copy.deepcopy(data)
    (data if target is None else data["arms"][target])[key] = value
    with pytest.raises(ValueError):
        check.validate_summary(data, spec, received)


def test_unexpected_outer_path_rejected_without_extracting(tmp_path):
    path = tmp_path / "extra.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for name in (check.SUMMARY, "workers_1.zip", "../workers_2.zip"):
            archive.writestr(name, b"data")
    with pytest.raises(ValueError, match="Outer ZIP members"):
        check.read_received(path)


def test_numeric_last_digits_recorded_but_strict_arm_comparison_rejects():
    reference = pd.DataFrame(
        {
            "grid_id": ["g"],
            "aoi_area_m2": [1000.0],
            "clear_fraction_estimate": [0.5],
            "negative_label_permitted": [False],
        }
    )
    actual = reference.copy()
    actual.loc[0, "aoi_area_m2"] += 1e-7
    differences = check.compare_area_tables(actual, reference)
    assert differences[0]["different_rows"] == 1
    assert differences[0]["max_absolute_difference"] < 1e-4
    with pytest.raises(AssertionError):
        check.compare_area_tables(actual, reference, exact=True)


@pytest.mark.parametrize(
    "field,value",
    [
        ("aoi_area_m2", 1000.01),
        ("clear_fraction_estimate", 0.50000001),
        ("negative_label_permitted", True),
    ],
)
def test_real_numeric_or_policy_changes_rejected(field, value):
    reference = pd.DataFrame(
        {
            "aoi_area_m2": [1000.0],
            "clear_fraction_estimate": [0.5],
            "negative_label_permitted": [False],
        }
    )
    actual = reference.copy()
    actual.loc[0, field] = value
    with pytest.raises(AssertionError):
        check.compare_area_tables(actual, reference)


def products(tmp_path, geometry, prefix):
    stem = "fixture"
    path = tmp_path / f"{prefix}.gpkg"
    gpd.GeoDataFrame({"grid_id": ["g"]}, geometry=[geometry], crs=6933).to_file(
        path, layer="clear", driver="GPKG"
    )
    csv = b"grid_id,pixel_center_count\ng,1\n"
    data = {
        stem + "_audit.json": json.dumps(
            {
                "checked_at_utc": "fixture",
                "sources": {"fire": {"path": "source.nc", "sha256": "a" * 64}},
            }
        ).encode(),
        stem + "_grid_centers.csv": csv,
        stem + "_area_estimate.csv": b"grid_id,aoi_area_m2\ng,1\n",
        stem + "_area_estimate.gpkg": path.read_bytes(),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name, body in data.items():
            z.writestr(name, body)
    return zipfile.ZipFile(io.BytesIO(buffer.getvalue()))


def test_boundary_change_rejected_even_when_area_and_counts_match(tmp_path):
    manifest = {"pairs": [{"stem": "fixture", "sample_id": "p"}]}
    spec = {
        "source_sha256": {"p": {"fire": "a" * 64}},
        "exact_csv_sha256": {
            "p": {"grid_centers.csv": check.sha(b"grid_id,pixel_center_count\ng,1\n")}
        },
    }
    with (
        products(tmp_path, box(0, 0, 1, 1), "ref") as reference,
        products(tmp_path, box(0.01, 0, 1.01, 1), "shift") as actual,
    ):
        with pytest.raises(ValueError, match="distance too large"):
            check.compare_products(actual, reference, manifest, spec, ["clear"], tmp_path)


def test_redundant_collinear_vertex_is_reported_without_claiming_exact_match(tmp_path):
    manifest = {"pairs": [{"stem": "fixture", "sample_id": "p"}]}
    spec = {
        "source_sha256": {"p": {"fire": "a" * 64}},
        "exact_csv_sha256": {
            "p": {"grid_centers.csv": check.sha(b"grid_id,pixel_center_count\ng,1\n")}
        },
    }
    extra = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0.5), (0, 0)])
    with (
        products(tmp_path, box(0, 0, 1, 1), "ref") as reference,
        products(tmp_path, extra, "extra") as actual,
    ):
        report = check.compare_products(actual, reference, manifest, spec, ["clear"], tmp_path)
        assert report["geometry_coordinates_exactly_equal"] is False
        assert report["geometry_roundoff_differences"][0]["different_coordinate_count_rows"] == 1
        with pytest.raises(ValueError, match="between arms"):
            check.compare_products(
                actual, reference, manifest, spec, ["clear"], tmp_path, exact=True
            )
