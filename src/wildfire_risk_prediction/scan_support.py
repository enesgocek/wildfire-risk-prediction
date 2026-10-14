"""Spatial repeats with acquisition-envelope separation; no negative label policy."""

import re

import numpy as np
import pandas as pd
import shapely

from wildfire_risk_prediction.feature_join import require, training_day, utc_times
from wildfire_risk_prediction.observation_window import classify_intervals

PAIR_COLUMNS = ["earlier_scan_id", "later_scan_id", "minimum_gap_hours", "overlap_area_m2"]


def read_scan_table(path):
    """Preserve nominal granule IDs as text and reconcile their compound scan keys."""
    frame = pd.read_csv(path, dtype={"pair_key": str}, float_precision="round_trip")
    require(
        {"grid_id", "sensor", "pair_key", "scan_index", "scan_id"} <= set(frame),
        "Scan identity columns",
    )
    require(
        frame.sensor.isin(["SNPP", "N20"]).all()
        and frame.pair_key.str.fullmatch(r"\d{7}\.\d{4}").eq(True).all(),
        "Text granule IDs",
    )
    indices = frame.scan_index.to_numpy(float)
    require(
        np.isfinite(indices).all()
        and (indices >= 0).all()
        and (indices == np.floor(indices)).all(),
        "Integer scan indices",
    )
    expected = (
        frame.sensor + ":" + frame.pair_key + ":" + frame.scan_index.astype("int64").astype(str)
    )
    require(
        frame.scan_id.eq(expected).all()
        and frame.grid_id.notna().all()
        and not frame.duplicated(["grid_id", "scan_id"]).any(),
        "Compound scan identity",
    )
    return frame


def temporal_repeat_support(frame, geometries, region, day, gaps=(1, 6, 12)):
    """Union overlapping nominal-land areas from distinct sensor/orbits separated by h.

    A scan has an acquisition envelope, not one exact acquisition instant per pixel.
    later.start - earlier.end is a lower bound on separation for both footprints.
    Boundaries outside (T,T+24h] are retained by callers, never admitted here.
    Distinct sensor/orbit identities do not imply statistical independence.
    """
    training_day(day)  # Guard even for empty data, before considering the source period.
    cuts = np.asarray(gaps, dtype=float)
    require(
        cuts.ndim == 1
        and len(cuts) > 0
        and np.isfinite(cuts).all()
        and (cuts > 0).all()
        and len(set(cuts)) == len(cuts),
        "Positive distinct hour cuts",
    )
    require(frame.scan_id.notna().all() and frame.scan_id.is_unique, "Unique scan identities")
    require(frame.grid_id.notna().all() and frame.grid_id.nunique() <= 1, "One grid per review")
    require(
        frame.orbit_id.map(
            lambda s: isinstance(s, str) and bool(re.fullmatch(r"(?:SNPP|N20):[1-9]\d*", s))
        ).all(),
        "Sensor-qualified orbit identity",
    )
    starts, ends = utc_times(frame.start_utc), utc_times(frame.end_utc)
    require(starts.notna().all() and ends.notna().all() and starts.lt(ends).all(), "Scan envelopes")
    shapes = np.asarray(geometries, dtype=object)
    require(
        shapes.shape == (len(frame),)
        and not shapely.is_missing(shapes).any()
        and shapely.is_valid(shapes).all(),
        "Aligned valid nominal-land geometry",
    )
    require(region is not None and shapely.is_valid(region) and region.area > 0, "Positive AOI")
    require(
        (shapely.area(shapely.difference(shapes, region)) <= max(0.05, region.area * 1e-8)).all(),
        "Support within AOI",
    )
    inside = classify_intervals(frame, day).eq("inside").to_numpy()
    indices = np.flatnonzero(inside & (shapely.area(shapes) > 0))
    order = indices[np.argsort(starts.iloc[indices].astype("int64").to_numpy(), kind="stable")]
    repeat = {float(h): [] for h in cuts}
    pairs = []
    for position, first in enumerate(order):
        for second in order[position + 1 :]:
            if frame.iloc[first].orbit_id == frame.iloc[second].orbit_id:
                continue
            gap = (starts.iloc[second].value - ends.iloc[first].value) / 3_600_000_000_000
            if gap < cuts.min():
                continue
            overlap = shapely.intersection(shapes[first], shapes[second])
            if overlap.area <= 0:
                continue
            pairs.append(
                {
                    "earlier_scan_id": frame.iloc[first].scan_id,
                    "later_scan_id": frame.iloc[second].scan_id,
                    "minimum_gap_hours": gap,
                    "overlap_area_m2": overlap.area,
                }
            )
            for cut in cuts:
                if gap >= cut:
                    repeat[float(cut)].append(overlap)
    return {
        cut: shapely.union_all(parts) if parts else shapely.GeometryCollection()
        for cut, parts in repeat.items()
    }, pd.DataFrame(pairs, columns=PAIR_COLUMNS)
