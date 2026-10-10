"""Proof-gated ISO adapter around the existing bounded vegetation supervisor."""

import argparse
import contextlib
import json
import re
from pathlib import Path

import vegetation_iso_adapter as adapter

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / "outputs/reports/landscape/iso_adapter_v1/proof_2019_03_22.json"


def checked_proof(path, expected):
    adapter.require(re.fullmatch(r"[a-f0-9]{64}", expected), "Proof digest")
    adapter.require(not path.is_symlink() and adapter.sha(path) == expected, "Pinned ISO proof")
    value = json.loads(path.read_text())
    adapter.require(
        value["protocol"] == adapter.PROTOCOL
        and value["adapter_sha256"] == adapter.identity()["adapter_sha256"]
        and value["base_source_sha256"] == adapter.checked_base()
        and value["original_failure_reproduced"] is True
        and value["strict_iso_equals_scalar"] is True
        and value["parser_namespace_restored"] is True
        and value["network_requests"] == value["production_writes"] == 0
        and value["snapshot_readback"]["status"] == "full_grid_integral_readback_passed"
        and value["snapshot_readback"]["rows"] == 5798
        and len(value["default_failed_batches"]) > 0,
        "Successful retained-source proof",
    )
    adapter.require(len(value["input_sha256"]) == 94, "Proof input population")
    for name, digest in value["input_sha256"].items():
        adapter.require(
            re.fullmatch(
                r"data/interim/vegetation/full_grid_v1/2019-03-22_b64/(?:manifest.json|snapshots.csv)"
                r"|data/raw/vegetation/full_grid_v1/2019-03-22_b64/(?:30|60)days_batch_\d{3}\.json",
                name,
            )
            and adapter.sha(ROOT / name) == digest,
            "Retained proof input changed",
        )
    return value


@contextlib.contextmanager
def adapted_supervisor(supervisor, proof, proof_sha):
    queue = supervisor.queue
    original_run_child, original_fingerprints, original_runtime = (
        queue.run_child,
        queue.fingerprints,
        supervisor.runtime,
    )
    additions = (
        Path(__file__).relative_to(ROOT).as_posix(),
        Path(adapter.__file__).relative_to(ROOT).as_posix(),
    )

    def fingerprints():
        adapter.checked_base()
        return {**original_fingerprints(), **{p: adapter.sha(ROOT / p) for p in additions}}

    def runtime():
        checked_proof(proof, proof_sha)
        return {
            **original_runtime(),
            "execution_adapter": {
                **adapter.identity(),
                "proof_sha256": proof_sha,
                "supervisor_v2_sha256": adapter.sha(Path(__file__)),
            },
        }

    def run_child(arguments, log_path, deadline):
        choices = {
            "scripts/landcover/prepare_vegetation_month.py": "prepare",
            "scripts/quality/verify_vegetation_month.py": "verify",
        }
        hits = [(i, choices[a]) for i, a in enumerate(arguments) if a in choices]
        adapter.require(len(hits) == 1, "Known bounded vegetation child")
        index, task = hits[0]
        rewritten = [
            *arguments[:index],
            str(Path(__file__)),
            "child",
            "--entry",
            task,
            "--",
            *arguments[index + 1 :],
        ]
        # The original timeout, log file, child cleanup and error handling remain active.
        return original_run_child(rewritten, log_path, deadline)

    queue.fingerprints, queue.run_child, supervisor.runtime = fingerprints, run_child, runtime
    try:
        yield supervisor
    finally:
        queue.fingerprints, queue.run_child, supervisor.runtime = (
            original_fingerprints,
            original_run_child,
            original_runtime,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    prove = modes.add_parser("prove")
    prove.add_argument("--out", type=Path, default=PROOF)
    run = modes.add_parser("run")
    run.add_argument("--proof", type=Path, default=PROOF)
    run.add_argument("--proof-sha", required=True)
    run.add_argument("--start", default="2018-01")
    run.add_argument("--end", default="2023-12")
    run.add_argument("--hours", type=float, default=24)
    run.add_argument("--batch-minutes", type=float, default=240)
    run.add_argument("--min-free-gib", type=float, default=10)
    run.add_argument("--job-id")
    child = modes.add_parser("child")
    child.add_argument("--entry", required=True, choices=["prepare", "verify"])
    child.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.mode == "prove":
        value = adapter.prove(args.out)
        print(
            "ISO PROOF PASSED",
            value["snapshot_readback"]["rows"],
            "SHA",
            adapter.sha(args.out),
            flush=True,
        )
    elif args.mode == "child":
        arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        adapter.entry(args.entry, arguments)
    else:
        checked_proof(args.proof, args.proof_sha)
        supervisor = adapter.load(
            "vegetation_frozen_supervisor", ROOT / "scripts/landcover/run_vegetation_training.py"
        )
        with adapted_supervisor(supervisor, args.proof, args.proof_sha):
            report, _ = supervisor.run(
                args.start,
                args.end,
                hours=args.hours,
                batch_minutes=args.batch_minutes,
                min_free_gib=args.min_free_gib,
                job_id=args.job_id,
            )
        if report["status"] == "failed_checkpoints_retained":
            raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("VEGETATION V2 STOPPED:", type(error).__name__, "; checkpoints retained", flush=True)
        raise SystemExit(1) from None
