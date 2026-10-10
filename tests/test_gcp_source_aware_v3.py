"""Verified ISO execution preserves legacy checkpoints and reviewed failure bytes."""

import ast
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


module = load(
    "continuation_v3_tests", ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v3.py"
)
previous = load(
    "continuation_v1_test_helpers", ROOT / "tests/test_gcp_source_aware_continuation.py"
)
snapshot_tests = load("snapshot_test_helpers", ROOT / "tests/test_gcp_v2_failure_snapshot.py")
snapshot = snapshot_tests.snapshot
PROOF = ROOT / (
    "outputs/gcp_acceleration/continuation_failure_v2_2026-10-10/received/" + module.PROOF_NAME
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
        "test_all_processable_months_are_not_all_training_months",
    ],
)
def test_previous_scientific_scheduling_and_error_guards_hold(name, tmp_path, monkeypatch):
    monkeypatch.setattr(previous, "module", module)
    method = getattr(previous, name)
    method() if name == "test_all_processable_months_are_not_all_training_months" else method(
        tmp_path
    )


def test_registry_filter_and_safe_failure_are_unchanged_ast():
    names = {"registry", "RunnerPhase", "filtered_pipeline", "safe_failure"}
    bodies = []
    for path in [
        ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v2.py",
        ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v3.py",
    ]:
        bodies.append(
            {
                node.name: ast.dump(node, include_attributes=False)
                for node in ast.parse(path.read_text()).body
                if getattr(node, "name", None) in names
            }
        )
    assert bodies[0] == bodies[1] and set(bodies[0]) == names


def test_progress_records_adapter_but_preserves_counter_and_checkpoint_identity():
    state = previous.state(processed=3)
    value = module.merged([], state, "remaining_months", "registry", "wrapper")
    assert value["pairs_processed_this_invocation"] == 3
    assert value["scan_time_adapter_sha256"] == module.ADAPTER_SHA
    assert value["scan_time_adapter_proof_sha256"] == module.PROOF_SHA
    assert value["negative_label_permitted"] is value["full_training_complete"] is False


@pytest.mark.skipif(not PROOF.is_file(), reason="Ignored actual proof fixture unavailable")
def test_actual_proof_identity_and_changed_bytes_refused(tmp_path):
    target = tmp_path / module.PROOF_NAME
    shutil.copyfile(PROOF, target)
    proof = module.accepted_proof(tmp_path)
    assert proof["scan_replay"]["center_rows"] == 1889
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Pinned successful scan adapter proof"):
        module.accepted_proof(tmp_path)


def test_adapted_science_restores_factory_and_adds_transparent_pair_provenance(monkeypatch):
    import contextlib

    import pandas as pd

    calls_seen = []
    timing = SimpleNamespace(pd=pd)

    def source(*args):
        calls_seen.append(timing.pd)
        return (
            [1],
            [1, 2],
            {"native_grid_counts_exact_match": True, "sources": {"raw": "same"}},
            None,
        )

    timing.source_scans = source

    @contextlib.contextmanager
    def parser(t, calls):
        assert t.source_scans is source
        original = t.pd
        t.pd = "proxy"
        calls.extend({"column": name, "rows": 2} for name in ("start_utc", "end_utc", "ev_mid_utc"))
        try:
            yield
        finally:
            t.pd = original

    runner = SimpleNamespace(science=lambda root: ("compact", SimpleNamespace(timing=timing)))
    original = runner.science
    adapter = SimpleNamespace(scan_parser=parser, COLUMNS={"start_utc", "end_utc", "ev_mid_utc"})
    with module.adapted_science(runner, adapter):
        _, native = runner.science("root")
        for _ in range(2):
            provenance = native.timing.source_scans()[2]
            assert provenance["sources"] == {"raw": "same"}
            assert provenance["scan_time_parser_adapter"]["adapter_sha256"] == module.ADAPTER_SHA
        assert timing.pd is pd
    assert (
        runner.science is original
        and timing.source_scans is source
        and calls_seen == ["proxy", "proxy"]
    )


@pytest.fixture
def reviewed(tmp_path, monkeypatch):
    monkeypatch.setattr(module.Path, "home", classmethod(lambda cls: tmp_path))
    work = tmp_path / "wildfire-gcp-production-v1"
    month = work / "months/2022-09"
    (month / "metadata").mkdir(parents=True)
    plan = month / "metadata/month.json"
    plan.write_text("Pinned plan fixture")
    data = json.dumps(snapshot_tests.state()).encode()
    for name in ["progress.json", "acceleration_run_summary.json", "continuation_summary.json"]:
        (work / name).write_bytes(data)
    focus = month / "accelerated_run/tasks" / snapshot.sha(snapshot.FOCUS.encode())
    raw = focus / "summer/raw/l2_sample_2022252.2230/geo.nc"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"RAW_UNCHANGED")
    children, sources = [], {}
    for index in range(15):
        identity = snapshot.FOCUS if index == 0 else f"SNPP:2022253.{index:04d}"
        value = {
            "sample_id": identity,
            "child_kind": "pair",
            "error_type": "ValueError" if index == 0 else "RuntimeError",
            "guard": "CLASS_ONLY",
            "safe_error": "UNCLASSIFIED_ERROR",
        }
        if index:
            value.update(exit_code=-9, termination_kind="nonzero_exit_without_python_diagnostic")
        path = (
            month
            / "accelerated_run/tasks"
            / snapshot.sha(identity.encode())
            / "continuation_failure.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        sources[path] = path.read_bytes()
        children.append({"sample_id": identity, **snapshot.failure(value, {"CLASS_ONLY"})})
    saved = json.dumps(
        {
            "progress": snapshot.progress(data),
            "focus_sample": snapshot.FOCUS,
            "child_failures": children,
        }
    ).encode()
    (tmp_path / module.SNAPSHOT_NAME).write_bytes(saved)
    monkeypatch.setattr(module, "SNAPSHOT_SHA", snapshot.sha(saved))
    proof = {
        "month_plan_sha256": module.sha(plan),
        "input_hashes": {"progress.json": snapshot.sha(data), "geo.nc": module.sha(raw)},
    }
    monkeypatch.setattr(module, "accepted_proof", lambda home: proof)
    monkeypatch.setattr(
        module,
        "checked_adapter",
        lambda: SimpleNamespace(
            checked_probe=lambda home: SimpleNamespace(helper=lambda home: snapshot)
        ),
    )
    control = SimpleNamespace(
        PRODUCTION=work, atomic=lambda path, value: path.write_text(json.dumps(value))
    )
    return control, sources, raw


def test_preflight_writes_nothing_and_rearming_preserves_every_diagnostic_byte(reviewed):
    control, sources, raw = reviewed
    before = {p: p.read_bytes() for p in control.PRODUCTION.rglob("*") if p.is_file()}
    module.prepare_reviewed_failures(control, apply=False)
    assert before == {p: p.read_bytes() for p in control.PRODUCTION.rglob("*") if p.is_file()}
    module.prepare_reviewed_failures(control, apply=True)
    assert raw.read_bytes() == b"RAW_UNCHANGED"
    for source, data in sources.items():
        assert not source.exists() and source.parent.is_dir()
        assert (
            control.PRODUCTION / "diagnostics/reviewed_v2" / (source.parent.name + ".json")
        ).read_bytes() == data
    module.prepare_reviewed_failures(control, apply=True)  # Interrupted start can re-enter safely.


def test_partial_archive_resumes_without_losing_or_overwriting_records(reviewed, monkeypatch):
    control, sources, _ = reviewed
    rename = Path.rename
    moves = []

    def interrupted(path, target):
        moves.append(path)
        if len(moves) == 2:
            raise OSError("Synthetic interruption")
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", interrupted)
    with pytest.raises(OSError):
        module.prepare_reviewed_failures(control, apply=True)
    monkeypatch.setattr(Path, "rename", rename)
    module.prepare_reviewed_failures(control, apply=True)
    for path, data in sources.items():
        assert (
            control.PRODUCTION / "diagnostics/reviewed_v2" / (path.parent.name + ".json")
        ).read_bytes() == data


@pytest.mark.parametrize("fault", ["new_failure", "raw_change", "state_change", "duplicate"])
def test_unknown_changes_refuse_rearming_before_any_move(reviewed, fault):
    control, sources, raw = reviewed
    first = next(iter(sources))
    if fault == "new_failure":
        value = json.loads(first.read_bytes())
        value["guard"] = "New error"
        first.write_text(json.dumps(value))
    elif fault == "raw_change":
        raw.write_bytes(b"CHANGED")
    elif fault == "state_change":
        (control.PRODUCTION / "progress.json").write_text("{}")
    else:
        archive = control.PRODUCTION / "diagnostics/reviewed_v2" / (first.parent.name + ".json")
        archive.parent.mkdir(parents=True)
        archive.write_bytes(first.read_bytes())
    before = {p: p.read_bytes() for p in control.PRODUCTION.rglob("*") if p.is_file()}
    with pytest.raises((ValueError, KeyError)):
        module.prepare_reviewed_failures(control, apply=True)
    assert before == {p: p.read_bytes() for p in control.PRODUCTION.rglob("*") if p.is_file()}


def test_new_v3_failure_requires_review_instead_of_automatic_retry(reviewed):
    control, _, _ = reviewed
    value = snapshot_tests.state()
    value.update(
        continuation_wrapper_sha256=module.sha(Path(module.__file__)),
        scan_time_adapter_sha256=module.ADAPTER_SHA,
        scan_time_adapter_proof_sha256=module.PROOF_SHA,
    )
    (control.PRODUCTION / "progress.json").write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Unreviewed failure"):
        module.prepare_reviewed_failures(control, apply=True)


SOURCE = (
    ROOT
    / "outputs/gcp_acceleration/continuation_failure_2026-10-09/received"
    / "gcp_source_aware_failure_2026-10-09.zip"
)


@pytest.mark.skipif(
    not SOURCE.is_file() or not PROOF.is_file(), reason="Ignored real VM fixture unavailable"
)
def test_real_v3_cli_reuses_old_checkpoint_without_network_or_changed_native_bytes(
    tmp_path, monkeypatch
):
    v2 = load("v2_integration_helper", ROOT / "tests/test_gcp_source_aware_v2.py")
    shutil.copyfile(PROOF, tmp_path / module.PROOF_NAME)
    shutil.copyfile(
        ROOT / "scripts/cloud/verify_gcp_scan_iso_adapter.py",
        tmp_path / "verify_gcp_scan_iso_adapter.py",
    )
    original_run = subprocess.run

    def run(command, *args, **kwargs):
        command = list(command)
        command[2] = command[2].replace(
            "run_gcp_source_aware_continuation_v2", "run_gcp_source_aware_continuation_v3"
        )
        return original_run(command, *args, **kwargs)

    monkeypatch.setattr(v2.subprocess, "run", run)
    v2.test_real_v2_child_reuses_november_checkpoint_without_network(tmp_path)
    # A separate fixture-only metadata extension must remain readable by the frozen validator.
    task = tmp_path / "wildfire-gcp-production-v1/months/2022-11/accelerated_run/tasks/warm_test"
    code = (
        "import sys,json;from pathlib import Path;"
        "sys.dont_write_bytecode=True;sys.path.insert(0,str(Path('scripts/cloud').resolve()));"
        "import probe_gcp_retained_sources as safety;safety.block_network();"
        f"sys.path.insert(0,{str(tmp_path / 'wildfire-gcp-production-package')!r});"
        "import run_gcp_production as worker;"
        f"root=Path({str(task)!r});_,native=worker.science(root);"
        "output=root/'summer/results';"
        "path=next(output.glob('*_scan_provenance.json'));"
        "value=json.loads(path.read_bytes());"
        "value['scan_time_parser_adapter']={'fixture_only':True};"
        "path.write_text(json.dumps(value));"
        "checkpoint=next(output.glob('*_checkpoint.json'));"
        "record=json.loads(checkpoint.read_bytes());"
        "record['outputs'][path.name]=worker.digest(path);"
        "checkpoint.write_text(json.dumps(record));"
        f"plan=json.loads(Path({str(tmp_path / 'month.json')!r}).read_bytes());"
        "pair=next(p for p in plan['pairs'] if p['sample_id']==record['sample_id']);"
        "assert native.checkpoint_read(pair,output,record['manifest_sha256'])==record;"
        "print('PASS fixture-only provenance extension')"
    )
    result = original_run(
        [__import__("sys").executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[-1500:]
    assert "PASS fixture-only provenance extension" in result.stdout


def test_shutdown_and_detached_child_paths_remain_identical_to_v2():
    v2 = ast.parse((ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v2.py").read_text())
    v3 = ast.parse(Path(module.__file__).read_text())
    names = {"diagnostic_launcher", "instrument_backend"}

    def selected(tree):
        return {
            node.name: ast.dump(node, include_attributes=False)
            for node in tree.body
            if getattr(node, "name", None) in names
        }

    assert selected(v2) == selected(v3)
    source = Path(module.__file__).read_text()
    assert (
        "control.supervise(args, runner, spec, scope, auth, reference, seconds, control.PRODUCTION)"
        in source
    )
