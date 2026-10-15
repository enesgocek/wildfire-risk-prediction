"""Offline recovery of a reviewed interrupted transfer; preserve partial bytes and receipts."""

import importlib.util
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
FAILED = ROOT / "outputs/reports/dataset/observation_pilot_run_v1/20261015T121531Z_911c43a7"
FAILED_SHA = "598b9fd63092d312e1c71c3d9aa22024a56288301204c90784f3e1422e270dc7"
PLAN = (
    ROOT
    / "outputs/reports/dataset/observation_pilot_queue_v2/20261015T114055Z_a141e892/queue_plan.json"
)


def quarantine_partial(partial, destination, source, root):
    require(partial.name == source["filename"] + ".part", "Exact pending source filename")
    require(partial.is_file() and not partial.is_symlink(), "Regular retained partial")
    require(
        partial.resolve().is_relative_to(root.resolve())
        and destination.parent.resolve().is_relative_to(root.resolve()),
        "Contained recovery paths",
    )
    require(
        not destination.exists() and not partial.with_suffix("").exists(),
        "No existing recovery or full source overwrite",
    )
    size, sha = partial.stat().st_size, digest(partial)
    require(0 < size < source["bytes"], "Strictly incomplete source requires full retry")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial.rename(destination)
    require(
        destination.stat().st_size == size and digest(destination) == sha,
        "Preserved partial byte identity",
    )
    require(not partial.exists(), "Active partial path released")
    return {
        "retained_bytes": size,
        "retained_sha256": sha,
        "retained_path": destination.relative_to(root).as_posix(),
        "partial_accepted_as_native_source": False,
        "raw_files_deleted": 0,
    }


def run():
    spec = importlib.util.spec_from_file_location(
        "reviewed_queue", ROOT / "scripts/firms/run_observation_pilot_queue.py"
    )
    queue = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(queue)
    plan = queue.load_queue(PLAN)
    require(digest(FAILED / "readback.json") == FAILED_SHA, "Pinned failed attempt")
    result = queue.verified_attempt(FAILED, digest(PLAN))
    failure = result["failure"]
    require(
        result["status"] == "failed_checkpoints_retained"
        and failure["error_type"] == "ConnectionError"
        and failure["transfer_diagnostics"]["final_http_status"] == 200,
        "Reviewed interrupted response, not identity or checksum failure",
    )
    require(
        result["completed_pair_count"] == 86 and result["missing_pair_count"] == 12,
        "Reviewed attempt scope",
    )
    job = queue.JOBS / digest(PLAN)[:16]
    raw = ROOT / "data/raw/observation_pilot_v1" / digest(PLAN)[:16]
    out = (
        ROOT
        / "outputs/reports/dataset/observation_pilot_recovery_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    lock = job / "writer.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    try:
        sources, accepted_bytes = [], 0
        pairs = {p["sample_id"]: p for p in plan["pairs"]}
        for sample in result["pair_receipts"]:
            pair = pairs[sample]
            cache = raw / queue.pair_name(pair)
            for source in pair["sources"]:
                record = check_file(cache / source["filename"], source)
                sources.append({"sample_id": sample, "role": source["role"], **record})
                accepted_bytes += record["bytes"]
        pair = pairs[failure["sample_id"]]
        cache = raw / queue.pair_name(pair)
        partials = list(raw.rglob("*.part"))
        require(len(partials) == 1, "Exactly one reviewed incomplete transfer")
        source = next(s for s in pair["sources"] if partials[0].name == s["filename"] + ".part")
        require(partials[0].parent.resolve() == cache.resolve(), "Failed pair partial location")
        for other in pair["sources"]:
            if other["role"] != source["role"]:
                check_file(cache / other["filename"], other)
        queue.write_json(
            out / "pre_move_review.json",
            {
                "status": "completed_sources_reverified_partial_not_accepted",
                "failed_attempt_sha256": FAILED_SHA,
                "queue_sha256": digest(PLAN),
                "completed_pair_count": 86,
                "reverified_source_count": len(sources),
                "accepted_raw_bytes": accepted_bytes,
                "sources": sources,
                "pending_source_id": source["source_id"],
                "partial_bytes": partials[0].stat().st_size,
                "partial_sha256": digest(partials[0]),
                "negative_label_permitted": False,
            },
        )
        preserved = quarantine_partial(
            partials[0], out / "retained_partial" / partials[0].name, source, ROOT
        )
        # All scientific code/plan and successful receipts still match their original hashes.
        queue.load_queue(PLAN)
        queue.verified_attempt(FAILED, digest(PLAN))
        report = {
            "status": "reviewed_interruption_preserved_ready_for_same_queue_retry",
            "queue_sha256": digest(PLAN),
            "failed_attempt_sha256": FAILED_SHA,
            "completed_pairs_reverified": 86,
            "completed_sources_reverified": len(sources),
            "accepted_raw_bytes_reverified": accepted_bytes,
            "remaining_pair_count": 12,
            "pending_source_id": source["source_id"],
            "retry_file_bytes": source["bytes"],
            **preserved,
            "artifact_sha256": {"pre_move_review.json": digest(out / "pre_move_review.json")},
            "script_sha256": digest(Path(__file__)),
            "network_bytes": 0,
            "labels_created": False,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "cloud_jobs_started": 0,
        }
        queue.write_json(out / "readback.json", report)
        queue.write_json(
            out / "completion_readback.json",
            {"status": "passed", "report_sha256": digest(out / "readback.json")},
        )
    finally:
        lock.unlink()
    print(out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    run()
