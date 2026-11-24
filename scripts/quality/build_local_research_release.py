"""Copy separate experimental parts into a local release; no labelled merge."""

import json
import shutil
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.ranking_queries import DYNAMIC_FEATURES

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
DATA = BASE / "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1"
REVIEW = BASE / "evaluation_review_package_v1/20261123T141815Z_be04a5fe"
MODEL = BASE / "primary_weather_rank_run_v1/20261123T143258Z_35678270"
UI = BASE / "historical_research_prototype_v2/20261123T195053Z_aa61b349"
DIAGNOSTIC = BASE / "frozen_score_support_diagnostic_v1/20261124T022210Z_e025acc0"
AUDIT = BASE / "frozen_score_support_audit_v1/20261124T022742Z_5a966751"


def main():
    sources = {
        DATA: "86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366",
        REVIEW: "4c1ddd5be410efd3d7dfe1f44324db4046f2dfb2fc4058b718519d654473e05e",
        MODEL: "004f7d27d6b0f1825b2b00d7a2825b311e2483b5f2d73c7063cadd9b45b2946d",
        UI: "1afe43954ce0ccbe139df71e414fda7b0d0faf9dbfc332ae66fbc0beea80caa1",
        DIAGNOSTIC: digest(DIAGNOSTIC / "readback.json"),
        AUDIT: digest(AUDIT / "readback.json"),
    }
    verified = {}
    for folder, expected in sources.items():
        receipt_path = folder / "readback.json"
        if digest(receipt_path) != expected:
            raise ValueError("Frozen receipt changed")
        verified[receipt_path] = expected
        receipt = json.loads(receipt_path.read_bytes())
        for name, sha in receipt.get("artifact_sha256", {}).items():
            path = folder / name
            if digest(path) != sha:
                raise ValueError("Frozen artifact changed")
            verified[path] = sha
    audit = json.loads((AUDIT / "readback.json").read_bytes())
    if (
        audit["status"] != "independent_relational_pair_audit_passed"
        or audit["input_sha256"][(DIAGNOSTIC / "readback.json").relative_to(ROOT).as_posix()]
        != sources[DIAGNOSTIC]
    ):
        raise ValueError("Independent diagnostic audit binding")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "local_research_release_v1" / stamp
    package = out / "package"
    package.mkdir(parents=True)
    files = {}

    def copy(source, name):
        target = package / name
        if target.exists():
            raise ValueError("Duplicate destination")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        sha = digest(source)
        if digest(target) != sha:
            raise ValueError("Copy changed bytes")
        files[name] = {
            "sha256": sha,
            "bytes": target.stat().st_size,
            "source_path": source.relative_to(ROOT).as_posix(),
        }

    def generate(name, body):
        target = package / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        files[name] = {"sha256": digest(target), "bytes": target.stat().st_size, "generated": True}

    for name in (
        "features.csv",
        "inspection_memberships.csv",
        "provenance.csv",
        "feature_dictionary.json",
        "province_support.csv",
        "original_candidate_lineage.csv",
        "original_review_roles.csv",
    ):
        copy(DATA / name, "data/" + name)
    for name in (
        "features.csv",
        "record_memberships.csv",
        "record_provenance.csv",
        "shared_calendar_keys.csv",
        "support_summary.csv",
    ):
        copy(REVIEW / name, "assessment/" + name)
    for name in ("inceleme.html", "research-app.js", "research-core.js", "review_data.js"):
        copy(UI / name, "interface/" + name)
    copy(MODEL / "metrics.csv", "results/primary_weather_metrics.csv")
    scenarios = sorted(p.name for p in MODEL.iterdir() if p.is_dir())
    if len(scenarios) != 9:
        raise ValueError("All nine models required")
    for scenario in scenarios:
        for path in sorted((MODEL / scenario).iterdir()):
            if path.suffix not in (".json", ".csv") or path not in verified:
                raise ValueError("Only verified model artifacts")
            copy(path, "models/" + scenario + "/" + path.name)
    generate("models/dynamic_features.json", json.dumps(DYNAMIC_FEATURES, indent=2) + "\n")
    for name in json.loads((DIAGNOSTIC / "readback.json").read_bytes())["artifact_sha256"]:
        copy(DIAGNOSTIC / name, "results/support/" + name)
    for folder in sources:
        copy(folder / "readback.json", "evidence/" + folder.parent.name + ".json")
    for name, location in {
        "dataset_audit": "experimental_SU_inspection_audit_v2/20261123T103325Z_7ab004e5",
        "model_audit": "primary_weather_rank_audit_v1/20261123T143500Z_2b454296",
        "score_package_audit": "evaluation_review_audit_v1/20261123T142016Z_d7e03899",
    }.items():
        copy(BASE / location / "readback.json", "evidence/" + name + ".json")
    for source_name, target_name in (
        ("DATASET_CARD_2026-11-24.md", "DATASET_CARD.md"),
        ("MODEL_CARD_2026-11-24.md", "MODEL_CARD.md"),
    ):
        copy(ROOT / "docs/research" / source_name, target_name)
    for name in ("pyproject.toml", "uv.lock", "package.json", "package-lock.json"):
        copy(ROOT / name, "environment/" + name)
    for path in sorted((ROOT / "src/wildfire_risk_prediction").glob("*.py")):
        copy(path, "reproducibility/" + path.relative_to(ROOT).as_posix())
    for name in (
        "analyze_frozen_score_support.py",
        "audit_frozen_score_support.py",
        "build_local_research_release.py",
        "verify_local_research_release.py",
        "run_primary_weather_rank.py",
        "audit_primary_weather_rank.py",
    ):
        copy(ROOT / "scripts/quality" / name, "reproducibility/scripts/quality/" + name)
    copy(
        ROOT / "scripts/quality/verify_local_research_release.py",
        "verify_local_research_release.py",
    )
    for name in ("frozen_score_diagnostics_v1.json", "primary_weather_rank_execution_v1.json"):
        copy(ROOT / "configs" / name, "reproducibility/configs/" + name)
    generate(
        "README.md",
        """# Yerel deneysel araştırma teslimi — 24 Kasım 2026

Başlangıç: `interface/inceleme.html` dosyasını yerel tarayıcıda aç.
Bu ekran 44.082 satırın tamamı yerine mevcut iki 2022 değerlendirme
takvimini gösterir. Ana deneysel veri `data/features.csv` içindedir.
`DATASET_CARD.md` ve `MODEL_CARD.md` kapsamı ve sınırlamaları açıklar.

Özellikler, üyelikler ve kaynak izleri ayrı dosyalardır. `target`/L
boş kalır. Bu teslim nihai etiketli birleştirme veya doğrulanmış risk
ürünü değildir. Dokuz ayarın tamamı, mevcut skorlar ve ayrı audit
makbuzları korunur. 2023–2025 verisi, yeni eğitim veya yeni tahmin yoktur.
İl filtreleri örtüşebilir; iki takvimin sayıları bağımsız vaka gibi toplanmaz.

Bütünlüğü yalnız Python standart kütüphanesiyle kontrol etmek için:
`python package/verify_local_research_release.py --release TESLIM_KLASORU`
TESLIM_KLASORU, `package`, `readback.json`, `research_release.zip`
içeren bu üst klasördür. Kontrol ağ erişimi veya eğitim yapmaz.
Manifest kaynak yolları özgün proje konumlarını belgeler; bu yollar
başka bilgisayarda otomatik veri indirme talimatı değildir.

Kod ve ortam dosyaları hash'li yöntem anlık görüntüsüdür. Ham kaynaklar
ve bütün tarihsel bağımlılıklar bu pakete dahil değildir; sıfırdan tam
yeniden eğitim için özgün depo ve makbuzların bağladığı girdiler gerekir.
Ekran kayıtlı skorlarla çevrimdışı çalışır. Model JSON'ları yalnız
15 dinamik alanın sabit sırasını ve uygunluk politikasını bilen araştırma
koduyla kullanılmalıdır. Kaynak takviminden nüfus olasılığı çıkarılamaz.
Bu paket yereldir; kaynak veri veya modeller dış servise yayımlanmamıştır.
""",
    )
    if not all(digest(path) == sha for path, sha in verified.items()):
        raise ValueError("Source artifacts changed during copying")
    base_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = {
        "version": "local_research_release_v1",
        "client_date": "2026-11-24",
        "base_git_commit_before_new_work_commit": base_commit,
        "source_code_snapshot_hashes_authoritative": True,
        "experimental_research_only": True,
        "labelled_training_dataset": False,
        "final_merge": False,
        "files": files,
    }
    manifest_path = package / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    archive = out / "research_release.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(package.rglob("*")):
            if path.is_file():
                zipped.write(path, path.relative_to(package).as_posix())
    receipt = {
        "status": "local_research_release_built_pending_separate_audit",
        "files_including_manifest": len(files) + 1,
        "manifest_sha256": digest(manifest_path),
        "zip_sha256": digest(archive),
        "zip_bytes": archive.stat().st_size,
        "new_training_or_predictions": 0,
        "new_true_Y_or_L": 0,
        "final_merge": False,
        "source_receipt_sha256": {str(p.relative_to(ROOT)): sha for p, sha in sources.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    (out / "readback.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT).as_posix(), receipt["status"], flush=True)


if __name__ == "__main__":
    main()
