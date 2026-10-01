from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
output_path = ROOT / "outputs/figures/landcover_fractions_preview.png"

parts = gpd.read_file(ROOT / "data/interim/grid_aoi_parts.geojson").to_crs(6933)

fractions = pd.read_csv(ROOT / "data/interim/grid_landcover_2017.csv")

data = parts[["grid_id", "aoi_area_km2", "geometry"]].merge(
    fractions[["grid_id", "natural_vegetation_fraction"]],
    on="grid_id",
    how="left",
    validate="one_to_one",
)

if len(data) != len(fractions):
    raise ValueError("Geometri ve örtü tablosundaki hücreler uyuşmuyor.")

values = data["natural_vegetation_fraction"]

if not np.isfinite(values).all():
    raise ValueError("Eksik veya geçersiz örtü oranı var.")

if (values < -1e-6).any() or (values > 1 + 1e-6).any():
    raise ValueError("Beklenen sınırların dışında örtü oranı var.")

# Yalnızca çizimde küçük yuvarlama taşmalarını sınırla
data["plot_fraction"] = values.clip(0, 1)

fig, axes = plt.subplots(
    1,
    2,
    figsize=(16, 7),
    gridspec_kw={"width_ratios": [1.6, 1]},
    layout="constrained",
)

data.plot(
    ax=axes[0],
    column="plot_fraction",
    cmap="YlGn",
    vmin=0,
    vmax=1,
    edgecolor="#64748b",
    linewidth=0.15,
    legend=True,
    legend_kwds={"label": "Doğal bitki örtüsü oranı"},
)

axes[0].set_title("2017 — Orman, çalılık ve otsu bitki örtüsü")
axes[0].set_axis_off()

axes[1].hist(
    data["plot_fraction"],
    bins=np.linspace(0, 1, 21),
    color="#15803d",
    edgecolor="white",
)

axes[1].set_title("Hücre bazında örtü dağılımı")
axes[1].set_xlabel("Doğal bitki örtüsü oranı")
axes[1].set_ylabel("Hücre sayısı")
axes[1].set_xlim(0, 1)
axes[1].grid(axis="y", alpha=0.2)

output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=200)
plt.close(fig)

print("Toplam hücre:", len(data))
print("Doğal bitki örtüsü oranı %0 olan hücre:", int((values == 0).sum()))

# Bunlar yalnızca inceleme aralıkları; eleme kuralları değil
for threshold in [0.05, 0.10, 0.20, 0.50]:
    count = int((values < threshold).sum())
    print(f"Örtü oranı %{threshold * 100:.0f} altında olan hücre: {count}")

small_parts = data["aoi_area_km2"] < 1
print(
    "AOI içinde kalan alanı 1 km²'den küçük hücre:",
    int(small_parts.sum()),
)

print("Görsel kaydedildi:", output_path)
