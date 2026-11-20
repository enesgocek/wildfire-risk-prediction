import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def bundle(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "bundle_test", folder / "build_pu_inspection_bundle.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def toy(bundle):
    u = pd.DataFrame(
        {
            "grid_id": ["A"],
            "prediction_timestamp_utc": ["2021-04-01T00:00:00+00:00"],
            "target": [None],
            "daily_observation_status": ["unknown"],
            "population_index": [42],
            "sampling_probability": [0.01],
            "sampling_weight": [100.0],
        }
    )
    s = u[bundle.join.KEYS + ["target", "daily_observation_status"]].copy()
    s["grid_id"] = "B"
    uf = u[bundle.join.KEYS].copy()
    sf = s[bundle.join.KEYS].copy()
    for frame in (uf, sf):
        for field in bundle.join.feature_names():
            frame[field] = float("nan")
        frame["temperature_mean_c"] = 0.0
    mapping = [
        {
            "archive_row": "ONE",
            "grid_id": "B",
            "prediction_timestamp_utc": s.iloc[0].prediction_timestamp_utc,
            "target": None,
        },
        {
            "archive_row": "TWO",
            "grid_id": "B",
            "prediction_timestamp_utc": s.iloc[0].prediction_timestamp_utc,
            "target": None,
        },
    ]
    support = pd.DataFrame({"grid_id": ["A", "B"], "province": ["Antalya", "Mersin"]})
    return u, s, uf, sf, mapping, support


def test_limited_union_keeps_unknowns_source_multiplicity_and_sampling_weights(bundle):
    args = toy(bundle)
    result = bundle.make_review_tables(*args)
    assert len(result) == 2 and result.target.isna().all()
    assert result.eksik_ozellik_sayisi.eq(26).all()
    assert result.temperature_mean_c.eq(0).all()
    assert result.loc[result.grid_id.eq("B"), "kaynak_kayit_sayisi"].iloc[0] == 2
    assert result.loc[result.grid_id.eq("A"), "sampling_weight"].iloc[0] == 100
    assert result.loc[result.grid_id.eq("B"), "sampling_weight"].isna().all()


@pytest.mark.parametrize("kind", ["overlap", "known_Y", "late_year", "missing_feature_key"])
def test_no_silent_overlap_drop_labels_or_later_years(bundle, kind):
    u, s, uf, sf, mapping, support = toy(bundle)
    if kind == "overlap":
        s["grid_id"] = "A"
    elif kind == "known_Y":
        s.loc[0, "target"] = 1
    elif kind == "late_year":
        u["prediction_timestamp_utc"] = "2024-01-01T00:00:00+00:00"
    else:
        uf["grid_id"] = "X"
    with pytest.raises(ValueError):
        bundle.make_review_tables(u, s, uf, sf, mapping, support)


def test_payload_uses_nulls_and_cannot_end_json_script(bundle):
    frame = pd.DataFrame(
        {
            "grid_id": ["</script><script>alert(1)</script>"],
            "prediction_timestamp_utc": ["2021-01-01T00:00:00+00:00"],
            "target": [float("nan")],
            "value": [0.0],
        }
    )
    template = '<script type="application/json" id="payload">__PAYLOAD_JSON__</script>'
    result = bundle.render_page(frame, frame[bundle.join.KEYS], [], template)
    assert result.count("</script>") == 1 and "alert(1)" in result
    encoded = result.split('id="payload">')[1].split("</script>")[0]
    saved = json.loads(encoded)
    assert saved["rows"][0]["target"] is None and saved["rows"][0]["value"] == 0.0
    assert saved["rows"][0]["grid_id"] == frame.iloc[0].grid_id
    assert saved["risk_predictions_present"] is False


def test_provenance_key_mismatch_is_not_ignored(bundle):
    frame = pd.DataFrame(
        {"grid_id": ["A"], "prediction_timestamp_utc": ["2021-01-01T00:00:00+00:00"]}
    )
    with pytest.raises(ValueError, match="provenance"):
        bundle.render_page(frame, frame.assign(grid_id="B"), [], "__PAYLOAD_JSON__")
