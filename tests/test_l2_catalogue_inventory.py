"""Catalogue guardrails: no sealed years, guessed pairs, or offline network access."""

import copy
import gzip
import importlib.util
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "inventory", Path(__file__).resolve().parents[1] / "scripts/firms/inventory_l2_catalogue.py"
)
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


def entry(product="VNP14IMG", day="2019013", minute="0100", version="002"):
    filename = f"{product}.A{day}.{minute}.{version}.2024086173248.nc"
    return {
        "collection_concept_id": inventory.capacity.PRODUCTS[product][2],
        "producer_granule_id": filename,
        "time_start": "2019-01-13T01:00:00Z",
        "time_end": "2019-01-13T01:06:00Z",
        "granule_size": "1.5",
        "id": f"G123-{product}",
        "links": [
            {
                "rel": "https://esipfed.org/ns/fedsearch/1.1/data#",
                "href": "https://example.org/" + filename,
            }
        ],
    }


def save_page(monkeypatch, tmp_path, entries, hits=None, token=None, next_token=None, number=1):
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    monkeypatch.setattr(inventory, "CACHE", tmp_path / "cache")
    path = inventory.CACHE / "VNP14IMG" / f"page_{number:03d}.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    page = {
        "query_url": inventory.query_url("VNP14IMG", "26,36,35,40"),
        "request_search_after": token,
        "next_search_after": next_token,
        "hits": len(entries) if hits is None else hits,
        "request_id": "fixture",
        "body": {"feed": {"entry": entries}},
    }
    path.write_bytes(gzip.compress(json.dumps(page).encode()))
    return path


@pytest.mark.parametrize("product", inventory.capacity.PRODUCTS)
def test_inventory_query_keeps_training_dates(product):
    query = parse_qs(urlsplit(inventory.query_url(product, "26,36,35,40")).query)
    assert (
        query["temporal"]
        == parse_qs(urlsplit(inventory.capacity.query_url(product, "26,36,35,40")).query)[
            "temporal"
        ]
    )
    assert query["sort_key[]"] == ["start_date", "producer_granule_id"]


def test_binary_mb_and_no_automatic_label():
    row = inventory.normalize(entry(), "VNP14IMG")
    assert row["catalogue_size_bytes_estimate"] == 1572864
    assert row["actual_input_identity_verified"] is False
    assert row["negative_label_permitted"] is False


@pytest.mark.parametrize("size", ["0", "-1", "NaN", "Infinity"])
def test_invalid_size_rejected(size):
    value = entry()
    value["granule_size"] = size
    with pytest.raises(ValueError):
        inventory.normalize(value, "VNP14IMG")


def test_sealed_year_rejected():
    value = entry(day="2025001")
    value.update(time_start="2025-01-01T01:00:00Z", time_end="2025-01-01T01:06:00Z")
    with pytest.raises(ValueError):
        inventory.normalize(value, "VNP14IMG")


def test_wrong_collection_and_filename_time_rejected():
    value = entry()
    value["collection_concept_id"] = "wrong"
    with pytest.raises(ValueError):
        inventory.normalize(value, "VNP14IMG")
    value = entry()
    value["time_start"] = "2019-01-13T01:01:00Z"
    with pytest.raises(ValueError):
        inventory.normalize(value, "VNP14IMG")


@pytest.mark.parametrize(
    "case,status",
    [
        ("unique", "nominal_unique_pair"),
        ("missing", "fire_only"),
        ("duplicate", "ambiguous_production"),
        ("interval", "interval_mismatch"),
    ],
)
def test_pairing_never_selects_unverified_production(case, status):
    fire = inventory.normalize(entry(), "VNP14IMG")
    geo = inventory.normalize(entry("VNP03IMG"), "VNP03IMG")
    rows = [fire] if case == "missing" else [fire, geo]
    if case == "duplicate":
        second = copy.copy(geo)
        second["concept_id"] = "G-second-production"
        rows.append(second)
    if case == "interval":
        geo["end_utc"] = "2019-01-13T01:05:59+00:00"
    pair = inventory.pair_catalogue(pd.DataFrame(rows)).iloc[0]
    assert pair.pair_status == status
    assert not pair.actual_input_identity_verified
    assert not pair.negative_label_permitted


def test_offline_missing_later_page_never_calls_network(monkeypatch, tmp_path):
    save_page(monkeypatch, tmp_path, [entry()], hits=2, next_token="next")

    def forbidden(*args):
        pytest.fail("Offline harvest attempted network")

    monkeypatch.setattr(inventory, "request_page", forbidden)
    with pytest.raises(ValueError, match="Missing cached page"):
        inventory.harvest("VNP14IMG", "26,36,35,40", offline=True)


@pytest.mark.parametrize("case", ["duplicates", "count_change", "misaligned"])
def test_cached_page_integrity_guards(monkeypatch, tmp_path, case):
    if case == "duplicates":
        save_page(monkeypatch, tmp_path, [entry(), entry()])
    else:
        save_page(monkeypatch, tmp_path, [entry()], hits=2, next_token="next")
        save_page(
            monkeypatch,
            tmp_path,
            [entry()],
            hits=3 if case == "count_change" else 2,
            token="next" if case == "count_change" else "wrong",
            number=2,
        )
    with pytest.raises(ValueError):
        inventory.harvest("VNP14IMG", "26,36,35,40", offline=True)


def test_empty_catalogue_is_not_a_fire_free_observation(monkeypatch, tmp_path):
    save_page(monkeypatch, tmp_path, [])
    rows, metadata = inventory.harvest("VNP14IMG", "26,36,35,40", offline=True)
    assert rows == []
    assert metadata["hits"] == 0
