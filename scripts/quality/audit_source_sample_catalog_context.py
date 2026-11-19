"""Retained fit-role catalogue context around frozen source points; never labels or recall."""

import csv
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import numpy as np
from prepare_marmaris_native_pair import write
from pyproj import Transformer

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
NATIVE = BASE / "source_sample_native_summary_v1/20261119T175128Z_e277cfc3/readback.json"
SAMPLE = BASE / "source_sampling_review_v1/20261119T133150Z_f94ebe6e/readback.json"
CATALOG = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
COVER = BASE / "mersin_joint_reference_v1/20261118T140734Z_19b35a6d/readback.json"
PINS = {
    NATIVE: "bf56b8ed36b6a12ac5c2e9c36f8ba7235013854a79cd0f93a4aaed8e3da107a0",
    SAMPLE: "9647a69248ac158aad6f7a864b48bfad8eb61860be08ff3250f8dc643cd4d453",
    CATALOG: "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5",
    COVER: "20c458af72b4a77e69d9e4713acfe91bbeaaaac2322165fa6e2a4fe248bcf5bc",
}


def main():
    require(all(digest(p) == h for p, h in PINS.items()), "Pinned source and existing catalogue")
    sample, native, cover = [
        json.loads(p.read_text(encoding="utf-8")) for p in (SAMPLE, NATIVE, COVER)
    ]
    rows = {r["archive_row"]: r for r in sample["intake"]}
    measured = [r["archive_row"] for r in native["source_rows"] if r.get("sample_id")]
    require(len(measured) == 8, "Exactly the eight previously measured source rows")
    windows, wanted_days = {}, set()
    for row in measured:
        source = rows[row]
        day = datetime.fromisoformat(source["reported_date"]).replace(tzinfo=UTC)
        entries = [
            {
                "basis": "source_date_UTC_target_window",
                "begin": day,
                "end": day + timedelta(days=1),
                "left_closed": False,
            }
        ]
        entries += [
            {
                "basis": h["basis"] + "_next24h",
                "begin": datetime.fromisoformat(h["reported_time_utc"]),
                "end": datetime.fromisoformat(h["reported_time_utc"]) + timedelta(days=1),
                "left_closed": True,
            }
            for h in source["clock_hypotheses"]
        ]
        require(
            all(2018 <= t.year <= 2022 for w in entries for t in (w["begin"], w["end"])),
            "Fit-only intervals",
        )
        windows[row] = entries
        for w in entries:
            wanted_days.update({w["begin"].date().isoformat(), w["end"].date().isoformat()})
    # Filter year/day metadata before accessing any scientific values.
    candidates, ids = [], set()
    with CATALOG.open(encoding="utf-8-sig", newline="") as stream:
        for raw in csv.DictReader(stream):
            stamp = raw["detection_timestamp_utc"]
            if not 2018 <= int(stamp[:4]) <= 2022 or stamp[:10] not in wanted_days:
                continue
            if raw["source_sensor"] not in {"SNPP", "N20"}:
                continue
            require(raw["detection_id"] not in ids, "Unique retained catalogue identity")
            ids.add(raw["detection_id"])
            candidates.append(
                {
                    "detection_id": raw["detection_id"],
                    "time": datetime.fromisoformat(stamp),
                    "longitude": float(raw["longitude"]),
                    "latitude": float(raw["latitude"]),
                    "sensor": raw["source_sensor"],
                    "grid_id": raw["grid_id"],
                }
            )
    project = Transformer.from_crs(4326, 6933, always_xy=True)
    xx, yy = project.transform(
        [c["longitude"] for c in candidates], [c["latitude"] for c in candidates]
    )
    contexts = []
    for row in measured:
        x, y = project.transform(rows[row]["longitude"], rows[row]["latitude"])
        distance = np.hypot(np.asarray(xx) - x, np.asarray(yy) - y)
        for window in windows[row]:
            for radius in (250, 1000):
                hits = [
                    c
                    for c, d in zip(candidates, distance, strict=True)
                    if d <= radius
                    and (
                        c["time"] >= window["begin"]
                        if window["left_closed"]
                        else c["time"] > window["begin"]
                    )
                    and c["time"] <= window["end"]
                ]
                contexts.append(
                    {
                        "archive_row": row,
                        "basis": window["basis"],
                        "begin_utc": window["begin"].isoformat(),
                        "end_utc": window["end"].isoformat(),
                        "left_closed": window["left_closed"],
                        "right_closed": True,
                        "projected_radius_m": radius,
                        "catalogue_records": len(hits),
                        "catalogue_ids": sorted(h["detection_id"] for h in hits),
                        "first_catalogue_time_utc": min(
                            (h["time"] for h in hits), default=None
                        ).isoformat()
                        if hits
                        else None,
                    }
                )
    old_cover = {
        r["archive_row"]: r
        for r in cover["reference_units"]
        if 2018 <= int(r["year"]) <= 2022 and r["archive_row"] in measured
    }
    require(
        set(old_cover) == set(measured), "All eight in retained source-coordinate cover context"
    )
    for row, context in old_cover.items():
        require(
            context["grid_id"] in rows[row]["candidate_grid_ids"],
            "Same archived source point/cell context",
        )
    out = (
        BASE
        / "source_sample_catalog_context_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    result = {
        "scope": "eight_frozen_source_rows_retained_AOI_catalogue_and_historical_map_context_only",
        "contexts": contexts,
        "historical_CORINE_2018_source_point_context": old_cover,
        "catalogue_matching_not_physical_event_linkage": True,
        "catalogue_AOI_filtered_not_all_global_granules": True,
        "coordinates_or_clock_standard_resolved": False,
        "new_L_memberships": 0,
        "labels_created": False,
        "model_trained": False,
        "recall_or_false_archive_rate_estimated": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    write(out / "readback.json", result)
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))
    print("PASS existing catalogue context; no new downloads or labels")


if __name__ == "__main__":
    main()
