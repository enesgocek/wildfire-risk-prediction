"""Screen a bounded Anamur window for repeatable post-event spectral change."""

import logging
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree

import numpy as np
import rasterio
from affine import Affine
from pyproj import Transformer
from rasterio.features import shapes
from rasterio.transform import array_bounds
from review_public_event_cover import plt, require, sha
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json
from shapely import contains_xy
from shapely.geometry import Point, shape

from wildfire_risk_prediction.imagery_review import bounded_window
from wildfire_risk_prediction.public_sentinel_windows import PublicWindows

SOURCE = BASE / "anamur_preevent_cover_v1/20261108T032025Z_2e88ca22/readback.json"
SOURCE_SHA = "ef0333fce0b9339f6559d7f4516f9f49b2f03b73c59f52a9da2b24b88b5f1c0e"
COLLECTION = "https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a/items"
SCENES = {
    "jul05": "S2A_MSIL2A_20230705T083601_R064_T36SVF_20230705T151750",
    "jul07": "S2B_MSIL2A_20230707T082609_R021_T36SVF_20230707T132649",
    "jul12": "S2A_MSIL2A_20230712T082611_R021_T36SVF_20230712T131256",
    "jul15": "S2A_MSIL2A_20230715T083601_R064_T36SVF_20230715T162048",
    "jul17": "S2B_MSIL2A_20230717T082609_R021_T36SVF_20230717T133038",
}
PAIRS = (("jul07", "jul12"), ("jul07", "jul17"), ("jul05", "jul15"))
THRESHOLDS = (0.10, 0.15, 0.20)
RADIUS = 700
EPSG = 32636


def calibration(reader, item):
    asset = item["assets"]["product-metadata"]["href"]
    response = reader.session.get(reader.sign(asset), timeout=(12, 25), allow_redirects=False)
    require(response.status_code == 200 and len(response.content) < 2_000_000, "Product metadata")
    xml = ElementTree.fromstring(response.content)
    quantum = int(xml.findtext(".//BOA_QUANTIFICATION_VALUE"))
    bands = {
        tag.attrib["physicalBand"]: tag.attrib["bandId"] for tag in xml.iter("Spectral_Information")
    }
    offsets = {tag.attrib["band_id"]: int(tag.text) for tag in xml.iter("BOA_ADD_OFFSET")}
    require(quantum > 0, "Positive quantification value")
    return {
        "sha256": sha256(response.content).hexdigest(),
        "unsigned_href": asset,
        "quantification": quantum,
        "offset": {band: offsets[bands[band]] for band in ("B8A", "B12")},
    }


def read_crop(reader, asset, bounds, band):
    href = asset["href"]
    signed = reader.sign(href)
    headers = reader.head(signed)
    resolution, channels = (10, 3) if band == "visual" else (20, 1)
    with (
        rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            GDAL_PAM_ENABLED="NO",
            GDAL_HTTP_TIMEOUT="30",
            GDAL_HTTP_CONNECTTIMEOUT="15",
            GDAL_HTTP_MAX_RETRY="0",
            CPL_DEBUG=False,
            CPL_CURL_VERBOSE=False,
            CPL_LOG="NUL",
        ),
        rasterio.open(signed) as ds,
    ):
        require(
            ds.crs.to_epsg() == EPSG
            and ds.res == (resolution, resolution)
            and ds.transform == Affine(*asset["proj:transform"])
            and ds.count == channels,
            "STAC and raster geometry",
        )
        window = bounded_window(bounds, ds.transform, ds.width, ds.height, clip_context=True)
        data = ds.read(window=window)
        valid = ds.dataset_mask(window=window) > 0
        transform = ds.window_transform(window)
        require(ds.scales == (1.0,) * channels and ds.offsets == (0.0,) * channels, "Raw samples")
    require(headers == reader.head(signed), "Unchanged remote asset")
    return data, valid, transform, {"unsigned_href": href, "headers": headers}


def acquire(reader, name, identity, bounds, folder):
    response = reader.session.get(
        f"{COLLECTION}/{identity}", timeout=(12, 25), allow_redirects=False
    )
    require(response.status_code == 200 and len(response.content) < 2_000_000, "STAC item")
    item = response.json()
    require(
        item["id"] == identity
        and item["properties"]["proj:epsg"] == EPSG
        and item["properties"]["datetime"].startswith(f"2023-07-{name[3:]}"),
        "Declared date and tile",
    )
    cal = calibration(reader, item)
    data, metadata, affine = {}, {}, {}
    bands = ("B8A", "B12", "SCL", "visual") if name in {"jul07", "jul12"} else ("B8A", "B12", "SCL")
    for band in bands:
        array, valid, affine[band], metadata[band] = read_crop(
            reader, item["assets"][band], bounds, band
        )
        data[band] = array if band == "visual" else array[0]
        data[f"{band}_valid"] = valid
    require(affine["B8A"] == affine["B12"] == affine["SCL"], "Aligned 20 m inputs")
    require(data["B8A"].shape == data["B12"].shape == data["SCL"].shape, "Common shape")
    path = folder / f"{name}.npz"
    np.savez_compressed(path, **data)
    with np.load(path, allow_pickle=False) as saved:
        require(
            all(np.array_equal(array, saved[band]) for band, array in data.items()), "Roundtrip"
        )
    return (
        data,
        affine,
        {
            "item_id": identity,
            "acquired_utc": item["properties"]["datetime"],
            "processing_baseline": item["properties"]["s2:processing_baseline"],
            "calibration": cal,
            "assets": metadata,
            "transforms": {k: list(v)[:6] for k, v in affine.items()},
            "crop_sha256": sha(path),
        },
    )


def nbr(data, cal):
    a, b = (
        (data[k].astype(np.float64) + cal["offset"][k]) / cal["quantification"]
        for k in ("B8A", "B12")
    )
    valid = (
        data["SCL_valid"]
        & data["B8A_valid"]
        & data["B12_valid"]
        & np.isin(data["SCL"], [4, 5])
        & (a >= 0)
        & (b >= 0)
        & (a + b > 0)
    )
    return np.divide(a - b, a + b, out=np.full(a.shape, np.nan), where=valid)


def describe(changes, transform, support, first_point):
    joint = support & np.isfinite(changes).all(axis=0)
    require(joint.any(), "Common clear support")
    result = {}
    for threshold in THRESHOLDS:
        mask = joint & (changes >= threshold).all(axis=0)
        patches = [
            shape(g) for g, _ in shapes(mask.astype("uint8"), mask=mask, transform=transform)
        ]
        largest = max(patches, key=lambda p: p.area) if patches else None
        result[str(threshold)] = {
            "pixels": int(mask.sum()),
            "largest_connected_m2": largest.area if largest is not None else 0,
            "distance_to_largest_m": largest.distance(first_point) if largest is not None else None,
        }
    return result, int(joint.sum())


def plot(path, crops, affine, changes, projected, support, center):
    fig, axes = plt.subplots(2, 3, figsize=(12, 8), layout="constrained")
    for ax, name in zip(axes[0, :2], ("jul07", "jul12"), strict=True):
        rgb = crops[name]["visual"]
        left, bottom, right, top = array_bounds(*rgb.shape[1:], affine[name]["visual"])
        ax.imshow(rgb.transpose(1, 2, 0), extent=(left, right, bottom, top))
        ax.set_title("7 Temmuz · Önce" if name == "jul07" else "12 Temmuz · Sonra")
    left, bottom, right, top = array_bounds(*changes.shape[1:], affine["jul07"]["SCL"])
    for ax, delta, title in zip(
        (axes[0, 2], *axes[1]),
        (*changes, np.min(changes, axis=0)),
        ("7 → 12 Temmuz", "7 → 17 Temmuz", "5 → 15 Temmuz", "Üç çiftte ortak en düşük değişim"),
        strict=True,
    ):
        image = ax.imshow(
            np.where(support, delta, np.nan),
            cmap="RdBu_r",
            vmin=-0.4,
            vmax=0.4,
            extent=(left, right, bottom, top),
        )
        ax.set_title(title)
    for ax in axes.flat:
        ax.scatter(
            [p.x for p in projected],
            [p.y for p in projected],
            facecolors="none",
            edgecolors="#ffe232" if ax in axes[0, :2] else "#181818",
            s=23,
        )
        ax.set(
            xlim=(center.x - RADIUS, center.x + RADIUS), ylim=(center.y - RADIUS, center.y + RADIUS)
        )
        ax.set_axis_off()
    fig.colorbar(image, ax=axes.ravel().tolist(), shrink=0.7, label="dNBR")
    fig.suptitle("Anamur | Olay sonrası spektral değişim · Halkalar VIIRS merkezleri")
    fig.savefig(path, dpi=145)
    plt.close(fig)


def main():
    logging.getLogger("rasterio").disabled = True
    logging.getLogger("urllib3").disabled = True
    require(sha(SOURCE) == SOURCE_SHA, "Frozen pre-event evidence")
    before = read_json(SOURCE)
    project = Transformer.from_crs(4326, EPSG, always_xy=True)
    projected = [
        Point(*project.transform(*before["points"][f"tespit_{i}"]["lon_lat"])) for i in range(1, 6)
    ]
    center = projected[0]
    circle = center.buffer(RADIUS)
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "anamur_burn_signal_v1" / run
    out.mkdir(parents=True, exist_ok=False)
    crops, affines, scenes = {}, {}, {}
    reader = PublicWindows()
    try:
        for name, identity in SCENES.items():
            crops[name], affines[name], scenes[name] = acquire(
                reader, name, identity, circle.bounds, out
            )
            print(name, "read", flush=True)
    except Exception as exc:
        print("Acquisition incomplete", type(exc).__name__, flush=True)
        raise SystemExit(1) from None
    finally:
        reader.close()
    affine = affines["jul07"]["SCL"]
    index = {name: nbr(data, scenes[name]["calibration"]) for name, data in crops.items()}
    require(
        all(
            affines[name]["SCL"] == affine and n.shape == index["jul07"].shape
            for name, n in index.items()
        ),
        "Identical comparison grids",
    )
    changes = np.stack([index[a] - index[b] for a, b in PAIRS])
    rows, cols = np.indices(changes.shape[1:])
    x, y = affine * (cols + 0.5, rows + 0.5)
    support = contains_xy(circle, x, y)
    thresholds, common_pixels = describe(changes, affine, support, center)
    path = out / "change_review.png"
    plot(path, crops, affines, changes, projected, support, center)
    report = {
        "pre_event_receipt_sha256": SOURCE_SHA,
        "producer_sha256": sha(Path(__file__)),
        "scenes": scenes,
        "pairs": [list(pair) for pair in PAIRS],
        "radius_m": RADIUS,
        "support_pixels": int(support.sum()),
        "common_clear_pixels": common_pixels,
        "all_pair_threshold_diagnostics": thresholds,
        "image_sha256": sha(path),
        "target": None,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "original_ignition_verified": False,
    }
    receipt = out / "readback.json"
    write_json(receipt, report)
    print(receipt.relative_to(ROOT).as_posix(), sha(receipt))


if __name__ == "__main__":
    main()
