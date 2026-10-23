"""Render fixed examples of approximate native support and the retained 2017 map."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
from pyproj import Transformer
from rasterio.windows import Window

from wildfire_risk_prediction.point_cover_context import cover_group

ROOT = Path(__file__).resolve().parents[2]
COLORS = {
    "forest": ("#25743c", "Orman"),
    "shrub": ("#84a84b", "Çalılık"),
    "agriculture": ("#efc85c", "Tarım"),
    "urban_built": ("#bd7374", "Yerleşim"),
    "herbaceous": ("#d9e4a2", "Otsu"),
    "herbaceous_wetland": ("#82c7b7", "Otsu sulak"),
    "water": ("#70aed2", "Su"),
    "ocean": ("#70aed2", "Su"),
    "unknown_or_unmapped": ("#dedede", "Bilinmeyen"),
    "bare_sparse": ("#c8b89b", "Çıplak/seyrek"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report_directory", type=Path)
    args = parser.parse_args()
    parent = args.report_directory.resolve()
    if not parent.is_relative_to(ROOT / "outputs/reports/dataset/native_candidate_cover_v1"):
        raise ValueError("Expected local native cover report")
    report = json.loads((parent / "readback.json").read_text())
    for name, digest in report["artifact_sha256"].items():
        if sha(parent / name) != digest:
            raise ValueError("Changed parent artifact")
    source = ROOT / "data/raw/landcover/landcover_copernicus_2017.tif"
    if sha(source) != "ee8bd6c9f742dbbdfcdcbbb6ecc446499f05d676eaeb202c4345c11ea6006470":
        raise ValueError("Changed map")
    frame = pd.read_csv(parent / "native_point_context.csv")
    geometry = json.loads((parent / "approximate_support_geometry.json").read_text())
    shapes = {p["detection_id"]: p for p in geometry["points"]}
    # Purposeful examples, not a random accuracy sample.
    ids = ["SNPP_815579_4958", "SNPP_815579_17606", "SNPP_815579_146808"]
    to_map = Transformer.from_crs(6933, 3857, always_xy=True)
    to_area = Transformer.from_crs(3857, 6933, always_xy=True)
    fig, axes = plt.subplots(1, 3, figsize=(15, 6.7))
    seen = set()
    with rasterio.open(source) as dataset:
        for ax, identifier in zip(axes, ids, strict=True):
            shape = shapes[identifier]
            row = frame.set_index("detection_id").loc[identifier]
            cx, cy = shape["native_center_6933"]
            x, y = to_map.transform([cx - 600, cx + 600], [cy - 600, cy + 600])
            top, left = dataset.index(min(x), max(y))
            bottom, right = dataset.index(max(x), min(y))
            top, left = max(0, top), max(0, left)
            bottom, right = min(dataset.height - 1, bottom), min(dataset.width - 1, right)
            data = dataset.read(
                1, window=Window(left, top, right - left + 1, bottom - top + 1), masked=True
            )
            polygons, colors = [], []
            t = dataset.transform
            for r, c in np.ndindex(data.shape):
                group = cover_group(None if np.ma.is_masked(data[r, c]) else int(data[r, c]))
                seen.add(group)
                corners = [
                    (t.a * cc + t.c, t.e * rr + t.f)
                    for cc, rr in [
                        (left + c, top + r),
                        (left + c + 1, top + r),
                        (left + c + 1, top + r + 1),
                        (left + c, top + r + 1),
                    ]
                ]
                xx, yy = to_area.transform(*np.asarray(corners).T)
                polygons.append(np.column_stack([xx - cx, yy - cy]))
                colors.append(COLORS.get(group, ("#dedede", group))[0])
            ax.add_collection(PolyCollection(polygons, facecolors=colors, edgecolors="none"))
            poly = np.asarray(shape["approximate_corners_6933"])
            ax.plot(poly[:, 0] - cx, poly[:, 1] - cy, color="#111111", linewidth=2.5)
            ax.scatter([0], [0], marker="x", s=85, color="#f50000", linewidths=2, zorder=4)
            ratio = row.forest_shrub_fraction_of_mapped_area * 100
            center = COLORS[row.center_cover_group_2017][1]
            ax.set_title(
                f"{row.detection_timestamp_utc[:10]} | Merkez: {center}\n"
                f"Yaklaşık alanda harita orman/çalı payı: %{ratio:.1f}",
                fontsize=11,
            )
            ax.set(
                xlim=(-600, 600),
                ylim=(-600, 600),
                aspect="equal",
                xlabel="Merkeze göre harita x (m)",
                ylabel="Merkeze göre harita y (m)",
            )
            ax.tick_params(labelsize=8)
    legend = [
        Patch(facecolor=COLORS[g][0], label=COLORS[g][1])
        for g in COLORS
        if g in seen and g != "ocean"
    ]
    fig.legend(
        handles=legend, loc="lower center", bbox_to_anchor=(0.5, 0.10), ncol=7, frameon=False
    )
    fig.suptitle(
        "Aynı nokta, farklı çevre: uydu pikseli ile eski örtü haritasını birlikte okuma",
        fontsize=15,
        y=0.98,
    )
    fig.text(
        0.5,
        0.045,
        "Siyah sınır: komşu uydu merkezlerinden yaklaşık alan. Kırmızı ×: native piksel merkezi.",
        ha="center",
        fontsize=10,
    )
    fig.text(
        0.5,
        0.012,
        "Zemin 2017 sınıflandırmasıdır; uydu fotoğrafı, resmî piksel sınırı "
        "veya doğrulanmış yangın türü değildir.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.24, 1, 0.91))
    out = (
        ROOT
        / "outputs/reports/dataset/native_cover_figure_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    image = out / "native_cover_examples.png"
    fig.savefig(image, dpi=160)
    plt.close(fig)
    (out / "readback.json").write_text(
        json.dumps(
            {
                "parent_report_sha256": sha(parent / "readback.json"),
                "figure_sha256": sha(image),
                "script_sha256": sha(Path(__file__)),
                "reference_map_sha256": sha(source),
                "purpose_selected_detection_ids": ids,
                "human_scientific_review": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
