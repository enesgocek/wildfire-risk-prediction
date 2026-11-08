"""Separate Menderes locality context, catalogue groups and retained scan counts."""

import csv
import time
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd
from prepare_pu_calendar_sample import digest
from review_anamur_observation_windows import inspect_minutes
from review_manavgat_reported_starts import CATALOG, OBS
from review_pu_candidate_timeline import GRAPH
from review_three_province_start_context import CATALOG_SHA
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json

from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.observation_window import review_window, source_schedule
from wildfire_risk_prediction.observation_window_source import read_month_offline

DAY = "2023-07-10"
OUT = BASE / "menderes_hona_context_v1"
PRIOR = BASE / "izmir_july_event_context_v1/20261108T034852Z_fa5863e0/readback.json"
GRAPH_RECEIPT = ROOT / GRAPH / "review.json"
INPUTS = {
    ROOT / CATALOG: CATALOG_SHA,
    PRIOR: "2cddafd97bace89d7f6b763951d7fd3c2952af413ff73ae1efe2b98b9fa6d3b6",
    GRAPH_RECEIPT: "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e",
    OBS: "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14",
    OUT / "sources/eov_2001_hona.pdf": (
        "9678c6a68634e43c0f6a7a21118bcf34531b8e2af01e7d25675ee57040b5e53f"
    ),
}
PLACE_REFERENCES = {
    "develi": (27.16804, 38.20586),
    "tekeli": (27.18992, 38.18722),
}


def grouping_counts(graph, selection, pins):
    summaries = {}
    for scenario, identities in sorted(graph["artifact_sha256"].items()):
        path = ROOT / f"data/interim/event_grouping/{scenario}_assignments.csv"
        require(digest(path) == identities["assignments_sha256"], "Frozen assignment table")
        pins[path] = identities["assignments_sha256"]
        assignments = pd.read_csv(path, usecols=["detection_id", "cluster_id"])
        require(
            len(assignments) == graph["training_detection_count"]
            and assignments.detection_id.is_unique,
            "Unique training assignments",
        )
        hits = selection.merge(assignments, on="detection_id", how="left", validate="one_to_one")
        require(hits.cluster_id.notna().all(), "All selected detections assigned")
        summaries[scenario] = [
            {
                "selected_detections": len(group),
                "first_selected_utc": group.timestamp.min().isoformat(),
                "selected_grid_ids": sorted(group.grid_id.unique()),
            }
            for _, group in hits.groupby("cluster_id")
        ]
    require(len(summaries) == 9, "Nine reviewed grouping settings")
    return summaries


def scan_counts(catalogue, grids):
    master = read_json(OBS)
    schedule = source_schedule(DAY, set(master["missing_source_days"]))
    require(schedule.source_status.eq("available_training_packet").all(), "Three source packets")
    month = next(row for row in master["reports"] if row["month"] == DAY[:7])
    request = {d: set(grids) for d in schedule.source_nominal_day}
    packet = read_month_offline(ROOT, month, request, time.monotonic() + 120)
    scans = pd.concat(packet["frames"].values(), ignore_index=True)
    result = {}
    for grid in grids:
        selected, summary = review_window(scans.loc[scans.grid_id.eq(grid)], DAY, grid, schedule)
        actual = inspect_minutes(selected.loc[selected.window_classification.eq("inside")])
        expected = Counter(
            (r.source_sensor, r.timestamp.floor("min").isoformat())
            for r in catalogue.loc[catalogue.grid_id.eq(grid)].itertuples()
        )
        result[grid] = {
            "window": {**summary, "target": None},
            "same_sensor_minute_counts": actual == expected,
            "minutes": [
                {
                    "sensor": sensor,
                    "utc": utc,
                    "catalogue": expected[sensor, utc],
                    "scan_thermal_centers": actual[sensor, utc],
                }
                for sensor, utc in sorted(
                    actual.keys() | expected.keys(), key=lambda key: key[::-1]
                )
            ],
        }
    return result, packet


def main():
    pins = INPUTS.copy()
    require(all(digest(path) == expected for path, expected in pins.items()), "Frozen evidence")
    prior = read_json(PRIOR)["cases"]["menderes"]
    ((reported, anchors),) = prior["anchor_sensitivity_by_reported_onset_utc"].items()
    anchor = anchors["oglananasi_hgm"]["approximate_lon_lat"]
    next_day = (date.fromisoformat(DAY) + timedelta(days=1)).isoformat()
    with (ROOT / CATALOG).open(encoding="utf-8-sig", newline="") as stream:
        rows = [
            r
            for r in csv.DictReader(stream)
            if r["detection_timestamp_utc"].startswith((DAY, next_day))
        ]
    catalogue = training_detections(pd.DataFrame(rows))
    catalogue = catalogue.loc[
        catalogue.timestamp.gt(pd.Timestamp(DAY, tz="UTC"))
        & catalogue.timestamp.le(pd.Timestamp(next_day, tz="UTC"))
    ]
    lon, lat = anchor
    distances = GEOD.inv(
        [lon] * len(catalogue), [lat] * len(catalogue), catalogue.longitude, catalogue.latitude
    )[2]
    selection = catalogue.loc[(distances <= 5000) & catalogue.timestamp.ge(pd.Timestamp(reported))]
    require(len(selection) == 14, "Frozen 5 km review sample")
    first = selection.iloc[0]
    require(selection.timestamp.eq(first.timestamp).sum() == 1, "Unique first selected centre")
    grids = sorted(selection.grid_id.unique())
    groups = grouping_counts(read_json(GRAPH_RECEIPT), selection, pins)
    windows, packet = scan_counts(catalogue, grids)
    pins[Path(__file__).resolve()] = digest(Path(__file__))

    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    path = OUT / run / "readback.json"
    path.parent.mkdir(parents=True, exist_ok=False)
    write_json(
        path,
        {
            "input_sha256": {
                **{p.relative_to(ROOT).as_posix(): expected for p, expected in pins.items()},
                **packet["inputs"],
            },
            "nominal_inner_sha256": packet["inner"],
            "selected_count": len(selection),
            "first_selected_utc": first.timestamp.isoformat(),
            "first_selected_sensor": first.source_sensor,
            "first_selected_grid": first.grid_id,
            "distance_from_first_center_to_place_references_m": {
                name: GEOD.inv(first.longitude, first.latitude, *point)[2]
                for name, point in {"oglananasi_hgm": anchor, **PLACE_REFERENCES}.items()
            },
            "selected_rows_by_grid": dict(sorted(Counter(selection.grid_id).items())),
            "groupings": groups,
            "whole_cell_scan_comparison": windows,
            "original_ignition_verified": False,
            "target": None,
            "daily_observation_status": "unknown",
            "positive_label_permitted": False,
            "negative_label_permitted": False,
        },
    )
    print(path.relative_to(ROOT).as_posix(), digest(path))


if __name__ == "__main__":
    main()
