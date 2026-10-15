"""Render the accepted single-pair diagnostic; this is not a wildfire risk map."""

import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / "outputs/reports/dataset/observation_core_spatial_v1/20261015T110104Z_9512936a"
PARENT_SHA = "e8870f29a99e2c7bb5aaad3b853cabda0f3df76442072c3ea7229a8e88c0fed2"


def deny(*args, **kwargs):
    raise RuntimeError("Offline diagnostic figure")


def run():
    socket.socket.connect = deny
    socket.create_connection = deny
    require(digest(PARENT / "readback.json") == PARENT_SHA, "Pinned spatial parent")
    parent = json.loads((PARENT / "readback.json").read_text(encoding="utf-8"))
    completion = json.loads((PARENT / "completion_readback.json").read_text(encoding="utf-8"))
    launcher = json.loads((PARENT / "launcher_receipt.json").read_text(encoding="utf-8"))
    require(
        completion["report_sha256"] == PARENT_SHA
        and launcher["status"] == "child_completed"
        and parent["negative_label_permitted"] is False,
        "Closed completed spatial parent",
    )
    for name, expected in parent["artifact_sha256"].items():
        require(digest(PARENT / name) == expected, "Plot artifact closure")
    for name, expected in parent["input_sha256"].items():
        require(digest(ROOT / name) == expected, "Plot input closure")
    parts = gpd.read_file(ROOT / "data/interim/grid_aoi_parts.geojson").to_crs(6933)
    table = pd.read_csv(PARENT / "l2_sample_2018045.0000_area_estimate.csv")
    frame = parts[["grid_id", "geometry"]].merge(table, on="grid_id", validate="one_to_one")
    require(len(frame) == parent["grid_count"], "All diagnostic map cells")
    groups = ["reconstructed_domain", "nominal_nonfire_land", "cloud"]
    titles = [
        "Yeniden kurulan yaklaşık alan",
        "Kalite koşulunu geçen\nyangın dışı kara",
        "Bulut sınıfının yaklaşık alanı",
    ]
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    for ax, group, title in zip(axes, groups, titles, strict=True):
        frame.plot(
            ax=ax,
            column=group + "_fraction_estimate",
            cmap="YlGnBu",
            vmin=0,
            vmax=1,
            linewidth=0,
            rasterized=True,
        )
        ax.set_title(title, fontsize=11)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.suptitle("Uydu gözlem tanısı — 14 Şubat 2018, 00:00–00:06 UTC", fontsize=15)
    fig.subplots_adjust(left=0.02, right=0.91, top=0.85, bottom=0.22, wspace=0.08)
    cax = fig.add_axes([0.93, 0.29, 0.012, 0.46])
    bar = fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0, 1), cmap="YlGnBu"), cax=cax)
    bar.set_label("Hücrenin AOI içindeki alanına oran (0–1)", fontsize=10)
    fig.text(
        0.03,
        0.13,
        "Tek altı dakikalık geçiş • 2.899 kayıtlı hücre • EPSG:6933 • "
        "Tarama içindeki komşu merkezlerden yaklaşık geometri",
        fontsize=10,
    )
    fig.text(
        0.03,
        0.08,
        "Bu görsel risk/yangın yokluğu haritası değildir. Sınıf alanları taramalar "
        "arasında örtüşebilir; toplanmaz. Günlük gözlem durumu: unknown.",
        fontsize=10,
    )
    out = (
        ROOT
        / "outputs/reports/dataset/observation_core_figure_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    fig.savefig(out / "observation_support.png", dpi=160)
    plt.close(fig)
    require(digest(PARENT / "readback.json") == PARENT_SHA, "Unchanged plot parent")
    report = {
        "status": "diagnostic_figure_rendered_not_human_review",
        "parent_sha256": PARENT_SHA,
        "script_sha256": digest(Path(__file__)),
        "artifact_sha256": {"observation_support.png": digest(out / "observation_support.png")},
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "network_bytes": 0,
    }
    (out / "readback.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "completion_readback.json").write_text(
        json.dumps({"status": "passed", "report_sha256": digest(out / "readback.json")}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    run()
