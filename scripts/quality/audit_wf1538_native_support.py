"""Offline source point versus catalogue/native WF1538 candidate; no event or label acceptance."""

import csv
import json
import socket
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import rasterio
from exactextract import exact_extract
from measure_corine_review_supports import class_areas
from prepare_marmaris_native_pair import module, write
from pyproj import Transformer, network
from rasterio.windows import Window
from shapely.geometry import Point
from shapely.ops import transform

from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.native_cover_context import (
    center_patch_polygon,
    overlap_reference_map,
    rounded_coordinate_matches,
)
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PLAN = BASE / "observation_core_transfer_v1/20261119T175711Z_78d19310/native_plan.json"
PROBE = BASE / "observation_core_native_v1/20261119T180544Z_45787761/native_probe.json"
SAMPLE = BASE / "source_sampling_review_v1/20261119T133150Z_f94ebe6e/readback.json"
CATALOG = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
CGLS = ROOT / "data/raw/landcover/landcover_copernicus_2017.tif"
DELIVERY = BASE / "corine_delivery_review_v1/20261103T212921Z_3cc30ebb"
CORINE = DELIVERY / "source/DATA/U2018_CLC2018_V2020_20u1.tif"
PROVISIONAL_SHA = "332b9b2ccf6ea0233c64ecfc3defd8fbec71abbd55ecfabe747e723f6018ff14"
PINS = {
    PLAN: "187a1afe064b18c3226ce5f62791b8e5353deb9654b75442b8af6d3e40d97dc4",
    PROBE: "47c287e36780fda500315b847798ecf7b8bf874432b7e1d5a488a9fee6cc8d9f",
    SAMPLE: "9647a69248ac158aad6f7a864b48bfad8eb61860be08ff3250f8dc643cd4d453",
    CATALOG: "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5",
    CGLS: "ee8bd6c9f742dbbdfcdcbbb6ecc446499f05d676eaeb202c4345c11ea6006470",
    CORINE: "69057d527b4338b89f58cf15693effcf18017611ff48144e5c491d083cf1b004",
    DELIVERY / "readback.json": "be52cf11729cec66f84a8abf8d45c3ac9bfaf8d764f68255f2c5ab4ae3b4313f",
}


def qa_context(flag):
    require(isinstance(flag, int) and 0 <= flag < 2**32, "Unsigned 32-bit QA")
    return {
        "qa": flag,
        "qa_set_bits": [b for b in range(32) if flag & (1 << b)],
        "input_low7": flag & 127,
        "geolocation_non_nominal": bool(flag & (1 << 5)),
        "m13_non_nominal": bool(flag & (1 << 6)),
        "residual_bowtie": bool(flag & (1 << 22)),
    }


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline native support")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    network.set_network_enabled(False)
    require(all(digest(p) == h for p, h in PINS.items()), "Pinned input versions")
    pins = dict(PINS)
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    completion = PROBE.parent / "completion_readback.json"
    require(
        json.loads(completion.read_text())["report_sha256"] == digest(PROBE), "Completed download"
    )
    runner = module("wf1538_runner", "scripts/firms/run_observation_core_pair.py")
    plan, pair = runner.load_plan(PLAN)
    require(
        pair["sample_id"] == "N20:2022147.1030" and probe["plan_sha256"] == digest(PLAN),
        "Exact follow-up pair",
    )
    cache = ROOT / probe["cache_directory"]
    require(
        cache.resolve() == ROOT / "data/raw/observation_core_v1" / digest(PLAN)[:16],
        "Dedicated cache",
    )
    paths = {s["role"]: cache / s["filename"] for s in pair["sources"]}
    for s in pair["sources"]:
        check_file(paths[s["role"]], s)
        pins[paths[s["role"]]] = s["sha256"]
    runner.native_headers(pair, cache)
    source = next(
        r for r in json.loads(SAMPLE.read_text())["intake"] if r["archive_row"] == "WF1538"
    )
    with CATALOG.open(encoding="utf-8-sig", newline="") as stream:
        rows = [
            r
            for r in csv.DictReader(stream)
            if r["acq_date"] == "2022-05-27" and r["detection_id"] == "N20_815590_170090"
        ]
    require(len(rows) == 1, "Exact 2022 source candidate")
    candidate = rows[0]
    inspector = module("wf1538_inspector", "scripts/firms/inspect_l2_observation_sample.py")
    area = module("wf1538_time", "scripts/firms/estimate_l2_observed_area.py")
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask = inspector.layer(stack, paths["fire"], "fire_mask")
        qa = inspector.layer(stack, paths["fire"], "algorithm_QA")
        lat, lon = [
            inspector.layer(stack, paths["geolocation"], "geolocation_data/" + n)
            for n in ("latitude", "longitude")
        ]
        sparse = inspector.read_sparse(stack, paths["fire"], int(mask.tags()["FirePix"]))
        matches = rounded_coordinate_matches(
            float(candidate["latitude"]),
            float(candidate["longitude"]),
            sparse["FP_latitude"],
            sparse["FP_longitude"],
        )
        require(len(matches) == 1, "Unique rounded catalogue/native sparse match")
        i = int(matches[0])
        r, c = int(sparse["FP_line"][i]), int(sparse["FP_sample"][i])
        window = Window(c - 1, r - 1, 3, 3)
        lng, lt, values, flags = [ds.read(1, window=window) for ds in (lon, lat, mask, qa)]
        value, flag = int(values[1, 1]), int(flags[1, 1])
        require(
            value == int(sparse["FP_confidence"][i]) == 8 and candidate["confidence"] == "n",
            "Catalogue/sparse/native nominal-confidence agreement",
        )
        require(
            abs(lng[1, 1] - sparse["FP_longitude"][i]) <= 1e-5
            and abs(lt[1, 1] - sparse["FP_latitude"][i]) <= 1e-5,
            "Native array orientation",
        )
        support = center_patch_polygon(lng, lt, r)
        project = Transformer.from_crs(4326, 6933, always_xy=True)
        source_point = Point(*project.transform(source["longitude"], source["latitude"]))
        center = Point(*project.transform(float(lng[1, 1]), float(lt[1, 1])))
        scan = r // 32
        leap = int(lat.tags()["TAI93_leapseconds"])
        times = {
            n: area.tai93_utc(
                inspector.layer(stack, paths["geolocation"], "scan_line_attributes/" + f)
                .read(1)
                .ravel(),
                leap,
            )[scan].isoformat()
            for n, f in (("start_utc", "scan_start_time"), ("end_utc", "scan_end_time"))
        }
        with rasterio.open(CGLS) as cgls, rasterio.open(CORINE) as corine:
            cgls_result = overlap_reference_map(support, cgls)
            polygon = transform(
                Transformer.from_crs(6933, corine.crs, always_xy=True).transform, support
            )
            areas = class_areas(corine, polygon)
            check = exact_extract(
                corine,
                gpd.GeoDataFrame(geometry=[polygon], crs=corine.crs),
                ["unique", "frac"],
                output="pandas",
            ).iloc[0]
            independent = {
                int(k): float(v) * polygon.area
                for k, v in zip(check["unique"], check["frac"], strict=True)
            }
            require(
                set(areas) == set(independent)
                and all(abs(areas[k] - independent[k]) / polygon.area < 1e-6 for k in areas),
                "Independent CORINE overlap",
            )
        actual_start = datetime.fromisoformat(times["start_utc"])
        result = {
            "scope": "WF1538_catalogue_native_source_point_diagnostic_only",
            "archive_row": "WF1538",
            "detection_id": candidate["detection_id"],
            "sample_id": pair["sample_id"],
            "source_row": source,
            "catalogue_record": candidate,
            "native_row": r,
            "native_column": c,
            "native_longitude": float(lng[1, 1]),
            "native_latitude": float(lt[1, 1]),
            "scan_index": scan,
            **times,
            "fire_mask": value,
            **qa_context(flag),
            "supersedes_provisional_report_sha256": PROVISIONAL_SHA,
            "provisional_QA_field_correction": (
                "Geolocation is bit 5; shifted seven-bit field removed"
            ),
            "mask_3x3": values.tolist(),
            "qa_3x3": flags.tolist(),
            "source_point_6933": [source_point.x, source_point.y],
            "native_center_6933": [center.x, center.y],
            "source_to_native_center_projected_m": source_point.distance(center),
            "source_point_inside_approximate_fire_support": bool(support.covers(source_point)),
            "source_point_to_approximate_fire_support_m": source_point.distance(support),
            "approximate_support_corners_6933": list(map(list, support.exterior.coords)),
            "approximate_support_area_m2": support.area,
            "official_pixel_corners": False,
            "CGLS_2017_context": cgls_result,
            "CORINE_2018_class_areas_m2": {str(k): v for k, v in areas.items()},
            "CORINE_overlap_independently_verified": True,
            "minutes_scan_after_report_by_hypothesis": [
                {
                    "basis": h["basis"],
                    "minutes": (
                        actual_start - datetime.fromisoformat(h["reported_time_utc"])
                    ).total_seconds()
                    / 60,
                }
                for h in source["clock_hypotheses"]
            ],
            "source_clock_standard_resolved": False,
            "same_physical_fire_verified": False,
            "source_coordinate_start_role_verified": False,
            "quality_used_as_false_positive_rate": False,
            "L_memberships_created": 0,
            "labels_created": False,
            "gate": specification(),
            "model_trained": False,
            "final_merge_performed": False,
            "network_used": False,
        }
    pins[completion] = digest(completion)
    result["input_sha256"] = {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()}
    result["code_sha256"] = {
        p.relative_to(ROOT).as_posix(): digest(p)
        for p in [
            Path(__file__),
            ROOT / "src/wildfire_risk_prediction/native_cover_context.py",
            ROOT / "scripts/firms/inspect_l2_observation_sample.py",
            ROOT / "scripts/quality/measure_corine_review_supports.py",
        ]
    }
    require(all(digest(p) == h for p, h in pins.items()), "Input closure")
    out = (
        BASE
        / "wf1538_native_support_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    write(out / "readback.json", result)
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))


if __name__ == "__main__":
    main()
