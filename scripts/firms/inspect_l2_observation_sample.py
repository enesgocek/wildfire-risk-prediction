"""Local training-sample audit of VIIRS swath arrays; does not produce labels.

Use HDF5 for all arrays to retain native line/sample order. Pixel-center counts
are diagnostics, not surface areas or daily observation coverage.
"""

import argparse
import hashlib
import json
import re
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Transformer
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/reports/observation_coverage"
SAMPLE = ROOT / "data/raw/firms_observation/sample_2019014_1018"
PRODUCTS = {
    "VNP14IMG": ("SNPP", "fire", "002", {"002"}),
    "VNP03IMG": ("SNPP", "geolocation", "002", {"2", "002"}),
    "VJ114IMG": ("N20", "fire", "002", {"002"}),
    "VJ103IMG": ("N20", "geolocation", "021", {"2.1", "021"}),
}
GUIDE = (
    "https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/"
    "Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf"
)
CLASSES = (
    "not_processed",
    "bowtie_deleted",
    "sun_glint",
    "water",
    "cloud",
    "land",
    "unclassified",
    "low_confidence_fire",
    "nominal_confidence_fire",
    "high_confidence_fire",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path, algorithm="sha256"):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def product_identity(filename):
    match = re.fullmatch(
        r"(VNP14IMG|VNP03IMG|VJ114IMG|VJ103IMG)\.A(\d{7})\.(\d{4})"
        r"\.(\d{3})\.\d{13}\.nc",
        filename,
    )
    require(match is not None, "Expected supported VIIRS sample filename")
    sensor, role, version, _ = PRODUCTS[match[1]]
    require(match[4] == version, "Unexpected product version")
    stamp = datetime.strptime(match[2] + match[3], "%Y%j%H%M").replace(tzinfo=UTC)
    require(stamp.strftime("%Y%j%H%M") == match[2] + match[3], "Invalid day-of-year")
    require(2018 <= stamp.year <= 2023, "Only training sample files may be opened")
    return sensor, role, match[2] + "." + match[3], stamp


def training_key(filename):
    _, _, key, stamp = product_identity(filename)
    return key, stamp


def sample_stem(sensor, key):
    require(sensor in {"SNPP", "N20"}, "Unsupported sensor")
    return f"l2_sample_{key}" if sensor == "SNPP" else f"l2_sample_N20_{key}"


def validate_pair(fire, geo, fire_tags, geo_tags):
    sensor, role, fire_key, stamp = product_identity(fire.name)
    geo_sensor, geo_role, geo_key, _ = product_identity(geo.name)
    require(sensor == geo_sensor, "Sensor mismatch")
    require(role == "fire" and geo_role == "geolocation", "Product roles reversed")
    require(fire_key == geo_key, "Granule time mismatch")
    fire_product, geo_product = fire.name.split(".")[0], geo.name.split(".")[0]
    require(fire_tags.get("ShortName") == fire_product, "Wrong fire product")
    require(geo_tags.get("ShortName") == geo_product, "Wrong geolocation product")
    # Some processing versions retain the shared VNP03IMG attribute name.
    declared = [fire_tags[k] for k in {geo_product, "VNP03IMG"} if k in fire_tags]
    pointers = [
        p.replace("\\", "/").rsplit("/", 1)[-1]
        for p in re.split(r"[,\s]+", fire_tags.get("InputPointer", ""))
    ]
    require(
        all(v == geo.name for v in declared) if declared else geo.name in pointers,
        "Not the actual geolocation input",
    )
    require(geo_tags.get("LocalGranuleID") == geo.name, "Geolocation identity mismatch")
    for field in ("StartTime", "EndTime"):
        require(fire_tags[field] == geo_tags[field], "Acquisition interval mismatch")
    start = datetime.strptime(fire_tags["StartTime"], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=UTC)
    end = datetime.strptime(fire_tags["EndTime"], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=UTC)
    require(start == stamp and (end - start).total_seconds() == 360, "Unexpected swath interval")
    return fire_key


def verify_cmr(path, metadata_path, short_name):
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    require(metadata["CollectionReference"]["ShortName"] == short_name, "CMR product mismatch")
    require(
        metadata["CollectionReference"]["Version"] in PRODUCTS[short_name][3],
        "CMR collection version mismatch",
    )
    require(
        any(u["URL"].endswith("/" + path.name) for u in metadata["RelatedUrls"]),
        "CMR download identity mismatch",
    )
    archive = metadata["DataGranule"]["ArchiveAndDistributionInformation"]
    require(len(archive) == 1, "Ambiguous CMR archive entry")
    entry = archive[0]
    expected = entry.get("SizeInBytes")
    if expected is None:
        require(entry["SizeUnit"] == "MB", "Unsupported CMR size unit")
        # These CMR sample entries report binary MB; retain original metadata.
        expected = round(entry["Size"] * 1024**2)
    require(path.stat().st_size == expected, "CMR file size mismatch")
    checksum = entry.get("Checksum")
    if checksum:
        actual = digest(path, checksum["Algorithm"].lower())
        require(actual.lower() == checksum["Value"].lower(), "CMR checksum mismatch")
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
        "cmr_metadata_sha256": digest(metadata_path),
        "cmr_checksum_verified": bool(checksum),
        "cmr_checksum": checksum,
        "cmr_interval": metadata["TemporalExtent"]["RangeDateTime"],
    }


def pilot_selection(lon, lat, aoi):
    valid = np.isfinite(lon) & np.isfinite(lat) & (abs(lon) <= 180) & (abs(lat) <= 90)
    west, south, east, north = aoi.bounds
    bbox = valid & (lon >= west) & (lon <= east) & (lat >= south) & (lat <= north)
    inside = np.zeros(lon.shape, dtype=bool)
    inside[bbox] = shapely.covers(aoi, shapely.points(lon[bbox], lat[bbox]))
    return valid, bbox, inside


def input_quality_flags(qa):
    # Fire-test bits are not input-quality failures. Bit 22 flags residual bowtie.
    return (qa & 127) != 0, (qa & (1 << 5)) != 0, (qa & (1 << 22)) != 0


def diagnostic_land(mask, qa):
    bad, _, residual = input_quality_flags(qa)
    # Single-pass diagnostic, never an eligibility or daily-negative rule.
    return (mask == 5) & ~bad & ~residual


def layer(stack, path, name):
    return stack.enter_context(rasterio.open(f'HDF5:"{path.as_posix()}"://{name}'))


def read_sparse(stack, fire, count):
    names = ("FP_line", "FP_sample", "FP_latitude", "FP_longitude", "FP_confidence")
    require(count >= 0, "Invalid FirePix count")
    # Empty sparse datasets are valid when the entire swath has no detections.
    return {n: layer(stack, fire, n).read(1).ravel() if count else np.array([]) for n in names}


def inspect(sample_directory, fire_metadata, geo_metadata):
    sample_directory = sample_directory.resolve()
    fire_metadata, geo_metadata = fire_metadata.resolve(), geo_metadata.resolve()
    files = [(p, product_identity(p.name)) for p in sample_directory.glob("*.nc")]
    fires = [p for p, identity in files if identity[1] == "fire"]
    geos = [p for p, identity in files if identity[1] == "geolocation"]
    require(len(fires) == len(geos) == 1, "Sample folder must contain exactly one pair")
    fire, geo = fires[0], geos[0]
    training_key(fire.name)
    training_key(geo.name)  # Guard before opening satellite arrays.
    sensor = product_identity(fire.name)[0]
    require(sensor == product_identity(geo.name)[0], "Sensor mismatch")
    sources = {
        "fire": verify_cmr(fire, fire_metadata, fire.name.split(".")[0]),
        "geolocation": verify_cmr(geo, geo_metadata, geo.name.split(".")[0]),
    }
    aoi_path, grid_path = ROOT / "data/aoi/aoi.geojson", ROOT / "data/aoi/grid_5km.geojson"
    aoi = gpd.read_file(aoi_path).to_crs(4326).geometry.union_all()
    # Index exact boundaries once; no simplification of the 88k-vertex pilot.
    shapely.prepare(aoi)
    grid = gpd.read_file(grid_path)
    counts = pd.DataFrame(
        0,
        index=grid.grid_id,
        columns=list(CLASSES)
        + [
            "input_non_nominal",
            "geo_non_nominal",
            "residual_bowtie",
            "land_nominal_input_no_residual",
        ],
        dtype="int64",
    )
    transformer = Transformer.from_crs(4326, 6933, always_xy=True)
    hist = np.zeros(10, dtype="int64")
    pilot_class_qa = np.zeros((10, 3), dtype="int64")
    totals = {"invalid_coordinates": 0, "bbox_centers": 0, "pilot_centers": 0}
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask = layer(stack, fire, "fire_mask")
        qa = layer(stack, fire, "algorithm_QA")
        latds = layer(stack, geo, "geolocation_data/latitude")
        londs = layer(stack, geo, "geolocation_data/longitude")
        tags, geo_tags = mask.tags(), latds.tags()
        key = validate_pair(fire, geo, tags, geo_tags)
        require(mask.shape == qa.shape == latds.shape == londs.shape, "Swath shape mismatch")
        require(mask.dtypes == ("uint8",) and qa.dtypes == ("uint32",), "Unexpected mask/QA type")
        for name, source in sources.items():
            cmr = source["cmr_interval"]
            for local_field, cmr_field in [
                ("StartTime", "BeginningDateTime"),
                ("EndTime", "EndingDateTime"),
            ]:
                local = datetime.strptime(tags[local_field], "%Y-%m-%d %H:%M:%S.%f")
                require(
                    local == datetime.fromisoformat(cmr[cmr_field].replace("Z", "")),
                    f"{name} CMR acquisition time mismatch",
                )
        # Independent sparse fire coordinates prove native line/sample orientation.
        sparse = read_sparse(stack, fire, int(tags["FirePix"]))
        require(
            all(len(v) == int(tags["FirePix"]) for v in sparse.values()), "Sparse count mismatch"
        )
        for i, (row, col) in enumerate(zip(sparse["FP_line"], sparse["FP_sample"], strict=True)):
            require(row < mask.height and col < mask.width, "Sparse index outside swath")
            window = Window(int(col), int(row), 1, 1)
            require(
                mask.read(1, window=window).item() == sparse["FP_confidence"][i],
                "Sparse fire class/orientation mismatch",
            )
            for ds, field in [(latds, "FP_latitude"), (londs, "FP_longitude")]:
                require(
                    abs(ds.read(1, window=window).item() - sparse[field][i]) <= 1e-5,
                    "Sparse coordinate/orientation mismatch",
                )
        for row in range(0, mask.height, 256):
            window = Window(0, row, mask.width, min(256, mask.height - row))
            values = mask.read(1, window=window)
            require(values.max() < 10, "Unexpected fire-mask class")
            hist += np.bincount(values.ravel(), minlength=10)
            lon, lat = londs.read(1, window=window), latds.read(1, window=window)
            valid, bbox, inside = pilot_selection(lon, lat, aoi)
            totals["invalid_coordinates"] += int((~valid).sum())
            totals["bbox_centers"] += int(bbox.sum())
            totals["pilot_centers"] += int(inside.sum())
            if not inside.any():
                continue
            quality = qa.read(1, window=window)[inside]
            bad, geo_bad, residual = input_quality_flags(quality)
            for label in range(10):
                selected = values[inside] == label
                pilot_class_qa[label] += [
                    int(flag[selected].sum()) for flag in (bad, geo_bad, residual)
                ]
            x, y = transformer.transform(lon[inside], lat[inside])
            ids = [
                f"E6933_5K_V1_C{c}_R{r}"
                for c, r in zip(
                    np.floor(x / 5000).astype(int),
                    np.floor(y / 5000).astype(int),
                    strict=True,
                )
            ]
            require(set(ids) <= set(counts.index), "Pixel center outside registered grid")
            frame = pd.DataFrame(
                {
                    "grid_id": ids,
                    "class": values[inside],
                    "input_non_nominal": bad,
                    "geo_non_nominal": geo_bad,
                    "residual_bowtie": residual,
                    "land_nominal_input_no_residual": diagnostic_land(values[inside], quality),
                }
            )
            for label, subset in frame.groupby("class"):
                grouped = subset.groupby("grid_id").size()
                counts.loc[grouped.index, CLASSES[int(label)]] += grouped
            flags = frame.groupby("grid_id")[
                [
                    "input_non_nominal",
                    "geo_non_nominal",
                    "residual_bowtie",
                    "land_nominal_input_no_residual",
                ]
            ].sum()
            counts.loc[flags.index, flags.columns] += flags
        require(hist.sum() == mask.height * mask.width, "Class counts do not reconcile")
        require(hist[7:].sum() == int(tags["FirePix"]), "Fire-mask/sparse count mismatch")
        require(
            int(counts[list(CLASSES)].to_numpy().sum()) == totals["pilot_centers"],
            "Grid counts do not reconcile",
        )
        shape = list(mask.shape)
        day_night_flag = tags.get("DayNightFlag")
    # Ensure files did not change during reading, and preserve all zero-center cells.
    for path, source in [(fire, sources["fire"]), (geo, sources["geolocation"])]:
        require(digest(path) == source["sha256"], "Sample changed during inspection")
    counts["pixel_center_count"] = counts[list(CLASSES)].sum(axis=1)
    counts["daily_observation_status"] = "unknown"
    counts["negative_label_permitted"] = False
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "pair_key": key,
        "status": "sample_verified_daily_coverage_unresolved",
        "sensor": sensor,
        "sample_id": f"{sensor}:{key}",
        "day_night_flag": day_night_flag,
        "start_utc": sources["fire"]["cmr_interval"]["BeginningDateTime"],
        "end_utc": sources["fire"]["cmr_interval"]["EndingDateTime"],
        "shape": shape,
        "sources": sources,
        "script_sha256": digest(Path(__file__)),
        "aoi_sha256": digest(aoi_path),
        "grid_sha256": digest(grid_path),
        "whole_swath_class_counts": dict(zip(CLASSES, map(int, hist), strict=True)),
        "spatial_counts": totals,
        "sparse_fire_count": len(sparse["FP_line"]),
        "native_orientation_verified_against_all_sparse_fires": bool(len(sparse["FP_line"])),
        "pilot_grid_count": len(counts),
        "grids_with_pixel_centers": int(counts.pixel_center_count.gt(0).sum()),
        "pilot_class_counts": counts[list(CLASSES)].sum().astype(int).to_dict(),
        "pilot_qa_counts": counts[["input_non_nominal", "geo_non_nominal", "residual_bowtie"]]
        .sum()
        .astype(int)
        .to_dict(),
        "pilot_class_qa_counts": {
            label: dict(
                zip(
                    ["input_non_nominal", "geo_non_nominal", "residual_bowtie"],
                    map(int, pilot_class_qa[i]),
                    strict=True,
                )
            )
            for i, label in enumerate(CLASSES)
        },
        "pilot_land_nominal_input_no_residual": int(counts.land_nominal_input_no_residual.sum()),
        "guide": GUIDE,
        "negative_label_permitted": False,
        "limitations": [
            "One six-minute swath, not daily coverage",
            "Pixel centers are not pixel footprints or area coverage",
            "No centers does not prove zero footprint intersection",
            "No negative labels or coverage threshold selected",
        ],
    }
    if not sources["fire"]["cmr_checksum_verified"]:
        report["limitations"].append(
            "Fire checksum absent in CMR; size/identity and local SHA verified"
        )
    if not len(sparse["FP_line"]):
        report["limitations"].append("No sparse fires; orientation cross-check unavailable")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    stem = sample_stem(sensor, key)
    counts.reset_index().to_csv(OUTPUT / f"{stem}_grid_centers.csv", index=False)
    destination = OUTPUT / f"{stem}_audit.json"
    destination.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Report: {destination}")
    print(json.dumps(totals))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-directory", type=Path, default=SAMPLE)
    parser.add_argument(
        "--fire-metadata", type=Path, default=OUTPUT / "G2923107950-LPCLOUD_metadata.json"
    )
    parser.add_argument(
        "--geo-metadata", type=Path, default=OUTPUT / "G2126422502-LAADS_metadata.json"
    )
    args = parser.parse_args()
    inspect(args.sample_directory, args.fire_metadata, args.geo_metadata)
