"""Screen seven published OGM start times with approximate, manually read map positions."""

import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import numpy as np
import pandas as pd
from prepare_pu_calendar_sample import digest
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json

from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.observation_window import review_window, source_schedule
from wildfire_risk_prediction.observation_window_source import read_month_offline
from wildfire_risk_prediction.target_admission import detection_windows

# Figure 2, page 6 at 140 dpi, 1158 x 1638. Axis label centers and symbol centers.
# Approximate map readings only. Figure symbols may be displaced or overlap.
LON_TICKS = [216, 297, 381, 465, 549, 634, 716, 802, 885, 970]
LAT_TICKS = [170, 222, 274, 327, 379, 431, 483, 536, 587, 640, 692, 744]
# Table 1, page 5 supplies start times separately from the first-response times.
STARTS = (
    ("2021-07-28T11:58", 593, 390),
    ("2021-07-28T16:00", 518, 441),
    ("2021-07-28T23:45", 852, 411),
    ("2021-07-29T01:30", 829, 487),
    ("2021-07-31T19:00", 916, 543),
    ("2021-08-02T13:00", 561, 378),
    ("2021-08-03T07:30", 713, 237),
)
RADII = (1000, 2000, 3000)
PDF_SHA = "08af0600d92e0640e7b263064cb6fa39ba1e23ddf31c91986dd326daea7e7bc6"
CATALOG = "data/interim/firms_combined_candidates_2018_2024.csv"
PARTS = "data/interim/grid_aoi_parts.geojson"
ASSIGNMENTS = "data/interim/event_grouping/d1000m_t48h_assignments.csv"
OBS = BASE / "observation_materialization_v1/20261014T145638Z_c0881064/accepted_readback.json"


def axis_fit(pixels, degrees):
    model = np.polyfit(pixels, degrees, 1)
    errors = [
        abs(np.polyval(np.polyfit(np.delete(pixels, i), np.delete(degrees, i), 1), x) - y)
        for i, (x, y) in enumerate(zip(pixels, degrees, strict=True))
    ]
    return model, float(max(errors))


def inspect_case_six(case, pins):
    obs_sha = "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14"
    require(digest(OBS) == obs_sha, "Frozen observation receipt")
    pins[OBS.relative_to(ROOT).as_posix()] = obs_sha
    master = read_json(OBS)
    day = case["prediction_utc"][:10]
    grids = set(case["scenarios"][0]["intersected_grid_ids"])
    schedule = source_schedule(day, set(master["missing_source_days"]))
    require(schedule.source_status.eq("available_training_packet").all(), "Three accepted days")
    month = next(r for r in master["reports"] if r["month"] == day[:7])
    packet = read_month_offline(
        ROOT, month, {d: grids for d in schedule.source_nominal_day}, time.monotonic() + 120
    )
    pins.update(packet["inputs"])
    scans = pd.concat(packet["frames"].values(), ignore_index=True)
    windows = []
    for grid in sorted(grids):
        _, summary = review_window(scans.loc[scans.grid_id.eq(grid)], day, grid, schedule)
        windows.append({**summary, "target": None})
    return {"case": case["case"], "source_inner_sha256": packet["inner"], "windows": windows}


def main():
    pins = {
        CATALOG: "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5",
        PARTS: "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9",
        ASSIGNMENTS: "a8d1c0dd4a6c5880cf15fbb2c4a35a4bc61e8f4a3f69836dcfcaec69d6d3fa56",
    }
    require(all(digest(ROOT / p) == h for p, h in pins.items()), "Frozen inputs")
    year = pd.read_csv(ROOT / CATALOG)
    # The existing combined source stores 2024 rows. Only 2021 enters the screen.
    detections = training_detections(
        year.loc[year.detection_timestamp_utc.str.startswith("2021-")].copy()
    )
    assignments = pd.read_csv(
        ROOT / ASSIGNMENTS, usecols=["detection_id", "timestamp", "cluster_id"]
    )
    require(assignments.detection_id.is_unique, "Unique exploratory assignments")
    assignments["timestamp"] = pd.to_datetime(assignments.timestamp, utc=True, format="ISO8601")
    component_starts = assignments.groupby("cluster_id").timestamp.min()
    detections = detections.merge(
        assignments, on=["detection_id", "timestamp"], validate="one_to_one", how="left"
    )
    require(detections.cluster_id.notna().all(), "Known exploratory component for every row")
    grids = gpd.read_file(ROOT / PARTS).to_crs(32636)
    require(grids.grid_id.is_unique, "Unique grid geometries")
    lon_fit, lon_error = axis_fit(LON_TICKS, 31 + np.arange(6, 43, 4) / 60)
    lat_fit, lat_error = axis_fit(LAT_TICKS, 37 + np.arange(4, -19, -2) / 60)
    times = pd.Series([x[0] for x in STARTS])
    times = pd.to_datetime(times).dt.tz_localize("Europe/Istanbul").dt.tz_convert("UTC")
    windows = detection_windows(times.map(lambda stamp: stamp.isoformat()))
    cases = []
    for i, (_, x, y) in enumerate(STARTS):
        lon, lat = float(np.polyval(lon_fit, x)), float(np.polyval(lat_fit, y))
        point = gpd.GeoSeries(gpd.points_from_xy([lon], [lat]), crs=4326).to_crs(32636).iloc[0]
        grid_ids = grids.loc[grids.geometry.covers(point), "grid_id"].tolist()
        require(len(grid_ids) <= 1, "Center grid ambiguity must be retained separately")
        start = times.iloc[i]
        t, end, edge = windows.iloc[i]
        require(not edge and t < start <= end, "Training start window")
        same_window = detections.loc[detections.timestamp.gt(t) & detections.timestamp.le(end)]
        nearest = same_window.assign(
            meters=GEOD.inv(
                np.full(len(same_window), lon),
                np.full(len(same_window), lat),
                same_window.longitude.to_numpy(),
                same_window.latitude.to_numpy(),
            )[2]
        )
        scenarios = []
        for radius in RADII:
            cells = sorted(grids.loc[grids.geometry.intersects(point.buffer(radius)), "grid_id"])
            nearby = nearest.loc[nearest.meters.le(radius)].sort_values(
                ["timestamp", "detection_id"]
            )
            after = nearby.loc[nearby.timestamp.ge(start)]
            groups = after.cluster_id.unique()
            scenarios.append(
                {
                    "radius_m": radius,
                    "intersected_grid_ids": cells,
                    "catalogue_rows_before_reported_start": len(nearby) - len(after),
                    "catalogue_rows_at_or_after_reported_start": len(after),
                    "earliest_at_or_after_utc": after.iloc[0].timestamp.isoformat()
                    if not after.empty
                    else None,
                    "after_rows_exploratory_components": len(groups),
                    "after_components_started_before_reported_start": int(
                        component_starts.loc[groups].lt(start).sum()
                    ),
                }
            )
        cases.append(
            {
                "case": i + 1,
                "reported_start_utc": start.isoformat(),
                "prediction_utc": t.isoformat(),
                "approximate_lon_lat": [lon, lat],
                "approximate_center_grid_ids": grid_ids,
                "scenarios": scenarios,
                "original_start_coordinate_verified": False,
                "target": None,
            }
        )

    observation = inspect_case_six(cases[5], pins)
    pins[Path(__file__).resolve().relative_to(ROOT).as_posix()] = digest(Path(__file__))
    out = (
        BASE
        / "manavgat_reported_starts_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "publication_doi": "10.3390/ijgi14020065",
        "publication_pdf_sha256": PDF_SHA,
        "source_sha256": pins,
        "axis_leave_one_out_max_error_degrees": {"lon": lon_error, "lat": lat_error},
        "cases": cases,
        "case_six_observation": observation,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
    }
    write_json(out / "readback.json", report)
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))


if __name__ == "__main__":
    main()
