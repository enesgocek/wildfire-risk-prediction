"""Reconcile official OGM province and forestry-region annual fire counts."""

import hashlib
import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset/ogm_province_year_v1"
SOURCE_MANIFEST = ROOT / "configs/ogm_province_year_sources_v1.json"
RECEIPT_SHA = "e8e9b4fa17077ac8dfe717e864ea646ab4a876cbf19f563fc0ba863750f004ad"
YEARS = range(2018, 2024)
PROVINCES = {"TR611": "Antalya", "TR323": "Muğla", "TR310": "İzmir", "TR622": "Mersin"}


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def workbook_cells(key, receipt, expected_sheet):
    path = BASE / "sources" / f"{key}.xlsx"
    source = receipt[key]
    data = path.read_bytes()
    check(
        len(data) == source["bytes"] and hashlib.sha256(data).hexdigest() == source["sha256"],
        f"Source identity: {key}",
    )
    with ZipFile(BytesIO(data)) as archive:
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets = book.findall(".//{*}sheet")
        check([s.get("name") for s in sheets] == [expected_sheet], f"Worksheet: {key}")
        strings = [
            "".join(part.text or "" for part in item.findall(".//{*}t"))
            for item in ET.fromstring(archive.read("xl/sharedStrings.xml"))
        ]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    cells = {}
    for cell in sheet.findall("./{*}sheetData/{*}row/{*}c"):
        raw = cell.findtext("{*}v")
        if raw is not None:
            cells[cell.get("r")] = strings[int(raw)] if cell.get("t") == "s" else raw
    return cells


def count(value):
    number = Decimal(value)
    check(number.is_finite() and number >= 0 and number == number.to_integral_value(), "Fire count")
    return int(number)


def area(value):
    number = Decimal(value)
    check(number.is_finite() and number >= 0, "Area in hectares")
    return number


def province_records(cells, year):
    check(all(str(year) in cells[f"{column}1"] for column in "AF"), "Turkish table year")
    check(str(year) in cells["F2"], "Continuation table year")
    expected_english_year = 2020 if year == 2021 else year
    check(str(expected_english_year) in cells["A2"], "English table year")
    if year == 2021:
        check(cells["D2"] == "2021", "2021 extra year cell")
    records = {}
    for block in ("ABCD", "FGHI"):
        code_column, name_column, count_column, area_column = block
        check(
            "3. Düzey" in cells[f"{code_column}3"]
            and "Number" in cells[f"{count_column}3"]
            and "Hectare" in cells[f"{area_column}3"],
            "Province scope and units",
        )
        for address, code in cells.items():
            if not address.startswith(code_column) or not re.fullmatch(r"TR(?:[A-Z0-9]{3})?", code):
                continue
            row = address[1:]
            check(code not in records, f"Duplicate province code: {code}")
            records[code] = (
                cells[f"{name_column}{row}"].strip(),
                cells[f"{count_column}{row}"],
                cells[f"{area_column}{row}"],
            )
    check(len(records) == 82 and "TR" in records, "81 provinces and published national total")
    return records


def regional_counts(cells):
    columns = "PQRSTU"
    check(
        "bölge müdürlüklerine" in cells["A1"] and "Number" in cells["U2"], "Region scope and unit"
    )
    check([int(cells[f"{col}4"]) for col in columns] == list(YEARS), "Regional years")
    labels = {*PROVINCES.values(), "Toplam-Total"}
    totals = {}
    for address, name in cells.items():
        if re.fullmatch(r"A\d+", address) and name in labels:
            check(name not in totals, f"Duplicate region: {name}")
            totals[name] = {
                year: count(cells[f"{col}{address[1:]}"])
                for year, col in zip(YEARS, columns, strict=True)
            }
    check(totals.keys() == labels, "Regional comparators")
    return totals


def audit(receipt, regions):
    rows = []
    reconciliation = []
    for year in YEARS:
        key = f"province_{year}"
        sheet = "2.12 İl yangın" if year == 2023 else "12.4 İl yangın"
        records = province_records(workbook_cells(key, receipt, sheet), year)
        national_name, national_count, national_area = records.pop("TR")
        counts = sum(count(raw_count) for _, raw_count, _ in records.values() if raw_count != "-")
        areas = sum(area(raw_area) for _, _, raw_area in records.values() if raw_area != "-")
        check(
            national_name == "Türkiye"
            and counts == count(national_count) == regions["Toplam-Total"][year],
            f"National count reconciliation: {year}",
        )
        reconciliation.append(
            {
                "year": year,
                "published_national_fire_count": counts,
                "published_national_area_ha": float(area(national_area)),
                "province_area_sum_ha": float(round(areas, 4)),
                "province_area_minus_national_ha": float(round(areas - area(national_area), 4))
                or 0.0,
                "dash_count_codes": sorted(code for code, row in records.items() if row[1] == "-"),
                "dash_area_codes": sorted(code for code, row in records.items() if row[2] == "-"),
            }
        )
        for code, name in PROVINCES.items():
            actual_name, raw_count, raw_area = records[code]
            check(actual_name == name, f"Province identity: {code}")
            province_count = count(raw_count)
            region_count = regions[name][year]
            rows.append(
                {
                    "year": year,
                    "province_code": code,
                    "province": name,
                    "province_fire_count": province_count,
                    "province_area_ha": float(round(area(raw_area), 4)),
                    "same_name_region_fire_count": region_count,
                    "province_minus_region_fire_count": province_count - region_count,
                }
            )
    return rows, reconciliation


def main():
    receipt_bytes = SOURCE_MANIFEST.read_text(encoding="utf-8").encode("utf-8")
    check(hashlib.sha256(receipt_bytes).hexdigest() == RECEIPT_SHA, "Source receipt identity")
    receipt = json.loads(receipt_bytes)["sources"]
    regions = regional_counts(workbook_cells("regional_2023", receipt, "2.11"))
    rows, reconciliation = audit(receipt, regions)
    result = {
        "purpose": "administrative_province_year_coverage_comparator_only",
        "source_receipt_sha256": RECEIPT_SHA,
        "source_tables": receipt,
        "province_year_rows": rows,
        "national_reconciliation": reconciliation,
        "known_header_note": "province_2021 A2 says 2020; A1, F1, F2, and D2 indicate 2021",
    }
    run = BASE / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    run.mkdir()
    path = run / "summary.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    check(json.loads(path.read_bytes()) == result, "Written audit readback")
    print(path.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
