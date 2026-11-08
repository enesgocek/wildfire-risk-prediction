"""Review other-day FIRMS detections near the July 2023 Menderes case."""

import csv
import io
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from prepare_pu_calendar_sample import digest
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json

from wildfire_risk_prediction.event_review import GEOD
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.firms_refresh import FIELDS, canonical

OUT = BASE / "menderes_recurrence_v1"
PRIOR = BASE / "menderes_hona_context_v1/20261108T035543Z_f2cfcec3/readback.json"
REFRESH = ROOT / "outputs/verification/firms_refresh_2026-10-21/received"
DELIVERIES = {
    "SNPP": (REFRESH / "SNPP/DL_FIRE_SV-C2_828284.zip", "fire_archive_SV-C2_828284.csv"),
    "N20": (REFRESH / "NOAA20/DL_FIRE_J1V-C2_828274.zip", "fire_archive_J1V-C2_828274.csv"),
}
MUNICIPAL = {
    "2019-08-04": OUT / "sources/izmir_dispatch_2019.xlsx",
    "2022-04-21": OUT / "sources/izmir_dispatch_2022.xlsx",
}
PINS = {
    PRIOR: "05b59ebb981cce0f367df145f3a663f54f627662ab407124a506dcfc42e28b92",
    DELIVERIES["SNPP"][0]: "f9506c5eb5221aeb7576285561538b6a84fb8c582cb1dad1643313eb06344585",
    DELIVERIES["N20"][0]: "067a587555dae7217d38bc93b989041dc0630e43f06d4c469ca93cef80cb0550",
    MUNICIPAL["2019-08-04"]: "de4920a20aaf98d25da1b560e1abf1478f8a82ff3a11c2dc9fcd6c29b16dcdf5",
    MUNICIPAL["2022-04-21"]: "b494a6e9f2eba1e47543470620ef1f83228b725d3839f80faaef1f53ed051612",
}
DAY = "2023-07-10"
RADII = (100, 250, 500, 1000)
CENTERS = {
    "south_first": (27.20077, 38.22447),
    "north_east": (27.23770, 38.26095),
    "north_west": (27.23373, 38.26072),
}


def municipal_context(path, day):
    with ZipFile(path) as archive:
        strings = [
            "".join(part.text or "" for part in item.findall(".//{*}t"))
            for item in ET.fromstring(archive.read("xl/sharedStrings.xml"))
        ]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))

    def value(cell):
        raw = cell.findtext("{*}v")
        return strings[int(raw)] if cell.get("t") == "s" else raw

    serial = str((date.fromisoformat(day) - date(1899, 12, 30)).days)
    total, matches = 0, []
    for row in sheet.findall("./{*}sheetData/{*}row"):
        i = row.get("r")
        cells = {cell.get("r"): cell for cell in row}
        if i == "1":
            require(
                [value(cells[c + i]) for c in ("A", "B", "Q", "V")]
                == ["TARIH", "YANGIN_TURU", "CIKIS_SAATI", "ILCE"],
                "Expected source columns",
            )
        elif f"A{i}" in cells and value(cells[f"A{i}"]) == serial:
            total += 1
            if f"V{i}" in cells and value(cells[f"V{i}"]) == "MENDERES":
                matches.append(
                    {
                        "category": value(cells[f"B{i}"]),
                        "crew_departure_local": value(cells[f"Q{i}"]),
                    }
                )
    require(total > 0, "Source contains the requested calendar date")
    return {"file_rows_on_date": total, "menderes_rows": matches}


def load_nearby():
    rows, delivery_counts = [], {}
    for sensor, (path, member) in DELIVERIES.items():
        with ZipFile(path) as archive, archive.open(member) as data:
            reader = csv.DictReader(io.TextIOWrapper(data, encoding="utf-8-sig", newline=""))
            require(tuple(reader.fieldnames) == FIELDS, "FIRMS archive fields")
            count = 0
            for row in reader:
                day = row["acq_date"]
                require("2018-01-01" <= day <= "2023-12-31", "Training period only")
                count += 1
                lon, lat = float(row["longitude"]), float(row["latitude"])
                # This rectangle contains every 1 km geodesic search circle.
                if 27.18 <= lon <= 27.26 and 38.20 <= lat <= 38.28:
                    rows.append(
                        {
                            "sensor": sensor,
                            "day": day,
                            "clock_utc": canonical("acq_time", row["acq_time"]),
                            "lon_lat": [lon, lat],
                            "type": row["type"],
                            "confidence": row["confidence"],
                        }
                    )
            delivery_counts[sensor] = count
    return rows, delivery_counts


def summarize(rows):
    return {
        "radial_counts": [
            {
                "radius_m": radius,
                "event_day_rows": sum(r["day"] == DAY for r in rows if r["distance_m"] <= radius),
                "other_day_rows": sum(r["day"] != DAY for r in rows if r["distance_m"] <= radius),
                "other_dates": sorted(
                    {r["day"] for r in rows if r["distance_m"] <= radius and r["day"] != DAY}
                ),
            }
            for radius in RADII
        ],
        "other_day_type_counts": dict(Counter(r["type"] for r in rows if r["day"] != DAY)),
        "other_day_records": [r for r in rows if r["day"] != DAY],
        "same_day_confidence_counts": dict(
            Counter(r["confidence"] for r in rows if r["day"] == DAY)
        ),
    }


def main():
    require(all(digest(path) == sha for path, sha in PINS.items()), "Frozen sources")
    prior = read_json(PRIOR)
    rows, delivery_counts = load_nearby()
    require(delivery_counts == {"SNPP": 230286, "N20": 232892}, "Accepted delivery counts")
    contexts = {}
    for label, (lon, lat) in CENTERS.items():
        records = [{**row, "distance_m": GEOD.inv(lon, lat, *row["lon_lat"])[2]} for row in rows]
        records = sorted(
            (row for row in records if row["distance_m"] <= max(RADII)),
            key=lambda row: (row["day"], row["clock_utc"], row["distance_m"]),
        )
        self_rows = [row for row in records if row["distance_m"] == 0 and row["day"] == DAY]
        expected = ("N20", "1103", "n") if label == "south_first" else ("SNPP", "1154", "h")
        require(
            [(r["sensor"], r["clock_utc"], r["confidence"]) for r in self_rows] == [expected]
            and self_rows[0]["type"] == "0",
            "Exact review centre identity",
        )
        contexts[label] = summarize(records)
    require(prior["selected_count"] == 14 and prior["target"] is None, "Frozen prior case")
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    output = OUT / run / "readback.json"
    output.parent.mkdir(parents=True, exist_ok=False)
    write_json(
        output,
        {
            "source_sha256": {
                **{path.relative_to(ROOT).as_posix(): h for path, h in PINS.items()},
                Path(__file__).resolve().relative_to(ROOT).as_posix(): digest(Path(__file__)),
            },
            "delivery_records": delivery_counts,
            "per_center": contexts,
            "municipal": {day: municipal_context(path, day) for day, path in MUNICIPAL.items()},
            "target": None,
            "daily_observation_status": "unknown",
            "positive_label_permitted": False,
            "negative_label_permitted": False,
        },
    )
    print(output.relative_to(ROOT).as_posix(), digest(output))


if __name__ == "__main__":
    main()
