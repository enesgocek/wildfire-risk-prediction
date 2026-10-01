import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

parser = argparse.ArgumentParser(description="FIRMS arşiv kontrolü")
parser.add_argument(
    "--source",
    default="data/raw/firms/815579/fire_archive_SV-C2_815579.csv",
)
parser.add_argument(
    "--report",
    default="outputs/reports/firms_archive_check.json",
)
parser.add_argument("--start", default="2018-01-01")
parser.add_argument("--end", default="2025-01-01")
args = parser.parse_args()

source_path = ROOT / args.source
report_path = ROOT / args.report

# Tarih, saat ve kaynak kodlarını metin olarak koru
df = pd.read_csv(source_path, dtype="string")

required = {
    "latitude",
    "longitude",
    "acq_date",
    "acq_time",
    "satellite",
    "instrument",
    "confidence",
    "version",
    "daynight",
    "type",
}

missing_columns = sorted(required - set(df.columns))

if missing_columns:
    raise ValueError(f"Eksik sütunlar: {missing_columns}")

if df.empty:
    raise ValueError("CSV içinde kayıt yok.")

latitude = pd.to_numeric(df["latitude"], errors="coerce")
longitude = pd.to_numeric(df["longitude"], errors="coerce")

valid_coordinates = latitude.between(-90, 90) & longitude.between(-180, 180)

dates = pd.to_datetime(
    df["acq_date"],
    format="%Y-%m-%d",
    errors="coerce",
    utc=True,
)

time_text = df["acq_time"].str.strip().str.zfill(4)
hours = pd.to_numeric(time_text.str[:2], errors="coerce")
minutes = pd.to_numeric(time_text.str[2:], errors="coerce")

valid_time = (
    time_text.str.fullmatch(r"\d{4}", na=False) & hours.between(0, 23) & minutes.between(0, 59)
)

timestamps = pd.to_datetime(
    df["acq_date"] + " " + time_text,
    format="%Y-%m-%d %H%M",
    errors="coerce",
    utc=True,
).where(valid_time)

outside_period = dates.notna() & (
    (dates < pd.Timestamp(args.start, tz="UTC")) | (dates >= pd.Timestamp(args.end, tz="UTC"))
)


def category_counts(column):
    values = df[column].fillna("<missing>").value_counts()
    return {str(key): int(value) for key, value in values.items()}


year_counts = dates.dt.year.value_counts().sort_index()

report = {
    "file": str(source_path.relative_to(ROOT)),
    "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
    "row_count": len(df),
    "columns": list(df.columns),
    "missing_values": {column: int(df[column].isna().sum()) for column in df.columns},
    "invalid_coordinate_count": int((~valid_coordinates).sum()),
    "invalid_date_count": int(dates.isna().sum()),
    "invalid_timestamp_count": int(timestamps.isna().sum()),
    "outside_requested_period_count": int(outside_period.sum()),
    "first_detection_utc": (timestamps.min().isoformat() if timestamps.notna().any() else None),
    "last_detection_utc": (timestamps.max().isoformat() if timestamps.notna().any() else None),
    "rows_by_year": {str(year): int(year_counts.get(year, 0)) for year in range(2018, 2025)},
    "satellite_counts": category_counts("satellite"),
    "instrument_counts": category_counts("instrument"),
    "version_counts": category_counts("version"),
    "confidence_counts": category_counts("confidence"),
    "type_counts": category_counts("type"),
    "daynight_counts": category_counts("daynight"),
    "exact_duplicate_row_count": int(df.duplicated().sum()),
    "latitude_min": float(latitude.min()),
    "latitude_max": float(latitude.max()),
    "longitude_min": float(longitude.min()),
    "longitude_max": float(longitude.max()),
}

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps(report, ensure_ascii=False, indent=2))
print("Rapor kaydedildi:", report_path)
