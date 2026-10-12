"""Resume frozen production while explicitly deferring one unresolved source day.

V6 admits eighteen hours and the exact reviewed V5 Drive failure/checkpoints.
Pair ReadTimeout retries remain; only Drive metadata GET 404 gets bounded retries.
Scan-time parsing and reviewed V2 failure preservation remain as in V3.
Frozen source files, scientific guards, checkpoint keys and readiness gate remain.
Execution adapter identity is explicit in new pair provenance and progress.
"""

import argparse
import ast
import contextlib
import getpass
import hashlib
import importlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

DIAGNOSTIC_SHA = "e1402d4cb28263fe8d05c474656ed64094cd069ca77040ed09e6d0a7296a9c63"
ADAPTER_SHA = "e729c56aced66feb6b3a461773c7d694e43d4f35b586d6060f8cabceee968a39"
PROOF_SHA = "edfba0a8a87cdbf642e9cfd31a9d7d3115ac3281003b844135e1b127369621ea"
PROOF_NAME = "gcp_scan_iso_adapter_proof_20261010T014316599475Z.json"
SNAPSHOT_SHA = "43c6a64e6547c2856f7ce39fcf478e12be3df40c8032d80cdfa3daf8e4062e0b"
SNAPSHOT_NAME = "gcp_v2_failure_snapshot_20261010T011955892163Z.json"

ORIGINAL_SCOPE = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
CONTROLLER_SCOPE = "102c9e4ab16e4450d0d94eb3511dfdbf360fd6b6292809c5457efc93d2be5837"
MONTH_SHA = "7f44606b19aab60fe75392f8df7e6951143892caf94e58eb6b23b2bfc5f19685"
GATE_SHA = "ac1f974daaf97a0a8392e9d6b225b4a7753147a9e527ec05caca4e6ea1cac3ef"
V3_FINAL_SHA = "cb455a47990b44387c9ee50100323b6d4b8e7165bb425da0059917bdc7e107d4"
V3_WRAPPER_SHA = "792d774f53c2a7249a10f4111f2f785e08d5bd2a8153e1151c73efe493b5942e"

V4_WRAPPER_SHA = "30a6bd4f65830e612dae69102abe3a0802f009c4689f626a2e64a8f165f1b7ef"
V4_FINAL_SHA = "58ff87f1e696740e602ea6e1ea340eaf64488b67510eabfcee82d0055da0d1b6"
V5_FINAL_SHA = "b9c5de20486ae2ddebc0db2696a9625a219f19d0d38656d1cf5b6fadf00c1249"
V5_PROBE_NAME = "gcp_v5_drive_probe_20261011T235837794613Z.json"
V5_PROBE_SHA = "65694b8707b8c9d39d0cfd1b7cc6719f635ee7c5c3e132b74b29a9ed56eb0d0e"
V4_DIAGNOSTICS = {
    f"months/2020-07/accelerated_run/tasks/{task}/continuation_failure.json": checksum
    for task, checksum in (
        (
            "0882e485daf250bf7b82ba9d51591a259308fda8a64f7c555e29f12bd950c11f",
            "557257ced7c9bb9b0c163b4af32758c9fc8ea8b8c3cce71cc331be644526fbb9",
        ),
        (
            "0dd1ae372918cb7c010ea7fd63d55434eecff35cb2f2fc3d1c85c2c171c8fcc8",
            "af7b2b048cf245bd3a02757d06b4c16920ca1c1f3e9833739f28206564e3300a",
        ),
        (
            "0e4af8c79452804552859bbe55cbc0d493abe7e060d58a0962a5290978abdf15",
            "bc1e1aedad26d6201aed3136f09dc83ca2fe10ae539f47d0425e8b825f9d86f5",
        ),
        (
            "14084baaea5604ebe342c75146c7c10c120f8a0bc38749893fe026b83338d3c6",
            "631f3127909e962f96fbbfd0783f2acf39c5e2bfbf420a53b566c9b99c39f169",
        ),
        (
            "1b57c0bde89e908eb7e8416019073a5b540bac4e1f0ecd5f57c99bbbb385a2f1",
            "2c3e30c92c12f8298ee9821f3ea36dd011eb3d0ca35bcd8a68b05cf79c20743a",
        ),
        (
            "30f7b4874c23f2a9686c0578bfd403c5b90cc28dbeba927008f6056cee1836fb",
            "4a37a1620b0ad92ea636cad8fe69c26fe9b403b6a871eaf9701fb95b4ce2e7db",
        ),
        (
            "53d270401b60030f781697478e10db8519ace0cf8f2f644bddb478c5377472c2",
            "9046306f49e1a286184cfb30886b6e6794e98606c50fc58272ffbfb7913297d9",
        ),
        (
            "5479e52ebf23bcb9b6556148c988b9f9ed3fe92fc38349d3948ab0dcfaf1cb4e",
            "f3f9cc9e7f3a885bfd8a524e73caddb173553d71954e6e10afbcdd94d08c022b",
        ),
        (
            "5bd857592799f0e5029868e361e348c8665fdbf0b4f5cb002deca504236b5ef7",
            "eaeabb0173c13643bfa557c7b7bd88cceb601a0d2962683f685b3ad57f6519e8",
        ),
        (
            "67874768b13fe0ea51bab6534ecea0a7976c5f12752694005c3a862c139672a1",
            "e4fa05b0d22b8e50cf9855eb3dac894851231562e93ea7bbc738054ada0a9933",
        ),
        (
            "70e7969fa602745b1df9b2a48b139bf7f2705d1c48c97f85dd1eb61c2faa8d1a",
            "3cfd7543e6057b5fdc765b93e9050b3c25b5f2b6576824ce9d70703ad0afce3a",
        ),
        (
            "7437fea3f6784118055bfa309c0ae6902b5c85b399c1e89de0d7693d3f4798c2",
            "6f638ae94e4620b2cc2108cc53538bbda4e57e53a6ccba98ef9512357bf3728b",
        ),
        (
            "763d33dfdbb6cedc41b4832ff15b5742fe59c683d880c5c6e86ff50f53ac687f",
            "bbf739e05df7e6dd66f94c8b8f9461078c11789fbf709f5cb49aa1400fcf4b1a",
        ),
        (
            "7d9932982cf19af5a2ac0af930fe8ceb3a82a68de08dd01e6d3edc7833aca57d",
            "c33715a7d8b129dd897ea119d49fd362514d1ebd8cc3c713d15625b404dff6d8",
        ),
        (
            "83047cd87711417717d3a2e37442aeb01e88cdc5bb3210d0d79e75ff0cba7703",
            "8d487f1f102105f39b3644ffa81aa2346c513c89847054b0f582f64e4f039eeb",
        ),
        (
            "87f008e23b6ebd1ab9af30918cde77b157966e53f44d4af59c0d323ec47fde0a",
            "07336e8b598bbd498541ad966848e2d88d9c72bdb8e6cf781ad24957adbe7b7f",
        ),
        (
            "8c8247acb3fcb5f7b26cae20ea3d0c2dcfb603c6758fefff59c36f9dfc660bf8",
            "de90da7aa0d7761ef2192334b5533d62431f5b1015784c3ee1f1b3a5e2b26ff7",
        ),
        (
            "a154449aa53fc9d1e8b4899e5622bc3ca04c47c645d97aa5b1c26fbca4931e6a",
            "a8b3c367aa1fe8fe6fc6702267a9d9f0f7dc3cc91cfad301cf2b3158cac8a86e",
        ),
        (
            "b6388ef6822e0497dfaf522771fdad27fc3c0d11222d3bfbebd5eb9b998f809d",
            "da1b4d782962cd31786aa823676feb4b0d7c72f67749800e3d760fe87e3c29df",
        ),
        (
            "b687a46a256ff10d88246f5e2b7f41dde1fa27ab260cc6aac0630db5d524b221",
            "3da8815cc9d8927dd112ce20227ae7a09917297abc853cc805e2ac557abf01d9",
        ),
        (
            "bf50739b7f32af0f8476677e993994c1ca85f1706bad040443eb6da7decb7c05",
            "c64ba39e0151e4a95d96c90dc82ea5eb818c39ed0f5b3a756d84e1ac4f55f853",
        ),
        (
            "c207105397ecee866aa94f89f4803f4f6ef4e0ba34ee36d134a6d0be8e749ce2",
            "7a25d3f8a17209797cc5263d2d25adb6195241308644de1980b10a2bd1114bbf",
        ),
        (
            "d6de9440fe21fc984103ed16993b1478efbf42a999b66b94755560a0c865eace",
            "f7e73bf0eea8f2952a021d2e8d2b83e1a3a5621f4b759d518948ba48c02e543a",
        ),
        (
            "da4b5bd44c60e060291f72681724826edf2b381fae82c4866f190ae231e0432d",
            "7a769943b898aff2c5b9f60d4f9240d505e82ef597729a7e1420e00fdb0bdf3a",
        ),
    )
}

BLOCKED_DAY = "2023-12-31"
EXPECTED = {
    "SNPP:2023365.0106": "VNP03IMG.A2023365.0106.002.2023365074552.nc",
    "SNPP:2023365.1048": "VNP03IMG.A2023365.1048.002.2023365174608.nc",
}


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def accepted_proof(home):
    path = home / PROOF_NAME
    require(
        path.is_file() and not path.is_symlink() and sha(path) == PROOF_SHA,
        "Pinned successful scan adapter proof",
    )
    value = json.loads(path.read_bytes())
    require(
        value["protocol"] == "gcp_scan_iso_adapter_proof_v1"
        and value["verification_script_sha256"] == ADAPTER_SHA
        and value["adapter_acceptance"] == "passed_single_retained_source"
        and value["scan_replay"]["status"] == "passed"
        and value["scan_replay"]["native_counts_match"] is True
        and value["scan_replay"]["scan_rows"] == 203
        and value["production_input_hashes_unchanged"] is True
        and value["parser_namespace_restored"] is True
        and value["runtime_parser_adapter_applied"] is True
        and value["frozen_source_files_changed"] is False
        and value["negative_label_permitted"] is False
        and value["daily_observation_status"] == "unknown"
        and value["production_resumed"] is False,
        "Successful proof policy",
    )
    return value


def checked_adapter():
    path = Path.home() / "verify_gcp_scan_iso_adapter.py"
    require(
        path.is_file() and not path.is_symlink() and sha(path) == ADAPTER_SHA,
        "Pinned verified scan parser adapter",
    )
    spec = importlib.util.spec_from_file_location("continuation_v3_scan_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def adapted_science(runner, adapter):
    original_science = runner.science
    installed = []

    def science(root):
        compact, native = original_science(root)
        timing = native.timing
        original_scans = timing.source_scans

        def scan(*args, **kwargs):
            calls = []
            timing.source_scans = original_scans
            try:
                with adapter.scan_parser(timing, calls):
                    centers, scans, provenance, begin = original_scans(*args, **kwargs)
                require(
                    len(calls) == 3
                    and {call["column"] for call in calls} == adapter.COLUMNS
                    and all(call["rows"] == len(scans) for call in calls)
                    and provenance["native_grid_counts_exact_match"] is True,
                    "Adapter preserves all native scan checks",
                )
                provenance = {
                    **provenance,
                    "scan_time_parser_adapter": {
                        "protocol": "strict_utc_iso8601_ns_v1",
                        "adapter_sha256": ADAPTER_SHA,
                        "accepted_proof_sha256": PROOF_SHA,
                        "continuation_wrapper_sha256": sha(Path(__file__)),
                        "frozen_source_files_changed": False,
                        "runtime_parser_adapter_applied": True,
                        "calls": calls,
                    },
                }
                return centers, scans, provenance, begin
            finally:
                timing.source_scans = scan

        timing.source_scans = scan
        installed.append((timing, original_scans))
        return compact, native

    runner.science = science
    try:
        yield
    finally:
        runner.science = original_science
        for timing, original_scans in installed:
            timing.source_scans = original_scans


def runtime_seconds(value, now=None):
    """Bound the real Google deadline; retain the original five-minute stop reserve."""
    now = now or datetime.now(UTC)
    finish = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(finish.tzinfo is not None and now.tzinfo is not None, "Deadline timezone")
    require(finish < datetime(2026, 10, 24, tzinfo=UTC), "Trial cutoff")
    remaining = (finish - now).total_seconds()
    require(4200 <= remaining <= 18 * 3600 + 60, "Actual deadline must be within eighteen hours")
    return remaining - 300


def reviewed_resume(state_data, state, work, snapshot):
    """Migration admits only exact accepted V3 or reviewed V4 final bytes."""
    if state.get("continuation_wrapper_sha256") == sha(Path(__file__)):
        return True
    if state.get("continuation_wrapper_sha256") == V4_WRAPPER_SHA:
        return snapshot.sha(state_data) == V4_FINAL_SHA
    if not (
        state.get("continuation_wrapper_sha256") == V3_WRAPPER_SHA
        and state.get("status") == "paused_at_runtime_reserve"
        and snapshot.sha(state_data) == V3_FINAL_SHA
    ):
        return False
    for name in ("acceleration_run_summary.json", "continuation_summary.json"):
        require(
            snapshot.sha(snapshot.read(work / name, work, 65536)) == V3_FINAL_SHA,
            "Accepted V3 final snapshots",
        )
    return True


def prepare_legacy_failures(control, apply):
    """Under the job lock, preserve only the pinned, reviewed V2 failure batch."""
    home, work = Path.home(), control.PRODUCTION
    proof = accepted_proof(home)
    adapter = checked_adapter()
    probe = adapter.checked_probe(home)
    snapshot = probe.helper(home)
    state_data = snapshot.read(work / "progress.json", work, 65536)
    state = json.loads(state_data)
    if snapshot.sha(state_data) != proof["input_hashes"]["progress.json"]:
        require(
            state["status"]
            in {
                "running",
                "paused_at_runtime_reserve",
                "processable_months_verified_source_resolution_pending",
            }
            and reviewed_resume(state_data, state, work, snapshot)
            and state["scan_time_adapter_sha256"] == ADAPTER_SHA
            and state["scan_time_adapter_proof_sha256"] == PROOF_SHA
            and state["queue_manifest_sha256"] == ORIGINAL_SCOPE
            and state["controller_manifest_sha256"] == CONTROLLER_SCOPE
            and state["negative_label_permitted"] is False
            and state["daily_observation_status"] == "unknown"
            and state["deferred_days"] == [BLOCKED_DAY]
            and state["deferred_months"] == ["2023-12"]
            and state["blocked_pairs"] == sorted(EXPECTED)
            and state["full_training_complete"] is False,
            "Unreviewed failure or changed resume identity",
        )
        return
    saved = snapshot.read(home / SNAPSHOT_NAME, home, 512000)
    require(snapshot.sha(saved) == SNAPSHOT_SHA, "Pinned reviewed V2 snapshot")
    evidence = json.loads(saved)
    require(snapshot.progress(state_data) == evidence["progress"], "Reviewed V2 state")
    for name in ("acceleration_run_summary.json", "continuation_summary.json"):
        require(
            snapshot.progress(snapshot.read(work / name, work, 65536)) == evidence["progress"],
            "Reviewed V2 final snapshots",
        )
    month = work / "months/2022-09"
    plan = month / "metadata/month.json"
    snapshot.boundary(plan, work)
    require(sha(plan) == proof["month_plan_sha256"], "Same reviewed month plan")
    focus = month / "accelerated_run/tasks" / snapshot.sha(evidence["focus_sample"].encode())
    for name, checksum in proof["input_hashes"].items():
        if name in {"month_plan", "progress.json"}:
            continue
        require(Path(name).name == name, "Proof input basename")
        path = (
            focus / "summer/raw/l2_sample_2022252.2230" / name
            if name.endswith(".nc")
            else focus / "summer/results" / name
        )
        snapshot.boundary(path, work)
        require(sha(path) == checksum, "Retained proof input unchanged")
    children = evidence["child_failures"]
    require(
        len(children) == 15
        and len({child["sample_id"] for child in children}) == 15
        and sum(child["error_type"] == "ValueError" for child in children) == 1
        and sum(child.get("exit_code") == -9 for child in children) == 14,
        "Exactly reviewed original failure batch",
    )
    destination = work / "diagnostics/reviewed_v2"
    snapshot.boundary(destination, work)
    pending, records = [], []
    for expected in children:
        task = snapshot.sha(expected["sample_id"].encode())
        source = month / "accelerated_run/tasks" / task / "continuation_failure.json"
        archive = destination / (task + ".json")
        for path in (source, archive):
            snapshot.boundary(path, work)
        path = source if source.exists() else archive
        data = snapshot.read(path, work, 65536)
        value = json.loads(data)
        require(
            value["sample_id"] == expected["sample_id"]
            and value["child_kind"] == "pair"
            and value["guard"] == "CLASS_ONLY"
            and {"sample_id": value["sample_id"], **snapshot.failure(value, {"CLASS_ONLY"})}
            == expected,
            "Only reviewed V2 child diagnostic",
        )
        if source.exists():
            require(not archive.exists(), "Reviewed diagnostic duplicate")
            pending.append((source, archive, snapshot.sha(data)))
        records.append({"sample_id": expected["sample_id"], "sha256": snapshot.sha(data)})
    receipt = {
        "protocol": "v3_reviewed_v2_diagnostic_archive",
        "snapshot_sha256": SNAPSHOT_SHA,
        "proof_sha256": PROOF_SHA,
        "diagnostics": records,
    }
    if apply:
        destination.mkdir(parents=True, exist_ok=True)
        receipt_path = destination / "receipt.json"
        if receipt_path.exists():
            require(
                json.loads(snapshot.read(receipt_path, work, 65536)) == receipt,
                "Same reviewed archive receipt",
            )
        else:
            control.atomic(receipt_path, receipt)
        for source, archive, checksum in pending:
            require(
                sha(source) == checksum and not archive.exists(),
                "Diagnostic unchanged before archive",
            )
            source.rename(archive)
        require(
            all(
                sha(destination / (snapshot.sha(row["sample_id"].encode()) + ".json"))
                == row["sha256"]
                for row in records
            ),
            "Archived diagnostic bytes unchanged",
        )
        print("Reviewed V2 diagnostics preserved:", len(records), flush=True)


def prepare_v4_failures(control, apply):
    """Rearm only the locally reviewed V4 batch; preserve its original bytes."""
    work = control.PRODUCTION
    state_path = work / "progress.json"
    boundary(state_path, work)
    require(not state_path.is_symlink() and state_path.stat().st_size < 65536, "State boundary")
    data = state_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != V4_FINAL_SHA:
        return prepare_legacy_failures(control, apply)
    # Exact final bytes cover all source pins, policies and the failed July state.
    require(
        json.loads(data)["continuation_wrapper_sha256"] == V4_WRAPPER_SHA, "Reviewed V4 identity"
    )
    for name in ("acceleration_run_summary.json", "continuation_summary.json"):
        path = work / name
        boundary(path, work)
        require(
            path.stat().st_size < 65536 and sha(path) == V4_FINAL_SHA, "Reviewed V4 final snapshots"
        )
    destination = work / "diagnostics/reviewed_v4_timeout"
    pending = []
    for name, checksum in V4_DIAGNOSTICS.items():
        source = work / name
        archive = destination / (source.parent.name + ".json")
        boundary(source, work)
        boundary(archive, work)
        path = source if source.exists() else archive
        require(
            path.is_file() and path.stat().st_size < 65536 and sha(path) == checksum,
            "Reviewed V4 diagnostic bytes",
        )
        if source.exists():
            require(not archive.exists(), "Reviewed V4 duplicate")
            pending.append((source, archive, checksum))
    actual = {
        p.relative_to(work).as_posix()
        for p in (work / "months/2020-07").rglob("continuation_failure.json")
    }
    require(
        actual == {p.relative_to(work).as_posix() for p, _, _ in pending},
        "No unreviewed July failures",
    )
    if apply:
        destination.mkdir(parents=True, exist_ok=True)
        receipt = {
            "protocol": "v5_reviewed_v4_timeout_archive",
            "final_sha256": V4_FINAL_SHA,
            "diagnostics": V4_DIAGNOSTICS,
        }
        receipt_path = destination / "receipt.json"
        boundary(receipt_path, work)
        if receipt_path.exists():
            require(json.loads(receipt_path.read_bytes()) == receipt, "Same V4 receipt")
        else:
            control.atomic(receipt_path, receipt)
        for source, archive, checksum in pending:
            require(sha(source) == checksum and not archive.exists(), "Unchanged V4 diagnostic")
            source.rename(archive)
            require(sha(archive) == checksum, "Preserved V4 bytes")
        print("Reviewed V4 timeout diagnostics preserved:", len(V4_DIAGNOSTICS), flush=True)


def prepare_reviewed_failures(control, apply):
    """Rearm only exact reviewed V5 bytes, with the unchanged successful probe evidence."""
    work, home = control.PRODUCTION, Path.home()
    state = work / "progress.json"
    boundary(state, work)
    if sha(state) != V5_FINAL_SHA:
        return prepare_v4_failures(control, apply)
    for name in ("acceleration_run_summary.json", "continuation_summary.json"):
        path = work / name
        boundary(path, work)
        require(path.stat().st_size < 65536 and sha(path) == V5_FINAL_SHA, "Reviewed V5 snapshots")
    probe_path = home / V5_PROBE_NAME
    boundary(probe_path, home)
    require(
        probe_path.stat().st_size < 65536 and sha(probe_path) == V5_PROBE_SHA,
        "Reviewed Drive probe",
    )
    probe = json.loads(probe_path.read_bytes())
    require(
        probe["status"] == "readonly_checks_passed"
        and probe["protected_files_unchanged"] is True
        and probe["reviewed_final_sha256"] == V5_FINAL_SHA
        and probe["child_diagnostics"] == []
        and probe["production_writes"] == probe["drive_object_writes"] == 0,
        "Successful reviewed Drive probe",
    )
    parent = work / probe["parent_diagnostic"]["path"]
    boundary(parent, work)
    require(
        parent.stat().st_size < 65536 and sha(parent) == probe["parent_diagnostic"]["sha256"],
        "Reviewed parent bytes",
    )
    rows = probe["pairs"]
    require(len(rows) == probe["retained_candidates"] == 31, "Reviewed retained population")
    for row in rows:
        path = (
            work
            / "months/2020-07/accelerated_run/tasks"
            / hashlib.sha256(row["sample_id"].encode()).hexdigest()
            / "pair.zip"
        )
        boundary(path, work)
        require(
            path.stat().st_size == row["local_bytes"] and sha(path) == row["local_sha256"],
            "Retained V5 payload unchanged",
        )
    require(
        not list((work / "months/2020-07").rglob("continuation_failure.json")),
        "No unreviewed V5 child failures",
    )
    # There are no child failures to archive. Preserve evidence before live counters reset.
    if apply:
        destination = work / "diagnostics/reviewed_v5_drive"
        boundary(destination, work)
        destination.mkdir(parents=True, exist_ok=True)
        sources = [
            state,
            work / "acceleration_run_summary.json",
            work / "continuation_summary.json",
            parent,
            probe_path,
        ]
        for source in sources:
            archive = destination / source.name
            boundary(archive, work)
            data = source.read_bytes()
            if archive.exists():
                require(archive.read_bytes() == data, "Same V5 evidence archive")
            else:
                with archive.open("xb") as stream:
                    stream.write(data)
            require(sha(archive) == hashlib.sha256(data).hexdigest(), "V5 evidence preserved")
        print("Reviewed V5 Drive evidence preserved; retained pairs: 31", flush=True)


def metadata_retry_requests(api, deadline, sampler):
    """Retry only the exact same Drive metadata GET on 404; no upload/creation retry."""
    original = api.request

    def request(path, method="GET", data=None, content_type=None, upload=False):
        eligible = (
            method == "GET"
            and data is None
            and not upload
            and re.fullmatch(r"/files/[A-Za-z0-9_-]{5,200}\?fields=[A-Za-z,]+", path)
        )
        retries = 0
        while True:
            try:
                return original(
                    path, method=method, data=data, content_type=content_type, upload=upload
                )
            except RuntimeError as error:
                if not (
                    eligible
                    and error.args == ("Drive HTTP 404; no secrets logged",)
                    and retries < 3
                ):
                    raise
                delay = (2, 5, 10)[retries]
                require(
                    not sampler.failed and time.monotonic() + 1200 + 300 + delay < deadline,
                    "Drive retry resource/deadline guard",
                )
                retries += 1
                print("DRIVE_METADATA_RETRY", retries, "HTTP_404", flush=True)
                end = time.monotonic() + delay
                while time.monotonic() < end:
                    require(
                        not sampler.failed and time.monotonic() + 1200 + 300 < deadline,
                        "Drive retry resource/deadline guard",
                    )
                    time.sleep(max(0, min(1, end - time.monotonic())))
                require(
                    not sampler.failed and time.monotonic() + 1200 + 300 < deadline,
                    "Drive retry resource/deadline guard",
                )

    api.request = request


def boundary(path, root):
    require(not root.is_symlink(), "Diagnostic root symlink")
    require(path.resolve().is_relative_to(root.resolve()), "Diagnostic path boundary")
    current = path
    while current != root:
        require(not current.is_symlink(), "Diagnostic ancestor symlink")
        current = current.parent


def retryable_failure(root, kind, identity):
    """Only an exact pair ReadTimeout schema is transient; no message text is trusted."""
    path = root / "continuation_failure.json"
    boundary(path, root)
    if not path.is_file() or path.stat().st_size >= 65536 or kind != "pair":
        return False
    value = json.loads(path.read_bytes())
    return value == {
        "sample_id": identity,
        "child_kind": "pair",
        "error_type": "ReadTimeout",
        "guard": "CLASS_ONLY",
        "safe_error": "UNCLASSIFIED_ERROR",
    }


def preserve_retry(root, identity, attempt, work):
    source = root / "continuation_failure.json"
    boundary(source, work)
    # Successful tasks are cleaned after verified publication. Keep retry
    # evidence outside their scratch directories so that cleanup cannot erase it.
    destination = (
        work / "diagnostics/transient_read_timeout" / hashlib.sha256(identity.encode()).hexdigest()
    )
    boundary(destination, work)
    destination.mkdir(parents=True, exist_ok=True)
    require(len(list(destination.iterdir())) < 128, "Retry history bound")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    archive = destination / f"attempt_{attempt}_{stamp}.json"
    require(not archive.exists(), "Retry archive collision")
    checksum = sha(source)
    source.rename(archive)
    require(sha(archive) == checksum, "Retry diagnostic preserved")
    print("PAIR READ TIMEOUT RETRY", identity, attempt, "of 2", flush=True)


def diagnostic_launcher(control, reference, args):
    launch_once = diagnostic_launcher_once(control, reference, args)

    def launch(runner, kind, root, plan, identity, auth, deadline, sampler):
        started = time.monotonic()
        for attempt in range(3):
            try:
                launch_once(runner, kind, root, plan, identity, auth, deadline, sampler)
                return time.monotonic() - started
            except RuntimeError:
                delay = (30, 60)[min(attempt, 1)]
                if (
                    attempt == 2
                    or sampler.failed
                    or not retryable_failure(root, kind, identity)
                    or time.monotonic() + delay + reference.CHILD_LIMIT + 1200 >= deadline
                ):
                    raise
                # Admission includes a full child budget plus the unchanged publish reserve.
                until = time.monotonic() + delay
                while time.monotonic() < until:
                    require(
                        not sampler.failed
                        and time.monotonic() + reference.CHILD_LIMIT + 1200 < deadline,
                        "Retry resource/deadline guard",
                    )
                    time.sleep(max(0, min(0.25, until - time.monotonic())))
                preserve_retry(root, identity, attempt + 1, control.PRODUCTION)
        raise AssertionError("Retry loop bound")

    return launch


def registry(path, checksum):
    require(
        not path.is_symlink() and 0 < path.stat().st_size < 65536 and sha(path) == checksum,
        "Pinned source-block registry",
    )
    value = json.loads(path.read_bytes())
    require(
        value["protocol"] == "gcp_unresolved_source_registry_v1"
        and value["original_scope_sha256"] == ORIGINAL_SCOPE
        and value["controller_scope_sha256"] == CONTROLLER_SCOPE
        and value["month_plan_sha256"] == MONTH_SHA
        and value["deferred_days"] == [BLOCKED_DAY]
        and value["negative_label_permitted"] is False
        and value["daily_observation_status"] == "unknown"
        and value["full_training_complete"] is False,
        "Source-block scope and policy",
    )
    require(
        {r["sample_id"]: r["required_geolocation"] for r in value["blocked_pairs"]} == EXPECTED
        and len(value["blocked_pairs"]) == 2,
        "Exactly two proven source blocks",
    )
    return value


class RunnerPhase:
    """Validate the full sealed catalogue first; only change month scheduling."""

    def __init__(self, runner, phase):
        self.runner, self.phase = runner, phase

    def __getattr__(self, name):
        return getattr(self.runner, name)

    def read_scope(self, package):
        spec, scope, catalogue, sources = self.runner.read_scope(package)
        require(scope == ORIGINAL_SCOPE, "Unchanged scientific resume scope")
        months = spec["months"]
        require(
            len(months) == 71
            and months[:5] == ["2023-08", "2023-09", "2023-10", "2023-11", "2023-12"],
            "Sealed month order",
        )
        chosen = months[:5] if self.phase == "december_safe_days" else months[5:]
        return {**spec, "months": chosen}, scope, catalogue, sources


def filtered_pipeline(original, *args, **kwargs):
    """The deferred day never reaches reduction or a daily/monthly completion."""
    plan, days = args[6], args[7]
    if plan["month"] != "2023-12":
        return original(*args, **kwargs)
    require(
        plan["negative_label_permitted"] is False
        and sha(args[5]) == MONTH_SHA
        and BLOCKED_DAY in days,
        "Exact December day filter",
    )
    changed = list(args)
    changed[7] = [d for d in days if d != BLOCKED_DAY]
    result = original(*changed, **kwargs)
    require(BLOCKED_DAY not in result["day_records"], "Deferred day must remain uncommitted")
    if result["status"] == "complete":
        result["status"] = "deferred_source_lineage"
    return result


def merged(states, current, phase, registry_sha, wrapper_sha):
    rows = [*states, current]
    value = dict(current)
    value["existing_months"] = sorted({m for s in rows for m in s["existing_months"]})
    value["days_verified_this_invocation"] = sorted(
        {d for s in rows for d in s["days_verified_this_invocation"]}
    )
    for key in ("pairs_processed_this_invocation", "pairs_reused_this_invocation"):
        value[key] = sum(s[key] for s in rows)
    require(
        BLOCKED_DAY not in value["days_verified_this_invocation"]
        and "2023-12" not in value["existing_months"],
        "Unresolved December cannot be complete",
    )
    if len(value["existing_months"]) == 71 and value["status"] != "failed_checkpoints_retained":
        value["status"] = "processable_months_verified_source_resolution_pending"
    value.update(
        continuation_phase=phase,
        deferred_days=[BLOCKED_DAY],
        deferred_months=["2023-12"],
        blocked_pairs=sorted(EXPECTED),
        source_block_registry_sha256=registry_sha,
        continuation_wrapper_sha256=wrapper_sha,
        full_training_complete=False,
        scan_time_adapter_sha256=ADAPTER_SHA,
        scan_time_adapter_proof_sha256=PROOF_SHA,
        scan_time_parser_protocol="strict_utc_iso8601_ns_v1",
    )
    return value


def run_phases(
    control, original_run, args, runner, spec, scope, auth, reference, deadline, sampler, work
):
    states = []
    control.atomic(work / "source_blocks.json", registry(args.registry, args.registry_sha))
    for phase in ("december_safe_days", "remaining_months"):
        if sampler.failed or time.monotonic() + 1200 >= deadline:
            break
        print("CONTINUATION PHASE", phase, "deferred day", BLOCKED_DAY, flush=True)
        # This is a scheduling wrapper, not a change to native science or stored code.
        original_pipeline, original_atomic = control.pipeline, control.atomic
        control.pipeline = lambda *a, _pipeline=original_pipeline, **k: filtered_pipeline(
            _pipeline, *a, **k
        )
        latest = {}

        def live_atomic(path, value, _phase=phase, _latest=latest, _atomic=original_atomic):
            if path in {work / "progress.json", work / "acceleration_run_summary.json"}:
                _latest["state"] = json.loads(json.dumps(value))
                value = merged(states, value, _phase, args.registry_sha, sha(Path(__file__)))
            _atomic(path, value)

        control.atomic = live_atomic
        current = None
        try:
            original_run(
                args,
                RunnerPhase(runner, phase),
                spec,
                scope,
                auth,
                reference,
                deadline,
                sampler,
                work,
            )
        except Exception as error:
            parent_failure(control, error, phase, sampler, work)
            raise
        finally:
            control.pipeline, control.atomic = original_pipeline, original_atomic
            if "state" in latest:
                current = latest["state"]
                combined = merged(states, current, phase, args.registry_sha, sha(Path(__file__)))
                control.atomic(work / "progress.json", combined)
                control.atomic(work / "acceleration_run_summary.json", combined)
                control.atomic(work / "continuation_summary.json", combined)
        states.append(current)
        if phase == "december_safe_days":
            required = {f"2023-12-{d:02d}" for d in range(1, 31)}
            if not required <= set(current["days_verified_this_invocation"]):
                break  # Runtime reserve reached; next invocation resumes the same work.


def safe_failure(error, root, original):
    labels = set()
    for directory, manifest, field in (
        (original, original / "production_manifest.json", "files"),
        (root, root / "summer/manifest.json", "bundle_files"),
    ):
        for name in json.loads(manifest.read_bytes())[field]:
            if not name.endswith(".py"):
                continue
            path = directory / name
            require(
                not path.is_symlink() and path.resolve().is_relative_to(directory.resolve()),
                "Guard source boundary",
            )
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call) and len(node.args) > 1:
                    fn, value = node.func, node.args[1]
                    if (
                        (
                            (isinstance(fn, ast.Name) and fn.id == "require")
                            or (isinstance(fn, ast.Attribute) and fn.attr == "require")
                        )
                        and isinstance(value, ast.Constant)
                        and isinstance(value.value, str)
                    ):
                        labels.add(value.value)
    value = error.args[0] if len(error.args) == 1 else None
    return {
        "error_type": type(error).__name__,
        "guard": value if isinstance(value, str) and value in labels else "CLASS_ONLY",
    }


def child(args, control, runner):
    require(
        args.root.resolve().is_relative_to(control.PRODUCTION.resolve())
        and not args.root.is_symlink(),
        "Continuation child root",
    )
    failure = args.root / "continuation_failure.json"
    try:
        if args.child == "pair":
            require(args.sample not in EXPECTED, "Blocked pair cannot be launched")
            adapter = checked_adapter()
            with adapted_science(runner, adapter):
                runner.child_pair(args)
        else:
            require(args.day != BLOCKED_DAY, "Blocked day cannot be reduced")
            runner.child_day(args)
    except Exception as error:
        value = safe_failure(error, args.root, control.ORIGINAL)
        value["safe_error"] = diagnostic_helper().safe_error(error)
        value.update(
            sample_id=args.sample if args.child == "pair" else args.day, child_kind=args.child
        )
        if args.child == "pair" and value["guard"] == "Not the actual geolocation input":
            try:
                plan = json.loads(args.plan.read_bytes())
                pair = next(p for p in plan["pairs"] if p["sample_id"] == args.sample)
                _, native = runner.science(args.root)
                fire = next(s for s in pair["sources"] if s["role"] == "fire")
                raw = args.root / "summer/raw" / pair["stem"] / fire["filename"]
                with contextlib.ExitStack() as stack:
                    tags = native.audit.layer(stack, raw, "fire_mask").tags()
                pattern = r"(?:VNP03IMG|VJ103IMG)\.A\d{7}\.\d{4}\.\d{3}\.\d{13}\.nc"
                value["declared_geolocation_filenames"] = sorted(
                    {
                        name
                        for key in ("VNP03IMG", "VJ103IMG", "InputPointer")
                        for name in re.findall(pattern, tags.get(key, "")[:8192])
                    }
                )
                value["selected_geolocation_filename"] = next(
                    s["filename"] for s in pair["sources"] if s["role"] == "geolocation"
                )
            except Exception:
                value["header_detail"] = "UNAVAILABLE"
        control.atomic(failure, value)
        raise


def diagnostic_launcher_once(control, reference, args):
    def launch(runner, kind, root, plan, identity, auth, deadline, sampler):
        failure = root / "continuation_failure.json"
        require(not failure.exists(), "Retained child failure requires review")
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            kind,
            "--root",
            str(root),
            "--plan",
            str(plan),
            "--sample" if kind == "pair" else "--day",
            identity,
            "--registry",
            str(args.registry.resolve()),
            "--registry-sha",
            args.registry_sha,
        ]
        started = time.monotonic()
        env = runner.environment(auth)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )
        with reference.ACTIVE_LOCK:
            reference.ACTIVE[process.pid] = process
        try:
            while process.poll() is None:
                if sampler.failed or time.monotonic() >= min(
                    deadline, started + reference.CHILD_LIMIT
                ):
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=30)
                    raise TimeoutError("Continuation child resource/deadline guard")
                time.sleep(0.25)
            if process.returncode != 0:
                if not failure.exists():
                    control.atomic(
                        failure,
                        {
                            "sample_id": identity,
                            "child_kind": kind,
                            "error_type": "RuntimeError",
                            "guard": "CLASS_ONLY",
                            "exit_code": process.returncode,
                            "termination_kind": "nonzero_exit_without_python_diagnostic",
                        },
                    )
                    print("CHILD_EXIT", identity, process.returncode, flush=True)
                if (
                    failure.is_file()
                    and not failure.is_symlink()
                    and failure.stat().st_size < 65536
                ):
                    value = json.loads(failure.read_bytes())
                    require(
                        value.get("sample_id") == identity and value.get("child_kind") == kind,
                        "Diagnostic child identity",
                    )
                    # File is written solely by the pinned wrapper; no HTTP/stdout text.
                    print("CHILD FAILED", identity, value["error_type"], value["guard"], flush=True)
                raise RuntimeError("Frozen scientific child failed; diagnostic retained")
            return time.monotonic() - started
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            raise
        finally:
            with reference.ACTIVE_LOCK:
                reference.ACTIVE.pop(process.pid, None)

    return launch


def diagnostic_helper():
    path = Path.home() / "diagnose_gcp_production_manifest.py"
    require(
        not path.is_symlink() and path.is_file() and sha(path) == DIAGNOSTIC_SHA,
        "Pinned HTTP diagnostic helper",
    )
    spec = importlib.util.spec_from_file_location("continuation_http_diagnostic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parent_failure(control, error, phase, sampler, work):
    """Keep only code-defined guards or sanitized HTTP classes, never traceback or auth."""
    try:
        helper = diagnostic_helper()
        labels = set()
        for package, manifest in (
            (control.ORIGINAL, "production_manifest.json"),
            (Path(control.__file__).parent, "acceleration_manifest.json"),
        ):
            spec = json.loads((package / manifest).read_bytes())
            for name, digest in spec["files"].items():
                if not name.endswith(".py"):
                    continue
                path = package / name
                require(
                    not path.is_symlink() and Path(name).name == name and sha(path) == digest,
                    "Parent guard source",
                )
                for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                    if isinstance(node, ast.Call) and len(node.args) > 1:
                        function, label = node.func, node.args[1]
                        if (isinstance(function, ast.Name) and function.id == "require") or (
                            isinstance(function, ast.Attribute) and function.attr == "require"
                        ):
                            if isinstance(label, ast.Constant) and isinstance(label.value, str):
                                labels.add(label.value)
        text = error.args[0] if len(error.args) == 1 else None
        value = {
            "protocol": "continuation_parent_failure_v3",
            "recorded_at_utc": datetime.now(UTC).isoformat(),
            "continuation_phase": phase,
            "error": helper.safe_error(error),
            "guard": text if isinstance(text, str) and text in labels else "CLASS_ONLY",
        }
        month = getattr(sampler, "arm", "")
        step = getattr(sampler, "phase", "")
        value["last_recorded_month"] = (
            month if re.fullmatch(r"20(?:18|19|2[0-3])-\d{2}", month) else "UNKNOWN"
        )
        value["last_recorded_stage"] = (
            step
            if step in {"metadata", "prepare_day", "pair_publication", "daily_publication"}
            else "UNKNOWN"
        )
        name = "parent_failure_v3_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
        control.atomic(work / "diagnostics" / name, value)
        print("PARENT_FAILURE", value["error"], value["guard"], flush=True)
    except Exception:
        print("PARENT_FAILURE diagnostic_unavailable; no external text logged", flush=True)


def instrument_backend(control, helper, deadline, sampler):
    original = control.backend

    def backend(*args, **kwargs):
        # Wrap the opener before the existing backend performs token/quota checks.
        from accelerated_checkpoint_store import IndexedDriveStore

        method = IndexedDriveStore.from_file.__func__

        def from_file(cls, path):
            store = method(cls, path)
            store.api.opener = helper.diagnostic_opener(store.api.opener)
            metadata_retry_requests(store.api, deadline, sampler)
            return store

        previous = IndexedDriveStore.__dict__.get("from_file")
        IndexedDriveStore.from_file = classmethod(from_file)
        try:
            return original(*args, **kwargs)
        finally:
            if previous is None:
                del IndexedDriveStore.from_file
            else:
                IndexedDriveStore.from_file = previous

    control.backend = backend


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--registry-sha", required=True)
    parser.add_argument("--termination")
    parser.add_argument(
        "--connection", type=Path, default=Path.home() / ".config/wildfire/drive_connection.json"
    )
    parser.add_argument("--gate", type=Path, default=Path.home() / "production_readiness.json")
    parser.add_argument("--gate-sha", default=GATE_SHA)
    parser.add_argument("--cpus", type=int, default=32, choices=[32])
    parser.add_argument("--poweroff", action="store_true")
    parser.add_argument("--supervise", action="store_true")
    parser.add_argument("--auth-fd", type=int)
    parser.add_argument("--child", choices=["pair", "day"])
    parser.add_argument("--root", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--sample")
    parser.add_argument("--day")
    args = parser.parse_args()
    registry(args.registry, args.registry_sha)
    accepted_proof(Path.home())
    checked_adapter()
    package = Path.home() / "wildfire-gcp-acceleration-package"
    require(
        sha(package / "acceleration_manifest.json") == CONTROLLER_SCOPE, "Pinned base controller"
    )
    sys.path.insert(0, str(package))
    control = importlib.import_module("run_gcp_acceleration")
    require(
        Path(control.__file__).resolve() == (package / "run_gcp_acceleration.py").resolve(),
        "Base controller import identity",
    )
    spec, scope, runner = control.checked()
    http = diagnostic_helper()
    if args.child:
        child(args, control, runner)
        return
    require(
        sys.platform == "linux"
        and sys.version_info[:2] == (3, 12)
        and sys.prefix != sys.base_prefix,
        "Existing Linux Python venv",
    )
    runner.vm_identity()
    require(os.cpu_count() == args.cpus, "Actual CPU count")
    require(
        control.memory_values(Path("/proc/meminfo").read_text())[0] >= 64 * 2**30,
        "Actual memory reserve",
    )
    seconds = runtime_seconds(args.termination)
    control.read_gate(args, scope)
    require(args.poweroff, "Automatic shutdown required")
    if not args.supervise:
        with control.production_lock():
            prepare_reviewed_failures(control, apply=False)
        require(
            subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60,
            ).returncode
            == 0,
            "Dependencies",
        )
        require(
            args.poweroff
            and subprocess.run(
                ["sudo", "-n", "true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).returncode
            == 0,
            "Automatic shutdown required",
        )
        auth = {
            "username": getpass.getpass("Earthdata kullanÄ±cÄ± adÄ± (gizli): "),
            "password": getpass.getpass("Earthdata parola (gizli): "),
        }
        require(
            all(isinstance(v, str) and 0 < len(v) <= 2048 for v in auth.values()),
            "Credentials required",
        )
        data = json.dumps(auth).encode()
        require(len(data) <= 8192, "Credential pipe bound")
        read_fd, write_fd = os.pipe()
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--supervise",
            "--registry",
            str(args.registry.resolve()),
            "--registry-sha",
            args.registry_sha,
            "--termination",
            args.termination,
            "--connection",
            str(args.connection.resolve()),
            "--gate",
            str(args.gate.resolve()),
            "--gate-sha",
            args.gate_sha,
            "--auth-fd",
            str(read_fd),
            "--poweroff",
        ]
        with (Path.home() / "gcp_source_aware_launcher_v6.log").open("ab") as log:
            process = subprocess.Popen(
                command,
                pass_fds=(read_fd,),
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                env=runner.environment(),
            )
        os.close(read_fd)
        os.write(write_fd, data)
        os.close(write_fd)
        print("Detached continuation requested; PID:", process.pid)
        print("Check:", Path.home() / "gcp_source_aware_launcher_v6.log")
        return
    auth = runner.read_auth(args.auth_fd)
    reference = control.reference_driver()
    reference.run_child = diagnostic_launcher(control, reference, args)
    production = importlib.import_module("accelerated_production")
    original_run = production.run

    def production_run(*values):
        prepare_reviewed_failures(control, apply=True)
        instrument_backend(control, http, values[-3], values[-2])
        return run_phases(control, original_run, *values)

    production.run = production_run
    args.mode = "production"
    control.supervise(args, runner, spec, scope, auth, reference, seconds, control.PRODUCTION)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    os.umask(0o077)
    try:
        main()
    except Exception as error:
        print(
            "Continuation stopped:",
            type(error).__name__,
            "; safe child diagnostics retained",
            flush=True,
        )
        raise SystemExit(1) from None
