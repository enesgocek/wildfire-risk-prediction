"""Overlay reviewed Menderes change patches with historical cover and local boundaries."""

from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET

import numpy as np
import rasterio
from affine import Affine
from audit_izmir_dispatch_coverage import INPUTS, WORKBOOK, workbook_records
from audit_menderes_burn_signal import CATALOG, CATALOG_SHA, EPSG, PRIOR, PRIOR_SHA, RADIUS, points
from measure_corine_review_supports import DELIVERY, DELIVERY_SHA, class_areas
from pyproj import Transformer
from rasterio.features import shapes
from rasterio.transform import array_bounds
from review_anamur_burn_signal import nbr
from review_public_event_cover import plt, require, sha
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json
from shapely import segmentize
from shapely.geometry import Polygon, shape
from shapely.ops import transform, unary_union

from wildfire_risk_prediction.perimeter_review import effis_gml

OPTICAL = BASE / "menderes_burn_signal_v1/20261108T041302Z_38822be1/readback.json"
OUT = BASE / "menderes_patch_context_v1"
SOURCES = OUT / "sources"
BOUNDARIES = {
    SOURCES / "mahalle_envelope.json": (
        "fda468cdc2a8b567a2d32dbd045fb501d73785ed95cf2397b44b94f15b97c687"
    ),
    SOURCES / "mahalle_kuner.json": (
        "0e3892a9ad7bf429754e0f03fe3a083365efb5faa23f1ec177e04ec27142dc63"
    ),
}
EFFIS_HITS = SOURCES / "effis_2023_menderes_hits.gml"
EFFIS_RESULTS = SOURCES / "effis_2023_menderes_results.gml"
PINS = {
    OPTICAL: "1cf41777f35c229aff52194e326b7541ef75253fb79c00145ca57f894ce290df",
    PRIOR: PRIOR_SHA,
    DELIVERY: DELIVERY_SHA,
    WORKBOOK: INPUTS[WORKBOOK],
    EFFIS_HITS: "bff769ad4d280a65b368a72f969e6820cb25a851fd2e7fd04ba8f8228b8e6eda",
    EFFIS_RESULTS: "75b69ea5c2daba0ca61e3917ff08363abe6ec279c86a4df3b5cd2ba950dbc6bd",
    **BOUNDARIES,
}


def load_boundaries():
    project = Transformer.from_crs(4326, EPSG, always_xy=True).transform
    boundaries = {}
    for path in BOUNDARIES:
        payload = read_json(path)
        require(
            payload["spatialReference"]["wkid"] == 4326
            and payload["geometryType"] == "esriGeometryPolygon"
            and not payload.get("exceededTransferLimit"),
            "Complete municipal polygons in WGS84",
        )
        for feature in payload["features"]:
            attrs = feature["attributes"]
            (ring,) = feature["geometry"]["rings"]
            polygon = transform(project, Polygon(ring))
            key = (attrs["OBJECTID"], attrs["ADINUMARASI"])
            require(polygon.is_valid and polygon.area > 0 and key not in boundaries, "Boundary")
            boundaries[key] = polygon
    require(len(boundaries) == 25, "Expected boundary count")
    return boundaries


def plot(path, images, scenes, region, patch, centres):
    left, bottom, right, top = region.bounds
    fig, axes = plt.subplots(1, 2, figsize=(10, 5), layout="constrained")
    for ax, day in zip(axes, ("01", "11"), strict=True):
        rgb = images[day]
        affine = Affine(*scenes[day]["transforms"]["visual"])
        west, south, east, north = array_bounds(*rgb.shape[1:], affine)
        ax.imshow(rgb.transpose(1, 2, 0), extent=(west, east, south, north))
        for polygon in patch.geoms if patch.geom_type == "MultiPolygon" else [patch]:
            ax.plot(*polygon.exterior.xy, color="#ffdc36", linewidth=1.2)
        ax.scatter(
            [point.x for point in centres],
            [point.y for point in centres],
            facecolors="none",
            edgecolors="#6de7ff",
            s=46,
        )
        ax.set(xlim=(left, right), ylim=(bottom, top), title=f"{int(day)} Temmuz 2023")
        ax.set_axis_off()
    fig.suptitle("Menderes kuzeyi | Sarı: dNBR ≥ 0,15 parçası · Mavi: VIIRS merkezleri")
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    require(all(sha(path) == value for path, value in PINS.items()), "Frozen sources")
    optical, delivery = read_json(OPTICAL), read_json(DELIVERY)
    require(optical["target"] is None and optical["radius_m"] == RADIUS, "Review context")
    raster = next(rel for rel in delivery["source_sha256"] if rel.endswith(".tif"))
    pins = {path.relative_to(ROOT).as_posix(): value for path, value in PINS.items()}
    pins[CATALOG] = CATALOG_SHA  # Verified by points().
    pins[raster] = delivery["source_sha256"][raster]
    require(sha(ROOT / raster) == pins[raster], "Frozen CORINE raster")

    scenes = optical["scenes"]
    index, images = {}, {}
    affine = Affine(*scenes["01"]["transforms"]["SCL"])
    for day, scene in scenes.items():
        path = OPTICAL.with_name(f"jul{day}.npz")
        require(sha(path) == scene["crop_sha256"], "Frozen crop")
        pins[path.relative_to(ROOT).as_posix()] = scene["crop_sha256"]
        with np.load(path, allow_pickle=False) as source:
            require(Affine(*scene["transforms"]["SCL"]) == affine, "Aligned grid")
            index[day] = nbr(source, scene["calibration"])
            if day in ("01", "11"):
                images[day] = source["visual"]
    minimum = np.min([index[a] - index[b] for a, b in optical["pairs"]], axis=0)
    a, b = optical["before_control_pair"]
    common = np.isfinite(minimum) & np.isfinite(index[a] - index[b])
    centres = points(read_json(PRIOR))
    supports = {name: unary_union([p.buffer(RADIUS) for p in ps]) for name, ps in centres.items()}
    boundaries = load_boundaries()
    hits = ET.fromstring(EFFIS_HITS.read_bytes())
    refs = effis_gml(EFFIS_RESULTS.read_bytes(), fire_date_window=("2023-07-09", "2023-07-13"))
    require(
        hits.tag == "{http://www.opengis.net/wfs}FeatureCollection"
        and hits.get("numberOfFeatures") == "1"
        and refs.reference_id.tolist() == ["217014"]
        and refs.geometry_valid.all(),
        "Complete valid EFFIS result",
    )
    reference = refs.to_crs(EPSG).iloc[0]
    perimeter = reference.geometry

    def admin_context(geometry):
        return [
            {"id": oid, "name": name, "patch_area_fraction": overlap / geometry.area}
            for (oid, name), polygon in boundaries.items()
            if (overlap := geometry.intersection(polygon).area) > 0
        ]

    overlaps, north_patch = {}, None
    with rasterio.open(ROOT / raster) as ds:
        require(ds.crs.to_wkt() == delivery["raster"]["wkt"], "CORINE projection")
        project = Transformer.from_crs(EPSG, ds.crs, always_xy=True).transform
        for threshold, reviewed in optical["thresholds"].items():
            mask = common & (minimum >= float(threshold))
            polygons = [
                shape(g) for g, _ in shapes(mask.astype("uint8"), mask=mask, transform=affine)
            ]
            overlaps[threshold] = {}
            for group, support in supports.items():
                patch = max(
                    (polygon.intersection(support) for polygon in polygons), key=lambda p: p.area
                )
                expected = reviewed["local_counts"][group]["largest_patch_inside_support_ha"]
                require(abs(patch.area / 10_000 - expected) < 1e-8, "Reproduced optical patch")
                equal_area = transform(project, segmentize(patch, 10))
                cover = {}
                for value, area in class_areas(ds, equal_area).items():
                    code = (
                        str(delivery["legend"][str(value)]["clc_code"])
                        if 1 <= value <= 44
                        else "unmapped"
                    )
                    cover[code] = cover.get(code, 0) + area / equal_area.area
                overlaps[threshold][group] = {
                    "patch_ha_utm": expected,
                    "clc_2018_area_fractions": cover,
                    "municipal_boundaries": admin_context(patch),
                    "distance_from_centres_m": [patch.distance(p) for p in centres[group]],
                    "kuner_boundary_distance_m": patch.distance(boundaries[(36884, "KÜNER")]),
                    "effis_intersection_ha": patch.intersection(perimeter).area / 10_000,
                    "effis_distance_m": patch.distance(perimeter),
                }
                if threshold == "0.15" and group == "north":
                    north_patch = patch

    dispatch = workbook_records()
    require(len(dispatch) == 12986, "Annual municipal workbook")
    event_day = date(2023, 7, 10)
    municipal = {
        district: dict(
            Counter(category for day, category, d in dispatch if day == event_day and d == district)
        )
        for district in ("MENDERES", "TORBALI")
    }
    out = OUT / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    image = out / "north_patch_review.png"
    plot(image, images, scenes, supports["north"], north_patch, centres["north"])
    receipt = out / "readback.json"
    write_json(
        receipt,
        {
            "inputs_sha256": pins,
            "producer_sha256": sha(Path(__file__)),
            "patches": overlaps,
            "effis": {
                "id": reference.reference_id,
                "reported_area_ha": float(reference.AREA_HA),
                "source_firedate": reference.FIREDATE,
                "source_finaldate": reference.FINALDATE,
                "group_centres_covered": {
                    group: sum(perimeter.covers(point) for point in ps)
                    for group, ps in centres.items()
                },
                "min_group_centre_distance_m": {
                    group: min(perimeter.distance(point) for point in ps)
                    for group, ps in centres.items()
                },
            },
            "centre_boundaries": {
                group: [
                    [name for (_, name), polygon in boundaries.items() if polygon.covers(point)]
                    for point in ps
                ]
                for group, ps in centres.items()
            },
            "municipal_dispatch_by_category_2023_07_10": municipal,
            "figure_sha256": sha(image),
            "target": None,
            "daily_observation_status": "unknown",
            "positive_label_permitted": False,
            "negative_label_permitted": False,
        },
    )
    print(receipt.relative_to(ROOT).as_posix(), sha(receipt))


if __name__ == "__main__":
    main()
