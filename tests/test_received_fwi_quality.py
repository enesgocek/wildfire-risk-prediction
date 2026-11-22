import importlib.util
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def review(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "scripts/quality"
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(
        "received_fwi_quality_test", folder / "review_received_fwi_pilot.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_zero_and_over_100_are_valid_and_declared_missing_is_preserved(review):
    x = np.ma.array([0.0, 120.0, 999.0, np.nan, -0.1], mask=[False, False, True, False, False])
    original = x.copy()
    result = review.quality(x)
    assert result["finite"] == 3 and result["zero_valid"] == 1
    assert result["above_100_not_automatically_invalid"] == 1 and result["negative"] == 1
    assert result["declared_missing"] == 1 and result["unmasked_nonfinite"] == 1
    np.testing.assert_array_equal(x.mask, original.mask)
    np.testing.assert_array_equal(x.data, original.data)


def test_all_missing_is_not_accepted_as_usable_FWI(review):
    with pytest.raises(ValueError, match="finite unmasked"):
        review.quality(np.ma.masked_all((2, 2)))
