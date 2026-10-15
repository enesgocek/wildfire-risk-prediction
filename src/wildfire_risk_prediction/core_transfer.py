"""Bounded, sequential pilot source transfer; never certify labels or evict evidence."""

import hashlib
import re
import shutil
import time
from contextlib import ExitStack, contextmanager
from urllib.parse import parse_qs, parse_qsl, unquote, urlsplit

from wildfire_risk_prediction.cmr_identity import identity
from wildfire_risk_prediction.feature_join import require

DATA_HOSTS = {"data.laadsdaac.earthdatacloud.nasa.gov", "data.lpdaac.earthdatacloud.nasa.gov"}
SIGV4_REQUIRED = {"X-Amz-Algorithm", "X-Amz-Credential", "X-Amz-Signature"}
SIGV4_FIELDS = SIGV4_REQUIRED | {
    "X-Amz-Date",
    "X-Amz-Expires",
    "X-Amz-Security-Token",
    "X-Amz-SignedHeaders",
}
CANNED_FIELDS = {"Expires", "Signature", "Key-Pair-Id"}
CDN_LOG_FIELDS = {"A-userid", "sourceip"}  # Values are never logged or persisted.
CDN_RESERVED = SIGV4_FIELDS | CANNED_FIELDS | {"Policy", "Hash-Algorithm"}
S3_SELECTORS = {"versionId", "partNumber", "uploadId"}

# Only these literal project guard messages may be mapped to a public error code.
# Arbitrary exception text, URL queries and server response bodies are never recorded.
SAFE_ERROR_CODES = {
    "Exact NASA data URL without embedded credentials": "source_url_identity",
    "Regular native file": "native_file_type",
    "Exact historical source size": "historical_size",
    "Exact historical SHA-256": "historical_sha256",
    "Supported provider checksum": "checksum_algorithm",
    "Provider checksum": "provider_checksum",
    "Dedicated regular cache": "cache_directory",
    "No cache symlinks": "cache_symlink",
    "Positive expected transfer": "transfer_budget",
    "Pilot cache capacity": "cache_capacity",
    "Free disk reserve": "disk_reserve",
    "Secure signed redirect": "redirect_transport",
    "Registered NASA bucket": "cmr_bucket",
    "Plain CMR S3 identity": "cmr_object_identity",
    "One exact CMR S3 object": "cmr_object_count",
    "Same signed S3 object key": "signed_object_key",
    "Exact regional S3 bucket/key": "signed_endpoint_or_key",
    "Signed S3 request parameters": "signed_parameters",
    "Exact direct NASA data URL": "origin_response_url",
    "Exact final object response": "final_response_url",
    "Deadline before signed hop": "redirect_deadline",
    "Contained native target": "cache_target_path",
    "Retained partial requires review before retry": "retained_partial",
    "Pilot deadline before request": "request_deadline",
    "Unencoded native bytes": "response_encoding",
    "Response length": "response_length",
    "Pilot transfer deadline": "transfer_deadline",
    "Transfer exceeds historical byte bound": "transfer_size_bound",
    "Transfer disk reserve": "transfer_disk_reserve",
    "Native pair key": "native_pair_key",
    "Native swath dimensions": "native_dimensions",
    "Native fire/QA types": "native_types",
    "Native orbit identity": "native_orbit",
    "Native/CMR interval": "native_interval",
    "Native probe input closure": "input_closure",
    "Native probe readback": "result_readback",
    "Not the actual geolocation input": "native_geolocation_lineage",
    "Direct NASA data response rejected": "data_http_status",
    "CloudFront distribution endpoint": "cloudfront_endpoint",
    "Exact CloudFront CMR object": "cloudfront_object",
    "Signed CloudFront request parameters": "cloudfront_parameters",
    "Single nonempty CDN query values": "cdn_query_cardinality",
    "One supported CDN signing scheme": "cdn_signing_scheme",
    "Known CDN query fields": "cdn_query_fields",
    "CDN SigV4 parameter shape": "cdn_sigv4_shape",
    "CDN canned parameter shape": "cdn_canned_shape",
    "Bounded CDN query fields": "cdn_query_bounds",
    "No conflicting CDN reserved fields": "cdn_query_reserved",
    "Supported CloudFront hash algorithm": "cdn_hash_algorithm",
}


def safe_error_details(error):
    result = {"safe_code": SAFE_ERROR_CODES.get(str(error), "unclassified")}
    status = getattr(error, "http_status", None)
    result["http_status"] = status if type(status) is int and 100 <= status <= 599 else None
    original = getattr(error, "transfer_diagnostics", {})
    original = original if isinstance(original, dict) else {}
    diagnostics = {}
    for name in ("origin_http_status", "final_http_status"):
        value = original.get(name)
        if type(value) is int and 100 <= value <= 599:
            diagnostics[name] = value
    for name in ("expected_body_bytes", "content_length_bytes"):
        value = original.get(name)
        if type(value) is int and 0 <= value < 10**12:
            diagnostics[name] = value
    for name in (
        "signed_parameters_present",
        "final_request_equivalent",
        "cdn_sigv4_fields_present",
        "cdn_canned_fields_present",
        "cdn_single_nonempty_values",
        "cdn_query_fields_allowed",
        "cdn_extra_query_fields_present",
    ):
        value = original.get(name)
        if type(value) is bool:
            diagnostics[name] = value
    if original.get("redirect_host_kind") in {
        "earthdata_login",
        "aws",
        "cloudfront",
        "other",
        "missing",
    }:
        diagnostics["redirect_host_kind"] = original["redirect_host_kind"]
    result["transfer_diagnostics"] = diagnostics
    return result


def same_request_url(actual, expected):
    """Ignore harmless URI quoting normalization, preserve host/path/query semantics."""
    a, b = urlsplit(actual), urlsplit(expected)
    return (
        a.scheme == b.scheme == "https"
        and a.hostname == b.hostname
        and a.port in {None, 443}
        and b.port in {None, 443}
        and not a.username
        and not a.password
        and not b.username
        and not b.password
        and not a.fragment
        and not b.fragment
        and unquote(a.path) == unquote(b.path)
        and sorted(parse_qsl(a.query, keep_blank_values=True))
        == sorted(parse_qsl(b.query, keep_blank_values=True))
    )


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


def signed_s3_target(source, location):
    """Validate the exact CMR bucket/key without logging or persisting signed queries."""
    target = urlsplit(location)
    require(
        target.scheme == "https"
        and target.port in {None, 443}
        and not target.username
        and not target.password
        and not target.fragment,
        "Secure signed redirect",
    )
    expected = set()
    for link in source.get("metadata", {}).get("RelatedUrls", []):
        url = urlsplit(link["URL"])
        if link.get("Type") == "GET DATA VIA DIRECT ACCESS" and url.scheme == "s3":
            require(url.hostname in {"lp-prod-protected", "prod-lads"}, "Registered NASA bucket")
            require(not url.query and not url.fragment, "Plain CMR S3 identity")
            if url.path.rsplit("/", 1)[-1] == source["filename"]:
                expected.add((url.hostname, unquote(url.path).lstrip("/")))
    require(len(expected) == 1, "One exact CMR S3 object")
    bucket, key = expected.pop()
    host, path = target.hostname, unquote(target.path).lstrip("/")
    if host in {f"{bucket}.s3.us-west-2.amazonaws.com", f"{bucket}.s3.amazonaws.com"}:
        require(path == key, "Same signed S3 object key")
    else:
        require(
            host == "s3.us-west-2.amazonaws.com" and path == bucket + "/" + key,
            "Exact regional S3 bucket/key",
        )
    params = parse_qs(target.query, keep_blank_values=True)
    require(
        params.get("X-Amz-Algorithm") == ["AWS4-HMAC-SHA256"]
        and len(params.get("X-Amz-Credential", [])) == 1
        and len(params.get("X-Amz-Signature", [])) == 1
        and re.fullmatch(r"[a-fA-F0-9]{64}", params["X-Amz-Signature"][0]) is not None,
        "Signed S3 request parameters",
    )
    # AWS verifies the signature; local validation is an identity/destination guard.
    return location


def anonymous_session():
    import requests

    return requests.Session()


def signed_parameter_shape(location):
    """Fixed booleans only; never retain field names or private query values."""
    params = parse_qs(urlsplit(location).query, keep_blank_values=True)
    return {
        "cdn_sigv4_fields_present": SIGV4_REQUIRED <= set(params),
        "cdn_canned_fields_present": CANNED_FIELDS <= set(params),
        "cdn_single_nonempty_values": all(len(v) == 1 and bool(v[0]) for v in params.values()),
        "cdn_query_fields_allowed": bounded_provider_query(params),
        "cdn_extra_query_fields_present": bool(set(params) - CDN_RESERVED - CDN_LOG_FIELDS),
    }


def bounded_provider_query(params):
    """Keep provider parameters opaque; bound syntax/size and reject source selectors.

    CloudFront signs the base URL including provider query parameters. A local
    fixed name list cannot enumerate these. Never remove or rewrite them.
    """
    return (
        0 < len(params) <= 32
        and not (set(params) & S3_SELECTORS)
        and all(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,63}", key) for key in params)
        and sum(len(key) + sum(len(v) for v in values) for key, values in params.items()) <= 65536
        and all(
            len(value) <= 16384 and not any(ord(c) < 32 or ord(c) == 127 for c in value)
            for values in params.values()
            for value in values
        )
    )


def signed_data_target(source, location):
    """Accept S3 or NASA-issued CloudFront routes to the same full CMR bucket/key.

    This is called only on a Location returned by the exact approved NASA source.
    The second request carries no EDL credentials. CDN signatures are checked by
    CloudFront; complete historical SHA/size checks remain mandatory locally.
    """
    target = urlsplit(location)
    if not (target.hostname or "").endswith(".cloudfront.net"):
        return signed_s3_target(source, location)
    require(
        target.scheme == "https"
        and target.port in {None, 443}
        and not target.username
        and not target.password
        and not target.fragment
        and re.fullmatch(r"d[a-z0-9]{8,30}\.cloudfront\.net", target.hostname) is not None,
        "CloudFront distribution endpoint",
    )
    objects = set()
    for link in source.get("metadata", {}).get("RelatedUrls", []):
        obj = urlsplit(link["URL"])
        if link.get("Type") == "GET DATA VIA DIRECT ACCESS" and obj.scheme == "s3":
            require(obj.hostname in {"lp-prod-protected", "prod-lads"}, "Registered NASA bucket")
            require(not obj.query and not obj.fragment, "Plain CMR S3 identity")
            if obj.path.rsplit("/", 1)[-1] == source["filename"]:
                objects.add((obj.hostname, unquote(obj.path).lstrip("/")))
    require(len(objects) == 1, "One exact CMR S3 object")
    bucket, key = objects.pop()
    path = unquote(target.path)
    parts = path.lstrip("/").split("/")
    # NASA's shared CDN wraps the exact virtual-hosted S3 URL in one routing
    # component. It is not sufficient to match only the final filename.
    routed = (
        len(parts) >= 3
        and re.fullmatch(r"[A-Za-z0-9_.:-]{1,256}", parts[0]) is not None
        and parts[0] not in {".", ".."}
        and parts[1] in {f"{bucket}.s3.us-west-2.amazonaws.com", f"{bucket}.s3.amazonaws.com"}
        and "/".join(parts[2:]) == key
    )
    require(
        "\\" not in path
        and not any(p in {".", ".."} for p in parts)
        and (path == "/" + bucket + "/" + key or routed),
        "Exact CloudFront CMR object",
    )
    params = parse_qs(target.query, keep_blank_values=True)
    shape = signed_parameter_shape(location)
    require(shape["cdn_single_nonempty_values"], "Single nonempty CDN query values")
    sigv4, canned = shape["cdn_sigv4_fields_present"], shape["cdn_canned_fields_present"]
    require(sigv4 != canned, "One supported CDN signing scheme")
    reserved = SIGV4_FIELDS if sigv4 else CANNED_FIELDS | {"Hash-Algorithm"}
    require(not ((set(params) - reserved) & CDN_RESERVED), "No conflicting CDN reserved fields")
    require(shape["cdn_query_fields_allowed"], "Bounded CDN query fields")
    if sigv4:
        # TEA can wrap a SigV4-signed S3 URL in CloudFront; it is not a
        # CloudFront canned signature. Preserve the original signed query.
        require(
            params["X-Amz-Algorithm"] == ["AWS4-HMAC-SHA256"]
            and re.fullmatch(r"[a-fA-F0-9]{64}", params["X-Amz-Signature"][0]) is not None,
            "CDN SigV4 parameter shape",
        )
    else:
        require(
            params.get("Hash-Algorithm", ["SHA1"]) in (["SHA1"], ["SHA256"]),
            "Supported CloudFront hash algorithm",
        )
        require(
            params["Expires"][0].isdigit()
            and int(params["Expires"][0]) > 0
            and re.fullmatch(r"[A-Za-z0-9_~=-]{32,2048}", params["Signature"][0]) is not None
            and re.fullmatch(r"[A-Za-z0-9]{2,80}", params["Key-Pair-Id"][0]) is not None,
            "CDN canned parameter shape",
        )
    return location


@contextmanager
def data_response(session, source, deadline):
    """NASA bearer request, then one exact S3/CDN object in a credential-free session."""
    url = source_url(source)
    options = {
        "stream": True,
        "allow_redirects": False,
        "timeout": (10, 30),
        "headers": {"Accept-Encoding": "identity"},
    }
    diagnostics = {"expected_body_bytes": source["bytes"]}
    try:
        with ExitStack() as stack:
            response = stack.enter_context(session.get(url, **options))
            diagnostics["origin_http_status"] = response.status_code
            require(same_request_url(response.url, url), "Exact direct NASA data URL")
            redirected = response.status_code in {302, 303, 307, 308}
            expected_url = url
            if redirected:
                location = response.headers.get("Location", "")
                parts = urlsplit(location)
                host = parts.hostname or ""
                diagnostics["redirect_host_kind"] = (
                    "earthdata_login"
                    if host == "urs.earthdata.nasa.gov"
                    else "aws"
                    if host.endswith(".amazonaws.com")
                    else "cloudfront"
                    if host.endswith(".cloudfront.net")
                    else "other"
                    if host
                    else "missing"
                )
                parameters = parse_qs(parts.query)
                diagnostics.update(signed_parameter_shape(location))
                diagnostics["signed_parameters_present"] = all(
                    key in parameters
                    for key in ("X-Amz-Algorithm", "X-Amz-Credential", "X-Amz-Signature")
                ) or all(key in parameters for key in ("Expires", "Signature", "Key-Pair-Id"))
                expected_url = signed_data_target(source, location)
                response.close()
                require(time.monotonic() < deadline, "Deadline before signed hop")
                clean = anonymous_session()
                stack.callback(clean.close)
                clean.headers.clear()
                clean.cookies.clear()
                clean.auth = None
                clean.trust_env = False
                response = stack.enter_context(clean.get(expected_url, **options))
            diagnostics["final_http_status"] = response.status_code
            if response.status_code != 200:
                raise DataResponseError(response.status_code)
            equivalent = same_request_url(response.url, expected_url)
            diagnostics["final_request_equivalent"] = equivalent
            require(equivalent, "Exact final object response")
            length = response.headers.get("Content-Length", "")
            if length.isdigit():
                diagnostics["content_length_bytes"] = int(length)
            yield response, redirected
    except Exception as error:
        error.transfer_diagnostics = diagnostics
        raise


def transfer_one(session, source, cache, *, deadline, cache_limit_bytes, reserve_bytes):
    """A full file or a retained partial; partial bytes are never an accepted checkpoint.

    Only an exact CMR S3/CDN object redirect is accepted, using a separate credential-free
    session. Authentication and additional redirects fail closed; no version substitution.
    """
    source_url(source)
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
    # No EDL header/cookie/session is forwarded to the signed S3 URL.
    with data_response(session, source, deadline) as (response, redirected):
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
    return {
        **result,
        "reused": False,
        "network_bytes": received,
        "verified_s3_redirect": redirected
        and not urlsplit(response.url).hostname.endswith(".cloudfront.net"),
        "verified_cloudfront_redirect": redirected
        and urlsplit(response.url).hostname.endswith(".cloudfront.net"),
    }
