"""Exact UTC parsing, scoped restoration and unchanged bounded queue behavior."""

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/landcover"))
adapter = importlib.import_module("vegetation_iso_adapter")

spec = importlib.util.spec_from_file_location(
    "vegetation_v2_test", ROOT / "scripts/landcover/run_vegetation_training_v2.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_mixed_precision_is_exact_and_pandas_itself_is_unchanged():
    values = ["2019-03-01T12:00:00.123456789+00:00", "2019-03-02T12:00:00+00:00"]
    original = pd.to_datetime
    with pytest.raises(ValueError):
        original(values, utc=True)
    calls = []
    module = SimpleNamespace(pd=pd)
    with adapter.scoped(module, calls):
        parsed = module.pd.to_datetime(values, utc=True)
        expected = pd.DatetimeIndex([pd.Timestamp(v) for v in values]).as_unit("ns")
        assert parsed.equals(expected)
        assert pd.to_datetime is original
    assert module.pd is pd and calls[0]["rows"] == 2


@pytest.mark.parametrize(
    "value",
    [
        "2019-03-01",
        "2019-03-01T00:00:00",
        "2019-03-01T00:00:00+03:00",
        "2019-02-30T00:00:00Z",
        "2019-03-01T00:00:00.1234567890Z",
        1000,
    ],
)
def test_ambiguous_invalid_or_overprecise_dates_fail_without_coercion(value):
    module = SimpleNamespace(pd=pd)
    with pytest.raises(ValueError), adapter.scoped(module, []):
        module.pd.to_datetime([value], utc=True)
    assert module.pd is pd


def test_missingness_index_and_numeric_millisecond_conversion_are_preserved():
    proxy = adapter.PandasScope([])
    series = pd.Series(["2019-03-01T00:00:00Z", None], index=[10, 20], name="acquisition")
    result = proxy.to_datetime(series, utc=True)
    assert result.index.equals(series.index) and result.name == series.name
    assert list(result.isna()) == [False, True]
    assert proxy.to_datetime(1000, unit="ms", utc=True) == pd.to_datetime(1000, unit="ms", utc=True)
    dates = [datetime(2019, 3, 1, tzinfo=UTC)]
    assert proxy.to_datetime(dates, utc=True).equals(pd.to_datetime(dates, utc=True))


def test_new_metadata_mismatch_is_rejected_but_legacy_manifest_is_retained(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"rows": 5798}))
    original = path.read_bytes()
    adapter.check_metadata(path)
    assert path.read_bytes() == original
    path.write_text(json.dumps({"datetime_parser_adapter": {"protocol": "changed"}}))
    with pytest.raises(ValueError, match="Stored execution adapter changed"):
        adapter.check_metadata(path)


def test_child_routing_keeps_warning_option_timeout_and_restores_parent(monkeypatch):
    calls = []

    def child(arguments, log, deadline):
        calls.append((arguments, log, deadline))

    def original_fingerprints():
        return {"base": "unchanged"}

    def original_runtime():
        return {"source_sha256": {}}

    queue = SimpleNamespace(run_child=child, fingerprints=original_fingerprints)
    supervisor = SimpleNamespace(queue=queue, runtime=original_runtime)
    monkeypatch.setattr(runner, "checked_proof", lambda *args: {})
    with runner.adapted_supervisor(supervisor, Path("proof.json"), "a" * 64):
        queue.run_child(
            [
                "-W",
                "error::DeprecationWarning",
                "scripts/quality/verify_vegetation_month.py",
                "--month",
                "2019-03",
            ],
            Path("log"),
            123,
        )
        assert calls[0][0][:2] == ["-W", "error::DeprecationWarning"]
        assert calls[0][0][-3:] == ["--", "--month", "2019-03"]
        assert calls[0][1:] == (Path("log"), 123)
        assert supervisor.runtime()["execution_adapter"]["protocol"] == adapter.PROTOCOL
        with pytest.raises(ValueError, match="Known bounded vegetation child"):
            queue.run_child(["unknown.py"], Path("log"), 123)
    assert queue.run_child is child and queue.fingerprints is original_fingerprints
    assert supervisor.runtime is original_runtime


def test_changed_proof_bytes_cannot_start_a_queue(tmp_path):
    path = tmp_path / "proof.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="Pinned ISO proof"):
        runner.checked_proof(path, "a" * 64)


def test_original_future_source_guard_still_rejects_under_adapter():
    import wildfire_risk_prediction.vegetation as vegetation

    with adapter.scoped(vegetation, []), pytest.raises(ValueError, match="strict past window"):
        vegetation.validate_window("2019-03-22", 30, ["2019-03-22T00:00:00Z"])
