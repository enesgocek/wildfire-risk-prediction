"""No cloud calls: deferral must preserve lineage, completion guards and live counters."""

import importlib
import json
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
module = importlib.import_module("run_gcp_source_aware_continuation")
REGISTRY = ROOT / "configs/gcp_source_blocks_2026-10-09.json"
REGISTRY_SHA = "6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d"
PRODUCTION = ROOT / "outputs/gcp_production/package"
EVIDENCE = ROOT / "outputs/gcp_acceleration/diagnosis_2026-10-09/received_verified"


def state(days=(), processed=0, months=("2023-07",), status="paused_at_runtime_reserve"):
    return {
        "existing_months": list(months),
        "days_verified_this_invocation": list(days),
        "pairs_processed_this_invocation": processed,
        "pairs_reused_this_invocation": 0,
        "status": status,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
    }


@pytest.mark.skipif(
    not (PRODUCTION / "production_manifest.json").is_file(),
    reason="Locally verified frozen production fixture is unavailable",
)
def test_sealed_catalogue_and_sources_are_identical_across_scheduling_phases():
    spec = json.loads(
        (ROOT / "outputs/gcp_production/package/production_manifest.json").read_bytes()
    )
    catalogue, sources, calls = object(), object(), []

    def read_scope(path):
        calls.append(path)
        return spec, module.ORIGINAL_SCOPE, catalogue, sources

    runner = SimpleNamespace(read_scope=read_scope)
    first = module.RunnerPhase(runner, "december_safe_days").read_scope("original")
    second = module.RunnerPhase(runner, "remaining_months").read_scope("original")
    assert first[0]["months"] + second[0]["months"] == spec["months"]
    assert first[2:] == second[2:] == (catalogue, sources)
    assert calls == ["original", "original"] and len(spec["months"]) == 71


@pytest.mark.skipif(
    not (EVIDENCE / "manifest.zip").is_file(),
    reason="Verified VM December metadata fixture is unavailable",
)
def test_actual_december_plan_deferred_day_never_reaches_science_or_completion(tmp_path):
    with zipfile.ZipFile(
        ROOT / "outputs/gcp_acceleration/diagnosis_2026-10-09/received_verified/manifest.zip"
    ) as z:
        data = z.read("month.json")
    plan = json.loads(data)
    path = tmp_path / "month.json"
    path.write_bytes(data)
    args = (None, None, None, None, None, path, plan, plan["days"])
    seen = []

    def pipeline(*values):
        seen.extend(values[7])
        return {"status": "complete", "day_records": {d: {} for d in values[7]}}

    result = module.filtered_pipeline(pipeline, *args)
    assert seen == plan["days"][:-1] and plan["days"][-1] == "2023-12-31"
    assert result["status"] == "deferred_source_lineage"
    assert module.BLOCKED_DAY not in result["day_records"]


def test_unaffected_pipeline_and_runtime_reserve_result_remain_unchanged(tmp_path):
    wanted = {"status": "paused_at_runtime_reserve", "day_records": {}}
    plan = {"month": "2023-06"}
    assert (
        module.filtered_pipeline(
            lambda *a: wanted, None, None, None, None, None, tmp_path / "unused", plan, []
        )
        is wanted
    )


def test_registry_cannot_defer_an_arbitrary_day_or_pair(tmp_path):
    module.registry(REGISTRY, REGISTRY_SHA)
    value = json.loads(REGISTRY.read_bytes())
    value["deferred_days"].append("2023-12-30")
    target = tmp_path / "registry.json"
    target.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Source-block scope"):
        module.registry(target, module.sha(target))


def test_all_processable_months_are_not_all_training_months():
    months = [
        f"{y}-{m:02d}"
        for y in range(2018, 2024)
        for m in range(1, 13)
        if f"{y}-{m:02d}" != "2023-12"
    ]
    result = module.merged([], state(months=months), "remaining_months", "r", "w")
    assert len(result["existing_months"]) == 71
    assert result["status"] == "processable_months_verified_source_resolution_pending"
    assert result["full_training_complete"] is False and result["deferred_months"] == ["2023-12"]
    with pytest.raises(ValueError, match="cannot be complete"):
        module.merged([], state(days=[module.BLOCKED_DAY]), "remaining_months", "r", "w")


def test_two_phase_live_and_final_counts_do_not_double_count(tmp_path):
    work = tmp_path
    live = []

    def atomic(path, value):
        path.write_text(json.dumps(value))
        if path == work / "progress.json":
            live.append(value["pairs_processed_this_invocation"])

    def original_pipeline(*a, **k):
        return None

    control = SimpleNamespace(atomic=atomic, pipeline=original_pipeline)
    phases = []

    def run(args, runner, *rest):
        phases.append(runner.phase)
        value = (
            state(
                days=[f"2023-12-{d:02d}" for d in range(1, 31)],
                processed=3,
                months=["2023-07", "2023-08", "2023-09", "2023-10", "2023-11"],
            )
            if runner.phase == "december_safe_days"
            else state(days=["2023-06-01"], processed=7, months=["2023-07", "2023-06"])
        )
        control.atomic(work / "progress.json", value)
        control.atomic(work / "acceleration_run_summary.json", value)

    args = SimpleNamespace(registry=REGISTRY, registry_sha=REGISTRY_SHA)
    module.run_phases(
        control,
        run,
        args,
        object(),
        {},
        "s",
        {},
        object(),
        time.monotonic() + 3000,
        SimpleNamespace(failed=False),
        work,
    )
    result = json.loads((work / "progress.json").read_bytes())
    assert phases == ["december_safe_days", "remaining_months"]
    assert result["pairs_processed_this_invocation"] == 10 and live[-1] == 10
    assert 7 not in live and 13 not in live
    assert result["existing_months"] == [
        "2023-06",
        "2023-07",
        "2023-08",
        "2023-09",
        "2023-10",
        "2023-11",
    ]
    assert control.atomic is atomic and control.pipeline is original_pipeline


def test_failure_restores_wrappers_and_keeps_registry_and_last_valid_progress(tmp_path):
    def atomic(path, value):
        path.write_text(json.dumps(value))

    def pipeline(*a, **k):
        return None

    control = SimpleNamespace(atomic=atomic, pipeline=pipeline)

    def run(*args):
        control.atomic(
            tmp_path / "progress.json", state(processed=1, status="failed_checkpoints_retained")
        )
        raise RuntimeError("External secret must not be logged")

    with pytest.raises(RuntimeError):
        module.run_phases(
            control,
            run,
            SimpleNamespace(registry=REGISTRY, registry_sha=REGISTRY_SHA),
            object(),
            {},
            "s",
            {},
            object(),
            time.monotonic() + 3000,
            SimpleNamespace(failed=False),
            tmp_path,
        )
    assert control.atomic is atomic and control.pipeline is pipeline
    result = json.loads((tmp_path / "progress.json").read_bytes())
    assert (
        result["status"] == "failed_checkpoints_retained"
        and result["pairs_processed_this_invocation"] == 1
    )
    assert "secret" not in (tmp_path / "continuation_summary.json").read_text()


def test_reserve_before_december_completion_does_not_start_remaining_months(tmp_path):
    phases = []
    control = SimpleNamespace(
        atomic=lambda p, v: p.write_text(json.dumps(v)), pipeline=lambda *a: None
    )

    def run(args, runner, *rest):
        phases.append(runner.phase)
        control.atomic(tmp_path / "progress.json", state(days=["2023-12-01"]))

    module.run_phases(
        control,
        run,
        SimpleNamespace(registry=REGISTRY, registry_sha=REGISTRY_SHA),
        object(),
        {},
        "s",
        {},
        object(),
        time.monotonic() + 3000,
        SimpleNamespace(failed=False),
        tmp_path,
    )
    assert phases == ["december_safe_days"]


def test_safe_child_error_never_logs_external_text(tmp_path):
    original, root = tmp_path / "original", tmp_path / "core"
    original.mkdir()
    (root / "summer").mkdir(parents=True)
    (original / "production_manifest.json").write_text(json.dumps({"files": {"guard.py": ""}}))
    (original / "guard.py").write_text('require(False, "Source checksum differs")')
    (root / "summer/manifest.json").write_text(json.dumps({"bundle_files": {}}))
    assert (
        module.safe_failure(ValueError("Source checksum differs"), root, original)["guard"]
        == "Source checksum differs"
    )
    assert (
        module.safe_failure(ValueError("SECRET_CONNECTION_VALUE"), root, original)["guard"]
        == "CLASS_ONLY"
    )


@pytest.mark.skipif(
    not (EVIDENCE / "capture_manifest.json").is_file()
    or not (PRODUCTION / "production_manifest.json").is_file()
    or not (ROOT / "outputs/gcp_acceleration/package/acceleration_manifest.json").is_file(),
    reason="Locally verified VM checkpoint and frozen package fixtures are unavailable",
)
def test_real_child_entry_point_reuses_native_checkpoint_without_network_or_raw_download(tmp_path):
    """Exercise new CLI and the original scientific child against real VM outputs."""
    for source, name in [
        (ROOT / "outputs/gcp_production/package", "wildfire-gcp-production-package"),
        (ROOT / "outputs/gcp_acceleration/package", "wildfire-gcp-acceleration-package"),
    ]:
        shutil.copytree(source, tmp_path / name, ignore=shutil.ignore_patterns("__pycache__"))
    work = tmp_path / "wildfire-gcp-production-v1"
    task = work / "months/2023-12/accelerated_run/tasks" / "warm_readback"
    sys.path.insert(0, str(ROOT / "outputs/gcp_production/package"))
    support = importlib.import_module("gcp_production_support")
    support.template(ROOT / "outputs/gcp_production/package", task)
    evidence = ROOT / "outputs/gcp_acceleration/diagnosis_2026-10-09/received_verified"
    with zipfile.ZipFile(evidence / "manifest.zip") as archive:
        plan_bytes = archive.read("month.json")
        meta = task / "production_metadata"
        meta.mkdir()
        for name in archive.namelist():
            if name != "month.json":
                (meta / name).write_bytes(archive.read(name))
    plan_path = tmp_path / "month.json"
    plan_path.write_bytes(plan_bytes)
    cap = json.loads((evidence / "capture_manifest.json").read_bytes())
    item = next(p for p in cap["task_inventory"] if p["pair_zip_present"])
    import hashlib

    key = hashlib.sha256(item["sample_id"].encode()).hexdigest()
    native = task / "summer/results"
    native.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(evidence / "tasks" / key / "pair.zip") as archive:
        expected = {name: archive.read(name) for name in archive.namelist()}
        for name, data in expected.items():
            (native / name).write_bytes(data)
    shim = (
        "import sys,importlib.util;from pathlib import Path;from unittest.mock import patch;"
        "sys.dont_write_bytecode=True;"
        "sys.path.insert(0,str(Path('scripts/cloud').resolve()));"
        "import probe_gcp_retained_sources as safety;safety.block_network();"
        "import run_gcp_source_aware_continuation as continuation;"
        "sys.argv=sys.argv[1:];"
        f"ctx=patch('pathlib.Path.home',return_value=Path({str(tmp_path)!r}));"
        "ctx.start();continuation.main()"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            shim,
            "continuation",
            "--child",
            "pair",
            "--registry",
            str(REGISTRY),
            "--registry-sha",
            REGISTRY_SHA,
            "--root",
            str(task),
            "--plan",
            str(plan_path),
            "--sample",
            item["sample_id"],
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    with zipfile.ZipFile(task / "pair.zip") as archive:
        assert {name: archive.read(name) for name in archive.namelist()} == expected
    assert not (task / "summer/raw").exists()
    assert not (task / "continuation_failure.json").exists()
