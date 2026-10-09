"""No network/VM actions: immutable records, independent readbacks and bounded overlap."""

import contextlib
import datetime as dt
import hashlib
import importlib
import io
import json
import re
import subprocess
import sys
import tarfile
import threading
import time
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cloud"))
sys.path.insert(0, str(ROOT / "outputs/gcp_production/package"))
controller = importlib.import_module("run_gcp_acceleration")
module = importlib.import_module("accelerated_checkpoint_store")
engine = importlib.import_module("accelerated_pipeline")
legacy = importlib.import_module("verified_job_store")


class API:
    def __init__(self):
        self.rows, self.data, self.calls = {}, {}, []
        self.on_create = None

    def listing(self, query):
        self.calls.append("list")
        job = re.search(r"value='([a-f0-9]+)'", query)[1]
        name = re.search(r"name = '([^']+)'", query)
        return [
            {k: v for k, v in row.items() if k not in {"parents", "trashed"}}
            for row in self.rows.values()
            if row["appProperties"]["job"] == job and (not name or row["name"] == name[1])
        ]

    def request(self, path):
        identity = path.split("/")[2].split("?")[0]
        self.calls.append("media" if "alt=media" in path else "metadata")
        if "alt=media" in path:
            return self.data[identity]
        return json.dumps(self.rows[identity]).encode()

    def create_file(self, row, data):
        identity = "object_" + str(len(self.rows)).zfill(5)
        self.rows[identity] = {**row, "id": identity, "size": str(len(data)), "trashed": False}
        self.data[identity] = data
        self.calls.append("create")
        if self.on_create:
            self.on_create(identity, self.rows[identity], data)
        return identity


def payload(tmp_path):
    path = tmp_path / "payload.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("data.csv", "id,count\n1,2\n")
    return path


def test_completion_last_and_two_full_scientific_checks_with_fresh_remote_bytes(tmp_path):
    api = API()
    backend = module.IndexedDriveStore(api, "folder_12345")
    store = module.AcceleratedCheckpointStore(backend, "a" * 64, "b" * 64, 100000)
    checked = []

    def science(path):
        with zipfile.ZipFile(path) as archive:
            assert archive.read("data.csv") == b"id,count\n1,2\n"
        checked.append(path)

    def created(identity, row, data):
        if row["mimeType"] == "application/json":
            assert len(checked) == 2

    api.on_create = created
    source = payload(tmp_path)
    record = store.save("task", source, {"data.csv"}, science)
    assert len(checked) == 2 and checked[0] == source and checked[1] != source
    assert api.calls.count("media") == 3
    assert api.calls.count("create") == 2 and api.calls.count("list") == 3
    assert store.restore("task", {"data.csv"}, science) == record
    assert len(checked) == 3


def test_new_store_reads_legacy_checkpoint_without_creation_or_reprocessing(tmp_path):
    api = API()
    backend = module.IndexedDriveStore(api, "folder_12345")
    old = legacy.VerifiedJobStore(backend, "a" * 64, "b" * 64, 100000)
    source = payload(tmp_path)
    record = old.save("old_task", source, {"data.csv"}, lambda p: p.read_bytes())
    before = api.calls.count("create")
    refreshed = module.IndexedDriveStore(api, "folder_12345")
    new = module.AcceleratedCheckpointStore(refreshed, "a" * 64, "b" * 64, 100000)
    assert new.restore("old_task", {"data.csv"}, lambda p: p.read_bytes()) == record
    assert api.calls.count("create") == before


@pytest.mark.parametrize("when", ["payload", "marker"])
def test_changed_remote_bytes_never_return_success(tmp_path, when):
    api = API()
    backend = module.IndexedDriveStore(api, "folder_12345")
    store = module.AcceleratedCheckpointStore(backend, "a" * 64, "b" * 64, 100000)

    def change(identity, row, data):
        if (when == "payload" and row["mimeType"] == "application/zip") or (
            when == "marker" and row["mimeType"] == "application/json"
        ):
            api.data[identity] = bytes([data[0] ^ 1]) + data[1:]

    api.on_create = change
    with pytest.raises(ValueError):
        store.save("task", payload(tmp_path), {"data.csv"}, lambda p: None)


def test_parent_change_and_duplicate_live_objects_refused(tmp_path):
    api = API()
    backend = module.IndexedDriveStore(api, "folder_12345")
    key = "jobs/" + "a" * 64 + "/object.zip"
    backend.create(key, b"bytes")
    identity = next(iter(api.rows))
    api.rows[identity]["parents"] = ["another_folder"]
    with pytest.raises(ValueError, match="parent/trash"):
        backend.get(key)
    api.rows[identity]["parents"] = ["folder_12345"]
    api.rows["other_id_123"] = dict(api.rows[identity], id="other_id_123")
    with pytest.raises(ValueError, match="Duplicate"):
        backend.create(key, b"bytes")


def test_orphan_payload_has_no_completion(tmp_path):
    api = API()
    backend = module.IndexedDriveStore(api, "folder_12345")
    store = module.AcceleratedCheckpointStore(backend, "a" * 64, "b" * 64, 100000)
    data = payload(tmp_path).read_bytes()
    key = store.task_prefix("task") + "/" + hashlib.sha256(data).hexdigest() + ".zip"
    backend.create(key, data)
    assert store.restore("task", {"data.csv"}, lambda p: None) is None


def test_collision_and_quota_prevent_false_completion(tmp_path):
    api = API()
    backend = module.IndexedDriveStore(api, "folder_12345")
    store = module.AcceleratedCheckpointStore(backend, "a" * 64, "b" * 64, 1)
    with pytest.raises(ValueError, match="budget"):
        store.save("task", payload(tmp_path), {"data.csv"}, lambda p: None)
    assert not api.rows
    key = "jobs/" + "a" * 64 + "/key.zip"
    backend.create(key, b"unchanged")
    with pytest.raises(ValueError, match="collision"):
        backend.create(key, b"changed")


def test_daily_union_overlaps_next_days_pairs_and_science_callbacks_are_serial():
    main = threading.get_ident()
    next_day_active, reduce_started = threading.Event(), threading.Event()
    callback_threads = []
    lock = threading.Lock()
    active, peak = 0, 0

    def prepare(day):
        callback_threads.append(threading.get_ident())
        return {"day": day, "pending": [day + ":a", day + ":b"]}

    def pair(state, identity):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        if state["day"] == "day2":
            next_day_active.set()
            assert reduce_started.wait(timeout=3)
        time.sleep(0.01)
        with lock:
            active -= 1
        return identity

    def daily(state):
        if state["day"] == "day1":
            assert next_day_active.wait(timeout=3)
            reduce_started.set()
        return state["day"]

    def publish_pair(state, identity, value):
        callback_threads.append(threading.get_ident())
        assert value == identity

    def publish_day(state, value):
        callback_threads.append(threading.get_ident())
        return {"day": value}

    result = engine.execute(
        ["day1", "day2", "day3"],
        prepare,
        pair,
        publish_pair,
        daily,
        publish_day,
        2,
        1,
        time.monotonic() + 30,
        lambda: True,
        reduce_started.set,
        reserve=1,
        window=3,
    )
    assert result["status"] == "complete" and len(result["day_records"]) == 3
    assert peak <= 2 and active == 0 and set(callback_threads) == {main}
    assert reduce_started.is_set()


def test_existing_days_reused_without_launching_any_child():
    def prepare(day):
        return {"day": day, "reused": {"day": day}}

    def forbidden(*args):
        pytest.fail("Completed data must not be recomputed")

    result = engine.execute(
        ["d1", "d2"],
        prepare,
        forbidden,
        forbidden,
        forbidden,
        forbidden,
        2,
        1,
        time.monotonic() + 30,
        lambda: True,
        lambda: None,
        reserve=1,
    )
    assert result["status"] == "complete" and len(result["day_records"]) == 2


def test_reserve_pauses_without_admitting_work():
    called = []
    result = engine.execute(
        ["d1"],
        lambda d: called.append(d),
        None,
        None,
        None,
        None,
        2,
        1,
        time.monotonic() + 1,
        lambda: True,
        lambda: None,
        reserve=20,
    )
    assert result["status"] == "paused_at_runtime_reserve" and not called


@pytest.mark.parametrize("cpus,reducers", [(25, 1), (1, 5), (0, 1)])
def test_unbounded_resource_parameters_refused(cpus, reducers):
    with pytest.raises(ValueError, match="bounds"):
        engine.execute(
            [], None, None, None, None, None, cpus, reducers, 0, lambda: True, lambda: None
        )


def test_budget_trial_and_eight_hour_bound():
    now = dt.datetime(2026, 10, 8, tzinfo=dt.UTC)
    assert controller.budget((now + dt.timedelta(hours=8)).isoformat(), False, now) == 28500
    with pytest.raises(ValueError):
        controller.budget((now + dt.timedelta(hours=8)).isoformat(), True, now)
    with pytest.raises(ValueError):
        controller.budget("2026-10-26T00:00:00Z", False, now)


def test_failed_pair_stops_own_children_without_daily_completion():
    stopped, published = [], []

    def fail(*args):
        raise RuntimeError("child failed")

    with pytest.raises(RuntimeError, match="child failed"):
        engine.execute(
            ["day"],
            lambda d: {"day": d, "pending": ["pair"]},
            fail,
            lambda *a: published.append(a),
            None,
            lambda *a: published.append(a),
            1,
            1,
            time.monotonic() + 30,
            lambda: True,
            lambda: stopped.append(True),
            reserve=1,
        )
    assert stopped == [True] and not published


@pytest.mark.parametrize("failure", ["integrity", "export", "telemetry"])
def test_supervisor_still_requests_stop_when_finalization_fails(tmp_path, monkeypatch, failure):
    events = []
    monkeypatch.setattr(controller, "production_lock", contextlib.nullcontext)
    sampler = SimpleNamespace(
        begin=lambda: None,
        close=lambda: events.append("telemetry"),
    )
    if failure == "telemetry":

        def broken_close():
            raise ValueError("telemetry failed")

        sampler.close = broken_close
    monkeypatch.setattr(controller, "Sampler", lambda _: sampler, raising=False)
    monkeypatch.setattr(controller, "proof", lambda *a: None)

    def fail():
        raise ValueError("finalization failed")

    monkeypatch.setattr(controller, "checked", fail if failure == "integrity" else lambda: None)
    monkeypatch.setattr(controller, "export_proof", lambda _: fail())
    monkeypatch.setattr(
        controller.subprocess,
        "run",
        lambda command, **kw: events.append(command) or SimpleNamespace(returncode=0),
    )
    reference = SimpleNamespace(
        install_alarm=lambda _: lambda: events.append("cancel"),
        kill_active=lambda: events.append("kill"),
    )
    with pytest.raises(ValueError):
        controller.supervise(
            SimpleNamespace(mode="proof", poweroff=True),
            None,
            None,
            None,
            None,
            reference,
            30,
            tmp_path / "work",
        )
    assert events[-1] == ["sudo", "-n", "shutdown", "-h", "now"]
    assert "kill" in events


def test_rejected_duplicate_supervisor_never_stops_owner(tmp_path, monkeypatch):
    @contextlib.contextmanager
    def occupied():
        raise BlockingIOError("owner running")
        yield

    monkeypatch.setattr(controller, "production_lock", occupied)
    monkeypatch.setattr(controller.subprocess, "run", lambda *a, **kw: pytest.fail("Stop owner"))
    with pytest.raises(BlockingIOError):
        controller.supervise(
            SimpleNamespace(mode="proof", poweroff=True),
            None,
            None,
            None,
            None,
            None,
            30,
            tmp_path,
        )


def test_unverified_gate_refuses_before_any_work(tmp_path):
    gate = {
        "protocol": "gcp_acceleration_ready_v1",
        "controller_manifest_sha256": "a" * 64,
        "status": "independent_acceleration_readback_passed",
        "cpus": 32,
        "baseline_stable": True,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "verified_daily_payloads": 12,
        "pair_slots": 24,
        "daily_slots": 4,
    }
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate))
    args = SimpleNamespace(gate=path, gate_sha=controller.digest(path), cpus=32)
    assert controller.read_gate(args, "a" * 64)["pair_slots"] == 24
    gate["pair_slots"] = 32
    path.write_text(json.dumps(gate))
    args.gate_sha = controller.digest(path)
    with pytest.raises(ValueError, match="CPU budget"):
        controller.read_gate(args, "a" * 64)
    args.gate_sha = "0" * 64
    with pytest.raises(ValueError, match="gate required"):
        controller.read_gate(args, "a" * 64)


def test_real_native_pair_and_daily_pipeline_keep_science_and_legacy_scope(tmp_path):
    """Fixture pair outputs; a real separate daily subprocess, never a raw-speed claim."""
    received = ROOT / "outputs/gcp_production/received/gcp_production_first_session_results.tar.gz"
    tuning = ROOT / "outputs/gcp_tuning/wildfire_gcp_tuning.zip"
    if not received.exists() or not tuning.exists():
        pytest.skip("Ignored real products unavailable")
    original = importlib.import_module("run_gcp_production")
    with zipfile.ZipFile(tuning) as source:
        approved = json.loads(source.read("tuning_plan.json"))
        meta = tmp_path / "metadata"
        meta.mkdir()
        with zipfile.ZipFile(io.BytesIO(source.read("month_manifest.zip"))) as archive:
            archive.extractall(meta)
    plan = json.loads((meta / "month.json").read_text())
    day = "2023-10-15"
    saved = {}
    with tarfile.open(received) as archive:
        for member in archive:
            if member.isfile() and member.name.startswith("days/2023-10-15/inputs/"):
                saved[Path(member.name).name] = archive.extractfile(member).read()
    core = tmp_path / "core"
    original.template(ROOT / "outputs/gcp_production/package", core)
    work = tmp_path / "pipeline"
    work.mkdir()
    controller.pair_validator = module.pair_validator
    controller.execute = engine.execute
    worker = original.digest(ROOT / "outputs/gcp_production/package/run_gcp_production.py")
    store = module.AcceleratedCheckpointStore(
        legacy.RehearsalFileStore(tmp_path / "store"),
        controller.ORIGINAL_SCOPE,
        worker,
        500_000_000,
    )

    def child(runner, kind, root, plan_path, identity, auth, deadline, sampler):
        started = time.monotonic()
        if kind == "pair":
            pair = next(p for p in plan["pairs"] if p["sample_id"] == identity)
            with zipfile.ZipFile(
                root / "pair.zip", "w", compression=zipfile.ZIP_DEFLATED
            ) as archive:
                for name, data in saved.items():
                    if name.startswith(pair["stem"] + "_"):
                        archive.writestr(name, data)
        else:
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "outputs/gcp_production/package/run_gcp_production.py"),
                    "--child",
                    "day",
                    "--root",
                    str(root),
                    "--plan",
                    str(plan_path),
                    "--day",
                    identity,
                ],
                env=original.environment(),
                check=True,
                capture_output=True,
                timeout=300,
            )
        return time.monotonic() - started

    reference = SimpleNamespace(run_child=child, kill_active=lambda: None)
    sampler = SimpleNamespace(failed=False, summary=lambda _: {"valid": False})
    result = controller.pipeline(
        original,
        reference,
        work,
        core,
        meta,
        meta / "month.json",
        plan,
        [day],
        store,
        None,
        time.monotonic() + 1800,
        sampler,
        "fixture",
        4,
        1,
    )
    assert (
        result["status"] == "complete" and result["pair_count"] == 10 and result["day_count"] == 1
    )
    with zipfile.ZipFile(work / (day + ".zip")) as archive:
        report = json.loads(archive.read("report.json"))
    assert len(report["pair_ids"]) == 10 and report["negative_label_permitted"] is False
    assert all(
        r["completion"]["manifest_sha256"] == controller.ORIGINAL_SCOPE
        and r["completion"]["task_id"] == r["sample_id"]
        for r in result["pairs"]
    )
    for saved_pair in report["sources"]:
        expected = approved["references"][saved_pair["sample_id"]]
        assert all(
            saved_pair["audit"]["sources"][role]["sha256"] == checksum
            for role, checksum in expected["source_sha256"].items()
        )
    restored_root = tmp_path / "legacy_readback"
    pairs = [p for p in plan["pairs"] if p["start_utc"].startswith(day)]
    original.ensure_root(restored_root, core, meta, pairs)
    context = {
        "production_month_manifest_sha256": controller.digest(meta / "month.json"),
        "catalogue_gap_records": [r for r in plan["unpaired_catalogue_records"] if r["day"] == day],
    }
    compact, _ = original.science(restored_root)
    old_store = legacy.VerifiedJobStore(
        store.backend, controller.ORIGINAL_SCOPE, worker, 500_000_000
    )
    restored = old_store.restore(
        "day:" + day,
        set(compact.NAMES),
        lambda path: original.restore_daily(path, restored_root, day, pairs, context),
    )
    assert restored == result["day_records"][day]
    warm = tmp_path / "warm"
    warm.mkdir()
    resumed = controller.pipeline(
        original,
        SimpleNamespace(
            run_child=lambda *a: pytest.fail("Completed day redownloaded"), kill_active=lambda: None
        ),
        warm,
        core,
        meta,
        meta / "month.json",
        plan,
        [day],
        store,
        None,
        time.monotonic() + 1800,
        sampler,
        "fixture",
        4,
        1,
    )
    assert resumed["pair_count"] == 0 and resumed["day_records"] == result["day_records"]


@pytest.fixture
def acceleration_readback_fixture(tmp_path):
    """Real source/daily products, artificial benchmark clocks and CPU profile labels."""
    package = ROOT / "outputs/gcp_acceleration/wildfire_gcp_acceleration.zip"
    received = ROOT / "outputs/gcp_tuning/received/gcp_tuning_results.zip"
    if not package.exists() or not received.exists():
        pytest.skip("Ignored real products unavailable")
    with zipfile.ZipFile(package) as prepared:
        files = {
            n: prepared.read(n)
            for n in ("acceleration_manifest.json", "proof_plan.json", "month_manifest.zip")
        }
    spec = json.loads(files["acceleration_manifest.json"])
    scope = hashlib.sha256(files["acceleration_manifest.json"]).hexdigest()
    mapping = dict(
        zip(
            ["four_before", "eight", "twelve", "four_after"],
            ["baseline_before", "pipeline_eight", "pipeline_scaled", "baseline_after"],
            strict=True,
        )
    )
    workers, daily, timings = [8, 8, 24, 8], [1, 1, 4, 1], [800, 500, 300, 810]
    with zipfile.ZipFile(received) as source:
        summary = json.loads(source.read("result_summary.json"))
        arms = summary["arms"]
        for i, arm in enumerate(arms):
            label = mapping[arm["arm"]]
            arm.update(
                arm=label, workers=workers[i], daily_workers=daily[i], wall_seconds=timings[i]
            )
            for row in [*arm["pairs"], *arm["days"]]:
                marker = row["completion"]
                task = (
                    label + ":" + (row["sample_id"] if "sample_id" in row else "day:" + row["day"])
                )
                marker.update(
                    task_id=task,
                    manifest_sha256=scope,
                    worker_sha256=spec["files"]["run_gcp_acceleration.py"],
                    payload_key=f"jobs/{scope}/{hashlib.sha256(task.encode()).hexdigest()}/"
                    + marker["payload_sha256"]
                    + ".zip",
                )
            files[label + "/arm_summary.json"] = json.dumps(arm).encode()
            old_label = list(mapping)[i]
            for day in spec["proof_days"]:
                files[label + "/" + day + ".zip"] = source.read(old_label + "/" + day + ".zip")
        telemetry = source.read("resource_samples.csv").decode()
        for old, new in mapping.items():
            telemetry = telemetry.replace("," + old + ",", "," + new + ",")
        files["resource_samples.csv"] = telemetry.encode()
        files["result_summary.json"] = json.dumps(
            {
                "status": "all_profiles_completed",
                "arms": arms,
                "cpus": 32,
                "controller_manifest_sha256": scope,
                "original_scope_sha256": controller.ORIGINAL_SCOPE,
                "negative_label_permitted": False,
                "daily_observation_status": "unknown",
                "production_months_added": 0,
                "production_progress_unchanged": True,
                "resource_guard_hit": False,
            }
        ).encode()
    target = tmp_path / "results.zip"

    def write():
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        return target

    return write, files, package


def test_partial_proof_has_no_production_gate(tmp_path, acceleration_readback_fixture):
    write, files, package = acceleration_readback_fixture
    summary = json.loads(files["result_summary.json"])
    summary["status"] = "partial_proof_retained"
    files["result_summary.json"] = json.dumps(summary).encode()
    reader = importlib.import_module("verify_gcp_acceleration_results")
    output = tmp_path / "readback"
    with pytest.raises(ValueError, match="partial has no gate"):
        reader.verify(write(), package, output)
    assert not (output / "production_readiness.json").exists()


def test_real_acceleration_archive_readback_and_gate(tmp_path, acceleration_readback_fixture):
    write, _, package = acceleration_readback_fixture
    reader = importlib.import_module("verify_gcp_acceleration_results")
    result = reader.verify(write(), package, tmp_path / "readback")
    assert result["verified_daily_payloads"] == 12 and result["pair_slots"] == 24
    assert result["daily_slots"] == 4 and result["baseline_stable"] is True
    assert result["negative_label_permitted"] is False
    assert len(result["resource_readback"]) == 4
    args = SimpleNamespace(gate=Path(result["gate_file"]), gate_sha=result["gate_sha256"], cpus=32)
    assert controller.read_gate(args, result["controller_manifest_sha256"])["daily_slots"] == 4


def test_manual_guide_installer_and_overwrite_rejection(tmp_path, monkeypatch):
    package = ROOT / "outputs/gcp_acceleration/wildfire_gcp_acceleration.zip"
    guide = (ROOT / "docs/GCP_ACCELERATION_2026-10-08.md").read_text(encoding="utf-8")
    program = re.search(r"(?s)```bash\n.*?<<'PY'\n(.*?)\nPY\n```", guide)[1]
    home = tmp_path / "home"
    home.mkdir()
    (home / package.name).write_bytes(package.read_bytes())
    monkeypatch.setattr(Path, "home", lambda: home)
    exec(compile(program, "manual_install", "exec"), {})
    destination = home / "wildfire-gcp-acceleration-package"
    assert len(list(destination.iterdir())) == 9
    with pytest.raises(AssertionError, match="mevcut"):
        exec(compile(program, "manual_install", "exec"), {})


def test_pinned_controller_rejects_changed_member_before_import(tmp_path, monkeypatch):
    with zipfile.ZipFile(
        ROOT / "outputs/gcp_acceleration/wildfire_gcp_acceleration.zip"
    ) as archive:
        archive.extractall(tmp_path)
    monkeypatch.setattr(controller, "PACKAGE", tmp_path)
    monkeypatch.setattr(controller, "ORIGINAL", ROOT / "outputs/gcp_production/package")
    # Other collected tests import the repository worker under the same module name.
    # Model the fresh VM process here; keep the production identity guard intact.
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.delitem(sys.modules, "run_gcp_production", raising=False)
    _, scope, _ = controller.checked()
    assert scope == controller.digest(tmp_path / "acceleration_manifest.json")
    (tmp_path / "gcp_tuning_resources.py").write_text("changed\n")
    with pytest.raises(ValueError, match="member SHA"):
        controller.checked()


def test_accelerated_month_checker_accepts_old_month_and_rejects_bad_nested_marker(tmp_path):
    """The all-month resume path must accept the existing full 31-day August receipt."""
    received = ROOT / "outputs/gcp_production/received/gcp_production_first_session_results.tar.gz"
    if not received.exists():
        pytest.skip("Ignored real products unavailable")
    original = importlib.import_module("run_gcp_production")
    production = importlib.import_module("accelerated_production")
    with tarfile.open(received) as archive:
        metadata_zip = archive.extractfile("months/2023-08/manifest.zip").read()
        month_zip = archive.extractfile("months/2023-08/month_results.zip").read()
    metadata = tmp_path / "metadata"
    metadata.mkdir()
    with zipfile.ZipFile(io.BytesIO(metadata_zip)) as archive:
        archive.extractall(metadata)
    plan = json.loads((metadata / "month.json").read_text())
    core, template = tmp_path / "science", tmp_path / "template"
    original.template(ROOT / "outputs/gcp_production/package", template)
    original.ensure_root(core, template, metadata, plan["pairs"])
    worker = controller.digest(ROOT / "outputs/gcp_production/package/run_gcp_production.py")
    _, check = production.month_validator(
        original,
        core,
        "2023-08",
        plan,
        controller.digest(metadata / "month.json"),
        controller.ORIGINAL_SCOPE,
        worker,
    )
    path = tmp_path / "month.zip"
    path.write_bytes(month_zip)
    check(path)
    with zipfile.ZipFile(io.BytesIO(month_zip)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    receipt = json.loads(files["receipt.json"])
    receipt["day_records"][plan["days"][0]]["worker_sha256"] = "0" * 64
    files["receipt.json"] = json.dumps(receipt).encode()
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    with pytest.raises(ValueError, match="nested completion"):
        check(path)
