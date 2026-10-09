"""Tuning scheduling, cold-reference, safety and readback guards; no speed claim."""

import datetime as dt
import importlib
import io
import json
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
runner = importlib.import_module("run_gcp_tuning")
resources = importlib.import_module("gcp_tuning_resources")
reader = importlib.import_module("verify_gcp_tuning_results")
builder = importlib.import_module("build_gcp_tuning_bundle")


@pytest.mark.parametrize("seconds", [4200, 6000, 7200])
def test_two_hour_runtime_preserves_export_reserve(seconds):
    now = dt.datetime(2026, 10, 8, tzinfo=dt.UTC)
    value = (now + dt.timedelta(seconds=seconds)).isoformat()
    limit = runner.remaining_seconds(value, now)
    assert limit <= 5400 and limit <= seconds - 900


@pytest.mark.parametrize("seconds", [4199, 7261, 8 * 3600])
def test_wrong_or_stale_google_deadline_refused(seconds):
    now = dt.datetime(2026, 10, 8, tzinfo=dt.UTC)
    with pytest.raises(ValueError):
        runner.remaining_seconds((now + dt.timedelta(seconds=seconds)).isoformat(), now)


def test_trial_date_and_missing_timezone_refused():
    now = dt.datetime(2026, 10, 23, 23, tzinfo=dt.UTC)
    with pytest.raises(ValueError, match="Trial safety"):
        runner.remaining_seconds((now + dt.timedelta(hours=2)).isoformat(), now)
    with pytest.raises(ValueError, match="timezone"):
        runner.remaining_seconds("2026-10-08T02:00:00")


def test_watchdog_covers_stalled_main_thread_io_and_restores_handler(monkeypatch):
    monkeypatch.setattr(runner.signal, "SIGALRM", 14, raising=False)
    monkeypatch.setattr(runner.signal, "ITIMER_REAL", 0, raising=False)
    monkeypatch.setattr(runner.signal, "getsignal", lambda _: "previous")
    handlers, timers = [], []
    monkeypatch.setattr(runner.signal, "signal", lambda event, handler: handlers.append(handler))
    monkeypatch.setattr(
        runner.signal, "setitimer", lambda event, delay: timers.append(delay), raising=False
    )
    cancel = runner.install_alarm(time.monotonic() + 10)
    assert 0 < timers[0] <= 10
    with pytest.raises(TimeoutError, match="active budget"):
        handlers[0](14, None)
    cancel()
    assert timers[-1] == 0 and handlers[-1] == "previous"


def test_cpu_guest_not_double_counted_and_loopback_excluded():
    assert resources.cpu_times("cpu 10 2 3 40 5 1 2 7 9 1\n") == (70, 40, 5, 7)
    assert resources.memory_values("MemTotal: 100 kB\nMemAvailable: 70 kB\n") == (102400, 71680)
    assert resources.net_bytes("lo: 99 0 0 0 0 0 0 0 88\nens4: 10 0 0 0 0 0 0 0 20") == (10, 20)


def test_resource_shortage_trips_guard_not_false_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "descendant_rss", lambda _: (100, 1))
    monkeypatch.setattr(resources.shutil, "disk_usage", lambda _: SimpleNamespace(free=3 * 2**30))

    def read(path):
        return {
            "/proc/stat": "cpu 10 0 0 70 5 0 0 15 0 0",
            "/proc/meminfo": "MemTotal: 33554432 kB\nMemAvailable: 31457280 kB",
            "/proc/net/dev": "ens4: 1 0 0 0 0 0 0 0 2",
        }[path.as_posix()]

    monkeypatch.setattr(Path, "read_text", read)
    sampler = resources.Sampler(tmp_path)
    sampler.collect((0, 0, 0, 0))
    assert sampler.failed and sampler.rows[0]["cpu_busy_pct"] == 10


def test_missing_resource_sample_aborts_instead_of_claiming_zero(tmp_path, monkeypatch):
    sampler = resources.Sampler(tmp_path)

    def fail(_):
        sampler.stop_event.set()
        raise OSError("missing /proc")

    monkeypatch.setattr(sampler, "collect", fail)
    sampler.loop()
    assert sampler.failed and sampler.summary("eight") == {"valid": False}


def test_failed_child_terminates_its_own_remaining_process_group(monkeypatch):
    monkeypatch.setattr(runner.signal, "SIGKILL", 9, raising=False)
    process = SimpleNamespace(pid=43210, returncode=1, poll=lambda: 1)
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **kw: process)
    killed = []
    monkeypatch.setattr(
        runner.os, "killpg", lambda pid, sig: killed.append((pid, sig)), raising=False
    )
    with pytest.raises(ValueError, match="scientific child failed"):
        runner.run_child(
            SimpleNamespace(environment=lambda _: {}),
            "pair",
            Path("child"),
            Path("plan"),
            "p",
            None,
            time.monotonic() + 1000,
            SimpleNamespace(failed=False),
        )
    assert [pid for pid, _ in killed] == [43210] and runner.ACTIVE == {}


@pytest.mark.parametrize("workers", [4, 8, 12])
def test_bounded_refill_while_publishing_and_all_three_days_retained(
    tmp_path, monkeypatch, workers
):
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(runner, "WORK", work)
    pairs = [
        {"sample_id": f"s{index}", "stem": f"s{index}", "start_utc": day + "T01:00:00"}
        for index, day in enumerate(
            [builder.DAYS[0]] * 9 + [builder.DAYS[1]] * 9 + [builder.DAYS[2]] * 10
        )
    ]
    lock = threading.Lock()
    active = peak = started = 0
    refill = threading.Event()
    initial_ready = threading.Barrier(workers)

    def child(_, kind, root, *args):
        nonlocal active, peak, started
        if kind == "pair":
            with lock:
                active += 1
                peak = max(peak, active)
                started += 1
                if started > workers:
                    refill.set()
                initial = started <= workers
            if initial:
                initial_ready.wait(timeout=5)
            time.sleep(0.02)
            (root / "pair.zip").write_bytes(b"fixture")
            with lock:
                active -= 1
        else:
            (root / "day.zip").write_bytes(b"daily fixture")
        return 0.02

    def ensure(root, core, meta, selected):
        (root / "inputs").mkdir(parents=True)

    def pair_check(_, root, pair, *args):
        def check(path):
            assert path.is_file()
            (root / "inputs" / (pair["stem"] + "_checkpoint.json")).write_text(
                json.dumps({"metrics": {"downloaded_payload_bytes": 100}})
            )

        return SimpleNamespace(), check

    calls = []

    def save(task, payload, names, check):
        if not calls:
            # Admission must continue while the publisher is busy.
            assert refill.wait(timeout=1)
        check(payload)
        calls.append(task)
        time.sleep(0.005)
        return {"task_id": task}

    fake = SimpleNamespace(
        ensure_root=ensure,
        pair_names=lambda *args: {"fixture"},
        owned_remove=lambda *args: None,
        science=lambda _: (SimpleNamespace(NAMES=["fixture"]), None),
        restore_daily=lambda *args: True,
    )
    plan = tmp_path / "month.json"
    plan.write_text("{}")
    monkeypatch.setattr(runner, "run_child", child)
    monkeypatch.setattr(runner, "pair_check", pair_check)
    sampler = SimpleNamespace(failed=False, summary=lambda _: {"valid": True})
    result = runner.execute_arm(
        "probe",
        workers,
        fake,
        tmp_path,
        tmp_path,
        plan,
        {"unpaired_catalogue_records": []},
        pairs,
        {p["sample_id"]: {} for p in pairs},
        SimpleNamespace(save=save),
        None,
        time.monotonic() + 3000,
        sampler,
    )
    assert peak == workers and active == 0 and started == 28
    assert len(calls) == len(set(calls)) == 31
    assert result["pair_count"] == 28 and result["day_count"] == 3
    # Existing work cannot be mistaken for another cold run.
    with pytest.raises(ValueError, match="fresh work root"):
        runner.execute_arm(
            "probe",
            workers,
            fake,
            None,
            None,
            plan,
            {},
            [],
            {},
            None,
            None,
            time.monotonic() + 3000,
            sampler,
        )


def test_changed_reference_raw_size_refused():
    pair = {"sample_id": "p", "stem": "p", "sources": [{"role": "fire", "bytes": 10}]}
    audit = {"sample_id": "p", "negative_label_permitted": False, "sources": {"fire": {"bytes": 9}}}
    with pytest.raises(ValueError, match="source size"):
        builder.reference(pair, audit, {})


def samples():
    return [
        {
            "arm": arm,
            "phase": "pairs",
            "cpu_busy_pct": "50",
            "cpu_iowait_pct": "0",
            "cpu_steal_pct": "0",
            "mem_available_bytes": str(20 * 2**30),
            "disk_free_bytes": str(10 * 2**30),
            "process_tree_rss_bytes": str(3 * 2**30),
        }
        for arm, _ in builder.ARMS
        for _ in range(5)
    ]


def arms(times):
    return [
        {"arm": arm, "workers": workers, "wall_seconds": seconds, "pair_count": 28, "day_count": 3}
        for (arm, workers), seconds in zip(builder.ARMS, times, strict=True)
    ]


def test_recommendation_prefers_eight_when_twelve_only_marginally_faster():
    result = reader.decision(arms([800, 440, 430, 800]), samples())
    assert result["candidate_workers_for_next_validated_runner"] == 8
    assert result["deployment_automatic"] is False


@pytest.mark.parametrize("times", [[800, 400, 300, 1400], [800, 790, 780, 800]])
def test_unstable_baseline_or_no_real_gain_cannot_recommend_more_workers(times):
    assert (
        reader.decision(arms(times), samples())["candidate_workers_for_next_validated_runner"]
        is None
    )


def test_resource_breach_and_nan_timing_refused():
    rows = samples()
    rows[-1]["disk_free_bytes"] = "10"
    with pytest.raises(ValueError, match="reserve"):
        reader.decision(arms([800, 400, 300, 800]), rows)
    with pytest.raises(ValueError, match="timing"):
        reader.decision(arms([800, float("nan"), 300, 800]), samples())


def test_duplicate_and_private_result_members_refused(tmp_path):
    target = tmp_path / "bad.zip"
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("../drive_connection.json", b"private")
    with zipfile.ZipFile(target) as archive, pytest.raises(ValueError, match="Unexpected"):
        reader.members(archive, {"result_summary.json"}, 10000)


def test_actual_reference_population_and_built_package_hashes(tmp_path, monkeypatch):
    source = ROOT / "outputs/gcp_tuning/wildfire_gcp_tuning.zip"
    if not source.exists():
        pytest.skip("Ignored tuning package unavailable")
    with zipfile.ZipFile(source) as archive:
        assert len(archive.namelist()) == 5 and archive.testzip() is None
        archive.extractall(tmp_path)
    spec = json.loads((tmp_path / "tuning_manifest.json").read_text())
    plan = json.loads((tmp_path / "tuning_plan.json").read_text())
    assert spec["nominal_raw_download_bytes"] == 20_559_071_684
    assert len(plan["sample_ids"]) == len(set(plan["sample_ids"])) == len(plan["references"]) == 28
    assert plan["days"] == builder.DAYS and spec["arms"] == builder.ARMS
    monkeypatch.setattr(runner, "PACKAGE", tmp_path)
    monkeypatch.setattr(runner, "ORIGINAL", ROOT / "outputs/gcp_production/package")
    checked, scope, _ = runner.checked_package()
    assert checked == spec and scope != runner.ORIGINAL_SCOPE
    (tmp_path / "gcp_tuning_resources.py").write_text("changed")
    with pytest.raises(ValueError, match="member SHA"):
        runner.checked_package()


def test_partial_profile_cannot_produce_speed_recommendation(tmp_path):
    package = ROOT / "outputs/gcp_tuning/wildfire_gcp_tuning.zip"
    if not package.exists():
        pytest.skip("Ignored tuning package unavailable")
    source = tmp_path / "partial.zip"
    with zipfile.ZipFile(package) as prepared, zipfile.ZipFile(source, "w") as target:
        spec_bytes = prepared.read("tuning_manifest.json")
        spec = json.loads(spec_bytes)
        for name in ("tuning_manifest.json", "tuning_plan.json", "month_manifest.zip"):
            target.writestr(name, prepared.read(name))
        summary = {
            "status": "partial_test_retained",
            "tuning_scope_sha256": builder.sha(spec_bytes),
            "original_production_scope_sha256": spec["original_production_scope_sha256"],
            "arms": [],
            "negative_label_permitted": False,
            "daily_observation_status": "unknown",
            "production_months_added": 0,
        }
        target.writestr("result_summary.json", json.dumps(summary))
        target.writestr("resource_samples.csv", "arm,phase\n")
    result = reader.verify(source, package, tmp_path / "result")
    assert result["status"] == "partial_test_no_speed_recommendation"
    assert "candidate_workers_for_next_validated_runner" not in result


def test_documented_installer_verifies_package_and_refuses_overwrite(tmp_path, monkeypatch):
    package = ROOT / "outputs/gcp_tuning/wildfire_gcp_tuning.zip"
    if not package.exists():
        pytest.skip("Ignored tuning package unavailable")
    guide = (ROOT / "docs/GCP_PARALLEL_TUNING_2026-10-08.md").read_text(encoding="utf-8")
    program = guide.split("<<'PY'\n", 1)[1].split("\nPY", 1)[0]
    (tmp_path / package.name).write_bytes(package.read_bytes())
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    exec(compile(program, "reviewed guide installer", "exec"), {})
    target = tmp_path / "wildfire-gcp-tuning-package"
    assert len(list(target.iterdir())) == 5
    with pytest.raises(AssertionError, match="zaten var"):
        exec(compile(program, "reviewed guide installer", "exec"), {})


def test_native_received_pair_can_be_saved_and_readback_in_separate_tuning_scope(tmp_path):
    """Replay existing scientific products; does not measure Linux/download performance."""
    package = ROOT / "outputs/gcp_tuning/wildfire_gcp_tuning.zip"
    received = ROOT / "outputs/gcp_production/received/gcp_production_first_session_results.tar.gz"
    if not package.exists() or not received.exists():
        pytest.skip("Ignored verified artifacts unavailable")
    sys.path.insert(0, str(ROOT / "outputs/gcp_production/package"))
    original = importlib.import_module("run_gcp_production")
    with zipfile.ZipFile(package) as archive:
        plan = json.loads(archive.read("tuning_plan.json"))
        metadata = tmp_path / "metadata"
        metadata.mkdir()
        with zipfile.ZipFile(io.BytesIO(archive.read("month_manifest.zip"))) as month_zip:
            month_zip.extractall(metadata)
        scope = builder.sha(archive.read("tuning_manifest.json"))
        worker = json.loads(archive.read("tuning_manifest.json"))["files"]["run_gcp_tuning.py"]
    month = json.loads((metadata / "month.json").read_text())
    pair = next(p for p in month["pairs"] if p["start_utc"].startswith(builder.DAYS[-1]))
    core, dayroot = tmp_path / "core", tmp_path / "day"
    original.template(ROOT / "outputs/gcp_production/package", core)
    original.ensure_root(dayroot, core, metadata, [pair])
    payload = tmp_path / "pair.zip"
    with (
        tarfile.open(received) as source,
        zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as dest,
    ):
        prefix = f"days/{builder.DAYS[-1]}/inputs/"
        for entry in source.getmembers():
            name = entry.name.removeprefix(prefix)
            if entry.isfile() and entry.name.startswith(prefix + pair["stem"] + "_"):
                dest.writestr(name, source.extractfile(entry).read())
    native, check = runner.pair_check(
        original,
        dayroot,
        pair,
        runner.sha(metadata / "month.json"),
        plan["references"][pair["sample_id"]],
    )

    class MemoryBackend:
        def __init__(self):
            self.files = {}

        def get(self, key):
            return self.files.get(key)

        def create(self, key, data):
            assert key.startswith("jobs/" + scope + "/")
            assert runner.ORIGINAL_SCOPE not in key
            self.files[key] = data

        def used_bytes(self, prefix):
            return sum(len(v) for k, v in self.files.items() if k.startswith(prefix))

    store = original.VerifiedJobStore(MemoryBackend(), scope, worker, 100_000_000)
    task = "four_before:" + pair["sample_id"]
    marker = store.save(task, payload, original.pair_names(pair, native), check)
    assert store.restore(task, original.pair_names(pair, native), check) == marker
    reader.marker(marker, task, scope, worker, payload.read_bytes())
    wrong = dict(plan["references"][pair["sample_id"]])
    wrong["exact_csv_sha256"] = dict(wrong["exact_csv_sha256"], **{"grid_centers.csv": "0" * 64})
    _, invalid = runner.pair_check(
        original, dayroot, pair, runner.sha(metadata / "month.json"), wrong
    )
    with pytest.raises(ValueError, match="CSV differs"):
        invalid(payload)


def test_full_result_reader_with_real_days_and_rebuilt_pending_union(tmp_path):
    """Fixture timings are artificial; science is replayed from checked real native products."""
    package = ROOT / "outputs/gcp_tuning/wildfire_gcp_tuning.zip"
    received = ROOT / "outputs/gcp_production/received/gcp_production_first_session_results.tar.gz"
    if not package.exists() or not received.exists():
        pytest.skip("Ignored verified artifacts unavailable")
    sys.path.insert(0, str(ROOT / "outputs/gcp_production/package"))
    original = importlib.import_module("run_gcp_production")
    with zipfile.ZipFile(package) as prepared:
        manifest_bytes = prepared.read("tuning_manifest.json")
        spec = json.loads(manifest_bytes)
        approved = json.loads(prepared.read("tuning_plan.json"))
        metadata = tmp_path / "metadata"
        metadata.mkdir()
        with zipfile.ZipFile(io.BytesIO(prepared.read("month_manifest.zip"))) as archive:
            archive.extractall(metadata)
    scope, worker = builder.sha(manifest_bytes), spec["files"]["run_gcp_tuning.py"]
    month = json.loads((metadata / "month.json").read_text())
    selected = [p for p in month["pairs"] if p["sample_id"] in approved["sample_ids"]]
    core, dayroot = tmp_path / "core", tmp_path / "pending_day"
    original.template(ROOT / "outputs/gcp_production/package", core)
    pending_pairs = [p for p in selected if p["start_utc"].startswith(builder.DAYS[-1])]
    original.ensure_root(dayroot, core, metadata, pending_pairs)
    (dayroot / "inputs").mkdir()
    daily_bytes = {}
    with tarfile.open(received) as source:
        for day in builder.DAYS[:2]:
            daily_bytes[day] = source.extractfile(f"months/2023-10/daily_archives/{day}.zip").read()
        for entry in source.getmembers():
            if entry.isfile() and entry.name.startswith("days/2023-10-15/inputs/"):
                (dayroot / "inputs" / Path(entry.name).name).write_bytes(
                    source.extractfile(entry).read()
                )
    compact, _ = original.science(dayroot)
    context = {
        "production_month_manifest_sha256": spec["production_month_manifest_sha256"],
        "catalogue_gap_records": [
            r for r in month["unpaired_catalogue_records"] if r["day"] == builder.DAYS[-1]
        ],
    }
    compact.reduce_day(
        builder.DAYS[-1],
        pending_pairs,
        dayroot / "inputs",
        dayroot / "daily",
        context,
        verify_geometry=True,
    )
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in compact.NAMES:
            archive.writestr(name, (dayroot / "daily" / name).read_bytes())
    daily_bytes[builder.DAYS[-1]] = stream.getvalue()

    def completion(task, payload):
        digest = builder.sha(payload)
        return {
            "protocol": "verified_job_checkpoint_v1",
            "task_id": task,
            "manifest_sha256": scope,
            "worker_sha256": worker,
            "payload_sha256": digest,
            "payload_bytes": len(payload),
            "payload_key": f"jobs/{scope}/{builder.sha(task.encode())}/{digest}.zip",
            "negative_label_permitted": False,
            "daily_observation_status": "unknown",
        }

    result = tmp_path / "fixture_results.zip"
    all_arms = arms([800, 440, 430, 800])
    summary = {
        "status": "all_profiles_completed",
        "tuning_scope_sha256": scope,
        "original_production_scope_sha256": spec["original_production_scope_sha256"],
        "arms": all_arms,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "production_months_added": 0,
        "production_progress_unchanged": True,
        "peak_sampled_resource_limit_hit": False,
        "raw_downloaded_bytes": spec["nominal_raw_download_bytes"],
    }
    with (
        zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as archive,
        zipfile.ZipFile(package) as prepared,
    ):
        for name in ("tuning_manifest.json", "tuning_plan.json", "month_manifest.zip"):
            archive.writestr(name, prepared.read(name))
        for arm in all_arms:
            label = arm["arm"]
            arm["pairs"] = [
                {
                    "sample_id": p["sample_id"],
                    "child_wall_seconds": 1,
                    "metrics": {
                        "elapsed_seconds": 1,
                        "downloaded_payload_bytes": sum(s["bytes"] for s in p["sources"]),
                    },
                    "completion": completion(label + ":" + p["sample_id"], b"fixture"),
                }
                for p in selected
            ]
            arm["days"] = [
                {"day": day, "completion": completion(label + ":day:" + day, payload)}
                for day, payload in daily_bytes.items()
            ]
            for day, payload in daily_bytes.items():
                archive.writestr(f"{label}/{day}.zip", payload)
            archive.writestr(f"{label}/arm_summary.json", json.dumps(arm))
        import csv

        text = io.StringIO()
        rows = samples()
        writer = csv.DictWriter(text, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        archive.writestr("resource_samples.csv", text.getvalue())
        archive.writestr("result_summary.json", json.dumps(summary))
    checked = reader.verify(result, package, tmp_path / "readback")
    assert checked["status"] == "independent_matched_tuning_readback_passed"
    assert checked["validated_daily_payloads"] == 12
