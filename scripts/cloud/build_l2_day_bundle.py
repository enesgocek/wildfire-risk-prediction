"""Build a bounded, credential-free two-sensor training-day Colab experiment."""

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "outputs/reports/observation_coverage"
OUTPUT = ROOT / "outputs/cloud_day"
SPEC = importlib.util.spec_from_file_location(
    "single_builder", ROOT / "scripts/cloud/build_l2_pilot_bundle.py"
)
single = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(single)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def make_notebook(bundle_sha):
    notebook = single.make_notebook(bundle_sha)
    notebook["metadata"]["colab"]["name"] = "l2_day_isolated.ipynb"
    cells = notebook["cells"]
    cells[0]["source"] = [
        "# İki sensörlü bir eğitim günü\n\n",
        "Ücretsiz CPU ve Python 3.12 kullan. 14 Ocak 2019: 8 geçiş, 16 dosya, toplam yaklaşık ",
        "1,46 GB NASA indirmesi. Dosyalar **Colab'da bir çift halinde** işlenir; ",
        "doğrulanmış sonuç ve checkpoint ZIP'i yazıldıktan sonra geçici ham çift silinir.\n\n",
        "İlk geçişten sonra süreç durur, ikinci süreç checkpoint'i okuyup devam eder. ",
        "Tepe çocuk süreç RAM'i ve 0,2 saniye aralıklı disk kullanımı raporlanır. ",
        "Etiket veya model üretmez. Hücreleri sırayla çalıştır.\n\n",
        "Colab oturumu kapanırsa geçici disk kaybolabilir. Sonuç ZIP'ini indirip sakla; ",
        "yeni oturumda paket yükleme hücresinde paketle birlikte bu ZIP'i de seçebilirsin.\n",
    ]
    cells[2]["source"] = [
        """
from google.colab import files
from pathlib import Path
import hashlib, zipfile, io
uploaded = files.upload()  # l2_day_bundle.zip; varsa önceki l2_day_results.zip de seçilebilir.
assert 'l2_day_bundle.zip' in uploaded
assert set(uploaded) <= {'l2_day_bundle.zip', 'l2_day_results.zip'}, 'Beklenmeyen dosya'
data = uploaded.pop('l2_day_bundle.zip')
assert hashlib.sha256(data).hexdigest() == 'BUNDLE_SHA', 'Paket sürümü farklı'
root = Path('/content/wildfire_l2_day')
root.mkdir(exist_ok=True)
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    assert all((root / name).resolve().is_relative_to(root.resolve())
               for name in archive.namelist())
    archive.extractall(root)
restore_args = []
if 'l2_day_results.zip' in uploaded:
    previous = root / 'received_checkpoint.zip'
    previous.write_bytes(uploaded.pop('l2_day_results.zip'))
    restore_args = ['--restore-results', str(previous)]
del data, uploaded
print('Paket doğrulandı; 8 geçiş ve iki sensör hazır.')
""".lstrip().replace("BUNDLE_SHA", bundle_sha)
    ]
    cells[3]["source"] = [
        """
import getpass, subprocess
auth_env = clean_env.copy()
for key in ('EARTHDATA_USERNAME', 'EARTHDATA_PASSWORD', 'EARTHDATA_TOKEN'):
    auth_env.pop(key, None)
try:
    auth_env['EARTHDATA_USERNAME'] = getpass.getpass('Earthdata kullanıcı adın: ')
    auth_env['EARTHDATA_PASSWORD'] = getpass.getpass('Earthdata parolan: ')
    command = [str(pilot_python), str(root / 'scripts/cloud/run_l2_day.py')]
    subprocess.run(command + ['--stop-after', '1'] + restore_args, check=True, env=auth_env)
    print('İlk süreç tamamlandı; checkpoint ile yeni süreçte devam ediliyor.')
    subprocess.run(command, check=True, env=auth_env)
finally:
    auth_env.clear()
    del auth_env
""".lstrip()
    ]
    cells[4]["source"] = [
        "Sonuç **passed_all_eight_references** ise sekiz geçişin bütün hücre/QA sayımları ",
        "yerel referanslarla eşleşti. İlk çalıştırmada ikinci süreçte en az bir checkpoint ",
        "yeniden kullanılmış olmalı. Bu, günlük gözlem alanı veya nihai etiket onayı değildir. ",
        "İşleme sırasında hata olursa son hücreyi çalıştırarak varsa tamamlanan checkpoint'leri ",
        "indir ve hata metniyle paylaş. Aynı paketle devam edilebilir.\n",
    ]
    cells[5]["source"] = [
        """
result = root / 'l2_day_results.zip'
assert result.exists(), 'Henüz doğrulanmış bir sonuç ZIP\u2019i yok.'
files.download(str(result))
""".lstrip()
    ]
    return notebook


def build():
    names = (
        "scripts/firms/inspect_l2_observation_sample.py",
        "scripts/cloud/run_l2_day.py",
        "scripts/cloud/run_l2_pilot.py",
        "scripts/cloud/verify_l2_pilot_results.py",
        "scripts/cloud/requirements_l2_pilot.txt",
        "data/aoi/aoi.geojson",
        "data/aoi/grid_5km.geojson",
    )
    files = {name: (ROOT / name).read_bytes() for name in names}
    catalogue_path = REPORTS / "l2_training_catalogue_granules.csv"
    catalogue = pd.read_csv(catalogue_path, dtype=str)
    catalogue = catalogue[catalogue.start_utc.str.startswith("2019-01-14T")]
    require(len(catalogue) == 16, "Expected the same 16 catalogue entries")
    files["day/catalogue_day.csv"] = catalogue.to_csv(index=False).encode()
    pairs, source_identities = [], set()
    for path in REPORTS.glob("l2_sample*2019014*_audit.json"):
        report = json.loads(path.read_text())
        for name, field in (
            (names[0], "script_sha256"),
            (names[-2], "aoi_sha256"),
            (names[-1], "grid_sha256"),
        ):
            require(sha(files[name]) == report[field], "Reference provenance changed")
        stem = path.name.removesuffix("_audit.json")
        reference = f"day/reference/{stem}"
        files[reference + "_audit.json"] = path.read_bytes()
        files[reference + "_grid_centers.csv"] = (REPORTS / f"{stem}_grid_centers.csv").read_bytes()
        sources, metadata = [], {}
        for role, source in report["sources"].items():
            matches = [
                p
                for p in REPORTS.glob("*_metadata.json")
                if sha(p.read_bytes()) == source["cmr_metadata_sha256"]
            ]
            require(len(matches) == 1, "Exact source metadata absent")
            metadata_path = matches[0]
            relative = "day/metadata/" + metadata_path.name
            files[relative] = metadata_path.read_bytes()
            metadata[role] = relative
            cmr = json.loads(metadata_path.read_text())
            filename = source["path"].replace("\\", "/").rsplit("/", 1)[-1]
            rows = catalogue[
                (catalogue.sensor == report["sensor"])
                & (catalogue.role == role)
                & (catalogue.filename == filename)
            ]
            require(len(rows) == 1, "Local source not unique in day's catalogue")
            url = rows.iloc[0].data_url
            require(url in {entry["URL"] for entry in cmr["RelatedUrls"]}, "Data URL differs")
            source_identities.add((report["sensor"], role, filename))
            sources.append(
                {
                    "role": role,
                    "filename": filename,
                    "url": url,
                    "provider": "LPCLOUD" if role == "fire" else "LAADS",
                    "bytes": source["bytes"],
                    "sha256": source["sha256"],
                }
            )
        pairs.append(
            {
                "sample_id": report["sample_id"],
                "sensor": report["sensor"],
                "key": report["pair_key"],
                "stem": stem,
                "start_utc": report["start_utc"],
                "day_night": report["day_night_flag"],
                "sources": sources,
                "metadata": metadata,
                "local_directory": source["path"].replace("\\", "/").split("/")[-2],
                "reference_audit": reference + "_audit.json",
                "reference_csv": reference + "_grid_centers.csv",
            }
        )
    require(len(pairs) == 8, "Expected eight reference pairs")
    require(
        source_identities
        == set(zip(catalogue.sensor, catalogue.role, catalogue.filename, strict=True)),
        "Catalogue day not fully represented",
    )
    pairs.sort(key=lambda pair: (pair["start_utc"], pair["sensor"]))
    manifest = {
        "day": "2019-01-14",
        "pairs": pairs,
        "catalogue_source_sha256": sha(catalogue_path.read_bytes()),
        "bundle_files": {name: sha(data) for name, data in files.items()},
        "negative_label_permitted": False,
    }
    files["day/manifest.json"] = json.dumps(manifest, indent=2).encode()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / "l2_day_bundle.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    bundle_sha = sha(destination.read_bytes())
    notebook = OUTPUT / "l2_day_isolated.ipynb"
    notebook.write_text(
        json.dumps(make_notebook(bundle_sha), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "bundle": str(destination),
                "bundle_bytes": destination.stat().st_size,
                "bundle_sha256": bundle_sha,
                "notebook": str(notebook),
                "pairs": len(pairs),
                "total_payload_bytes": sum(s["bytes"] for p in pairs for s in p["sources"]),
                "largest_pair_bytes": max(sum(s["bytes"] for s in p["sources"]) for p in pairs),
            }
        )
    )


if __name__ == "__main__":
    build()
