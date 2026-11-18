"""Bind public timeline semantics to two archive rows without assigning ignition roles."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pandas as pd
from audit_mersin_open_incidents import ARCHIVE, CATALOG, GEOD, PINS, ROOT, read_incidents
from audit_stage_one_selection import verify

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import detection_windows

SOURCES = ROOT / (
    "outputs/reports/dataset/gulnar_public_timeline_sources_v1/"
    "20261118T202337Z_1a001542/readback.json"
)
NOTES = ROOT / (
    "outputs/reports/dataset/gulnar_researcher_cover_notes_v1/"
    "20261118T153604Z_6db68bee/readback.json"
)


def main():
    verify(SOURCES, "1f515069670f5a412d400eaf8c93ee9491896778797c1ef3280cfdf32787f288")
    verify(NOTES, "b4a611863afa21b0970fa02eee4511ebf232dd0310aecde45fa6993973f26a50")
    for path in (ARCHIVE, CATALOG):
        verify(path, PINS[path])
    snapshots = json.loads(SOURCES.read_bytes())["sources"]
    for source in snapshots:
        if "path" in source:
            verify(ROOT / source["path"], source["sha256"])
    events, _ = read_incidents()
    records = events.loc[["WF1578", "WF1579"]]
    require(records.date.map(str).eq("2022-09-07").all(), "Two fixed case rows")
    require(
        records.ignition_hour.map(lambda h: round(Decimal(h) * 60)).eq(433).all(),
        "Both archive rows state 07:13",
    )
    a, b = records.itertuples()
    _, _, distance = GEOD.inv(
        float(a.longitude), float(a.latitude), float(b.longitude), float(b.latitude)
    )
    clocks = [
        ("municipality_dispatch", "reported_notification", "07:12"),
        ("ministry", "reported_start", "07:13"),
        ("ministry", "reported_first_response", "07:20"),
        ("municipality_followup", "approximate_start_in_followup", "07:30"),
    ]
    timeline = []
    for source, meaning, clock in clocks:
        for zone in ("Europe/Istanbul", "UTC"):
            stamp = pd.Timestamp(f"2022-09-07T{clock}:00", tz=zone).tz_convert("UTC")
            window = detection_windows(pd.Series([stamp.isoformat()]))
            timeline.append(
                {
                    "source": source,
                    "time_meaning": meaning,
                    "clock": clock,
                    "if_source_zone": zone,
                    "utc": stamp.isoformat(),
                    "prediction_timestamp_utc": window.prediction_timestamp_utc.iloc[0].isoformat(),
                }
            )
    require(
        {r["prediction_timestamp_utc"] for r in timeline} == {"2022-09-07T00:00:00+00:00"},
        "All eight clock/meaning scenarios have the same target day",
    )
    catalogue = pd.read_csv(CATALOG)
    catalogue = catalogue.loc[
        catalogue.detection_timestamp_utc.str.startswith(("2022-09-06", "2022-09-07", "2022-09-08"))
    ].copy()
    times = pd.to_datetime(catalogue.detection_timestamp_utc, utc=True, format="ISO8601")
    require(times.dt.year.eq(2022).all(), "Training-only catalogue context")
    begin, end = pd.Timestamp("2022-09-07T04:13:00Z"), pd.Timestamp("2022-09-08T00:00:00Z")
    previous_begin = pd.Timestamp("2022-09-06T04:13:00Z")
    local = []
    for key, event in records.iterrows():
        _, _, distances = GEOD.inv(
            [float(event.longitude)] * len(catalogue),
            [float(event.latitude)] * len(catalogue),
            catalogue.longitude.to_numpy(),
            catalogue.latitude.to_numpy(),
        )
        for radius in (250, 1000):
            previous = (distances <= radius) & times.gt(previous_begin) & times.le(begin)
            selected = catalogue.loc[(distances <= radius) & times.gt(begin) & times.le(end)].copy()
            selected["utc"] = times.loc[selected.index]
            selected = selected.sort_values("utc")
            local.append(
                {
                    "archive_row": key,
                    "radius_m": radius,
                    "after_reported_local_start_same_target_day_count": len(selected),
                    "previous_24h_count": int(previous.sum()),
                    "first_catalogue_utc": selected.utc.iloc[0].isoformat()
                    if len(selected)
                    else None,
                    "first_detection_id": selected.detection_id.iloc[0] if len(selected) else None,
                }
            )
    result = {
        "reported_point_separation_m": distance,
        "timeline": timeline,
        "catalogue_context": local,
        "source_snapshots": snapshots,
        "rendered_map_sha256": {p.name: digest(p) for p in SOURCES.parent.glob("map_page-*.png")},
        "source_receipts_sha256": {str(p.relative_to(ROOT)): digest(p) for p in (SOURCES, NOTES)},
        "archive_sha256": PINS[ARCHIVE],
        "catalogue_sha256": PINS[CATALOG],
        "archive_rows": list(records.index),
        "original_ignition_point_verified": False,
        "row_roles": {key: "start_or_spread_unresolved" for key in records.index},
        "record_merging_performed": False,
        "labels_created": False,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
    }
    out = (
        ROOT
        / "outputs/reports/dataset/gulnar_start_context_v1"
        / (f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}")
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Timeline result roundtrip")
    print(json.dumps({"point_separation_m": distance, "catalogue_context": local}, indent=2))
    print(path.relative_to(ROOT), digest(path))


if __name__ == "__main__":
    main()
