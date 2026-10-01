import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from exactextract import exact_extract
from exactextract.operation import Operation
from exactextract.raster import RasterioRasterSource

ROOT = Path(__file__).resolve().parents[1]

source_path = ROOT / "data/raw/landcover/landcover_copernicus_2017.tif"
weights_path = ROOT / "data/interim/landcover_pixel_area_m2.tif"
parts_path = ROOT / "data/interim/grid_aoi_parts.geojson"
output_path = ROOT / "data/interim/grid_landcover_2017.csv"
report_path = ROOT / "outputs/reports/landcover_fractions.json"

class_codes = [
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
]
forest_codes = [
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
]

# Ağırlıkların mevcut kaynak rasterden üretildiğini doğrula
weights_report = json.loads(
    (ROOT / "outputs/reports/landcover_weights.json").read_text(encoding="utf-8")
)
source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()

if source_hash != weights_report["source_sha256"]:
    raise ValueError("Kaynak değişmiş; alan ağırlıkları yeniden üretilmeli.")

parts = gpd.read_file(parts_path).to_crs(6933)

if parts.empty or not parts["grid_id"].is_unique:
    raise ValueError("Hücre listesi boş veya kimlikler tekrarlı.")

if parts.geometry.is_empty.any() or not parts.geometry.is_valid.all():
    raise ValueError("Boş veya geçersiz hesaplama geometrisi var.")

# Uzun kenarları bölerek koordinat dönüşümündeki yaklaşımı iyileştir
parts.geometry = parts.geometry.segmentize(50)

with rasterio.open(source_path) as src, rasterio.open(weights_path) as weights:
    if src.crs != weights.crs or src.transform != weights.transform or src.shape != weights.shape:
        raise ValueError("Kaynak raster ile alan ağırlıkları hizalı değil.")

    calculation_parts = parts.to_crs(src.crs)

    values_source = RasterioRasterSource(src, name="landcover")
    area_source = RasterioRasterSource(weights, name="pixel_area")

    operations = [
        Operation("unique", "class_codes", values_source),
        Operation(
            "weighted_frac",
            "class_fractions",
            values_source,
            weights=area_source,
        ),
        Operation("sum", "covered_area_m2", area_source),
    ]

    print("Hücrelerin örtü oranları hesaplanıyor...", flush=True)

    stats = exact_extract(
        values_source,
        calculation_parts,
        operations,
        include_cols=["grid_id"],
        output="pandas",
        strategy="feature-sequential",
        max_cells_in_memory=2_000_000,
    )

rows = []

for _, item in stats.iterrows():
    codes = np.asarray(item["class_codes"])
    fractions = np.asarray(item["class_fractions"], dtype=float)

    if len(codes) == 0 or len(codes) != len(fractions) or not np.isfinite(fractions).all():
        raise ValueError(f"Geçersiz sonuç: {item['grid_id']}")

    if not np.isclose(fractions.sum(), 1.0, atol=1e-6):
        raise ValueError(f"Oranların toplamı 1 değil: {item['grid_id']}")

    if (fractions < 0).any() or (fractions > 1 + 1e-6).any():
        raise ValueError(f"Oran sınırı ihlali: {item['grid_id']}")

    mapping = {int(code): float(fraction) for code, fraction in zip(codes, fractions, strict=True)}

    if set(mapping) - set(class_codes):
        raise ValueError(f"Beklenmeyen sınıf: {mapping}")

    row = {
        "grid_id": item["grid_id"],
        "reference_year": 2017,
        "covered_area_km2": float(item["covered_area_m2"]) / 1_000_000,
    }

    # Bütün sınıfları sakla; henüz hiçbir sınıfı veya hücreyi eleme
    for code in class_codes:
        row[f"lc_{code}_fraction"] = mapping.get(code, 0.0)

    row["forest_fraction"] = sum(mapping.get(c, 0.0) for c in forest_codes)
    row["shrub_fraction"] = mapping.get(20, 0.0)
    row["herbaceous_fraction"] = mapping.get(30, 0.0)
    row["agriculture_fraction"] = mapping.get(40, 0.0)
    row["urban_fraction"] = mapping.get(50, 0.0)
    row["water_fraction"] = mapping.get(80, 0.0) + mapping.get(200, 0.0)
    row["unknown_fraction"] = mapping.get(0, 0.0)

    row["natural_vegetation_fraction"] = (
        row["forest_fraction"] + row["shrub_fraction"] + row["herbaceous_fraction"]
    )

    rows.append(row)

result = pd.DataFrame(rows).sort_values("grid_id")

if len(result) != len(parts) or set(result["grid_id"]) != set(parts["grid_id"]):
    raise ValueError("Sonuçta eksik veya fazla hücre var.")

if (result["covered_area_km2"] <= 0).any():
    raise ValueError("Raster kapsamı olmayan hücre var.")

covered_area = result["covered_area_km2"].sum()
expected_area = parts["aoi_area_km2"].sum()
relative_difference = abs(covered_area - expected_area) / expected_area

if relative_difference > 0.0001:
    raise ValueError(f"Raster/AOI alanları uyuşmuyor: {covered_area:.6f} / {expected_area:.6f} km²")

output_path.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(output_path, index=False, encoding="utf-8-sig")

report = {
    "grid_count": len(result),
    "reference_year": 2017,
    "unknown_class_grid_count": int((result["unknown_fraction"] > 0).sum()),
    "natural_vegetation_fraction_min": float(result["natural_vegetation_fraction"].min()),
    "natural_vegetation_fraction_median": float(result["natural_vegetation_fraction"].median()),
    "natural_vegetation_fraction_max": float(result["natural_vegetation_fraction"].max()),
    "covered_area_km2": float(result["covered_area_km2"].sum()),
    "aoi_area_km2": float(parts["aoi_area_km2"].sum()),
    "source_sha256": source_hash,
    "method": "Fractional pixel overlap weighted by approximate WGS84 pixel area",
}

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps(report, ensure_ascii=False, indent=2))
print("Örtü tablosu kaydedildi:", output_path)
