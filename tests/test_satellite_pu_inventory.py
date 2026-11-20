import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def inventory(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "satellite_inventory_test", folder / "prepare_satellite_pu_inventory.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate():
    return {
        "grid_id": "A",
        "prediction_timestamp_utc": "2021-06-01T00:00:00+00:00",
        "target": "",
        "event_identity_accepted": "False",
        "event_membership_complete": "False",
        "positive_label_permitted": "False",
        "negative_label_permitted": "False",
        "scenarios_with_candidate": "9",
    }


def test_later_roles_require_only_timestamp_and_boundary_is_preserved(inventory):
    kept, boundary, later = inventory.fit_units(
        [
            candidate(),
            {"prediction_timestamp_utc": "2023-06-01T00:00:00+00:00"},
            {"prediction_timestamp_utc": "2022-12-31T00:00:00+00:00", "grid_id": "B"},
        ]
    )
    assert len(kept) == len(boundary) == later == 1
    assert kept[0]["target"] is None and kept[0]["weak_positive_membership"] is None


def test_U_with_and_without_context_stay_unknown_without_row_loss(inventory):
    rows = [
        {
            "grid_id": k,
            "prediction_timestamp_utc": "2021-06-01T00:00:00+00:00",
            "target": "",
            "daily_observation_status": "unknown",
        }
        for k in ("A", "B")
    ]
    result = inventory.u_context(rows, [candidate()])
    assert len(result) == 2
    assert [r["catalogue_first_candidate_context_present"] for r in result] == [True, False]
    assert all(
        r["target"] == "" and not r["context_is_fire_label"] and not r["candidate_overlap_removed"]
        for r in result
    )


@pytest.mark.parametrize("kind", ["duplicate", "label", "nonmidnight"])
def test_no_duplicate_or_admission_or_time_repair(inventory, kind):
    row = candidate()
    if kind == "duplicate":
        rows = [row, dict(row)]
    else:
        row["target" if kind == "label" else "prediction_timestamp_utc"] = (
            "1" if kind == "label" else "2021-06-01T01:00:00+00:00"
        )
        rows = [row]
    with pytest.raises(ValueError):
        inventory.fit_units(rows)
