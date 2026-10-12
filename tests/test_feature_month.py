"""Full calendar acceptance, held-out isolation and candidate-only storage boundaries."""

import json

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_month as month
from wildfire_risk_prediction import feature_partition as parts


def day_frames(day):
    features = pd.DataFrame(
        {"grid_id": ["g2", "g1"], "prediction_timestamp_utc": [day + "T00:00:00+00:00"] * 2}
    )
    for field in join.feature_names():
        features[field] = [np.nan, 0.12345678901234568]
    qa = features[join.KEYS].copy().iloc[::-1].reset_index(drop=True)
    for field in parts.provenance_columns()[len(join.KEYS) :]:
        qa[field] = np.nan
    qa["operational_eligible"] = False
    qa["habitat_eligibility_decided"] = False
    qa["usage"] = "retrospective_candidate_only"
    qa["join_version"] = join.VERSION
    return day, features, qa


def rewrite(path, edit):
    value = json.loads(path.read_bytes())
    edit(value)
    data = json.dumps(value).encode()
    path.write_bytes(data)
    return parts.digest(data)


@pytest.fixture
def complete(tmp_path):
    folder = tmp_path / "month"
    digest = month.write_month(
        folder, (day_frames(d) for d in month.calendar_days("2020-02")), ["g1", "g2"], "2020-02"
    )
    return folder, digest


@pytest.mark.parametrize("value,count", [("2018-02", 28), ("2020-02", 29), ("2023-12", 31)])
def test_real_calendar_includes_leap_and_period_end(value, count):
    days = month.calendar_days(value)
    assert len(days) == count and days[-1] == f"{value}-{count}"


@pytest.mark.parametrize("value", ["2017-12", "2024-01", "2025-01", "2018-13", "2018-1"])
def test_scope_rejected_before_source_or_destination_access(tmp_path, value):
    def forbidden():
        raise AssertionError("Source iterator must remain unread")
        yield

    with pytest.raises(ValueError):
        month.write_month(tmp_path / "uncreated", forbidden(), ["g1"], value)
    assert not (tmp_path / "uncreated").exists()


def test_complete_leap_month_roundtrip_keeps_missing_values_and_flags(complete):
    folder, digest = complete
    rows = list(month.iter_month(folder, expected_manifest_sha256=digest, grid_ids=["g2", "g1"]))
    assert len(rows) == 29 and rows[-1][0] == "2020-02-29"
    for _, features, qa in rows:
        assert features.grid_id.tolist() == qa.grid_id.tolist() == ["g1", "g2"]
        assert features.iloc[1][join.feature_names()].isna().all()
        assert features.iloc[0][join.feature_names()[0]] == 0.12345678901234568
    manifest = json.loads((folder / "month_manifest.json").read_bytes())
    assert manifest["rows"] == 58
    assert manifest["daily_observation_status"] == "unknown"
    assert all(manifest[f] is False for f in month.FALSE_FLAGS)


@pytest.mark.parametrize("change", ["missing", "extra", "duplicate", "out_of_order"])
def test_incomplete_or_repeated_calendar_never_publishes_month(tmp_path, change):
    days = month.calendar_days("2018-02")
    if change == "missing":
        days.pop()
    elif change == "extra":
        days.append("2018-03-01")
    elif change == "duplicate":
        days.insert(1, days[0])
    else:
        days[0], days[1] = days[1], days[0]
    folder = tmp_path / "incomplete"
    with pytest.raises(ValueError, match="calendar"):
        month.write_month(folder, (day_frames(d) for d in days), ["g1", "g2"], "2018-02")
    assert not (folder / "month_manifest.json").exists()


def test_existing_output_and_targets_rejected(tmp_path, complete):
    with pytest.raises(FileExistsError):
        month.write_month(complete[0], [], ["g1", "g2"], "2020-02")
    day, features, qa = day_frames("2018-02-01")
    features["target"] = 0
    folder = tmp_path / "target"
    with pytest.raises(ValueError, match="allowlist"):
        month.write_month(folder, [(day, features, qa)], ["g1", "g2"], "2018-02")
    assert not (folder / "month_manifest.json").exists()


@pytest.mark.parametrize("change", ["held_out", "missing_day", "acceptance", "parts_missing"])
def test_manifest_checks_precede_all_csv_access(complete, monkeypatch, change):
    folder, _ = complete
    if change == "parts_missing":
        part_digest = rewrite(folder / "parts/manifest.json", lambda m: m["days"].pop())

    def edit(m):
        if change == "parts_missing":
            m.update(parts_manifest_sha256=part_digest)
        elif change == "held_out":
            m.update(month="2025-02")
        elif change == "missing_day":
            m["days"].pop()
        else:
            m.update(negative_label_permitted=True)

    digest = rewrite(folder / "month_manifest.json", edit)

    def forbidden(*args, **kwargs):
        raise AssertionError("CSV read before calendar/scope check")

    monkeypatch.setattr(parts, "parse_csv", forbidden)
    with pytest.raises(ValueError):
        list(month.iter_month(folder, expected_manifest_sha256=digest, grid_ids=["g1", "g2"]))


def test_wrong_hash_inventory_and_corrupt_data_rejected(complete):
    folder, digest = complete
    with pytest.raises(ValueError, match="identity"):
        list(month.iter_month(folder, expected_manifest_sha256="0" * 64, grid_ids=["g1", "g2"]))
    with pytest.raises(ValueError, match="inventory"):
        list(month.iter_month(folder, expected_manifest_sha256=digest, grid_ids=["g1", "other"]))
    path = folder / "parts/2020-02/2020-02-01_features.csv"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="content mismatch"):
        list(month.iter_month(folder, expected_manifest_sha256=digest, grid_ids=["g1", "g2"]))
