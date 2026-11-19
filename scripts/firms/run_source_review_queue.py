"""Seven frozen source rows: one private login, sequential headers-only download queue."""

import argparse
import contextlib
import getpass
import importlib.util
import io
import json
import logging
import os
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset/source_review_queue_v1"
ROWS = {"WF1207", "WF1300", "WF1351", "WF1421", "WF1431", "WF1504", "WF1538"}
SAMPLE_SHA = "9647a69248ac158aad6f7a864b48bfad8eb61860be08ff3250f8dc643cd4d453"


def runner_module():
    spec = importlib.util.spec_from_file_location(
        "source_pair_runner", ROOT / "scripts/firms/run_observation_core_pair.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_policy(plan):
    require(
        plan["scope"] == "seven_frozen_source_rows_download_headers_only"
        and plan["source_sample_sha256"] == SAMPLE_SHA,
        "Frozen source sample only",
    )
    require(
        plan["workers"] == 1
        and plan["download_runtime_seconds"] == 3600
        and plan["per_pair_runtime_seconds"] == 900
        and plan["stop_on_first_failure"] is True
        and plan["automatic_restart"] is False
        and plan["raw_eviction_permitted"] is False,
        "One worker, bounded duration, retained files and no automatic retry",
    )
    require(
        plan["labels_created"] is False
        and plan["negative_label_permitted"] is False
        and plan["daily_observation_status"] == "unknown"
        and plan["model_training_permitted"] is False
        and plan["cloud_execution_permitted"] is False
        and plan["spatial_or_daily_acceptance_permitted"] is False,
        "Closed scientific and cloud gates",
    )
    units = plan["units"]
    require(
        len(units) == 7 and {r["archive_row"] for r in units} == ROWS,
        "Exactly seven pending rows; no replacements",
    )
    require(
        all(2018 <= int(r["source_day"][:4]) <= 2022 and r["bytes"] > 0 for r in units)
        and sum(r["bytes"] for r in units) == plan["total_raw_bytes"]
        and plan["total_raw_bytes"] <= 1_500_000_000,
        "Fit-role years and bounded raw bytes",
    )


def load_plan(path, runner):
    path = path.resolve()
    require(path.is_relative_to(BASE) and path.name == "queue_plan.json", "Local queue plan")
    report_path = path.parent / "readback.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    receipt = json.loads((path.parent / "completion_readback.json").read_text(encoding="utf-8"))
    require(digest(report_path) == receipt["report_sha256"], "Queue preparation receipt")
    require(digest(path) == report["artifact_sha256"][path.name], "Queue plan bytes")
    plan = json.loads(path.read_text(encoding="utf-8"))
    validate_policy(plan)
    require(
        all(digest(ROOT / n) == h for n, h in plan["input_sha256"].items()),
        "Exact queue code and evidence inputs",
    )
    for unit in plan["units"]:
        native_path = (ROOT / unit["plan"]).resolve()
        require(digest(native_path) == unit["plan_sha256"], "Pinned pair plan")
        native, pair = runner.load_plan(native_path)
        require(
            len(native["all_pairs_inventory_only"]) == 1
            and native["source_review_archive_row"] == unit["archive_row"]
            and pair["sample_id"] == unit["sample_id"]
            and pair["source_day"] == unit["source_day"]
            and pair["bytes"] == unit["bytes"],
            "Queue and pair scope match",
        )
    return plan


def completed_probe(unit, runner):
    """Resume only from a completed, hash-verified native result and surviving bytes."""
    for path in sorted(runner.OUTPUT.glob("*/native_probe.json"), reverse=True):
        report = json.loads(path.read_text(encoding="utf-8"))
        if report.get("plan_sha256") != unit["plan_sha256"]:
            continue
        receipt_path = path.parent / "completion_readback.json"
        if not receipt_path.is_file():
            continue
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        require(
            receipt["status"] == "passed" and receipt["report_sha256"] == digest(path),
            "Completed native receipt",
        )
        require(
            report["status"] == "one_pair_bytes_and_headers_passed"
            and report["sample_id"] == unit["sample_id"]
            and report["native_pair_input_pointer_verified"] is True
            and report["labels_created"] is False
            and report["negative_label_permitted"] is False
            and report["daily_observation_status"] == "unknown",
            "Native headers only; gates closed",
        )
        expected = "data/raw/observation_core_v1/" + unit["plan_sha256"][:16]
        require(report["cache_directory"] == expected, "Exact pair cache")
        _, pair = runner.load_plan(ROOT / unit["plan"])
        for source in pair["sources"]:
            check_file(ROOT / expected / source["filename"], source)
        return {"probe": path.relative_to(ROOT).as_posix(), "sha256": digest(path)}
    return None


@contextlib.contextmanager
def private_token(prompt):
    """Keep credentials in memory/environment only; restore the caller environment."""
    keys = ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD", "EARTHDATA_TOKEN")
    old = {k: os.environ.get(k) for k in keys}
    old_logging = logging.root.manager.disable
    username = password = token = auth = None
    try:
        logging.disable(logging.CRITICAL)
        if prompt:
            require(sys.stdin.isatty(), "Private login requires an interactive terminal")
            import earthaccess

            username = getpass.getpass("Earthdata kullanici adi (gizli): ")
            password = getpass.getpass("Earthdata sifre (gizli): ")
            os.environ.pop("EARTHDATA_TOKEN", None)
            os.environ["EARTHDATA_USERNAME"], os.environ["EARTHDATA_PASSWORD"] = username, password
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                auth = earthaccess.login(strategy="environment", persist=False)
                require(auth.authenticated, "Private login")
                token = auth.token["access_token"]
        else:
            token = old["EARTHDATA_TOKEN"]
            require(bool(token), "Private token or interactive login required")
        os.environ.pop("EARTHDATA_USERNAME", None)
        os.environ.pop("EARTHDATA_PASSWORD", None)
        os.environ["EARTHDATA_TOKEN"] = token
        username = password = auth = None
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        username = password = token = auth = None
        logging.disable(old_logging)


def write(path, value):
    require(not path.exists(), "No evidence overwrite")
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run(path, execute=False, prompt=False):
    runner = runner_module()
    plan = load_plan(path, runner)
    done = {u["archive_row"]: completed_probe(u, runner) for u in plan["units"]}
    pending = [u for u in plan["units"] if done[u["archive_row"]] is None]
    amount = sum(u["bytes"] for u in pending)
    require(shutil.disk_usage(ROOT).free >= 20_000_000_000 + amount, "Disk reserve")
    print("Kalan cift:", len(pending), "Azami yeni bayt:", amount, flush=True)
    if not execute:
        print("PASS queue_preflight_only; indirme baslatilmadi.")
        return 0
    out = BASE / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    print("Sonuc klasoru:", out.relative_to(ROOT).as_posix(), flush=True)
    result = {
        "plan_sha256": digest(path),
        "status": "running",
        "units": [],
        "labels_created": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "spatial_or_daily_acceptance_performed": False,
        "credentials_written": False,
        "cloud_jobs_started": 0,
    }
    try:
        if pending:
            with private_token(prompt):
                deadline = time.monotonic() + plan["download_runtime_seconds"]
                for unit in plan["units"]:
                    prior = done[unit["archive_row"]]
                    if prior is None:
                        if time.monotonic() + 930 > deadline:
                            result["status"] = "paused_at_download_runtime_reserve"
                            break
                        print("Kontrol:", unit["archive_row"], flush=True)
                        before = set(runner.OUTPUT.glob("*/launcher_receipt.json"))
                        try:
                            with contextlib.redirect_stdout(io.StringIO()):
                                code = runner.run(ROOT / unit["plan"], prompt=False)
                        finally:
                            result["last_attempt_archive_row"] = unit["archive_row"]
                            result["last_attempt_receipts"] = [
                                p.relative_to(ROOT).as_posix()
                                for p in sorted(
                                    set(runner.OUTPUT.glob("*/launcher_receipt.json")) - before
                                )
                            ]
                        require(code == 0, "Pair failed; stop and retain files")
                        prior = completed_probe(unit, runner)
                        require(prior is not None, "Verified native completion required")
                    result["units"].append({"archive_row": unit["archive_row"], **prior})
                    # This file is explicitly mutable live progress, not an accepted final report.
                    (out / "progress.json").write_text(
                        json.dumps(result, indent=2), encoding="utf-8"
                    )
        else:
            result["units"] = [{"archive_row": k, **v} for k, v in done.items()]
        if result["status"] == "running":
            result["status"] = "seven_pairs_bytes_headers_complete_not_spatial_acceptance"
    except (Exception, KeyboardInterrupt) as error:
        result["status"] = "stopped_outputs_retained"
        result["error_type"] = type(error).__name__
        result["exception_message_recorded"] = False
    finally:
        write(out / "readback.json", result)
        write(out / "completion_readback.json", {"report_sha256": digest(out / "readback.json")})
    print(result["status"], "; etiket veya gunluk gozlem kabulu degildir.", flush=True)
    return 0 if len(result["units"]) == 7 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--prompt-login", action="store_true")
    args = parser.parse_args()
    try:
        raise SystemExit(run(args.plan, args.run, args.prompt_login))
    except Exception as error:
        print("Kontrol tamamlanmadi:", type(error).__name__, "; dosyalar korundu.")
        raise SystemExit(1) from None
