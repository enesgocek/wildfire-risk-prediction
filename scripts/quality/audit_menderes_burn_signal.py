"""Compare local Sentinel-2 change around the two July 2023 Menderes groups."""

import csv
import logging
import math
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import rasterio
from affine import Affine
from pyproj import Transformer
from rasterio.features import shapes
from rasterio.transform import array_bounds
from rasterio.windows import Window, from_bounds
from review_anamur_burn_signal import COLLECTION, THRESHOLDS, calibration, nbr
from review_manavgat_reported_starts import CATALOG
from review_public_event_cover import plt, require, sha
from review_three_province_start_context import CATALOG_SHA
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json
from shapely import contains_xy
from shapely.geometry import Point, box, shape
from shapely.ops import unary_union

from wildfire_risk_prediction.event_review import GEOD
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows

PRIOR = BASE / "menderes_hona_context_v1/20261108T035543Z_f2cfcec3/readback.json"
PRIOR_SHA = "05b59ebb981cce0f367df145f3a663f54f627662ab407124a506dcfc42e28b92"
SCENES = {
    "01": "S2A_MSIL2A_20230701T085601_R007_T35SNC_20230701T161701",
    "06": "S2B_MSIL2A_20230706T085559_R007_T35SNC_20230706T133640",
    "11": "S2A_MSIL2A_20230711T085601_R007_T35SNC_20230711T152256",
    "16": "S2B_MSIL2A_20230716T085559_R007_T35SNC_20230716T130732",
    "21": "S2A_MSIL2A_20230721T085601_R007_T35SNC_20230721T152015",
}
PAIRS = (("01", "11"), ("06", "16"), ("01", "21"))
RADIUS = 700
CONTEXT_MARGIN = 750
EPSG = 32635


def points(prior):
    """Reconstruct the previously reviewed 12 and 2 selected centres."""
    source = ROOT / CATALOG
    require(sha(source) == CATALOG_SHA, "Frozen VIIRS catalogue")
    groups = {"south": [], "north": []}
    project = Transformer.from_crs(4326, EPSG, always_xy=True)
    start = datetime(2023, 7, 10, 11, tzinfo=UTC)
    end = datetime(2023, 7, 11, tzinfo=UTC)
    with source.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            utc = row["detection_timestamp_utc"]
            if not utc.startswith(("2023-07-10", "2023-07-11")) or not (
                start <= datetime.fromisoformat(utc) <= end
            ):
                continue
            lon, lat = float(row["longitude"]), float(row["latitude"])
            if GEOD.inv(27.224579, 38.239681, lon, lat)[2] <= 5000:
                grid = row["grid_id"]
                require(grid in prior["selected_rows_by_grid"], "Reviewed cell")
                key = "north" if grid.endswith("C525_R906") else "south"
                groups[key].append(Point(*project.transform(lon, lat)))
    require(
        {key: len(value) for key, value in groups.items()} == {"south": 12, "north": 2},
        "14 selected points",
    )
    return groups


def crop(reader, asset, bounds, band):
    href = asset["href"]
    url = reader.sign(href)
    headers = reader.head(url)
    resolution, channels = (10, 3) if band == "visual" else (20, 1)
    with (
        rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            GDAL_HTTP_TIMEOUT="30",
            GDAL_HTTP_CONNECTTIMEOUT="15",
            GDAL_HTTP_MAX_RETRY="0",
            CPL_DEBUG=False,
            CPL_CURL_VERBOSE=False,
            CPL_LOG="NUL",
        ),
        rasterio.open(url) as ds,
    ):
        require(
            ds.crs.to_epsg() == EPSG
            and ds.res == (resolution, resolution)
            and ds.count == channels
            and ds.transform == Affine(*asset["proj:transform"])
            and ds.scales == (1.0,) * channels
            and ds.offsets == (0.0,) * channels,
            "Native crop geometry and encoding",
        )
        left, bottom, right, top = bounds
        require(max(right - left, top - bottom) <= 8500, "Bounded two-group crop")
        requested = from_bounds(left, bottom, right, top, ds.transform)
        c0, r0 = math.floor(requested.col_off), math.floor(requested.row_off)
        c1 = math.ceil(requested.col_off + requested.width)
        r1 = math.ceil(requested.row_off + requested.height)
        require(0 <= c0 < c1 <= ds.width and 0 <= r0 < r1 <= ds.height, "Crop within tile")
        window = Window(c0, r0, c1 - c0, r1 - r0)
        array = ds.read(window=window)
        valid = ds.dataset_mask(window=window) > 0
        affine = ds.window_transform(window)
    require(headers == reader.head(url), "Asset identity unchanged")
    return (
        array if band == "visual" else array[0],
        valid,
        affine,
        {"unsigned_href": href, "headers": headers},
    )


def acquire(reader, day, item_id, bounds, out):
    response = reader.session.get(
        f"{COLLECTION}/{item_id}", timeout=(12, 25), allow_redirects=False
    )
    require(response.status_code == 200 and len(response.content) < 2_000_000, "Scene metadata")
    item = response.json()
    properties = item["properties"]
    require(
        item["id"] == item_id
        and properties["datetime"].startswith(f"2023-07-{day}")
        and properties["proj:epsg"] == EPSG
        and properties["sat:relative_orbit"] == 7,
        "Pinned scene identity",
    )
    cal = calibration(reader, item)
    data, transforms, provenance = {}, {}, {}
    bands = ("B8A", "B12", "SCL", "visual") if day in ("01", "11") else ("B8A", "B12", "SCL")
    for band in bands:
        data[band], data[f"{band}_valid"], transforms[band], provenance[band] = crop(
            reader, item["assets"][band], bounds, band
        )
    require(transforms["B8A"] == transforms["B12"] == transforms["SCL"], "Common 20 m geometry")
    path = out / f"jul{day}.npz"
    np.savez_compressed(path, **data)
    with np.load(path, allow_pickle=False) as saved:
        require(
            all(np.array_equal(saved[key], value) for key, value in data.items()), "Crop roundtrip"
        )
    return (
        data,
        transforms,
        {
            "id": item_id,
            "utc": properties["datetime"],
            "baseline": properties["s2:processing_baseline"],
            "calibration": cal,
            "assets": provenance,
            "transforms": {key: list(affine)[:6] for key, affine in transforms.items()},
            "crop_sha256": sha(path),
        },
    )


def compare(common, minimum, control, masks, affine, groups, supports):
    edge = box(*array_bounds(*common.shape, affine)).boundary
    result = {}
    for threshold in THRESHOLDS:
        mask = common & (minimum >= threshold)
        patches = [shape(g) for g, _ in shapes(mask.astype("uint8"), mask=mask, transform=affine)]
        largest = max(patches, key=lambda p: p.area) if patches else None
        result[str(threshold)] = {
            "largest_patch_ha": largest.area / 10_000 if largest is not None else 0,
            "largest_patch_touches_crop_edge": largest.intersects(edge)
            if largest is not None
            else False,
            "largest_patch_distance_to_centres_m": {
                name: [largest.distance(point) if largest is not None else None for point in points]
                for name, points in groups.items()
            },
            "patches_intersecting_both_supports": sum(
                all(p.intersects(support) for support in supports.values()) for p in patches
            ),
            "local_counts": {
                name: {
                    "post_change_pixels": int((mask & local).sum()),
                    "before_control_pixels": int((common & local & (control >= threshold)).sum()),
                    "largest_patch_inside_support_ha": max(
                        (p.intersection(supports[name]).area / 10_000 for p in patches), default=0
                    ),
                }
                for name, local in masks.items()
            },
        }
    return result


def plot(path, arrays, transforms, affine, delta, groups, supports):
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), layout="constrained")
    for ax, day in zip(axes[:2], ("01", "11"), strict=True):
        rgb = arrays[day]["visual"]
        left, bottom, right, top = array_bounds(*rgb.shape[1:], transforms[day]["visual"])
        ax.imshow(rgb.transpose(1, 2, 0), extent=(left, right, bottom, top))
        ax.set_title(f"{int(day)} Temmuz 2023")
    west, south, east, north = array_bounds(*delta.shape, affine)
    view = axes[2].imshow(
        delta, extent=(west, east, south, north), cmap="RdBu_r", vmin=-0.35, vmax=0.35
    )
    axes[2].set_title("Üç karşılaştırmada en düşük dNBR")
    for ax in axes:
        for name, color in (("south", "#ffd739"), ("north", "#67e9ff")):
            for point in groups[name]:
                ax.scatter(point.x, point.y, s=14, facecolors="none", edgecolors=color)
            ax.plot(*supports[name].exterior.xy, color=color, lw=0.8)
        ax.set(xlim=(west, east), ylim=(south, north))
        ax.set_axis_off()
    fig.colorbar(view, ax=axes[2], shrink=0.72, label="dNBR")
    fig.suptitle("Menderes Hona Boğazı | Güney ve kuzey VIIRS çevreleri")
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    require(sha(PRIOR) == PRIOR_SHA, "Frozen Menderes context")
    groups = points(read_json(PRIOR))
    supports = {
        name: unary_union([p.buffer(RADIUS) for p in points]) for name, points in groups.items()
    }
    bounds = unary_union(list(supports.values())).buffer(CONTEXT_MARGIN).bounds
    out = (
        BASE
        / "menderes_burn_signal_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    arrays, transforms, scenes = {}, {}, {}
    reader = PublicWindows()
    try:
        for day, identity in SCENES.items():
            arrays[day], transforms[day], scenes[day] = acquire(reader, day, identity, bounds, out)
            print(f"July {day} acquired", flush=True)
    except Exception as exc:
        print("Acquisition incomplete", type(exc).__name__, flush=True)
        raise SystemExit(1) from None
    finally:
        reader.close()

    affine = transforms["01"]["SCL"]
    index = {day: nbr(data, scenes[day]["calibration"]) for day, data in arrays.items()}
    require(
        all(
            transforms[day]["SCL"] == affine and value.shape == index["01"].shape
            for day, value in index.items()
        ),
        "Aligned observation grid",
    )
    changes = np.stack([index[before] - index[after] for before, after in PAIRS])
    control = index["01"] - index["06"]
    common = np.isfinite(changes).all(axis=0) & np.isfinite(control)
    minimum = np.min(changes, axis=0)
    rows, cols = np.indices(common.shape)
    x, y = affine * (cols + 0.5, rows + 0.5)
    masks = {name: contains_xy(support, x, y) for name, support in supports.items()}
    require(
        all((common & mask).any() for mask in masks.values()),
        "Usable optical observations in both supports",
    )
    image = out / "change_review.png"
    plot(image, arrays, transforms, affine, minimum, groups, supports)
    result = {
        "prior_sha256": PRIOR_SHA,
        "catalogue_sha256": CATALOG_SHA,
        "producer_sha256": sha(Path(__file__)),
        "scenes": scenes,
        "pairs": [list(pair) for pair in PAIRS],
        "before_control_pair": ["01", "06"],
        "radius_m": RADIUS,
        "context_margin_m": CONTEXT_MARGIN,
        "local_coverage": {
            name: {
                "pixels": int(mask.sum()),
                "common_clear_pixels": int((common & mask).sum()),
                "usable_by_scene": {
                    day: int((np.isfinite(value) & mask).sum()) for day, value in index.items()
                },
            }
            for name, mask in masks.items()
        },
        "thresholds": compare(common, minimum, control, masks, affine, groups, supports),
        "image_sha256": sha(image),
        "target": None,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
    }
    receipt = out / "readback.json"
    write_json(receipt, result)
    print(receipt.relative_to(ROOT).as_posix(), sha(receipt))


if __name__ == "__main__":
    main()
