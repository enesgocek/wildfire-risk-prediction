"""Inspect publisher DOCX table fields; never treat aftermath cases as origin labels."""

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / (
    "outputs/reports/dataset/eker_2021_supplement_v1/"
    "20261119T003240Z_8a1d7b64/publisher_supplement.docx"
)
EXPECTED = "bca3c83d0e5528589c715110b77356942e801cacc7173c269ba17309eda554a5"
PUBLISHER = "https://doi.org/10.1007/s11069-024-06622-0"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
HEADERS = [
    "No",
    "Case Code",
    "Region*",
    "Province/Location",
    "Starting Date",
    "Ending Date",
    "Duration (days)",
    "Area Burned (ha)",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell_text(cell):
    paragraphs = []
    for paragraph in cell.findall("w:p", NS):
        chunks = []
        for element in paragraph.iter():
            if element.tag == "{" + NS["w"] + "}t":
                chunks.append(element.text or "")
            elif element.tag in {"{" + NS["w"] + "}" + k for k in ("br", "cr", "tab")}:
                chunks.append(" ")
        paragraphs.append("".join(chunks))
    return " ".join(" ".join(paragraphs).split())


def main():
    if sha(SOURCE) != EXPECTED:
        raise ValueError("Publisher supplement identity changed")
    with zipfile.ZipFile(SOURCE) as archive:
        info = archive.getinfo("word/document.xml")
        if info.file_size > 10_000_000:
            raise ValueError("Bounded document XML")
        xml = ET.fromstring(archive.read(info))
    tables = xml.findall("./w:body/w:tbl", NS)
    rows = []
    for row in tables[0].findall("w:tr", NS):
        # Preserve adjacent text runs; only real breaks separate words.
        cells = [cell_text(c) for c in row.findall("w:tc", NS)]
        rows.append(cells)
    if len(tables) != 4 or len(rows) != 31 or rows[0] != HEADERS:
        raise ValueError("Expected four tables and explicit eight-field S1 schema")
    records = []
    for values in rows[1:]:
        if len(values) != 8:
            raise ValueError("Unexpected merged or split record")
        row = dict(zip(HEADERS, values, strict=True))
        start = datetime.strptime(row["Starting Date"], "%d.%m.%Y").date()
        end = datetime.strptime(row["Ending Date"], "%d.%m.%Y").date()
        duration = int(row["Duration (days)"])
        if start.year != 2021 or end.year != 2021 or end < start or (end - start).days != duration:
            raise ValueError("Source date/duration accounting")
        records.append(
            {
                "case_code": row["Case Code"],
                "source_location_label": row["Province/Location"],
                "starting_day_as_published": start.isoformat(),
                "ending_day_as_published": end.isoformat(),
                "duration_days": duration,
            }
        )
    if len({r["case_code"] for r in records}) != 30:
        raise ValueError("Nonunique publisher case code")
    selected = [
        r
        for r in records
        if r["source_location_label"].split("/")[0] in {"Antalya", "Muğla", "İzmir", "Mersin"}
    ]
    if len(selected) != 15:
        raise ValueError("Project province label count changed")
    result = {
        "scope": "publisher_supplement_field_review_not_label_acceptance",
        "source_path": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": EXPECTED,
        "publication": PUBLISHER,
        "producer_sha256": sha(Path(__file__)),
        "review_method": "OOXML_table_cells_cross_checked_with_bundled_python_docx",
        "rendered_visual_review": False,
        "table_count": len(tables),
        "s1_column_names": HEADERS,
        "s1_data_rows": len(records),
        "rows_with_project_province_label": len(selected),
        "distinct_real_ignition_count": None,
        "s1_explicit_clock_column_present": False,
        "s1_explicit_coordinate_column_present": False,
        "published_date_duration_arithmetic_consistent": True,
        "physical_extinction_times_verified": False,
        "original_start_geometry_verified": False,
        "source_examples": [r for r in selected if r["case_code"] in {"MATA", "MRMS", "MILS"}],
        "source_timing_lineage": "article_methods_report_GDF_dates_not_an_independent_second_clock",
        "source_spatial_lineage": "article_extent_from_post_fire_Sentinel_2_not_ignition_geometry",
        "new_cases_added_to_registry": 0,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "model_ready": False,
        "final_merge_permitted": False,
    }
    out = (
        ROOT
        / "outputs/reports/dataset/eker_supplement_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    saved = out / "readback.json"
    saved.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if json.loads(saved.read_bytes()) != result:
        raise ValueError("Saved source field review changed")
    print(out.relative_to(ROOT).as_posix())
    print("PASS source_schema_dates_and_scope; no start labels accepted")
    print("readback_sha256", sha(saved))


if __name__ == "__main__":
    main()
