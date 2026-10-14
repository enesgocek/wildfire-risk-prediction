"""Reject misleading final closure, unsafe archives and contaminated invocation logs."""

import copy
import importlib
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/cloud"))
audit = importlib.import_module("verify_gcp_v7_session_logs")


def fixture():
    blocked = ["N20:2018164.0018", "SNPP:2023365.0106"]
    value = {
        "status": "processable_months_verified_source_resolution_pending",
        "continuation_phase": "remaining_months",
        "queue_manifest_sha256": audit.SCOPE,
        "controller_manifest_sha256": audit.CONTROLLER,
        "continuation_wrapper_sha256": audit.WRAPPER,
        "source_block_registry_sha256": audit.REGISTRY,
        "scan_time_adapter_sha256": audit.ADAPTER,
        "scan_time_adapter_proof_sha256": audit.PROOF,
        "scan_time_parser_protocol": "strict_utc_iso8601_ns_v1",
        "actual_vm_termination_timestamp": "2026-10-14T13:35:01.727602Z",
        "cpu_count": 32,
        "pair_workers": 24,
        "daily_workers": 4,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "full_training_complete": False,
        "deferred_days": sorted(audit.DEFERRED),
        "deferred_months": ["2018-06", "2023-12"],
        "blocked_pairs": sorted(blocked),
        "existing_months": sorted(audit.COMPLETE),
        "days_verified_this_invocation": sorted(audit.VERIFIED_DAYS),
        "pairs_processed_this_invocation": len(audit.VERIFIED_DAYS),
        "pairs_reused_this_invocation": 0,
    }
    nominal = {f"SNPP:2018{i:03d}.0000": d for i, d in enumerate(sorted(audit.VERIFIED_DAYS), 1)}
    by_day = {d: i for i, d in nominal.items()}
    # Include an older failed invocation, which must not contaminate new counters.
    lines = [
        "Reviewed V6 lineage evidence preserved; children: 18; retained ZIPs: 22",
        "CONTINUATION PHASE december_safe_days" + audit.SUFFIX,
        "PARENT_FAILURE GOOGLE_HTTP_400 CLASS_ONLY",
        "Guest poweroff requested: True",
        "Reviewed V6 lineage evidence preserved; children: 18; retained ZIPs: 22",
    ]
    for phase in audit.PHASES:
        lines.append("CONTINUATION PHASE " + phase + audit.SUFFIX)
        if phase == "december_safe_days":
            selected = audit.days("2023-12") - audit.DEFERRED
        elif phase == "june_safe_days":
            selected = audit.days("2018-06") - audit.DEFERRED
        else:
            for month in sorted(audit.COMPLETE - audit.NEW_MONTHS - {"2023-07"}):
                lines.append("Month verified/reused: " + month)
            selected = audit.VERIFIED_DAYS - audit.PARTIAL_DAYS
        for day in sorted(selected):
            lines.extend([f"{day[:7]} pair saved/verified {by_day[day]}", "DAY COMMITTED " + day])
        if phase == "remaining_months":
            lines.extend(
                "MONTH NOMINAL DIAGNOSTICS COMPLETE: " + m for m in sorted(audit.NEW_MONTHS)
            )
    lines.append("Guest poweroff requested: True")
    return value, blocked, nominal, "\n".join(lines).encode()


def snapshots(value):
    return dict.fromkeys(audit.SNAPSHOTS, json.dumps(value).encode())


def test_complete_final_and_latest_invocation_only():
    value, blocked, nominal, log = fixture()
    state = audit.state(snapshots(value), blocked)
    result = audit.log_check(log, state, nominal)
    assert result["invocations_detected"] == 2
    assert len(result["new_months"]) == 5
    assert result["new_pair_lines"] == 210


@pytest.mark.parametrize(
    "change",
    [
        "missing_month",
        "missing_day",
        "blocked_day",
        "negative",
        "full_complete",
        "wrapper",
        "new_field",
    ],
)
def test_false_final_claims_rejected(change):
    value, blocked, _, _ = fixture()
    if change == "missing_month":
        value["existing_months"].pop()
    elif change == "missing_day":
        value["days_verified_this_invocation"].pop()
    elif change == "blocked_day":
        value["days_verified_this_invocation"].append("2018-06-13")
    elif change == "negative":
        value["negative_label_permitted"] = True
    elif change == "full_complete":
        value["full_training_complete"] = True
    elif change == "wrapper":
        value["continuation_wrapper_sha256"] = "0" * 64
    else:
        value["unreviewed_field"] = "untrusted"
    with pytest.raises(ValueError):
        audit.state(snapshots(value), blocked)


def test_mismatched_final_snapshots_rejected():
    value, blocked, _, _ = fixture()
    files = snapshots(value)
    other = copy.deepcopy(value)
    other["pairs_processed_this_invocation"] += 1
    files["continuation_summary.json"] = json.dumps(other).encode()
    with pytest.raises(ValueError, match="snapshots differ"):
        audit.state(files, blocked)


@pytest.mark.parametrize("data", [b'{"status":1,"status":2}', b'{"value":NaN}'])
def test_ambiguous_json_rejected(data):
    with pytest.raises(ValueError):
        audit.strict_json(data)


@pytest.mark.parametrize("change", ["failure", "unknown_pair", "duplicate_day", "counter"])
def test_log_catalogue_inconsistencies_rejected(change):
    value, _, nominal, log = fixture()
    if change == "failure":
        log += b"\nPARENT_FAILURE GOOGLE_HTTP_400 CLASS_ONLY\nGuest poweroff requested: True"
    elif change == "unknown_pair":
        log = log.replace(b"SNPP:2018001.0000", b"SNPP:2018999.0000", 1)
    elif change == "duplicate_day":
        log = log.replace(
            b"DAY COMMITTED 2018-01-01", b"DAY COMMITTED 2018-01-01\nDAY COMMITTED 2018-01-01", 1
        )
    else:
        value["pairs_reused_this_invocation"] += 1
    with pytest.raises(ValueError):
        audit.log_check(log, value, nominal)


@pytest.mark.parametrize("kind", ["traversal", "symlink", "duplicate"])
def test_unsafe_archive_rejected(tmp_path, kind):
    path = tmp_path / "unsafe.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo("../progress.json" if kind == "traversal" else "progress.json")
        member.size = 2
        if kind == "symlink":
            member.type = tarfile.SYMTYPE
            member.linkname = "outside"
        archive.addfile(member, io.BytesIO(b"{}"))
        if kind == "duplicate":
            archive.addfile(member, io.BytesIO(b"{}"))
    with pytest.raises(ValueError):
        audit.contents(path)


def test_report_collision_rejects_before_read(tmp_path):
    report = tmp_path / "accepted.json"
    report.write_text("preserved", encoding="utf-8")
    with pytest.raises(ValueError, match="collision"):
        audit.verify(tmp_path / "absent.tar.gz", report)
    assert report.read_text() == "preserved"
