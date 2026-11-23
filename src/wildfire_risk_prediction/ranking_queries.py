"""No-fit inventory of source-context ordering queries; preserve unknown fire targets."""

import numpy as np
import pandas as pd

from .feature_join import KEYS, require

DYNAMIC_FEATURES = [
    "temperature_mean_c",
    "temperature_min_c",
    "temperature_max_c",
    "dewpoint_mean_c",
    "wind_speed_mean_ms",
    "wind_speed_max_ms",
    "soil_water_layer_1_mean",
    "rain_24h_nonnegative_mm",
    "rain_72h_nonnegative_mm",
    "rain_168h_nonnegative_mm",
    "rain_336h_nonnegative_mm",
    "vegetation_30d_ndvi_median_mean",
    "vegetation_30d_ndmi_median_mean",
    "vegetation_60d_ndvi_median_mean",
    "vegetation_60d_ndmi_median_mean",
]


def query_inventory(metadata, source_context, complete):
    require(not metadata.duplicated(KEYS).any(), "Unique query keys")
    require(
        metadata.target.isna().all()
        and metadata.accepted_L_membership.isna().all()
        and metadata.daily_observation_status.eq("unknown").all(),
        "Unassigned scientific targets",
    )
    times = pd.to_datetime(metadata.prediction_timestamp_utc, utc=True, format="ISO8601")
    require(times.dt.year.between(2018, 2022).all(), "Only existing 2018-2022 rows")
    require(times.eq(times.dt.normalize()).all(), "Daily UTC midnight query keys")
    roles = metadata.review_temporal_role
    require(
        roles.isin(["proposed_fit_2018_2021", "proposed_assessment_2022"]).all()
        and (roles.eq("proposed_fit_2018_2021") == times.dt.year.le(2021)).all(),
        "Exact pilot years, never move assessment rows into fit",
    )
    source, supported = np.asarray(source_context), np.asarray(complete)
    require(
        source.dtype == supported.dtype == np.dtype(bool)
        and len(source) == len(supported) == len(metadata),
        "Boolean source/support alignment",
    )
    work = metadata[KEYS + ["review_temporal_role"]].copy()
    work["calendar_month"] = times.dt.strftime("%Y-%m")
    work["source_context"] = source
    work["complete"] = supported
    rows = []
    for (grid, month, role), group in work.groupby(
        ["grid_id", "calendar_month", "review_temporal_role"], sort=True
    ):
        count = int(group.complete.sum())
        s = int((group.source_context & group.complete).sum())
        u = count - s
        require(len(group) <= 31, "At most one record per day in each cell-month")
        rows.append(
            {
                "grid_id": grid,
                "calendar_month": month,
                "pilot_role": role,
                "all_rows_retained": len(group),
                "complete_dynamic_rows": count,
                "source_context_rows": s,
                "unassigned_rows_not_true_negatives": u,
                "possible_cross_context_pairs": s * u,
                "informative_for_ordering": s > 0 and u > 0,
            }
        )
    return pd.DataFrame(rows)
