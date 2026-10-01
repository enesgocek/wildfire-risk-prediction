import json
from collections import Counter
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
raster_path = ROOT / "data/raw/landcover/landcover_copernicus_2017.tif"
report_path = ROOT / "outputs/reports/landcover_check.json"

if not raster_path.is_file():
    raise FileNotFoundError(f"Dosya bulunamadı: {raster_path}")

expected_codes = {
    0,
    20,
    30,
    40,
    50,
    60,
    70,
    80,
    90,
    100,
    111,
    112,
    113,
    114,
    115,
    116,
    121,
    122,
    123,
    124,
    125,
    126,
    200,
}

counts = Counter()
missing_count = 0

with rasterio.open(raster_path) as src:
    if src.count != 1:
        raise ValueError(f"Tek bant bekleniyordu; bulunan: {src.count}")

    if src.crs is None:
        raise ValueError("Koordinat sistemi tanımlı değil.")

    print("Raster bloklar halinde kontrol ediliyor...", flush=True)

    for _, window in src.block_windows(1):
        block = src.read(1, window=window, masked=True)

        missing_count += int(np.ma.getmaskarray(block).sum())

        values, frequencies = np.unique(
            block.compressed(),
            return_counts=True,
        )

        for value, frequency in zip(values, frequencies, strict=True):
            counts[int(value)] += int(frequency)

    unexpected_codes = sorted(set(counts) - expected_codes)

    report = {
        "file": str(raster_path.relative_to(ROOT)),
        "file_size_mb": round(raster_path.stat().st_size / 1_000_000, 2),
        "crs": src.crs.to_string(),
        "crs_units": "degrees" if src.crs.is_geographic else "projected",
        "pixel_size_crs_units": list(src.res),
        "width": src.width,
        "height": src.height,
        "band_count": src.count,
        "dtype": src.dtypes[0],
        "nodata": src.nodata,
        "bounds": list(src.bounds),
        "valid_pixel_count": sum(counts.values()),
        "missing_pixel_count": missing_count,
        "unknown_class_pixel_count": counts.get(0, 0),
        "class_pixel_counts": dict(sorted(counts.items())),
        "unexpected_class_codes": unexpected_codes,
    }

if report["valid_pixel_count"] == 0:
    raise ValueError("Dosyada geçerli piksel bulunamadı.")

if unexpected_codes:
    raise ValueError(f"Beklenmeyen sınıf kodları: {unexpected_codes}")

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps(report, ensure_ascii=False, indent=2))
print(f"\nRapor kaydedildi: {report_path}")
