"""Capacity queries must respect sensor-request dates and sealed years."""

import importlib.util
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

SPEC = importlib.util.spec_from_file_location(
    "capacity", Path(__file__).resolve().parents[1] / "scripts/firms/snapshot_l2_capacity.py"
)
capacity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capacity)


@pytest.mark.parametrize("product", capacity.PRODUCTS)
def test_training_only_query_and_noaa20_request_start(product):
    sensor, _, collection = capacity.PRODUCTS[product]
    query = parse_qs(urlparse(capacity.query_url(product, "26,36,35,40")).query)
    start = "2018-01-01" if sensor == "SNPP" else "2018-04-01"
    assert query["temporal"] == [f"{start}T00:00:00.000001Z,2023-12-31T23:59:59.999999Z"]
    assert query["collection_concept_id"] == [collection]
    assert query["page_size"] == ["1"]
