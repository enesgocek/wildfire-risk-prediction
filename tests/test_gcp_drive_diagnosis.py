"""Regression: no arbitrary error text, token, JSON or URL enters diagnostics."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "drive_diagnostic_test",
    Path(__file__).resolve().parents[1] / "scripts/cloud/diagnose_gcp_drive_proof.py",
)
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 503])
def test_http_status_without_response_body(status):
    assert (
        doctor.safe_error(RuntimeError(f"Drive HTTP {status}; no secrets logged"))
        == f"GOOGLE_HTTP_{status}"
    )


@pytest.mark.parametrize(
    "value",
    [
        "refresh_token=secret",
        '{"access_token":"secret"}',
        "Drive HTTP 401; secret",
        "https://host/?code=secret",
    ],
)
def test_arbitrary_sensitive_error_text_not_logged(value, capsys):
    def broken():
        raise RuntimeError(value)

    assert doctor.stage("oauth_refresh", broken) == (False, None)
    output = capsys.readouterr().out
    assert output == "FAIL oauth_refresh: RuntimeError\n"
    assert "secret" not in output


def test_redirect_has_specific_safe_code():
    assert doctor.safe_error(RuntimeError("Drive redirect refused")) == "REDIRECT_REFUSED"


def test_only_literal_checked_code_labels_can_be_reported():
    doctor.add_safe_check_messages(
        "require(ok, 'Static validation label')\nrequire(ok, f'Secret {token}')"
    )
    assert (
        doctor.safe_error(ValueError("Static validation label"))
        == "CHECK_FAILED: Static validation label"
    )
    assert doctor.safe_error(ValueError("Secret confidential")) == "ValueError"
