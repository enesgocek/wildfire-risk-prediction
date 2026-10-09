"""Reject sealed/invalid periods before file access; never overwrite accepted reports."""

import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/quality/verify_vegetation_month.py"
SPEC = importlib.util.spec_from_file_location("month_readback", PATH)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


@pytest.mark.parametrize("month", ["2025-01", "2024-08", "2017-12", "2018-8", "../../.env"])
def test_guard_precedes_any_source_file_access(month, monkeypatch):
    def forbidden_read(*args, **kwargs):
        raise AssertionError("No file access before scope validation")

    monkeypatch.setattr(Path, "read_text", forbidden_read)
    with pytest.raises(ValueError):
        checker.verify(month)


def test_changed_accepted_report_is_never_overwritten(tmp_path):
    path = tmp_path / "accepted.json"
    checker.write_report(path, {"status": "passed"})
    before = path.read_bytes()
    checker.write_report(path, {"status": "passed"})
    with pytest.raises(ValueError, match="Accepted report retained"):
        checker.write_report(path, {"status": "different"})
    assert path.read_bytes() == before
