import hashlib
import json
from pathlib import Path

import geopandas as gpd
import shapely

ROOT = Path(__file__).resolve().parents[1]

aoi_path = ROOT / "data/aoi/aoi.geojson"
candidate_path = ROOT / "data/interim/grid_5km_candidates.geojson"
output_path = ROOT / "data/aoi/grid_5km.geojson"
report_path = ROOT / "outputs/reports/grid_preparation.json"

# Her iki veriyi aynı metre tabanlı sisteme dönüştür
aoi = gpd.read_file(aoi_path).to_crs(epsg=6933)
candidates = gpd.read_file(candidate_path).to_crs(epsg=6933)

if aoi.empty or candidates.empty:
    raise ValueError("Girdi dosyalarından biri boş.")

if not aoi.geometry.is_valid.all():
    raise ValueError("AOI içinde geçersiz geometri var.")

if not candidates.geometry.is_valid.all():
    raise ValueError("Aday gridlerde geçersiz geometri var.")

if candidates["grid_id"].isna().any():
    raise ValueError("Eksik grid_id bulundu.")

if not candidates["grid_id"].is_unique:
    raise ValueError("Tekrarlı grid_id bulundu.")

aoi_geometry = shapely.union_all(aoi.geometry.array)

# Önce hızlı bir kesişme kontrolü yap
print("AOI ile kesişebilecek hücreler seçiliyor...", flush=True)

shapely.prepare(aoi_geometry)
intersects = shapely.intersects(
    aoi_geometry,
    candidates.geometry.array,
)
grid = candidates.loc[intersects].copy()

# Ayrıntılı alan hesabını yalnızca seçilen hücrelerde yap
print("AOI içinde kalan alanlar hesaplanıyor...", flush=True)

inside_geometries = grid.geometry.intersection(aoi_geometry)

grid["cell_area_km2"] = grid.geometry.area / 1_000_000
grid["aoi_area_km2"] = inside_geometries.area / 1_000_000

# Yalnızca sınır çizgisine dokunan hücreleri çıkar
grid = grid.loc[grid["aoi_area_km2"] > 0].copy()

if grid.empty:
    raise ValueError("AOI ile pozitif alan kesişimi bulunan hücre yok.")

grid["aoi_fraction"] = grid["aoi_area_km2"] / grid["cell_area_km2"]

if (grid["aoi_fraction"] > 1 + 1e-8).any():
    raise ValueError("AOI içindeki alan tam hücre alanından büyük.")

# Çok küçük sayısal taşmaları düzelt
grid["aoi_fraction"] = grid["aoi_fraction"].clip(0, 1)

# Hücrelerin AOI'yi alan bakımından kapsadığını doğrula
aoi_area_km2 = aoi_geometry.area / 1_000_000
covered_area_km2 = grid["aoi_area_km2"].sum()
area_difference = abs(covered_area_km2 - aoi_area_km2)

if area_difference > max(0.001, aoi_area_km2 * 1e-6):
    raise ValueError(f"AOI kapsama kontrolü başarısız. Alan farkı: {area_difference:.6f} km²")

# Tam hücre geometrileri korunur; GeoJSON enlem-boylamla kaydedilir
grid = grid.sort_values("grid_id").reset_index(drop=True)

output_path.parent.mkdir(parents=True, exist_ok=True)
grid.to_crs(epsg=4326).to_file(
    output_path,
    driver="GeoJSON",
    index=False,
)

report = {
    "candidate_count": len(candidates),
    "retained_count": len(grid),
    "removed_count": len(candidates) - len(grid),
    "unique_grid_ids": int(grid["grid_id"].nunique()),
    "aoi_area_km2": float(aoi_area_km2),
    "covered_aoi_area_km2": float(covered_area_km2),
    "area_difference_km2": float(area_difference),
    "min_aoi_fraction": float(grid["aoi_fraction"].min()),
    "max_aoi_fraction": float(grid["aoi_fraction"].max()),
    "calculation_crs": "EPSG:6933",
    "output_geometry_crs": "EPSG:4326",
    "grid_version": "E6933_5K_V1",
    "aoi_sha256": hashlib.sha256(aoi_path.read_bytes()).hexdigest(),
    "candidates_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
}

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(json.dumps(report, ensure_ascii=False, indent=2))
print(f"\nGrid kaydedildi: {output_path}")
