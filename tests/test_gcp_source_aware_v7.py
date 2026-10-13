"""V7 migration evidence, two-day exclusion and three-phase acceptance guards."""

import ast
import hashlib
import importlib
import json
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
m = importlib.import_module("run_gcp_source_aware_continuation_v7")
RECEIVED = ROOT / "outputs/gcp_acceleration/source_aware_v6_session_2026-10-13/received"
REGISTRY = ROOT / "configs/gcp_source_blocks_2026-10-13.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def state(days=(), months=("2023-07",), status="paused_at_runtime_reserve", processed=0):
    return dict(
        status=status,
        existing_months=list(months),
        days_verified_this_invocation=list(days),
        pairs_processed_this_invocation=processed,
        pairs_reused_this_invocation=0,
        negative_label_permitted=False,
        daily_observation_status="unknown",
        queue_manifest_sha256=m.ORIGINAL_SCOPE,
        controller_manifest_sha256=m.CONTROLLER_SCOPE,
    )


def test_runtime_science_and_shutdown_functions_are_identical_to_frozen_v6():
    def nodes(file):
        return {
            n.name: ast.dump(n, include_attributes=False)
            for n in ast.parse(file.read_text(encoding="utf-8")).body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef))
        }

    old = nodes(ROOT / "scripts/cloud/run_gcp_source_aware_continuation_v6.py")
    new = nodes(Path(m.__file__))
    changed = {
        "prepare_reviewed_failures",
        "registry",
        "RunnerPhase",
        "filtered_pipeline",
        "merged",
        "run_phases",
        "child",
        "main",
    }
    for name in set(old) - changed:
        assert old[name] == new[name], name
    # main only changes its log filename, preserving lock, detached pipe and shutdown.
    old_main = old["main"].replace(
        "gcp_source_aware_launcher_v6.log", "gcp_source_aware_launcher_v7.log"
    )
    assert new["main"] == old_main


def test_actual_registry_and_snapshot_match_eight_source_blocks():
    value = m.registry(REGISTRY, m.REGISTRY_SHA)
    assert len(value["blocked_pairs"]) == 8
    if not (RECEIVED / m.RESUME_NAME).exists():
        pytest.skip("Local ignored VM snapshot absent")
    resume = json.loads((RECEIVED / m.RESUME_NAME).read_bytes())
    assert m.sha(RECEIVED / m.RESUME_NAME) == m.RESUME_SHA
    assert len(resume["retained_pair_zips"]) == 22
    assert resume["retained_pair_zip_bytes"] == 65888711
    lineage = json.loads((RECEIVED / m.LINEAGE_NAME).read_bytes())
    for row in lineage["failures"]:
        assert m.EXPECTED[row["sample_id"]] == row["declared_geolocation_filenames"][0]


def test_registry_cannot_add_arbitrary_exclusion_even_with_supplied_hash(tmp_path):
    value = json.loads(REGISTRY.read_bytes())
    value["deferred_days"].append("2018-06-12")
    target = tmp_path / "registry.json"
    put(target, json.dumps(value).encode())
    with pytest.raises(ValueError, match="Pinned V7"):
        m.registry(target, m.sha(target))


def test_three_phases_partition_original_catalogue_without_changing_source_objects():
    spec = json.loads(
        (ROOT / "outputs/gcp_production/package/production_manifest.json").read_bytes()
    )
    catalogue, sources = object(), object()
    runner = SimpleNamespace(read_scope=lambda _: (spec, m.ORIGINAL_SCOPE, catalogue, sources))
    results = [
        m.RunnerPhase(runner, phase).read_scope("sealed")
        for phase in ("december_safe_days", "june_safe_days", "remaining_months")
    ]
    months = [v for result in results for v in result[0]["months"]]
    assert len(months) == len(set(months)) == 71 and set(months) == set(spec["months"])
    assert all(result[2:] == (catalogue, sources) for result in results)
    assert results[1][0]["months"] == ["2018-06"]
    assert "2018-06" not in results[2][0]["months"]
    assert spec["months"] == runner.read_scope("sealed")[0]["months"]


@pytest.mark.parametrize("month,blocked", [("2018-06", "2018-06-13"), ("2023-12", "2023-12-31")])
def test_day_exclusion_retains_original_plan_and_never_accepts_partial_month(
    tmp_path, monkeypatch, month, blocked
):
    n = 30 if month == "2018-06" else 31
    plan = dict(
        month=month,
        days=[f"{month}-{d:02d}" for d in range(1, n + 1)],
        pairs=[{"sample_id": "all nominal sources preserved"}],
        negative_label_permitted=False,
        daily_observation_status="unknown",
    )
    raw = json.dumps(plan).encode()
    path = tmp_path / "month.json"
    put(path, raw)
    monkeypatch.setitem(m.PLAN_SHA_BY_MONTH, month, digest(raw))
    seen = []

    def pipeline(*args):
        assert args[6] is plan and args[5] == path
        seen.extend(args[7])
        return dict(status="complete", day_records={d: {} for d in args[7]})

    result = m.filtered_pipeline(pipeline, None, None, None, None, None, path, plan, plan["days"])
    assert blocked not in seen and len(seen) == n - 1
    assert result["status"] == "deferred_source_lineage"
    assert blocked in plan["days"] and len(plan["pairs"]) == 1
    with pytest.raises(ValueError, match="Deferred day"):
        m.filtered_pipeline(
            lambda *a: dict(status="complete", day_records={blocked: {}}),
            None,
            None,
            None,
            None,
            None,
            path,
            plan,
            plan["days"],
        )
    with pytest.raises(ValueError, match="Every safe day"):
        m.filtered_pipeline(
            lambda *a: dict(status="complete", day_records={}),
            None,
            None,
            None,
            None,
            None,
            path,
            plan,
            plan["days"],
        )
    put(path, raw + b" ")
    with pytest.raises(ValueError, match="Exact deferred"):
        m.filtered_pipeline(pipeline, None, None, None, None, None, path, plan, plan["days"])


def test_seventy_months_need_safe_june_and_december_days_and_never_complete_training():
    months = [
        f"{y}-{mo:02d}"
        for y in range(2018, 2024)
        for mo in range(1, 13)
        if f"{y}-{mo:02d}" not in m.DEFERRED_MONTHS
    ]
    days = set().union(*m.SAFE_DAYS.values())
    partial = m.merged([], state(months=months), "remaining_months", "r", "w")
    assert partial["status"] == "paused_at_runtime_reserve"
    full = m.merged([], state(months=months, days=days), "remaining_months", "r", "w")
    assert full["status"] == "processable_months_verified_source_resolution_pending"
    assert full["full_training_complete"] is False
    failed = m.merged(
        [],
        state(months=months, days=days, status="failed_checkpoints_retained"),
        "remaining_months",
        "r",
        "w",
    )
    assert failed["status"] == "failed_checkpoints_retained"
    for day in m.DEFERRED_DAYS:
        with pytest.raises(ValueError, match="cannot be complete"):
            m.merged([], state(days=[day]), "june_safe_days", "r", "w")
    with pytest.raises(ValueError, match="cannot be complete"):
        m.merged([], state(months=["2018-06"]), "june_safe_days", "r", "w")


def test_live_three_phase_counts_and_failure_propagation(tmp_path, monkeypatch):
    calls = []

    def atomic(path, value):
        put(path, json.dumps(value).encode())

    def pipeline(*args):
        return None

    control = SimpleNamespace(PRODUCTION=tmp_path, atomic=atomic, pipeline=pipeline)

    def run(args, runner, *rest):
        calls.append(runner.phase)
        phase = runner.phase
        control.atomic(
            tmp_path / "progress.json", state(days=m.SAFE_DAYS.get(phase, ()), processed=2)
        )

    monkeypatch.setattr(m.time, "monotonic", lambda: 0)
    m.run_phases(
        control,
        run,
        SimpleNamespace(registry=REGISTRY, registry_sha=m.REGISTRY_SHA),
        object(),
        {},
        "scope",
        {},
        None,
        10000,
        SimpleNamespace(failed=False),
        tmp_path,
    )
    final = json.loads((tmp_path / "continuation_summary.json").read_bytes())
    assert calls == ["december_safe_days", "june_safe_days", "remaining_months"]
    assert final["pairs_processed_this_invocation"] == 6
    assert len(final["days_verified_this_invocation"]) == 59
    assert control.atomic is atomic and control.pipeline is pipeline
    calls.clear()

    def reserve(args, runner, *rest):
        calls.append(runner.phase)
        control.atomic(tmp_path / "progress.json", state(days=[]))

    m.run_phases(
        control,
        reserve,
        SimpleNamespace(registry=REGISTRY, registry_sha=m.REGISTRY_SHA),
        object(),
        {},
        "scope",
        {},
        None,
        10000,
        SimpleNamespace(failed=False),
        tmp_path,
    )
    assert calls == ["december_safe_days"]


@pytest.fixture
def reviewed(tmp_path, monkeypatch):
    if not (RECEIVED / m.RESUME_NAME).exists():
        pytest.skip("Ignored actual fixture absent")
    home = tmp_path
    work = home / "wildfire-gcp-production-v1"
    work.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    resume = json.loads((RECEIVED / m.RESUME_NAME).read_bytes())
    lineage = json.loads((RECEIVED / m.LINEAGE_NAME).read_bytes())
    with tarfile.open(RECEIVED / "gcp_v6_session_20261013T095138Z_logs.tar.gz") as z:
        final = z.extractfile("progress.json").read()
    protected = {}
    for name in lineage["protected_file_sha256"]:
        if name.endswith(
            ("progress.json", "acceleration_run_summary.json", "continuation_summary.json")
        ):
            data = final
        elif name == "run_gcp_source_aware_continuation_v6.py":
            data = (ROOT / "scripts/cloud" / name).read_bytes()
        elif name == "source_blocks.json":
            data = (ROOT / "configs/gcp_source_blocks_2026-10-09.json").read_bytes()
        else:
            data = ("synthetic evidence " + name).encode()
        put(home / name, data)
        protected[name] = digest(data)
    for row in resume["child_diagnostics"]:
        data = json.dumps(
            {"child_kind": "pair", **{k: v for k, v in row.items() if k not in ("path", "sha256")}}
        ).encode()
        put(work / row["path"], data)
        row["sha256"] = digest(data)
        if row["error_type"] == "ValueError":
            protected["wildfire-gcp-production-v1/" + row["path"]] = digest(data)
    for row in resume["parent_diagnostics"]:
        data = b"synthetic reviewed parent"
        put(work / row["path"], data)
        row["sha256"] = digest(data)
    for i, row in enumerate(resume["retained_pair_zips"]):
        data = f"synthetic ZIP {i}".encode()
        put(work / row["path"], data)
        row["bytes"] = len(data)
        row["sha256"] = digest(data)
    plan_hash = protected["wildfire-gcp-production-v1/months/2018-06/metadata/month.json"]
    monkeypatch.setitem(m.PLAN_SHA_BY_MONTH, "2018-06", plan_hash)
    lineage["protected_file_sha256"] = protected
    lineage["month_plan_sha256"] = plan_hash
    raw = json.dumps(lineage).encode()
    put(home / m.LINEAGE_NAME, raw)
    monkeypatch.setattr(m, "LINEAGE_SHA", digest(raw))
    resume["geolocation_snapshot_sha256"] = digest(raw)
    resume["month_plan_sha256"] = plan_hash
    raw = json.dumps(resume).encode()
    put(home / m.RESUME_NAME, raw)
    monkeypatch.setattr(m, "RESUME_SHA", digest(raw))

    def atomic(path, value):
        put(path, json.dumps(value).encode())

    return home, SimpleNamespace(PRODUCTION=work, atomic=atomic), resume


def all_bytes(home):
    return {p.relative_to(home).as_posix(): p.read_bytes() for p in home.rglob("*") if p.is_file()}


def test_migration_dry_run_then_idempotent_archive_preserves_every_payload(reviewed):
    home, control, resume = reviewed
    before = all_bytes(home)
    m.prepare_reviewed_failures(control, False)
    assert all_bytes(home) == before
    m.prepare_reviewed_failures(control, True)
    m.prepare_reviewed_failures(control, True)
    for row in resume["retained_pair_zips"]:
        assert (control.PRODUCTION / row["path"]).read_bytes() == before[
            "wildfire-gcp-production-v1/" + row["path"]
        ]
    archive = control.PRODUCTION / "diagnostics/reviewed_v6_geolocation"
    assert len(json.loads((archive / "receipt.json").read_bytes())["files"]) == 27
    for row in resume["child_diagnostics"]:
        assert not (control.PRODUCTION / row["path"]).exists()
        assert (archive / "files/wildfire-gcp-production-v1" / row["path"]).read_bytes() == before[
            "wildfire-gcp-production-v1/" + row["path"]
        ]
    for name in ("progress.json", "acceleration_run_summary.json", "continuation_summary.json"):
        assert (control.PRODUCTION / name).read_bytes() == before[
            "wildfire-gcp-production-v1/" + name
        ]
    new = m.merged([], state(), "june_safe_days", m.REGISTRY_SHA, m.sha(Path(m.__file__)))
    control.atomic(control.PRODUCTION / "progress.json", new)
    for row in resume["retained_pair_zips"]:
        (control.PRODUCTION / row["path"]).rename(
            control.PRODUCTION / row["path"].replace("pair.zip", "published.fixture")
        )
    m.prepare_reviewed_failures(control, False)  # published/cleaned scratch is not pinned forever
    new["status"] = "failed_checkpoints_retained"
    control.atomic(control.PRODUCTION / "progress.json", new)
    with pytest.raises(ValueError, match="Unreviewed V7"):
        m.prepare_reviewed_failures(control, True)


@pytest.mark.parametrize(
    "change",
    [
        "final",
        "summary",
        "lineage",
        "resume",
        "child",
        "parent",
        "zip",
        "extra_child",
        "extra_zip",
        "registry",
        "plan",
    ],
)
def test_unreviewed_changed_bytes_cannot_rearm_or_archive(reviewed, change):
    home, control, resume = reviewed
    work = control.PRODUCTION
    paths = {
        "final": work / "progress.json",
        "summary": work / "continuation_summary.json",
        "lineage": home / m.LINEAGE_NAME,
        "resume": home / m.RESUME_NAME,
        "child": work / resume["child_diagnostics"][0]["path"],
        "parent": work / resume["parent_diagnostics"][0]["path"],
        "zip": work / resume["retained_pair_zips"][0]["path"],
        "registry": home / "source_blocks.json",
        "plan": work / "months/2018-06/metadata/month.json",
    }
    if change == "extra_child":
        put(work / "months/2018-05/new/continuation_failure.json", b"{}")
    elif change == "extra_zip":
        put(work / "months/2018-06/accelerated_run/tasks/new/pair.zip", b"extra")
    else:
        put(paths[change], paths[change].read_bytes() + b" ")
    before = all_bytes(home)
    with pytest.raises(ValueError):
        m.prepare_reviewed_failures(control, True)
    assert all_bytes(home) == before


def test_interrupted_migration_can_resume_exact_archived_child(reviewed):
    home, control, resume = reviewed
    work = control.PRODUCTION
    row = resume["child_diagnostics"][0]
    source = work / row["path"]
    target = (
        work / "diagnostics/reviewed_v6_geolocation/files/wildfire-gcp-production-v1" / row["path"]
    )
    target.parent.mkdir(parents=True)
    source.rename(target)
    m.prepare_reviewed_failures(control, True)
    assert target.is_file() and not source.exists()


def test_changed_archive_blocks_even_nonfailed_v7_resume(reviewed):
    home, control, resume = reviewed
    work = control.PRODUCTION
    m.prepare_reviewed_failures(control, True)
    new = m.merged([], state(), "june_safe_days", m.REGISTRY_SHA, m.sha(Path(m.__file__)))
    control.atomic(work / "progress.json", new)
    archived = work / "diagnostics/reviewed_v6_geolocation/files" / m.RESUME_NAME
    put(archived, archived.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Pinned V6"):
        m.prepare_reviewed_failures(control, False)


@pytest.mark.parametrize(
    "kind,identity",
    [("pair", "N20:2018164.0018"), ("pair", "SNPP:2018164.1054"), ("day", "2018-06-13")],
)
def test_excluded_pairs_including_nonblocked_sensor_never_reach_science(
    tmp_path, monkeypatch, kind, identity
):
    root = tmp_path / "task"
    root.mkdir()
    plan = tmp_path / "plan.json"
    put(
        plan,
        json.dumps(
            {"pairs": [{"sample_id": identity, "start_utc": "2018-06-13T10:54:00Z"}]}
        ).encode(),
    )
    calls = []
    control = SimpleNamespace(
        PRODUCTION=tmp_path, ORIGINAL=tmp_path, atomic=lambda p, v: put(p, json.dumps(v).encode())
    )
    runner = SimpleNamespace(
        child_pair=lambda _: calls.append("pair"), child_day=lambda _: calls.append("day")
    )
    monkeypatch.setattr(
        m, "safe_failure", lambda *a: dict(error_type="ValueError", guard="CLASS_ONLY")
    )
    monkeypatch.setattr(
        m, "diagnostic_helper", lambda: SimpleNamespace(safe_error=lambda e: "CLASS_ONLY")
    )
    args = SimpleNamespace(root=root, child=kind, sample=identity, day=identity, plan=plan)
    with pytest.raises(ValueError):
        m.child(args, control, runner)
    assert calls == []
