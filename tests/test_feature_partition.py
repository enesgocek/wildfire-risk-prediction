"""Storage corruption, sparse coverage, held-out scope and key alignment boundaries."""

import json

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_partition as store


def sample(day="2018-08-01"):
    features = pd.DataFrame(
        {"grid_id": ["g2", "g1"], "prediction_timestamp_utc": [day + "T00:00:00+00:00"] * 2}
    )
    for field in join.feature_names():
        features[field] = [np.nan, 0.12345678901234568]
    provenance = features[join.KEYS].copy().iloc[::-1].reset_index(drop=True)
    for field in store.provenance_columns()[len(join.KEYS) :]:
        provenance[field] = np.nan
    provenance["operational_eligible"] = False
    provenance["habitat_eligibility_decided"] = False
    provenance["usage"] = "retrospective_candidate_only"
    provenance["join_version"] = join.VERSION
    return day, features, provenance


def rewritten_manifest(folder, edit):
    path = folder / "manifest.json"
    manifest = json.loads(path.read_bytes())
    edit(manifest)
    data = json.dumps(manifest).encode()
    path.write_bytes(data)
    return store.digest(data)


def test_sparse_roundtrip_preserves_values_missingness_and_key_alignment(tmp_path):
    folder = tmp_path / "pilot"
    digest = store.write_pilot(folder, [sample(), sample("2018-08-09")], ["g1", "g2"])
    rows = list(store.iter_pilot(folder, expected_manifest_sha256=digest, grid_ids=["g2", "g1"]))
    assert [day for day, _, _ in rows] == ["2018-08-01", "2018-08-09"]
    for _, features, qa in rows:
        assert features.grid_id.tolist() == qa.grid_id.tolist() == ["g1", "g2"]
        assert features.iloc[0][join.feature_names()[0]] == 0.12345678901234568
        assert features.iloc[1][join.feature_names()].isna().all()
        assert qa.weather_available_at.isna().all()
    manifest = json.loads((folder / "manifest.json").read_bytes())
    assert manifest["rows"] == 4 and manifest["scope"] == "sparse_training_pilot"
    assert manifest["model_ready"] is False and manifest["labels_created"] is False


@pytest.mark.parametrize("violation", ["lost_grid", "duplicate_grid", "target", "day", "infinite"])
def test_invalid_part_never_publishes_manifest(tmp_path, violation):
    day, features, qa = sample()
    if violation == "lost_grid":
        features = features.iloc[:1]
    elif violation == "duplicate_grid":
        features.loc[0, "grid_id"] = "g1"
    elif violation == "target":
        features["target"] = 0
    elif violation == "day":
        qa.loc[0, "prediction_timestamp_utc"] = "2018-08-02T00:00:00Z"
    else:
        features.loc[0, join.feature_names()[0]] = np.inf
    folder = tmp_path / "pilot"
    with pytest.raises(ValueError):
        store.write_pilot(folder, [(day, features, qa)], ["g1", "g2"])
    assert not (folder / "manifest.json").exists()


def test_duplicate_day_and_existing_destination_rejected(tmp_path):
    folder = tmp_path / "pilot"
    with pytest.raises(ValueError, match="Duplicate"):
        store.write_pilot(folder, [sample(), sample()], ["g1", "g2"])
    assert not (folder / "manifest.json").exists()
    with pytest.raises(FileExistsError):
        store.write_pilot(folder, [sample()], ["g1", "g2"])


def test_content_corruption_and_wrong_external_manifest_hash(tmp_path):
    folder = tmp_path / "pilot"
    digest = store.write_pilot(folder, [sample()], ["g1", "g2"])
    with pytest.raises(ValueError, match="Manifest identity"):
        list(store.iter_pilot(folder, expected_manifest_sha256="0" * 64, grid_ids=["g1", "g2"]))
    path = folder / "2018-08/2018-08-01_features.csv"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="content mismatch"):
        list(store.iter_pilot(folder, expected_manifest_sha256=digest, grid_ids=["g1", "g2"]))


@pytest.mark.parametrize("day", ["2024-01-01", "2025-01-01"])
def test_held_out_manifest_rejected_before_data_read(tmp_path, monkeypatch, day):
    folder = tmp_path / "pilot"
    store.write_pilot(folder, [sample()], ["g1", "g2"])
    digest = rewritten_manifest(folder, lambda m: m["days"][0].update(day=day))

    def forbidden(*args, **kwargs):
        raise AssertionError("Data must not be read")

    monkeypatch.setattr(store, "parse_csv", forbidden)
    with pytest.raises(ValueError, match="Training only"):
        list(store.iter_pilot(folder, expected_manifest_sha256=digest, grid_ids=["g1", "g2"]))


def test_inventory_change_and_path_escape_rejected(tmp_path):
    folder = tmp_path / "pilot"
    digest = store.write_pilot(folder, [sample()], ["g1", "g2"])
    with pytest.raises(ValueError, match="Grid/schema"):
        list(store.iter_pilot(folder, expected_manifest_sha256=digest, grid_ids=["g1", "g3"]))
    digest = rewritten_manifest(
        folder, lambda m: m["days"][0]["artifacts"]["features"].update(path="../other.csv")
    )
    with pytest.raises(ValueError, match="Unexpected partition path"):
        list(store.iter_pilot(folder, expected_manifest_sha256=digest, grid_ids=["g1", "g2"]))


def test_fabricated_acceptance_rejected(tmp_path):
    day, features, qa = sample()
    qa["operational_eligible"] = True
    with pytest.raises(ValueError, match="acceptance state"):
        store.write_pilot(tmp_path / "pilot", [(day, features, qa)], ["g1", "g2"])


def test_extra_target_column_in_provenance_rejected(tmp_path):
    day, features, qa = sample()
    qa["target"] = 1
    with pytest.raises(ValueError, match="Provenance allowlist"):
        store.write_pilot(tmp_path / "pilot", [(day, features, qa)], ["g1", "g2"])
