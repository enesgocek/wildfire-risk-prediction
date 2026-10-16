"""Audit training-only fold metadata; never select event policy, embargo or spatial blocks."""

import pandas as pd

from wildfire_risk_prediction.feature_join import boolean, require, utc_times


def training_metadata(frame):
    required = {"grid_id", "prediction_timestamp_utc", "event_ids", "event_membership_complete"}
    require(required <= set(frame.columns) and len(frame) > 0, "Complete nonempty fold metadata")
    require(
        frame.grid_id.map(lambda x: isinstance(x, str) and bool(x.strip())).all()
        and not frame.duplicated(["grid_id", "prediction_timestamp_utc"]).any(),
        "Unique complete grid/timestamp identities",
    )
    times = utc_times(frame.prediction_timestamp_utc)
    require(times.notna().all() and times.eq(times.dt.normalize()).all(), "Daily UTC issue times")
    require(
        pd.MultiIndex.from_arrays([frame.grid_id, times]).is_unique,
        "Canonical UTC grid/time identities must be unique",
    )
    require(times.dt.year.between(2018, 2023).all(), "Training only; 2024/2025 sealed here")
    boolean(frame.event_membership_complete, "event_membership_complete")
    require(frame.event_membership_complete.all(), "Resolved event membership is required")
    require(
        frame.event_ids.map(
            lambda ids: (
                isinstance(ids, list)
                and all(isinstance(x, str) and bool(x.strip()) for x in ids)
                and len(ids) == len(set(ids))
            )
        ).all(),
        "Explicit unique event memberships; empty list only when resolved",
    )
    return times, {event for ids in frame.event_ids for event in ids}


def audit_training_fold(train, held_out, *, embargo_hours, spatial_column=None):
    """Require forward time, disjoint events, and optional disjoint named spatial blocks."""
    require(
        type(embargo_hours) is int and 0 <= embargo_hours <= 24 * 366 * 6,
        "Explicit bounded nonnegative whole embargo hours",
    )
    train_times, train_events = training_metadata(train)
    held_times, held_events = training_metadata(held_out)
    # (T,T+24h] and (T+24h,T+48h] meet at a point included only in the earlier window.
    hour_ns = 3_600_000_000_000
    latest_end = pd.Timestamp(train_times.max().value + 24 * hour_ns, unit="ns", tz="UTC")
    boundary = pd.Timestamp(held_times.min().value - embargo_hours * hour_ns, unit="ns", tz="UTC")
    require(latest_end <= boundary, "Forward time and nonoverlapping target windows plus embargo")
    require(not (train_events & held_events), "Same event cannot occur in both fold partitions")
    if spatial_column is not None:
        require(isinstance(spatial_column, str) and spatial_column, "Named spatial block column")
        for frame in (train, held_out):
            require(
                spatial_column in frame
                and frame[spatial_column]
                .map(lambda x: isinstance(x, str) and bool(x.strip()))
                .all(),
                "Complete spatial blocks",
            )
        require(
            not set(train[spatial_column]) & set(held_out[spatial_column]),
            "Spatial blocks must be disjoint",
        )
    return {
        "status": "fold_metadata_checks_passed_not_training_authorization",
        "training_rows": len(train),
        "held_out_rows": len(held_out),
        "latest_training_target_end_utc": latest_end.isoformat(),
        "earliest_held_out_issue_utc": held_times.min().isoformat(),
        "embargo_hours": embargo_hours,
        "shared_event_count": 0,
        "spatial_blocks_checked": spatial_column is not None,
        "labels_accepted": False,
        "model_ready": False,
    }


def forward_year_skeleton():
    """Calendar proposal only; no observations, exclusions or policy acceptance implied."""
    return [
        {
            "fit_years": list(range(2018, year)),
            "held_out_year": year,
            "embargo_hours": None,
            "event_boundary_policy": "pending",
            "status": "calendar_skeleton_not_executable_fold",
        }
        for year in range(2019, 2024)
    ]
