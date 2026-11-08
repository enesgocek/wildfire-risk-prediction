"""Compare six place references with the training grid and local detection catalogue."""

import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import pandas as pd
from prepare_pu_calendar_sample import digest
from review_manavgat_reported_starts import CATALOG, PARTS
from review_three_province_start_context import CATALOG_SHA, inspect_anchor
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json
from shapely.geometry import Point

from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import detection_windows

TIME_RECEIPT = "outputs/reports/dataset/public_fire_source_review_v1/20261108/readback.json"
INPUTS = {
    CATALOG: CATALOG_SHA,
    PARTS: "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9",
    TIME_RECEIPT: "300d0ef9e3ece1ce0e1bcfcf6a4e3a236d8d3db03808c59b9fb59f606146271c",
}
ANCHORS = {
    "milas_maya_yolu": (
        32635,
        {
            "bogazici_village": (27.58494, 37.20159),
            "maya_pier": (27 + 32 / 60 + 7 / 3600, 37 + 11 / 60 + 16 / 3600),
        },
    ),
    "milas_kemikler": (
        32635,
        {"airport_access_road": (27.672953, 37.235850), "kemikler_center": (27.656612, 37.194949)},
    ),
    "anamur_belensazak_approximate": (
        32636,
        {"belensazak_locality": (32.79535, 36.19931), "asagi_kukur_hgm": (32.775322, 36.199306)},
    ),
}


def inspect_anamur_grouping(rows, anchors, pins):
    lon, lat = anchors["belensazak_locality"]
    distances = GEOD.inv([lon] * len(rows), [lat] * len(rows), rows.longitude, rows.latitude)[2]
    nearby = rows.loc[distances <= 2000]
    result = {}
    for distance in (500, 1000, 2000):
        for hours in (24, 48, 72):
            scenario = f"d{distance}m_t{hours}h"
            name = f"data/interim/event_grouping/{scenario}_assignments.csv"
            pins[name] = digest(ROOT / name)
            assignments = pd.read_csv(ROOT / name)
            hits = assignments.loc[assignments.detection_id.isin(nearby.detection_id)]
            require(
                set(hits.detection_id) == set(nearby.detection_id) and hits.detection_id.is_unique,
                "Each nearby detection has one assignment",
            )
            cluster_sizes = []
            for _, cluster in assignments.loc[assignments.cluster_id.isin(hits.cluster_id)].groupby(
                "cluster_id"
            ):
                first = pd.to_datetime(cluster.timestamp, utc=True, format="ISO8601")
                cluster_sizes.append(
                    {
                        "members": len(cluster),
                        "first_detection_utc": first.min().isoformat(),
                        "first_grid_ids": sorted(
                            set(cluster.loc[first.eq(first.min()), "grid_id"])
                        ),
                    }
                )
            result[scenario] = cluster_sizes
    return {
        "nearby_detection_count": len(nearby),
        "nearby_detection_grid_ids": sorted(set(nearby.grid_id)),
        "exploratory_scenarios": result,
    }


def main():
    require(all(digest(ROOT / p) == h for p, h in INPUTS.items()), "Frozen local input bytes")
    source_times = read_json(ROOT / TIME_RECEIPT)["source_reported_utc_times"]
    times = pd.Series({key: source_times[key] for key in ANCHORS})
    windows = detection_windows(times)
    days = tuple(
        (stamp + timedelta(days=offset)).date().isoformat()
        for stamp in windows.prediction_timestamp_utc
        for offset in (0, 1, 2)
    )
    require(all(day.startswith("2023-07-") for day in days), "July 2023 only")
    with (ROOT / CATALOG).open(encoding="utf-8-sig", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["detection_timestamp_utc"].startswith(days)]
    catalogue = training_detections(pd.DataFrame(rows))
    parts = gpd.read_file(ROOT / PARTS)
    require(parts.grid_id.is_unique, "Unique grid geometry identities")
    grids = {epsg: parts.to_crs(epsg) for epsg in (32635, 32636)}
    pins = {**INPUTS, "producer": digest(Path(__file__))}
    cases = {}
    for key, (epsg, anchors) in ANCHORS.items():
        start = pd.Timestamp(times[key])
        t, end, edge = windows.loc[key]
        require(not edge and t < start <= end, "Valid training window")
        rows = catalogue.loc[
            catalogue.timestamp.gt(t) & catalogue.timestamp.le(end + timedelta(days=1))
        ]
        grid = grids[epsg]
        results = {}
        for label, coord in anchors.items():
            point = gpd.GeoSeries([Point(*coord)], crs=4326).to_crs(epsg).iloc[0]
            result = inspect_anchor(rows, coord, start, end)
            result["point_grid_ids"] = sorted(grid.loc[grid.geometry.covers(point), "grid_id"])
            result["intersected_grid_ids_within_1km"] = sorted(
                grid.loc[grid.geometry.intersects(point.buffer(1000)), "grid_id"]
            )
            results[label] = result
        left, right = anchors.values()
        cases[key] = {
            "reported_start_utc": start.isoformat(),
            "target_window_start_utc": t.isoformat(),
            "target_window_end_utc": end.isoformat(),
            "anchor_separation_m": GEOD.inv(*left, *right)[2],
            "anchors": results,
            "original_ignition_verified": False,
            "target": None,
        }
        if key == "anamur_belensazak_approximate":
            cases[key]["belensazak_2km_grouping"] = inspect_anamur_grouping(rows, anchors, pins)
    report = {
        "source_sha256": pins,
        "cases": cases,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
    }
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "july_2023_start_context_v1" / run / "readback.json"
    out.parent.mkdir(parents=True, exist_ok=False)
    write_json(out, report)
    print(out.relative_to(ROOT).as_posix(), digest(out))


if __name__ == "__main__":
    main()
