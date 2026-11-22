import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def audit():
    path = (
        Path(__file__).resolve().parents[1] / "scripts/quality/audit_delivery_readiness_metadata.py"
    )
    spec = importlib.util.spec_from_file_location("delivery_metadata_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row(path, day="2025-01-01"):
    return {"day": day, "kind": "features", "path": path, "sha256": "a" * 64, "bytes": "3"}


def test_inventory_classifies_closed_year_metadata_without_reading_daily_contents(
    audit, tmp_path, monkeypatch
):
    file = tmp_path / "outputs/reports/dataset/2025_day.csv"
    file.parent.mkdir(parents=True)
    file.write_bytes(b"abc")

    def no_content(*args, **kwargs):
        raise AssertionError("Daily contents must not be read")

    monkeypatch.setattr(Path, "open", no_content)
    inventory, _ = audit.inventory_index(tmp_path, [row(file.relative_to(tmp_path).as_posix())])
    assert inventory[0]["year"] == 2025 and inventory[0]["size_matches"]


def test_missing_file_is_recorded_not_silently_accepted(audit, tmp_path):
    inventory, _ = audit.inventory_index(tmp_path, [row("outputs/reports/dataset/missing.csv")])
    assert not inventory[0]["exists"] and not inventory[0]["size_matches"]


def test_duplicate_or_out_of_store_index_is_rejected(audit, tmp_path):
    entry = row("outputs/reports/dataset/day.csv")
    with pytest.raises(ValueError, match="duplicate"):
        audit.inventory_index(tmp_path, [entry, entry])
    with pytest.raises(ValueError, match="inside accepted"):
        audit.inventory_index(tmp_path, [row("../outside.csv")])
