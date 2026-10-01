import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Geod, Transformer

ROOT = Path(__file__).resolve().parents[2]
source_path = ROOT / "data/raw/landcover/landcover_copernicus_2017.tif"
output_path = ROOT / "data/interim/landcover_pixel_area_m2.tif"
report_path = ROOT / "outputs/reports/landcover_weights.json"

geod = Geod(ellps="WGS84")

with rasterio.open(source_path) as src:
    # Bu hesap mevcut, dönüklüğü olmayan Web Mercator rasteri içindir.
    if src.crs.to_epsg() != 3857:
        raise ValueError("Bu betik EPSG:3857 kaynak bekliyor.")

    transform = src.transform

    if transform.b != 0 or transform.d != 0:
        raise ValueError("Dönük raster için farklı hesap gerekir.")

    if transform.a <= 0 or transform.e >= 0:
        raise ValueError("Beklenmeyen raster yönü.")

    to_lonlat = Transformer.from_crs(
        src.crs,
        "EPSG:4326",
        always_xy=True,
    )

    # Web Mercator'da aynı satırdaki pikseller eşit alanlıdır.
    row_areas = np.empty(src.height, dtype="float64")
    left = transform.c
    right = left + transform.a

    print("Piksel alanları hesaplanıyor...", flush=True)

    for row in range(src.height):
        top = transform.f + row * transform.e
        bottom = top + transform.e

        lons, lats = to_lonlat.transform(
            [left, right, right, left],
            [top, top, bottom, bottom],
        )

        area, _ = geod.polygon_area_perimeter(lons, lats)
        row_areas[row] = abs(area)

    if not np.isfinite(row_areas).all() or (row_areas <= 0).any():
        raise ValueError("Geçersiz piksel alanı hesaplandı.")

    profile = src.profile.copy()
    profile.update(
        driver="GTiff",
        count=1,
        dtype="float64",
        nodata=None,
        compress="deflate",
        predictor=3,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Kaynakla aynı boyut ve hizaya sahip ağırlık rasteri
    with rasterio.open(output_path, "w", **profile) as dst:
        for _, window in src.block_windows(1):
            start = int(window.row_off)
            stop = start + int(window.height)

            block = np.broadcast_to(
                row_areas[start:stop, None],
                (int(window.height), int(window.width)),
            ).copy()

            dst.write(block, 1, window=window)

report = {
    "source": str(source_path.relative_to(ROOT)),
    "output": str(output_path.relative_to(ROOT)),
    "weight_units": "m2",
    "method": "WGS84 geodesic area of four pixel corners",
    "min_pixel_area_m2": float(row_areas.min()),
    "max_pixel_area_m2": float(row_areas.max()),
    "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
}

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps(report, ensure_ascii=False, indent=2))
print("Alan ağırlıkları kaydedildi:", output_path)
