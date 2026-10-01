import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Geod
from shapely.geometry import Point, box
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
OUTPUT = ROOT / "data/interim/event_grouping"
REPORTS = ROOT / "outputs/reports"

# Bunlar karşılaştırma ayarlarıdır; nihai olay kuralları değildir.
DISTANCES_M = [500, 1000, 2000]
TIME_GAPS_H = [24, 48, 72]

df = pd.read_csv(SOURCE, dtype="string")
df["timestamp"] = pd.to_datetime(df["detection_timestamp_utc"], utc=True, errors="raise")

# Ayar incelemesi yalnızca eğitim döneminde yapılır.
df = df.loc[df["timestamp"].dt.year.between(2018, 2023)].copy()
df = df.sort_values(["timestamp", "detection_id"]).reset_index(drop=True)

if df.empty or df["detection_id"].isna().any():
    raise ValueError("Eğitim kayıtları boş veya tespit kimlikleri eksik.")
if df["detection_id"].duplicated().any():
    raise ValueError("Tekrarlanan tespit kimliği bulundu.")

longitude = pd.to_numeric(df["longitude"], errors="raise").to_numpy()
latitude = pd.to_numeric(df["latitude"], errors="raise").to_numpy()

if not (
    np.isfinite(longitude).all()
    and np.isfinite(latitude).all()
    and (np.abs(longitude) <= 180).all()
    and (np.abs(latitude) <= 90).all()
):
    raise ValueError("Geçersiz koordinat bulundu.")

# WGS84 üzerinde gerçek mesafe hesaplanır.
geod = Geod(ellps="WGS84")
points = [Point(x, y) for x, y in zip(longitude, latitude, strict=True)]
tree = STRtree(points)
times_ns = np.array([value.value for value in df["timestamp"]], dtype=np.int64)

OUTPUT.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)
summaries = []

for distance_m in DISTANCES_M:
    # Coğrafi kutu yalnızca hızlı aday aramasıdır.
    # Son mesafe kontrolü aşağıda WGS84 ile yapılır.
    latitude_margin = distance_m / 100000
    longitude_margin = latitude_margin / np.cos(np.deg2rad(latitude))

    spatial_neighbours = []

    for i in range(len(df)):
        search_box = box(
            longitude[i] - longitude_margin[i],
            latitude[i] - latitude_margin,
            longitude[i] + longitude_margin[i],
            latitude[i] + latitude_margin,
        )
        neighbours = tree.query(search_box)
        neighbours = neighbours[neighbours > i]

        if len(neighbours):
            _, _, distances = geod.inv(
                np.full(len(neighbours), longitude[i]),
                np.full(len(neighbours), latitude[i]),
                longitude[neighbours],
                latitude[neighbours],
            )
            neighbours = neighbours[np.asarray(distances) <= distance_m]

        spatial_neighbours.append(neighbours)

    for gap_h in TIME_GAPS_H:
        scenario = f"d{distance_m}m_t{gap_h}h"
        print("İnceleniyor:", scenario, flush=True)

        parent = np.arange(len(df))
        sizes = np.ones(len(df), dtype=np.int64)
        gap_ns = gap_h * 3600 * 1_000_000_000
        edge_count = 0

        def find(index, parent=parent):
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index

        def union(first, second, parent=parent, sizes=sizes, find=find):
            first = find(first)
            second = find(second)
            if first == second:
                return
            if sizes[first] < sizes[second]:
                first, second = second, first
            parent[second] = first
            sizes[first] += sizes[second]

        for i, neighbours in enumerate(spatial_neighbours):
            selected = neighbours[(times_ns[neighbours] - times_ns[i]) <= gap_ns]
            edge_count += len(selected)
            for j in selected:
                union(i, int(j))

        roots = np.fromiter((find(i) for i in range(len(df))), dtype=np.int64)
        cluster_numbers = pd.factorize(roots, sort=False)[0] + 1

        assignments = df[["detection_id", "grid_id", "source_sensor", "timestamp"]].copy()
        assignments["cluster_id"] = [f"{scenario}_C{number:06d}" for number in cluster_numbers]

        clusters = assignments.groupby("cluster_id").agg(
            detection_count=("detection_id", "size"),
            first_detection_utc=("timestamp", "min"),
            last_detection_utc=("timestamp", "max"),
            grid_count=("grid_id", "nunique"),
            sensor_count=("source_sensor", "nunique"),
        )
        clusters["duration_hours"] = (
            clusters["last_detection_utc"] - clusters["first_detection_utc"]
        ).dt.total_seconds() / 3600

        if assignments["detection_id"].nunique() != len(df):
            raise ValueError("Gruplama sırasında kayıt kaybı oluştu.")
        if int(clusters["detection_count"].sum()) != len(df):
            raise ValueError("Küme toplamları kaynak kayıtlarla uyuşmuyor.")

        assignments.to_csv(OUTPUT / f"{scenario}_assignments.csv", index=False)
        clusters.to_csv(OUTPUT / f"{scenario}_clusters.csv")

        summaries.append(
            {
                "scenario": scenario,
                "distance_m": distance_m,
                "time_gap_hours": gap_h,
                "detection_count": len(df),
                "cluster_count": len(clusters),
                "singleton_cluster_count": int(clusters["detection_count"].eq(1).sum()),
                "largest_cluster_detections": int(clusters["detection_count"].max()),
                "longest_cluster_hours": float(clusters["duration_hours"].max()),
                "pair_connection_count": edge_count,
            }
        )

summary = pd.DataFrame(summaries)
summary.to_csv(REPORTS / "event_grouping_sensitivity.csv", index=False)

manifest = {
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "training_detection_count": len(df),
    "analysis_period": "2018–2023",
    "distance_method": "WGS84 geodesic point-centre distance",
    "method": "connected components of spatial-temporal detection links",
    "status": "exploratory clusters; not confirmed events or training labels",
    "limitation": (
        "Chained links can merge different fires. Pilot boundaries and "
        "training-period boundaries can truncate clusters."
    ),
    "scenarios": summaries,
}
(REPORTS / "event_grouping_sensitivity.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("\nKarşılaştırma:")
print(summary.to_string(index=False))
print("\nRapor:", REPORTS / "event_grouping_sensitivity.csv")
