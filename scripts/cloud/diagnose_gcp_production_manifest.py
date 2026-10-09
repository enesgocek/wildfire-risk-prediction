"""Diagnose the failed first manifest; publish only with explicit --publish.

No NASA requests, raw processing, resource control or credential output.
The original production package and existing work are not rewritten.
"""

import argparse
import contextlib
import hashlib
import importlib
import json
import re
import sys
import urllib.error
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

EXPECTED_SCOPE = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
FILES = {
    "summer.zip",
    "compact.py",
    "pairs.csv",
    "sources.csv",
    "july_verification.json",
    "run_gcp_production.py",
    "gcp_production_support.py",
    "verified_job_store.py",
    "drive_job_store.py",
    "production_drive_store.py",
    "requirements.txt",
}
HTTP_REASONS = {
    "authError",
    "appNotAuthorizedToFile",
    "insufficientFilePermissions",
    "notFound",
    "storageQuotaExceeded",
    "dailyLimitExceeded",
    "rateLimitExceeded",
    "userRateLimitExceeded",
    "forbidden",
    "backendError",
    "accessNotConfigured",
    "badRequest",
    "invalid",
    "insufficientPermissions",
    "activeItemCreationLimitExceeded",
    "domainPolicy",
}


def http_summary(data):
    try:
        require(len(data) <= 65536, "HTTP body bound")
        body = json.loads(data)
        reasons = {r.get("reason") for r in body["error"].get("errors", [])}
        return ",".join(sorted(reasons & HTTP_REASONS)) or "UNCLASSIFIED"
    except Exception:
        return "UNCLASSIFIED"


def request_role(url):
    parsed = urlsplit(url)
    if parsed.hostname == "oauth2.googleapis.com":
        return "OAUTH"
    if parsed.path == "/upload/drive/v3/files":
        return "UPLOAD"
    if parsed.path == "/drive/v3/files/generateIds":
        return "ID_ALLOCATION"
    if parsed.path == "/drive/v3/about":
        return "QUOTA"
    if parse_qs(parsed.query).get("alt") == ["media"]:
        return "DOWNLOAD"
    return "LIST" if parsed.path == "/drive/v3/files" else "FILE_METADATA"


def diagnostic_opener(opener):
    def wrapped(request, timeout):
        try:
            return opener(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            # The existing transport discards bodies. Report only known reason enums.
            try:
                reason = http_summary(error.read(65537))
            except Exception:
                reason = "UNCLASSIFIED"
            code = error.code if type(error.code) is int and 100 <= error.code <= 599 else 0
            print("HTTP_DIAGNOSTIC", request_role(request.full_url), code, reason, flush=True)
            raise

    return wrapped


def quota_values(data):
    quota = json.loads(data)["storageQuota"]
    result = {}
    for key in ("limit", "usage"):
        value = quota.get(key)
        if value is None and key == "limit":
            result[key] = None
            continue
        require(isinstance(value, str) and re.fullmatch(r"[0-9]{1,20}", value), "Quota number")
        result[key] = int(value)
    return result


def require(ok, label):
    if not ok:
        raise ValueError(label)


def safe_error(error):
    # Do not expose URLs, response bodies, file contents or arbitrary messages.
    message = error.args[0] if len(error.args) == 1 else None
    if isinstance(message, str):
        match = re.fullmatch(r"Drive HTTP ([1-5][0-9]{2}); no secrets logged", message)
        if match:
            return "GOOGLE_HTTP_" + match[1]
        known = {
            "Drive transport failed; checkpoint retained": "GOOGLE_TRANSPORT_FAILURE",
            "Drive redirect refused": "GOOGLE_REDIRECT_REFUSED",
        }
        if message in known:
            return known[message]
    name = type(error).__name__
    return (
        name
        if name
        in {
            "ValueError",
            "RuntimeError",
            "OSError",
            "PermissionError",
            "FileNotFoundError",
            "JSONDecodeError",
            "KeyError",
            "TimeoutError",
            "BlockingIOError",
        }
        else "UNCLASSIFIED_ERROR"
    )


def stage(name, action):
    try:
        result = action()
    except Exception as error:
        print(f"FAIL {name}: {safe_error(error)}", flush=True)
        raise SystemExit(1) from None
    print("PASS", name, flush=True)
    return result


def verify_package(package, expected_scope=EXPECTED_SCOPE):
    require(not package.is_symlink(), "Package directory")
    manifest = package / "production_manifest.json"
    require(not manifest.is_symlink(), "Manifest symlink")
    data = manifest.read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected_scope, "Expected original manifest")
    spec = json.loads(data)
    require(set(spec["files"]) == FILES, "Package file set")
    for name, sha in spec["files"].items():
        path = package / name
        require(not path.is_symlink() and path.is_file(), "Package member")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == sha, "Package member SHA")
    return spec


def load_modules(package):
    sys.path.insert(0, str(package.resolve()))
    return (
        importlib.import_module("gcp_production_support"),
        importlib.import_module("production_drive_store"),
        importlib.import_module("verified_job_store"),
    )


def diagnose(package, connection, work, publish=False):
    spec = stage("original_package_integrity", lambda: verify_package(package))
    support, drive, protocol = load_modules(package)
    _, scope, catalogue, sources = stage("training_scope", lambda: support.read_scope(package))
    month = spec["months"][0]
    rows = sources.loc[sources.day.str.startswith(month)]
    payload = work / "months" / month / "manifest.zip"
    require(payload.is_file() and not payload.is_symlink(), "Existing manifest ZIP required")
    require(0 < payload.stat().st_size <= 20_000_000, "Metadata-only ZIP size bound")

    def check(path):
        return support.validate_month(path, month, rows, catalogue)

    stage("local_manifest_scientific_check", lambda: check(payload))
    print("MANIFEST_ZIP_BYTES", payload.stat().st_size, flush=True)
    backend = stage("private_connection", lambda: drive.ProductionDriveStore.from_file(connection))
    backend.api.opener = diagnostic_opener(backend.api.opener)
    stage("oauth_refresh", backend.api.token)

    def folder_check():
        value = json.loads(
            backend.api.request(f"/files/{backend.folder_id}?fields=mimeType,trashed")
        )
        require(value["mimeType"] == "application/vnd.google-apps.folder", "Folder type")
        require(value.get("trashed") is not True, "Folder trashed")

    stage("drive_folder_access", folder_check)
    quota = stage(
        "authenticated_drive_storage_quota",
        lambda: quota_values(backend.api.request("/about?fields=storageQuota(limit,usage)")),
    )
    print("DRIVE_USAGE_GB", round(quota["usage"] / 1_000_000_000, 2), flush=True)
    if quota["limit"] is None:
        print("DRIVE_LIMIT unlimited_or_no_limit_returned", flush=True)
    else:
        print("DRIVE_LIMIT_GB", round(quota["limit"] / 1_000_000_000, 2), flush=True)
        print(
            "DRIVE_FREE_GB", round((quota["limit"] - quota["usage"]) / 1_000_000_000, 2), flush=True
        )
        stage(
            "metadata_storage_capacity",
            lambda: require(
                quota["limit"] - quota["usage"] >= payload.stat().st_size + 65536,
                "Drive quota insufficient for metadata",
            ),
        )
    used = stage("production_listing", lambda: backend.used_bytes("jobs/" + scope))
    print("PRODUCTION_SAVED_BYTES", used, flush=True)
    store = protocol.VerifiedJobStore(
        backend, scope, spec["files"]["run_gcp_production.py"], 200_000_000_000
    )
    task = "manifest:" + month
    names = support.month_names(rows)
    saved = stage("existing_manifest_readback", lambda: store.restore(task, names, check))
    if saved is not None:
        print("MANIFEST_READY existing verified completion; no write needed", flush=True)
        return
    print("MANIFEST_COMPLETION absent", flush=True)
    if not publish:
        print("READ_ONLY_COMPLETE; no upload requested", flush=True)
        return

    def first_failed_invocation():
        progress = json.loads((work / "progress.json").read_text())
        require(progress["queue_manifest_sha256"] == scope, "Progress original scope")
        require(progress["status"] == "failed_checkpoints_retained", "Expected failed invocation")
        require(progress["pairs_processed_this_invocation"] == 0, "No processed pairs expected")
        require(progress["pairs_reused_this_invocation"] == 0, "No reused pairs expected")
        require(progress["days_verified_this_invocation"] == [], "No completed days expected")

    stage("first_failure_scope", first_failed_invocation)
    stage("manifest_publish_and_verified_readback", lambda: store.save(task, payload, names, check))
    print("MANIFEST_READY published and verified; raw processing not started", flush=True)


@contextlib.contextmanager
def exclusive_work(work):
    import fcntl

    require(work.is_dir() and not work.is_symlink(), "Existing work directory required")
    path = work / "job.lock"
    require(path.is_file() and not path.is_symlink(), "Existing job lock required")
    with path.open("r+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true", help="Save only the checked metadata ZIP")
    args = parser.parse_args()
    home = Path.home()
    work = home / "wildfire-gcp-production-v1"
    try:
        with exclusive_work(work):
            diagnose(
                home / "wildfire-gcp-production-package",
                home / ".config/wildfire/drive_connection.json",
                work,
                publish=args.publish,
            )
    except Exception as error:
        print("FAIL diagnostic_setup:", safe_error(error), flush=True)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
