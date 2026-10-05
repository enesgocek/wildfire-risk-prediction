"""Prepare approved July 2023 scope; public metadata only, no local raw download."""

import concurrent.futures
import importlib.util
import json
import time
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/cloud_month"
REPORTS = ROOT / "outputs/reports/observation_coverage"
SPEC = importlib.util.spec_from_file_location(
    "month_build_summer", Path(__file__).with_name("build_l2_summer_bundle.py")
)
summer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(summer)
require, sha = summer.require, summer.sha
OLD_BUNDLE_SHA = "0a90b93be0ed31fa468b6ecef61851612bcd255e34caf3ccdb6adf2d6d425f7e"
OLD_RESULTS_SHA = "d5cd87e2960e855b0bdeea34c424161d112a1618b0695768fdda9c463476031e"
DAYS = [f"2023-07-{n:02d}" for n in range(1, 32)]


def fetch(concept):
    path = OUTPUT / "metadata" / f"{concept}.json"
    if not path.exists():
        url = f"https://cmr.earthdata.nasa.gov/search/concepts/{concept}.umm_json"
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=45) as response:
                    value = json.load(response)
                path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
                break
            except (urllib.error.URLError, TimeoutError):
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
    return path.read_bytes()


def notebook(bundle_sha):
    value = summer.notebook(bundle_sha)
    value["metadata"]["colab"]["name"] = "l2_month_2023_07.ipynb"
    cells = value["cells"]
    cells[0]["source"] = [
        "# Temmuz 2023 — aylık gözlem tanıları\n\n",
        "Ücretsiz CPU / Python 3.12. **31 gün, 264 yeni dosya çifti; ",
        "16 Temmuz'un 6 çifti hazır sonuçtan kullanılır.** ",
        "48,30 GB toplam ham transfer yalnızca Colab'a, bir çift sırayla. ",
        "Ham arşiv Drive'a veya bilgisayarına kaydedilmez. ",
        "Önceki ölçümden yaklaşık 9 saat; kurulum, günlük birleştirme ve kayıt ek süre getirir. ",
        "Ücretsiz Colab bu süreyi garanti etmez. Sekmeyi açık bırak; ",
        "bilgisayarın uykuya geçmesin. Sürekli tıklamak gerekmez.\n\n",
        "Her doğrulanmış çift Drive'a ayrı denetim paketi olarak kaydedilir. ",
        "Gün bitince çakışan alanlar birleştirilir ve küçük günlük tablolar saklanır. ",
        "Ham çift ancak kayıt ve geri okuma geçince temizlenir. ",
        "Drive'da bu işe özel **20 GB koruma sınırı** var. ",
        "Kesinti olursa aynı paketle hücreleri tekrar çalıştır: tamamlanmış günler ",
        "ve yarım günün kayıtlı çiftleri yeniden indirilmez. ",
        "Yeni Colab oturumunu sen başlatırsın; otomatik oturum açma yok.\n\n",
        "Hücreleri sırayla çalıştır. NASA bilgilerini gizli istemlere gir. ",
        "Son hücre küçük aylık sonuç ZIP'ini indirir. ",
        "Günlük gözlem durumu belirsiz kalır; bu iş nihai yangın etiketi veya model üretmez.\n",
    ]
    cells[2]["source"] = [
        "".join(cells[2]["source"])
        .replace("l2_summer_B_bundle.zip", "l2_month_2023_07_bundle.zip")
        .replace("/content/wildfire_l2_summer_B", "/content/wildfire_l2_month_202307")
        .replace("B paketi doğrulandı.", "Aylık paket doğrulandı.")
    ]
    cells[3]["source"] = [
        "".join(cells[3]["source"])
        .replace("colab_checkpoints/summer_B", "colab_checkpoints/month_2023_07")
        .replace("run_l2_summer.py", "run_l2_month.py")
        .replace(
            "'--store-root', str(store_root)]",
            "'--store-root', str(store_root), '--budget-gb', '20']",
        )
    ]
    cells[4]["source"] = [
        "# Ay tamamlandıktan sonra Drive'ı yeniden bağlayıp 31 günlük kaydı doğrula.\n"
        "drive.flush_and_unmount(timeout_ms=60000)\n"
        "drive.mount('/content/drive')\n"
        "subprocess.run(command + ['--verify-only'], check=True, env=clean_env)\n"
        "print('31/31 günlük kayıt yeniden bağlama sonrası doğrulandı.')\n"
    ]
    cells[5]["source"] = [
        "# Kesintiden sonra varsa kısmi ZIP de indirilebilir; tam ay olduğu anlamına gelmez.\n"
        "result = root / 'l2_month_2023_07_results.zip'\n"
        "assert result.exists(), 'Henüz tamamlanmış günlük sonuç yok'\n"
        "files.download(str(result))\n"
    ]
    return value


def build():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "metadata").mkdir(exist_ok=True)
    inventory_path = REPORTS / "l2_training_catalogue_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    for value in inventory["outputs"].values():
        require(sha((ROOT / value["path"]).read_bytes()) == value["sha256"], "Catalogue changed")
    catalog = pd.read_csv(ROOT / inventory["outputs"]["granules"]["path"], dtype={"pair_key": str})
    nominal = pd.read_csv(ROOT / inventory["outputs"]["pairs"]["path"], dtype={"pair_key": str})
    month = nominal.loc[nominal.day.str.startswith("2023-07-")]
    require(
        len(month) == 270 and month.pair_status.eq("nominal_unique_pair").all(),
        "Expected 270 nominal month pairs",
    )
    selected = catalog.loc[
        catalog.start_utc.str.startswith("2023-07-")
        & ~catalog.start_utc.str.startswith("2023-07-16T")
    ].copy()
    require(
        len(selected) == 528 and not selected.duplicated(["sensor", "pair_key", "role"]).any(),
        "Expected 528 new unique sources",
    )
    require(
        set(selected.sensor + ":" + selected.pair_key)
        == set(
            month.loc[month.day.ne("2023-07-16"), "sensor"]
            + ":"
            + month.loc[month.day.ne("2023-07-16"), "pair_key"]
        ),
        "Month pair set",
    )
    old_bundle = ROOT / "outputs/cloud_summer/l2_summer_B_bundle.zip"
    received = ROOT / "outputs/cloud_summer/received/l2_summer_results.zip"
    require(sha(old_bundle.read_bytes()) == OLD_BUNDLE_SHA, "Frozen B bundle changed")
    require(sha(received.read_bytes()) == OLD_RESULTS_SHA, "Verified B results changed")
    checked = json.loads((REPORTS / "colab_summer_received_verification.json").read_text())
    require(checked["status"] == "independent_summer_result_readback_passed", "B readback required")
    files = {}
    with zipfile.ZipFile(old_bundle) as old:
        require(old.testzip() is None, "B CRC")
        b = old.read("summer/manifest.json")
        original = json.loads(b)
        for name in original["bundle_files"]:
            data = old.read(name)
            require(sha(data) == original["bundle_files"][name], "B member changed")
            if name.startswith(("scripts/", "data/")):
                require((ROOT / name).read_bytes() == data, "Frozen helper/geography changed")
                files[name] = data
            elif name.startswith("summer/metadata/"):
                files[name] = data
        files["month/bootstrap_manifest.json"] = b
    files["month/bootstrap_results.zip"] = received.read_bytes()
    for name in ("scripts/cloud/run_l2_month.py", "scripts/cloud/l2_daily_compact.py"):
        files[name] = (ROOT / name).read_bytes()
    files["month/catalogue_new.csv"] = selected.to_csv(index=False).encode()
    concepts = selected.concept_id.tolist()
    require(len(set(concepts)) == 528, "Duplicate metadata concept")
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        metadata = {}
        for n, (concept, data) in enumerate(
            zip(concepts, pool.map(fetch, concepts), strict=True), 1
        ):
            metadata[concept] = data
            if n % 50 == 0 or n == 528:
                print(f"Public metadata checked/cached: {n}/528", flush=True)
    pairs = []
    for (sensor, key), group in selected.groupby(["sensor", "pair_key"]):
        require(len(group) == 2 and set(group.role) == {"fire", "geolocation"}, "Pair roles")
        sources, paths = [], {}
        for row in group.itertuples():
            data = metadata[row.concept_id]
            relative = f"month/metadata/{row.concept_id}.json"
            files[relative] = data
            paths[row.role] = relative
            sources.append(
                {
                    "role": row.role,
                    "filename": row.filename,
                    "url": row.data_url,
                    "provider": "LPCLOUD" if row.role == "fire" else "LAADS",
                    "bytes": summer.source_metadata(row, json.loads(data)),
                    "metadata_sha256": sha(data),
                }
            )
        row = group.loc[group.role.eq("fire")].iloc[0]
        pairs.append(
            {
                "sample_id": f"{sensor}:{key}",
                "sensor": sensor,
                "key": key,
                "stem": f"l2_sample_{key}" if sensor == "SNPP" else f"l2_sample_N20_{key}",
                "start_utc": row.start_utc,
                "end_utc": row.end_utc,
                "day_night": row.day_night,
                "sources": sources,
                "metadata": paths,
            }
        )
    pairs.sort(key=lambda p: (p["start_utc"], p["sensor"]))
    total = sum(s["bytes"] for p in pairs for s in p["sources"])
    require(total == 48_301_330_714, "Approved source size changed")
    manifest = {
        "scope": "2023-07",
        "days": DAYS,
        "pairs": pairs,
        "new_source_bytes": total,
        "catalogue_inventory_sha256": sha(inventory_path.read_bytes()),
        "bootstrap_results_sha256": OLD_RESULTS_SHA,
        "bootstrap_bundle_sha256": OLD_BUNDLE_SHA,
        "bootstrap_readback_sha256": sha(
            (REPORTS / "colab_summer_received_verification.json").read_bytes()
        ),
        "negative_label_permitted": False,
        "golden_raw_reference_available": False,
        "bundle_files": {n: sha(data) for n, data in files.items()},
    }
    files["month/manifest.json"] = json.dumps(manifest, indent=2).encode()
    bundle = OUTPUT / "l2_month_2023_07_bundle.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    checksum = sha(bundle.read_bytes())
    book = OUTPUT / "l2_month_2023_07.ipynb"
    book.write_text(json.dumps(notebook(checksum), ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "prepared_at_utc": datetime.now(UTC).isoformat(),
        "status": "prepared_not_cloud_executed",
        "bundle": str(bundle),
        "notebook": str(book),
        "bundle_sha256": checksum,
        "bundle_bytes": bundle.stat().st_size,
        "new_pairs": 264,
        "bootstrap_pairs": 6,
        "days": 31,
        "new_source_bytes": total,
        "drive_job_guard_bytes": 20_000_000_000,
        "local_raw_downloads": 0,
        "negative_label_permitted": False,
    }
    (OUTPUT / "preparation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    build()
