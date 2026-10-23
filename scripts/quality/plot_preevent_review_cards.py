"""Offline, aligned old-cover/TCI/SCL cards for researcher review; no automatic labels."""

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
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from pyproj import Transformer
from rasterio.warp import Resampling, reproject

from wildfire_risk_prediction.point_cover_context import cover_group

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "outputs/reports/dataset/native_candidate_cover_v1/20261023T143656Z_90c1c93b"
MAP = ROOT / "data/raw/landcover/landcover_copernicus_2017.tif"
GROUPS = {
    "forest": ("#25743c", "Orman"),
    "shrub": ("#84a84b", "Çalılık"),
    "agriculture": ("#efc85c", "Tarım"),
    "urban_built": ("#bd7374", "Yerleşim"),
    "herbaceous": ("#d9e4a2", "Otsu"),
    "herbaceous_wetland": ("#82c7b7", "Otsu sulak"),
    "water": ("#70aed2", "Su"),
    "ocean": ("#70aed2", "Deniz"),
    "bare_sparse": ("#c8b89b", "Çıplak/seyrek"),
    "unknown_or_unmapped": ("#dedede", "Bilinmeyen"),
}
SCL_COLORS = [
    "#000000",
    "#ff0000",
    "#333333",
    "#765033",
    "#269c39",
    "#dfc568",
    "#1255d4",
    "#999999",
    "#cccccc",
    "#ffffff",
    "#79dfff",
    "#e97bff",
]
SCL_NAMES = [
    "Veri yok",
    "Kusurlu",
    "Koyu/gölge",
    "Bulut gölgesi",
    "Bitki (orman ayrımı yok)",
    "Bitkisiz",
    "Su",
    "Sınıflanmamış",
    "Orta bulut",
    "Yüksek bulut",
    "Sirüs",
    "Kar/buz",
]
EXAMPLES = ["SNPP_815579_4958", "SNPP_815579_17606", "SNPP_815579_146808"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("window_directory", type=Path)
    args = parser.parse_args()
    source = args.window_directory.resolve()
    if not source.is_relative_to(ROOT / "outputs/reports/dataset/preevent_image_windows_v1"):
        raise ValueError("Expected local windows")
    pins = {}

    def pin(path, expected=None):
        value = sha(path)
        if expected is not None and value != expected:
            raise ValueError("Changed input")
        pins[path.relative_to(ROOT).as_posix()] = value
        return path

    report = json.loads(pin(source / "readback.json").read_text())
    if report["completed_points"] != 25 or report["labels_created"]:
        raise ValueError("Completed unlabelled windows required")
    for name, value in report["artifact_sha256"].items():
        pin(source / name, value)
    native = json.loads(
        pin(
            NATIVE / "readback.json",
            "65443618bddc95f01a453f0186473891112d9712b50289e3c4613ac71470568b",
        ).read_text()
    )
    geometry = json.loads(
        pin(
            NATIVE / "approximate_support_geometry.json",
            native["artifact_sha256"]["approximate_support_geometry.json"],
        ).read_text()
    )
    geometries = {p["detection_id"]: p for p in geometry["points"]}
    pin(MAP, "ee8bd6c9f742dbbdfcdcbbb6ecc446499f05d676eaeb202c4345c11ea6006470")
    pin(Path(__file__).resolve())
    pin(ROOT / "src/wildfire_risk_prediction/point_cover_context.py")
    out = (
        ROOT
        / "outputs/reports/dataset/preevent_review_cards_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    review, panels = [], {}
    for identity in geometries:
        receipt = json.loads((source / identity / "receipt.json").read_text())
        with rasterio.open(source / identity / "visual.tif") as rgb:
            image = np.moveaxis(rgb.read(), 0, -1)
            valid = rgb.dataset_mask() > 0
            rgba = np.concatenate([image, (valid * 255).astype("uint8")[..., None]], axis=2)
            old = np.full((rgb.height, rgb.width), -9999, dtype="int16")
            with rasterio.open(MAP) as reference:
                reproject(
                    rasterio.band(reference, 1),
                    old,
                    dst_transform=rgb.transform,
                    dst_crs=rgb.crs,
                    dst_nodata=-9999,
                    resampling=Resampling.nearest,
                )
            groups = np.zeros_like(old, dtype="uint8")
            keys = list(GROUPS)
            for code in np.unique(old):
                groups[old == code] = keys.index(cover_group(int(code)))
            projector = Transformer.from_crs(6933, rgb.crs, always_xy=True)
            center = projector.transform(*geometries[identity]["native_center_6933"])
            polygon = (
                np.asarray(
                    [
                        projector.transform(*p)
                        for p in geometries[identity]["approximate_corners_6933"]
                    ]
                )
                - center
            )
            bounds = rgb.bounds
            extent = [
                bounds.left - center[0],
                bounds.right - center[0],
                bounds.bottom - center[1],
                bounds.top - center[1],
            ]
        with rasterio.open(source / identity / "SCL.tif") as scl:
            classes = scl.read(1)
            classes[scl.dataset_mask() == 0] = 0
            b = scl.bounds
            scl_extent = [
                b.left - center[0],
                b.right - center[0],
                b.bottom - center[1],
                b.top - center[1],
            ]
        panels[identity] = (groups, rgba, classes, extent, scl_extent, polygon, receipt)
        fig, axes = plt.subplots(1, 3, figsize=(16, 7.4))
        draw(axes, panels[identity], include_scl=True)
        fig.suptitle(
            f"{identity}  |  İlk tespit günü: {receipt['prediction_utc'][:10]}\n"
            "Görsel inceleme adayı — kabul edilmiş habitat/yangın etiketi değil",
            fontsize=14,
        )
        legends = [Patch(facecolor=v[0], label=v[1]) for v in GROUPS.values()]
        fig.legend(
            handles=legends,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.14),
            ncol=5,
            title="Soldaki 2017 haritası (özgün çözünürlük 100 m)",
            fontsize=8,
        )
        fig.legend(
            handles=[
                Patch(facecolor=c, edgecolor="#888888", label=f"{i}: {SCL_NAMES[i]}")
                for i, c in enumerate(SCL_COLORS)
            ],
            loc="lower center",
            ncol=6,
            bbox_to_anchor=(0.5, 0.035),
            title="Sağdaki SCL: otomatik görüntü kalite sınıfları",
            fontsize=8,
        )
        fig.text(
            0.5,
            0.012,
            "Sarı sınır: yaklaşık VIIRS piksel alanı • Kırmızı +: kaynak piksel merkezi "
            "• Kuzey yukarı",
            ha="center",
            fontsize=9,
        )
        fig.subplots_adjust(top=0.79, bottom=0.33, wspace=0.2)
        path = out / f"{identity}.png"
        fig.savefig(path, dpi=150, facecolor="white")
        plt.close(fig)
        review.append(
            {
                "detection_id": identity,
                "card": path.name,
                "item_id": receipt["item_id"],
                "researcher_cover_assessment": "",
                "researcher_notes": "",
                "reviewer": "",
                "reviewed_at": "",
                "human_review_completed": False,
                "fire_label_accepted": False,
            }
        )
    fig, axes = plt.subplots(3, 2, figsize=(12, 15))
    for row, identity in enumerate(EXAMPLES):
        draw(axes[row], panels[identity], include_scl=False)
        axes[row, 0].set_ylabel(f"Örnek {'ABC'[row]} • {identity}\nKuzey–güney (m)")
    fig.suptitle(
        "Olay öncesi gerçek uydu görüntüleri ve eski örtü haritası\n"
        "Üç amaçlı örnek; insan incelemesi ve habitat kabulü bekliyor",
        fontsize=15,
    )
    fig.legend(
        handles=[Patch(facecolor=v[0], label=v[1]) for v in GROUPS.values()],
        loc="lower center",
        ncol=5,
        bbox_to_anchor=(0.5, 0.025),
        fontsize=9,
    )
    fig.text(
        0.5,
        0.012,
        "Sarı sınır yaklaşık alandır; yangın sınırı değildir. Kırmızı + kaynak piksel merkezidir.",
        ha="center",
        fontsize=9,
    )
    fig.subplots_adjust(top=0.92, bottom=0.11, hspace=0.37, wspace=0.2)
    fig.savefig(out / "three_examples.png", dpi=150, facecolor="white")
    plt.close(fig)
    (out / "human_review_template.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for name, value in pins.items():
        if sha(ROOT / name) != value:
            raise ValueError("Input changed during rendering")
    (out / "input_manifest.json").write_text(json.dumps(pins, indent=2))
    artifacts = {p.name: sha(p) for p in out.iterdir() if p.is_file()}
    result = {
        "version": "preevent_review_cards_v1",
        "cards": 25,
        "purposeful_examples": EXAMPLES,
        "map_resampling": "nearest; 100m map remains 100m information",
        "rgb_source": "native 10m byte TCI; no further contrast stretch",
        "network_requests": 0,
        "human_review_completed": False,
        "labels_created": False,
        "artifact_sha256": artifacts,
    }
    (out / "readback.json").write_text(json.dumps(result, indent=2))
    print("Result:", out.relative_to(ROOT).as_posix())
    print("Readback SHA256:", sha(out / "readback.json"))


def draw(axes, data, include_scl):
    groups, rgb, classes, extent, scl_extent, polygon, receipt = data
    axes[0].imshow(
        groups,
        cmap=ListedColormap([v[0] for v in GROUPS.values()]),
        vmin=-0.5,
        vmax=len(GROUPS) - 0.5,
        extent=extent,
        interpolation="nearest",
    )
    axes[0].set_title("2017 örtü haritası • 100 m")
    axes[1].imshow(rgb, extent=extent, interpolation="nearest")
    q = receipt["quality"]
    cloud = 100 * q["cloud_cirrus_fraction"]
    shadow = 100 * q["cloud_shadow_fraction"]
    axes[1].set_title(
        f"Sentinel-2 • {receipt['acquired_utc'][:10]} • 10 m\n"
        f"Alan içi SCL: bulut %{cloud:.1f} • gölge %{shadow:.1f}"
    )
    if include_scl:
        axes[2].imshow(
            classes,
            cmap=ListedColormap(SCL_COLORS),
            norm=BoundaryNorm(np.arange(-0.5, 12.5), 12),
            extent=scl_extent,
            interpolation="nearest",
        )
        axes[2].set_title(
            "SCL otomatik sınıflandırma • 20 m\nBitki sınıfı, orman doğrulaması değildir"
        )
    for ax in axes:
        ax.plot(polygon[:, 0], polygon[:, 1], color="#ffff00", linewidth=1.4)
        ax.plot(0, 0, marker="+", color="#ef2222", markersize=11, markeredgewidth=1.8)
        ax.set_xlim(extent[:2])
        ax.set_ylim(extent[2:])
        ax.set_xlabel("Merkeze göre doğu–batı (m)")
        ax.set_aspect("equal")
        ax.tick_params(labelsize=8)


if __name__ == "__main__":
    main()
