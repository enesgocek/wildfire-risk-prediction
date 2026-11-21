import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def reader():
    path = Path(__file__).resolve().parents[1] / "scripts/quality/inspect_fwi_reference_metadata.py"
    spec = importlib.util.spec_from_file_location("fwi_metadata_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cf_hour_and_day_coordinates_agree_without_assuming_product_availability(reader):
    hours = reader.nominal_cf_times("hours since 2022-06-01 00:00:00", [12, 36])
    days = reader.nominal_cf_times("days since 2022-06-01T00:00:00Z", [0.5, 1.5])
    assert hours == days == ["2022-06-01T12:00:00+00:00", "2022-06-02T12:00:00+00:00"]


@pytest.mark.parametrize(
    "units,values",
    [("hours since 2023-06-01", [12]), ("hours since 2022-06-30", [36]), ("unrecognized", [1])],
)
def test_pilot_rejects_closed_year_other_month_or_unknown_CF_unit(reader, units, values):
    with pytest.raises(ValueError):
        reader.nominal_cf_times(units, values)
