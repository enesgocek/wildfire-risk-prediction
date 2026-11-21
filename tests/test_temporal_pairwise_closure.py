import importlib.util
from pathlib import Path

import pandas as pd


def test_date_slices_ignore_original_index_alignment_and_respect_direction():
    path = Path(__file__).resolve().parents[1] / "scripts/quality/close_temporal_pairwise_pilot.py"
    spec = importlib.util.spec_from_file_location("temporal_closure_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    dates = pd.Series(
        pd.to_datetime(["2022-06-15", "2022-06-14", "2022-06-18", "2022-06-20"], utc=True)
    )
    masks = module.date_slices(dates, [0, 0, 0], [1, 2, 3])
    assert masks["other_day_before_source_day"].tolist() == [True, False, False]
    assert masks["other_day_after_source_day"].tolist() == [False, True, True]
    assert masks["gap_1_to_3_days"].tolist() == [True, True, False]
    assert masks["gap_4_to_30_days"].tolist() == [False, False, True]
