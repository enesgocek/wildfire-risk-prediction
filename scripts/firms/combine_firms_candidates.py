import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

sources = [
    (
        "SNPP",
        "815579",
        "data/interim/firms_fire_candidates_2018_2024.csv",
        "2018-01-01",
    ),
    (
        "N20",
        "815590",
        "data/interim/firms_noaa20_fire_candidates_2018_2024.csv",
        "2018-04-01",
    ),
]

frames = []
source_reports = []

required = {
    "source_record_number",
    "satellite",
    "grid_id",
    "detection_timestamp_utc",
    "type",
    "confidence",
    "latitude",
    "longitude",
}

for sensor, request_id, relative_path, start_date in sources:
    path = ROOT / relative_path
    df = pd.read_csv(path, dtype="string")

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{sensor}: eksik sütunlar: {sorted(missing)}")

    if df.empty or df[list(required)].isna().any().any():
        raise ValueError(f"{sensor}: boş tablo veya eksik temel alan var.")

    if not df["satellite"].eq(sensor).all():
        raise ValueError(f"{sensor}: beklenmeyen uydu kimliği var.")

    if not (df["type"].eq("0") & df["confidence"].isin(["n", "h"])).all():
        raise ValueError(f"{sensor}: aday seçim kuralına uymayan kayıt var.")

    record_numbers = pd.to_numeric(df["source_record_number"], errors="raise")
    if (
        (record_numbers < 1).any()
        or (record_numbers % 1 != 0).any()
        or record_numbers.duplicated().any()
    ):
        raise ValueError(f"{sensor}: kaynak kayıt numaraları geçersiz.")

    timestamps = pd.to_datetime(df["detection_timestamp_utc"], utc=True, errors="raise")
    if (
        (timestamps < pd.Timestamp(start_date, tz="UTC"))
        | (timestamps >= pd.Timestamp("2025-01-01", tz="UTC"))
    ).any():
        raise ValueError(f"{sensor}: kaynak dönemi dışında kayıt var.")

    df["source_sensor"] = sensor
    df["source_request_id"] = request_id
    df["detection_id"] = (
        sensor + "_" + request_id + "_" + record_numbers.astype("int64").astype("string")
    )

    source_reports.append(
        {
            "sensor": sensor,
            "request_id": request_id,
            "file": relative_path,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "candidate_count": len(df),
        }
    )
    frames.append(df)

combined = pd.concat(frames, ignore_index=True)

if combined["detection_id"].duplicated().any():
    raise ValueError("Tekrarlanan detection_id bulundu.")

timestamps = pd.to_datetime(combined["detection_timestamp_utc"], utc=True, errors="raise")
combined["detection_timestamp_utc"] = timestamps.astype("string")
combined = combined.sort_values(["detection_timestamp_utc", "detection_id"]).reset_index(drop=True)

years = timestamps.dt.year

report = {
    "sources": source_reports,
    "combined_candidate_count": len(combined),
    "unique_detection_ids": int(combined["detection_id"].nunique()),
    "train_candidate_count": int(years.between(2018, 2023).sum()),
    "validation_candidate_count": int(years.eq(2024).sum()),
    "grids_with_candidates": int(combined["grid_id"].nunique()),
    "deduplication_applied": False,
    "event_grouping_applied": False,
    "status": "exploratory detections; not events or training labels",
}

output_path = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
report_path = ROOT / "outputs/reports/firms_combined_candidates.json"

output_path.parent.mkdir(parents=True, exist_ok=True)
report_path.parent.mkdir(parents=True, exist_ok=True)

combined.to_csv(output_path, index=False, encoding="utf-8-sig")
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps(report, ensure_ascii=False, indent=2))
print("Ortak aday tablosu kaydedildi:", output_path)
