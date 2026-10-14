"""Training observation diagnostics, kept separate from predictors and binary labels."""

import numpy as np
import pandas as pd

from wildfire_risk_prediction import feature_join as join

VERSION = "training_observation_sidecar_v1"
METHOD = "scan_interior_center_midpoints_v1_approximate"
GROUPS = ("reconstructed_domain", "nominal_nonfire_land", "cloud")
AREAS = ["aoi_area_m2"] + [
    f"{group}_{suffix}" for group in GROUPS for suffix in ("area_estimate_m2", "fraction_estimate")
]
COUNTS = [
    "pixel_center_count",
    "cloud",
    "land_nominal_input_no_residual",
    "nominal_confidence_fire",
    "high_confidence_fire",
    "boundary_unknown_scan_count",
    "any_center_scan_count",
    "any_center_day_scan_count",
    "any_center_night_scan_count",
    "nominal_land_center_scan_count",
    "nominal_land_center_day_scan_count",
    "nominal_land_center_night_scan_count",
]
DURATIONS = [
    f"{group}_{field}"
    for group in ("any_center", "nominal_land_center")
    for field in ("envelope_union_seconds", "longest_envelope_gap_seconds")
]
TIMES = [
    f"{group}_{field}"
    for group in ("any_center", "nominal_land_center")
    for field in ("first_start_utc", "last_end_utc")
]
NUMERIC = AREAS + COUNTS + DURATIONS
DIAGNOSTICS = NUMERIC + TIMES


def diagnostic_day(day, grid_ids, areas=None, centers=None):
    """Align by keys; missing source products retain NaN rather than measured zero."""
    stamp = join.training_day(day)
    ids = sorted(grid_ids)
    join.require(ids and len(ids) == len(set(ids)), "Unique diagnostic grid")
    join.require((areas is None) == (centers is None), "Both source tables or explicit gap")
    result = pd.DataFrame({"grid_id": ids, "prediction_timestamp_utc": stamp.isoformat()})
    present = areas is not None
    if present:
        for table in (areas, centers):
            join.require(
                table.grid_id.notna().all()
                and table.grid_id.is_unique
                and len(table) == len(ids)
                and set(table.grid_id) == set(ids),
                "Exact observation grid keys",
            )
            join.boolean(table.negative_label_permitted, "Source negative gate")
            join.require(
                not table.negative_label_permitted.any()
                and table.daily_observation_status.eq("unknown").all(),
                "Observation scientific gates unchanged",
            )
        areas = areas.set_index("grid_id").loc[ids]
        centers = centers.set_index("grid_id").loc[ids]
        join.require(areas.method.eq(METHOD).all(), "Approximate area method")
        join.require(
            np.isfinite(areas[AREAS].to_numpy()).all()
            and areas[AREAS].ge(0).all().all()
            and areas.aoi_area_m2.gt(0).all(),
            "Finite nonnegative area diagnostics",
        )
        for group in GROUPS:
            measured = areas[f"{group}_area_estimate_m2"]
            join.require(
                measured.le(areas.aoi_area_m2 + 0.1).all()
                and np.allclose(
                    measured / areas.aoi_area_m2,
                    areas[f"{group}_fraction_estimate"],
                    rtol=1e-10,
                    atol=1e-12,
                ),
                "Approximate area numerator/denominator",
            )
        values = centers[COUNTS].to_numpy()
        join.require(
            np.isfinite(values).all()
            and (values >= 0).all()
            and (values == np.floor(values)).all(),
            "Integer center diagnostics",
        )
        values = centers[DURATIONS].to_numpy()
        join.require(
            np.isfinite(values).all() and (values >= 0).all() and (values <= 86400.000001).all(),
            "Bounded center envelope diagnostics",
        )
        for field in DIAGNOSTICS:
            result["obs_" + field] = (areas if field in AREAS else centers)[field].to_numpy()
    else:
        for field in DIAGNOSTICS:
            result["obs_" + field] = np.nan if field in NUMERIC else pd.NA
    result["obs_product_present"] = present
    result["obs_source_status"] = "accepted_compact_product" if present else "deferred_source_day"
    result["obs_daily_observation_status"] = "unknown"
    result["obs_negative_label_permitted"] = False
    result["obs_nominal_granule_day"] = day
    result["obs_target_window_alignment"] = "boundary_timing_unresolved"
    return result


def summarize(frame):
    present = frame.obs_product_present
    join.boolean(present, "Product presence")
    join.boolean(frame.obs_negative_label_permitted, "Negative gate")
    join.require(
        frame.obs_daily_observation_status.eq("unknown").all()
        and frame.obs_negative_label_permitted.eq(False).all(),
        "Closed observation gate",
    )
    join.require(
        frame.loc[~present, ["obs_" + field for field in DIAGNOSTICS]].isna().all().all(),
        "Missing source must not contain diagnostic zero or dates",
    )
    return {
        "rows": len(frame),
        "rows_with_product": int(present.sum()),
        "rows_missing_product": int((~present).sum()),
        "rows_with_cloud_centers": int(frame.obs_cloud.gt(0).sum()),
        "rows_with_nominal_land_centers": int(frame.obs_land_nominal_input_no_residual.gt(0).sum()),
        "rows_with_nominal_or_high_thermal_centers": int(
            (frame.obs_nominal_confidence_fire + frame.obs_high_confidence_fire).gt(0).sum()
        ),
        "eligible_negative_rows": None,
        "binary_targets_created": 0,
    }
