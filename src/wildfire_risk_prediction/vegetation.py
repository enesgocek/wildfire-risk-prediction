"""Past-image vegetation contracts and daily as-of selection without labels."""

from datetime import timedelta

import numpy as np
import pandas as pd

SOURCE = "LANDSAT/LC08/C02/T1_L2"
VERSION = "landsat_seasonal_window_v1"
WINDOWS = (16, 30, 60)
QA_EXCLUDED_MASK = 191
INDEX_FIELDS = ["ndvi_median_mean", "ndmi_median_mean"]
AGE_FIELDS = ["latest_pixel_age_mean_days", "median_pixel_age_mean_days"]


def prediction_time(value, training_only=False):
    t = pd.Timestamp(value)
    if pd.isna(t):
        raise ValueError("Prediction time missing")
    t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    if t.time().isoformat() != "00:00:00" or not 2018 <= t.year <= (
        2023 if training_only else 2024
    ):
        raise ValueError("Prediction must be midnight in the allowed development years")
    return t.to_pydatetime()


def validate_window(target, window_days, source_times):
    t = prediction_time(target)
    if type(window_days) is not int or window_days not in WINDOWS:
        raise ValueError("Vegetation window must be 16, 30 or 60 days")
    start = t - timedelta(days=window_days)
    for value in source_times:
        time = pd.Timestamp(value)
        if pd.isna(time) or time.tzinfo is None or not start <= time < t:
            raise ValueError("Source acquisition outside the strict past window")
    return start, t


def indexed_image(image, ee, target):
    """EE graph matching the declared reflectance/QA policy; add valid-pixel age."""
    reflectance = image.select(["SR_B4", "SR_B5", "SR_B6"]).multiply(0.0000275).subtract(0.2)
    red, nir, swir = [reflectance.select(i) for i in (0, 1, 2)]
    valid = (
        image.select("QA_PIXEL")
        .bitwiseAnd(QA_EXCLUDED_MASK)
        .eq(0)
        .And(image.select("QA_RADSAT").eq(0))
        .And(reflectance.gte(0).And(reflectance.lte(1)).reduce(ee.Reducer.min()))
        .And(nir.add(red).gt(0))
        .And(nir.add(swir).gt(0))
    )
    ndvi = nir.subtract(red).divide(nir.add(red)).rename("ndvi")
    ndmi = nir.subtract(swir).divide(nir.add(swir)).rename("ndmi")
    age = (
        ee.Image.constant(
            ee.Date(target.isoformat()).difference(ee.Date(image.get("system:time_start")), "day")
        )
        .rename("age_days")
        .toFloat()
    )
    return (
        ndvi.addBands(ndmi)
        .addBands(age)
        .updateMask(valid)
        .copyProperties(image, ["system:time_start"])
    )


def summary_row(properties, area_m2, target, window_days):
    start, end = validate_window(target, window_days, [])
    area = properties.get("vegetation_support_m2") or 0.0
    if not np.isfinite(area) or area < 0 or not np.isfinite(area_m2) or area_m2 <= 0:
        raise ValueError("Vegetation support or AOI area")
    names = INDEX_FIELDS + ["valid_observation_count_mean"] + AGE_FIELDS
    integrals = [
        "ndvi_m2",
        "ndmi_m2",
        "observation_count_m2",
        "latest_age_days_m2",
        "median_age_days_m2",
    ]
    row = {
        "grid_id": properties["grid_id"],
        "snapshot_cutoff_utc": end.isoformat(),
        "window_days": window_days,
        "window_start_utc": start.isoformat(),
        "valid_area_m2": float(area),
        "aoi_area_m2": float(area_m2),
        "support_to_aoi_ratio": float(area / area_m2),
        "available_at": None,
        "usage": "retrospective_candidate_only",
        "processing_version": VERSION,
    }
    for name, integral in zip(names, integrals, strict=True):
        value = properties.get(integral)
        if area and (value is None or not np.isfinite(value)):
            raise ValueError("Missing vegetation integral")
        if not area and value not in (None, 0):
            raise ValueError("Vegetation value without support")
        row[name] = float(value / area) if area else np.nan
    if area:
        if (
            any(abs(row[name]) > 1 + 1e-7 for name in INDEX_FIELDS)
            or row["valid_observation_count_mean"] < 1 - 1e-7
        ):
            raise ValueError("Vegetation index/count bounds")
        if not (0 <= row[AGE_FIELDS[0]] <= row[AGE_FIELDS[1]] <= window_days + 1e-7):
            raise ValueError("Vegetation age bounds")
    return row


def as_of_snapshots(
    snapshots,
    grid_ids,
    prediction_dates,
    window_days,
    max_snapshot_age_days=8,
    mode="retrospective",
):
    """Carry a previous snapshot with explicit age; never backfill or invent availability.

    One window/version per input. In operational mode, recorded available_at
    must be known and precede T; that mode alone does not prove source provenance.
    """
    if mode not in {"retrospective", "operational"}:
        raise ValueError("Unknown vegetation selection mode")
    if (
        type(window_days) is not int
        or window_days not in WINDOWS
        or type(max_snapshot_age_days) is not int
    ):
        raise ValueError("Invalid snapshot policy")
    if not 0 <= max_snapshot_age_days <= 30:
        raise ValueError("Snapshot age limit must be 0–30 days")
    ids = list(grid_ids)
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Grid identities must be nonempty and unique")
    frame = snapshots.copy()
    required = [
        "grid_id",
        "snapshot_cutoff_utc",
        "window_start_utc",
        "window_days",
        "available_at",
        "valid_area_m2",
        "support_to_aoi_ratio",
        "source_acquisition_latest_utc",
        "processing_version",
        *INDEX_FIELDS,
        *AGE_FIELDS,
    ]
    if set(required) - set(frame):
        raise ValueError("Missing snapshot provenance/values")
    if (
        not frame.window_days.eq(window_days).all()
        or not frame.processing_version.eq(VERSION).all()
    ):
        raise ValueError("Mixed window or version")
    if not set(frame.grid_id) <= set(ids):
        raise ValueError("Unknown snapshot grids")
    frame["cutoff"] = pd.to_datetime(frame.snapshot_cutoff_utc, utc=True)
    frame["start"] = pd.to_datetime(frame.window_start_utc, utc=True)
    frame["acquisition"] = pd.to_datetime(frame.source_acquisition_latest_utc, utc=True)
    frame["release"] = pd.to_datetime(frame.available_at, utc=True)
    expected_starts = [
        prediction_time(value) - timedelta(days=window_days) for value in frame.cutoff
    ]
    supported = frame.valid_area_m2.gt(0)
    if (
        frame.cutoff.isna().any()
        or frame.start.isna().any()
        or (frame.start != pd.to_datetime(expected_starts, utc=True)).any()
        or (supported & frame.acquisition.isna()).any()
        or (
            frame.acquisition.notna()
            & ((frame.acquisition >= frame.cutoff) | (frame.acquisition < frame.start))
        ).any()
        or frame.duplicated(["grid_id", "cutoff"]).any()
    ):
        raise ValueError("Invalid or duplicate snapshot times")
    if (
        not np.isfinite(frame.valid_area_m2).all()
        or frame.valid_area_m2.lt(0).any()
        or not np.isfinite(frame.support_to_aoi_ratio).all()
        or frame.support_to_aoi_ratio.lt(0).any()
        or not frame.loc[supported, INDEX_FIELDS + AGE_FIELDS].map(np.isfinite).all().all()
        or frame.loc[supported, INDEX_FIELDS].abs().gt(1 + 1e-7).any().any()
        or frame.loc[supported, AGE_FIELDS[0]].lt(0).any()
        or (frame.loc[supported, AGE_FIELDS[0]] > frame.loc[supported, AGE_FIELDS[1]]).any()
        or frame.loc[supported, AGE_FIELDS[1]].gt(window_days + 1e-7).any()
        or frame.loc[~supported, INDEX_FIELDS + AGE_FIELDS].notna().any().any()
    ):
        raise ValueError("Invalid snapshot values or missingness")
    if (frame.release.notna() & (frame.release < frame.acquisition)).any():
        raise ValueError("Availability predates acquisition")
    results = []
    targets = [prediction_time(d) for d in prediction_dates]
    if len(targets) != len(set(targets)):
        raise ValueError("Duplicate prediction dates")
    for t in sorted(targets):
        usable = frame[
            (frame.cutoff <= t)
            & (frame.cutoff >= t - timedelta(days=max_snapshot_age_days))
            & (frame.valid_area_m2 > 0)
        ].copy()
        if mode == "operational":
            usable = usable[usable.release.notna() & (usable.release <= t)]
        picked = usable.sort_values("cutoff").groupby("grid_id").tail(1).set_index("grid_id")
        for grid_id in ids:
            row = {
                "grid_id": grid_id,
                "prediction_timestamp_utc": t.isoformat(),
                "snapshot_cutoff_utc": None,
                "snapshot_age_days": np.nan,
                "vegetation_present": False,
                "window_days": window_days,
                "support_to_aoi_ratio": np.nan,
                "available_at": None,
                "selection_mode": mode,
                **{f: np.nan for f in INDEX_FIELDS + AGE_FIELDS},
            }
            if grid_id in picked.index:
                saved = picked.loc[grid_id]
                row.update(
                    {
                        "snapshot_cutoff_utc": saved.cutoff.isoformat(),
                        "snapshot_age_days": (t - saved.cutoff.to_pydatetime()).total_seconds()
                        / 86400,
                        "vegetation_present": True,
                        "support_to_aoi_ratio": saved.support_to_aoi_ratio,
                        "available_at": saved.available_at,
                        **{f: saved[f] for f in INDEX_FIELDS},
                    }
                )
                # Pixel ages are relative to the source cutoff; advance them to prediction T.
                for name in AGE_FIELDS:
                    row[name] = saved[name] + row["snapshot_age_days"]
            results.append(row)
    return pd.DataFrame(results)
