"""Current closed label gate and training-only target-window diagnostics, without labels."""

import json

import pandas as pd

from wildfire_risk_prediction.feature_join import boolean, require, utc_times

VERSION = "target_admission_diagnostic_v1"
DAY_NS = 86_400_000_000_000
TRAIN_START = pd.Timestamp("2018-01-01", tz="UTC").value
TRAIN_END = pd.Timestamp("2024-01-01", tz="UTC").value


def specification():
    return {
        "version": VERSION,
        "window": "(T,T+24h]",
        "prediction_hour_utc": 0,
        "source_type_semantics_verified": False,
        "event_definition_accepted": False,
        "first_cell_policy_accepted": False,
        "habitat_policy_accepted": False,
        "observation_negative_policy_accepted": False,
        "negative_label_permitted": False,
        "positive_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
        "scope": "training_catalog_diagnostic_only",
    }


def detection_windows(values):
    """Midnight belongs to preceding T; keep out-of-training window flags instead of fixing them."""
    first = utc_times(values)
    require(first.notna().all(), "Missing first detection")
    ns = first.astype("int64")
    require(ns.ge(TRAIN_START).all() and ns.lt(TRAIN_END).all(), "Training detections only")
    start_ns = ((ns - 1) // DAY_NS) * DAY_NS
    end_ns = start_ns + DAY_NS
    return pd.DataFrame(
        {
            "prediction_timestamp_utc": pd.to_datetime(start_ns, unit="ns", utc=True),
            "target_end_inclusive_utc": pd.to_datetime(end_ns, unit="ns", utc=True),
            # Equality matters: the right endpoint belongs to the held-out year.
            "training_window_boundary_review": start_ns.lt(TRAIN_START) | end_ns.ge(TRAIN_END),
        },
        index=values.index,
    )


def assert_targets_unassigned(frame):
    """Fail closed while event, habitat and observation acceptance remain unresolved.

    This gate cannot be opened by a caller's 'observed' flag or by empty event matches.
    A later scientific acceptance requires a new version, rather than changing this guard.
    """
    require("target" in frame and not frame.empty, "Explicit nullable target column required")
    require(frame.target.isna().all(), "Binary targets are not admitted by the current protocol")


def assert_event_disjoint(assignments):
    """Check proposed train/validation event identities; no event construction or final access."""
    require(not assignments.empty and {"event_id", "split"} <= set(assignments), "Event schema")
    require(
        assignments.event_id.map(lambda s: isinstance(s, str) and bool(s.strip())).all(),
        "Event identities",
    )
    require(
        assignments.split.isin(["train", "validation"]).all(),
        "Only train/validation identity metadata; final test sealed",
    )
    require(
        assignments.groupby("event_id").split.nunique().le(1).all(),
        "An event cannot appear in multiple splits",
    )


def review_catalog(catalog):
    """Audit all exploratory clusters in one scenario without choosing an event/first-cell rule."""
    require(
        not catalog.empty and catalog.cluster_id.notna().all() and catalog.cluster_id.is_unique,
        "Unique exploratory cluster identities",
    )
    require(catalog.event_status.eq("exploratory_cluster_only").all(), "Exploratory status")
    boolean(catalog.negative_label_permitted, "negative_label_permitted")
    require(not catalog.negative_label_permitted.any(), "Negative gate changed")
    windows = detection_windows(catalog.first_detection_utc)
    saved = utc_times(catalog.candidate_prediction_timestamp_utc)
    require(saved.eq(windows.prediction_timestamp_utc).all(), "Right-closed target mapping")
    output = catalog[
        [
            "cluster_id",
            "membership_sha256",
            "first_detection_utc",
            "candidate_prediction_timestamp_utc",
            "earliest_grid_ids_json",
        ]
    ].copy()
    output["target_end_inclusive_utc"] = windows.target_end_inclusive_utc.map(
        lambda t: t.isoformat()
    )
    output["training_window_boundary_review"] = windows.training_window_boundary_review
    flags = [
        "temporal_chain_review",
        "spatial_chain_review",
        "multi_grid_first_detection_review",
        "calendar_year_crossing_review",
        "period_start_context_missing",
        "period_end_context_missing",
    ]
    for field in flags:
        boolean(catalog[field], field)
        output[field] = catalog[field]
    for row in catalog.itertuples():
        cells = json.loads(row.earliest_grid_ids_json)
        require(
            isinstance(cells, list)
            and cells
            and all(isinstance(g, str) and g for g in cells)
            and cells == sorted(set(cells))
            and len(cells) == row.earliest_grid_count,
            "Earliest cells; never resolve a tie using canonical grid",
        )
    # Nullable placeholders are diagnostics, never training labels or reliable negatives.
    output["target"] = pd.Series(pd.NA, dtype="Int8", index=output.index)
    output["event_policy_unaccepted"] = True
    output["source_semantics_unaccepted"] = True
    output["habitat_policy_unaccepted"] = True
    output["first_cell_policy_unaccepted"] = True
    output["observation_negative_policy_unaccepted"] = True
    assert_targets_unassigned(output)
    summary = {
        "clusters": len(catalog),
        "unassigned_targets": len(output),
        "training_window_boundary_review": int(output.training_window_boundary_review.sum()),
        "additional_case_review": int(output[flags].any(axis=1).sum()),
        "binary_targets_created": 0,
        "scenario_selected": None,
    }
    return output, summary
