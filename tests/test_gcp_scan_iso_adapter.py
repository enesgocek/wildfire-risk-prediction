"""UTC parser scope, frozen scan invariants and read-only proof controls."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = load("scan_iso_adapter", ROOT / "scripts/cloud/verify_gcp_scan_iso_adapter.py")


def test_mixed_precision_preserves_ns_and_does_not_modify_global_pandas():
    values = pd.Series(["2022-09-09T22:30:00Z", "2022-09-09T22:30:01.123456789Z"], name="start_utc")
    with pytest.raises(ValueError):
        pd.to_datetime(values, utc=True)
    original = pd.to_datetime
    calls = []
    proxy = adapter.ScanPandas(pd, calls)
    parsed = proxy.to_datetime(values, utc=True)
    assert parsed.array.asi8[1] % 1_000_000_000 == 123456789
    assert proxy.Timestamp is pd.Timestamp and pd.to_datetime is original
    assert calls == [{"column": "start_utc", "rows": 2}]


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "2022-09-09T22:30:00",
        "2022-09-09T22:30:00+03:00",
        "2022-09-09T22:30:00.1234567890Z",
        123,
    ],
)
def test_invalid_time_never_becomes_missing_or_rounded(bad):
    with pytest.raises(adapter.AdapterCheck, match="Strict scan UTC schema"):
        adapter.ScanPandas(pd, []).to_datetime(pd.Series([bad], name="start_utc"), utc=True)


@pytest.mark.parametrize(
    "name,kwargs",
    [
        ("private", {"utc": True}),
        ("start_utc", {"utc": False}),
        ("start_utc", {"utc": True, "errors": "coerce"}),
    ],
)
def test_only_exact_scan_call_is_adapted(name, kwargs):
    with pytest.raises(adapter.AdapterCheck, match="Only frozen scan UTC conversion"):
        adapter.ScanPandas(pd, []).to_datetime(
            pd.Series(["2022-09-09T22:30:00Z"], name=name), **kwargs
        )


@pytest.fixture
def frozen(tmp_path, monkeypatch):
    timing = load("frozen_scan_for_adapter", ROOT / "scripts/firms/audit_l2_observation_timing.py")
    audit, area = timing.audit, timing.area
    output = tmp_path / "results"
    output.mkdir()
    monkeypatch.setattr(timing, "ROOT", tmp_path)
    monkeypatch.setattr(timing, "OUTPUT", output)
    for name in ["aoi.geojson", "grid_5km.geojson"]:
        path = tmp_path / "data/aoi" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("geography fixture")
    raw = {}
    for role, prefix in [("fire", "VNP14IMG"), ("geolocation", "VNP03IMG")]:
        path = tmp_path / (prefix + ".A2022252.2230.002.2022253070012.nc")
        path.write_bytes(b"raw fixture")
        raw[role] = {"path": path.name, "sha256": audit.digest(path)}
    stem = audit.sample_stem("SNPP", "2022252.2230")
    prior_path = output / (stem + "_audit.json")
    prior_path.write_text(
        json.dumps(
            {
                "sensor": "SNPP",
                "pair_key": "2022252.2230",
                "sources": raw,
                "script_sha256": audit.digest(Path(audit.__file__)),
                "aoi_sha256": audit.digest(tmp_path / "data/aoi/aoi.geojson"),
                "grid_sha256": audit.digest(tmp_path / "data/aoi/grid_5km.geojson"),
                "start_utc": "2022-09-09T22:30:00Z",
            }
        )
    )
    base = (
        pd.Timestamp("2022-09-09T22:30:00Z") - pd.Timestamp("1993-01-01T00:00:00Z")
    ).total_seconds() + 37
    starts = np.array([base, base + 1.125])
    raw_fields = {
        "scan_start_time": starts,
        "scan_end_time": starts + 0.5,
        "ev_mid_time": starts + 0.25,
        "scan_quality": np.array([0, 0]),
        "sensor_mode": np.array([4, 5]),
    }
    times = pd.DataFrame(
        {
            "scan_index": [0, 1],
            "first_native_row": [0, 32],
            "geolocation_scan_quality": [0, 0],
            "sensor_mode": [4, 5],
            **{
                name: area.tai93_utc(raw_fields[band], 37).astype(str)
                for name, band in [
                    ("start_utc", "scan_start_time"),
                    ("end_utc", "scan_end_time"),
                    ("ev_mid_utc", "ev_mid_time"),
                ]
            },
        }
    )
    times_path = output / (stem + "_scan_times.csv")
    times.to_csv(times_path, index=False)
    pd.DataFrame(
        [
            {
                "grid_id": "g1",
                **{name: 0 for name in timing.COUNTS},
                "daily_observation_status": "unknown",
                "negative_label_permitted": False,
            }
        ]
    ).to_csv(output / (stem + "_grid_centers.csv"), index=False)
    (output / (stem + "_area_estimate.json")).write_text(
        json.dumps(
            {
                "sources": {
                    "previous_audit_sha256": audit.digest(prior_path),
                    "scan_times_sha256": audit.digest(times_path),
                    "script_sha256": audit.digest(Path(area.__file__)),
                }
            }
        )
    )

    def layer(stack, path, field):
        if field.startswith("scan_line_attributes/"):
            data = raw_fields[field.split("/")[-1]]
            return SimpleNamespace(read=lambda band: data.reshape(1, -1))
        dtype = (
            "uint8" if field == "fire_mask" else "uint32" if field == "algorithm_QA" else "float64"
        )
        return SimpleNamespace(
            shape=(64, 1),
            height=64,
            width=1,
            dtypes=(dtype,),
            tags=lambda: {"TAI93_leapseconds": "37", "OrbitNumber": "42"},
            read=lambda band, window=None: np.zeros((64, 1), dtype=dtype),
        )

    monkeypatch.setattr(audit, "layer", layer)
    monkeypatch.setattr(audit, "validate_pair", lambda *args: None)
    monkeypatch.setattr(
        audit, "pilot_selection", lambda lon, lat, aoi: (None, None, np.zeros_like(lon, dtype=bool))
    )
    return timing, tmp_path, raw_fields


def test_unmodified_scan_routine_reproduces_error_then_passes_all_invariants(frozen):
    timing, root, _ = frozen
    original_parser = pd.to_datetime
    original_source = timing.source_scans
    before = {p: adapter.digest(p) for p in root.rglob("*") if p.is_file()}
    with pytest.raises(ValueError):
        timing.source_scans("SNPP", "2022252.2230", None, None, {"g1"})
    calls = []
    with adapter.scan_parser(timing, calls):
        centers, scans, provenance, begin = timing.source_scans(
            "SNPP", "2022252.2230", None, None, {"g1"}
        )
    assert len(centers) == 0 and len(scans) == 2
    assert provenance["native_grid_counts_exact_match"] is True
    assert begin == pd.Timestamp("2022-09-09T00:00:00Z")
    assert timing.source_scans is original_source and timing.pd is pd
    assert pd.to_datetime is original_parser and len(calls) == 3
    assert before == {p: adapter.digest(p) for p in root.rglob("*") if p.is_file()}


def test_adapter_does_not_bypass_original_quality_guards_and_restores_namespace(frozen):
    timing, _, fields = frozen
    fields["sensor_mode"][0] = 99
    with pytest.raises(ValueError, match="Unknown sensor mode"):
        with adapter.scan_parser(timing, []):
            timing.source_scans("SNPP", "2022252.2230", None, None, {"g1"})
    assert timing.pd is pd


def test_adapter_does_not_bypass_original_time_equalities(frozen):
    timing, _, fields = frozen
    fields["scan_start_time"] += 0.000001
    with pytest.raises(ValueError, match="Time mismatch: start_utc"):
        with adapter.scan_parser(timing, []):
            timing.source_scans("SNPP", "2022252.2230", None, None, {"g1"})
    assert timing.pd is pd


def test_unknown_scientific_implementation_is_rejected(tmp_path):
    source = tmp_path / "different.py"
    source.write_text("# Different source")
    timing = SimpleNamespace(__file__=str(source), pd=pd)
    with pytest.raises(adapter.AdapterCheck, match="Pinned scan implementation"):
        with adapter.scan_parser(timing, []):
            raise AssertionError("Untrusted source entered")


def test_changed_helper_or_evidence_is_rejected_before_import(tmp_path):
    (tmp_path / "diagnose_gcp_v2_scan_times.py").write_text("raise RuntimeError('SECRET')")
    with pytest.raises(adapter.AdapterCheck, match="Pinned probe"):
        adapter.checked_probe(tmp_path)
    (tmp_path / adapter.EVIDENCE_NAME).write_text("{}")
    with pytest.raises(adapter.AdapterCheck, match="Pinned original replay evidence"):
        adapter.verify(tmp_path, None, None)
