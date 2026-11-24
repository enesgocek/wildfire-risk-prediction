"""Read back report tables, frozen result arithmetic and rendered-page evidence."""

import argparse
import csv
import hashlib
import json
import re
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

import pdfplumber
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def normalize(value):
    return re.sub(r"\s+", " ", value).strip().replace("–", "-")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.relative_to(ROOT / "outputs/reports/dataset/thesis_research_report_v1")
    receipt = json.loads((report / "readback.json").read_bytes())
    for name, value in receipt["input_sha256"].items():
        path = ROOT / name
        path.resolve().relative_to(ROOT)
        require(digest(path) == value, "Preserved input hash: " + name)
    for name, value in receipt["artifact_sha256"].items():
        require(digest(report / name) == value, "Report artifact hash: " + name)
    tables = json.loads((report / "report_tables.json").read_bytes())
    content = json.loads((report / "report_content.json").read_bytes())
    pdf_paths = list(report.glob("*.pdf"))
    require(len(pdf_paths) == 1, "Exactly one report PDF")
    pdf = pdf_paths[0]
    extracted_tables = []
    text = []
    with pdfplumber.open(pdf) as document:
        require(len(document.pages) == 11, "Report page count")
        for page in document.pages:
            text.append(normalize(page.extract_text()))
            require(
                all(
                    47 <= char["x0"] < char["x1"] <= page.width - 47
                    and 35 <= char["top"] < char["bottom"] <= page.height - 20
                    for char in page.chars
                ),
                "All characters stay inside document boundaries",
            )
            extracted_tables.extend(page.extract_tables())
    expected_names = [
        block["name"]
        for page in content["pages"]
        for block in page["blocks"]
        if block["type"] == "table"
    ]
    require(len(extracted_tables) == len(expected_names) == 8, "All eight PDF tables")
    cell_count = 0
    for observed, name in zip(extracted_tables, expected_names, strict=True):
        expected = [tables[name]["headers"], *tables[name]["rows"]]
        require(len(observed) == len(expected), "PDF table row count: " + name)
        for actual_row, expected_row in zip(observed, expected, strict=True):
            require(
                [normalize(x or "") for x in actual_row] == [normalize(x) for x in expected_row],
                "PDF table text matches complete source cell: " + name,
            )
            cell_count += len(actual_row)
    for i, page in enumerate(content["pages"]):
        require(page["heading"] in text[i], "Section heading and page placement")
    raw = " ".join(text)
    require(
        all(
            phrase in raw
            for phrase in [
                "gerçek yangın başarımı değildir",
                "negatif etiket izni false",
                "Günlük gözlem durumu unknown",
                "2022 kör final test değildir",
                "Nihai etiketli veri birleştirmesi yapılmamıştır",
                "yapay zekâ desteğiyle hazırlanmıştır",
            ]
        ),
        "Scientific and contribution caveats present in final PDF",
    )

    def source_rows(prefix):
        paths = [
            ROOT / path
            for path in receipt["input_sha256"]
            if prefix in path and path.endswith("/metrics.csv")
        ]
        require(len(paths) == 1, "Unambiguous frozen metric source")
        with paths[0].open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    main_rows = source_rows("/primary_weather_rank_run_v1/")
    overlap_rows = source_rows("/source_disjoint_frozen_assessment_v1/")
    exact = []
    for row in main_rows + overlap_rows:
        value = Fraction(2 * int(row["wins"]) + int(row["ties"]), 2 * int(row["pairs"]))
        require(
            abs(float(value) - float(row["auxiliary_pair_AUC"])) < 1e-14,
            "Exact source-credit arithmetic",
        )
        exact.append((row, value))

    def credit_range(rows, **criteria):
        chosen = [
            (row, value)
            for row, value in exact
            if row in rows and all(row[k] == v for k, v in criteria.items())
        ]
        require(
            len(chosen) == len({r["scenario"] for r, _ in chosen}) == 9,
            "Nine exact scenario credits",
        )
        values = [v for _, v in chosen]
        return normalize(f"{float(min(values)):.6f} - {float(max(values)):.6f}".replace(".", ","))

    range_cells = 0
    for table_row, (cohort, slice_name) in zip(
        tables["results"]["rows"],
        [
            ("four_province", "all_same_grid_month"),
            ("four_province", "gap_1_to_3_days"),
            ("separate_Mersin", "all_same_grid_month"),
            ("separate_Mersin", "gap_1_to_3_days"),
        ],
        strict=True,
    ):
        for cell, variant in zip(
            table_row[1:],
            ["primary_weather_XGBoost", "broad_weather_XGBoost", "frozen_linear"],
            strict=True,
        ):
            require(
                normalize(cell)
                == credit_range(main_rows, cohort=cohort, slice=slice_name, variant=variant),
                "Exact main report range",
            )
            range_cells += 1
    for table_row, group in zip(
        tables["overlap"]["rows"],
        [
            "original_source_calendar",
            "exclude_any_same_key_satellite_proposal",
            "absent_from_four_province_calendar",
        ],
        strict=True,
    ):
        for cell, slice_name in zip(
            table_row[2:], ["all_same_grid_month", "gap_1_to_3_days"], strict=True
        ):
            require(
                normalize(cell)
                == credit_range(
                    overlap_rows,
                    source_group=group,
                    slice=slice_name,
                    variant="primary_weather_XGBoost",
                ),
                "Exact overlap report range",
            )
            range_cells += 1
    links = PdfReader(pdf).pages[-1].get("/Annots", [])
    require(len(links) == len(content["references"]) == 4, "Four literature hyperlinks")
    require(
        {link.get_object()["/A"]["/URI"] for link in links}
        == {ref["url"] for ref in content["references"]},
        "Actual PDF hyperlink targets",
    )
    review_path = report / "page_review.json"
    review = json.loads(review_path.read_bytes())
    require(
        review["reviewer"] == "assistant_visual_inspection"
        and review["pdf_sha256"] == digest(pdf)
        and review["all_pages_reviewed"]
        and len(review["page_sha256"]) == 11,
        "Visual review must be explicitly recorded for this PDF",
    )
    for name, expected in review["page_sha256"].items():
        require(digest(report / "render" / name) == expected, "Reviewed rendered page hash")
    out = (
        ROOT
        / "outputs/reports/dataset/thesis_research_report_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    result = {
        "status": "research_report_pdf_tables_and_pages_verified_not_scientific_acceptance",
        "report_receipt_sha256": digest(report / "readback.json"),
        "report_pdf_sha256": digest(pdf),
        "page_review_sha256": digest(review_path),
        "auditor_sha256": digest(Path(__file__)),
        "pages": 11,
        "tables": 8,
        "table_cells_checked": cell_count,
        "source_metric_rows_fraction_checked": len(exact),
        "exact_range_cells": range_cells,
        "hyperlinks_checked": 4,
        "all_page_images_visually_reviewed_by_assistant": True,
        "human_label_acceptance": False,
        "new_scientific_experiment": False,
        "final_merge": False,
        "docx_delivered": False,
    }
    (out / "readback.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
