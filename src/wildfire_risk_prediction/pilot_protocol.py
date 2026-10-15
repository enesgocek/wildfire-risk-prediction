"""Descriptive six-hour support and thermal witnesses; no observation/label policy."""

import numpy as np
import pandas as pd
import shapely

from wildfire_risk_prediction.feature_join import require, training_day, utc_times
from wildfire_risk_prediction.observation_window import classify_intervals, loaded_envelope_metrics


def unit_evidence(frame, shapes, region, day):
    begin = training_day(day)
    require(frame.scan_id.is_unique, "Distinct scan witnesses")
    require(frame.grid_id.nunique() == 1, "One pilot cell")
    require(
        np.asarray(shapes).shape == (len(frame),)
        and not shapely.is_missing(shapes).any()
        and shapely.is_valid(shapes).all()
        and region is not None
        and shapely.is_valid(region)
        and region.area > 0,
        "Aligned valid support geometry",
    )
    require(
        (shapely.area(shapely.difference(shapes, region)) <= 0.05).all(),
        "Support inside AOI cell",
    )
    count_columns = ["pixel_center_count", "nominal_confidence_fire", "high_confidence_fire"]
    counts = frame[count_columns].to_numpy(float)
    require(
        np.isfinite(counts).all() and (counts >= 0).all() and (counts == np.floor(counts)).all(),
        "Integer thermal counts",
    )
    thermal = frame.nominal_confidence_fire + frame.high_confidence_fire
    require(thermal.le(frame.pixel_center_count).all(), "Thermal centers within all centers")
    require(
        frame.orbit_id.str.fullmatch(r"(?:SNPP|N20):[1-9]\d*").eq(True).all(),
        "Sensor-qualified orbit IDs",
    )
    classes = classify_intervals(frame, day)
    inside = classes.eq("inside").to_numpy()
    boundary = classes.eq("boundary_unknown").to_numpy()
    starts, ends = utc_times(frame.start_utc), utc_times(frame.end_utc)
    require(starts.lt(ends).all(), "Strict scan envelopes")
    shapes = np.asarray(shapes, dtype=object)
    land = shapely.area(shapes) > 0
    daily = shapely.union_all(shapes[inside])
    seconds, gap = loaded_envelope_metrics(frame.loc[inside & land], day)
    rows, unions, ambiguous = [], [], []
    for slot in range(4):
        left = begin + pd.Timedelta(6 * slot, unit="h")
        right = left + pd.Timedelta(6, unit="h")
        admitted = inside & starts.gt(left).to_numpy() & ends.le(right).to_numpy()
        uncertain = inside & ~admitted & ends.gt(left).to_numpy() & starts.le(right).to_numpy()
        union = shapely.union_all(shapes[admitted])
        unions.append(union)
        ambiguous.extend(shapes[uncertain])
        rows.append(
            {
                "slot_index": slot,
                "slot_start_utc": left.isoformat(),
                "slot_end_utc": right.isoformat(),
                "inside_scan_count": int(admitted.sum()),
                "positive_land_scan_count": int((admitted & land).sum()),
                "positive_land_sensor_orbit_count": int(
                    frame.loc[admitted & land].orbit_id.nunique()
                ),
                "nominal_land_area_m2": float(union.area),
                "nominal_land_fraction": float(union.area / region.area),
                "bin_boundary_scan_count": int(uncertain.sum()),
                "accepted_label_rule": False,
            }
        )
    all_four = shapely.intersection_all(unions)
    require(
        shapely.difference(shapely.union_all(unions), daily).area <= 0.05
        and shapely.difference(all_four, daily).area <= 0.05,
        "Time-bin support is a daily support subset",
    )
    result = {
        "nominal_land_daily_m2": float(daily.area),
        "nominal_land_positive_scan_count": int((inside & land).sum()),
        "nominal_land_sensor_orbit_count": int(frame.loc[inside & land].orbit_id.nunique()),
        "anypart_land_scan_envelope_union_seconds": seconds,
        "anypart_land_longest_envelope_gap_seconds": gap,
        "nominal_land_all_four_bins_m2": float(all_four.area),
        "nominal_land_all_four_bins_fraction": float(all_four.area / region.area),
        "internal_bin_boundary_land_m2": float(shapely.union_all(ambiguous).area),
        "thermal_center_definite_count": int(thermal[inside].sum()),
        "thermal_center_boundary_count": int(thermal[boundary].sum()),
        "thermal_center_outside_loaded_count": int(thermal[~inside & ~boundary].sum()),
        "thermal_center_definite_sensor_orbit_count": int(
            frame.loc[inside & thermal.gt(0)].orbit_id.nunique()
        ),
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "target": None,
        "accepted_label_rule": False,
    }
    return result, rows
