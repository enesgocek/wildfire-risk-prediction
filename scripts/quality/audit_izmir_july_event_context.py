"""Compare dispatch, reported onset and VIIRS timing for four July 2023 cases."""

import csv
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from zoneinfo import ZoneInfo

import pandas as pd
from audit_izmir_dispatch_coverage import FOREST, INPUTS, SHRUB, WORKBOOK, workbook_records
from prepare_pu_calendar_sample import digest
from review_manavgat_reported_starts import CATALOG
from review_three_province_start_context import CATALOG_SHA, inspect_anchor
from run_stratified_cover_pilot import BASE, ROOT, write_json

from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require

LOCAL = ZoneInfo("Europe/Istanbul")
CASES = {
    "aliaga": (
        date(2023, 7, 10),
        "ALİAĞA",
        ("13:30", "13:45"),
        {"caltilidere_hgm": (27.035076, 38.852447), "kostem_beach": (27.006102, 38.859348)},
    ),
    "menderes": (
        date(2023, 7, 10),
        "MENDERES",
        ("14:00",),
        {
            "oglananasi_hgm": (27.224579, 38.239681),
            "oglananasi_map_alternative": (27.140629, 38.256691),
        },
    ),
    "kemalpasa": (
        date(2023, 7, 25),
        "KEMALPAŞA",
        ("14:06",),
        {"hamzababa_hgm": (27.708889, 38.419338)},
    ),
    "menemen": (
        date(2023, 7, 25),
        "MENEMEN",
        ("14:18",),
        {"ayvacik_map": (27.19062, 38.61254)},
    ),
}


def dispatch_times(indices):
    """Return local crew-departure times for selected sheet rows."""
    with ZipFile(WORKBOOK) as archive:
        strings = [
            "".join(part.text or "" for part in item.findall(".//{*}t"))
            for item in ET.fromstring(archive.read("xl/sharedStrings.xml"))
        ]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    selected_cells = {f"U{i}" for i in (1, *indices)}
    cells = {
        cell.get("r"): strings[int(cell.findtext("{*}v"))]
        for cell in sheet.findall("./{*}sheetData/{*}row/{*}c")
        if cell.get("r") in selected_cells and cell.get("t") == "s"
    }
    require(cells["U1"] == "EKIPLERİN_CIKIS_SAATI", "Crew departure header")
    return {i: time.fromisoformat(cells[f"U{i}"]) for i in indices}


def main():
    pins = {
        WORKBOOK: INPUTS[WORKBOOK],
        ROOT / CATALOG: CATALOG_SHA,
        Path(__file__).resolve().with_name("audit_izmir_dispatch_coverage.py"): (
            "872eac2438012fe8bbcc06dec30aed65f114958e0a0e92023a01edb26bc74ab6"
        ),
    }
    require(all(digest(path) == sha for path, sha in pins.items()), "Frozen workbook and catalogue")
    scope = {(day, district): key for key, (day, district, _, _) in CASES.items()}
    day_counts, matching = Counter(), {}
    for i, (day, kind, district) in enumerate(workbook_records(), 2):
        key = scope.get((day, district))
        if key is not None:
            day_counts[key] += 1
            if kind in (FOREST, SHRUB):
                require(key not in matching, "One selected-category dispatch candidate per case")
                matching[key] = i, kind
    require(matching.keys() == CASES.keys(), "Dispatch context for each case")
    departures = dispatch_times([i for i, _ in matching.values()])

    days = {day + timedelta(days=offset) for day, _, _, _ in CASES.values() for offset in (0, 1)}
    date_prefixes = tuple(day.isoformat() for day in sorted(days))
    with (ROOT / CATALOG).open(encoding="utf-8-sig", newline="") as stream:
        rows = [
            r
            for r in csv.DictReader(stream)
            if r["detection_timestamp_utc"].startswith(date_prefixes)
        ]
    catalogue = training_detections(pd.DataFrame(rows))
    results = {}
    for key, (day, district, clocks, anchors) in CASES.items():
        row, kind = matching[key]
        departure = datetime.combine(day, departures[row], LOCAL)
        begin = datetime.combine(day, time.min, UTC)
        end = begin + timedelta(days=1)
        same = catalogue.loc[
            catalogue.timestamp.gt(begin) & catalogue.timestamp.le(end + timedelta(days=1))
        ]
        reported = [datetime.combine(day, time.fromisoformat(clock), LOCAL) for clock in clocks]
        results[key] = {
            "day": day.isoformat(),
            "district": district,
            "district_day_all_dispatch_rows": day_counts[key],
            "crew_departure_local": departure.isoformat(),
            "dispatch_category": kind,
            "reported_onset_local": [stamp.isoformat() for stamp in reported],
            "dispatch_minus_reported_onset_minutes": [
                int((departure - stamp).total_seconds() / 60) for stamp in reported
            ],
            "anchor_sensitivity_by_reported_onset_utc": {
                stamp.astimezone(UTC).isoformat(): {
                    name: inspect_anchor(same, coord, stamp, end) for name, coord in anchors.items()
                }
                for stamp in reported
            },
            "original_ignition_verified": False,
            "target": None,
        }
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "izmir_july_event_context_v1" / run / "readback.json"
    out.parent.mkdir(parents=True, exist_ok=False)
    pins[Path(__file__).resolve()] = digest(Path(__file__))
    write_json(
        out,
        {
            "source_sha256": {p.relative_to(ROOT).as_posix(): value for p, value in pins.items()},
            "kemalpasa_menemen_anchor_distance_m": GEOD.inv(
                *CASES["kemalpasa"][3]["hamzababa_hgm"], *CASES["menemen"][3]["ayvacik_map"]
            )[2],
            "cases": results,
            "daily_observation_status": "unknown",
            "positive_label_permitted": False,
            "negative_label_permitted": False,
        },
    )
    print(out.relative_to(ROOT).as_posix(), digest(out))


if __name__ == "__main__":
    main()
