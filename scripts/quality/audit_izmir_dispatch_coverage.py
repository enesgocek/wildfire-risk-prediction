"""Compare the frozen 2023 İzmir dispatch file, API projection and annual totals."""

import hashlib
import json
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset/izmir_dispatch_coverage_v1"
WORKBOOK = BASE / "sources/izmir_dispatch_2023.xlsx"
PROJECTION = BASE / "20261108T033936Z_765251ae/api_projection.json"
INPUTS = {
    WORKBOOK: "2082ac26367c89364d8cf18d814c8a2e45b517c7cd887ef8cb9ec54bd6b4dcdf",
    PROJECTION: "4bf5d59552368ee4dd7fc03d4912d9e5ea870999e51d40282e695c7200d2b036",
}
RESOURCE = "f718e29e-0e3f-4b63-8019-e1920ca94330"
REPORT_URL = "https://itfaiye.izmir.bel.tr/YuklenenDosyalar/Dokumanlar/23012024_2023.pdf"
FIELDS = ("TARIH", "YANGIN_TURU", "ILCE")
COLUMNS = ("A", "B", "V")
FOREST, SHRUB = "ORMAN/FİDANLIK", "MAKİLİK/ÇALI"
ANNUAL_COUNTS = {"rows": 12986, FOREST: 194, SHRUB: 82}


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def workbook_records():
    """Read only three analysis columns from the pinned, single-sheet workbook."""
    with ZipFile(WORKBOOK) as archive:
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets = book.findall(".//{*}sheet")
        properties = book.find("{*}workbookPr")
        check(
            len(sheets) == 1
            and sheets[0].get("name") == "Sayfa1"
            and (properties is None or properties.get("date1904") in (None, "0", "false")),
            "Expected worksheet and Excel date system",
        )
        strings = [
            "".join(part.text or "" for part in item.findall(".//{*}t"))
            for item in ET.fromstring(archive.read("xl/sharedStrings.xml"))
        ]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))

    def value(cell):
        raw = cell.findtext("{*}v")
        return strings[int(raw)] if cell.get("t") == "s" else raw

    records = []
    for index, row in enumerate(sheet.findall("./{*}sheetData/{*}row"), 1):
        check(row.get("r") == str(index), "Consecutive workbook rows")
        cells = {cell.get("r"): cell for cell in row}
        selected = tuple(value(cells[f"{column}{index}"]) for column in COLUMNS)
        if index == 1:
            check(selected == FIELDS, "Expected workbook columns")
            continue
        excel_day, category, district = selected
        day = date(1899, 12, 30) + timedelta(days=int(excel_day))
        records.append((day, category, district))
    return records


def api_records():
    source = json.loads(PROJECTION.read_bytes())
    pages = source["pages"]
    check(source["resource_id"] == RESOURCE, "Expected API resource")
    check(
        [page["offset"] for page in pages] == [0, 5000, 10000, 15000] and not pages[-1]["records"],
        "Complete paginated API projection",
    )
    raw = [row for page in pages for row in page["records"]]
    check(all(page["reported_total"] == len(raw) for page in pages), "API total reconciliation")
    records = []
    for index, row in enumerate(raw, 1):
        check(set(row) == {*FIELDS, "_id"} and row["_id"] == index, "API projection and row order")
        stamp = datetime.fromisoformat(row["TARIH"])
        check(stamp == datetime.combine(stamp.date(), datetime.min.time()), "API date granularity")
        records.append((stamp.date(), row["YANGIN_TURU"], row["ILCE"]))
    return records


def counts(records):
    categories = Counter(category for _, category, _ in records)
    return {"rows": len(records), FOREST: categories[FOREST], SHRUB: categories[SHRUB]}


def main():
    hashes = {}
    for path, expected in INPUTS.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        check(actual == expected, "Frozen source identity")
        hashes[path.relative_to(ROOT).as_posix()] = actual
    full, api = workbook_records(), api_records()
    check(all(day.year == 2023 for day, _, _ in full), "2023-only workbook")
    check(full[: len(api)] == api, "API rows match the file prefix on three selected columns")
    check(counts(full) == ANNUAL_COUNTS, "Workbook totals agree with the annual report")
    remainder = full[len(api) :]
    check(remainder and api, "Observed API coverage difference")
    omitted_days = {day for day, _, _ in remainder}
    api_days = {day for day, _, _ in api}
    last_api_day = max(api_days)
    report = {
        "input_sha256": hashes,
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "annual_report_url": REPORT_URL,
        "api_resource": RESOURCE,
        "year": 2023,
        "matched_columns_in_order": list(FIELDS),
        "workbook": counts(full),
        "api": counts(api),
        "annual_report": ANNUAL_COUNTS,
        "workbook_suffix_only": counts(remainder),
        "suffix_date_bounds": [min(omitted_days).isoformat(), max(omitted_days).isoformat()],
        "suffix_distinct_dates": len(omitted_days),
        "suffix_dates_absent_entirely_from_api": len(omitted_days - api_days),
        "last_api_date": last_api_day.isoformat(),
        "last_api_date_rows": sum(day == last_api_day for day, _, _ in api),
        "last_api_date_workbook_rows": sum(day == last_api_day for day, _, _ in full),
        "suffix_by_month": dict(
            sorted(Counter(day.strftime("%Y-%m") for day, _, _ in remainder).items())
        ),
        "verified_original_start_coordinates": False,
        "documented_complete_wildfire_incidence": False,
        "target": None,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
    }
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    output = BASE / run / "readback.json"
    output.parent.mkdir(parents=True, exist_ok=False)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output.relative_to(ROOT).as_posix(), hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
