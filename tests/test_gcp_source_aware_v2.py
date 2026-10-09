"""V2 observability must preserve source deferral, counters and frozen checkpoint reuse."""

import ast
import hashlib
import importlib
import importlib.util
import json
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
module = importlib.import_module("run_gcp_source_aware_continuation_v2")
diagnostic = importlib.import_module("diagnose_gcp_production_manifest")
spec = importlib.util.spec_from_file_location(
    "v1_tests", ROOT / "tests/test_gcp_source_aware_continuation.py"
)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
SOURCE = ROOT / (
    "outputs/gcp_acceleration/continuation_failure_2026-10-09/received/"
    "gcp_source_aware_failure_2026-10-09.zip"
)


@pytest.mark.parametrize(
    "name",
    [
        "test_registry_cannot_defer_an_arbitrary_day_or_pair",
        "test_unaffected_pipeline_and_runtime_reserve_result_remain_unchanged",
        "test_two_phase_live_and_final_counts_do_not_double_count",
        "test_failure_restores_wrappers_and_keeps_registry_and_last_valid_progress",
        "test_reserve_before_december_completion_does_not_start_remaining_months",
        "test_safe_child_error_never_logs_external_text",
    ],
)
def test_v1_scheduling_invariants_hold_for_v2(name, tmp_path, monkeypatch):
    monkeypatch.setattr(previous, "module", module)
    getattr(previous, name)(tmp_path)


def test_complete_processable_months_still_not_full_training(monkeypatch):
    monkeypatch.setattr(previous, "module", module)
    previous.test_all_processable_months_are_not_all_training_months()


def test_frozen_scope_and_deferral_helpers_are_identical_to_v1():
    names = {"registry", "RunnerPhase", "filtered_pipeline", "merged", "safe_failure"}
    bodies = []
    for path in [
        ROOT / "scripts/cloud/run_gcp_source_aware_continuation.py",
        ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v2.py",
    ]:
        bodies.append(
            {
                n.name: ast.dump(n, include_attributes=False)
                for n in ast.parse(path.read_text()).body
                if getattr(n, "name", None) in names
            }
        )
    assert bodies[0] == bodies[1] and set(bodies[0]) == names


def test_nonzero_child_without_python_exception_records_exit_code(tmp_path, monkeypatch, capsys):
    process = SimpleNamespace(pid=12345, returncode=1, poll=lambda: 1)
    monkeypatch.setattr(module.subprocess, "Popen", lambda *a, **k: process)
    monkeypatch.setattr(module.os, "killpg", lambda *a: None, raising=False)
    monkeypatch.setattr(module.signal, "SIGKILL", 9, raising=False)
    control = SimpleNamespace(atomic=lambda p, v: p.write_text(json.dumps(v)))
    reference = SimpleNamespace(ACTIVE_LOCK=threading.Lock(), ACTIVE={}, CHILD_LIMIT=900)
    args = SimpleNamespace(registry=previous.REGISTRY, registry_sha=previous.REGISTRY_SHA)
    launch = module.diagnostic_launcher(control, reference, args)
    with pytest.raises(RuntimeError):
        launch(
            SimpleNamespace(environment=lambda auth: {}),
            "pair",
            tmp_path,
            tmp_path / "plan",
            "SNPP:2022314.1048",
            {"password": "SECRET_TOKEN"},
            time.monotonic() + 3000,
            SimpleNamespace(failed=False),
        )
    value = json.loads((tmp_path / "continuation_failure.json").read_text())
    assert value["exit_code"] == 1 and value["guard"] == "CLASS_ONLY"
    assert reference.ACTIVE == {} and "SECRET" not in capsys.readouterr().out


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Drive HTTP 503; no secrets logged", "GOOGLE_HTTP_503"),
        ("SECRET_TOKEN_RESPONSE", "RuntimeError"),
        ("Known guard", "ValueError"),
    ],
)
def test_parent_diagnostic_is_safe_unique_and_reraises_upstream(
    tmp_path, monkeypatch, capsys, text, expected
):
    original, controller, work = [tmp_path / name for name in ("original", "controller", "work")]
    for package, manifest in [
        (original, "production_manifest.json"),
        (controller, "acceleration_manifest.json"),
    ]:
        package.mkdir()
        body = b'require(True, "Known guard")'
        (package / "guard.py").write_bytes(body)
        (package / manifest).write_text(
            json.dumps({"files": {"guard.py": hashlib.sha256(body).hexdigest()}})
        )

    def atomic(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    control = SimpleNamespace(
        ORIGINAL=original, __file__=str(controller / "main.py"), atomic=atomic
    )
    monkeypatch.setattr(module, "diagnostic_helper", lambda: diagnostic)
    error = ValueError(text) if expected == "ValueError" else RuntimeError(text)
    sampler = SimpleNamespace(arm="2022-11", phase="pair_publication")
    module.parent_failure(control, error, "remaining_months", sampler, work)
    module.parent_failure(control, error, "remaining_months", sampler, work)
    files = list((work / "diagnostics").glob("parent_failure_v2_*.json"))
    assert len(files) == 2
    for path in files:
        value = json.loads(path.read_text())
        assert value["error"] == expected
        assert value["guard"] == ("Known guard" if expected == "ValueError" else "CLASS_ONLY")
        assert "SECRET" not in path.read_text()
    assert "SECRET" not in capsys.readouterr().out


@pytest.mark.parametrize("failing", [False, True])
def test_backend_opener_is_wrapped_before_use_and_factory_restored(monkeypatch, failing):
    class Base:
        @classmethod
        def from_file(cls, path):
            return SimpleNamespace(api=SimpleNamespace(opener="ORIGINAL"))

    class Store(Base):
        pass

    monkeypatch.setitem(
        sys.modules, "accelerated_checkpoint_store", SimpleNamespace(IndexedDriveStore=Store)
    )

    def backend(path):
        result = Store.from_file(path)
        assert result.api.opener == "WRAPPED"
        if failing:
            raise RuntimeError("transport failure")
        return result

    control = SimpleNamespace(backend=backend)
    module.instrument_backend(control, SimpleNamespace(diagnostic_opener=lambda op: "WRAPPED"))
    if failing:
        with pytest.raises(RuntimeError):
            control.backend("unused")
    else:
        control.backend("unused")
    assert "from_file" not in Store.__dict__
    assert Store.from_file("unused").api.opener == "ORIGINAL"


@pytest.mark.skipif(not SOURCE.is_file(), reason="Ignored real native fixture unavailable")
def test_real_v2_child_reuses_november_checkpoint_without_network(tmp_path):
    for source, name in [
        (ROOT / "outputs/gcp_production/package", "wildfire-gcp-production-package"),
        (ROOT / "outputs/gcp_acceleration/package", "wildfire-gcp-acceleration-package"),
    ]:
        shutil.copytree(source, tmp_path / name, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(
        ROOT / "scripts/cloud/diagnose_gcp_production_manifest.py",
        tmp_path / "diagnose_gcp_production_manifest.py",
    )
    sys.path.insert(0, str(ROOT / "outputs/gcp_production/package"))
    support = importlib.import_module("gcp_production_support")
    task = tmp_path / "wildfire-gcp-production-v1/months/2022-11/accelerated_run/tasks/warm_test"
    support.template(ROOT / "outputs/gcp_production/package", task)
    with zipfile.ZipFile(SOURCE) as archive:
        with zipfile.ZipFile(__import__("io").BytesIO(archive.read("manifest.zip"))) as metadata:
            plan = tmp_path / "month.json"
            plan.write_bytes(metadata.read("month.json"))
            meta = task / "production_metadata"
            meta.mkdir()
            for name in metadata.namelist():
                if name != "month.json":
                    (meta / name).write_bytes(metadata.read(name))
        capture = json.loads(archive.read("capture_manifest.json"))
        item = next(t for t in capture["task_inventory"] if t["pair_zip_present"])
        key = hashlib.sha256(item["sample_id"].encode()).hexdigest()
        native = task / "summer/results"
        native.mkdir(parents=True)
        with zipfile.ZipFile(
            __import__("io").BytesIO(archive.read(f"tasks/{key}/pair.zip"))
        ) as pair:
            expected = {name: pair.read(name) for name in pair.namelist()}
            for name, data in expected.items():
                (native / name).write_bytes(data)
    shim = (
        "import sys;from pathlib import Path;from unittest.mock import patch;"
        "sys.dont_write_bytecode=True;sys.path.insert(0,str(Path('scripts/cloud').resolve()));"
        "import probe_gcp_retained_sources as safety;safety.block_network();"
        "import run_gcp_source_aware_continuation_v2 as continuation;sys.argv=sys.argv[1:];"
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
            str(previous.REGISTRY),
            "--registry-sha",
            previous.REGISTRY_SHA,
            "--root",
            str(task),
            "--plan",
            str(plan),
            "--sample",
            item["sample_id"],
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[-1500:]
    with zipfile.ZipFile(task / "pair.zip") as archive:
        assert {name: archive.read(name) for name in archive.namelist()} == expected
    assert json.loads((task / "task_metrics.json").read_text())["downloaded_payload_bytes"] == 0
    assert not (task / "summer/raw").exists()
