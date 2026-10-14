"""Selected compact-table bytes and scope must remain bound to prior acceptance."""

import importlib.util
import io
import json
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/quality/materialize_observations.py"
spec = importlib.util.spec_from_file_location("observation_materialization_test", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def archive(change=None):
    area = b"grid_id,value\na,0\n"
    center = b"grid_id,value\na,1\n"
    report = {
        "day": "2018-01-01",
        "parts_sha256": "a" * 64,
        "compact_code_sha256": module.COMPACT_SHA,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "outputs_sha256": {"area.csv": module.sha(area), "centers.csv": module.sha(center)},
    }
    if change == "day":
        report["day"] = "2018-01-02"
    elif change == "gate":
        report["negative_label_permitted"] = True
    elif change == "status":
        report["daily_observation_status"] = "observed"
    elif change == "bytes":
        area = b"grid_id,value\na,99\n"
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as result:
        for name, data in (
            ("report.json", json.dumps(report).encode()),
            ("area.csv", area),
            ("centers.csv", center),
        ):
            result.writestr(name, data)
    return zipfile.ZipFile(io.BytesIO(stream.getvalue()))


def test_selected_table_hashes_and_metadata_agree():
    with archive() as source:
        area, center = module.tables(source, "2018-01-01", "", "a" * 64)
    assert area.value.tolist() == [0] and center.value.tolist() == [1]


@pytest.mark.parametrize("change", ["day", "gate", "status", "bytes"])
def test_changed_identity_policy_or_table_rejected(change):
    with archive(change) as source, pytest.raises(ValueError):
        module.tables(source, "2018-01-01", "", "a" * 64)


@pytest.mark.parametrize("months", [["2024-01"], ["2025-01"], ["2018-01", "2018-01"]])
def test_scope_rejected_before_accepted_sources_are_opened(monkeypatch, months):
    monkeypatch.setattr(module, "checked", lambda *a: pytest.fail("No source access allowed"))
    with pytest.raises(ValueError):
        module.run(months, 1, 1)
