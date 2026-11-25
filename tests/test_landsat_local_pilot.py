from datetime import UTC, datetime
from io import BytesIO

import numpy as np
import pytest

from wildfire_risk_prediction.landsat_local_pilot import BudgetHTTP, PilotStop, native_indices


def test_scale_offset_common_QA_and_saturation_zero_semantics():
    a = np.array([10000] * 5, dtype="uint16")
    b = np.array([20000] * 5, dtype="uint16")
    c = np.array([15000] * 5, dtype="uint16")
    qa = np.array([0, 64, 128, 8, 0], dtype="uint16")
    saturation = np.array([0, 0, 0, 0, 1], dtype="uint16")
    ndvi, ndmi = native_indices(a, b, c, qa, saturation)
    np.testing.assert_allclose(ndvi[:2], (0.35 - 0.075) / (0.35 + 0.075))
    np.testing.assert_allclose(ndmi[:2], (0.35 - 0.2125) / (0.35 + 0.2125))
    assert np.isnan(ndvi[2:]).all() and np.isnan(ndmi[2:]).all()


def test_negative_reflectance_and_fill_do_not_become_valid_indices():
    a = np.array([0, 1000], dtype="uint16")
    ndvi, ndmi = native_indices(a, a, a, np.zeros(2, dtype="uint16"), np.zeros(2, dtype="uint16"))
    assert np.isnan(ndvi).all() and np.isnan(ndmi).all()


def budget(folder):
    return BudgetHTTP(
        {
            "original_probe_start_utc": datetime.now(UTC).isoformat(),
            "max_body_bytes": 10,
            "max_requests": 2,
            "max_seconds": 30,
            "prior_probe_body_bytes": 0,
            "prior_probe_request_attempts": 0,
        },
        folder,
    )


class Response:
    status_code = 200

    def __init__(self, body, length=True):
        self.raw = BytesIO(body)
        self.headers = {"Content-Length": str(len(body))} if length else {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_declared_oversized_body_is_rejected_before_read(tmp_path, monkeypatch):
    http = budget(tmp_path)
    response = Response(b"x" * 11)
    monkeypatch.setattr(http.session, "request", lambda *args, **kwargs: response)
    with pytest.raises(PilotStop, match="response_exceeds_bound"):
        http.get("https://test.blob.core.windows.net/public/a.tif", role="range")
    assert response.raw.tell() == 0 and http.bytes == 0


def test_unknown_length_never_reads_beyond_remaining_budget(tmp_path, monkeypatch):
    http = budget(tmp_path)
    response = Response(b"x" * 30, length=False)
    monkeypatch.setattr(http.session, "request", lambda *args, **kwargs: response)
    with pytest.raises(PilotStop, match="bounded_response_eof_unverified"):
        http.get("https://test.blob.core.windows.net/public/a.tif", role="range")
    assert response.raw.tell() == http.bytes == 10


def test_access_query_never_appears_in_checkpoint(tmp_path, monkeypatch):
    http = budget(tmp_path)
    monkeypatch.setattr(http.session, "request", lambda *args, **kwargs: Response(b"abc"))
    data, _ = http.get(
        "https://test.blob.core.windows.net/public/a.tif?sig=never_persist_this", role="range"
    )
    assert data == b"abc"
    assert "never_persist_this" not in (tmp_path / "network_checkpoint.json").read_text()
