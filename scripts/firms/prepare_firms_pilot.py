import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]

parser = argparse.ArgumentParser(description="FIRMS pilot alan hazırlığı")
parser.add_argument(
    "--source",
    default="data/raw/firms/815579/fire_archive_SV-C2_815579.csv",
)
parser.add_argument(
    "--output",
    default="data/interim/firms_pilot_2018_2024.csv",
)
parser.add_argument(
    "--report",
    default="outputs/reports/firms_pilot_preparation.json",
)
parser.add_argument("--start", default="2018-01-01")
parser.add_argument("--end", default="2025-01-01")
args = parser.parse_args()

source_path = ROOT / args.source
aoi_path = ROOT / "data/aoi/aoi.geojson"
grid_path = ROOT / "data/aoi/grid_5km.geojson"
output_path = ROOT / args.output
report_path = ROOT / args.report

df = pd.read_csv(source_path, dtype="string")

# Ham dosyadaki 1'den başlayan veri kaydı numarası
df["source_record_number"] = np.arange(1, len(df) + 1)

longitude = pd.to_numeric(df["longitude"], errors="raise")
latitude = pd.to_numeric(df["latitude"], errors="raise")

aoi = gpd.read_file(aoi_path).to_crs(4326)
aoi_geometry = shapely.union_all(aoi.geometry.array)

if aoi_geometry.is_empty or not aoi_geometry.is_valid:
    raise ValueError("AOI boş veya geçersiz.")

# İl sınırındaki noktaları da dahil et
shapely.prepare(aoi_geometry)
points = shapely.points(longitude.to_numpy(), latitude.to_numpy())
inside = shapely.covers(aoi_geometry, points)

pilot = df.loc[inside].copy()

if pilot.empty:
    raise ValueError("Pilot çalışma alanında tespit bulunamadı.")

# Sabit grid başlangıcına göre hücre kimliğini belirle
transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:6933",
    always_xy=True,
)

x, y = transformer.transform(
    longitude.loc[inside].to_numpy(),
    latitude.loc[inside].to_numpy(),
)

columns = np.floor(np.asarray(x) / 5000).astype("int64")
rows = np.floor(np.asarray(y) / 5000).astype("int64")

pilot["grid_id"] = [
    f"E6933_5K_V1_C{column}_R{row}" for column, row in zip(columns, rows, strict=True)
]

grid = gpd.read_file(grid_path)
unmatched = ~pilot["grid_id"].isin(grid["grid_id"])

if unmatched.any():
    raise ValueError(
        f"{int(unmatched.sum())} tespit mevcut gride eşleşmedi. Sınır/koordinat kontrolü gerekiyor."
    )

# UTC zamanını açık biçimde ekle; ham tarih/saat sütunlarını koru
time_text = pilot["acq_time"].str.zfill(4)

timestamps = pd.to_datetime(
    pilot["acq_date"] + " " + time_text,
    format="%Y-%m-%d %H%M",
    utc=True,
    errors="raise",
)

if (
    (timestamps < pd.Timestamp(args.start, tz="UTC"))
    | (timestamps >= pd.Timestamp(args.end, tz="UTC"))
).any():
    raise ValueError("İstenen dönem dışında tespit var.")

pilot["detection_timestamp_utc"] = timestamps.astype("string")


def counts(series):
    return {str(key): int(value) for key, value in series.value_counts().sort_index().items()}


report = {
    "source_row_count": len(df),
    "pilot_detection_count": len(pilot),
    "outside_pilot_count": len(df) - len(pilot),
    "grids_with_detections": int(pilot["grid_id"].nunique()),
    "detections_by_year": counts(timestamps.dt.year),
    "type_counts": counts(pilot["type"]),
    "confidence_counts": counts(pilot["confidence"]),
    "train_period_detection_count": int((timestamps.dt.year <= 2023).sum()),
    "validation_period_detection_count": int((timestamps.dt.year == 2024).sum()),
    "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
    "aoi_sha256": hashlib.sha256(aoi_path.read_bytes()).hexdigest(),
    "grid_sha256": hashlib.sha256(grid_path.read_bytes()).hexdigest(),
    "filters": "AOI only; no type or confidence filtering",
}

output_path.parent.mkdir(parents=True, exist_ok=True)
pilot.to_csv(output_path, index=False, encoding="utf-8-sig")

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps(report, ensure_ascii=False, indent=2))
print("Pilot tespitler kaydedildi:", output_path)
