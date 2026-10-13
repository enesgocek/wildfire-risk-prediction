"""Install a renewed private Drive connection after same-folder and OAuth checks."""

import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

PRODUCTION_SHA = "0c5302cadf0c05dce36843254300cd8719346ddac4648c78c5c20a7dfd8f7394"
FIELDS = {"client_id", "client_secret", "refresh_token", "scope", "folder_id"}


def require(ok, label):
    if not ok:
        raise ValueError(label)


def read_private(path, home):
    require(path.resolve().is_relative_to(home.resolve()), "Private path boundary")
    for part in (path, *path.parents):
        require(not part.is_symlink(), "Private path symlink")
        if part == home:
            break
    require(path.is_file() and 0 < path.stat().st_size <= 65536, "Private file byte bound")
    return path.read_bytes()


def install(home, api_type, scope):
    source = home / "drive_connection.json"
    target = home / ".config/wildfire/drive_connection.json"
    old_raw, new_raw = read_private(target, home), read_private(source, home)
    old, new = json.loads(old_raw), json.loads(new_raw)
    require(set(old) == set(new) == FIELDS, "Private connection schema")
    require(
        all(isinstance(v, str) and 0 < len(v) <= 4096 for v in new.values()),
        "Private connection field bounds",
    )
    require(
        all(old[k] == new[k] for k in ("client_id", "client_secret", "scope", "folder_id"))
        and new["scope"] == scope,
        "Same client scope and result folder required",
    )
    require(re.fullmatch(r"[A-Za-z0-9_-]{10,200}", new["folder_id"]), "Folder identity")
    api = api_type(new)
    api.token()
    folder = json.loads(
        api.request(
            f"/files/{new['folder_id']}?fields=id,mimeType,trashed,capabilities(canAddChildren)"
        )
    )
    require(
        folder.get("id") == new["folder_id"]
        and folder.get("mimeType") == "application/vnd.google-apps.folder"
        and folder.get("trashed") is False
        and folder.get("capabilities", {}).get("canAddChildren") is True,
        "Renewed token must access the same result folder",
    )
    require(
        read_private(target, home) == old_raw and read_private(source, home) == new_raw,
        "Private connection changed during checks",
    )
    source.chmod(0o600)
    source.replace(target)
    require(read_private(target, home) == new_raw, "Private installation readback")
    print("PASS same_client_scope_folder")
    print("PASS renewed_token_and_existing_folder")
    print("PASS private_connection_installed")


def main():
    import fcntl

    require(sys.platform == "linux", "Run on the Linux VM")
    home = Path.home()
    package = home / "wildfire-gcp-production-package"
    manifest = package / "production_manifest.json"
    require(
        hashlib.sha256(read_private(manifest, home)).hexdigest() == PRODUCTION_SHA,
        "Pinned production manifest",
    )
    expected = json.loads(manifest.read_bytes())["files"]["drive_job_store.py"]
    path = package / "drive_job_store.py"
    require(
        hashlib.sha256(read_private(path, home)).hexdigest() == expected, "Pinned Drive library"
    )
    spec = importlib.util.spec_from_file_location("private_install_drive", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lock = home / "wildfire-gcp-production-v1/job.lock"
    require(lock.is_file() and not lock.is_symlink(), "Existing production lock")
    require(lock.resolve().is_relative_to(home.resolve()), "Job lock boundary")
    for part in lock.parents:
        require(not part.is_symlink(), "Job lock ancestor symlink")
        if part == home:
            break
    with lock.open("r") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        install(home, module.DriveAPI, module.SCOPE)


if __name__ == "__main__":
    os.umask(0o077)
    sys.dont_write_bytecode = True
    try:
        main()
    except Exception as error:
        print("Private connection check failed:", type(error).__name__, "; no external text logged")
        raise SystemExit(1) from None
