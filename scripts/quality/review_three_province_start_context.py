"""Compare published start times with VIIRS near named places in three provinces."""

import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd
from prepare_pu_calendar_sample import digest
from review_manavgat_reported_starts import CATALOG
from run_stratified_cover_pilot import BASE, ROOT, write_json

from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import detection_windows

# These points describe a village, a study area, a shore or a locality.
# They are deliberately retained as separate spatial hypotheses for the same event.
CASES = {
    "tirazli_2019": (
        "2019-08-18T13:00",
        {
            "village": (27.0612, 38.3198),
            "study_area": (27 + 19.27 / 3600, 38 + 14 / 60 + 59.75 / 3600),
        },
    ),
    "marmaris_2022": (
        "2022-06-21T20:02",
        {
            "shore_a": (28 + 3.100 / 60, 36 + 52.840 / 60),
            "shore_b": (28 + 3.340 / 60, 36 + 52.660 / 60),
        },
    ),
    "gulnar_2022": (
        "2022-09-07T07:13",
        {"karadere_locality": (33.56937, 36.20586), "buyukeceli_center": (33.5575259, 36.1693683)},
    ),
}
RADII = (2000, 5000, 10000)
CATALOG_SHA = "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5"


def inspect_anchor(rows, anchor, start, end):
    lon, lat = anchor
    distances = GEOD.inv([lon] * len(rows), [lat] * len(rows), rows.longitude, rows.latitude)[2]
    counts = []
    for radius in RADII:
        nearby = rows.loc[distances <= radius]
        after = nearby.loc[nearby.timestamp.ge(start) & nearby.timestamp.le(end)]
        following = nearby.loc[nearby.timestamp.gt(end)]
        counts.append(
            {
                "radius_m": radius,
                "before_reported_start_same_utc_day": int(nearby.timestamp.lt(start).sum()),
                "at_or_after_start_same_utc_window": len(after),
                "following_utc_window": len(following),
                "first_same_window_utc": after.timestamp.min().isoformat() if len(after) else None,
                "first_following_window_utc": following.timestamp.min().isoformat()
                if len(following)
                else None,
            }
        )
    return {"approximate_lon_lat": list(anchor), "radii": counts}


def main():
    source = ROOT / CATALOG
    require(digest(source) == CATALOG_SHA, "Frozen source catalogue")
    starts = pd.to_datetime(pd.Series({key: value[0] for key, value in CASES.items()}))
    starts = starts.dt.tz_localize("Europe/Istanbul").dt.tz_convert("UTC")
    windows = detection_windows(starts.map(lambda stamp: stamp.isoformat()))
    days = tuple(
        (t + timedelta(days=offset)).date().isoformat()
        for t in windows.prediction_timestamp_utc
        for offset in (0, 1, 2)
    )
    require(all(day.startswith(("2019-", "2022-")) for day in days), "Training dates only")
    with source.open(encoding="utf-8-sig", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["detection_timestamp_utc"].startswith(days)]
    catalogue = training_detections(pd.DataFrame(rows))
    cases = {}
    for key, (_, anchors) in CASES.items():
        start = starts.loc[key]
        t, end, edge = windows.loc[key]
        require(not edge and t < start <= end, "Declared event timing")
        subset = catalogue.loc[
            catalogue.timestamp.gt(t) & catalogue.timestamp.le(end + timedelta(days=1))
        ]
        left, right = anchors.values()
        cases[key] = {
            "reported_start_utc": start.isoformat(),
            "target_window_start_utc": t.isoformat(),
            "target_window_end_utc": end.isoformat(),
            "anchor_separation_m": GEOD.inv(*left, *right)[2],
            "anchors": {
                label: inspect_anchor(subset, coords, start, end)
                for label, coords in anchors.items()
            },
            "original_ignition_verified": False,
            "target": None,
        }
    report = {
        "source_sha256": {
            CATALOG: CATALOG_SHA,
            Path(__file__).resolve().relative_to(ROOT).as_posix(): digest(Path(__file__)),
        },
        "cases": cases,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
    }
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "three_province_start_context_v1" / run
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "readback.json", report)
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))


if __name__ == "__main__":
    main()
