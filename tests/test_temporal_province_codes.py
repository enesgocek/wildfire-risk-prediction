import importlib.util
from pathlib import Path

import pandas as pd
import pytest


def test_province_membership_uses_source_codes_including_shared_border():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/quality/correct_temporal_pairwise_provinces.py"
    )
    spec = importlib.util.spec_from_file_location("temporal_province_codes_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    signatures = pd.Series(["Izmir", "Mugla", "Antalya|Mugla", "Mersin"])
    assert module.membership_mask(signatures, "Mugla").tolist() == [False, True, True, False]
    assert module.membership_mask(signatures, "Izmir").tolist() == [True, False, False, False]
    with pytest.raises(ValueError):
        module.membership_mask(signatures, "İzmir")
