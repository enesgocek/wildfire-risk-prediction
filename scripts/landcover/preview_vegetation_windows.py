"""Scientific comparison figure for the matched seasonal vegetation sample."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main():
    frame = pd.read_csv(ROOT / "outputs/reports/landscape/seasonal_v1/comparisons_32cells.csv")
    dates = sorted(frame.date.unique())
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.9))
    for n, (window, color) in enumerate(
        zip([16, 30, 60], ["#406eaf", "#3b9c83", "#d28a35"], strict=True)
    ):
        rows = frame[frame.window_days.eq(window)].set_index("date").loc[dates]
        positions = np.arange(4) + (n - 1) * 0.25
        coverage = rows.ratio_at_least_90pct_cells / 32 * 100
        bars = axes[0].bar(positions, coverage, width=0.23, color=color, label=f"{window} gün")
        axes[0].bar_label(
            bars, labels=[str(v) for v in rows.ratio_at_least_90pct_cells], fontsize=8, padding=3
        )
        bars = axes[1].bar(positions, rows.median_age_median_days, width=0.23, color=color)
        axes[1].bar_label(bars, fmt="%.1f", fontsize=8, padding=3)
    for ax in axes:
        ax.set_xticks(np.arange(4), ["1 Şubat", "1 Mayıs", "1 Ağustos", "1 Kasım"])
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.16)
        ax.set_axisbelow(True)
    axes[0].set_ylim(0, 112)
    axes[0].set_ylabel("AOI alanının en az %90'ında destek bulunan hücre (%)")
    axes[0].set_title("Alan desteği · etiketler 32 hücre içindeki sayı")
    axes[0].legend(frameon=False, ncols=3, loc="upper left")
    axes[1].set_ylim(0, 41)
    axes[1].set_ylabel("Hücrelerin piksel medyan yaşı özetinin medyanı (gün)")
    axes[1].set_title("Görüntü yaşı · yalnız destekli hücreler")
    fig.suptitle(
        "Landsat 8 geçmiş görüntü pencereleri — eşleştirilmiş 2018 mevsim örneği", fontsize=13
    )
    fig.text(
        0.5,
        0.025,
        "Aynı 32 hücre; dört kesim tarihi. %90 tanısal eşik, model kabul kuralı değildir.\n"
        "Kaynak yayımlanma zamanı bilinmiyor; operasyonel uygunluk doğrulanmadı.",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.1, 1, 0.94))
    output = ROOT / "outputs/figures/landscape/seasonal_v1"
    output.mkdir(parents=True, exist_ok=True)
    for suffix in ["png", "svg"]:
        fig.savefig(output / f"window_comparison_2018.{suffix}", dpi=180)
    plt.close(fig)
    print(output / "window_comparison_2018.png")


if __name__ == "__main__":
    main()
