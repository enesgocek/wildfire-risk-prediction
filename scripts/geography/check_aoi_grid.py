from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]

aoi_path = ROOT / "data/aoi/aoi.geojson"
grid_path = ROOT / "data/interim/grid_5km_candidates.geojson"

for path in (aoi_path, grid_path):
    if not path.is_file():
        raise FileNotFoundError(f"Dosya bulunamadı: {path}")

aoi = gpd.read_file(aoi_path)
grid = gpd.read_file(grid_path)

if aoi.empty or grid.empty:
    raise ValueError("AOI veya grid dosyası boş.")

if aoi.crs is None or grid.crs is None:
    raise ValueError("Dosyalardan birinin koordinat sistemi tanımlı değil.")

if "grid_id" not in grid.columns:
    raise ValueError("Grid dosyasında grid_id alanı bulunamadı.")

print("AOI kayıt sayısı:", len(aoi))
print("Aday hücre sayısı:", len(grid))
print("AOI dosyasının koordinat sistemi:", aoi.crs)
print("Grid dosyasının koordinat sistemi:", grid.crs)

print("Eksik grid_id sayısı:", grid["grid_id"].isna().sum())
print("Benzersiz grid_id sayısı:", grid["grid_id"].nunique())

print("Geçersiz AOI geometrisi sayısı:", (~aoi.geometry.is_valid).sum())
print("Geçersiz grid geometrisi sayısı:", (~grid.geometry.is_valid).sum())

# Alan hesabından önce metre tabanlı sisteme dönüştür
grid_metres = grid.to_crs(epsg=6933)
areas_km2 = grid_metres.geometry.area / 1_000_000

print("En küçük tam hücre alanı (km²):", areas_km2.min())
print("En büyük tam hücre alanı (km²):", areas_km2.max())
