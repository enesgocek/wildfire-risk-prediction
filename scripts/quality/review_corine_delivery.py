"""Audit the received original CLC2018 archive and sample the frozen review centers."""

import hashlib
import io
import json
import stat
import struct
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from uuid import uuid4
from xml.etree import ElementTree as ET

import rasterio
from pyproj import CRS, Transformer
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
ARCHIVE = ROOT / "data/raw/landcover/corine_2018_review/incoming/7858.zip"
ARCHIVE_SHA = "aefe9f5175ca05d9e786b9ef221a78236018398b8d93649dc3fa33b161f090db"
FRAME = BASE / "corine_review_intake_v1/20261027T191612Z_2cba6fc4/review_points.geojson"
FRAME_SHA = "5e2af7289fb036bc52e6645539db17b1d915b287baa8ecd578ee5bdbd2407a3f"
STEM = "U2018_CLC2018_V2020_20u1"
PREFIX = "u2018_clc2018_v2020_20u1_raster100m/"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inspect_zip(z, limit):
    entries = z.infolist()
    require(
        len(entries) <= 100 and len({i.filename for i in entries}) == len(entries), "ZIP entries"
    )
    require(sum(i.file_size for i in entries) <= limit, "ZIP size limit")
    for info in entries:
        path = PurePosixPath(info.filename)
        require(
            not path.is_absolute()
            and ".." not in path.parts
            and "\\" not in info.filename
            and ":" not in info.filename,
            "Unsafe archive path",
        )
        require(not stat.S_ISLNK(info.external_attr >> 16), "Archive symlink")
        require(not info.flag_bits & 1, "Encrypted archive")
    require(z.testzip() is None, "ZIP CRC failure")
    return [{"path": i.filename, "bytes": i.file_size, "crc32": i.CRC} for i in entries]


def dbf_records(data):
    """Read the bundled plain DBF attribute table without executing package content."""
    count = struct.unpack_from("<I", data, 4)[0]
    header, width = struct.unpack_from("<HH", data, 8)
    fields = []
    offset = 32
    while data[offset] != 13:
        field = data[offset : offset + 32]
        fields.append((field[:11].split(b"\0")[0].decode("ascii"), field[16]))
        offset += 32
    require(sum(size for _, size in fields) + 1 == width, "DBF record length")
    rows = []
    for i in range(count):
        record = data[header + i * width : header + (i + 1) * width]
        require(len(record) == width and record[:1] == b" ", "Invalid DBF record")
        row, pos = {}, 1
        for name, size in fields:
            row[name] = record[pos : pos + size].decode("utf-8").strip()
            pos += size
        rows.append(row)
    return rows


def main():
    require(sha(ARCHIVE) == ARCHIVE_SHA and sha(FRAME) == FRAME_SHA, "Changed input")
    code_sha = sha(Path(__file__))
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = BASE / "corine_delivery_review_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(ARCHIVE) as outer:
        outer_inventory = inspect_zip(outer, 150_000_000)
        inner_name = "Results/" + PREFIX.rstrip("/") + ".zip"
        require(outer.namelist() == [inner_name], "Unexpected delivered package")
        inner_bytes = outer.read(inner_name)
    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
        inner_inventory = inspect_zip(inner, 300_000_000)
        wanted = [
            "DATA/" + STEM + suffix for suffix in (".tif", ".tfw", ".tif.vat.dbf", ".tif.xml")
        ] + [
            "Documents/readme_" + STEM + ".txt",
            "Legend/clc_legend_qgis_raster.qml",
            "Legend/CLC2018_CLC2018_V2018_20_QGIS.txt",
            "Metadata/" + STEM + ".xml",
        ]
        paths = {}
        for relative in wanted:
            content = inner.read(PREFIX + relative)
            destination = out / "source" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            paths[relative] = destination
    readme = paths["Documents/readme_" + STEM + ".txt"].read_text(encoding="utf-8-sig")
    require("Layer name: " + STEM in readme and "TR was added to CLC2018" in readme, "Identity")
    qml = ET.parse(paths["Legend/clc_legend_qgis_raster.qml"])
    legend = {}
    for entry in qml.findall(".//paletteEntry"):
        value = int(entry.attrib["value"])
        clc, label = entry.attrib["label"].split(" - ", 1)
        legend[value] = {"clc_code": int(clc), "label": label}
    require(set(legend) == set(range(1, 45)) | {48}, "Unexpected legend values")
    dbf = dbf_records(paths["DATA/" + STEM + ".tif.vat.dbf"].read_bytes())
    require(
        {int(r["Value"]): int(r["CODE_18"]) for r in dbf}
        == {v: r["clc_code"] for v, r in legend.items()},
        "DBF and QML class mappings differ",
    )
    (out / "bundled_attribute_table.json").write_text(json.dumps(dbf, indent=2), encoding="utf-8")
    points = json.loads(FRAME.read_text(encoding="utf-8"))["features"]
    require(len(points) == len({p["properties"]["detection_id"] for p in points}) == 25, "Points")
    rows = []
    with rasterio.open(paths["DATA/" + STEM + ".tif"]) as ds:
        wkt = ds.crs.to_wkt()
        require('AUTHORITY["EPSG","3035"]' in wkt, "Missing declared CRS")
        source_crs = CRS.from_wkt(wkt)
        operation = source_crs.coordinate_operation
        require(operation.method_name == "Lambert Azimuthal Equal Area", "Projection method")
        require(
            {p.name: p.value for p in operation.params}
            == {p.name: p.value for p in CRS.from_epsg(3035).coordinate_operation.params},
            "Projection parameters",
        )
        require(source_crs.ellipsoid.name == "GRS 1980", "Ellipsoid")
        require(ds.res == (100, 100), "Resolution")
        require(ds.count == 1 and ds.dtypes == ("int8",), "Band or datatype")
        require(ds.nodata == -128, "Unexpected raster NoData")
        transform = Transformer.from_crs(4326, ds.crs, always_xy=True)
        reference = Transformer.from_crs(4326, 3035, always_xy=True)
        coordinate_differences = []
        for feature in points:
            properties = feature["properties"]
            require(
                2018 <= datetime.fromisoformat(properties["prediction_utc"]).year <= 2023, "Split"
            )
            require(properties["target"] is None, "Unexpected target")
            x, y = transform.transform(*feature["geometry"]["coordinates"])
            ex, ey = reference.transform(*feature["geometry"]["coordinates"])
            coordinate_differences.append(max(abs(ex - x), abs(ey - y)))
            require(coordinate_differences[-1] < 0.01, "Reference CRS coordinate mismatch")
            row, col = ds.index(x, y)
            require(1 <= row < ds.height - 1 and 1 <= col < ds.width - 1, "Outside raster")
            value = int(next(ds.sample([(x, y)]))[0])
            window = ds.read(1, window=Window(col - 1, row - 1, 3, 3))
            require(value == int(window[1, 1]) and value in legend, "Sampling mismatch")
            require(all(int(v) in legend or int(v) == ds.nodata for v in window.flat), "Local code")
            rows.append(
                {
                    **properties,
                    "raster_value": value,
                    "corine_class": legend[value],
                    "valid_class": 1 <= value <= 44,
                    "raster_row": row,
                    "raster_col": col,
                    "raster_xy": [x, y],
                    "neighbor_3x3_values": window.tolist(),
                    "neighbor_3x3_distinct_values": sorted({int(v) for v in window.flat}),
                    "is_full_support_measurement": False,
                    "historical_predictor_use_permitted": False,
                    "natural_cover_verified": False,
                }
            )
        raster = {
            "crs": str(ds.crs),
            "resolution": ds.res,
            "shape": ds.shape,
            "transform": list(ds.transform),
            "bounds": list(ds.bounds),
            "dtype": ds.dtypes[0],
            "nodata": ds.nodata,
            "wkt": wkt,
            "automatic_epsg_recognition": ds.crs.to_epsg(),
            "declared_epsg": 3035,
            "projection_parameters_match_3035": True,
            "max_25_point_coordinate_difference_m": max(coordinate_differences),
        }
    source_hashes = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in paths.values()}
    source_hashes[ARCHIVE.relative_to(ROOT).as_posix()] = ARCHIVE_SHA
    source_hashes[FRAME.relative_to(ROOT).as_posix()] = FRAME_SHA
    source_hashes[Path(__file__).relative_to(ROOT).as_posix()] = code_sha
    result = {
        "purpose": "retrospective_land_use_context_only",
        "download_provenance": (
            "user_reported_official_portal_download; no provider checksum obtained"
        ),
        "source_sha256": source_hashes,
        "inner_zip_sha256": hashlib.sha256(inner_bytes).hexdigest(),
        "archive_inventories": {"outer": outer_inventory, "inner": inner_inventory},
        "archive_crc_and_paths_passed": True,
        "raster": raster,
        "legend": legend,
        "point_results": rows,
        "summary": {
            "points": len(rows),
            "valid_classes": sum(r["valid_class"] for r in rows),
            "center_class_counts": dict(Counter(str(r["corine_class"]["clc_code"]) for r in rows)),
            "heterogeneous_3x3_points": sum(
                len(r["neighbor_3x3_distinct_values"]) > 1 for r in rows
            ),
        },
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    for relative, expected in source_hashes.items():
        require(sha(ROOT / relative) == expected, "Source modified during run")
    report = out / "readback.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(
        json.loads(report.read_text(encoding="utf-8")) == json.loads(json.dumps(result)), "Readback"
    )
    print(out.relative_to(ROOT))
    print(json.dumps(result["summary"]))
    print("report_sha256", sha(report))
    for row in rows:
        print(row["code"], row["cover_reference_2017"], json.dumps(row["corine_class"]))


if __name__ == "__main__":
    main()
