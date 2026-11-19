"""Read two dated, pre-T public Sentinel crops for researcher cover review only."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import matplotlib
import rasterio
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform, unary_union

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.imagery_review import support_quality
from wildfire_risk_prediction.preevent_imagery import inspect_item, utc_time
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows
from wildfire_risk_prediction.target_admission import specification

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
NATIVE = BASE / "marmaris_native_support_v1/20261119T130257Z_bf16c6bd/readback.json"
NATIVE_SHA = "09baaccbd41d5e8a175b2bd988d46acf25c782fd5ac0b20ab21679bea6024ff4"
INVENTORY = BASE / "marmaris_preevent_inventory_v1/20261119T130348Z_7c9fdbae"
INVENTORY_SHA = "124f620ad4f51edca5b3c647b12290312f9d4dd5ea812cb1423c205ba7409884"
CUTOFF = datetime(2022, 6, 21, tzinfo=UTC)


def select_scenes(payload, support, cutoff):
    choices = []
    for item in payload["features"]:
        check = inspect_item(item, support, cutoff, lookback_days=30)
        if check["metadata_candidate"] and "visual" in item["assets"]:
            choices.append((item, check))
    choices.sort(
        key=lambda v: (
            v[1]["scene_cloud_percent"] is None or v[1]["scene_cloud_percent"] > 20,
            v[1]["days_before_prediction"],
            v[0]["id"],
        )
    )
    by_date = {}
    for item, check in choices:
        by_date.setdefault(check["acquired_utc"][:10], (item, check))
    return list(by_date.values())[:2]


def render(out, images, primary):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for (name, col), info in images.items():
        row = 0 if name == "north" else 1
        ax = axes[row, col]
        if info["state"] != "read":
            ax.text(0.5, 0.5, "Kesit okunamadı", transform=ax.transAxes, ha="center")
            ax.set_axis_off()
            continue
        with rasterio.open(out / info["folder"] / "visual.tif") as src:
            ax.imshow(
                src.read().transpose(1, 2, 0),
                origin="upper",
                extent=(src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top),
            )
            project = Transformer.from_crs(6933, src.crs, always_xy=True).transform
            to_rgb = Transformer.from_crs(4326, src.crs, always_xy=True).transform
            for code, point in primary.items():
                if (name == "south") != (point["native_row"] == 5009):
                    continue
                support = transform(project, Polygon(point["approximate_support_corners_6933"]))
                ax.plot(*support.exterior.xy, color="#fa44ff", lw=1.6)
                x, y = to_rgb(point["catalog_longitude"], point["catalog_latitude"])
                ax.scatter(x, y, color="yellow", marker="+", s=50)
                ax.text(
                    x + 45,
                    y + 40,
                    code,
                    fontsize=11,
                    color="white",
                    bbox={"facecolor": "black", "alpha": 0.6, "pad": 1},
                )
            ax.set_xlim(src.bounds.left, src.bounds.right)
            ax.set_ylim(src.bounds.bottom, src.bounds.top)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
        ax.set_title(f"{info['acquired_utc'][:10]} | " + ("M2–M5" if name == "north" else "M1"))
    fig.suptitle("Marmaris • 21 Haziran 2022 öncesi Sentinel-2 örtü incelemesi", fontsize=14)
    fig.text(
        0.5,
        0.025,
        "Mor: komşu ham merkezlerden yaklaşık piksel alanı; resmî köşe veya yanmış alan değil.\n"
        "Sarı artı: katalog merkezi. Örtü ön notu isteniyor; yangın etiketi kabulü değil.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.065, 1, 0.955))
    fig.savefig(out / "marmaris_cover_review.png", dpi=110, facecolor="white")
    plt.close(fig)


def main():
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    require(digest(NATIVE) == NATIVE_SHA, "Pinned native parent")
    require(digest(INVENTORY / "readback.json") == INVENTORY_SHA, "Pinned public inventory")
    native = json.loads(NATIVE.read_text())
    metadata = INVENTORY / "catalogue.json"
    inventory = json.loads((INVENTORY / "readback.json").read_text())
    require(digest(metadata) == inventory["metadata_sha256"], "Pinned public metadata")
    require(inventory["native_parent_sha256"] == NATIVE_SHA, "Same reviewed supports")
    pins = {
        NATIVE: NATIVE_SHA,
        metadata: inventory["metadata_sha256"],
        INVENTORY / "readback.json": INVENTORY_SHA,
    }
    primary = {
        f"M{i}": p
        for i, p in enumerate((p for p in native["points"] if p["planned_primary_center"]), 1)
    }
    require(len(primary) == 5, "Five planned native centers")
    whole = unary_union([Polygon(p["approximate_support_corners_6933"]) for p in primary.values()])
    ll = transform(Transformer.from_crs(6933, 4326, always_xy=True).transform, whole.envelope)
    selected = select_scenes(json.loads(metadata.read_text()), ll, CUTOFF)
    require(
        len(selected) == 2 and all(utc_time(c["acquired_utc"]) < CUTOFF for _, c in selected),
        "Two distinct pre-T dates",
    )
    out = (
        BASE
        / "marmaris_cover_review_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    images = {}
    reader = PublicWindows()
    try:
        for col, (item, check) in enumerate(selected):
            epsg = item["properties"]["proj:epsg"]
            for name in ("north", "south"):
                subset = {
                    code: p
                    for code, p in primary.items()
                    if (name == "south") == (p["native_row"] == 5009)
                }
                union = unary_union(
                    [Polygon(p["approximate_support_corners_6933"]) for p in subset.values()]
                )
                project = Transformer.from_crs(6933, epsg, always_xy=True).transform
                support = transform(project, union)
                folder = out / f"{name}_{col}"
                folder.mkdir(exist_ok=False)
                info = {
                    "folder": folder.name,
                    "acquired_utc": check["acquired_utc"],
                    "item_id": item["id"],
                    "metadata_check": check,
                }
                try:
                    assets, quality = reader.read(item, support, folder)
                    per_point = {}
                    with rasterio.open(folder / "SCL.tif") as scl:
                        for code, point in subset.items():
                            polygon = transform(
                                project, Polygon(point["approximate_support_corners_6933"])
                            )
                            per_point[code] = support_quality(
                                scl.read(1), scl.dataset_mask() > 0, scl.transform, polygon
                            )
                    info.update(
                        state="read",
                        assets=assets,
                        union_quality=quality,
                        per_point_quality=per_point,
                    )
                except Exception as exc:
                    # In particular, signed raster URLs and exception messages never enter output.
                    info.update(state="failed_outputs_retained", error_type=type(exc).__name__)
                images[name, col] = info
                print(name, col, info["state"], flush=True)
    finally:
        reader.close()
    render(out, images, primary)
    result = {
        "scope": "five_Marmaris_preT_visual_cover_notes_only",
        "state": "researcher_review_pending"
        if all(i["state"] == "read" for i in images.values())
        else "incomplete_outputs_retained",
        "prediction_cutoff_utc": CUTOFF.isoformat(),
        "primary_index": {
            code: {
                "detection_id": p["detection_id"],
                "native_row": p["native_row"],
                "native_column": p["native_column"],
                "researcher_note": None,
                "researcher_reviewed": False,
                "target": None,
            }
            for code, p in primary.items()
        },
        "images": {f"{k[0]}_{k[1]}": v for k, v in images.items()},
        "number_of_independent_acquisition_dates": len(selected),
        "historical_available_at_verified": False,
        "source_initial_point_count_resolved": False,
        "L_memberships_created": 0,
        "gate": specification(),
        "model_trained": False,
        "final_merge_performed": False,
        "cloud_jobs_started": 0,
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "code_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in [
                Path(__file__),
                ROOT / "src/wildfire_risk_prediction/public_sentinel_windows.py",
                ROOT / "src/wildfire_risk_prediction/preevent_imagery.py",
                ROOT / "src/wildfire_risk_prediction/imagery_review.py",
            ]
        },
        "artifact_sha256": {
            p.relative_to(out).as_posix(): digest(p) for p in out.rglob("*") if p.is_file()
        },
    }
    path = out / "readback.json"
    require(all(digest(p) == h for p, h in pins.items()), "Input closure")
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Readback")
    print(path.relative_to(ROOT).as_posix(), digest(path))


if __name__ == "__main__":
    main()
