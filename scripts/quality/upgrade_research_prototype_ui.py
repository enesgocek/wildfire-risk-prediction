"""Clarify UI labels and persist offline DOM interaction tests; preserve all scientific bytes."""

import json
import os
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PARENT = BASE / "historical_research_prototype_v1/20261123T144811Z_555ee371"


def main():
    pins = {
        PARENT / "readback.json": "37b544bd96a9cd74ef5cb4ec30185bb401363bfae5b9acf3caded4008204e6ea"
    }
    require(digest(PARENT / "readback.json") == pins[PARENT / "readback.json"], "Frozen v1 receipt")
    parent = json.loads((PARENT / "readback.json").read_bytes())
    pins.update({PARENT / p: h for p, h in parent["artifact_sha256"].items()})
    source = Path(__file__).parent
    assets = {
        "inceleme.html": source / "research_prototype_v2_template.html",
        "research-app.js": source / "research_prototype_v2_app.js",
        "research-core.js": PARENT / "research-core.js",
        "review_data.js": PARENT / "review_data.js",
    }
    for p in (
        *assets.values(),
        ROOT / "package.json",
        ROOT / "package-lock.json",
        ROOT / "tests/js/research_prototype_dom.test.cjs",
    ):
        pins[p] = digest(p)
    require(
        all(digest(p) == h for p, h in pins.items()), "Current immutable parent and new UI inputs"
    )
    installed = json.loads((ROOT / "node_modules/jsdom/package.json").read_bytes())
    lock = json.loads((ROOT / "package-lock.json").read_bytes())
    require(
        installed["version"] == lock["packages"]["node_modules/jsdom"]["version"] == "31.0.1",
        "Pinned DOM test engine",
    )
    out = (
        BASE
        / "historical_research_prototype_v2"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    for name, path in assets.items():
        shutil.copyfile(path, out / name)
    require(
        digest(out / "review_data.js") == parent["artifact_sha256"]["review_data.js"]
        and digest(out / "research-core.js") == parent["artifact_sha256"]["research-core.js"],
        "Scientific payload and ranking/filter calculation bytes unchanged",
    )
    node = shutil.which("node")
    require(node is not None, "Installed local Node")
    for name in ("research-core.js", "research-app.js"):
        subprocess.run(
            [node, "--check", str(out / name)], check=True, capture_output=True, timeout=30
        )
    result = subprocess.run(
        [
            node,
            "--test",
            "--test-reporter=tap",
            str(ROOT / "tests/js/research_prototype_dom.test.cjs"),
        ],
        cwd=ROOT,
        env=os.environ | {"RESEARCH_PROTOTYPE_DIR": str(out)},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    (out / "dom_interactions.tap").write_text(result.stdout + result.stderr, encoding="utf-8")
    require(
        result.returncode == 0
        and re.search(r"# tests 9\b", result.stdout)
        and re.search(r"# pass 9\b", result.stdout)
        and re.search(r"# fail 0\b", result.stdout),
        "Nine actual app DOM interaction tests, including new context/label checks",
    )
    (out / "README.txt").write_text(
        "Yerel arastirma prototipi v2. inceleme.html dosyasi acilarak kullanilir.\n"
        "Puan hesaplanan kayit karti acik adlandirildi. Aktif il ek filtresi gorunur.\n"
        "Inceleme grubu degisince il ve hucre ek filtreleri temizlenir.\n"
        "Veri ve hesap cekirdegi v1 ile birebir ayni; yeni etiket veya model yok.\n"
        "Rutin sayim/filtre/tiklama testleri otomatik yapildi; kullanici test kapisi yok.\n"
        "DOM testleri gercek tarayici gorsel render dogrulamasi degildir.\n",
        encoding="utf-8",
    )
    require(
        all(digest(p) == h for p, h in pins.items()), "All original bytes preserved after tests"
    )
    body = {
        "status": "offline_prototype_DOM_interactions_passed_no_user_test_gate",
        "parent": PARENT.relative_to(ROOT).as_posix(),
        "parent_readback_sha256": pins[PARENT / "readback.json"],
        "actual_offline_DOM_tests_passed": 9,
        "DOM_engine": "jsdom==31.0.1",
        "validation_scope": (
            "HTML_DOM_events_filters_cards_table_pagination_SVG_and_feature_details"
        ),
        "actual_browser_visual_render_verified": False,
        "user_technical_test_gate_required": False,
        "payload_sha256_preserved": digest(out / "review_data.js"),
        "scientific_data_or_calculation_core_changed": False,
        "new_models_predictions_labels_or_closed_year_values": False,
        "final_merge_performed": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    path = out / "readback.json"
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), "readback_sha256", digest(path), flush=True)
    print("nine offline DOM interaction tests passed; no user technical gate", flush=True)


if __name__ == "__main__":
    main()
