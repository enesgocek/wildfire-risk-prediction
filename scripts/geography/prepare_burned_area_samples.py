import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS

ROOT = Path(__file__).resolve().parents[2]

source_dir = ROOT / "data/raw/burned_area/samples"
output_dir = ROOT / "data/interim/burned_area/samples"

# Earth Engine kaynak koordinatlarıyla doğrulanan MODIS küresel tanımı.
correct_crs = CRS.from_string("+proj=sinu +R=6371007.181 +units=m +no_defs")

bands = ("BurnDate", "Uncertainty", "QA", "FirstDay", "LastDay")
months = ("2019_08", "2021_07", "2021_08")
reports = []

output_dir.mkdir(parents=True, exist_ok=True)

for month in months:
    filename = f"burned_area_sample_{month}.tif"
    source_path = source_dir / filename
    output_path = output_dir / filename

    with rasterio.open(source_path) as src:
        if src.count != 5 or src.descriptions != bands:
            raise ValueError(f"{filename}: beklenmeyen bant yapısı.")

        if src.crs is None or src.crs.to_dict().get("proj") != "sinu":
            raise ValueError(f"{filename}: beklenmeyen kaynak projeksiyonu.")

        if not np.allclose(
            [src.transform.a, -src.transform.e],
            [463.3127165279165, 463.3127165279167],
            rtol=0,
            atol=0.000001,
        ):
            raise ValueError(f"{filename}: beklenmeyen piksel boyutu.")

        if src.transform.b != 0 or src.transform.d != 0:
            raise ValueError(f"{filename}: döndürülmüş grid.")

        data = src.read()
        transform = src.transform
        source_crs = src.crs.to_wkt()
        profile = src.profile.copy()
        tags = src.tags()

    # Yalnızca CRS etiketi düzeltilir; grid ve piksel değerleri değişmez.
    profile.update(crs=correct_crs, compress="deflate")

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(data)
        dst.descriptions = bands
        dst.update_tags(**tags)
        dst.update_tags(
            preparation="MODIS spherical CRS metadata correction",
            source_file=filename,
        )

    with rasterio.open(output_path) as check:
        if (
            check.crs != correct_crs
            or check.transform != transform
            or not np.array_equal(check.read(), data)
        ):
            raise ValueError(f"{filename}: çalışma kopyası doğrulanamadı.")

    reports.append(
        {
            "source": str(source_path.relative_to(ROOT)),
            "output": str(output_path.relative_to(ROOT)),
            "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
            "source_crs_wkt": source_crs,
            "corrected_crs_wkt": correct_crs.to_wkt(),
            "pixel_values_unchanged": True,
            "pixel_grid_unchanged": True,
            "resampling_applied": False,
        }
    )

    print("Hazırlandı ve doğrulandı:", filename)

report_path = ROOT / "outputs/reports/burned_area_samples_preparation.json"
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    json.dumps(reports, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print("Çalışma kopyaları:", output_dir)
print("Rapor:", report_path)
