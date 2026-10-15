"""Bounded, sequential pilot source transfer; never certify labels or evict evidence."""

import hashlib
import shutil
import time
from urllib.parse import urlsplit

from wildfire_risk_prediction.cmr_identity import identity
from wildfire_risk_prediction.feature_join import require

DATA_HOSTS = {"data.laadsdaac.earthdatacloud.nasa.gov", "data.lpdaac.earthdatacloud.nasa.gov"}


class DataResponseError(ValueError):
    """Only a numeric HTTP status may leave the private download worker."""

    def __init__(self, status):
        self.http_status = int(status)
        super().__init__("Direct NASA data response rejected")


def digest(path, algorithm="sha256"):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def source_url(source):
    identity(source)
    url = urlsplit(source["url"])
    require(
        url.scheme == "https"
        and url.hostname in DATA_HOSTS
        and url.port in {None, 443}
        and not url.username
        and not url.password
        and not url.query
        and not url.fragment
        and url.path.rsplit("/", 1)[-1] == source["filename"],
        "Exact NASA data URL without embedded credentials",
    )
    return source["url"]


def check_file(path, source):
    require(path.is_file() and not path.is_symlink(), "Regular native file")
    require(path.stat().st_size == source["bytes"], "Exact historical source size")
    require(digest(path) == source["sha256"], "Exact historical SHA-256")
    checksum = source.get("provider_checksum")
    if checksum:
        algorithm = checksum["Algorithm"].lower().replace("-", "")
        require(algorithm in {"md5", "sha256"}, "Supported provider checksum")
        require(digest(path, algorithm) == checksum["Value"].lower(), "Provider checksum")
    return {
        "bytes": path.stat().st_size,
        "sha256": digest(path),
        "provider_checksum_verified": bool(checksum),
    }


def cache_usage(cache):
    require(cache.is_dir() and not cache.is_symlink(), "Dedicated regular cache")
    files = list(cache.rglob("*"))
    require(not any(p.is_symlink() for p in files), "No cache symlinks")
    return sum(p.stat().st_size for p in files if p.is_file())


def capacity(cache, expected_bytes, cache_limit_bytes, reserve_bytes):
    require(type(expected_bytes) is int and expected_bytes > 0, "Positive expected transfer")
    require(cache_usage(cache) + expected_bytes <= cache_limit_bytes, "Pilot cache capacity")
    require(shutil.disk_usage(cache).free >= reserve_bytes + expected_bytes, "Free disk reserve")


def transfer_one(session, source, cache, *, deadline, cache_limit_bytes, reserve_bytes):
    """A full file or a retained partial; partial bytes are never an accepted checkpoint.

    Redirects are refused, not followed with credentials. A current distribution requiring
    another auth flow is an explicit failed access probe; no alternate URL substitution.
    """
    url = source_url(source)
    target = cache / source["filename"]
    require(target.parent.resolve() == cache.resolve(), "Contained native target")
    if target.exists():
        result = check_file(target, source)
        return {**result, "reused": True, "network_bytes": 0}
    partial = target.with_suffix(target.suffix + ".part")
    require(not partial.exists(), "Retained partial requires review before retry")
    capacity(cache, source["bytes"], cache_limit_bytes, reserve_bytes)
    require(time.monotonic() < deadline, "Pilot deadline before request")
    received = 0
    # Session owns only an in-memory EDL bearer token; raw credential redirects are disabled.
    with session.get(
        url,
        stream=True,
        allow_redirects=False,
        timeout=(10, 30),
        headers={"Accept-Encoding": "identity"},
    ) as response:
        if response.status_code != 200:
            raise DataResponseError(response.status_code)
        require(response.url == url, "Exact direct NASA data URL")
        require(
            response.headers.get("Content-Encoding", "identity") == "identity",
            "Unencoded native bytes",
        )
        length = response.headers.get("Content-Length")
        require(
            length is None or length.isdigit() and int(length) == source["bytes"], "Response length"
        )
        with partial.open("xb") as stream:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                require(time.monotonic() < deadline, "Pilot transfer deadline")
                if not chunk:
                    continue
                received += len(chunk)
                require(received <= source["bytes"], "Transfer exceeds historical byte bound")
                require(
                    shutil.disk_usage(cache).free >= reserve_bytes + len(chunk),
                    "Transfer disk reserve",
                )
                stream.write(chunk)
    check_file(partial, source)
    partial.rename(target)
    result = check_file(target, source)
    return {**result, "reused": False, "network_bytes": received}
