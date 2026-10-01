from pathlib import Path

import geopandas as gpd
import shapely

ROOT = Path(__file__).resolve().parents[1]
output_path = ROOT / "data/interim/grid_aoi_parts.geojson"

aoi = gpd.read_file(ROOT / "data/aoi/aoi.geojson").to_crs(6933)
grid = gpd.read_file(ROOT / "data/aoi/grid_5km.geojson").to_crs(6933)

aoi_geometry = shapely.union_all(aoi.geometry.array)

# Her hücrenin yalnızca çalışma alanında kalan bölümünü al
parts = grid.copy()
parts.geometry = grid.geometry.intersection(aoi_geometry)

if parts.geometry.is_empty.any():
    raise ValueError("Çalışma alanında boş kalan hücre bulundu.")

if not parts.geometry.is_valid.all():
    raise ValueError("Geçersiz kesişim geometrisi bulundu.")

areas_km2 = parts.geometry.area / 1_000_000

if (areas_km2 <= 0).any():
    raise ValueError("Pozitif alanı olmayan hücre bulundu.")

# Önceden kaydettiğimiz alanlarla karşılaştır
differences = (areas_km2 - parts["aoi_area_km2"]).abs()

if differences.max() > 0.00001:
    raise ValueError("Kesişim alanları önceki grid hesabıyla uyuşmuyor.")

if not parts["grid_id"].is_unique:
    raise ValueError("Tekrarlı grid kimliği bulundu.")

output_path.parent.mkdir(parents=True, exist_ok=True)
parts.to_crs(4326).to_file(
    output_path,
    driver="GeoJSON",
    index=False,
)

print("Hesaplamaya hazırlanmış hücre sayısı:", len(parts))
print("Toplam çalışma alanı (km²):", areas_km2.sum())
print("En büyük alan farkı (km²):", differences.max())
print("Dosya kaydedildi:", output_path)
