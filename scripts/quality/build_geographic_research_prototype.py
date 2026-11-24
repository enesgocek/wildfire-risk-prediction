"""Add offline geography and fixed evidence navigation; preserve all scientific bytes."""

import csv
import json
import os
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction import prototype_geography as geography
from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PARENT = BASE / "historical_research_prototype_v2/20261123T195053Z_aa61b349"
CASES = BASE / "frozen_rank_case_review_v1/20261124T024256Z_abeb3e00"
RUN = BASE / "source_disjoint_frozen_assessment_v1/20261124T031245Z_91cd329d"
AUDIT = BASE / "source_disjoint_frozen_assessment_audit_v1/20261124T031414Z_9c5bc04c"
PLAN = BASE / "source_disjoint_evaluation_preparation_v1/20261124T030406Z_9554fb98"


def csv_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    pins = {
        PARENT
        / "readback.json": "1afe43954ce0ccbe139df71e414fda7b0d0faf9dbfc332ae66fbc0beea80caa1",
        CASES / "readback.json": "a65579afa7165b72a830f22e39367bb9331e100c0b5aa7d0b982bdf8dcc8c4af",
        RUN / "readback.json": "7f6e16ff58084954610dea8ca41d9ca87ece9fd02192b076cfec5973845a5d23",
        AUDIT / "readback.json": "caf4f7650b1d8c5842e27a14d387081bb1967aa8b728a10e83c82d012afc2275",
        PLAN / "readback.json": "c20b988ba0ab1387f4e4121efeabe6a6939e30eac2bedbf7c6ba9cfbafffa45f",
        Path(geography.__file__): digest(Path(geography.__file__)),
    }
    for folder in (PARENT, CASES, RUN, PLAN):
        receipt = json.loads((folder / "readback.json").read_bytes())
        pins.update({folder / name: sha for name, sha in receipt["artifact_sha256"].items()})
    manifest_path = ROOT / "data/aoi/manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    pins[manifest_path] = digest(manifest_path)
    grid_path, aoi_path = ROOT / "data/aoi/grid_5km.geojson", ROOT / "data/aoi/aoi.geojson"
    pins[grid_path], pins[aoi_path] = manifest["grid_sha256"], manifest["aoi_sha256"]
    assets = {
        "inceleme.html": Path(__file__).with_name("research_prototype_v3_template.html"),
        "research-app.js": Path(__file__).with_name("research_prototype_v3_app.js"),
        "research-map.js": Path(__file__).with_name("research_prototype_v3_map.js"),
        "research-core.js": PARENT / "research-core.js",
        "review_data.js": PARENT / "review_data.js",
    }
    test = ROOT / "tests/js/research_prototype_v3_dom.test.cjs"
    for path in (*assets.values(), test, ROOT / "package-lock.json"):
        pins[path] = digest(path)
    require(
        all(digest(p) == sha for p, sha in pins.items()),
        "Unchanged scientific sources and geometry",
    )
    raw = (PARENT / "review_data.js").read_text(encoding="utf-8").strip()
    data = json.loads(raw.removeprefix("globalThis.RESEARCH_DATA=")[:-1])
    require(
        data["scientific_state"]
        == {
            "target": None,
            "accepted_L_membership": None,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
            "fire_risk_validated": False,
        },
        "Unknown target, research prototype only",
    )
    requested = {r["grid"] for r in data["records"]}
    geo = geography.prepare(
        json.loads(grid_path.read_bytes()), json.loads(aoi_path.read_bytes()), requested
    )
    examples = [
        {
            "case_id": r["case_id"],
            "cohort": r["cohort"],
            "grid": r["grid_id"],
            "time": r["source_prediction_timestamp_utc"],
            "illustrative_tier": r["illustrative_tier"],
        }
        for r in csv_rows(CASES / "illustrative_cases.csv")
    ]
    lookup = {(r["cohort"], r["grid"], r["time"]): r for r in data["records"]}
    require(
        len(examples) == 12
        and all((r["cohort"], r["grid"], r["time"]) in lookup for r in examples),
        "Exact existing illustrative records",
    )
    require(
        all(r["time"].startswith("2022-") for r in data["records"]), "Existing 2022 records only"
    )
    metrics = csv_rows(RUN / "metrics.csv")
    support = csv_rows(PLAN / "planned_support.csv")
    groups = [
        ("original_source_calendar", "Özgün kaynak takvimi"),
        ("exclude_any_same_key_satellite_proposal", "Ortak S adayları çıkarıldı"),
        ("absent_from_four_province_calendar", "Dört-il takviminde anahtarı yok"),
    ]
    summaries = []
    for group, label in groups:
        item = {
            "source_group": group,
            "label": label,
            "source_days": int(
                next(
                    r
                    for r in support
                    if r["source_group"] == group and r["slice"] == "all_same_grid_month"
                )["eligible_source_anchors"]
            ),
        }
        for prefix, section in (("general", "all_same_grid_month"), ("near", "gap_1_to_3_days")):
            values = [
                float(r["auxiliary_pair_AUC"])
                for r in metrics
                if r["source_group"] == group
                and r["variant"] == "primary_weather_XGBoost"
                and r["slice"] == section
            ]
            require(len(values) == 9, "All nine existing metric values")
            item[prefix + "_min"], item[prefix + "_max"] = min(values), max(values)
        summaries.append(item)
    out = (
        BASE
        / "historical_research_prototype_v3"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    links = []
    for label, relative in (
        ("Veri kartı", "docs/research/DATASET_CARD_2026-11-24.md"),
        ("Model kartı", "docs/research/MODEL_CARD_2026-11-24.md"),
        ("Sonuç ve sınırlamalar", "docs/SOURCE_DISJOINT_EVALUATION_RESULTS_2026-11-24.md"),
    ):
        path = ROOT / relative
        require(path.is_file(), "Existing local evidence file")
        links.append(
            {
                "label": label,
                "path": os.path.relpath(path, out).replace("\\", "/"),
                "sha256": digest(path),
            }
        )
    context = {
        "version": "existing_research_context_v1",
        "examples": examples,
        "overlap_summary": summaries,
        "links": links,
        "assessment_readback_sha256": pins[RUN / "readback.json"],
        "assessment_audit_sha256": pins[AUDIT / "readback.json"],
        "case_readback_sha256": pins[CASES / "readback.json"],
    }
    for name, value in (("geography_data.js", geo), ("research_context.js", context)):
        prefix = (
            "globalThis.RESEARCH_GEOGRAPHY="
            if name == "geography_data.js"
            else "globalThis.RESEARCH_CONTEXT="
        )
        (out / name).write_text(
            prefix
            + json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
            + ";\n",
            encoding="utf-8",
        )
    for name, source in assets.items():
        shutil.copyfile(source, out / name)
    node = shutil.which("node")
    require(node is not None, "Existing local Node runtime")
    for name in ("research-app.js", "research-map.js", "geography_data.js", "research_context.js"):
        subprocess.run(
            [node, "--check", str(out / name)], check=True, capture_output=True, timeout=30
        )
    result = subprocess.run(
        [node, "--test", "--test-reporter=tap", str(test)],
        cwd=ROOT,
        env=os.environ | {"RESEARCH_PROTOTYPE_DIR": str(out)},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
        check=False,
    )
    (out / "dom_interactions.tap").write_text(result.stdout + result.stderr, encoding="utf-8")
    require(
        result.returncode == 0
        and re.search(r"# tests 14\b", result.stdout)
        and re.search(r"# pass 14\b", result.stdout),
        "Fourteen actual offline DOM tests",
    )
    require(
        all(digest(p) == sha for p, sha in pins.items()), "All parent and input bytes preserved"
    )
    (out / "README.txt").write_text(
        "Yerel arastirma prototipi v3: inceleme.html dosyasini ac.\n"
        "Hucre konum haritasi, 12 ornek kisayolu ve mevcut sonuc ozeti eklendi.\n"
        "Skor/ozellik verisi ve hesap cekirdegi v2 ile byte olarak ayni.\n"
        "Harita yangin konumu veya risk rengi gostermez; dis ag kullanmaz.\n"
        "Kanıt baglantilari ayni proje klasorundeki belgeleri acar.\n"
        "DOM testleri gorsel tarayici render kontrolu degildir.\n",
        encoding="utf-8",
    )
    body = {
        "status": "offline_geographic_prototype_DOM_passed_pending_separate_data_audit",
        "parent_readback_sha256": pins[PARENT / "readback.json"],
        "scientific_payload_sha256": digest(out / "review_data.js"),
        "scientific_core_sha256": digest(out / "research-core.js"),
        "requested_cell_ids": len(requested),
        "mapped_cell_ids": len(geo["cells"]),
        "missing_cell_ids": geo["missing_grid_ids"],
        "illustrative_shortcuts": len(examples),
        "offline_DOM_tests_passed": 14,
        "actual_browser_visual_render_verified": False,
        "new_training_predictions_labels_or_closed_year_values": False,
        "validated_risk_colors": False,
        "external_upload_or_network_access": False,
        "user_technical_test_gate_required": False,
        "final_merge": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha for p, sha in pins.items()},
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "producer_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(
        out.relative_to(ROOT).as_posix(),
        body["status"],
        "mapped_cells",
        len(geo["cells"]),
        flush=True,
    )


if __name__ == "__main__":
    main()
