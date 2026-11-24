from fractions import Fraction

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.frozen_score_diagnostics import (
    leave_one_cell_out,
    source_day_credits,
    summarize,
)


def sample():
    rows = []
    for day in range(1, 12):
        rows.append(
            {
                "grid_id": "a",
                "prediction_timestamp_utc": f"2022-01-{day:02}T00:00:00+00:00",
                "source_context": day == 1,
                "primary_eligible": True,
                "score": 3.0 if day == 1 else 1.0,
            }
        )
    for day in (1, 2):
        rows.append(
            {
                "grid_id": "b",
                "prediction_timestamp_utc": f"2022-01-{day:02}T00:00:00+00:00",
                "source_context": day == 1,
                "primary_eligible": True,
                "score": float(day),
            }
        )
    frame = pd.DataFrame(rows)
    frame["target"], frame["accepted_L_membership"] = np.nan, np.nan
    frame["daily_observation_status"] = "unknown"
    frame["province_area_intersections"] = "Mersin"
    frame["cell_seen_in_fit"] = False
    return frame


def test_pair_weighting_can_differ_from_equal_day_or_cell_weighting():
    frame = sample()
    frame.loc[frame.grid_id.eq("b"), "score"] = [0.0, 1.0]
    credits = source_day_credits(frame, {"fixed": "score"})
    result = summarize(credits)
    assert (result["pairs"], result["source_days"], result["cells"]) == (11, 2, 2)
    assert result["pair_weighted_credit"] == float(Fraction(10, 11))
    assert (
        result["equal_source_day_credit"]
        == result["equal_cell_month_credit"]
        == result["equal_cell_credit"]
        == 0.5
    )
    omitted = leave_one_cell_out(credits).set_index("omitted_cell")
    assert omitted.loc["a", "credit_after_omitting_cell"] == 0
    assert omitted.loc["b", "credit_after_omitting_cell"] == 1


def test_ties_and_missing_comparators_are_preserved_without_negative_labels():
    frame = sample()
    frame["score"] = 2.0
    frame.loc[2, ["primary_eligible", "score"]] = [False, np.nan]
    result = summarize(source_day_credits(frame, {"fixed": "score"}))
    assert result["pairs"] == result["ties"] == 10
    assert result["pair_weighted_credit"] == 0.5 and frame.target.isna().all()
    only = source_day_credits(frame.loc[frame.grid_id.eq("b")], {"fixed": "score"})
    omitted = leave_one_cell_out(only)
    assert omitted.retained_pairs.iloc[0] == 0
    assert pd.isna(omitted.credit_after_omitting_cell.iloc[0])


def test_later_year_true_target_and_duplicate_keys_are_rejected():
    frame = sample()
    frame.loc[0, "prediction_timestamp_utc"] = "2023-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="existing 2022"):
        source_day_credits(frame, {"fixed": "score"})
    frame = sample()
    frame.loc[0, "target"] = 1
    with pytest.raises(ValueError, match="Unknown scientific"):
        source_day_credits(frame, {"fixed": "score"})
    with pytest.raises(ValueError, match="Unique diagnostic"):
        source_day_credits(pd.concat([sample(), sample()]), {"fixed": "score"})
