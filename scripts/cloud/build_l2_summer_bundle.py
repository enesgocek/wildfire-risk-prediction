"""Prepare the user's approved B scope; fetch only 12 public UMM metadata files."""

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
REPORTS = ROOT / "outputs/reports/observation_coverage"
OUTPUT = ROOT / "outputs/cloud_summer"
SPEC = importlib.util.spec_from_file_location(
    "summer_single", Path(__file__).with_name("build_l2_pilot_bundle.py")
)
single = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(single)
sha = single.sha


def require(ok, message):
    if not ok:
        raise ValueError(message)


def source_metadata(row, metadata):
    require(
        {
            item["Identifier"].removesuffix(".nc")
            for item in metadata["DataGranule"]["Identifiers"]
            if item["IdentifierType"] == "ProducerGranuleId"
        }
        == {row.filename.removesuffix(".nc")},
        "Producer granule differs",
    )
    collection = metadata["CollectionReference"]
    require(collection["ShortName"] == row.product, "Metadata product")
    require(
        collection["Version"] in ({"2.1", "021"} if row.product == "VJ103IMG" else {"2", "002"}),
        "Metadata version",
    )
    dates = metadata["TemporalExtent"]["RangeDateTime"]
    require(
        pd.Timestamp(dates["BeginningDateTime"]) == pd.Timestamp(row.start_utc)
        and pd.Timestamp(dates["EndingDateTime"]) == pd.Timestamp(row.end_utc),
        "Metadata interval",
    )
    require(row.data_url in {u["URL"] for u in metadata["RelatedUrls"]}, "Data URL changed")
    entries = metadata["DataGranule"]["ArchiveAndDistributionInformation"]
    require(len(entries) == 1, "Ambiguous archive entry")
    entry = entries[0]
    size = entry.get("SizeInBytes")
    if size is None:
        require(entry["SizeUnit"] == "MB", "Unsupported size unit")
        size = round(entry["Size"] * 2**20)
    require(isinstance(size, int) and size > 0, "Invalid exact file size")
    require(abs(size - row.catalogue_size_bytes_estimate) <= 1, "Catalogue/UMM size differs")
    return size


def fetch(concept):
    directory = OUTPUT / "metadata"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{concept}.json"
    if not path.exists():
        url = f"https://cmr.earthdata.nasa.gov/search/concepts/{concept}.umm_json"
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=45) as response:
                    value = json.load(response)
                path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
                break
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise
                time.sleep(attempt + 1)
    return path.read_bytes()


def notebook(bundle_sha):
    value = single.make_notebook(bundle_sha)
    value["metadata"]["colab"]["name"] = "l2_summer_B.ipynb"
    cells = value["cells"]
    cells[0]["source"] = [
        "# Yaz kontrolü — B seçeneği\n\n",
        "Ücretsiz CPU / Python 3.12. **16 Temmuz 2023, iki sensör, altı dosya çifti.** ",
        "Yaklaşık 1,10 GB ham kaynak yalnızca Colab'a iner. ",
        "Tek çalıştırma altı çifti sırayla işler; ",
        "ham arşiv Drive'a yüklenmez. Sınıf/QA, yaklaşık alan ve doğal tarama zamanlarını sınar; ",
        "nihai yangın etiketi veya model üretmez.\n\n",
        "Her doğrulanmış çift için ayrı sonuç ZIP'i ve tamamlanma kaydı Drive'daki ",
        "MyDrive/wildfire-risk-prediction/colab_checkpoints/summer_B altında saklanır. ",
        "Kaydetme/geri okuma tamamlandıktan sonra Colab'daki o ham çift temizlenir. ",
        "Yeni oturumda aynı notebook ve paketle devam edebilirsin; ",
        "tamamlanan çiftler yeniden inmez.\n\n",
        "Hücreleri sırayla çalıştır. NASA bilgilerini yalnızca gizli istemlere yaz. ",
        "Google Drive erişimini kendi hesabında onayla. Son hücreyle sonuç ZIP'ini indir; ",
        "yerel bağımsız sonuç denetimi bundan sonra yapılacak.\n",
    ]
    cells[2]["source"] = [
        f"""
from google.colab import files
from pathlib import Path
import hashlib, io, zipfile
uploaded = files.upload()  # l2_summer_B_bundle.zip seç.
assert set(uploaded) == {{'l2_summer_B_bundle.zip'}}
data = uploaded.pop('l2_summer_B_bundle.zip')
assert hashlib.sha256(data).hexdigest() == '{bundle_sha}', 'Paket sürümü farklı'
root = Path('/content/wildfire_l2_summer_B')
root.mkdir(exist_ok=True)
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    assert len(archive.namelist()) == len(set(archive.namelist()))
    assert all((root / n).resolve().is_relative_to(root.resolve()) for n in archive.namelist())
    for n in archive.namelist():
        target = root / n
        content = archive.read(n)
        if target.exists():
            assert target.read_bytes() == content, 'Mevcut paket sürümü farklı'
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
del data, uploaded
print('B paketi doğrulandı.')
""".lstrip()
    ]
    cells[3]["source"] = [
        """
from google.colab import drive
import getpass
drive.mount('/content/drive')
store_root = Path('/content/drive/MyDrive/wildfire-risk-prediction/colab_checkpoints/summer_B')
command = [str(pilot_python), str(root / 'scripts/cloud/run_l2_summer.py'),
           '--store-root', str(store_root)]
auth_env = clean_env.copy()
for key in ('EARTHDATA_USERNAME', 'EARTHDATA_PASSWORD', 'EARTHDATA_TOKEN'):
    auth_env.pop(key, None)
try:
    auth_env['EARTHDATA_USERNAME'] = getpass.getpass('Earthdata kullanıcı adın: ')
    auth_env['EARTHDATA_PASSWORD'] = getpass.getpass('Earthdata parolan: ')
    subprocess.run(command, check=True, env=auth_env)
finally:
    auth_env.clear()
    del auth_env
""".lstrip()
    ]
    cells[4] = {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": [
            """
# Drive yazılarını eşitle, yeniden bağla ve altı tamamlanmış çifti yeniden doğrula.
drive.flush_and_unmount(timeout_ms=60000)
drive.mount('/content/drive')
subprocess.run(command + ['--verify-only'], check=True, env=clean_env)
print('6/6 kayıt Drive yeniden bağlama sonrası doğrulandı.')
""".lstrip()
        ],
    }
    cells[5]["source"] = [
        """
result = root / 'l2_summer_results.zip'
assert result.exists(), 'Henüz sonuç ZIP\u2019i yok'
files.download(str(result))
""".lstrip()
    ]
    return value


def build():
    inventory_path = REPORTS / "summer_control_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    readback = json.loads((REPORTS / "summer_control_readback.json").read_text())
    require(
        readback["status"] == "passed"
        and readback["inventory_sha256"] == sha(inventory_path.read_bytes()),
        "Current independently verified inventory required",
    )
    for name, checksum in (inventory["sources_sha256"] | inventory["outputs_sha256"]).items():
        require(sha((ROOT / name).read_bytes()) == checksum, "Inventory input/output changed")
    selected = pd.read_csv(
        REPORTS / "summer_control_B_one_day_granules.csv", dtype={"pair_key": str}
    )
    require(
        len(selected) == 12 and selected.start_utc.str.startswith("2023-07-16T").all(),
        "Fixed B scope",
    )
    names = (
        "scripts/cloud/run_l2_summer.py",
        "scripts/cloud/run_l2_day.py",
        "scripts/cloud/run_l2_pilot.py",
        "scripts/cloud/verify_l2_pilot_results.py",
        "scripts/cloud/checkpoint_store.py",
        "scripts/cloud/requirements_l2_pilot.txt",
        "scripts/firms/inspect_l2_observation_sample.py",
        "scripts/firms/estimate_l2_observed_area.py",
        "scripts/firms/combine_l2_area_estimates.py",
        "scripts/firms/audit_l2_observation_timing.py",
        "data/aoi/aoi.geojson",
        "data/aoi/grid_5km.geojson",
        "data/interim/grid_aoi_parts.geojson",
    )
    files = {name: (ROOT / name).read_bytes() for name in names}
    files["summer/catalogue.csv"] = selected.to_csv(index=False).encode()
    pairs = []
    for (sensor, key), group in selected.groupby(["sensor", "pair_key"]):
        require(
            len(group) == 2 and set(group.role) == {"fire", "geolocation"}, "One source per role"
        )
        sources, metadata_paths = [], {}
        for row in group.itertuples():
            data = fetch(row.concept_id)
            relative = f"summer/metadata/{row.concept_id}.json"
            files[relative] = data
            metadata_paths[row.role] = relative
            metadata = json.loads(data)
            sources.append(
                {
                    "role": row.role,
                    "filename": row.filename,
                    "url": row.data_url,
                    "provider": "LPCLOUD" if row.role == "fire" else "LAADS",
                    "bytes": source_metadata(row, metadata),
                    "metadata_sha256": sha(data),
                }
            )
        row = group.loc[group.role.eq("fire")].iloc[0]
        stem = f"l2_sample_{key}" if sensor == "SNPP" else f"l2_sample_N20_{key}"
        pairs.append(
            {
                "sample_id": f"{sensor}:{key}",
                "sensor": sensor,
                "key": key,
                "stem": stem,
                "start_utc": row.start_utc,
                "end_utc": row.end_utc,
                "day_night": row.day_night,
                "sources": sources,
                "metadata": metadata_paths,
            }
        )
    pairs.sort(key=lambda p: (p["start_utc"], p["sensor"]))
    manifest = {
        "day": "2023-07-16",
        "option": "B_one_day",
        "pairs": pairs,
        "inventory_sha256": sha(inventory_path.read_bytes()),
        "bundle_files": {n: sha(data) for n, data in files.items()},
        "golden_raw_reference_available": False,
        "negative_label_permitted": False,
    }
    files["summer/manifest.json"] = json.dumps(manifest, indent=2).encode()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    bundle = OUTPUT / "l2_summer_B_bundle.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    book = OUTPUT / "l2_summer_B.ipynb"
    book.write_text(
        json.dumps(notebook(sha(bundle.read_bytes())), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    result = {
        "prepared_at_utc": datetime.now(UTC).isoformat(),
        "selected_option": "B_one_day",
        "status": "prepared_not_cloud_executed",
        "bundle": str(bundle),
        "notebook": str(book),
        "bundle_sha256": sha(bundle.read_bytes()),
        "bundle_bytes": bundle.stat().st_size,
        "pairs": len(pairs),
        "source_bytes": sum(s["bytes"] for p in pairs for s in p["sources"]),
        "largest_pair_bytes": max(sum(s["bytes"] for s in p["sources"]) for p in pairs),
        "raw_local_downloads": 0,
        "negative_label_permitted": False,
    }
    (OUTPUT / "preparation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    build()
