"""Read-only diagnosis of the frozen VM proof; credentials never printed.

Does not rewrite uploaded code/manifests, upload/delete Drive objects, or
download NASA raw data. Caller should bound execution with GNU timeout.
"""

import ast
import hashlib
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path

SAFE_CHECK_MESSAGES = set()


def add_safe_check_messages(source):
    # Only static require(..., 'literal') labels from SHA-checked source code
    # are eligible; never print a dynamic exception message/response body.
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or len(node.args) < 2:
            continue
        name = getattr(node.func, "id", getattr(node.func, "attr", ""))
        label = node.args[1]
        if (
            name == "require"
            and isinstance(label, ast.Constant)
            and isinstance(label.value, str)
            and 0 < len(label.value) <= 100
            and all(32 <= ord(c) < 127 for c in label.value)
        ):
            SAFE_CHECK_MESSAGES.add(label.value)


def safe_error(error):
    """Only exact messages emitted by our transport get public detail."""
    message = str(error)
    matched = re.fullmatch(r"Drive HTTP (\d{3}); no secrets logged", message)
    if matched:
        return "GOOGLE_HTTP_" + matched[1]
    if isinstance(error, ValueError) and message in SAFE_CHECK_MESSAGES:
        return "CHECK_FAILED: " + message
    known = {
        "Drive redirect refused": "REDIRECT_REFUSED",
        "Drive transport failed; checkpoint retained": "TRANSPORT_FAILED",
        "Unexpected OAuth scope": "OAUTH_SCOPE_DIFFERS",
        "Connection must be chmod 600": "CONNECTION_PERMISSIONS",
        "Duplicate Drive object; manual review required": "DUPLICATE_OBJECT",
    }
    return known.get(message, type(error).__name__)


def stage(name, action):
    try:
        result = action()
    except Exception as error:
        print(f"FAIL {name}: {safe_error(error)}", flush=True)
        return False, None
    print(f"PASS {name}", flush=True)
    return True, result


def diagnose(package, connection, work):
    sys.path.insert(0, str(package))
    import run_gcp_drive_proof as runner
    from drive_job_store import DriveJobStore
    from verified_job_store import VerifiedJobStore

    runner.PACKAGE = package
    ok, spec = stage("package_integrity", runner.spec_read)
    if not ok:
        return 1
    for filename in spec["files"]:
        if filename.endswith(".py"):
            add_safe_check_messages((package / filename).read_text())
    with zipfile.ZipFile(package / "summer.zip") as archive:
        for name in archive.namelist():
            if name.endswith(".py"):
                add_safe_check_messages(archive.read(name).decode())
    ok, backend = stage("private_connection", lambda: DriveJobStore.from_file(connection))
    if not ok:
        return 1
    ok, _ = stage("oauth_refresh", backend.api.token)
    if not ok:
        return 1

    def check_folder():
        data = json.loads(
            backend.api.request(f"/files/{backend.folder_id}?fields=id,mimeType,trashed")
        )
        if data["mimeType"] != "application/vnd.google-apps.folder" or data.get("trashed") is True:
            raise ValueError("Invalid folder")

    ok, _ = stage("drive_folder_access", check_folder)
    if not ok:
        return 1
    ok, entries = stage("drive_object_listing", backend.entries)
    if not ok:
        return 1
    print(f"OBJECT_COUNT {len(entries)}", flush=True)
    job = VerifiedJobStore(
        backend,
        runner.digest(package / "proof_manifest.json"),
        spec["files"]["verified_job_store.py"],
        20_000_000,
    )
    prefix = job.task_prefix(spec["sample_id"])
    payload_key = prefix + "/" + spec["files"]["pair.zip"] + ".zip"
    ok, data = stage("saved_payload_readback", lambda: backend.get(payload_key))
    if not ok:
        return 1
    if data is None:
        print("SAVED_PAYLOAD absent; no completion inferred", flush=True)
    elif hashlib.sha256(data).hexdigest() != spec["files"]["pair.zip"]:
        print("FAIL saved_payload_checksum", flush=True)
        return 1
    else:
        print("PASS saved_payload_checksum", flush=True)

    def science():
        work.mkdir(mode=0o700, parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as directory:
            root = Path(directory)
            native = runner.load("diagnostic_native", package / "run_gcp_benchmark.py")
            native.unpack(package / "summer.zip", root / "native")
            module = native.load_summer(root / "native")
            manifest, manifest_sha = module.manifest_read()
            pair = next(p for p in manifest["pairs"] if p["sample_id"] == spec["sample_id"])
            module.restore_pair(package / "pair.zip", pair, manifest_sha, root / "restored")
            if not module.checkpoint_read(pair, root / "restored", manifest_sha):
                raise ValueError("Science checkpoint missing")

    ok, _ = stage("local_scientific_readback", science)
    if ok:
        print("READ_ONLY_DIAGNOSIS_COMPLETE; no upload or production work performed", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    home = Path.home()
    try:
        code = diagnose(
            home / "wildfire-gcp-drive-package",
            home / ".config/wildfire/drive_connection.json",
            home / "wildfire-gcp-drive-proof/diagnostic",
        )
    except Exception as error:
        print("FAIL diagnostic_setup:", safe_error(error), flush=True)
        code = 1
    raise SystemExit(code)
