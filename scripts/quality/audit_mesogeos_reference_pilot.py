"""Independently read open-year metadata/selected geometries and preserve S/U roles."""

import csv
import hashlib
import json
import struct
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pyogrio
from pyproj import CRS
from shapely import wkt
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
FIRST = BASE / "mesogeos_reference_pilot_run_v1/20261124T231948Z_e9a7e57e"
GEOMETRY = BASE / "mesogeos_reference_geometry_review_v1/20261124T232735Z_136d2a12"
OLD = BASE / "experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def save(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def main():
    initial = json.loads((FIRST / "readback.json").read_bytes())
    geo_receipt = json.loads((GEOMETRY / "readback.json").read_bytes())
    require(
        digest(FIRST / "readback.json") == geo_receipt["first_stage_receipt_sha256"],
        "Exact first-stage receipt",
    )
    raw = ROOT / geo_receipt["source_directory"]
    for name, expected in geo_receipt["raw_file_sha256"].items():
        require(digest(raw / name) == expected, "Complete native source snapshots")
    for name, expected in geo_receipt["artifact_sha256"].items():
        require(digest(GEOMETRY / name) == expected, "Geometry review artifacts")
    for name, expected in initial["artifact_sha256"].items():
        if name != "child.log":
            require(digest(FIRST / name) == expected, "First-stage scientific artifacts")
    require(
        digest(FIRST / "child.log")
        == geo_receipt["first_stage_streaming_log"]["post_launcher_sha256"],
        "Completed streaming log snapshot",
    )
    require(
        geo_receipt["elapsed_from_original_run_seconds"] < 900
        and geo_receipt["total_original_file_bytes_received"] == 159822559,
        "Original time/byte budget",
    )
    point_rows = csv_rows(FIRST / "point_context_review.csv")
    polygon_rows = csv_rows(GEOMETRY / "perimeter_context_review.csv")
    by_index = {int(row["source_record_index"]): row for row in point_rows}
    aoi = shape(json.loads((ROOT / "data/aoi/aoi.geojson").read_bytes())["features"][0]["geometry"])
    encoding = (raw / "med_burned_areas_updated.cpg").read_text(encoding="ascii").strip()
    allowed = {b"2018", b"2019", b"2020", b"2021", b"2022"}
    seen = set()
    with (raw / "med_burned_areas_updated.dbf").open("rb") as handle:
        first = handle.read(32)
        count, header_bytes, width = struct.unpack_from("<IHH", first, 4)
        handle.seek(0)
        header = handle.read(header_bytes)
        offsets, offset = {}, 1
        for i in range(32, header_bytes - 1, 32):
            name = header[i : i + 11].split(b"\x00", 1)[0].decode("ascii")
            size = header[i + 16]
            offsets[name] = slice(offset, offset + size)
            offset += size
        decoded = 0
        for index in range(count):
            record = handle.read(width)
            require(len(record) == width, "Complete native record boundary")
            if record[:1] != b" " or record[offsets["YEAR"]].strip() not in allowed:
                continue
            if record[offsets["IGNITION_D"]].lstrip()[:4] not in allowed:
                continue
            acquisition = record[offsets["ACQ_DATE"]].strip()
            if (
                acquisition.lower() not in {b"", b"none", b"nan", b"null"}
                and acquisition[:4] not in allowed
            ):
                continue
            decoded += 1
            lon = float(record[offsets["LONGITUDE"]].decode(encoding).strip())
            lat = float(record[offsets["LATITUDE"]].decode(encoding).strip())
            if not aoi.covers(Point(lon, lat)):
                continue
            seen.add(index)
            require(index in by_index, "Independent attribute-coordinate AOI selection")
            for name in ["id", "YEAR", "IGNITION_D", "ACQ_DATE", "ACQ_TIME", "geometry_h"]:
                require(
                    record[offsets[name]].decode(encoding).strip() == by_index[index][name],
                    "Raw native field preservation",
                )
    require(
        decoded == 9900 and seen == set(by_index) and len(seen) == 92,
        "Year guards and AOI point inventory",
    )
    gdf = pyogrio.read_dataframe(
        raw / "med_burned_areas_updated.shp",
        columns=[],
        fids=sorted(seen),
        fid_as_index=True,
        use_arrow=False,
    )
    require(
        set(map(int, gdf.index)) == seen
        and gdf.crs == CRS.from_epsg(5643)
        and list(gdf.columns) == ["geometry"],
        "Only selected open-year shapes",
    )
    with (
        (raw / "med_burned_areas_updated.shx").open("rb") as index_file,
        (raw / "med_burned_areas_updated.shp").open("rb") as shape_file,
    ):
        for row in polygon_rows:
            index = int(row["source_record_index"])
            index_file.seek(100 + 8 * index)
            offset_words, size_words = struct.unpack(">II", index_file.read(8))
            shape_file.seek(2 * offset_words)
            number, actual_size = struct.unpack(">II", shape_file.read(8))
            require(
                number == index + 1 and actual_size == size_words, "Raw SHX record ordinal mapping"
            )
            geometry, point = gdf.loc[index].geometry, wkt.loads(by_index[index]["geometry_h"])
            require(
                geometry.is_valid and row["geometry_valid"] == "True", "Source geometry validity"
            )
            require(
                str(bool(geometry.covers(point))) == row["native_point_covered_by_final_perimeter"],
                "Native point/perimeter relationship",
            )
            require(
                abs(
                    geometry.distance(point)
                    - float(row["native_point_to_final_perimeter_distance_m"])
                )
                < 1e-8,
                "Native projection distance readback",
            )
    old_receipt = json.loads((OLD / "readback.json").read_bytes())
    require(
        digest(OLD / "readback.json")
        == "86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366",
        "Unchanged original S/U receipt",
    )
    require(
        digest(OLD / "inspection_memberships.csv")
        == old_receipt["artifact_sha256"]["inspection_memberships.csv"],
        "Original membership artifact",
    )
    old = csv_rows(OLD / "inspection_memberships.csv")
    lookup = {(row["grid_id"], row["prediction_timestamp_utc"][:10]): row for row in old}
    s_columns = [name for name in old[0] if name.startswith("S_candidate_context_")]
    require(len(s_columns) == 9, "Original nine source-context settings")
    links = []
    for row in point_rows:
        require(
            not row["target"]
            and not row["accepted_L_membership"]
            and row["daily_observation_status"] == "unknown"
            and row["negative_label_permitted"] == "False"
            and row["clock_semantics_accepted"] == "False",
            "No source labels or accepted clock",
        )
        key = (row["candidate_grid_id_not_membership_acceptance"], row["IGNITION_D"][:10])
        prior = lookup.get(key)
        count_s = sum(prior[column] == "True" for column in s_columns) if prior else 0
        category = (
            "existing_S_context"
            if count_s
            else ("existing_unassigned_context" if prior else "native_key_absent_from_old_calendar")
        )
        links.append(
            {
                "source_record_index": row["source_record_index"],
                "source_id": row["id"],
                "grid_candidate": key[0],
                "native_date_not_accepted_UTC_target": key[1],
                "calendar_lookup_only": category,
                "existing_S_scenario_count": count_s,
                "new_S_proposal": None,
                "target": None,
                "accepted_L_membership": None,
                "negative_label_permitted": False,
            }
        )
    categories = dict(Counter(row["calendar_lookup_only"] for row in links))
    require(
        categories
        == {
            "existing_S_context": 60,
            "native_key_absent_from_old_calendar": 27,
            "existing_unassigned_context": 5,
        },
        "Exact native date lookup inventory",
    )
    out = (
        BASE
        / "mesogeos_reference_pilot_audit_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    with (out / "native_date_context_lookup.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(links[0]))
        writer.writeheader()
        writer.writerows(links)
    result = {
        "status": "supplementary_reference_context_and_native_lookup_audited_not_label_acceptance",
        "analysis_date": "2026-11-25",
        "geometry_receipt_sha256": digest(GEOMETRY / "readback.json"),
        "first_stage_receipt_sha256": digest(FIRST / "readback.json"),
        "permitted_global_rows": decoded,
        "selected_AOI_rows": len(seen),
        "native_record_ordinals_checked": len(polygon_rows),
        "valid_geometries": len(polygon_rows),
        "point_inside_final_perimeter_rows": sum(
            row["native_point_covered_by_final_perimeter"] == "True" for row in polygon_rows
        ),
        "all_native_distances_below_1000m": all(
            float(row["native_point_to_final_perimeter_distance_m"]) <= 1000 for row in polygon_rows
        ),
        "native_lookup_counts": categories,
        "lookup_is_event_identity_or_true_positive_validation": False,
        "new_S_or_Y_or_L": False,
        "negative_labels_assigned": False,
        "final_merge": False,
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "auditor_sha256": digest(Path(__file__)),
    }
    save(out / "readback.json", result)
    print(out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
