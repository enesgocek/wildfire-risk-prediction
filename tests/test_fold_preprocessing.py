from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from wildfire_risk_prediction.feature_join import KEYS, feature_names
from wildfire_risk_prediction.fold_preprocessing import fit_fold_preprocessor

FEATURES = tuple(feature_names()[:3])


def metadata(day, count=4, prefix="g"):
    return pd.DataFrame(
        {
            "grid_id": [f"{prefix}{i}" for i in range(count)],
            "prediction_timestamp_utc": [day + "T00:00:00Z"] * count,
            "event_ids": [[] for _ in range(count)],
            "event_membership_complete": [True] * count,
        }
    )


def fixture():
    train = metadata("2020-07-01")
    held = metadata("2021-07-01", 2)
    values = train[KEYS].copy()
    values[FEATURES[0]] = [1.0, np.nan, 3.0, 8.0]
    values[FEATURES[1]] = [7.0] * 4
    values[FEATURES[2]] = [np.nan] * 4
    return values, train, held


def fit(values=None, train=None, held=None, **kwargs):
    default_values, default_train, default_held = fixture()
    options = dict(
        features=FEATURES,
        imputation="median",
        standardize=True,
        empty_policy="drop",
        embargo_hours=0,
    )
    options.update(kwargs)
    return fit_fold_preprocessor(
        default_values if values is None else values,
        default_train if train is None else train,
        default_held if held is None else held,
        **options,
    )


def test_training_median_mean_and_scale_by_hand_and_preserve_inputs():
    values, train, held = fixture()
    before = values.copy(deep=True)
    state = fit(values, train, held)
    assert state.medians == (3, 7)
    assert state.means == (3.75, 7)
    assert state.scales == pytest.approx((np.sqrt(6.6875), 1))
    assert state.observed_counts == (3, 4, 0)
    transformed = state.transform(values, partition="training")
    assert transformed[FEATURES[0]].mean() == pytest.approx(0)
    assert transformed[FEATURES[0]].var(ddof=0) == pytest.approx(1)
    assert transformed[FEATURES[1]].eq(0).all()
    pd.testing.assert_frame_equal(values, before)


def test_held_values_missing_extreme_and_newly_observed_empty_column_never_update_state():
    _, _, held = fixture()
    state = fit()
    before = state.summary()
    values = held[KEYS].copy()
    values[FEATURES[0]], values[FEATURES[1]], values[FEATURES[2]] = [np.nan, 1e6], 9, 42
    result = state.transform(values, partition="held_out")
    assert result.iloc[0][FEATURES[0]] == pytest.approx((3 - 3.75) / np.sqrt(6.6875))
    assert result[FEATURES[1]].eq(2).all()
    assert FEATURES[2] not in result
    assert state.summary() == before
    values[FEATURES[0]] = [-1e6, np.nan]
    state.transform(values, partition="held_out")
    assert state.summary() == before


def test_unscaled_option_preserves_observed_values_and_only_imputes():
    values, _, _ = fixture()
    state = fit(standardize=False)
    result = state.transform(values, partition="training")
    assert result[FEATURES[0]].tolist() == [1, 3, 3, 8]
    assert result[FEATURES[1]].tolist() == [7] * 4
    assert state.summary()["imputed_training_means"] is None
    assert state.summary()["training_scales"] is None


def test_folds_are_independent_and_fitted_snapshot_is_immutable():
    values, _, _ = fixture()
    first = fit()
    values[FEATURES[0]] += 100
    second = fit(values)
    assert second.medians[0] == first.medians[0] + 100
    assert first.training_digest != second.training_digest
    with pytest.raises(FrozenInstanceError):
        first.standardize = False


def test_reordered_columns_rows_and_utc_alias_preserve_identity_and_statistics():
    values, train, held = fixture()
    original = fit()
    values = values.iloc[::-1, ::-1]
    values.prediction_timestamp_utc = values.prediction_timestamp_utc.str.replace("Z", "+00:00")
    reordered = fit(values, train.iloc[::-1], held)
    assert reordered == original
    result = reordered.transform(values, partition="training")
    assert result.grid_id.tolist() == values.grid_id.tolist()
    assert list(result) == KEYS + list(FEATURES[:2])


@pytest.mark.parametrize("column", ["target", "daily_observation_status", "available_at", "extra"])
def test_target_quality_and_provenance_do_not_enter_features(column):
    values, _, _ = fixture()
    values[column] = 0
    with pytest.raises(ValueError, match="schema"):
        fit(values)


@pytest.mark.parametrize("bad", ["2", True, 1 + 2j, np.inf, -np.inf])
def test_non_numeric_boolean_complex_and_infinite_inputs_rejected(bad):
    values, _, _ = fixture()
    values[FEATURES[0]] = [bad] * len(values)
    with pytest.raises(ValueError):
        fit(values)


@pytest.mark.parametrize(
    "options",
    [
        {"features": ["target"]},
        {"features": [FEATURES[0], FEATURES[0]]},
        {"features": []},
        {"imputation": "zero"},
        {"standardize": "true"},
        {"empty_policy": "zero"},
        {"embargo_hours": None},
    ],
)
def test_invalid_or_implicit_policy_rejected(options):
    with pytest.raises(ValueError):
        fit(**options)


def test_all_missing_policy_error_and_all_columns_empty_drop_both_reject():
    with pytest.raises(ValueError, match="All-training-missing"):
        fit(empty_policy="error")
    values, _, _ = fixture()
    values.loc[:, FEATURES] = np.nan
    with pytest.raises(ValueError, match="observed training"):
        fit(values)


@pytest.mark.parametrize("problem", ["missing", "extra", "duplicate", "wrong_time", "wrong_grid"])
def test_training_features_must_match_metadata(problem):
    values, _, _ = fixture()
    if problem == "missing":
        values = values.iloc[1:]
    elif problem == "extra":
        added = values.iloc[[0]].assign(grid_id="other")
        values = pd.concat([values, added])
    elif problem == "duplicate":
        values = pd.concat([values, values.iloc[[0]]])
    elif problem == "wrong_time":
        values.loc[0, "prediction_timestamp_utc"] = "2020-07-02T00:00:00Z"
    else:
        values.loc[0, "grid_id"] = "wrong"
    with pytest.raises(ValueError):
        fit(values)


@pytest.mark.parametrize("problem", ["unknown_event", "shared_event", "past", "2024", "2025"])
def test_fold_guards_before_fitting(problem):
    _, train, held = fixture()
    if problem == "unknown_event":
        train.loc[0, "event_membership_complete"] = False
    elif problem == "shared_event":
        train.at[0, "event_ids"] = ["shared"]
        held.at[1, "event_ids"] = ["shared"]
    else:
        year = "2019" if problem == "past" else problem
        held.prediction_timestamp_utc = year + "-07-01T00:00:00Z"
    with pytest.raises(ValueError):
        fit(train=train, held=held)


def test_disjoint_named_spatial_blocks_required_when_requested():
    _, train, held = fixture()
    train["block"], held["block"] = "same", "same"
    with pytest.raises(ValueError, match="disjoint"):
        fit(train=train, held=held, spatial_column="block")


@pytest.mark.parametrize("problem", ["subset", "wrong_partition", "2025", "bad_score", "target"])
def test_transform_only_exact_audited_partition_with_valid_schema(problem):
    values, _, held = fixture()
    state = fit()
    if problem == "subset":
        values = values.iloc[1:]
    elif problem == "2025":
        values.prediction_timestamp_utc = "2025-07-01T00:00:00Z"
    elif problem == "bad_score":
        values[FEATURES[0]] = np.inf
    elif problem == "target":
        values["target"] = 0
    else:
        values = held[KEYS].copy()
        for name in FEATURES:
            values[name] = 1.0
    with pytest.raises(ValueError):
        state.transform(values, partition="training")


def test_nullable_numeric_missing_is_supported_and_schema_missing_column_rejected():
    values, _, _ = fixture()
    values[FEATURES[0]] = pd.Series([1, None, 3, 8], dtype="Int64")
    assert fit(values).medians[0] == 3
    with pytest.raises(ValueError, match="schema"):
        fit(values.drop(columns=FEATURES[0]))


def test_duplicate_column_schema_rejected():
    values, _, _ = fixture()
    values = pd.concat([values, values[[FEATURES[0]]]], axis=1)
    with pytest.raises(ValueError):
        fit(values)


def test_near_constant_scale_and_nonfinite_transform_guard():
    values, _, _ = fixture()
    values[FEATURES[0]] = np.array([1e12, 1e12, 1e12, 1e12 + 0.0001])
    assert fit(values).scales[0] == 1
    values[FEATURES[0]] = [0, 1e-10, 0, 1e-10]
    state = fit(values)
    values[FEATURES[0]] = 1e308
    with pytest.raises(ValueError, match="Finite transformed"):
        state.transform(values, partition="training")


@pytest.mark.parametrize("problem", ["empty", "non_midnight", "duplicate_metadata"])
def test_invalid_metadata_never_fitted(problem):
    _, train, _ = fixture()
    if problem == "empty":
        train = train.iloc[:0]
    elif problem == "non_midnight":
        train.prediction_timestamp_utc = "2020-07-01T12:00:00Z"
    else:
        train = pd.concat([train, train[["grid_id"]]], axis=1)
    with pytest.raises(ValueError):
        fit(train=train)


def test_unknown_transform_partition_rejected():
    values, _, _ = fixture()
    with pytest.raises(ValueError, match="Explicit audited partition"):
        fit().transform(values, partition="final")
