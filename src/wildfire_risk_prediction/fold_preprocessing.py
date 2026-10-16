"""Training-fold numeric preparation only; no label or model admission authority."""

import hashlib
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from wildfire_risk_prediction.evaluation_folds import audit_training_fold
from wildfire_risk_prediction.feature_join import KEYS, feature_names, require, utc_times


def identities(frame):
    require(frame.columns.is_unique and set(KEYS) <= set(frame), "Unique schema with keys")
    require(len(frame) > 0, "Nonempty feature partition")
    require(
        frame.grid_id.map(lambda x: isinstance(x, str) and bool(x.strip())).all(),
        "Complete string grid identities",
    )
    times = utc_times(frame.prediction_timestamp_utc)
    require(times.notna().all() and times.eq(times.dt.normalize()).all(), "Daily UTC keys")
    require(times.dt.year.between(2018, 2023).all(), "Training only; 2024/2025 sealed here")
    keys = tuple(zip(frame.grid_id, times.map(lambda x: x.isoformat()), strict=True))
    require(len(set(keys)) == len(keys), "Unique canonical feature keys")
    return keys


def numeric_matrix(frame, features):
    require(
        frame.columns.is_unique and set(frame) == set(KEYS) | set(features),
        "Exact declared feature schema; target and QA/provenance forbidden",
    )
    for name in features:
        require(
            pd.api.types.is_numeric_dtype(frame[name])
            and not pd.api.types.is_bool_dtype(frame[name])
            and not pd.api.types.is_complex_dtype(frame[name]),
            "Real numeric features only; no string coercion",
        )
    values = frame.loc[:, features].to_numpy(dtype=np.float64, na_value=np.nan, copy=True)
    require(not np.isinf(values).any(), "Infinite feature values forbidden")
    return values


@dataclass(frozen=True)
class FoldPreprocessor:
    """Immutable statistics for exactly two audited partitions, not a deployment object."""

    features: tuple
    retained_features: tuple
    medians: tuple
    means: tuple
    scales: tuple
    observed_counts: tuple
    train_keys: tuple
    held_out_keys: tuple
    training_digest: str
    standardize: bool
    empty_policy: str

    def transform(self, frame, *, partition):
        require(partition in ("training", "held_out"), "Explicit audited partition")
        keys = identities(frame)
        expected = self.train_keys if partition == "training" else self.held_out_keys
        require(set(keys) == set(expected), "Exact audited partition keys; no row loss/addition")
        values = numeric_matrix(frame, self.features)
        indices = [self.features.index(name) for name in self.retained_features]
        values = values[:, indices]
        values = np.where(np.isnan(values), np.asarray(self.medians), values)
        if self.standardize:
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                values = (values - np.asarray(self.means)) / np.asarray(self.scales)
        require(np.isfinite(values).all(), "Finite transformed values required; no clipping")
        out = frame.loc[:, KEYS].copy()
        for i, name in enumerate(self.retained_features):
            out[name] = values[:, i]
        return out

    def summary(self):
        return {
            "status": "fold_preprocessing_statistics_not_training_authorization",
            "features": list(self.features),
            "retained_features": list(self.retained_features),
            "dropped_features": [x for x in self.features if x not in self.retained_features],
            "training_observed_counts": dict(zip(self.features, self.observed_counts, strict=True)),
            "training_medians": dict(zip(self.retained_features, self.medians, strict=True)),
            "imputed_training_means": (
                dict(zip(self.retained_features, self.means, strict=True))
                if self.standardize
                else None
            ),
            "training_scales": (
                dict(zip(self.retained_features, self.scales, strict=True))
                if self.standardize
                else None
            ),
            "standardize": self.standardize,
            "empty_policy": self.empty_policy,
            "training_rows": len(self.train_keys),
            "held_out_rows": len(self.held_out_keys),
            "training_input_sha256": self.training_digest,
            "labels_accepted": False,
            "model_ready": False,
        }


def fit_fold_preprocessor(
    train,
    train_metadata,
    held_out_metadata,
    *,
    features,
    imputation,
    standardize,
    empty_policy,
    embargo_hours,
    spatial_column=None,
):
    """Audit before learning. Held-out feature values are deliberately not a fit argument."""
    require(
        isinstance(features, (tuple, list))
        and len(features) > 0
        and all(isinstance(x, str) for x in features)
        and len(features) == len(set(features))
        and set(features) <= set(feature_names()),
        "Explicit unique subset of retrospective feature whitelist",
    )
    require(imputation == "median", "Only explicit median candidate implemented")
    require(type(standardize) is bool, "Explicit boolean scaling choice")
    require(empty_policy in ("error", "drop"), "Explicit all-training-missing policy")
    train_keys, held_out_keys = identities(train_metadata), identities(held_out_metadata)
    audit_training_fold(
        train_metadata,
        held_out_metadata,
        embargo_hours=embargo_hours,
        spatial_column=spatial_column,
    )
    keys = identities(train)
    require(set(keys) == set(train_keys), "Training features must match audited metadata exactly")
    features = tuple(features)
    values = numeric_matrix(train, features)
    counts = (~np.isnan(values)).sum(axis=0)
    require(empty_policy != "error" or (counts > 0).all(), "All-training-missing feature")
    indices = np.flatnonzero(counts > 0)
    require(len(indices) > 0, "At least one observed training feature required")
    retained = tuple(features[i] for i in indices)
    # Explicitly remove allowed empty columns before fitting; no implicit zero filling.
    imputer = SimpleImputer(strategy="median", keep_empty_features=False, add_indicator=False)
    imputed = imputer.fit_transform(values[:, indices])
    means, scales = np.zeros(len(indices)), np.ones(len(indices))
    if standardize:
        scaler = StandardScaler(copy=True, with_mean=True, with_std=True).fit(imputed)
        means, scales = scaler.mean_, scaler.scale_
    require(
        np.isfinite(imputer.statistics_).all()
        and np.isfinite(means).all()
        and np.isfinite(scales).all()
        and (scales > 0).all(),
        "Finite fitted statistics and positive scales",
    )
    # Canonical keys, declared feature order and exact float64 bytes bind training input.
    order = sorted(range(len(keys)), key=lambda i: keys[i])
    canonical = values[order].copy()
    canonical[np.isnan(canonical)] = np.nan
    header = json.dumps({"keys": sorted(keys), "features": features}, sort_keys=True).encode()
    checksum = hashlib.sha256(header + canonical.astype("<f8").tobytes()).hexdigest()
    return FoldPreprocessor(
        features,
        retained,
        tuple(float(x) for x in imputer.statistics_),
        tuple(float(x) for x in means),
        tuple(float(x) for x in scales),
        tuple(int(x) for x in counts),
        tuple(sorted(train_keys)),
        tuple(sorted(held_out_keys)),
        checksum,
        standardize,
        empty_policy,
    )
