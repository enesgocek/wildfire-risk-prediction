"""Build an explicit, credential-free Colab pilot bundle; never includes raw arrays."""

import hashlib
import json
import zipfile
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/cloud_pilot"
REPORTS = ROOT / "outputs/reports/observation_coverage"
REQUIREMENTS = Path(__file__).with_name("requirements_l2_pilot.txt")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    report = json.loads((REPORTS / "l2_sample_2019013.0100_audit.json").read_text())
    files = {}
    for name in (
        "scripts/firms/inspect_l2_observation_sample.py",
        "scripts/cloud/run_l2_pilot.py",
        "data/aoi/aoi.geojson",
        "data/aoi/grid_5km.geojson",
    ):
        files[name] = (ROOT / name).read_bytes()
    assert sha(files["scripts/firms/inspect_l2_observation_sample.py"]) == report["script_sha256"]
    assert sha(files["data/aoi/aoi.geojson"]) == report["aoi_sha256"]
    assert sha(files["data/aoi/grid_5km.geojson"]) == report["grid_sha256"]
    files["pilot/reference/audit.json"] = (
        REPORTS / "l2_sample_2019013.0100_audit.json"
    ).read_bytes()
    files["pilot/reference/grid_centers.csv"] = (
        REPORTS / "l2_sample_2019013.0100_grid_centers.csv"
    ).read_bytes()
    sources, metadata = [], {}
    for role, source in report["sources"].items():
        candidates = [
            path
            for path in REPORTS.glob("*_metadata.json")
            if sha(path.read_bytes()) == source["cmr_metadata_sha256"]
        ]
        assert len(candidates) == 1, "Expected exact CMR metadata source"
        cmr_path = candidates[0]
        cmr = json.loads(cmr_path.read_text(encoding="utf-8"))
        name = source["path"].replace("\\", "/").rsplit("/", 1)[-1]
        urls = {
            item["URL"]
            for item in cmr["RelatedUrls"]
            if item["URL"].startswith("https://") and item["URL"].endswith("/" + name)
        }
        assert len(urls) == 1, "Expected one source data URL"
        relative = "pilot/metadata/" + cmr_path.name
        files[relative] = cmr_path.read_bytes()
        metadata[role] = relative
        sources.append(
            {
                "role": role,
                "filename": name,
                "url": urls.pop(),
                "provider": "LPCLOUD" if role == "fire" else "LAADS",
                "bytes": source["bytes"],
                "sha256": source["sha256"],
            }
        )
    keys = [
        "pair_key",
        "status",
        "sensor",
        "sample_id",
        "day_night_flag",
        "start_utc",
        "end_utc",
        "shape",
        "whole_swath_class_counts",
        "spatial_counts",
        "sparse_fire_count",
        "native_orientation_verified_against_all_sparse_fires",
        "pilot_grid_count",
        "grids_with_pixel_centers",
        "pilot_class_counts",
        "pilot_qa_counts",
        "pilot_class_qa_counts",
        "pilot_land_nominal_input_no_residual",
        "negative_label_permitted",
    ]
    manifest = {
        "sample_id": report["sample_id"],
        "stem": "l2_sample_2019013.0100",
        "bundle_files": {name: sha(data) for name, data in files.items()},
        "sources": sources,
        "metadata": metadata,
        "comparison_keys": keys,
    }
    files["pilot/manifest.json"] = json.dumps(manifest, indent=2).encode()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / "l2_pilot_isolated_bundle.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    bundle_sha = sha(destination.read_bytes())

    notebook = make_notebook(bundle_sha)
    path = OUTPUT / "l2_pilot_isolated.ipynb"
    path.write_text(json.dumps(notebook, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "bundle": str(destination),
                "bundle_bytes": destination.stat().st_size,
                "bundle_sha256": bundle_sha,
                "notebook": str(path),
                "cloud_payload_bytes": sum(source["bytes"] for source in sources),
            }
        )
    )


def make_notebook(bundle_sha):
    requirements_text = REQUIREMENTS.read_text(encoding="utf-8")

    def cell(kind, source):
        value = {
            "cell_type": kind,
            "metadata": {},
            "source": dedent(source).lstrip().splitlines(keepends=True),
        }
        if kind == "code":
            value.update(execution_count=None, outputs=[])
        return value

    cells = [
        cell(
            "markdown",
            """
            # Tek geçiş Colab denemesi

            Ücretsiz **CPU** ortamı kullan. Tam yılları indirmez. Yaklaşık 195 MB ham veri
            Colab bilgisayarına gelir; kendi bilgisayarına yalnızca küçük kontrol sonucu iner.
            Günlük etiket veya model üretmez.

            Hücreleri sırayla çalıştır. Google hesabınla Colab'a giriş yap; NASA bilgilerini
            yalnızca gizli giriş istemine yaz. Python 3.12 çalışma ortamı önerilir.
            Bu sürüm ayrı bir Python ortamı kurar; Colab'ın sistem paketleri değiştirilmez.
            Eski notebook'un kurulumu çalıştıysa önce Colab çalışma zamanını silip yenisini aç.
            """,
        ),
        cell(
            "code",
            f"""
            import os, sys, subprocess, venv
            from pathlib import Path
            assert sys.version_info[:2] == (3, 12), 'Colab Python 3.12 ortamını seç.'
            isolated = Path('/content/wildfire_l2_venv_v2')
            venv.EnvBuilder(with_pip=False, system_site_packages=False).create(isolated)
            pilot_python = isolated / 'bin/python'
            clean_env = os.environ.copy()
            for key in ('PYTHONPATH', 'PYTHONHOME'):
                clean_env.pop(key, None)
            clean_env['PYTHONNOUSERSITE'] = '1'
            requirements_file = Path('/content/wildfire_l2_requirements_v2.txt')
            requirements_file.write_text({requirements_text!r}, encoding='utf-8')
            subprocess.run([sys.executable, '-m', 'pip', '--isolated', '--python',
                            str(pilot_python), 'install', '--quiet', '--no-cache-dir',
                            '--only-binary=:all:', '-r', str(requirements_file)],
                           check=True, env=clean_env)
            subprocess.run([str(pilot_python), '-m', 'pip', 'check'], check=True, env=clean_env)
            preflight = (
                "import rasterio\\n"
                "with rasterio.Env() as env:\\n"
                "    assert 'HDF5' in env.drivers(), 'GDAL HDF5 driver missing'\\n")
            subprocess.run([str(pilot_python), '-c', preflight], check=True, env=clean_env)
            print('Ayrı Python ortamı hazır; paket uyumluluk kontrolü geçti.')
            """,
        ),
        cell(
            "code",
            f"""
            from google.colab import files
            from pathlib import Path
            import hashlib, zipfile, io
            uploaded = files.upload()  # Yalnızca l2_pilot_isolated_bundle.zip dosyasını seç.
            assert set(uploaded) == {{'l2_pilot_isolated_bundle.zip'}}, 'Tek paket seçilmeli'
            data = uploaded.pop('l2_pilot_isolated_bundle.zip')
            assert hashlib.sha256(data).hexdigest() == '{bundle_sha}', 'Paket sürümü farklı'
            root = Path('/content/wildfire_l2_pilot')
            root.mkdir(exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                assert all((root / name).resolve().is_relative_to(root.resolve())
                           for name in archive.namelist())
                archive.extractall(root)
            del data, uploaded
            print('Paket doğrulandı; tek geçiş hazır.')
            """,
        ),
        cell(
            "code",
            """
            import getpass, subprocess
            auth_env = clean_env.copy()
            for key in ('EARTHDATA_USERNAME', 'EARTHDATA_PASSWORD', 'EARTHDATA_TOKEN'):
                auth_env.pop(key, None)
            try:
                auth_env['EARTHDATA_USERNAME'] = getpass.getpass('Earthdata kullanıcı adın: ')
                auth_env['EARTHDATA_PASSWORD'] = getpass.getpass('Earthdata parolan: ')
                subprocess.run([str(pilot_python), str(root / 'scripts/cloud/run_l2_pilot.py'),
                                '--login-strategy', 'environment'], check=True, env=auth_env)
            finally:
                auth_env.clear()
                del auth_env
            """,
        ),
        cell(
            "markdown",
            """
            Sonuç **passed_exact_local_reference_comparison** ise yerel denetimle aynı
            piksel/QA sayımları üretildi. Bu, nihai gözlem alanı veya etiket yönteminin
            doğrulandığı anlamına gelmez. Hata çıkarsa dur; başka yıl/sürüm deneme.
            """,
        ),
        cell(
            "code",
            """
            import shutil
            result = shutil.make_archive('/content/l2_pilot_results', 'zip', root / 'pilot/results')
            files.download(result)
            """,
        ),
    ]
    return {
        "cells": cells,
        "metadata": {
            "colab": {"name": "l2_pilot_isolated.ipynb"},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }


if __name__ == "__main__":
    build()
