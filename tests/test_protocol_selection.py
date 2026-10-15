import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.protocol_selection import describe_selection


def cohort():
    return pd.DataFrame(
        {
            "review_unit_id": ["a", "b", "c", "d"],
            "grid_id": ["g1", "g1", "g2", "g3"],
            "target_day": ["2021-07-01", "2021-07-02", "2018-01-01", "2023-03-01"],
            "primary_province": ["Antalya", "Antalya", "Muğla", "İzmir"],
            "calendar_season": ["summer", "summer", "winter", "spring"],
            "signal_group": ["no_selected_thermal_center"] * 3 + ["thermal_center_present"],
            "cover_group": ["forest_shrub", "forest_shrub", "urban", "herbaceous"],
            "thermal_center_definite_count": [0, 0, 0, 1],
            "nominal_land_fraction": [1.0, 0.96, 0.6, 0.4],
            "repeat_12h_fraction": [0.96, 0.5, 0.2, 0.3],
            "nominal_land_all_four_bins_fraction": [0.4, 0.96, 0.1, 0.1],
            "target": [None] * 4,
            "daily_observation_status": ["unknown"] * 4,
            "negative_label_permitted": [False] * 4,
            "labels_created": [False] * 4,
            "accepted_label_rule": [False] * 4,
        }
    )


def test_identical_units_paired_counts_and_repeated_grids_are_distinct():
    original = cohort()
    before = original.copy(deep=True)
    rows, counts, pairs = describe_selection(original, (0.95,))
    pd.testing.assert_frame_equal(original, before)
    totals = counts.loc[counts.dimension.eq("all")].set_index("screen")
    assert totals.passing_units.to_dict() == {"daily_land": 2, "repeat_12h": 1, "all_four_bins": 1}
    assert totals.denominator_units.eq(4).all() and totals.denominator_grids.eq(3).all()
    assert totals.loc["daily_land", "passing_grids"] == 1
    pair = pairs.loc[pairs.dimension.eq("all") & pairs.left_screen.eq("repeat_12h")].iloc[0]
    assert [pair.both_pass, pair.left_only, pair.right_only, pair.neither_pass] == [0, 1, 1, 2]
    assert rows.target.isna().all() and not rows.negative_label_permitted.any()


def test_all_marginal_strata_conserve_units_and_screens_do_not_choose_policy():
    rows, counts, pairs = describe_selection(cohort())
    for dimension in ("primary_province", "calendar_season", "cover_group", "year", "signal_group"):
        sub = counts.loc[counts.dimension.eq(dimension)]
        assert sub.groupby(["area_fraction_cut", "screen"]).denominator_units.sum().eq(4).all()
    assert len(rows) == 20 and not rows.accepted_label_rule.any()
    assert (
        (pairs.both_pass + pairs.left_only + pairs.right_only + pairs.neither_pass)
        .eq(pairs.denominator_units)
        .all()
    )


@pytest.mark.parametrize(
    "change",
    [
        "duplicate_id",
        "duplicate_key",
        "holdout",
        "season",
        "target",
        "negative",
        "unknown",
        "string_flag",
        "missing_stratum",
        "nan_support",
        "over_support",
        "negative_support",
        "repeat_outside",
        "thermal_group",
        "thermal_fraction",
    ],
)
def test_bad_or_admitted_pilot_rejected(change):
    frame = cohort()
    if change == "duplicate_id":
        frame.loc[1, "review_unit_id"] = "a"
    if change == "duplicate_key":
        frame.loc[1, "target_day"] = "2021-07-01"
    if change == "holdout":
        frame.loc[0, "target_day"] = "2025-07-01"
    if change == "season":
        frame.loc[0, "calendar_season"] = "winter"
    if change == "target":
        frame.loc[0, "target"] = 0
    if change == "negative":
        frame.loc[0, "negative_label_permitted"] = True
    if change == "unknown":
        frame.loc[0, "daily_observation_status"] = "observed"
    if change == "string_flag":
        frame["labels_created"] = "False"
    if change == "missing_stratum":
        frame.loc[0, "cover_group"] = None
    if change == "nan_support":
        frame.loc[0, "nominal_land_fraction"] = np.nan
    if change == "over_support":
        frame.loc[0, "nominal_land_fraction"] = 1.001
    if change == "negative_support":
        frame.loc[0, "repeat_12h_fraction"] = -0.1
    if change == "repeat_outside":
        frame.loc[3, "repeat_12h_fraction"] = 0.9
    if change == "thermal_group":
        frame.loc[0, "thermal_center_definite_count"] = 1
    if change == "thermal_fraction":
        frame["thermal_center_definite_count"] = 0.5
    with pytest.raises(ValueError):
        describe_selection(frame)


@pytest.mark.parametrize("cuts", [(), (0.9, 0.9), (0.0,), (1.1,), (float("nan"),)])
def test_explanatory_cuts_must_be_finite_distinct_fractions(cuts):
    with pytest.raises(ValueError):
        describe_selection(cohort(), cuts)


def test_valid_numerical_area_roundoff_is_preserved_without_changing_cut():
    frame = cohort()
    frame.loc[0, "nominal_land_fraction"] = 1 + 1e-10
    rows, _, _ = describe_selection(frame, (1.0,))
    assert rows.loc[rows.review_unit_id.eq("a"), "daily_land_screen"].item()


def test_reused_dataframe_index_does_not_duplicate_or_mix_grid_day_pairs():
    frame = cohort()
    frame.index = [0, 0, 0, 0]
    rows, counts, _ = describe_selection(frame, (0.95,))
    assert len(rows) == 4 and rows.review_unit_id.is_unique
    assert (
        counts.loc[
            counts.dimension.eq("all") & counts.screen.eq("daily_land"), "passing_units"
        ].item()
        == 2
    )


def test_zero_support_keeps_excluded_denominators_and_unknown_targets():
    frame = cohort()
    frame[
        ["nominal_land_fraction", "repeat_12h_fraction", "nominal_land_all_four_bins_fraction"]
    ] = 0.0
    rows, counts, paired = describe_selection(frame, (0.95,))
    assert counts.passing_units.eq(0).all()
    assert counts.excluded_units.eq(counts.denominator_units).all()
    assert paired.neither_pass.eq(paired.denominator_units).all()
    assert rows.target.isna().all() and rows.daily_observation_status.eq("unknown").all()
