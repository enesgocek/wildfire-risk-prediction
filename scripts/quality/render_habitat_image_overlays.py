"""Render existing pre-event imagery and CORINE boundaries in the same local CRS."""

import hashlib
import json
from datetime import UTC, datetime
from math import ceil, floor
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET

import matplotlib
import numpy as np
import rasterio
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as PlotPolygon
from pyproj import Transformer
from rasterio.windows import Window
from shapely import segmentize
from shapely.geometry import Polygon, box
from shapely.ops import transform, unary_union

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
MATRIX = BASE / "habitat_evidence_matrix_v1/20261103T215030Z_1106f3eb/readback.json"
MATRIX_SHA = "da877cc44c0626995dde7577892b2dbfbbc9f3a2efea5f226aa268569298366e"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rings(geometry):
    parts = geometry.geoms if geometry.geom_type == "MultiPolygon" else [geometry]
    for part in parts:
        yield part.exterior
        yield from part.interiors


def main():
    pins = {}

    def pin(path, expected):
        require(sha(path) == expected, "Changed evidence: " + path.name)
        pins[path.relative_to(ROOT).as_posix()] = expected

    def load(path, expected):
        pin(path, expected)
        return json.loads(path.read_text(encoding="utf-8"))

    matrix = load(MATRIX, MATRIX_SHA)
    area_path = next(ROOT / p for p in matrix["source_sha256"] if "corine_support_review_v1" in p)
    areas = load(area_path, matrix["source_sha256"][area_path.relative_to(ROOT).as_posix()])
    image_path = next(
        ROOT / p for p in matrix["source_sha256"] if "habitat_temporal_evidence_audit" in p
    )
    images = load(image_path, matrix["source_sha256"][image_path.relative_to(ROOT).as_posix()])
    geometry_path = next(
        ROOT / p for p in areas["source_sha256"] if p.endswith("approximate_support_geometry.json")
    )
    geometry = load(
        geometry_path, areas["source_sha256"][geometry_path.relative_to(ROOT).as_posix()]
    )
    native = {r["detection_id"]: r for r in geometry["points"]}
    raster = next(
        ROOT / p for p in areas["source_sha256"] if p.endswith("U2018_CLC2018_V2020_20u1.tif")
    )
    qml = next(ROOT / p for p in areas["source_sha256"] if p.endswith("clc_legend_qgis_raster.qml"))
    pin(raster, areas["source_sha256"][raster.relative_to(ROOT).as_posix()])
    pin(qml, areas["source_sha256"][qml.relative_to(ROOT).as_posix()])
    colors = {
        int(e.attrib["value"]): e.attrib["color"] for e in ET.parse(qml).findall(".//paletteEntry")
    }
    pin(Path(__file__), sha(Path(__file__)))
    rows = {r["code"]: r for r in matrix["rows"]}
    groups = {
        "C_D": [("C", 0), ("D", 0)],
        "E_F": [("E", 0), ("F", 0)],
        "R03_dates": [("R03", 0), ("R03", 1), ("R03", 2)],
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = BASE / "habitat_image_overlay_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    records, artifacts = [], {}
    with rasterio.open(raster) as clc:
        for group, selections in groups.items():
            fig, axes = plt.subplots(len(selections), 3, figsize=(15, 5.1 * len(selections)))
            for line, (code, date_index) in enumerate(selections):
                row = rows[code]
                evidence = row["image_evidence"][date_index]
                receipt_path = ROOT / evidence["receipt_path"]
                receipt = load(receipt_path, images["source_sha256"][evidence["receipt_path"]])
                visual_path = receipt_path.parent / "visual.tif"
                pin(visual_path, receipt["assets"]["visual"]["sha256"])
                require(
                    receipt["acquired_utc"].replace("Z", "+00:00") == evidence["acquired_utc"],
                    "Date",
                )
                with rasterio.open(visual_path) as src:
                    require(src.crs.to_epsg() == receipt["epsg"], "Image CRS")
                    require(
                        list(src.transform)[:6] == receipt["assets"]["visual"]["transform"],
                        "Image transform",
                    )
                    require(
                        list(src.shape) == receipt["assets"]["visual"]["shape"][1:], "Image shape"
                    )
                    rgb = np.moveaxis(src.read(), 0, -1)
                    alpha = src.dataset_mask()
                    rgba = np.dstack([rgb, alpha])
                    project = Transformer.from_crs(6933, src.crs, always_xy=True).transform
                    support = transform(
                        project,
                        segmentize(
                            Polygon(native[row["detection_id"]]["approximate_corners_6933"]), 12.5
                        ),
                    )
                    center = project(*native[row["detection_id"]]["native_center_6933"])
                    require(box(*src.bounds).covers(support), "Image does not contain support")
                    x0, y0, x1, y1 = support.bounds
                    radius = max(x1 - x0, y1 - y0) / 2 + 200
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    viewport = box(
                        max(src.bounds.left, cx - radius),
                        max(src.bounds.bottom, cy - radius),
                        min(src.bounds.right, cx + radius),
                        min(src.bounds.top, cy + radius),
                    )
                    to_clc = Transformer.from_crs(src.crs, clc.crs, always_xy=True).transform
                    from_clc = Transformer.from_crs(clc.crs, src.crs, always_xy=True).transform
                    back = from_clc(*to_clc(*center))
                    error = max(abs(back[k] - center[k]) for k in (0, 1))
                    require(error < 0.01, "CRS roundtrip")
                    b = transform(to_clc, segmentize(viewport, 25)).bounds
                    c0, r0 = (~clc.transform) * (b[0], b[3])
                    c1, r1 = (~clc.transform) * (b[2], b[1])
                    c0, r0, c1, r1 = floor(c0), floor(r0), ceil(c1), ceil(r1)
                    require(0 <= c0 < c1 <= clc.width and 0 <= r0 < r1 <= clc.height, "Map extent")
                    require((c1 - c0) * (r1 - r0) <= 2500, "Window limit")
                    array = clc.read(1, window=Window(c0, r0, c1 - c0, r1 - r0))
                    by_class = {}
                    for rr in range(array.shape[0]):
                        for cc in range(array.shape[1]):
                            value = int(array[rr, cc])
                            if value == clc.nodata or value == 48:
                                continue
                            require(value in colors, "Unknown class")
                            left, top = clc.transform * (c0 + cc, r0 + rr)
                            right, bottom = clc.transform * (c0 + cc + 1, r0 + rr + 1)
                            cell = transform(
                                from_clc, segmentize(box(left, bottom, right, top), 25)
                            )
                            if cell.intersects(viewport):
                                by_class.setdefault(value, []).append(cell)
                    ax0, ax1, ax2 = axes[line]
                    for ax in (ax0, ax1):
                        ax.imshow(
                            rgba,
                            extent=(
                                src.bounds.left,
                                src.bounds.right,
                                src.bounds.bottom,
                                src.bounds.top,
                            ),
                            interpolation="nearest",
                        )
                    patches, patch_colors = [], []
                    for value, cells in by_class.items():
                        for cell in cells:
                            patches.append(PlotPolygon(list(cell.exterior.coords)))
                            patch_colors.append(colors[value])
                        for ring in rings(unary_union(cells)):
                            ax1.plot(*ring.xy, color="white", linewidth=0.7, alpha=0.8)
                    ax2.add_collection(
                        PatchCollection(
                            patches, facecolors=patch_colors, edgecolors="none", antialiaseds=False
                        )
                    )
                    for ax in (ax0, ax1, ax2):
                        ax.plot(
                            *support.exterior.xy,
                            color="yellow" if ax is not ax2 else "black",
                            linewidth=1.8,
                        )
                        ax.plot(
                            *center,
                            marker="x",
                            color="red" if ax is not ax2 else "blue",
                            markersize=7,
                        )
                        ax.set_xlim(viewport.bounds[0], viewport.bounds[2])
                        ax.set_ylim(viewport.bounds[1], viewport.bounds[3])
                        ax.set_aspect("equal")
                        ax.set_xticks([])
                        ax.set_yticks([])
                    date = evidence["acquired_utc"][:10]
                    ax0.set_title(f"{code} | Sentinel-2 {date}")
                    ax1.set_title("Aynı uydu + beyaz CORINE sınırları")
                    ax2.set_title("CORINE 2018 | aynı pencere")
                    label = ", ".join(
                        f"{c['clc_code']}: {c['fraction_of_entire_support'] * 100:.1f}%"
                        for c in row["local_context_2018"]["classes"]
                        if c["fraction_of_entire_support"] >= 0.001
                    )
                    ax2.set_xlabel(label, fontsize=9)
                    records.append(
                        {
                            "code": code,
                            "detection_id": row["detection_id"],
                            "receipt_path": evidence["receipt_path"],
                            "image_date": date,
                            "scene_item_id": evidence["item_id"],
                            "group": group,
                            "row": line,
                            "viewport_crs": str(src.crs),
                            "viewport_bounds": list(viewport.bounds),
                            "crs_roundtrip_error_m": error,
                            "quality_flags": evidence["quality_flags_present"],
                            "map_observation_date_verified": False,
                            "human_review_completed": False,
                            "habitat_admission": "undecided",
                        }
                    )
            fig.suptitle(
                "Aynı konum, farklı kaynak tarihleri | sarı/siyah: yaklaşık tespit alanı\n"
                "İnceleme amaçlı; yangın sınırı veya kabul edilmiş etiket değildir",
                fontsize=12,
            )
            fig.subplots_adjust(
                left=0.02, right=0.98, bottom=0.07, top=0.90, wspace=0.08, hspace=0.23
            )
            target = out / (group + ".png")
            fig.savefig(target, dpi=160)
            plt.close(fig)
            artifacts[target.name] = sha(target)
    for relative, expected in pins.items():
        require(sha(ROOT / relative) == expected, "Source changed during rendering")
    require(len(records) == 7 and len({r["detection_id"] for r in records}) == 5, "Review coverage")
    result = {
        "source_sha256": pins,
        "artifact_sha256": artifacts,
        "records": records,
        "image_records": 7,
        "unique_points": 5,
        "figures": 3,
        "corine_categories_interpolated": False,
        "alignment_is_ground_truth_validation": False,
        "new_researcher_reviews": 0,
        "labels_created": False,
        "final_merge_performed": False,
    }
    report = out / "readback.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(json.loads(report.read_text()) == result, "JSON readback")
    print(out.relative_to(ROOT))
    print("report_sha256", sha(report))
    print("sources", len(pins))


if __name__ == "__main__":
    main()
