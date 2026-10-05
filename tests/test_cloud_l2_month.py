"""Monthly immutable storage, resumption, scope and spatial/time union invariants."""

import ast
import importlib.util
import json
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import shapely

ROOT = Path(__file__).parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/cloud" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


month = load("test_month", "run_l2_month.py")
builder = load("test_month_builder", "build_l2_month_bundle.py")


def test_overlap_is_union_not_area_sum_and_clips_to_aoi():
    domain = np.array([shapely.box(0, 0, 10, 10)], dtype=object)
    left = np.array([shapely.box(-10, 0, 7, 10)], dtype=object)
    right = np.array([shapely.box(3, 0, 20, 10)], dtype=object)
    result = month.compact.union_arrays([left, right], domain)
    assert shapely.area(result).tolist() == [100]
    assert shapely.equals(result, domain).all()


def test_union_rejects_mismatched_grid_dimensions():
    with pytest.raises(ValueError, match="dimensions"):
        month.compact.union_arrays(
            [np.array([], dtype=object)], np.array([shapely.box(0, 0, 1, 1)])
        )


def test_time_sweep_overlap_and_longest_gap():
    scale = 10**9
    union, gap = month.compact.sweep(
        [(2 * scale, 5 * scale), (3 * scale, 7 * scale)], 0, 10 * scale
    )
    assert (union, gap) == (5, 3)
    assert month.compact.sweep([], 0, 10 * scale) == (0, 10)


@pytest.mark.parametrize("interval", [(0, 5), (-1, 5), (2, 11), (5, 5), (5, 4)])
def test_time_sweep_excludes_boundary_and_invalid_envelopes(interval):
    with pytest.raises(ValueError):
        month.compact.sweep([interval], 0, 10)


def test_notebook_one_month_job_and_private_login():
    book = builder.notebook("a" * 64)
    source = "\n".join("".join(c["source"]) for c in book["cells"] if c["cell_type"] == "code")
    for cell in book["cells"]:
        if cell["cell_type"] == "code":
            ast.parse("".join(cell["source"]))
            assert cell["outputs"] == [] and cell["execution_count"] is None
    assert "run_l2_month.py" in source and "run_l2_summer.py" not in source
    assert "month_2023_07" in source and "'--budget-gb', '20'" in source
    assert "getpass.getpass" in source and "finally:" in source and "auth_env.clear()" in source
    assert "system_site_packages=False" in source and "--verify-only" in source
    assert "l2_month_2023_07_results.zip" in source


@pytest.fixture
def daily(monkeypatch, tmp_path):
    monkeypatch.setattr(month, "ROOT", tmp_path)
    output = tmp_path / "month/daily/2023-07-01"
    output.mkdir(parents=True)
    pairs = [{"sample_id": "SNPP:2023182.0012"}]
    report = {"pair_ids": [pairs[0]["sample_id"]]}
    for name in month.compact.NAMES:
        (output / name).write_text(json.dumps(report) if name == "report.json" else "trusted table")
    # Real numeric validation is exercised in the independent 2,899-grid rehearsal;
    # this fixture isolates copy/commit ordering and fresh-session restore.
    monkeypatch.setattr(month.compact, "validate_day", lambda *args: report)
    return output, pairs, tmp_path / "store"


def test_save_and_fresh_session_restore(daily):
    output, pairs, store = daily
    saved = month.save_day("2023-07-01", output, store, "a" * 64, pairs, 1000000)
    fresh = month.ROOT / "fresh"
    assert month.restore_day("2023-07-01", pairs, store, "a" * 64, fresh) == saved
    assert all((fresh / n).read_bytes() == (output / n).read_bytes() for n in month.compact.NAMES)


@pytest.mark.parametrize("change", ["payload", "worker", "manifest", "pairs", "permission", "name"])
def test_corrupt_or_wrong_scope_day_is_not_reused(daily, change):
    output, pairs, store = daily
    record = month.save_day("2023-07-01", output, store, "a" * 64, pairs, 1000000)
    folder = store / "days" / ("a" * 64)
    marker = next(folder.glob("*.commit.json"))
    if change == "payload":
        (folder / record["payload_name"]).write_bytes(b"bad")
    else:
        fields = {
            "worker": "worker_sha256",
            "manifest": "manifest_sha256",
            "pairs": "pair_ids",
            "permission": "negative_label_permitted",
            "name": "payload_name",
        }
        record[fields[change]] = True if change == "permission" else "other"
        marker.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        month.restore_day("2023-07-01", pairs, store, "a" * 64, month.ROOT / "fresh")


def test_zip_without_commit_is_not_completed_day(daily):
    output, pairs, store = daily
    month.save_day("2023-07-01", output, store, "a" * 64, pairs, 1000000)
    next((store / "days" / ("a" * 64)).glob("*.commit.json")).unlink()
    assert month.restore_day("2023-07-01", pairs, store, "a" * 64, month.ROOT / "fresh") is None


def test_budget_failure_preserves_work_and_writes_no_commit(daily):
    output, pairs, store = daily
    with pytest.raises(ValueError, match="budget exceeded"):
        month.save_day("2023-07-01", output, store, "a" * 64, pairs, 1)
    assert all((output / n).is_file() for n in month.compact.NAMES)
    assert not list(store.rglob("*.commit.json"))


def test_corrupt_copy_never_marks_completed(daily, monkeypatch):
    output, pairs, store = daily

    def fail(*args):
        raise ValueError("copy verification failed")

    monkeypatch.setattr(month.summer.storage, "copy_verified", fail)
    with pytest.raises(ValueError, match="copy verification"):
        month.save_day("2023-07-01", output, store, "a" * 64, pairs, 1000000)
    assert not list(store.rglob("*.commit.json"))
    assert all((output / n).is_file() for n in month.compact.NAMES)


def test_untrusted_zip_rejected_before_extract(daily):
    _, pairs, _ = daily
    payload = month.ROOT / "bad.zip"
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("../escape", "bad")
    with pytest.raises(ValueError, match="Unexpected daily ZIP"):
        month.restore_day_zip(payload, month.ROOT / "fresh", "2023-07-01", pairs, {})
    assert not (month.ROOT.parent / "escape").exists()


def test_completed_days_do_not_open_pair_journals_or_download(monkeypatch, tmp_path):
    monkeypatch.setattr(month, "ROOT", tmp_path)
    (tmp_path / "month").mkdir()
    (tmp_path / "month/bootstrap_manifest.json").write_text(json.dumps({"pairs": []}))
    manifest = {"pairs": []}
    monkeypatch.setattr(month, "manifest_read", lambda: (manifest, "a" * 64))
    monkeypatch.setattr(month, "validate_cloud", lambda *args: None)
    monkeypatch.setattr(month, "restore_day", lambda day, *args: {"day": day})
    exports = []
    monkeypatch.setattr(month, "export_summary", lambda m, s, r: exports.append(len(r)))

    def forbidden(*args):
        raise AssertionError("Completed day must skip raw/pair work")

    monkeypatch.setattr(month, "bootstrap", forbidden)
    monkeypatch.setattr(month.summer, "restore_store", forbidden)
    monkeypatch.setattr(month.summer, "download_pair", forbidden)
    month.run(tmp_path / "store", 1000000, verify_only=True)
    assert exports[-1] == 31


def test_cleanup_cannot_touch_external_input_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(month, "ROOT", tmp_path / "job")
    inputs = tmp_path / "originals"
    inputs.mkdir()
    original = inputs / "keep.txt"
    original.write_text("keep")
    with pytest.raises(ValueError, match="outside month work"):
        month.clean_work("2023-07-01", [], inputs)
    assert original.read_text() == "keep"


@pytest.fixture
def scope(monkeypatch, tmp_path):
    monkeypatch.setattr(month, "ROOT", tmp_path)
    directory = tmp_path / "month"
    directory.mkdir()
    metadata = directory / "metadata.json"
    metadata.write_text("{}")
    bootstrap = directory / "bootstrap_results.zip"
    bootstrap.write_bytes(b"frozen bootstrap")
    pairs, rows = [], []
    for n in range(264):
        key = f"2023182.{n // 60:02d}{n % 60:02d}"
        stem = month.summer.audit.sample_stem("SNPP", key)
        sources = []
        for role, product in (("fire", "VNP14IMG"), ("geolocation", "VNP03IMG")):
            filename = f"{product}.A{key}.002.2023197000000.nc"
            url = "https://data.lpdaac.earthdatacloud.nasa.gov/" + filename
            source = {
                "role": role,
                "filename": filename,
                "url": url,
                "bytes": 1,
                "metadata_sha256": month.digest(metadata),
            }
            sources.append(source)
            rows.append(
                {
                    "sensor": "SNPP",
                    "pair_key": key,
                    "role": role,
                    "filename": filename,
                    "data_url": url,
                }
            )
        pairs.append(
            {
                "sample_id": "SNPP:" + key,
                "sensor": "SNPP",
                "key": key,
                "stem": stem,
                "start_utc": f"2023-07-01T{n // 60:02d}:{n % 60:02d}:00Z",
                "sources": sources,
                "metadata": {"fire": "month/metadata.json", "geolocation": "month/metadata.json"},
            }
        )
    pd.DataFrame(rows).to_csv(directory / "catalogue_new.csv", index=False)
    manifest = {
        "scope": "2023-07",
        "days": month.DAYS,
        "pairs": pairs,
        "negative_label_permitted": False,
        "bundle_files": {},
        "new_source_bytes": 528,
        "bootstrap_results_sha256": month.digest(bootstrap),
    }
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest))
    return manifest, path


def test_fixed_scope_accepts_exact_pair_keys_including_trailing_zero(scope):
    manifest, _ = scope
    assert month.manifest_read()[0] == manifest


@pytest.mark.parametrize(
    "change", ["month", "bootstrap_day", "duplicate", "size_total", "host", "label"]
)
def test_wrong_month_catalogue_or_download_host_rejected(scope, change):
    manifest, path = scope
    if change == "month":
        manifest["scope"] = "2024-07"
    elif change == "bootstrap_day":
        manifest["pairs"][0]["start_utc"] = "2023-07-16T00:00:00Z"
    elif change == "duplicate":
        manifest["pairs"][0] = manifest["pairs"][1]
    elif change == "size_total":
        manifest["new_source_bytes"] += 1
    elif change == "host":
        manifest["pairs"][0]["sources"][0]["url"] = "https://example.com/file.nc"
    else:
        manifest["negative_label_permitted"] = True
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        month.manifest_read()


def test_interrupted_day_reuses_pair_commit_without_downloading(monkeypatch, tmp_path):
    monkeypatch.setattr(month, "ROOT", tmp_path)
    (tmp_path / "month").mkdir()
    (tmp_path / "month/bootstrap_manifest.json").write_text(json.dumps({"pairs": []}))
    pair = {
        "sample_id": "SNPP:2023182.0012",
        "stem": "l2_sample_2023182.0012",
        "start_utc": "2023-07-01T00:12:00Z",
    }
    manifest = {"pairs": [pair]}
    monkeypatch.setattr(month, "manifest_read", lambda: (manifest, "a" * 64))
    monkeypatch.setattr(month, "validate_cloud", lambda *args: None)
    monkeypatch.setattr(
        month, "restore_day", lambda day, *args: {"day": day} if day == "2023-07-16" else None
    )
    recovered = []
    monkeypatch.setattr(month.summer, "restore_store", lambda p, *args: recovered.append(p) or True)
    monkeypatch.setattr(month.summer, "checkpoint_read", lambda *args: {"already_validated": True})
    monkeypatch.setattr(month.summer, "cleanup_pair", lambda *args: None)
    monkeypatch.setattr(month.compact, "reduce_day", lambda *args, **kwargs: None)
    monkeypatch.setattr(month, "save_day", lambda day, *args: {"day": day})
    monkeypatch.setattr(month, "clean_work", lambda *args: None)
    monkeypatch.setattr(month, "export_summary", lambda *args: None)

    def forbidden(*args):
        raise AssertionError("Saved pair must not be downloaded or saved twice")

    monkeypatch.setattr(month.summer, "download_pair", forbidden)
    monkeypatch.setattr(month, "save_pair", forbidden)
    month.run(tmp_path / "store", 1000000, stop_after=1)
    assert recovered == [pair]


@pytest.fixture
def numeric_day(monkeypatch, tmp_path):
    compact = month.compact
    geometry = gpd.GeoDataFrame(
        {"grid_id": ["a", "b"]},
        geometry=[shapely.box(0, 0, 1, 1), shapely.box(1, 0, 2, 1)],
        crs=6933,
    )
    parts_path = tmp_path / "parts.json"
    parts_path.write_text("test geographic identity")
    monkeypatch.setattr(compact.area, "load_parts", lambda: (parts_path, geometry))
    areas = pd.DataFrame({"grid_id": ["a", "b"], "aoi_area_m2": [1.0, 1.0]})
    for group in compact.area.GROUPS:
        areas[f"{group}_area_estimate_m2"] = 0.4
        areas[f"{group}_fraction_estimate"] = 0.4
    areas["method"] = compact.area.METHOD
    areas["daily_observation_status"] = "unknown"
    areas["negative_label_permitted"] = False
    row = {
        "sensor": "SNPP",
        "pair_key": "2023182.0100",
        "scan_index": 0,
        "start_utc": "2023-07-01T01:00:00Z",
        "end_utc": "2023-07-01T01:05:00Z",
        "day_window_status": "inside",
        "orbit_id": "SNPP:1",
        "sensor_mode": 4,
    }
    scans = pd.DataFrame([row])
    grid = pd.DataFrame([{**row, "grid_id": "a", **dict.fromkeys(compact.timing.COUNTS, 0)}])
    centers = compact.timing.summarize_grid(grid, {"a", "b"}, pd.Timestamp("2023-07-01T00:00Z"))
    for name, table in (
        ("area.csv", areas),
        ("centers.csv", centers),
        ("scan_grid.csv", grid),
        ("scans.csv", scans),
    ):
        table.to_csv(tmp_path / name, index=False)
    report = {
        "day": "2023-07-01",
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "method": compact.area.METHOD,
        "compact_code_sha256": compact.digest(Path(compact.__file__)),
        "parts_sha256": compact.digest(parts_path),
        "pair_ids": ["SNPP:2023182.0100"],
        "outputs_sha256": {n: compact.digest(tmp_path / n) for n in compact.NAMES[:-1]},
    }
    (tmp_path / "report.json").write_text(json.dumps(report))
    return tmp_path, report


def test_daily_numeric_readback_counts_and_empty_cell_time(numeric_day):
    output, report = numeric_day
    assert month.compact.validate_day(output, "2023-07-01", report["pair_ids"]) == report


@pytest.mark.parametrize(
    "change", ["label", "boundary", "time_lineage", "negative_count", "double_area", "gap"]
)
def test_numeric_inconsistency_rejected_even_if_csv_hash_is_updated(numeric_day, change):
    output, report = numeric_day
    filename = {
        "label": "centers.csv",
        "boundary": "scans.csv",
        "time_lineage": "scans.csv",
        "negative_count": "scan_grid.csv",
        "double_area": "area.csv",
        "gap": "centers.csv",
    }[change]
    table = pd.read_csv(output / filename, dtype={"pair_key": str})
    if change == "label":
        table.loc[0, "negative_label_permitted"] = True
    elif change == "boundary":
        table.loc[0, "day_window_status"] = "outside"
    elif change == "time_lineage":
        table.loc[0, "end_utc"] = "2023-07-01T01:06:00Z"
    elif change == "negative_count":
        table.loc[0, month.compact.timing.COUNTS[0]] = -1
    elif change == "double_area":
        table.loc[0, "reconstructed_domain_area_estimate_m2"] = 2
    else:
        table.loc[0, "any_center_longest_envelope_gap_seconds"] += 1
    table.to_csv(output / filename, index=False)
    report["outputs_sha256"][filename] = month.compact.digest(output / filename)
    (output / "report.json").write_text(json.dumps(report))
    with pytest.raises(ValueError):
        month.compact.validate_day(output, "2023-07-01", report["pair_ids"])
