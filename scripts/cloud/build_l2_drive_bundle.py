"""Prepare a Drive copy/recovery proof using the already verified cloud day."""

import importlib.util
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/cloud_drive"
SPEC = importlib.util.spec_from_file_location(
    "pilot_builder", Path(__file__).with_name("build_l2_pilot_bundle.py")
)
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


def notebook(bundle_sha):
    value = pilot.make_notebook(bundle_sha)
    value["metadata"]["colab"]["name"] = "l2_drive_storage.ipynb"
    cells = value["cells"]
    cells[0]["source"] = [
        "# Google Drive kayıt ve geri yükleme denemesi\n\n",
        "Python 3.12 / ücretsiz CPU. Dün doğrulanan küçük sonuç paketle birlikte gelir; ",
        "**yeni uydu indirmesi yapılmaz ve NASA parolası istenmez.**\n\n",
        "Hücreleri sırayla çalıştır. Google, Drive erişimini onaylamanı isteyecek. ",
        "Kod yalnızca MyDrive/wildfire-risk-prediction/colab_checkpoints altında ",
        "kendi sonuçlarını yazar. Drive izni teknik olarak daha geniş erişim sağlar; ",
        "notebook'u güvenmediğin kodla paylaşma/değiştirme.\n\n",
        "Deneme küçük ZIP'i kaydeder, SHA ve bütün hücre sonuçlarını geri okur; ",
        "Drive bağlantısını boşaltıp yeniden bağlayarak tekrar denetler. ",
        "Mevcut Drive dosyaları silinmez, ham uydu yüklenmez.\n",
    ]
    cells[2]["source"] = [
        f"""
from google.colab import files
from pathlib import Path
import hashlib, zipfile, io
uploaded = files.upload()  # Yalnızca l2_drive_bundle.zip seç.
assert set(uploaded) == {{'l2_drive_bundle.zip'}}
data = uploaded.pop('l2_drive_bundle.zip')
assert hashlib.sha256(data).hexdigest() == '{bundle_sha}', 'Paket sürümü farklı'
root = Path('/content/wildfire_l2_drive')
root.mkdir(exist_ok=True)
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    assert all((root / name).resolve().is_relative_to(root.resolve())
               for name in archive.namelist())
    archive.extractall(root)
del data, uploaded
""".lstrip()
    ]
    cells[3]["source"] = [
        """
from google.colab import drive
drive.mount('/content/drive')
store_root = Path('/content/drive/MyDrive/wildfire-risk-prediction/colab_checkpoints')
command = [str(pilot_python), str(root / 'scripts/cloud/run_l2_day_persistent.py'),
           '--store-root', str(store_root)]
subprocess.run(command, check=True, env=clean_env)
""".lstrip()
    ]
    cells[4] = {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": [
            """
# Yazıları eşitle, bağlantıyı kapat ve Drive'dan yeniden okuyarak kontrol et.
drive.flush_and_unmount(timeout_ms=60000)
drive.mount('/content/drive')
subprocess.run(command + ['--after-remount'], check=True, env=clean_env)
print('Drive yeniden bağlandı; sekiz tamamlanmış kayıt geri yükleme denetiminden geçti.')
""".lstrip()
        ],
    }
    cells[5]["source"] = [
        """
import shutil
result = shutil.make_archive('/content/l2_drive_proof', 'zip', root / 'storage/results')
files.download(result)
""".lstrip()
    ]
    return value


def build():
    report = json.loads(
        (
            ROOT / "outputs/reports/observation_coverage/colab_day_received_verification.json"
        ).read_text()
    )
    if (
        report["status"] != "independent_day_result_verified"
        or report["environment"] != "authenticated_cloud_day"
    ):
        raise ValueError("Verified cloud bootstrap required")
    files = {}
    for name in ("scripts/cloud/checkpoint_store.py", "scripts/cloud/run_l2_day_persistent.py"):
        files[name] = (ROOT / name).read_bytes()
    files["storage/l2_day_bundle.zip"] = (ROOT / "outputs/cloud_day/l2_day_bundle.zip").read_bytes()
    files["storage/received_day_results.zip"] = (
        ROOT / "outputs/cloud_day/received/l2_day_results_2e3dc9f61a8fa41f.zip"
    ).read_bytes()
    if (
        pilot.sha(files["storage/l2_day_bundle.zip"]) != report["bundle_sha256"]
        or pilot.sha(files["storage/received_day_results.zip"]) != report["results_zip_sha256"]
    ):
        raise ValueError("Bootstrap input/bundle differs from independent verification")
    manifest = {
        "protocol": "validated_zip_v1",
        "bootstrap_results_sha256": report["results_zip_sha256"],
        "files": {name: pilot.sha(data) for name, data in files.items()},
        "raw_files_included": False,
        "raw_downloads_requested": False,
    }
    files["storage/manifest.json"] = json.dumps(manifest, indent=2).encode()
    OUTPUT.mkdir(exist_ok=True)
    destination = OUTPUT / "l2_drive_bundle.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    path = OUTPUT / "l2_drive_storage.ipynb"
    path.write_text(
        json.dumps(notebook(pilot.sha(destination.read_bytes())), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "bundle": str(destination),
                "bundle_bytes": destination.stat().st_size,
                "notebook": str(path),
                "new_satellite_download_bytes": 0,
            }
        )
    )


if __name__ == "__main__":
    build()
