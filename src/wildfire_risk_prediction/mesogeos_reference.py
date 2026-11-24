"""Metadata parsers for public reference preflight, without opening event rows."""

import math
import struct
from pathlib import PurePosixPath


def dbf_header(raw):
    """Read only a DBF header; reject bytes extending into scientific records."""
    if len(raw) < 33:
        raise ValueError("Incomplete DBF header")
    if raw[0] not in {0x03, 0x04, 0x30, 0x31, 0x43, 0x63, 0x83, 0x8B, 0xCB, 0xF5}:
        raise ValueError("Unsupported DBF metadata signature")
    count, length, record_size = struct.unpack_from("<IHH", raw, 4)
    if not 33 <= length <= 65535 or len(raw) != length or raw[-1] != 0x0D:
        raise ValueError("Exact DBF metadata boundary required")
    if (length - 33) % 32 or not 1 <= record_size <= 65535:
        raise ValueError("Invalid DBF schema layout")
    fields = []
    for offset in range(32, length - 1, 32):
        field = raw[offset : offset + 32]
        name = field[:11].split(b"\x00", 1)[0].decode("ascii")
        kind = chr(field[11])
        if not name or kind not in "CDFILMNTYB@O+":
            raise ValueError("Invalid DBF field descriptor")
        fields.append({"name": name, "type": kind, "width": field[16], "decimals": field[17]})
    if len({row["name"] for row in fields}) != len(fields):
        raise ValueError("Repeated DBF field names")
    if 1 + sum(row["width"] for row in fields) != record_size:
        raise ValueError("DBF field widths disagree with record size")
    return {
        "record_count_declared": count,
        "header_bytes": length,
        "record_bytes": record_size,
        "field_count": len(fields),
        "fields": fields,
        "record_values_read": 0,
    }


def shp_header(raw):
    """Read a 100-byte shapefile header, without feature geometries."""
    if len(raw) != 100 or struct.unpack_from(">I", raw)[0] != 9994:
        raise ValueError("Exact shapefile metadata boundary required")
    version, kind = struct.unpack_from("<II", raw, 28)
    if version != 1000 or kind not in {0, 1, 3, 5, 8, 11, 13, 15, 18, 21, 23, 25, 28, 31}:
        raise ValueError("Unsupported shapefile metadata")
    bounds = list(struct.unpack_from("<dddd", raw, 36))
    if not all(math.isfinite(x) for x in bounds) or not (
        bounds[0] <= bounds[2] and bounds[1] <= bounds[3]
    ):
        raise ValueError("Invalid shapefile metadata bounds")
    return {
        "file_bytes_declared": 2 * struct.unpack_from(">I", raw, 24)[0],
        "version": version,
        "shape_type": kind,
        "xy_bounds_declared": bounds,
        "feature_values_read": 0,
    }


def validate_proposal(config):
    """Keep this proposed source review separate from fire labels and models."""
    if config["permitted_years"] != [2018, 2019, 2020, 2021, 2022]:
        raise ValueError("Only existing open research years are proposed")
    forbidden = [
        "source_is_independent_ground_truth",
        "source_absence_is_negative",
        "new_model_training",
        "new_model_predictions",
        "target_assignment",
        "accepted_L_assignment",
        "risk_category_assignment",
        "final_merge",
        "cloud_execution",
        "external_contact",
        "execute_authorized",
    ]
    if not all(config[key] is False for key in forbidden):
        raise ValueError("Reference proposal cannot grant scientific acceptance or execution")
    files = config["files"]
    if len(files) != 5 or len({row["name"] for row in files}) != 5:
        raise ValueError("Exactly five distinct vector members")
    for row in files:
        if PurePosixPath(row["name"]).name != row["name"] or "\\" in row["name"]:
            raise ValueError("Reference members must be plain filenames")
        if not isinstance(row["expected_bytes"], int) or row["expected_bytes"] <= 0:
            raise ValueError("Known positive file sizes required")
    extensions = {PurePosixPath(row["name"]).suffix for row in files}
    if extensions != {".cpg", ".prj", ".dbf", ".shx", ".shp"}:
        raise ValueError("No datacube or unrelated data in proposed transfer")
    if sum(row["expected_bytes"] for row in files) > config["max_total_file_bytes"]:
        raise ValueError("Reference transfer exceeds proposed budget")
    if not 0 < config["max_elapsed_seconds"] <= 900:
        raise ValueError("Bounded local reference review")
