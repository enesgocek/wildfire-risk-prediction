"""Key-aligned unassigned-target preview; current protocol never admits binary labels."""

import pandas as pd

from wildfire_risk_prediction import feature_join as join
from wildfire_risk_prediction import feature_partition as parts
from wildfire_risk_prediction import target_admission as targets

VERSION = "candidate_target_join_preview_v1"
LABEL_COLUMNS = join.KEYS + [
    "target",
    "event_id",
    "observation_status",
    "habitat_status",
    "unassigned_reason",
    "target_policy_version",
]


def unassigned_targets(features):
    """Explicit unknown placeholders, not produced negative or positive training samples."""
    result = features[join.KEYS].copy()
    result["target"] = pd.Series(pd.NA, index=result.index, dtype="Int8")
    result["event_id"] = pd.Series(pd.NA, index=result.index, dtype="string")
    result["observation_status"] = "unknown"
    result["habitat_status"] = "undecided"
    result["unassigned_reason"] = "scientific_policy_pending"
    result["target_policy_version"] = targets.VERSION
    return result


def assemble_day(features, provenance, labels, grid_ids, day):
    """Keep all grids and NaN, align each table by keys, and isolate audit fields from features."""
    target = join.training_day(day)
    features, provenance = parts.check_day(features, provenance, grid_ids, day)
    ids = features.grid_id.tolist()
    join.require(labels.columns.tolist() == LABEL_COLUMNS, "Label preview schema")
    labels = join.grid_rows(labels, ids, "label preview")
    join.require(
        join.utc_times(labels.prediction_timestamp_utc).eq(target).all(), "Target preview day"
    )
    targets.assert_targets_unassigned(labels)
    join.require(labels.target.dtype == pd.Int8Dtype(), "Nullable Int8 target preview")
    join.require(
        labels.event_id.isna().all()
        and labels.observation_status.eq("unknown").all()
        and labels.habitat_status.eq("undecided").all()
        and labels.unassigned_reason.eq("scientific_policy_pending").all()
        and labels.target_policy_version.eq(targets.VERSION).all(),
        "Unaccepted label/observation/habitat claim",
    )
    # Both label and feature keys have been validated independently; never merge by row position.
    for frame in (features, provenance, labels):
        frame["prediction_timestamp_utc"] = target.isoformat()
    candidate = features.merge(labels[join.KEYS + ["target"]], on=join.KEYS, validate="one_to_one")
    join.require(len(candidate) == len(ids), "Target join lost cells")
    targets.assert_targets_unassigned(candidate)
    return candidate, provenance, labels
