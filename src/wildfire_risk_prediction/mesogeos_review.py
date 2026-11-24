"""Read source context after byte-level year guards; no fire-label acceptance."""

import codecs
import math
import re
import struct
from collections import Counter
from datetime import UTC, date, datetime, time
from pathlib import Path

from pyproj import Geod, Transformer
from shapely import wkt
from shapely.geometry import Point
from shapely.ops import transform

from .mesogeos_reference import dbf_header

OPEN_YEAR = rb"(?:2018|2019|2020|2021|2022)"
FIELDS = [
    "id",
    "YEAR",
    "FIREDATE",
    "COUNTRY",
    "PROVINCE",
    "COMMUNE",
    "AREA_HA",
    "IGNITION_D",
    "ACQ_DATE",
    "ACQ_TIME",
    "LATITUDE",
    "LONGITUDE",
    "SATELLITE_",
    "INSTRUMENT",
    "CONFIDENCE",
    "VERSION",
    "geometry_h",
]


def read_open_year_rows(path, encoding):
    """Never decode scientific fields until YEAR and native date guards pass."""
    codecs.lookup(encoding)
    counts = Counter()
    result = []
    with Path(path).open("rb") as handle:
        initial = handle.read(32)
        header_length = struct.unpack_from("<H", initial, 8)[0]
        handle.seek(0)
        schema = dbf_header(handle.read(header_length))
        offsets, start = {}, 1
        for field in schema["fields"]:
            offsets[field["name"]] = slice(start, start + field["width"])
            start += field["width"]
        if not set(FIELDS) <= set(offsets):
            raise ValueError("Required native context fields missing")
        for index in range(schema["record_count_declared"]):
            raw = handle.read(schema["record_bytes"])
            if len(raw) != schema["record_bytes"]:
                raise ValueError("Truncated native reference record")
            counts["source_records_scanned_for_year_metadata"] += 1
            if raw[:1] == b"*":
                counts["deleted_records_skipped"] += 1
                continue
            if raw[:1] != b" ":
                raise ValueError("Unexpected DBF deletion flag")
            if not re.fullmatch(rb"\s*" + OPEN_YEAR + rb"\s*", raw[offsets["YEAR"]]):
                counts["opaque_YEAR_outside_allowlist_or_unreadable"] += 1
                continue
            if not re.match(rb"\s*" + OPEN_YEAR + rb"-", raw[offsets["IGNITION_D"]]):
                counts["opaque_IGNITION_D_year_outside_allowlist_or_unreadable"] += 1
                continue
            acq = raw[offsets["ACQ_DATE"]].strip()
            if (
                acq
                and acq.lower() not in {b"none", b"nan", b"null"}
                and not re.match(OPEN_YEAR + rb"-", acq)
            ):
                counts["opaque_ACQ_DATE_year_outside_allowlist_or_unreadable"] += 1
                continue
            row = {"source_record_index": index}
            for name in FIELDS:
                value = raw[offsets[name]].strip()
                if name == "FIREDATE" and value and not re.match(OPEN_YEAR + rb"-", value):
                    row[name] = ""
                    row["FIREDATE_redacted_outside_open_years"] = True
                else:
                    row[name] = value.decode(encoding, errors="strict").strip()
            row.setdefault("FIREDATE_redacted_outside_open_years", False)
            result.append(row)
            counts["open_year_rows_decoded"] += 1
        trailing = handle.read()
        if trailing not in {b"", b"\x1a"}:
            raise ValueError("Unexpected bytes after declared DBF records")
    return result, dict(counts), schema


def finite_number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None


def acquisition_clock_candidate(row):
    """Conditional preserved-FIRMS clock interpretation, never an accepted onset."""
    try:
        day = date.fromisoformat(row["ACQ_DATE"][:10])
        raw = row["ACQ_TIME"].strip()
        if raw.endswith(".0"):
            raw = raw[:-2]
        if not raw.isdigit() or not 1 <= len(raw) <= 4:
            return None
        raw = raw.zfill(4)
        clock = time(int(raw[:2]), int(raw[2:]))
        return datetime.combine(day, clock, tzinfo=UTC).isoformat()
    except (ValueError, KeyError):
        return None


def review_points(rows, aoi):
    to_geo = Transformer.from_crs(5643, 4326, always_xy=True)
    to_grid = Transformer.from_crs(4326, 6933, always_xy=True)
    geod = Geod(ellps="WGS84")
    reviewed, issues = [], []
    for original in rows:
        row = dict(original)
        point = None
        try:
            native = wkt.loads(row["geometry_h"])
            if native.geom_type != "Point" or native.is_empty:
                raise ValueError("Not a native reference point")
            point = transform(to_geo.transform, native)
            if not (-180 <= point.x <= 180 and -90 <= point.y <= 90):
                raise ValueError("Invalid transformed native point")
        except Exception:
            issues.append(
                {
                    "source_record_index": row["source_record_index"],
                    "issue": "native_point_unreadable",
                }
            )
        lon, lat = finite_number(row["LONGITUDE"]), finite_number(row["LATITUDE"])
        attribute_point = (
            Point(lon, lat)
            if lon is not None and lat is not None and -180 <= lon <= 180 and -90 <= lat <= 90
            else None
        )
        native_in = point is not None and aoi.covers(point)
        attribute_in = attribute_point is not None and aoi.covers(attribute_point)
        if not (native_in or attribute_in):
            continue
        row.update(
            {
                "native_point_in_AOI": bool(native_in),
                "attribute_point_in_AOI": bool(attribute_in),
                "native_point_lon": point.x if point is not None else None,
                "native_point_lat": point.y if point is not None else None,
                "coordinate_pair_distance_m": abs(geod.inv(point.x, point.y, lon, lat)[2])
                if point is not None and attribute_point is not None
                else None,
                "acquisition_utc_candidate_if_FIRMS_fields_preserved": acquisition_clock_candidate(
                    row
                ),
                "native_ignition_date_equals_acquisition_date": row["IGNITION_D"][:10]
                == row["ACQ_DATE"][:10],
                "area_ha_numeric": finite_number(row["AREA_HA"]),
                "clock_semantics_accepted": False,
                "target": None,
                "accepted_L_membership": None,
                "daily_observation_status": "unknown",
                "negative_label_permitted": False,
                "source_role": "supplementary_satellite_context_not_independent_truth",
            }
        )
        if point is not None:
            gx, gy = to_grid.transform(point.x, point.y)
            row["candidate_grid_id_not_membership_acceptance"] = (
                f"E6933_5K_V1_C{math.floor(gx / 5000)}_R{math.floor(gy / 5000)}"
            )
        else:
            row["candidate_grid_id_not_membership_acceptance"] = None
        reviewed.append(row)
    return reviewed, issues
