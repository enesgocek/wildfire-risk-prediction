"""Malformed archives and false completion claims cannot receive log acceptance."""

import copy
import importlib.util
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "v3_log_readback", ROOT / "scripts/cloud/verify_gcp_v3_session_logs.py"
)
sys.path.insert(0, str(ROOT / "scripts/cloud"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def final():
    return {
        "status": "paused_at_runtime_reserve",
        "queue_manifest_sha256": module.SCOPE,
        "controller_manifest_sha256": module.CONTROLLER,
        "continuation_wrapper_sha256": module.WRAPPER,
        "scan_time_adapter_sha256": module.ADAPTER,
        "scan_time_adapter_proof_sha256": module.PROOF,
        "scan_time_parser_protocol": "strict_utc_iso8601_ns_v1",
        "source_block_registry_sha256": module.REGISTRY,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "full_training_complete": False,
        "deferred_days": ["2023-12-31"],
        "deferred_months": ["2023-12"],
        "blocked_pairs": ["SNPP:2023365.0106", "SNPP:2023365.1048"],
        "cpu_count": 32,
        "pair_workers": 24,
        "daily_workers": 4,
        "existing_months": ["2023-07"],
        "days_verified_this_invocation": ["2022-02-01"],
        "pairs_processed_this_invocation": 2,
        "pairs_reused_this_invocation": 0,
    }


def snapshots(value):
    return {
        name: json.dumps(value).encode()
        for name in ("progress.json", "acceleration_run_summary.json", "continuation_summary.json")
    }


@pytest.mark.parametrize("attack", ["traversal", "symlink", "duplicate", "oversize", "missing"])
def test_tar_rejects_unsafe_members_without_extracting(tmp_path, attack):
    source = tmp_path / "received.tar.gz"
    with tarfile.open(source, "w:gz") as archive:
        for name in sorted(module.MEMBERS):
            if attack in {"missing", "oversize"} and name == "progress.json":
                continue
            info = tarfile.TarInfo(name)
            info.size = 2
            archive.addfile(info, io.BytesIO(b"{}"))
        if attack != "missing":
            info = tarfile.TarInfo(
                "../credentials.json" if attack == "traversal" else "progress.json"
            )
            if attack == "symlink":
                info.type, info.linkname = tarfile.SYMTYPE, "../private.json"
            elif attack == "oversize":
                info.size = module.LIMIT
                archive.fileobj.write(info.tobuf())
            else:
                info.size = 2
            if attack != "oversize":
                archive.addfile(info, io.BytesIO(b"{}") if info.isfile() else None)
    with pytest.raises(ValueError):
        module.contents(source)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["received.tar.gz"]


@pytest.mark.parametrize(
    "change",
    [
        {"negative_label_permitted": True},
        {"days_verified_this_invocation": ["2022-02-30"]},
        {"existing_months": ["2023-07", "2023-12"]},
        {"status": "failed_checkpoints_retained"},
    ],
)
def test_final_rejects_policy_calendar_and_failure_changes(final, change):
    final.update(change)
    with pytest.raises(ValueError):
        module.state(snapshots(final))


def test_conflicting_final_snapshots_cannot_pass(final):
    files = snapshots(final)
    other = copy.deepcopy(final)
    other["pairs_processed_this_invocation"] += 1
    files["continuation_summary.json"] = json.dumps(other).encode()
    with pytest.raises(ValueError, match="Final snapshots differ"):
        module.state(files)


@pytest.fixture
def log():
    return "\n".join(
        [
            "CONTINUATION PHASE december_safe_days deferred day 2023-12-31",
            "CONTINUATION PHASE remaining_months deferred day 2023-12-31",
            "2022-02 pair saved/verified SNPP:2022032.1000",
            "DAY COMMITTED 2022-02-01",
            "2022-02 pair saved/verified SNPP:2022033.1000",
            "Guest poweroff requested: True",
        ]
    ).encode()


NOMINAL = {"SNPP:2022032.1000": "2022-02-01", "SNPP:2022033.1000": "2022-02-02"}


def test_saved_pair_is_pending_until_daily_commit(final, log):
    report = module.log_check(log, final, NOMINAL)
    assert report["pending_days"] == {
        "2022-02-02": {"saved_pair_lines": 1, "nominal_pairs": 1, "daily_committed": False}
    }


def test_appended_old_invocation_does_not_double_count(final, log):
    report = module.log_check(log + b"\n" + log, final, NOMINAL)
    assert report["new_pair_lines"] == 2
    assert report["prior_log_lines_excluded"] == 6


@pytest.mark.parametrize("change", ["source", "duplicate", "counter", "false_commit"])
def test_catalogue_counter_and_completion_corruption_rejected(final, log, change):
    if change == "source":
        log = log.replace(b"2022032.1000", b"2022032.9999")
    elif change == "duplicate":
        log = log.replace(
            b"DAY COMMITTED", b"2022-02 pair saved/verified SNPP:2022032.1000\nDAY COMMITTED"
        )
    elif change == "counter":
        final["pairs_processed_this_invocation"] += 1
    else:
        log = log.replace(b"Guest poweroff", b"DAY COMMITTED 2022-02-02\nGuest poweroff")
    with pytest.raises(ValueError):
        module.log_check(log, final, NOMINAL)


def test_telemetry_rejects_nan_and_reports_resource_breach():
    head = (
        "seconds,arm,phase,cpu_busy_pct,disk_free_bytes,"
        "mem_available_bytes,process_tree_rss_bytes\n"
    )
    rows = "0,m,p,10,1,9000000000,100\n2,m,p,20,9000000000,9000000000,100\n"
    assert module.telemetry((head + rows).encode())["sampled_reserve_breach"] is True
    with pytest.raises(ValueError, match="Telemetry numbers"):
        module.telemetry((head + rows.replace(",10,", ",nan,")).encode())
