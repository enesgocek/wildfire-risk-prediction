import pandas as pd
import pytest

from wildfire_risk_prediction.source_review_sampling import sample_source_keys


def frame():
    return pd.DataFrame(
        [
            {"archive_row": f"{year}_{i}", "year": year}
            for year in range(2018, 2023)
            for i in range(year - 2013)
        ]
    )


def test_selection_is_order_independent_with_known_within_source_probabilities():
    source = frame()
    a = sample_source_keys(source, per_year=2, seed=42)
    b = sample_source_keys(source.sample(frac=1, random_state=9), per_year=2, seed=42)
    pd.testing.assert_frame_equal(a, b)
    assert a.groupby("year").size().eq(2).all()
    assert a.archive_row.is_unique and a.target.isna().all()
    assert a.review_role.eq("source_sampling_review_only_not_L").all()
    for year, selected in a.groupby("year"):
        n = source.year.eq(year).sum()
        assert selected.inclusion_probability_within_source_year.eq(2 / n).all()


@pytest.mark.parametrize(
    "column", ["fire_detected", "cloud_fraction", "burned_area_ha", "latitude"]
)
def test_outcome_quality_size_or_location_columns_are_rejected(column):
    source = frame().assign(**{column: 0})
    with pytest.raises(ValueError, match="Only identifier/year"):
        sample_source_keys(source, per_year=2, seed=42)


@pytest.mark.parametrize("year", [2017, 2023, 2024, 2025])
def test_outside_fit_year_is_rejected(year):
    source = pd.concat([frame(), pd.DataFrame([{"archive_row": "other", "year": year}])])
    with pytest.raises(ValueError, match="Exactly fit-role"):
        sample_source_keys(source, per_year=2, seed=42)


def test_duplicate_source_identity_is_rejected():
    source = pd.concat([frame(), frame().iloc[:1]])
    with pytest.raises(ValueError, match="unique"):
        sample_source_keys(source, per_year=2, seed=42)


def test_small_year_stratum_is_not_filled_by_replacement_or_another_year():
    source = frame()
    source = source.loc[~source.year.eq(2018) | source.archive_row.eq("2018_0")]
    with pytest.raises(ValueError, match="Not enough source rows"):
        sample_source_keys(source, per_year=2, seed=42)
