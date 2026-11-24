"""Verify a local release without pandas, model libraries, network or training."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


def sha256(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def verify(release):
    package = release / "package"
    receipt = json.loads((release / "readback.json").read_bytes())
    manifest_path = package / "manifest.json"
    archive = release / "research_release.zip"
    if (
        sha256(manifest_path) != receipt["manifest_sha256"]
        or sha256(archive) != receipt["zip_sha256"]
    ):
        raise ValueError("Release container hash mismatch")
    manifest = json.loads(manifest_path.read_bytes())
    entries = manifest["files"]
    expected = set(entries) | {"manifest.json"}
    observed = {p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()}
    if expected != observed:
        raise ValueError("Package file inventory mismatch")
    for name, entry in entries.items():
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
            raise ValueError("Unsafe manifest path")
        local = package / name
        if (
            local.is_symlink()
            or local.stat().st_size != entry["bytes"]
            or sha256(local) != entry["sha256"]
        ):
            raise ValueError("Package byte mismatch: " + name)
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        if len(names) != len(set(names)) or set(names) != expected:
            raise ValueError("ZIP inventory mismatch")
        if zipped.testzip() is not None:
            raise ValueError("ZIP CRC mismatch")
        for name in names:
            if zipped.getinfo(name).file_size != (package / name).stat().st_size:
                raise ValueError("ZIP size mismatch")
            digest = hashlib.sha256()
            with zipped.open(name) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            if digest.hexdigest() != sha256(package / name):
                raise ValueError("ZIP bytes differ from directory")
    return {
        "files_including_manifest": len(expected),
        "status": "all_directory_and_zip_bytes_verified",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    print(json.dumps(verify(parser.parse_args().release), ensure_ascii=False))
