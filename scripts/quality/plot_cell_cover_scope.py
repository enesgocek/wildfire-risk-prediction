"""Render historical map sensitivity from a pinned local comparison report."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from wildfire_risk_prediction.feature_join import require

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / (
    "outputs/reports/dataset/cell_cover_scope_v1/20261119T002103Z_099cd518/readback.json"
)
SOURCE_SHA = "1831e4d0f67789883d9d98f636c6df23194609dbf53a3f74b127ab8c68993f59"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    require(digest(SOURCE) == SOURCE_SHA, "Pinned comparison report")
    report = json.loads(SOURCE.read_bytes())
    rows = [r for r in report["thresholds"] if r["fraction_limit"] in (0, 0.1, 0.25, 0.5, 0.75)]
    require(len(rows) == 5 and report["threshold_selected"] is None, "Descriptive cuts only")
    out = (
        ROOT
        / "outputs/reports/dataset/cell_cover_scope_visual_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(10.4, 5.6))
    for offset, key, color, label in (
        (-0.17, "cgls_2017_cells", "#2463a6", "CGLS 2017: ağaç + çalı sınıfları"),
        (0.17, "clc_2018_cells", "#12816f", "CORINE 2018: seçili odunsu sınıflar"),
    ):
        values = [r[key] for r in rows]
        ax.barh(y + offset, values, height=0.32, color=color, label=label)
        for i, value in enumerate(values):
            ax.text(
                value + 20, i + offset, f"{value:,}".replace(",", "."), va="center", fontsize=10
            )
    ax.set_yticks(
        y, ["Herhangi bir kesişim (>0)", "En az %10", "En az %25", "En az %50", "En az %75"]
    )
    ax.invert_yaxis()
    ax.set_xlim(0, 3200)
    ax.axvline(2889, color="#707070", linestyle="--", linewidth=1)
    ax.text(2909, -0.63, "Mevcut aday kapsam: 2.889 hücre", fontsize=9, ha="right", color="#555555")
    ax.set_xlabel("Belirtilen kesimi sağlayan hücre sayısı / 2.889")
    ax.set_title(
        "Orman/çalılık payına göre kapsam, kullanılan haritaya da bağlı",
        loc="left",
        fontsize=13,
        pad=30,
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    fig.text(
        0.02,
        0.02,
        "Dört il, AOI ile kesişen hücre alanları. Tarih, sınıf tanımı ve payda farkları var.\n"
        "Bu bir doğruluk/gerçek örtü değişimi ölçümü değildir; eşik seçilmedi ve hücre dışlanmadı.",
        fontsize=9,
        color="#444444",
    )
    fig.tight_layout(rect=[0, 0.10, 1, 0.97])
    path = out / "scope_options.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    receipt = {
        "input_report_sha256": SOURCE_SHA,
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {path.name: digest(path)},
        "researcher_review": False,
        "habitat_policy_accepted": False,
        "labels_created": False,
    }
    (out / "readback.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT).as_posix())
    print("readback_sha256", digest(out / "readback.json"))


if __name__ == "__main__":
    main()
