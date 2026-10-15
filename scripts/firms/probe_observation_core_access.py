"""Two first-pair HTTP header probes; no redirects, response bodies or raw writes."""

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
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from wildfire_risk_prediction.core_transfer import (
    DATA_HOSTS,
    digest,
    safe_error_details,
    same_request_url,
    signed_data_target,
    source_url,
)
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/reports/dataset/observation_core_access_v1"
LIMIT = 120
PUBLIC_HOSTS = DATA_HOSTS | {"urs.earthdata.nasa.gov", "ladsweb.modaps.eosdis.nasa.gov"}
OAUTH_CODES = {
    "invalid_token",
    "invalid_grant",
    "invalid_client",
    "invalid_request",
    "unauthorized_client",
    "access_denied",
    "insufficient_scope",
    "server_error",
    "temporarily_unavailable",
}


def runner():
    spec = importlib.util.spec_from_file_location(
        "accepted_core_runner", ROOT / "scripts/firms/run_observation_core_pair.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def redirect_summary(location, origin):
    """Return only fixed public host/path classes and literal OAuth codes."""
    target, start = urlsplit(location), urlsplit(origin)
    host = target.hostname or ""
    path = target.path
    kind = (
        "provider_error"
        if host == start.hostname and path in {"/error", "/error/"}
        else "provider_login"
        if host == start.hostname and path in {"/login", "/login/"}
        else "edl_authorize"
        if host == "urs.earthdata.nasa.gov" and path == "/oauth/authorize"
        else "science_filename"
        if path.rsplit("/", 1)[-1] == start.path.rsplit("/", 1)[-1]
        else "unclassified"
    )
    params = parse_qs(target.query)
    error = params.get("error", [])
    return {
        "public_host": host
        if host in PUBLIC_HOSTS
        else "aws"
        if host.endswith(".amazonaws.com")
        else "cloudfront"
        if host.endswith(".cloudfront.net")
        else "unclassified",
        "same_origin": target.scheme == start.scheme and target.netloc == start.netloc,
        "path_kind": kind,
        "oauth_error_code": error[0]
        if len(error) == 1 and error[0] in OAUTH_CODES
        else "unclassified",
        "has_query": bool(target.query),
    }


def inspect_source(session, source):
    url = source_url(source)
    record = {"source_id": source["source_id"], "role": source["role"], "body_bytes_read": 0}
    try:
        with session.get(
            url,
            stream=True,
            allow_redirects=False,
            timeout=(10, 20),
            headers={"Accept-Encoding": "identity"},
        ) as response:
            require(same_request_url(response.url, url), "Exact direct NASA data URL")
            record["http_status"] = int(response.status_code)
            if response.status_code in {302, 303, 307, 308}:
                location = response.headers.get("Location", "")
                record["redirect"] = redirect_summary(location, url)
                try:
                    signed_data_target(source, location)
                    record["exact_signed_object"] = True
                except ValueError as error:
                    record["exact_signed_object"] = False
                    record["safe_code"] = safe_error_details(error)["safe_code"]
                record["status"] = "redirect_headers_only"
            elif response.status_code == 200:
                length = response.headers.get("Content-Length", "")
                record["content_length_matches"] = (
                    length.isdigit() and int(length) == source["bytes"]
                )
                record["status"] = "direct_headers_only"
            else:
                record["status"] = "http_rejected"
    except Exception as error:
        record.update(
            status="request_failed", error_type=type(error).__name__, **safe_error_details(error)
        )
    return record


def header_session():
    import requests

    class HeaderOnlySession(requests.Session):
        def resolve_redirects(self, *_args, **_kwargs):
            # Session.send otherwise prepares Response.next and consumes a redirect body
            # even with allow_redirects=False. Never enter that machinery for this probe.
            return iter(())

    return HeaderOnlySession()


def worker(out, plan_path):
    logging.disable(logging.CRITICAL)
    m = runner()
    plan, pair = m.load_plan(plan_path)
    require(
        len(pair["sources"]) == 2
        and {s["role"] for s in pair["sources"]} == {"fire", "geolocation"},
        "Exactly two planned access probes",
    )
    require(out.resolve().is_relative_to(OUTPUT) and out.is_dir(), "Prepared access output")
    token = os.environ.pop("EARTHDATA_TOKEN", None)
    require(bool(token), "Private EDL token required")
    # Fresh session: no netrc/proxy injection, Earthaccess hooks or browser cookies.
    with header_session() as session:
        session.trust_env = False
        session.auth = None
        session.headers.clear()
        session.headers["Authorization"] = "Bearer " + token
        try:
            records = [inspect_source(session, source) for source in pair["sources"]]
        finally:
            session.headers.clear()
            session.cookies.clear()
            token = None
    m.load_plan(plan_path)
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "header_probe_complete_not_content_acceptance",
        "sample_id": pair["sample_id"],
        "plan_sha256": digest(plan_path),
        "probe_code_sha256": digest(Path(__file__)),
        "plan_inputs_verified": len(plan["input_sha256"]),
        "records": records,
        "request_limit": 2,
        "redirects_followed": 0,
        "body_bytes_read": 0,
        "raw_files_written": 0,
        "credentials_written": False,
        "cache_used_as_access_evidence": False,
        "automatic_transfer_verified": False,
        "labels_created": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
        "cloud_jobs_started": 0,
    }
    m.write_json(out / "access_probe.json", report)
    require(
        json.loads((out / "access_probe.json").read_text(encoding="utf-8")) == report,
        "Access report readback",
    )
    m.write_json(
        out / "completion_readback.json",
        {"status": "headers_recorded", "report_sha256": digest(out / "access_probe.json")},
    )


def private_token():
    require(sys.stdin.isatty(), "Private login requires an interactive terminal")
    import earthaccess

    names = ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD", "EARTHDATA_TOKEN")
    previous = {name: os.environ.get(name) for name in names}
    username = getpass.getpass("Earthdata kullanici adi (gizli): ")
    password = getpass.getpass("Earthdata sifre (gizli): ")
    try:
        os.environ.pop("EARTHDATA_TOKEN", None)
        os.environ["EARTHDATA_USERNAME"] = username
        os.environ["EARTHDATA_PASSWORD"] = password
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            auth = earthaccess.login(strategy="environment", persist=False)
        require(auth.authenticated, "Private EDL authentication")
        return auth.token["access_token"]
    finally:
        username = password = None
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def run():
    logging.disable(logging.CRITICAL)
    m = runner()
    plan_path = m.latest_plan()
    _, pair = m.load_plan(plan_path)  # Validate source/code closure before private input.
    token = private_token()
    out = OUTPUT / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    for name in ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD"):
        env.pop(name, None)
    env["EARTHDATA_TOKEN"] = token
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__)), "--worker", str(out), "--plan", str(plan_path)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=LIMIT,
            check=False,
        )
        state = "worker_finished" if result.returncode == 0 else "worker_failed"
    except subprocess.TimeoutExpired:
        state = "hard_timeout"
    finally:
        env.pop("EARTHDATA_TOKEN", None)
        token = None
    m.write_json(
        out / "launcher_receipt.json",
        {
            "status": state,
            "sample_id": pair["sample_id"],
            "plan_sha256": digest(plan_path),
            "probe_code_sha256": digest(Path(__file__)),
            "hard_runtime_seconds": LIMIT,
            "credentials_written": False,
            "child_output_suppressed": True,
        },
    )
    if state != "worker_finished":
        print("Erisim teshisi tamamlanmadi:", state, flush=True)
        return 1
    report_path = out / "access_probe.json"
    completion = json.loads((out / "completion_readback.json").read_text(encoding="utf-8"))
    require(completion["report_sha256"] == digest(report_path), "Access completion receipt")
    print("TESHIS KAYDEDILDI; indirme basarisi anlamina gelmez.", flush=True)
    print("Sonuc klasoru:", out.relative_to(ROOT).as_posix(), flush=True)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prompt-login", action="store_true")
    action.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--plan", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.worker:
            require(args.plan is not None, "Worker needs exact plan")
            worker(args.worker, args.plan)
        else:
            raise SystemExit(run())
    except Exception as error:
        print("Erisim teshisi tamamlanmadi:", type(error).__name__, flush=True)
        raise SystemExit(1) from None
