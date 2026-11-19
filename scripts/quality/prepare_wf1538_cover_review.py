"""Two pre-T public Sentinel crops for WF1538 human cover notes; no labels."""

import argparse
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import matplotlib
import rasterio
import requests
from prepare_marmaris_cover_review import select_scenes
from prepare_marmaris_native_pair import write
from pyproj import Transformer
from shapely.geometry import Point, Polygon
from shapely.ops import transform

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.imagery_review import support_quality
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows
from wildfire_risk_prediction.target_admission import specification

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
CUTOFF = datetime(2022, 5, 27, tzinfo=UTC)


def render(out, images, native):
    source = Point(native["source_point_6933"])
    polygon = Polygon(native["approximate_support_corners_6933"])
    center = Point(native["native_center_6933"])
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    for ax, info in zip(axes, images, strict=True):
        if info["state"] != "read":
            ax.text(0.5, 0.5, "Görüntü alınamadı", ha="center")
            continue
        with rasterio.open(out / info["folder"] / "visual.tif") as ds:
            rgb = ds.read().transpose(1, 2, 0)
            extent = (ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top)
            ax.imshow(rgb, extent=extent, origin="upper", interpolation="nearest")
            project = Transformer.from_crs(6933, ds.crs, always_xy=True).transform
            poly, sp, cp = [transform(project, g) for g in (polygon, source, center)]
            circle = transform(project, source.buffer(250))
            ax.plot(*poly.exterior.xy, c="#fa44ff", lw=2, label="B: yaklaşık yangın pikseli")
            ax.plot(*circle.exterior.xy, c="yellow", ls="--", lw=1, label="A: kaynak noktası 250 m")
            ax.scatter(sp.x, sp.y, marker="*", s=100, c="yellow")
            ax.text(sp.x + 20, sp.y + 20, "A", c="yellow", weight="bold")
            ax.scatter(cp.x, cp.y, marker="+", s=100, c="cyan")
            ax.text(cp.x + 20, cp.y + 20, "B", c="cyan", weight="bold")
            ax.set_xlim(ds.bounds.left, ds.bounds.right)
            ax.set_ylim(ds.bounds.bottom, ds.bounds.top)
        ax.set_title(info["acquired_utc"][:10] + " • Sentinel-2 olay öncesi")
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("WF1538: kaynak noktası ve komşu uydu adayının örtüsü", fontsize=13)
    fig.text(
        0.5,
        0.04,
        "Sarı A: yayımlanmış kaynak koordinatı • Mor B: komşu ham merkezlerden yaklaşık alan\n"
        "Mor sınır yanmış alan veya resmî köşe değil. Yalnız örtü ön notu isteniyor.",
        ha="center",
        fontsize=9,
    )
    axes[0].legend(loc="lower left", fontsize=8)
    fig.tight_layout(rect=(0, 0.1, 1, 0.94))
    fig.savefig(out / "wf1538_cover_review.png", dpi=110, facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    args = parser.parse_args()
    native_path = args.native.resolve()
    require(
        native_path.is_relative_to(BASE / "wf1538_native_support_v1"), "Contained native parent"
    )
    native = json.loads(native_path.read_text(encoding="utf-8"))
    require(
        native["code_sha256"]["scripts/quality/audit_wf1538_native_support.py"]
        == digest(ROOT / "scripts/quality/audit_wf1538_native_support.py"),
        "Current corrected native code",
    )
    require(
        native["detection_id"] == "N20_815590_170090"
        and native["L_memberships_created"] == 0
        and native["gate"] == specification(),
        "Review-only single candidate",
    )
    require(
        all(digest(ROOT / n) == h for n, h in native["input_sha256"].items()),
        "Native input closure",
    )
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    polygon = Polygon(native["approximate_support_corners_6933"])
    source = Point(native["source_point_6933"])
    whole = polygon.union(source.buffer(1)).convex_hull
    ll = transform(Transformer.from_crs(6933, 4326, always_xy=True).transform, whole.envelope)
    params = {
        "collections": "sentinel-2-l2a",
        "bbox": ",".join(map(str, ll.bounds)),
        "datetime": (CUTOFF - timedelta(days=30)).isoformat() + "/" + CUTOFF.isoformat(),
        "limit": 100,
    }
    out = (
        BASE
        / "wf1538_cover_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    with requests.Session() as session:
        session.trust_env = False
        response = session.get(
            "https://planetarycomputer.microsoft.com/api/stac/v1/search",
            params=params,
            timeout=(15, 45),
            allow_redirects=False,
        )
        require(
            response.status_code == 200 and len(response.content) <= 8_000_000,
            "Bounded public catalogue response",
        )
        (out / "catalogue.json").write_bytes(response.content)
    payload = json.loads(response.content)
    require(
        not any(link.get("rel") == "next" for link in payload.get("links", [])),
        "Catalogue pagination must not be silently truncated",
    )
    selected = select_scenes(payload, ll, CUTOFF)
    require(len(selected) == 2, "Two distinct pre-T scene dates")
    images = []
    reader = PublicWindows()
    try:
        for i, (item, check) in enumerate(selected):
            folder = out / str(i)
            folder.mkdir(exist_ok=False)
            info = {
                "folder": str(i),
                "item_id": item["id"],
                "acquired_utc": check["acquired_utc"],
                "metadata_check": check,
            }
            try:
                project = Transformer.from_crs(
                    6933, item["properties"]["proj:epsg"], always_xy=True
                ).transform
                assets, _ = reader.read(item, transform(project, whole), folder)
                with rasterio.open(folder / "SCL.tif") as scl:
                    quality = {
                        name: support_quality(
                            scl.read(1),
                            scl.dataset_mask() > 0,
                            scl.transform,
                            transform(project, g),
                        )
                        for name, g in (
                            ("source_250m", source.buffer(250)),
                            ("native_fire_support", polygon),
                        )
                    }
                info.update(state="read", assets=assets, quality=quality)
            except Exception as error:
                info.update(state="failed_outputs_retained", error_type=type(error).__name__)
            images.append(info)
            print("Scene", i, info["state"], flush=True)
    finally:
        reader.close()
    render(out, images, native)
    result = {
        "scope": "WF1538_two_preT_cover_notes_only",
        "images": images,
        "state": "researcher_review_pending"
        if all(i["state"] == "read" for i in images)
        else "incomplete_outputs_retained",
        "prediction_cutoff_utc": CUTOFF.isoformat(),
        "public_catalogue_query": params,
        "source_clock_standard_resolved": False,
        "same_physical_fire_verified": False,
        "researcher_cover_note": None,
        "historical_available_at_verified": False,
        "L_memberships_created": 0,
        "labels_created": False,
        "gate": specification(),
        "model_trained": False,
        "final_merge_performed": False,
        "cloud_jobs_started": 0,
        "input_sha256": {native_path.relative_to(ROOT).as_posix(): digest(native_path)},
        "code_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in [
                Path(__file__),
                ROOT / "src/wildfire_risk_prediction/public_sentinel_windows.py",
                ROOT / "src/wildfire_risk_prediction/preevent_imagery.py",
                ROOT / "scripts/quality/prepare_marmaris_cover_review.py",
            ]
        },
        "artifact_sha256": {
            p.relative_to(out).as_posix(): digest(p) for p in out.rglob("*") if p.is_file()
        },
    }
    write(out / "readback.json", result)
    write(out / "completion_readback.json", {"report_sha256": digest(out / "readback.json")})
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))


if __name__ == "__main__":
    main()
