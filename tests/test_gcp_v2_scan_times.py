"""Offline scan diagnostic preserves native time and excludes private errors."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "v2_scan_probe", ROOT / "scripts/cloud/diagnose_gcp_v2_scan_times.py"
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_mixed_precision_reproduces_default_error_without_changing_native_ns():
    values = ["2022-09-09 22:30:00.123456789+00:00", "2022-09-09 22:30:01+00:00"]
    native = pd.DatetimeIndex(pd.to_datetime(values, utc=True, format="ISO8601"))
    result = probe.parse_times(pd.DataFrame({"start_utc": values}), {"start_utc": native})
    assert result == [
        {
            "column": "start_utc",
            "rows": 2,
            "fractional_rows": 1,
            "default_status": "ValueError",
            "default_exact_native_ns": None,
            "iso_exact_native_ns": True,
        }
    ]
    assert native.asi8[0] % 1_000_000_000 == 123456789


def test_uniform_precision_passes_both_parsers():
    values = ["2022-09-09T22:30:00Z", "2022-09-09T22:30:01Z"]
    native = pd.DatetimeIndex(pd.to_datetime(values, utc=True))
    row = probe.parse_times(pd.DataFrame({"end_utc": values}), {"end_utc": native})[0]
    assert row["default_status"] == "passed"
    assert row["default_exact_native_ns"] is row["iso_exact_native_ns"] is True


@pytest.mark.parametrize(
    "bad", [None, "2022-09-09 22:30:00", "2022-09-09T22:30:00+03:00", "SECRET"]
)
def test_unknown_or_non_utc_reference_is_rejected(bad):
    with pytest.raises(probe.ProbeCheck, match="Reference UTC schema"):
        probe.parse_times(
            pd.DataFrame({"start_utc": [bad]}),
            {"start_utc": pd.DatetimeIndex(["2022-09-09T22:30:00Z"])},
        )


def test_explicit_parser_cannot_change_even_one_nanosecond():
    values = ["2022-09-09T22:30:00Z"]
    actual = pd.DatetimeIndex(["2022-09-09T22:30:00.000000001Z"])
    with pytest.raises(probe.ProbeCheck, match="changes native time"):
        probe.parse_times(pd.DataFrame({"start_utc": values}), {"start_utc": actual})


def test_checked_frame_only_and_no_private_exception_text(tmp_path):
    code = compile(
        "def source_scans():\n    raise ValueError('SECRET_TOKEN https://private')\nsource_scans()",
        str(tmp_path / "science.py"),
        "exec",
    )
    with pytest.raises(ValueError) as caught:
        exec(code, {})
    safe = SimpleNamespace(safe_error=lambda kind: kind)
    result = probe.error_location(caught.value, tmp_path, {"science.py"}, {"Known guard"}, safe)
    assert result["error_type"] == "ValueError" and result["guard"] == "CLASS_ONLY"
    assert result["scientific_frames"][-1] == {
        "file": "science.py",
        "line": 2,
        "function": "source_scans",
    }
    assert "SECRET" not in json.dumps(result) and "private" not in json.dumps(result)
    assert (
        probe.error_location(caught.value, tmp_path, set(), set(), safe)["scientific_frames"] == []
    )


def test_literal_checked_guard_is_preserved():
    safe = SimpleNamespace(safe_error=lambda kind: kind)
    result = probe.error_location(ValueError("Known guard"), ROOT, set(), {"Known guard"}, safe)
    assert result["guard"] == "Known guard"


def test_changed_helper_is_rejected_before_execution(tmp_path):
    (tmp_path / "collect_gcp_v2_failure_snapshot.py").write_text(
        "raise RuntimeError('MUST_NOT_EXECUTE')"
    )
    with pytest.raises(probe.ProbeCheck, match="Pinned snapshot helper"):
        probe.helper(tmp_path)


@pytest.mark.parametrize(
    "action",
    [
        "socket.getaddrinfo('example.com',443)",
        "socket.socket().connect(('127.0.0.1',9))",
        "socket.socket().bind(('127.0.0.1',0))",
    ],
)
def test_network_guard_blocks_dns_connections_and_listener(action):
    path = str(ROOT / "scripts/cloud/diagnose_gcp_v2_scan_times.py")
    code = f"import runpy,socket; p=runpy.run_path({path!r}); p['no_network'](); {action}"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=15
    )
    assert result.returncode != 0 and "Diagnostic network forbidden" in result.stderr


@pytest.fixture
def replay(tmp_path, monkeypatch):
    import geopandas as gpd
    from shapely.geometry import box

    def sha(data):
        return hashlib.sha256(data).hexdigest()

    work = tmp_path / "wildfire-gcp-production-v1"
    meta = work / "months/2022-09/metadata"
    meta.mkdir(parents=True)
    pair = {
        "sample_id": probe.FOCUS,
        "sensor": "SNPP",
        "key": "2022252.2230",
        "sources": [
            {"role": role, "filename": name}
            for role, name in [("fire", "fire.nc"), ("geolocation", "geo.nc")]
        ],
    }
    plan = meta / "month.json"
    plan.write_text(json.dumps({"pairs": [pair]}))
    monkeypatch.setattr(probe, "PLAN_SHA", probe.digest(plan))
    (work / "progress.json").write_text('{"status":"failed_checkpoints_retained"}')
    task = meta.parent / "accelerated_run/tasks" / sha(probe.FOCUS.encode())
    raw = task / "summer/raw" / probe.STEM
    raw.mkdir(parents=True)
    for name in ["fire.nc", "geo.nc"]:
        (raw / name).write_bytes(b"retained raw fixture")
    results = task / "summer/results"
    results.mkdir()
    values = pd.DatetimeIndex(["2022-09-09T22:30:00.123456789Z", "2022-09-09T22:30:01Z"])
    pd.DataFrame(
        {name: values.astype(str) for name in ["start_utc", "end_utc", "ev_mid_utc"]}
    ).to_csv(results / (probe.STEM + "_scan_times.csv"), index=False)
    (task / "summer/manifest.json").write_text('{"bundle_files": {}}')
    script = task / "scripts/cloud/l2_daily_compact.py"
    script.parent.mkdir(parents=True)
    script.write_text("# Checked fixture\n")
    snap = SimpleNamespace(
        collect=lambda home: {
            "focus_sample": probe.FOCUS,
            "month_plan_sha256": probe.PLAN_SHA,
            "focus_raw_inventory": [{"present": True, "actual_bytes": 20, "expected_bytes": 20}],
        },
        sha=sha,
        boundary=lambda path, owner: None,
        read=lambda path, owner: path.read_bytes(),
        guards=lambda data: set(),
        NATIVE_SUFFIXES={"scan_times.csv"},
        safe_error=lambda kind: kind,
    )
    layer = SimpleNamespace(
        tags=lambda: {"TAI93_leapseconds": "37"}, read=lambda band: np.array([[1, 2]])
    )
    area = SimpleNamespace(
        audit=SimpleNamespace(),
        tai93_utc=lambda raw, offset: values,
        load_parts=lambda: (None, SimpleNamespace(grid_id=["grid"])),
    )
    timing = SimpleNamespace(
        source_scans=lambda *args: ([1], [1, 2], {"native_grid_counts_exact_match": True}, None)
    )
    native = SimpleNamespace(
        area=area, audit=SimpleNamespace(layer=lambda *args: layer), timing=timing
    )
    monkeypatch.setitem(
        sys.modules, "run_gcp_production", SimpleNamespace(science=lambda root: (None, native))
    )
    monkeypatch.setattr(
        gpd, "read_file", lambda path: gpd.GeoDataFrame(geometry=[box(0, 0, 1, 1)], crs=4326)
    )
    before = {p: probe.digest(p) for p in tmp_path.rglob("*") if p.is_file()}
    return tmp_path, snap, timing, script, before


def test_full_read_only_replay_preserves_all_existing_bytes(replay):
    home, snapshot, timing, script, before = replay
    result = probe.run(home, snapshot)
    assert result["scan_replay"]["status"] == "passed"
    assert all(
        row["default_status"] == "ValueError" and row["iso_exact_native_ns"]
        for row in result["parser_comparison"]
    )
    assert result["production_input_hashes_unchanged"]
    assert result["raw_downloads"] == result["production_writes"] == 0
    assert result["credentials_read"] is result["native_code_changed"] is False
    assert before == {p: probe.digest(p) for p in home.rglob("*") if p.is_file()}


def test_actual_failure_reports_checked_location_without_error_body(replay):
    home, snapshot, timing, script, _ = replay
    namespace = {}
    exec(
        compile(
            "def source_scans(*args):\n    raise ValueError('SECRET_TOKEN')", str(script), "exec"
        ),
        namespace,
    )
    timing.source_scans = namespace["source_scans"]
    result = probe.run(home, snapshot)
    assert result["scan_replay"]["status"] == "local_failure_reproduced"
    assert result["scan_replay"]["scientific_frames"][-1]["line"] == 2
    assert "SECRET_TOKEN" not in json.dumps(result)
    assert result["historical_exception_automatically_proven"] is False


def test_changed_input_prevents_success_report(replay):
    home, snapshot, timing, script, _ = replay

    def changed(*args):
        (home / "wildfire-gcp-production-v1/progress.json").write_text("CHANGED")
        return [], [], {"native_grid_counts_exact_match": True}, None

    timing.source_scans = changed
    with pytest.raises(probe.ProbeCheck, match="Production input changed"):
        probe.run(home, snapshot)


def test_different_failed_source_cannot_enter_science(replay):
    home, snapshot, _, _, _ = replay
    snapshot.collect = lambda home: {"focus_sample": "OTHER", "month_plan_sha256": probe.PLAN_SHA}
    with pytest.raises(probe.ProbeCheck, match="Focus snapshot identity"):
        probe.run(home, snapshot)
