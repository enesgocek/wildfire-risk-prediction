from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
output_path = ROOT / "outputs/figures/grid_preview.png"

aoi = gpd.read_file(ROOT / "data/aoi/aoi.geojson").to_crs(6933)
grid = gpd.read_file(ROOT / "data/aoi/grid_5km.geojson").to_crs(6933)

fig, axes = plt.subplots(1, 2, figsize=(16, 7), layout="constrained")

# Solda bütün pilot alan
grid.plot(
    ax=axes[0],
    facecolor="#dbeafe",
    edgecolor="#64748b",
    linewidth=0.25,
)
aoi.boundary.plot(ax=axes[0], color="#dc2626", linewidth=1)
axes[0].set_title(f"Pilot çalışma alanı — {len(grid):,} hücre")

# Sağda Antalya kıyısında daha yakın görünüm
grid.plot(
    ax=axes[1],
    column="aoi_fraction",
    cmap="YlGnBu",
    vmin=0,
    vmax=1,
    edgecolor="#64748b",
    linewidth=0.5,
    legend=True,
    legend_kwds={"label": "Hücrenin çalışma alanı içinde kalan oranı"},
)
aoi.boundary.plot(ax=axes[1], color="#dc2626", linewidth=1.2)

zoom = gpd.GeoSeries(
    gpd.points_from_xy([30.7], [36.9]),
    crs=4326,
).to_crs(6933)

x, y = zoom.iloc[0].x, zoom.iloc[0].y
axes[1].set_xlim(x - 35_000, x + 35_000)
axes[1].set_ylim(y - 30_000, y + 30_000)
axes[1].set_title("Antalya kıyısı — sınır hücreleri")

for ax in axes:
    ax.set_aspect("equal")
    ax.set_axis_off()

output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=200)
plt.close(fig)

print(f"Harita kaydedildi: {output_path}")
