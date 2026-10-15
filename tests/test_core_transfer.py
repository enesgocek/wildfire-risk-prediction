"""Fail closed on bad bytes, low disk, partial writes, redirects and runner timeout."""

import hashlib
import importlib.util
import json
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode, urlunsplit

import pytest

from wildfire_risk_prediction import core_transfer as transfer


def source(data=b"native"):
    return {
        "source_id": "SNPP:2021046.0100|fire",
        "source_day": "2021-02-15",
        "sample_id": "SNPP:2021046.0100",
        "role": "fire",
        "filename": "VNP14IMG.A2021046.0100.002.2024000000000.nc",
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "url": "https://data.lpdaac.earthdatacloud.nasa.gov/path/VNP14IMG.A2021046.0100.002.2024000000000.nc",
        "provider_checksum": {"Algorithm": "MD5", "Value": hashlib.md5(data).hexdigest()},
    }


class Response:
    def __init__(self, record, chunks=(b"na", b"tive"), status=200, headers=None):
        self.status_code, self.url = status, record["url"]
        self.headers = {} if headers is None else headers
        self.chunks = chunks

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def close(self):
        pass

    def iter_content(self, chunk_size):
        yield from self.chunks


class Session:
    def __init__(self, response):
        self.response, self.calls = response, []
        self.headers, self.cookies = {"Authorization": "synthetic"}, {"edl": "synthetic"}
        self.auth, self.trust_env = "synthetic", True

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response

    def close(self):
        pass


def run(record, cache, response=None, **kwargs):
    session = Session(response or Response(record))
    result = transfer.transfer_one(
        session,
        record,
        cache,
        deadline=kwargs.get("deadline", time.monotonic() + 30),
        cache_limit_bytes=kwargs.get("limit", 10000),
        reserve_bytes=kwargs.get("reserve", 0),
    )
    return session, result


def test_success_writes_only_verified_bytes_and_reuses_without_request(tmp_path):
    r = source()
    session, a = run(r, tmp_path)
    assert a["network_bytes"] == 6 and a["provider_checksum_verified"]
    assert not a["reused"] and (tmp_path / r["filename"]).read_bytes() == b"native"
    assert session.calls[0][1]["allow_redirects"] is False
    assert session.calls[0][1]["headers"] == {"Accept-Encoding": "identity"}
    second, b = run(r, tmp_path)
    assert b["reused"] and b["network_bytes"] == 0 and not second.calls


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/file.nc",
        "http://data.lpdaac.earthdatacloud.nasa.gov/file.nc",
        "https://data.lpdaac.earthdatacloud.nasa.gov:8443/file.nc",
        urlunsplit(
            ("https", "user:password@data.lpdaac.earthdatacloud.nasa.gov", "/file.nc", "", "")
        ),
    ],
)
def test_unapproved_url_never_reaches_session(tmp_path, url):
    r = source()
    r["url"] = url
    s = Session(Response(r))
    with pytest.raises(ValueError):
        transfer.transfer_one(
            s, r, tmp_path, deadline=time.monotonic() + 1, cache_limit_bytes=100, reserve_bytes=0
        )
    assert not s.calls


def test_query_token_is_rejected_before_transfer():
    r = source()
    r["url"] += "?signature=dummy"
    with pytest.raises(ValueError):
        transfer.source_url(r)


@pytest.mark.parametrize("chunks", [(b"short",), (b"native!",), (b"wrong!",)])
def test_truncated_oversized_or_corrupted_bytes_remain_partial(tmp_path, chunks):
    r = source()
    with pytest.raises(ValueError):
        run(r, tmp_path, Response(r, chunks=chunks))
    assert not (tmp_path / r["filename"]).exists()
    assert (tmp_path / (r["filename"] + ".part")).exists()


def test_existing_same_size_corruption_is_not_redownloaded_or_overwritten(tmp_path):
    r = source()
    p = tmp_path / r["filename"]
    p.write_bytes(b"wrong!")
    with pytest.raises(ValueError):
        run(r, tmp_path)
    assert p.read_bytes() == b"wrong!"


def test_partial_is_preserved_and_never_counted_as_reusable(tmp_path):
    r = source()
    p = tmp_path / (r["filename"] + ".part")
    p.write_bytes(b"na")
    with pytest.raises(ValueError):
        run(r, tmp_path)
    assert p.read_bytes() == b"na"


@pytest.mark.parametrize("status", [302, 401, 403, 404, 500])
def test_auth_redirect_and_http_failures_write_no_native_file(tmp_path, status):
    r = source()
    with pytest.raises(ValueError):
        run(r, tmp_path, Response(r, status=status))
    assert not list(tmp_path.iterdir())


def test_header_length_mismatch_fails_before_writing(tmp_path):
    r = source()
    with pytest.raises(ValueError):
        run(r, tmp_path, Response(r, headers={"Content-Length": "9"}))
    assert not list(tmp_path.iterdir())


def test_cache_limit_and_disk_reserve_do_not_start_transfer(tmp_path, monkeypatch):
    r = source()
    with pytest.raises(ValueError):
        run(r, tmp_path, limit=5)
    monkeypatch.setattr(transfer.shutil, "disk_usage", lambda _: SimpleNamespace(free=10))
    with pytest.raises(ValueError):
        run(r, tmp_path, reserve=5)
    assert not list(tmp_path.iterdir())


def test_expired_deadline_does_not_start_transfer(tmp_path):
    with pytest.raises(ValueError):
        run(source(), tmp_path, deadline=time.monotonic() - 1)
    assert not list(tmp_path.iterdir())


def test_provider_checksum_conflict_fails_even_if_historical_sha_matches(tmp_path):
    r = source()
    r["provider_checksum"]["Value"] = "0" * 32
    with pytest.raises(ValueError):
        run(r, tmp_path)
    assert not (tmp_path / r["filename"]).exists()


def runner():
    p = Path(__file__).resolve().parents[1] / "scripts/firms/run_observation_core_pair.py"
    spec = importlib.util.spec_from_file_location("bounded_core_runner_test", p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parent_timeout_uses_hard_cap_and_keeps_token_out_of_arguments_and_files(
    tmp_path, monkeypatch
):
    module = runner()
    monkeypatch.setattr(module.logging, "disable", lambda *_: None)
    monkeypatch.setattr(module, "OUTPUT", tmp_path)
    monkeypatch.setattr(
        module,
        "load_plan",
        lambda _: ({"hard_runtime_seconds": 900}, {"sample_id": "fixed", "bytes": 6}),
    )
    monkeypatch.setattr(module, "digest", lambda _: "a" * 64)
    monkeypatch.setenv("EARTHDATA_TOKEN", "synthetic-test-only")

    def timeout(command, **kwargs):
        assert kwargs["timeout"] == 900 and kwargs["stdout"] == subprocess.DEVNULL
        assert "synthetic-test-only" not in " ".join(command)
        assert "EARTHDATA_PASSWORD" not in kwargs["env"]
        raise subprocess.TimeoutExpired(command, 900)

    monkeypatch.setattr(module.subprocess, "run", timeout)
    assert module.run(tmp_path / "plan.json", False) == 1
    path = next(tmp_path.glob("*/launcher_receipt.json"))
    assert json.loads(path.read_text())["status"] == "hard_timeout_partial_and_lock_retained"
    assert "synthetic-test-only" not in path.read_text()


def test_private_prompt_refuses_non_interactive_input(tmp_path, monkeypatch):
    module = runner()
    monkeypatch.setattr(module.logging, "disable", lambda *_: None)
    monkeypatch.setattr(module, "load_plan", lambda _: ({}, {"sample_id": "fixed", "bytes": 6}))
    monkeypatch.setattr(module.sys.stdin, "isatty", lambda: False)
    with pytest.raises(ValueError, match="interactive terminal"):
        module.run(tmp_path / "plan.json", True)


def redirected_source():
    r = source()
    r["metadata"] = {
        "RelatedUrls": [
            {
                "Type": "GET DATA VIA DIRECT ACCESS",
                "URL": "s3://lp-prod-protected/product/" + r["filename"],
            }
        ]
    }
    return r


def signed_url(r, host="lp-prod-protected.s3.us-west-2.amazonaws.com", key=None):
    params = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": "synthetic",
        "X-Amz-Signature": "0" * 64,
    }
    return urlunsplit(
        ("https", host, "/" + (key or "product/" + r["filename"]), urlencode(params), "")
    )


@pytest.mark.parametrize("status", [302, 303, 307, 308])
def test_exact_signed_s3_redirect_uses_separate_empty_session(tmp_path, monkeypatch, status):
    r = redirected_source()
    target = signed_url(r)
    origin = Session(Response(r, status=status, headers={"Location": target}))
    final = Response(r)
    final.url = target
    clean = Session(final)
    monkeypatch.setattr(transfer, "anonymous_session", lambda: clean)
    result = transfer.transfer_one(
        origin,
        r,
        tmp_path,
        deadline=time.monotonic() + 30,
        cache_limit_bytes=10000,
        reserve_bytes=0,
    )
    assert result["verified_s3_redirect"] and result["network_bytes"] == 6
    assert len(origin.calls) == len(clean.calls) == 1
    assert clean.auth is None and clean.trust_env is False
    assert not clean.headers and not clean.cookies
    assert clean.calls[0][1]["allow_redirects"] is False
    assert "Authorization" not in clean.calls[0][1]["headers"]
    assert "Cookie" not in clean.calls[0][1]["headers"]


@pytest.mark.parametrize(
    "host,key",
    [
        ("lp-prod-protected.s3.amazonaws.com", None),
        ("s3.us-west-2.amazonaws.com", "lp-prod-protected/product/" + source()["filename"]),
    ],
)
def test_same_registered_object_in_supported_s3_endpoint_forms(host, key):
    r = redirected_source()
    u = signed_url(r, host, key)
    assert transfer.signed_s3_target(r, u) == u


@pytest.mark.parametrize(
    "kind",
    [
        "wrong_bucket",
        "wrong_key",
        "non_s3_host",
        "missing_signature",
        "http",
        "login_redirect",
        "no_cmr_object",
        "extra_cmr_object",
    ],
)
def test_unregistered_redirect_never_starts_second_request(tmp_path, monkeypatch, kind):
    r = redirected_source()
    target = signed_url(r)
    if kind == "wrong_bucket":
        target = signed_url(r, "other-bucket.s3.us-west-2.amazonaws.com")
    if kind == "wrong_key":
        target = signed_url(r, key="different/" + r["filename"])
    if kind == "non_s3_host":
        target = signed_url(r, "example.com")
    if kind == "missing_signature":
        target = target.split("?")[0]
    if kind == "http":
        target = target.replace("https:", "http:")
    if kind == "login_redirect":
        target = "https://urs.earthdata.nasa.gov/oauth/authorize"
    if kind == "no_cmr_object":
        r["metadata"] = {}
    if kind == "extra_cmr_object":
        r["metadata"]["RelatedUrls"].append(
            {"Type": "GET DATA VIA DIRECT ACCESS", "URL": "s3://prod-lads/other/" + r["filename"]}
        )
    origin = Session(Response(r, status=303, headers={"Location": target}))

    def forbidden():
        raise AssertionError("Must not create destination session")

    monkeypatch.setattr(transfer, "anonymous_session", forbidden)
    with pytest.raises(ValueError):
        transfer.transfer_one(
            origin,
            r,
            tmp_path,
            deadline=time.monotonic() + 30,
            cache_limit_bytes=10000,
            reserve_bytes=0,
        )
    assert len(origin.calls) == 1 and not list(tmp_path.iterdir())


def test_signed_destination_cannot_redirect_again(tmp_path, monkeypatch):
    r = redirected_source()
    target = signed_url(r)
    final = Response(r, status=303)
    final.url = target
    monkeypatch.setattr(transfer, "anonymous_session", lambda: Session(final))
    with pytest.raises(transfer.DataResponseError) as error:
        run(r, tmp_path, Response(r, status=303, headers={"Location": target}))
    assert error.value.http_status == 303 and not list(tmp_path.iterdir())


def test_safe_error_codes_never_copy_arbitrary_exception_text():
    assert (
        transfer.safe_error_details(ValueError("Response length"))["safe_code"] == "response_length"
    )
    error = ValueError("synthetic-private-value")
    error.transfer_diagnostics = {
        "Location": "synthetic-private-value",
        "origin_http_status": 303,
        "redirect_host_kind": "synthetic-private-value",
        "expected_body_bytes": 6,
        "signed_parameters_present": True,
        "Authorization": "synthetic-private-value",
    }
    result = transfer.safe_error_details(error)
    assert result["safe_code"] == "unclassified"
    assert result["transfer_diagnostics"] == {
        "origin_http_status": 303,
        "expected_body_bytes": 6,
        "signed_parameters_present": True,
    }
    assert "synthetic-private-value" not in json.dumps(result)


def test_request_equivalence_allows_quoting_not_new_object_or_signature():
    r = redirected_source()
    original = signed_url(r) + "&audit=%7E"
    assert transfer.same_request_url(original.replace("%7E", "~"), original)
    assert not transfer.same_request_url(original.replace("product/", "other/"), original)
    assert not transfer.same_request_url(
        original.replace("X-Amz-Signature=0", "X-Amz-Signature=1"), original
    )
    assert not transfer.same_request_url(original.replace(".com/", ".com:0/"), original)


def test_signed_response_normalization_preserves_hash_and_identity_checks(tmp_path, monkeypatch):
    r = redirected_source()
    target = signed_url(r) + "&audit=%7E"
    final = Response(r)
    final.url = target.replace("%7E", "~")
    monkeypatch.setattr(transfer, "anonymous_session", lambda: Session(final))
    _, result = run(r, tmp_path, Response(r, status=303, headers={"Location": target}))
    assert result["sha256"] == r["sha256"] and result["verified_s3_redirect"]


def test_redirect_rejection_records_only_safe_structure(tmp_path):
    r = redirected_source()
    target = signed_url(r, key="wrong/" + r["filename"])
    with pytest.raises(ValueError) as error:
        run(r, tmp_path, Response(r, status=303, headers={"Location": target}))
    details = transfer.safe_error_details(error.value)
    assert details["safe_code"] == "signed_object_key"
    assert details["transfer_diagnostics"]["origin_http_status"] == 303
    assert details["transfer_diagnostics"]["redirect_host_kind"] == "aws"
    assert "X-Amz" not in json.dumps(details) and "synthetic" not in json.dumps(details)


def test_response_size_rejection_is_distinguishable_without_url_or_token(tmp_path):
    r = source()
    with pytest.raises(ValueError) as error:
        run(r, tmp_path, Response(r, headers={"Content-Length": "9"}))
    details = transfer.safe_error_details(error.value)
    assert details["safe_code"] == "response_length"
    assert details["transfer_diagnostics"]["content_length_bytes"] == 9
    assert details["transfer_diagnostics"]["expected_body_bytes"] == 6


def test_parent_shows_only_allowlisted_failure_code(tmp_path, monkeypatch, capsys):
    module = runner()
    monkeypatch.setattr(module.logging, "disable", lambda *_: None)
    monkeypatch.setattr(module, "OUTPUT", tmp_path)
    monkeypatch.setattr(
        module,
        "load_plan",
        lambda _: ({"hard_runtime_seconds": 900}, {"sample_id": "fixed", "bytes": 6}),
    )
    monkeypatch.setattr(module, "digest", lambda _: "a" * 64)
    monkeypatch.setenv("EARTHDATA_TOKEN", "synthetic-test-only")

    def failed(command, **kwargs):
        (Path(command[-1]) / "failure.json").write_text(
            json.dumps({"safe_code": "synthetic-private-value"}), encoding="utf-8"
        )
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(module.subprocess, "run", failed)
    assert module.run(tmp_path / "plan.json", False) == 1
    output = capsys.readouterr().out
    assert "Kontrol kodu: unclassified" in output and "synthetic-private-value" not in output


def test_latest_plan_chooses_completed_output_and_still_requires_separate_validation(
    tmp_path, monkeypatch
):
    module = runner()
    monkeypatch.setattr(module, "PLAN_ROOT", tmp_path)
    with pytest.raises(ValueError):
        module.latest_plan()
    for folder in ("20260101_a", "20260102_b", "20260103_incomplete"):
        p = tmp_path / folder
        p.mkdir()
        (p / "native_plan.json").write_text("{}")
        if "incomplete" not in folder:
            (p / "completion_readback.json").write_text("{}")
    assert module.latest_plan() == tmp_path / "20260102_b/native_plan.json"
    # A completion filename does not grant admission to a malformed or stale plan.
    with pytest.raises((ValueError, FileNotFoundError)):
        module.load_plan(module.latest_plan())


def cloudfront_url(record):
    path = "/route/lp-prod-protected.s3.us-west-2.amazonaws.com/product/" + record["filename"]
    return urlunsplit(
        (
            "https",
            "d123456789abc.cloudfront.net",
            path,
            urlencode(
                {
                    "Expires": "2000000000",
                    "Signature": "a" * 64,
                    "Key-Pair-Id": "K123456789ABC",
                    "A-userid": "synthetic-private-account",
                }
            ),
            "",
        )
    )


def test_exact_cloudfront_object_uses_empty_second_session_and_full_byte_checks(
    tmp_path, monkeypatch
):
    r = redirected_source()
    target = cloudfront_url(r)
    final = Response(r)
    final.url = target
    clean = Session(final)
    monkeypatch.setattr(transfer, "anonymous_session", lambda: clean)
    _, result = run(r, tmp_path, Response(r, status=303, headers={"Location": target}))
    assert result["verified_cloudfront_redirect"] and not result["verified_s3_redirect"]
    assert result["sha256"] == r["sha256"] and result["network_bytes"] == 6
    assert not clean.headers and not clean.cookies and clean.auth is None and not clean.trust_env
    assert clean.calls[0][1]["allow_redirects"] is False
    assert "synthetic-private" not in json.dumps(result)


@pytest.mark.parametrize(
    "change",
    [
        lambda u: u.replace("https:", "http:"),
        lambda u: u.replace(".cloudfront.net", ".cloudfront.net.attacker.example"),
        lambda u: u.replace("/product/", "/other/"),
        lambda u: u.replace("lp-prod-protected.s3", "prod-lads.s3"),
        lambda u: u.replace("/route/", "/../"),
        lambda u: u.replace("Signature=", "unexpected="),
        lambda u: u + "&Signature=" + "b" * 64,
        lambda u: u + "&versionId=unexpected",
    ],
)
def test_cloudfront_rejects_changed_host_full_key_bucket_route_and_signature(change):
    r = redirected_source()
    with pytest.raises(ValueError):
        transfer.signed_data_target(r, change(cloudfront_url(r)))


def test_cloudfront_same_filename_with_wrong_full_key_cannot_pass():
    r = redirected_source()
    with pytest.raises(ValueError, match="CMR object"):
        transfer.signed_data_target(r, cloudfront_url(r).replace("/product/", "/other/product/"))


def test_cloudfront_second_redirect_is_never_followed(tmp_path, monkeypatch):
    r = redirected_source()
    target = cloudfront_url(r)
    final = Response(r, status=302, headers={"Location": "https://synthetic-private.example"})
    final.url = target
    clean = Session(final)
    monkeypatch.setattr(transfer, "anonymous_session", lambda: clean)
    with pytest.raises(transfer.DataResponseError):
        run(r, tmp_path, Response(r, status=303, headers={"Location": target}))
    assert len(clean.calls) == 1 and not list(tmp_path.iterdir())


def cloudfront_sigv4_url(record):
    path = "/s3-route/lp-prod-protected.s3.us-west-2.amazonaws.com/product/" + record["filename"]
    return urlunsplit(
        (
            "https",
            "d123456789abc.cloudfront.net",
            path,
            urlencode(
                {
                    "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
                    "X-Amz-Credential": "synthetic-private-credential",
                    "X-Amz-Signature": "b" * 64,
                    "X-Amz-Date": "20261015T000000Z",
                    "X-Amz-Expires": "3600",
                    "X-Amz-Security-Token": "synthetic-private-token",
                    "X-Amz-SignedHeaders": "host",
                    "A-userid": "synthetic-private-account",
                }
            ),
            "",
        )
    )


def test_tea_cloudfront_wrapped_sigv4_download_preserves_full_identity(tmp_path, monkeypatch):
    r = redirected_source()
    target = cloudfront_sigv4_url(r)
    final = Response(r)
    final.url = target
    clean = Session(final)
    monkeypatch.setattr(transfer, "anonymous_session", lambda: clean)
    _, result = run(r, tmp_path, Response(r, status=303, headers={"Location": target}))
    assert result["verified_cloudfront_redirect"] and result["sha256"] == r["sha256"]
    assert not clean.headers and not clean.cookies and clean.auth is None and not clean.trust_env
    assert "synthetic-private" not in json.dumps(result)


@pytest.mark.parametrize("factory", [cloudfront_url, cloudfront_sigv4_url])
def test_documented_cdn_logging_fields_are_accepted_without_becoming_identity(factory):
    r = redirected_source()
    target = factory(r) + "&sourceip=192.0.2.123"
    assert transfer.signed_data_target(r, target) == target
    with pytest.raises(ValueError, match="CMR object"):
        transfer.signed_data_target(r, target.replace("/product/", "/different/"))


@pytest.mark.parametrize("factory", [cloudfront_url, cloudfront_sigv4_url])
def test_duplicate_cdn_signature_is_rejected_in_both_schemes(factory):
    r = redirected_source()
    target = factory(r)
    key = "X-Amz-Signature" if factory == cloudfront_sigv4_url else "Signature"
    with pytest.raises(ValueError, match="Single nonempty"):
        transfer.signed_data_target(r, target + "&" + key + "=" + "c" * 64)


@pytest.mark.parametrize(
    "change",
    [
        lambda u: u.replace("AWS4-HMAC-SHA256", "unsupported"),
        lambda u: u.replace("X-Amz-Signature=" + "b" * 64, "X-Amz-Signature=malformed"),
        lambda u: u + "&Expires=2000000000&Signature=" + "a" * 64 + "&Key-Pair-Id=K123",
        lambda u: u + "&versionId=synthetic-private",
        lambda u: u.replace("X-Amz-Credential=synthetic-private-credential", "X-Amz-Credential="),
    ],
)
def test_wrapped_sigv4_rejects_invalid_ambiguous_or_unrecognized_query(change):
    r = redirected_source()
    with pytest.raises(ValueError):
        transfer.signed_data_target(r, change(cloudfront_sigv4_url(r)))


def test_parameter_shape_diagnostics_distinguish_schemes_without_values(tmp_path):
    r = redirected_source()
    target = cloudfront_sigv4_url(r) + "&versionId=synthetic-private"
    with pytest.raises(ValueError) as error:
        run(r, tmp_path, Response(r, status=303, headers={"Location": target}))
    result = transfer.safe_error_details(error.value)
    assert result["safe_code"] == "cdn_query_bounds"
    assert result["transfer_diagnostics"]["cdn_sigv4_fields_present"] is True
    assert result["transfer_diagnostics"]["cdn_canned_fields_present"] is False
    assert result["transfer_diagnostics"]["cdn_query_fields_allowed"] is False
    assert "synthetic-private" not in json.dumps(result) and not list(tmp_path.iterdir())


@pytest.mark.parametrize("factory", [cloudfront_url, cloudfront_sigv4_url])
def test_provider_specific_signed_query_is_preserved_but_never_reported(
    tmp_path, monkeypatch, factory
):
    r = redirected_source()
    target = factory(r) + "&provider-context=synthetic-private-value"
    assert transfer.signed_data_target(r, target) == target
    final = Response(r)
    final.url = target
    clean = Session(final)
    monkeypatch.setattr(transfer, "anonymous_session", lambda: clean)
    _, result = run(r, tmp_path, Response(r, status=303, headers={"Location": target}))
    assert clean.calls[0][0] == target and result["sha256"] == r["sha256"]
    assert "provider-context" not in json.dumps(result) and "synthetic-private" not in json.dumps(
        result
    )


@pytest.mark.parametrize("algorithm", ["SHA1", "SHA256"])
def test_documented_optional_cloudfront_hash_algorithm(algorithm):
    r = redirected_source()
    target = cloudfront_url(r) + "&Hash-Algorithm=" + algorithm
    assert transfer.signed_data_target(r, target) == target


@pytest.mark.parametrize(
    "extra",
    [
        "&Hash-Algorithm=unsupported",
        "&Policy=synthetic-policy",
        "&versionId=other-version",
        "&partNumber=1",
        "&uploadId=other",
        "&provider-context=one&provider-context=two",
        "&provider-context=%00private",
        "&bad%20key=private",
        "&provider-context=" + "a" * 16385,
    ],
)
def test_provider_query_extension_keeps_auth_identity_and_bounds(extra):
    r = redirected_source()
    with pytest.raises(ValueError):
        transfer.signed_data_target(r, cloudfront_url(r) + extra)
