"""One planned native pair, private in-memory login, sequential cache and 15-minute cap."""

import argparse
import contextlib
import getpass
import importlib.util
import io
import json
import logging
import os
import subprocess
import sys
import time
import uuid
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path

from wildfire_risk_prediction.core_transfer import (
    SAFE_ERROR_CODES,
    check_file,
    digest,
    safe_error_details,
    transfer_one,
)
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/reports/dataset/observation_core_native_v1"
PLAN_ROOT = ROOT / "outputs/reports/dataset/observation_core_transfer_v1"


def load_plan(path):
    path = path.resolve()
    require(
        path.is_relative_to(PLAN_ROOT) and path.name == "native_plan.json",
        "Project-local prepared plan",
    )
    folder = path.parent
    report = json.loads((folder / "readback.json").read_text(encoding="utf-8"))
    completion = json.loads((folder / "completion_readback.json").read_text(encoding="utf-8"))
    require(digest(folder / "readback.json") == completion["report_sha256"], "Preparation receipt")
    require(digest(path) == report["artifact_sha256"]["native_plan.json"], "Accepted native plan")
    plan = json.loads(path.read_text(encoding="utf-8"))
    require(
        plan["status"] == "bounded_one_pair_access_and_header_probe"
        and plan["execution_scope"] == "first_chronological_pair_only"
        and plan["pair_workers"] == 1
        and plan["hard_runtime_seconds"] == 900
        and plan["cache_limit_bytes"] == 2_000_000_000
        and plan["minimum_free_bytes"] == 20_000_000_000
        and plan["cloud_execution_permitted"] is False
        and plan["raw_eviction_permitted"] is False
        and plan["negative_label_permitted"] is False
        and plan["daily_observation_status"] == "unknown",
        "Bounded pilot policy",
    )
    require(
        plan.get("redirect_policy")
        == "one_exact_cmr_s3_object_in_separate_credential_free_session",
        "Reviewed single-hop S3 policy",
    )
    require(
        plan.get("failure_diagnostics_policy")
        == "literal_guard_codes_and_safe_structural_fields_only",
        "Safe failure diagnostics policy",
    )
    require(
        all(digest(ROOT / n) == h for n, h in plan["input_sha256"].items()),
        "Exact current plan inputs",
    )
    first = plan["all_pairs_inventory_only"][0]
    require(
        first["sample_id"] == plan["first_pair"] and first["bytes"] == plan["first_pair_bytes"],
        "First pair only",
    )
    return plan, first


def latest_plan():
    candidates = sorted(PLAN_ROOT.glob("*/native_plan.json"), reverse=True)
    completed = [p for p in candidates if (p.parent / "completion_readback.json").is_file()]
    require(bool(completed), "Completed native plan required")
    # The caller still runs load_plan; never fall back silently if newest code/scope is stale.
    return completed[0]


def native_headers(pair, cache):
    import rasterio

    path = ROOT / "scripts/firms/inspect_l2_observation_sample.py"
    spec = importlib.util.spec_from_file_location("core_native_inspector", path)
    inspector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inspector)
    sources = {s["role"]: s for s in pair["sources"]}
    fire, geo = [cache / sources[r]["filename"] for r in ("fire", "geolocation")]
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask = inspector.layer(stack, fire, "fire_mask")
        qa = inspector.layer(stack, fire, "algorithm_QA")
        lat = inspector.layer(stack, geo, "geolocation_data/latitude")
        lon = inspector.layer(stack, geo, "geolocation_data/longitude")
        key = inspector.validate_pair(fire, geo, mask.tags(), lat.tags())
        require(pair["sample_id"].endswith(":" + key), "Native pair key")
        require(mask.shape == qa.shape == lat.shape == lon.shape, "Native swath dimensions")
        require(mask.dtypes == ("uint8",) and qa.dtypes == ("uint32",), "Native fire/QA types")
        interval = sources["fire"]["metadata"]["TemporalExtent"]["RangeDateTime"]
        for field, expected in (("StartTime", "BeginningDateTime"), ("EndTime", "EndingDateTime")):
            actual = datetime.strptime(mask.tags()[field], "%Y-%m-%d %H:%M:%S.%f").replace(
                tzinfo=UTC
            )
            require(
                actual == datetime.fromisoformat(interval[expected].replace("Z", "+00:00")),
                "Native/CMR interval",
            )
        orbit = int(lat.tags()["OrbitNumber"])
        require(orbit > 0, "Native orbit identity")
        return {
            "native_pair_input_pointer_verified": True,
            "native_dimensions": list(mask.shape),
            "orbit_id": pair["sample_id"].split(":")[0] + ":" + str(orbit),
            "array_values_spatially_audited": False,
        }


def write_json(path, value):
    require(not path.exists(), "No accepted result overwrite")
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def child(plan_path, out):
    import earthaccess

    logging.disable(logging.CRITICAL)
    plan, pair = load_plan(plan_path)
    require(out.resolve().is_relative_to(OUTPUT) and out.is_dir(), "Prepared output directory")
    cache = ROOT / "data/raw/observation_core_v1" / digest(plan_path)[:16]
    cache.mkdir(parents=True, exist_ok=True)
    lock = cache / "writer.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    phase = "private_authentication"
    active_role = None
    try:
        deadline = time.monotonic() + plan["hard_runtime_seconds"] - 20
        records = []
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            auth = earthaccess.login(strategy="environment", persist=False)
            require(auth.authenticated, "Private EDL authentication")
            session = auth.get_session()
            session.auth = None  # Bearer only; never send the username/password to a data URL.
            session.trust_env = False  # No ambient netrc credential injection.
            try:
                for source in pair["sources"]:
                    phase = "bounded_file_transfer"
                    active_role = source["role"]
                    records.append(
                        transfer_one(
                            session,
                            source,
                            cache,
                            deadline=deadline,
                            cache_limit_bytes=plan["cache_limit_bytes"],
                            reserve_bytes=plan["minimum_free_bytes"],
                        )
                    )
            finally:
                session.close()
        phase = "native_headers"
        headers = native_headers(pair, cache)
        for source in pair["sources"]:
            check_file(cache / source["filename"], source)
        require(
            all(digest(ROOT / n) == h for n, h in plan["input_sha256"].items()),
            "Native probe input closure",
        )
        result = {
            "checked_at_utc": datetime.now(UTC).isoformat(),
            "status": "one_pair_bytes_and_headers_passed",
            "sample_id": pair["sample_id"],
            "plan_sha256": digest(plan_path),
            "sources": records,
            "network_bytes": sum(r["network_bytes"] for r in records),
            "cache_directory": cache.relative_to(ROOT).as_posix(),
            **headers,
            "labels_created": False,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "model_ready": False,
            "full_spatial_pilot_complete": False,
            "cloud_jobs_started": 0,
        }
        write_json(out / "native_probe.json", result)
        require(
            json.loads((out / "native_probe.json").read_text(encoding="utf-8")) == result,
            "Native probe readback",
        )
        write_json(
            out / "completion_readback.json",
            {"status": "passed", "report_sha256": digest(out / "native_probe.json")},
        )
    except Exception as error:
        write_json(
            out / "failure.json",
            {
                "status": "failed_raw_and_partial_files_retained",
                "phase": phase,
                "error_type": type(error).__name__,
                **safe_error_details(error),
                "active_source_role": active_role,
                "sample_id": pair["sample_id"],
                "exception_message_recorded": False,
                "negative_label_permitted": False,
            },
        )
        raise
    finally:
        lock.unlink()


def run(plan_path, prompt):
    logging.disable(logging.CRITICAL)
    plan, pair = load_plan(plan_path)

    print("Tek çift:", pair["sample_id"], "Bayt:", pair["bytes"], flush=True)
    token = None
    if prompt:
        require(sys.stdin.isatty(), "Private login requires an interactive terminal")
        import earthaccess

        username = getpass.getpass("Earthdata kullanici adi (gizli): ")
        password = getpass.getpass("Earthdata sifre (gizli): ")
        old = {
            k: os.environ.get(k)
            for k in ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD", "EARTHDATA_TOKEN")
        }
        try:
            os.environ.pop("EARTHDATA_TOKEN", None)
            os.environ["EARTHDATA_USERNAME"], os.environ["EARTHDATA_PASSWORD"] = username, password
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                auth = earthaccess.login(strategy="environment", persist=False)
                require(auth.authenticated, "Private login")
                token = auth.token["access_token"]
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        username = password = None
    else:
        require(
            bool(os.environ.get("EARTHDATA_TOKEN")), "Set a private EDL token or use --prompt-login"
        )
        token = os.environ["EARTHDATA_TOKEN"]
    out = OUTPUT / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    env.pop("EARTHDATA_USERNAME", None)
    env.pop("EARTHDATA_PASSWORD", None)
    env["EARTHDATA_TOKEN"] = token
    # The child receives the token only in its environment, never arguments, files or logs.
    command = [
        sys.executable,
        str(Path(__file__)),
        "--plan",
        str(plan_path.resolve()),
        "--worker",
        str(out),
    ]
    print(
        "15 dakika sinirli yerel kontrol basliyor; bilgileri veya terminal dokumunu paylasma.",
        flush=True,
    )
    try:
        result = subprocess.run(
            command,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=plan["hard_runtime_seconds"],
            check=False,
        )
        state = "child_completed" if result.returncode == 0 else "child_failed_partial_retained"
    except subprocess.TimeoutExpired:
        state = "hard_timeout_partial_and_lock_retained"
    finally:
        env.pop("EARTHDATA_TOKEN", None)
        token = None
    write_json(
        out / "launcher_receipt.json",
        {
            "status": state,
            "plan_sha256": digest(plan_path),
            "sample_id": pair["sample_id"],
            "hard_runtime_seconds": plan["hard_runtime_seconds"],
            "credentials_written": False,
            "child_output_suppressed": True,
            "cloud_jobs_started": 0,
        },
    )
    print("Sonuc klasoru:", out.relative_to(ROOT).as_posix(), flush=True)
    if state != "child_completed":
        failure_path = out / "failure.json"
        if failure_path.is_file():
            failure = json.loads(failure_path.read_text(encoding="utf-8"))
            code = failure.get("safe_code", "unclassified")
            code = code if code in set(SAFE_ERROR_CODES.values()) else "unclassified"
            print("Kontrol kodu:", code, flush=True)
        print("Kontrol tamamlanmadi; dosyalari koru ve yalniz bu genel durumu bildir.", flush=True)
        return 1
    completion = json.loads((out / "completion_readback.json").read_text(encoding="utf-8"))
    require(
        completion["report_sha256"] == digest(out / "native_probe.json"), "Completed child result"
    )
    print("PASS one_pair_bytes_and_headers; etiket veya genis pilot kabul edilmedi.", flush=True)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--plan", type=Path)
    source.add_argument("--latest-plan", action="store_true")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--run-one", action="store_true")
    action.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--prompt-login", action="store_true")
    args = parser.parse_args()
    try:
        plan_path = latest_plan() if args.latest_plan else args.plan
        if args.worker:
            child(plan_path, args.worker)
        else:
            raise SystemExit(run(plan_path, args.prompt_login))
    except Exception as error:
        print("Kontrol tamamlanmadi:", type(error).__name__, flush=True)
        raise SystemExit(1) from None
