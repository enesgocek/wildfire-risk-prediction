"""Publish a PDF synthesis from frozen receipts without fitting or predicting.

Run with the Codex bundled Python (reportlab/pypdf). Scientific inputs remain
read-only. No external upload, institutional format claim or label acceptance.
"""

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CONTENT = ROOT / "docs/research/thesis_report_content_2026-11-24.json"
INPUTS = {
    "K1": (
        "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1",
        "86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366",
    ),
    "K2": (
        "primary_weather_rank_run_v1/20261123T143258Z_35678270",
        "004f7d27d6b0f1825b2b00d7a2825b311e2483b5f2d73c7063cadd9b45b2946d",
    ),
    "K3": (
        "source_disjoint_frozen_assessment_v1/20261124T031245Z_91cd329d",
        "7f6e16ff58084954610dea8ca41d9ca87ece9fd02192b076cfec5973845a5d23",
    ),
    "K4": (
        "frozen_rank_case_review_v1/20261124T024256Z_abeb3e00",
        "a65579afa7165b72a830f22e39367bb9331e100c0b5aa7d0b982bdf8dcc8c4af",
    ),
    "K5": (
        "portable_research_release_v1/20261124T190220Z_58fe285c",
        "ddb18f8e05f17b1113b05ca73230cef44441f261d032ac861f8cf5c65db7a677",
    ),
}
SUPPORT = BASE / "frozen_score_support_diagnostic_v1/20261124T022210Z_e025acc0"
SUPPORT_SHA = "b888b1a1ea01af8b59728395a940f4f7f87b22c46830752e350dd686e4f1efc9"
FONT_ROOT = Path("C:/Windows/Fonts")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition, note):
    if not condition:
        raise ValueError(note)


def integer(value):
    return f"{int(value):,}".replace(",", ".")


def decimal(value, places=6):
    return f"{float(value):.{places}f}".replace(".", ",")


def credit_range(rows):
    require(len(rows) == 9, "Every reported range includes nine scenarios")
    require(len({r["scenario"] for r in rows}) == 9, "Nine unique scenarios")
    values = [float(r["auxiliary_pair_AUC"]) for r in rows]
    return f"{decimal(min(values))} - {decimal(max(values))}"


def selected(rows, **criteria):
    return [r for r in rows if all(r[k] == v for k, v in criteria.items())]


def fixed_text(text):
    # Use ordinary PDF hyphens, preserving the meaning and decimal precision.
    return text.replace("–", "-").replace("—", "-").replace("−", "-")


def build():
    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    require(len(content["pages"]) == 11, "Expected report outline")
    pins = {CONTENT: sha(CONTENT), Path(__file__): sha(Path(__file__))}
    receipts = {}

    # Verify the frozen receipts and every artifact used by this report.
    def pinned_file(folder, receipt, name):
        path = folder / name
        expected = receipt.get("artifact_sha256", {}).get(name)
        if expected is None:
            expected = receipt.get("input_sha256", {}).get(path.relative_to(ROOT).as_posix())
        require(expected is not None, "Source receipt must identify artifact: " + name)
        require(sha(path) == expected, "Source artifact hash: " + name)
        pins[path] = expected
        return path

    for code, (name, expected) in INPUTS.items():
        receipt_path = BASE / name / "readback.json"
        require(sha(receipt_path) == expected, "Frozen input receipt " + code)
        pins[receipt_path] = expected
        receipts[code] = json.loads(receipt_path.read_bytes())
    require(sha(SUPPORT / "readback.json") == SUPPORT_SHA, "Frozen support receipt")
    pins[SUPPORT / "readback.json"] = SUPPORT_SHA
    folders = {k: BASE / v[0] for k, v in INPUTS.items()}
    features = read_csv(pinned_file(folders["K1"], receipts["K1"], "features.csv"))
    memberships = read_csv(pinned_file(folders["K1"], receipts["K1"], "inspection_memberships.csv"))
    require(
        len(memberships) == 44082
        and all(
            not row["target"]
            and not row["accepted_L_membership"]
            and row["daily_observation_status"] == "unknown"
            and row["negative_label_permitted"] == "False"
            for row in memberships
        ),
        "Scientific uncertainty fields preserved in all rows",
    )
    dictionary = json.loads(
        pinned_file(folders["K1"], receipts["K1"], "feature_dictionary.json").read_bytes()
    )
    metrics = read_csv(pinned_file(folders["K2"], receipts["K2"], "metrics.csv"))
    overlap = read_csv(pinned_file(folders["K3"], receipts["K3"], "metrics.csv"))
    cases = read_csv(pinned_file(folders["K4"], receipts["K4"], "illustrative_cases.csv"))
    names = [r["name"] for r in dictionary]
    require(len(names) == 27 and len(set(names)) == 27, "Feature dictionary")
    keys = {(r["grid_id"], r["prediction_timestamp_utc"]) for r in features}
    years = Counter(r["prediction_timestamp_utc"][:4] for r in features)
    complete = sum(all(r[name] != "" for name in names) for r in features)
    require(set(years) == {"2018", "2019", "2020", "2021", "2022"}, "Only frozen years")
    require(len(features) == len(keys) == 44082, "Actual unique feature count")
    require(len({r["grid_id"] for r in features}) == 822, "Actual cell count")
    require(complete == receipts["K1"]["complete_features"] == 41358, "Actual completeness")
    require(
        years["2022"] == 6573 and sum(v for k, v in years.items() if k != "2022") == 37509,
        "Actual year split",
    )
    require(
        len(metrics) == 270 and len(overlap) == 405 and len(cases) == 12, "Frozen result dimensions"
    )
    for row in metrics + overlap:
        exact_credit = (2 * int(row["wins"]) + int(row["ties"])) / (2 * int(row["pairs"]))
        require(
            abs(exact_credit - float(row["auxiliary_pair_AUC"])) < 1e-14,
            "Wins/ties credit readback",
        )
    tables = {
        "literature": {
            "headers": ["Kaynak", "Görev", "Bu raporda kullanım"],
            "widths": [0.20, 0.31, 0.49],
            "rows": [
                [
                    "[1] Apostolakis",
                    "Ertesi gün yangın oluşumu",
                    "Zamansal değerlendirme ve hedef tanımı",
                ],
                ["[2] Mesogeos", "Veri küpü ve iki ayrı görev", "Veri hazırlığı ve görev ayrımı"],
                ["[3] Huot", "Mevcut yangının yayılması", "Yeni yangın ile yayılımın ayrılması"],
                [
                    "[4] Kiryo",
                    "Pozitif ve etiketsiz öğrenme",
                    "PU yönü ve uygulanmayan varsayımlar",
                ],
            ],
        },
        "dataset": {
            "headers": ["Ölçü", "Mevcut deneysel paket"],
            "widths": [0.66, 0.34],
            "rows": [
                ["Farklı hücre-gün", integer(len(keys))],
                ["Farklı hücre", "822"],
                ["Özellik sayısı", "27"],
                ["27 özelliği tam satır", integer(complete)],
                ["En az bir eksiği olan satır", integer(len(features) - complete)],
                ["2018-2021 rolündeki satır", "37.509"],
                ["2022 keşif rolündeki satır", integer(years["2022"])],
                [
                    "En az bir S önerisindeki anahtar",
                    integer(receipts["K1"]["proposal_union_keys"]),
                ],
                [
                    "Üyelik önerisi ayara duyarlı anahtar",
                    integer(receipts["K1"]["scenario_dependent_keys"]),
                ],
            ],
        },
        "model": {
            "headers": ["Bileşen", "Sabit düzen"],
            "widths": [0.30, 0.70],
            "rows": [
                ["Algoritma", "XGBoost 3.4.1 rank:pairwise"],
                ["Girdi", "11 meteoroloji ve 4 geçmiş bitki örtüsü alanı"],
                ["Öğrenme ve inceleme", "2018-2021 öğrenme; 2022 keşif değerlendirmesi"],
                ["Ağaç ayarları", "100 ağaç; derinlik 3; öğrenme hızı 0,05"],
                ["Diğer ayarlar", "min_child_weight 5; L2 1; tam satır ve sütun"],
                ["Çalıştırma", "CPU hist; 4 iş parçacığı; seed 20261123"],
                ["Grup düzeni", "topk 31; çift ve skor normalizasyonu açık"],
                ["Korunan senaryolar", "3 uzaklık × 3 süre = 9 ayar; üretim seçimi yok"],
            ],
        },
        "cohorts": {
            "headers": ["2022 inceleme takvimi", "Satır", "Hücre", "Ana destekli satır"],
            "widths": [0.43, 0.16, 0.16, 0.25],
            "rows": [
                ["Dört il uydu aday takvimi", "6.573", "185", "4.841"],
                ["Ayrı Mersin kaynak takvimi", "2.383", "68", "1.929"],
            ],
        },
        "results": {
            "headers": ["2022 kesiti", "Ana XGBoost", "Geniş destekli XGBoost", "Doğrusal"],
            "widths": [0.31, 0.23, 0.23, 0.23],
            "rows": [],
        },
        "overlap": {
            "headers": [
                "Kaynak grubu",
                "Uygun gün ve hücre",
                "Genel çift kredisi",
                "1-3 gün kredisi",
            ],
            "widths": [0.27, 0.23, 0.25, 0.25],
            "rows": [],
        },
        "cases": {
            "headers": ["2022 örneği", "Kaynak günü ortalama sırası", "Dokuz ayarda kredi"],
            "widths": [0.45, 0.27, 0.28],
            "rows": [],
        },
        "delivery": {
            "headers": ["Bileşen", "Kapsam ve rol"],
            "widths": [0.35, 0.65],
            "rows": [
                ["Deneysel veri", "44.082 anahtar; ayrı özellik, üyelik ve köken dosyaları"],
                ["Araştırma modelleri", "Dokuz sabit ana model ve mevcut karşılaştırmalar"],
                ["İnceleme arayüzü", "İki 2022 takvimi; 244 hücre ve 12 örneğe geçiş"],
                [
                    "Taşınabilir yerel paket",
                    "499 dosya; 24.032.305 bayt ZIP; tek başlangıç sayfası",
                ],
            ],
        },
    }
    result_checks = []
    for cohort, kind, label in [
        ("four_province", "all_same_grid_month", "Dört il tüm çiftler"),
        ("four_province", "gap_1_to_3_days", "Dört il 1-3 gün"),
        ("separate_Mersin", "all_same_grid_month", "Ayrı Mersin tüm çiftler"),
        ("separate_Mersin", "gap_1_to_3_days", "Ayrı Mersin 1-3 gün"),
    ]:
        row = [label]
        for variant in ["primary_weather_XGBoost", "broad_weather_XGBoost", "frozen_linear"]:
            candidates = selected(metrics, cohort=cohort, slice=kind, variant=variant)
            row.append(credit_range(candidates))
            result_checks.append(
                {"cohort": cohort, "slice": kind, "variant": variant, "range": row[-1]}
            )
        tables["results"]["rows"].append(row)
    for group, label, days, cells in [
        ("original_source_calendar", "G0 özgün", 65, 56),
        ("exclude_any_same_key_satellite_proposal", "G1 S ortaklığı yok", 59, 54),
        ("absent_from_four_province_calendar", "G2 takvim ortaklığı yok", 56, 51),
    ]:
        tables["overlap"]["rows"].append(
            [
                label,
                f"{days} gün / {cells} hücre",
                credit_range(
                    selected(
                        overlap,
                        source_group=group,
                        variant="primary_weather_XGBoost",
                        slice="all_same_grid_month",
                    )
                ),
                credit_range(
                    selected(
                        overlap,
                        source_group=group,
                        variant="primary_weather_XGBoost",
                        slice="gap_1_to_3_days",
                    )
                ),
            ]
        )
    for case_id, label in [
        ("four_province_01", "Antalya C596/R882 12 Nisan"),
        ("four_province_06", "Antalya C572/R867 22 Eylül"),
        ("separate_Mersin_01", "Mersin C634/R862 31 Temmuz"),
        ("separate_Mersin_06", "Mersin C654/R868 22 Mayıs"),
    ]:
        matches = selected(cases, case_id=case_id)
        require(len(matches) == 1, "Illustrative case identifier")
        case = matches[0]
        tables["cases"]["rows"].append(
            [
                label,
                decimal(case["source_day_rank_mean"], 3) + " / " + case["eligible_days_in_month"],
                decimal(case["primary_credit_min"]) + " - " + decimal(case["primary_credit_max"]),
            ]
        )
    out = (
        BASE
        / "thesis_research_report_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    (out / "report_tables.json").write_text(
        json.dumps(tables, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "report_content.json").write_bytes(CONTENT.read_bytes())
    for name, file in [("Report", "arial.ttf"), ("ReportBold", "arialbd.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(FONT_ROOT / file)))
    pdfmetrics.registerFontFamily(
        "Report", normal="Report", bold="ReportBold", italic="Report", boldItalic="ReportBold"
    )
    styles = {
        "body": ParagraphStyle(
            "Body",
            fontName="Report",
            fontSize=10.5,
            leading=14.5,
            spaceAfter=8,
            textColor=colors.black,
        ),
        "heading": ParagraphStyle(
            "Heading",
            fontName="ReportBold",
            fontSize=16,
            leading=20,
            spaceAfter=12,
            keepWithNext=True,
            textColor=colors.black,
        ),
        "sub": ParagraphStyle(
            "Subheading",
            fontName="ReportBold",
            fontSize=11.7,
            leading=15,
            spaceBefore=6,
            spaceAfter=7,
            keepWithNext=True,
            textColor=colors.black,
        ),
        "cell": ParagraphStyle(
            "Cell", fontName="Report", fontSize=9.0, leading=12, textColor=colors.black
        ),
        "number": ParagraphStyle(
            "NumberCell",
            fontName="Report",
            fontSize=9.0,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.black,
        ),
        "headcell": ParagraphStyle(
            "HeaderCell", fontName="ReportBold", fontSize=9.0, leading=12, textColor=colors.black
        ),
        "ref": ParagraphStyle(
            "Reference",
            fontName="Report",
            fontSize=9.3,
            leading=12.6,
            spaceAfter=9,
            splitLongWords=True,
            textColor=colors.black,
        ),
    }

    def para(text, style="body"):
        return Paragraph(escape(fixed_text(text)), styles[style])

    def table(name):
        spec = tables[name]
        data = [[para(text, "headcell") for text in spec["headers"]]]
        for row in spec["rows"]:
            data.append(
                [
                    para(
                        value,
                        "number"
                        if j > 0 and name in {"dataset", "cohorts", "results", "overlap", "cases"}
                        else "cell",
                    )
                    for j, value in enumerate(row)
                ]
            )
        result = Table(
            data, colWidths=[(A4[0] - 100) * f for f in spec["widths"]], repeatRows=1, hAlign="LEFT"
        )
        result.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9EDF2")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return [result, Spacer(1, 10)]

    story = []
    for i, page in enumerate(content["pages"]):
        if i:
            story.append(PageBreak())
        else:
            title_style = ParagraphStyle(
                "Title", parent=styles["heading"], fontSize=22, leading=27, spaceAfter=10
            )
            story += [
                Paragraph(escape(content["title"]), title_style),
                para(content["subtitle"]),
                para(content["date"], "ref"),
                Spacer(1, 6),
            ]
        story.append(para(page["heading"], "heading"))
        for block in page["blocks"]:
            kind = block["type"]
            if kind == "p":
                story.append(para(block["text"]))
            elif kind == "h":
                story.append(para(block["text"], "sub"))
            elif kind == "table":
                story += table(block["name"])
            elif kind == "references":
                for ref in content["references"]:
                    text = escape("[" + ref["id"] + "] " + fixed_text(ref["text"]))
                    text += (
                        ' <link href="'
                        + escape(ref["url"], {'"': "&quot;"})
                        + '">Yayın kaydı</link>.'
                    )
                    story.append(Paragraph(text, styles["ref"]))
            elif kind == "evidence":
                for code, (folder, expected) in INPUTS.items():
                    story.append(
                        para(f"{code}  {folder}  Makbuz SHA-256 başlangıcı {expected[:16]}", "ref")
                    )
            else:
                raise ValueError("Unrecognized report block")

    pdf = out / "Orman_yangini_arastirma_raporu_2026-11-24.pdf"

    def footer(canvas, doc):
        canvas.setFont("Report", 8.5)
        canvas.setFillColor(colors.black)
        canvas.drawString(50, 29, "Orman yangını araştırması  |  24 Kasım 2026")
        canvas.drawRightString(A4[0] - 50, 29, str(doc.page))

    doc = SimpleDocTemplate(
        str(pdf),
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=40,
        bottomMargin=49,
        title=content["title"],
        author="",
        subject="Dört il için deneysel veri hazırlığı ve kaynak günü sıralaması",
        pageCompression=1,
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    reader = PdfReader(pdf)
    texts = [page.extract_text() for page in reader.pages]
    require(len(texts) == len(content["pages"]), "One complete section per page without overflow")
    for page, expected in zip(texts, content["pages"], strict=True):
        require(fixed_text(expected["heading"]) in page, "Expected section page")
        require("\ufffd" not in page and "\u25a0" not in page, "No replacement glyph")
    full_text = re.sub(r"\s+", " ", " ".join(texts))
    require(
        all(
            value in full_text
            for value in [
                "44.082",
                "41.358",
                "2.724",
                "rank:pairwise",
                "unknown",
                "false",
                "güven aralığı",
                "kör final test değildir",
            ]
        ),
        "Key claims and caveats survived PDF extraction",
    )
    require(
        not re.search(r"turn\d+(search|view)|TODO|TBD|Lorem ipsum", full_text),
        "No drafting or tool artifacts",
    )
    require(len(reader.pages[-1].get("/Annots", [])) == 4, "Four clickable literature references")
    # The source files must still match after document production.
    require(all(sha(path) == value for path, value in pins.items()), "Frozen input preservation")
    result = {
        "status": "research_report_pdf_built_pending_page_image_review",
        "analysis_date": "2026-11-24",
        "pages": len(reader.pages),
        "input_sha256": {path.relative_to(ROOT).as_posix(): value for path, value in pins.items()},
        "artifact_sha256": {
            path.name: sha(path)
            for path in [pdf, out / "report_tables.json", out / "report_content.json"]
        },
        "tables": len(tables),
        "existing_metric_rows_checked": len(metrics) + len(overlap),
        "source_feature_rows_checked": len(features),
        "result_range_cells": len(result_checks),
        "references_primary_record_checked": 4,
        "new_fit": False,
        "new_predictions": False,
        "new_download": False,
        "new_fire_labels": False,
        "years_2023_to_2025_opened": False,
        "final_merge": False,
        "risk_categories_accepted": False,
        "docx_render_available_from_bundled_runtime": False,
        "pdf_visual_review_complete": False,
    }
    (out / "readback.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    build()
