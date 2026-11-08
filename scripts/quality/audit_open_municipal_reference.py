"""Audit İzmir dispatch coverage and the public location bound for one Urla case."""

import csv
import hashlib
import json
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from math import floor
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from wildfire_risk_prediction.event_review import training_detections

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset/open_municipal_reference_v1"
SOURCES = {
    2019: "de4920a20aaf98d25da1b560e1abf1478f8a82ff3a11c2dc9fcd6c29b16dcdf5",
    2020: "c02de622c0fee519a6b1deda0876cd66f4cd7d733ab952d226854f26092a5381",
    2021: "cd550d9078966093ca1acfa767fe82d83ff3728e8d42d33c4c224bb23e33e804",
    2022: "b494a6e9f2eba1e47543470620ef1f83228b725d3839f80faaef1f53ed051612",
}
FIELDS = {"A": "TARIH", "B": "YANGIN_TURU", "Q": "CIKIS_SAATI", "V": "ILCE"}
FOREST = "ORMAN/FİDANLIK"
SHRUB = "MAKİLİK/ÇALI"
URLA_DAY = date(2022, 6, 9)
SPATIAL_SOURCES = {
    BASE / "sources/kuscular_boundary.json": (
        "516af639bcf80ca377dcae464b196b8b766378c70a4cfa8515007b7f203d3029"
    ),
    BASE / "sources/urla_district.json": (
        "b5ae661be83b3f76c5a473c7c5ba47b129dd509673d5f6e012ac166f15a3f5ac"
    ),
    ROOT / "data/interim/grid_aoi_parts.geojson": (
        "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9"
    ),
    ROOT / "data/interim/firms_combined_candidates_2018_2024.csv": (
        "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5"
    ),
}


def workbook_summary(path, year, expected_hash):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
        raise ValueError("Unexpected workbook revision")

    with ZipFile(path) as book:
        workbook = ET.fromstring(book.read("xl/workbook.xml"))
        properties = workbook.find("{*}workbookPr")
        if len(workbook.findall(".//{*}sheet")) != 1 or (
            properties is not None and properties.get("date1904") not in (None, "0", "false")
        ):
            raise ValueError("Unexpected worksheet count or date system")
        strings = [
            "".join(t.text or "" for t in entry.findall(".//{*}t"))
            for entry in ET.fromstring(book.read("xl/sharedStrings.xml"))
        ]
        sheet = ET.fromstring(book.read("xl/worksheets/sheet1.xml"))

    def value(cell):
        if cell is None:
            return None
        raw = cell.findtext("{*}v")
        return strings[int(raw)] if raw is not None and cell.get("t") == "s" else raw

    header, *records = sheet.findall("./{*}sheetData/{*}row")
    columns = {cell.get("r").removesuffix("1"): value(cell) for cell in header}
    if any(columns.get(column) != name for column, name in FIELDS.items()):
        raise ValueError("Unexpected workbook headers")

    counts = Counter()
    date_formats = Counter()
    outside_source_year = Counter()
    coverage = set()
    urla = {"rows": 0, "forest_or_nursery_rows": 0, "forest_or_nursery_dispatch_times": []}
    for index, row in enumerate(records, 2):
        if row.get("r") != str(index):
            raise ValueError("Nonconsecutive workbook rows")
        cells = {cell.get("r"): cell for cell in row}
        stamp, category, dispatch, district = (
            value(cells.get(f"{column}{index}")) for column in FIELDS
        )
        if stamp is None or category is None:
            raise ValueError("Missing date or category")
        if "/" in stamp:
            day = datetime.strptime(stamp, "%m/%d/%y").date()
            date_formats["month_first_text"] += 1
        else:
            serial = floor(Decimal(stamp))
            day = date(1899, 12, 30) + timedelta(days=serial + (0 < serial < 60))
            date_formats["excel_serial"] += 1
        counts[category] += 1
        if day.year != year:
            outside_source_year[category] += 1
            continue
        coverage.add(day.month)
        if day == URLA_DAY and district == "URLA":
            urla["rows"] += 1
            if category == FOREST:
                urla["forest_or_nursery_rows"] += 1
                urla["forest_or_nursery_dispatch_times"].append(
                    datetime.strptime(dispatch, "%H:%M").strftime("%H:%M")
                )

    return {
        "year": year,
        "sha256": expected_hash,
        "rows": len(records),
        "forest_or_nursery_rows": counts[FOREST],
        "scrub_rows": counts[SHRUB],
        "months_present": sorted(coverage),
        "date_encodings": dict(date_formats),
        "rows_outside_source_year": sum(outside_source_year.values()),
        "forest_or_scrub_rows_outside_source_year": (
            outside_source_year[FOREST] + outside_source_year[SHRUB]
        ),
        "has_address_area_category": columns.get("W") == "ADRES_BOLGESI",
        "urla_2022_06_09": urla if year == URLA_DAY.year else None,
    }


def urla_location_summary():
    for path, expected in SPATIAL_SOURCES.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Unexpected spatial source revision")
    boundary, district, grid, catalog = SPATIAL_SOURCES
    source = json.loads(boundary.read_bytes())
    (neighborhood,) = source["features"]
    (parent,) = json.loads(district.read_bytes())["features"]
    if (
        source["spatialReference"]["wkid"] != 4326
        or neighborhood["attributes"]["ADINUMARASI"] != "KUŞÇULAR"
        or parent["attributes"]["ADINUMARASI"] != "URLA"
        or neighborhood["attributes"]["ILCEID"] != parent["attributes"]["ID"]
    ):
        raise ValueError("Unexpected neighborhood, district or coordinate reference")
    (ring,) = neighborhood["geometry"]["rings"]
    shape = Polygon(ring)
    if not shape.is_valid or shape.is_empty:
        raise ValueError("Invalid neighborhood polygon")

    cells = gpd.read_file(grid)
    (project_crs,) = cells.grid_crs.unique()
    area = gpd.GeoSeries([shape], crs=4326).to_crs(project_crs).iloc[0]
    parts = cells.to_crs(project_crs).intersection(area).area
    cell_count = cells.loc[parts.gt(0), "grid_id"].nunique()
    if cell_count == 0 or not cells.cell_size_m.eq(5000).all():
        raise ValueError("Unexpected neighborhood overlap or grid size")

    day_end = URLA_DAY + timedelta(days=1)
    dates = (URLA_DAY.isoformat(), day_end.isoformat())
    with catalog.open(encoding="utf-8-sig", newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["detection_timestamp_utc"].startswith(dates)
        ]
    detections = training_detections(pd.DataFrame(rows))
    day_start_utc = pd.Timestamp(URLA_DAY, tz="UTC")
    day_end_utc = pd.Timestamp(day_end, tz="UTC")
    day = detections[detections.timestamp.gt(day_start_utc) & detections.timestamp.le(day_end_utc)]
    points = gpd.GeoSeries(
        gpd.points_from_xy(day.longitude, day.latitude), index=day.index, crs=4326
    )
    within = day[points.covered_by(shape)]
    first = within.timestamp.min()

    return {
        "case": "urla_kuscular_2022_06_09",
        "boundary_area_km2": round(area.area / 1e6, 4),
        "overlap_area_km2": round(parts.sum() / 1e6, 4),
        "intersecting_cells": int(cell_count),
        "centers_in_boundary_during_utc_window": len(within),
        "cells_with_centers_during_utc_window": int(within.grid_id.nunique()),
        "first_center_utc": first.tz_convert(UTC).isoformat() if pd.notna(first) else None,
        "boundary_represents_ignition_location": False,
        "inputs": {path.relative_to(ROOT).as_posix(): h for path, h in SPATIAL_SOURCES.items()},
    }


def main():
    summaries = [
        workbook_summary(BASE / "sources" / f"izmir_{year}.xlsx", year, digest)
        for year, digest in SOURCES.items()
    ]
    receipt = {
        "purpose": "dispatch_source_context_only",
        "workbooks": summaries,
        "location_check": urla_location_summary(),
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
    }
    run = BASE / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    run.mkdir(parents=True, exist_ok=False)
    result = run / "readback.json"
    result.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(result.relative_to(ROOT).as_posix(), hashlib.sha256(result.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
