"""Scheduling/integrity boundaries; no network, VM or synthetic speed claims."""

import importlib.util
import json
import threading
import time
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "gcp_benchmark_test", ROOT / "scripts/cloud/run_gcp_benchmark.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.mark.parametrize("workers", [1, 2])
def test_pool_obeys_worker_bound_and_processes_every_pair(workers):
    lock = threading.Lock()
    active, peak = 0, 0

    def task(pair, deadline):
        nonlocal active, peak
        assert deadline > time.perf_counter()
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.02)
        with lock:
            active -= 1
        return pair

    completed, duration = runner.execute_arm(list(range(6)), workers, task, time.perf_counter() + 5)
    assert set(completed) == set(range(6))
    assert peak == workers and active == 0 and duration > 0


def test_worker_failure_never_returns_complete_measurement():
    def task(pair, _):
        raise ValueError("source mismatch")

    with pytest.raises(ValueError, match="source mismatch"):
        runner.execute_arm(["bad", "other"], 1, task, time.perf_counter() + 5)


def test_extra_worker_scope_rejected():
    with pytest.raises(ValueError, match="Worker count"):
        runner.execute_arm([], 4, lambda p, d: p, time.perf_counter() + 1)


def test_changed_science_bundle_rejected_before_writes(tmp_path):
    bad = tmp_path / "changed.zip"
    bad.write_bytes(b"changed source")
    target = tmp_path / "unpacked"
    with pytest.raises(ValueError, match="Frozen summer"):
        runner.unpack(bad, target)
    assert not target.exists()


def test_actual_frozen_science_extraction_and_manifest(tmp_path):
    bundle = ROOT / "outputs/cloud_summer/l2_summer_B_bundle.zip"
    if not bundle.exists():
        pytest.skip("Ignored local frozen artifact unavailable")
    root = tmp_path / "native"
    manifest = runner.unpack(bundle, root)
    assert len(manifest["pairs"]) == 6
    summer = runner.load_summer(root)
    parsed, _ = summer.manifest_read()
    assert parsed == manifest
    assert summer.ROOT == root and summer.area.ROOT == root and summer.audit.ROOT == root
    assert runner.unpack(bundle, root) == manifest
    (root / "scripts/cloud/run_l2_summer.py").write_text("changed")
    with pytest.raises(ValueError, match="Existing bundle file"):
        runner.unpack(bundle, root)


def test_inherited_secrets_removed_and_thread_counts_equal_between_arms(monkeypatch):
    for key in ("EARTHDATA_USERNAME", "EARTHDATA_TOKEN", "PYTHONPATH", "PYTHONHOME"):
        monkeypatch.setenv(key, "secret")
    env = runner.clean_environment()
    assert not any(k.startswith("EARTHDATA_") for k in env)
    assert "PYTHONPATH" not in env and "PYTHONHOME" not in env
    assert env["OPENBLAS_NUM_THREADS"] == env["OMP_NUM_THREADS"] == "1"


def test_package_members_do_not_include_credentials_or_raw_sources(tmp_path):
    bundle = ROOT / "outputs/gcp_benchmark/wildfire_gcp_benchmark.zip"
    if not bundle.exists():
        pytest.skip("Package not built yet")
    with zipfile.ZipFile(bundle) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {
            "summer.zip",
            "requirements.txt",
            "run_gcp_benchmark.py",
            "benchmark_manifest.json",
        }
        z.extractall(tmp_path)
    manifest = runner.package_spec(tmp_path)
    assert manifest["arms"] == [1, 2] and manifest["source_bytes_per_arm"] == 1097404203
    assert len(manifest["source_sha256"]) == len(manifest["exact_csv_sha256"]) == 6
    (tmp_path / "requirements.txt").write_text("changed")
    with pytest.raises(ValueError, match="Package changed"):
        runner.package_spec(tmp_path)


def test_atomic_summary_roundtrip(tmp_path):
    target = tmp_path / "summary.json"
    data = {"negative_label_permitted": False, "completed_arms": []}
    runner.atomic_json(target, data)
    assert json.loads(target.read_text()) == data
    assert not target.with_suffix(".json.pending").exists()


def test_child_journal_readback_and_cleanup_order_with_received_colab_fixture(
    tmp_path, monkeypatch
):
    """Replay received products, NOT a raw-processing or Linux performance proof."""
    package = ROOT / "outputs/gcp_benchmark/wildfire_gcp_benchmark.zip"
    reference = ROOT / "outputs/cloud_summer/received/l2_summer_results.zip"
    if not package.exists() or not reference.exists():
        pytest.skip("Local frozen artifacts unavailable")
    extracted = tmp_path / "package"
    with zipfile.ZipFile(package) as archive:
        archive.extractall(extracted)
    native = tmp_path / "native"
    manifest = runner.unpack(extracted / "summer.zip", native)
    summer = runner.load_summer(native)
    pair = manifest["pairs"][0]
    checked = []

    def fixture_products(selected, raw):
        assert selected == pair
        assert raw.resolve().is_relative_to(native.resolve())
        with zipfile.ZipFile(reference) as archive:
            for suffix in summer.SUFFIXES:
                name = f"{pair['stem']}_{suffix}"
                (summer.OUTPUT / name).write_bytes(archive.read(name))
        (summer.OUTPUT / f"{pair['stem']}_memory.json").write_text(
            json.dumps({"child_peak_rss_bytes": 100})
        )

    def cleanup(selected, raw):
        # This fixture has no raw files; verify journal before the cleanup callback.
        assert summer.checkpoint_read(
            selected, summer.OUTPUT, runner.digest(native / "summer/manifest.json")
        )
        checked.append("verified_before_cleanup")

    monkeypatch.setattr(runner, "load_summer", lambda _: summer)
    monkeypatch.setattr(summer, "download_pair", lambda p, _: sum(s["bytes"] for s in p["sources"]))
    monkeypatch.setattr(summer, "child_audit", fixture_products)
    monkeypatch.setattr(summer, "cleanup_pair", cleanup)
    runner.child(extracted, native, pair["sample_id"])
    assert checked == ["verified_before_cleanup"]
    record = json.loads((summer.OUTPUT / f"{pair['stem']}_checkpoint.json").read_text())
    assert record["metrics"]["disk_sampling_enabled"] is False
    # A second invocation must not reuse outputs and report them as a cold run.
    with pytest.raises(ValueError, match="Cached pair"):
        runner.child(extracted, native, pair["sample_id"])
