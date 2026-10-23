"""Offline contact sheets for points without researcher notes; no classification."""

import hashlib
import json
import socket
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SOURCES = {
    "first": (
        "preevent_image_windows_v1/20261023T152456Z_e03ae61d",
        "a3d1378c3f13a2b1947b045aaa2f296426bdfb4246861160aa83adf3caa6a5f8",
    ),
    "native": (
        "native_candidate_cover_v1/20261023T143656Z_90c1c93b",
        "65443618bddc95f01a453f0186473891112d9712b50289e3c4613ac71470568b",
    ),
    "human1": (
        "preevent_researcher_review_v1/20261023T153234Z_ecee9147",
        "36fac85b3d6fe2f288af7070b70cfed5b037f70bd5b0601646a2eeb38e184645",
    ),
    "human2": (
        "habitat_researcher_notes_v1/20261023T160518Z_3166f1d9",
        "d3e71111b30cc6686eee9319165d9b86b25f9d6c1f2811c4dcbca3ab3e1495fb",
    ),
    "dates": (
        "preevent_date_comparison_v1/20261023T154219Z_144befb7",
        "f50778b9bd1a344c35336273fb46d19258481dc50676a692682e8772bd8b468d",
    ),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline review")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    pins, folders, reports = {}, {}, {}

    def pin(path, expected=None):
        value = sha(path)
        if expected is not None and value != expected:
            raise ValueError("Changed source")
        pins[path.relative_to(ROOT).as_posix()] = value

    for key, (relative, expected) in SOURCES.items():
        folder = BASE / relative
        pin(folder / "readback.json", expected)
        report = json.loads((folder / "readback.json").read_text(encoding="utf-8"))
        for name, digest in report.get("artifact_sha256", {}).items():
            pin(folder / name, digest)
        for name, digest in report.get("input_sha256", {}).items():
            pin(ROOT / name, digest)
        folders[key], reports[key] = folder, report
    pin(Path(__file__).resolve())
    reviewed = {r["detection_id"] for key in ("human1", "human2") for r in reports[key]["records"]}
    geometry = {
        p["detection_id"]: p
        for p in json.loads((folders["native"] / "approximate_support_geometry.json").read_text())[
            "points"
        ]
    }
    remaining = sorted(set(geometry) - reviewed)
    if len(reviewed) != 6 or len(remaining) != 19 or not reviewed.issubset(geometry):
        raise ValueError("Expected six reviewed and nineteen pending points")
    out = (
        BASE
        / "remaining_cover_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    records = []
    for start in range(0, 19, 5):
        group = remaining[start : start + 5]
        fig, axes = plt.subplots(3, 2, figsize=(12, 16))
        for offset, (ax, identity) in enumerate(zip(axes.flat, group, strict=False)):
            code = f"R{start + offset + 1:02d}"
            receipt = json.loads((folders["first"] / identity / "receipt.json").read_text())
            with rasterio.open(folders["first"] / identity / "visual.tif") as src:
                rgb = np.dstack((np.moveaxis(src.read(), 0, -1), src.dataset_mask()))
                b = src.bounds
                converter = Transformer.from_crs(6933, src.crs, always_xy=True)
                point = geometry[identity]
                cx, cy = converter.transform(*point["native_center_6933"])
                x, y = converter.transform(*zip(*point["approximate_corners_6933"], strict=True))
                ax.imshow(rgb, extent=[b.left - cx, b.right - cx, b.bottom - cy, b.top - cy])
            ax.plot(np.asarray(x) - cx, np.asarray(y) - cy, color="yellow", linewidth=1.5)
            ax.plot(0, 0, "+", color="red", markersize=8)
            ax.set_title(f"{code} | {identity}\n{receipt['acquired_utc'][:10]}", fontsize=11)
            ax.set_xlabel("Doğu-batı (m)")
            ax.set_ylabel("Kuzey-güney (m)")
            alternate = folders["dates"] / f"{identity}.png"
            records.append(
                {
                    "code": code,
                    "detection_id": identity,
                    "sheet": f"sheet_{start // 5 + 1}.png",
                    "acquired_utc": receipt["acquired_utc"],
                    "visual_sha256": receipt["assets"]["visual"]["sha256"],
                    "alternative_card": alternate.relative_to(ROOT).as_posix()
                    if alternate.is_file()
                    else None,
                    "researcher_note": None,
                    "researcher_reviewed": False,
                    "habitat_admission": False,
                    "target": None,
                }
            )
        for ax in list(axes.flat)[len(group) :]:
            ax.axis("off")
        fig.suptitle(f"Kalan örtü örnekleri — sayfa {start // 5 + 1}/4", fontsize=17)
        fig.text(
            0.5,
            0.015,
            "Sarı: yaklaşık tespit alanı • Kırmızı: kaynak merkez\n"
            "Görüntüler ön inceleme içindir; yeşillik orman veya yangın doğrulaması değildir.",
            ha="center",
            fontsize=10,
        )
        fig.tight_layout(rect=(0, 0.05, 1, 0.96))
        fig.savefig(out / f"sheet_{start // 5 + 1}.png", dpi=150)
        plt.close(fig)
    for path, digest in pins.items():
        if sha(ROOT / path) != digest:
            raise ValueError("Source changed during run")
    for name, value in (("review_index.json", records), ("input_manifest.json", pins)):
        (out / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    report = {
        "version": "remaining_cover_review_v1",
        "points": 19,
        "prior_researcher_points": 6,
        "new_researcher_reviews": 0,
        "labels_created": False,
        "rows_excluded": 0,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "positive_label_permitted": False,
        "final_merge_performed": False,
        "network_used": False,
        "artifact_sha256": {p.name: sha(p) for p in out.iterdir() if p.is_file()},
    }
    (out / "readback.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(out.relative_to(ROOT))
    print("Readback SHA", sha(out / "readback.json"))


if __name__ == "__main__":
    main()
