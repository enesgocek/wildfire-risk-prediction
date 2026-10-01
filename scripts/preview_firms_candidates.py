from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd

matplotlib.use("Agg")

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
output_path = ROOT / "outputs/figures/firms_train_candidates.png"

df = pd.read_csv(
    ROOT / "data/interim/firms_fire_candidates_2018_2024.csv",
    dtype="string",
)

timestamps = pd.to_datetime(
    df["detection_timestamp_utc"],
    utc=True,
    errors="raise",
)

train = df.loc[timestamps.dt.year <= 2023].copy()
train["year"] = timestamps.loc[train.index].dt.year
train["month"] = timestamps.loc[train.index].dt.month

points = gpd.GeoDataFrame(
    train,
    geometry=gpd.points_from_xy(
        pd.to_numeric(train["longitude"], errors="raise"),
        pd.to_numeric(train["latitude"], errors="raise"),
    ),
    crs=4326,
).to_crs(6933)

aoi = gpd.read_file(ROOT / "data/aoi/aoi.geojson").to_crs(6933)

monthly = pd.crosstab(train["month"], train["year"]).reindex(
    index=range(1, 13),
    columns=range(2018, 2024),
    fill_value=0,
)

fig, axes = plt.subplots(
    1,
    2,
    figsize=(16, 7),
    gridspec_kw={"width_ratios": [1.4, 1]},
    layout="constrained",
)

aoi.plot(
    ax=axes[0],
    facecolor="#f1f5f9",
    edgecolor="#64748b",
    linewidth=0.5,
)

points.plot(
    ax=axes[0],
    color="#dc2626",
    markersize=2,
    alpha=0.25,
)

axes[0].set_title("2018–2023 — Yangın olayı gruplaması adayları")
axes[0].set_axis_off()

for year in monthly.columns:
    axes[1].plot(
        monthly.index,
        monthly[year],
        marker="o",
        markersize=3,
        label=str(year),
    )

axes[1].set_title("Eğitim döneminde aylık tespit sayıları")
axes[1].set_xlabel("Ay")
axes[1].set_ylabel("Aday tespit sayısı")
axes[1].set_xticks(range(1, 13))
axes[1].grid(alpha=0.2)
axes[1].legend(title="Yıl")

output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=200)
plt.close(fig)

print("Eğitim dönemindeki aday tespit:", len(train))
print("\nAylık aday tespit tablosu:")
print(monthly.to_string())
print("\nGörsel kaydedildi:", output_path)
