from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

source_path = ROOT / "data/interim/firms_pilot_2018_2024.csv"
output_dir = ROOT / "outputs/reports"

df = pd.read_csv(source_path, dtype="string")

timestamps = pd.to_datetime(
    df["detection_timestamp_utc"],
    utc=True,
    errors="raise",
)

df["year"] = timestamps.dt.year

year_type = pd.crosstab(df["year"], df["type"]).reindex(
    index=range(2018, 2025),
    columns=["0", "2", "3"],
    fill_value=0,
)

type_confidence = pd.crosstab(
    df["type"],
    df["confidence"],
).reindex(
    index=["0", "2", "3"],
    columns=["l", "n", "h"],
    fill_value=0,
)

# Tekrarlanan sabit kaynak incelemesi yalnızca eğitim döneminde
train = df.loc[df["year"] <= 2023]
static_train = train.loc[train["type"] == "2"]

static_grid_counts = (
    static_train.groupby("grid_id").size().sort_values(ascending=False).rename("detection_count")
)

output_dir.mkdir(parents=True, exist_ok=True)

year_type.to_csv(
    output_dir / "firms_pilot_year_type.csv",
    encoding="utf-8-sig",
)

type_confidence.to_csv(
    output_dir / "firms_pilot_type_confidence.csv",
    encoding="utf-8-sig",
)

static_grid_counts.to_csv(
    output_dir / "firms_train_static_grid_counts.csv",
    encoding="utf-8-sig",
)

print("Yıllara göre tespit türleri:")
print(year_type.to_string())

print("\nTespit türüne göre güven düzeyleri:")
print(type_confidence.to_string())

print("\nEğitim döneminde en fazla type=2 tespiti bulunan 10 hücre:")
print(static_grid_counts.head(10).to_string())

print("\nİnceleme tabloları kaydedildi:", output_dir)
