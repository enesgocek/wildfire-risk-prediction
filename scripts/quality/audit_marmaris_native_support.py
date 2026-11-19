"""Offline native review of five planned centers and their uncut same-minute graph context."""

import csv
import json
import socket
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from exactextract import exact_extract
from measure_corine_review_supports import class_areas
from prepare_marmaris_native_pair import BASE, ROOT, module
from pyproj import Transformer, network
from rasterio.windows import Window
from shapely.ops import transform, unary_union

from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.event_lineage import trace_lineage
from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.native_cover_context import (
    center_patch_polygon,
    overlap_reference_map,
    rounded_coordinate_matches,
)
from wildfire_risk_prediction.target_admission import specification

PLAN = BASE / "observation_core_transfer_v1/20261119T124453Z_f5b8c745/native_plan.json"
PROBE = BASE / "observation_core_native_v1/20261119T125201Z_9bbb60ae/native_probe.json"
CONTEXT = BASE / "marmaris_published_marker_v1/20261119T124316Z_6993b935/readback.json"
CATALOG = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
DELIVERY = BASE / "corine_delivery_review_v1/20261103T212921Z_3cc30ebb"
CGLS = ROOT / "data/raw/landcover/landcover_copernicus_2017.tif"
CORINE = DELIVERY / "source/DATA/U2018_CLC2018_V2020_20u1.tif"
GUIDE = BASE / "salur_native_support_v1/sources/VIIRS_C2_AF-375m_User_Guide_1.2.pdf"
PINS = {
    PLAN: "04b40b06a7137b0fbea2618a141867ad2fef13052e265ed070c13f34b358a864",
    PROBE: "8073703bdc484df25f4b51760939d5a92670fedd1a70b7c11a8d202ef99cb82f",
    CONTEXT: "6672e96bb52dbc65d385b9debd00675528f868086b6eb0df2992feb6a438301b",
    CATALOG: "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5",
    CGLS: "ee8bd6c9f742dbbdfcdcbbb6ecc446499f05d676eaeb202c4345c11ea6006470",
    CORINE: "69057d527b4338b89f58cf15693effcf18017611ff48144e5c491d083cf1b004",
    DELIVERY / "readback.json": "be52cf11729cec66f84a8abf8d45c3ac9bfaf8d764f68255f2c5ab4ae3b4313f",
    GUIDE: "fb957afb6e465cb312fb8229a2b6e424c489344bb09e76a7baee80a248d1ccb7",
}
FIRST = pd.Timestamp("2022-06-21T23:22:00Z")


def first_pass_context(anchors):
    with CATALOG.open(encoding="utf-8-sig", newline="") as stream:
        rows = [
            r
            for r in csv.DictReader(stream)
            if r["acq_date"] == "2022-06-21"
            and r["source_sensor"] == "N20"
            and pd.Timestamp(r["detection_timestamp_utc"]) == FIRST
        ]
    frame = training_detections(pd.DataFrame(rows))
    require(len(frame) == 40 and frame.timestamp.eq(FIRST).all(), "Complete saved AOI/pass")
    require(set(anchors) <= set(frame.detection_id), "Every planned center remains in context")
    n = len(frame)
    xy = frame[["longitude", "latitude"]].to_numpy(float)
    distances = np.asarray(
        GEOD.inv(
            np.repeat(xy[:, 0], n),
            np.repeat(xy[:, 1], n),
            np.tile(xy[:, 0], n),
            np.tile(xy[:, 1], n),
        )[2]
    ).reshape(n, n)
    summaries, selected, membership = [], None, None
    for radius in (500, 1000, 2000):
        _, _, _, assignments, _ = trace_lineage(frame, distance_m=radius, gap_hours=24)
        key = "final_graph_membership_sha256"
        chosen = assignments.loc[assignments.detection_id.isin(anchors), key].unique()
        groups = assignments.loc[assignments[key].isin(chosen)]
        # Independent all-pairs closure; no radius crop before the graph is built.
        reach = distances <= radius
        for k in range(n):
            reach |= reach[:, k, None] & reach[k, None, :]
        expected = {
            tuple(sorted(frame.loc[reach[i], "detection_id"]))
            for i in frame.index[frame.detection_id.isin(anchors)]
        }
        actual = {tuple(sorted(g.detection_id)) for _, g in groups.groupby(key)}
        require(actual == expected, "Saved indexed graph equals independent complete-pass closure")
        summaries.append(
            {
                "distance_m": radius,
                "complete_AOI_same_minute_rows": len(frame),
                "selected_graph_groups": [
                    {
                        "membership_sha256": h,
                        "member_count": len(g),
                        "detection_ids": sorted(g.detection_id),
                        "first_cells": sorted(g.grid_id.unique()),
                    }
                    for h, g in groups.groupby(key)
                ],
                "graph_group_count_is_physical_fire_count": False,
                "complete_outside_project_AOI": False,
            }
        )
        if radius == 1000:
            selected = frame.loc[frame.detection_id.isin(groups.detection_id)].copy()
            membership = groups.set_index("detection_id")[key].to_dict()
    require(len(selected) == 15 and set(anchors) <= set(selected.detection_id), "15-center context")
    selected["planned_primary_center"] = selected.detection_id.isin(anchors)
    selected["same_minute_component_sha256"] = selected.detection_id.map(membership)
    return frame, selected, summaries


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline cached-pair review")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    network.set_network_enabled(False)
    pins = dict(PINS)
    require(all(digest(p) == h for p, h in pins.items()), "Pinned review inputs")
    probe = json.loads(PROBE.read_text())
    completion = PROBE.parent / "completion_readback.json"
    require(
        json.loads(completion.read_text())["report_sha256"] == pins[PROBE], "Completed download"
    )
    require(
        probe["status"] == "one_pair_bytes_and_headers_passed"
        and probe["plan_sha256"] == pins[PLAN],
        "Correct bounded download",
    )
    runner = module("marmaris_pair_runner", "scripts/firms/run_observation_core_pair.py")
    plan, pair = runner.load_plan(PLAN)
    require(pair["sample_id"] == "N20:2022172.2318", "Selected 2022 fit-role granule")
    cache = ROOT / probe["cache_directory"]
    require(
        cache.resolve().is_relative_to(ROOT / "data/raw/observation_core_v1"), "Contained cache"
    )
    paths = {s["role"]: cache / s["filename"] for s in pair["sources"]}
    for source in pair["sources"]:
        check_file(paths[source["role"]], source)
        pins[paths[source["role"]]] = source["sha256"]
    pins[completion] = digest(completion)
    full_pass, cohort, scenarios = first_pass_context(plan["selection_catalog_ids"])
    inspector = module("marmaris_native", "scripts/firms/inspect_l2_observation_sample.py")
    records, polygons, native_positions = [], {}, set()
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask = inspector.layer(stack, paths["fire"], "fire_mask")
        qa = inspector.layer(stack, paths["fire"], "algorithm_QA")
        lat = inspector.layer(stack, paths["geolocation"], "geolocation_data/latitude")
        lon = inspector.layer(stack, paths["geolocation"], "geolocation_data/longitude")
        inspector.validate_pair(paths["fire"], paths["geolocation"], mask.tags(), lat.tags())
        sparse = inspector.read_sparse(stack, paths["fire"], int(mask.tags()["FirePix"]))
        scan_fields = {
            name: inspector.layer(stack, paths["geolocation"], "scan_line_attributes/" + name)
            .read(1)
            .ravel()
            for name in ("scan_start_time", "scan_end_time", "scan_quality", "sensor_mode")
        }
        leap = int(lat.tags()["TAI93_leapseconds"])
        require(
            0 <= leap <= 100 and all(len(v) * 32 == mask.height for v in scan_fields.values()),
            "Scan clock shape and conversion",
        )
        with rasterio.open(CGLS) as cgls, rasterio.open(CORINE) as corine:
            legend = json.loads((DELIVERY / "readback.json").read_text())["legend"]
            for p in cohort.itertuples():
                matches = rounded_coordinate_matches(
                    p.latitude, p.longitude, sparse["FP_latitude"], sparse["FP_longitude"]
                )
                require(
                    len(matches) == 1, "Every context center uniquely matches this native granule"
                )
                index = int(matches[0])
                r, c = int(sparse["FP_line"][index]), int(sparse["FP_sample"][index])
                require(
                    (r, c) not in native_positions, "Distinct native center for each catalog row"
                )
                native_positions.add((r, c))
                require(1 <= r < mask.height - 1 and 1 <= c < mask.width - 1, "Complete 3x3 patch")
                w = Window(c - 1, r - 1, 3, 3)
                lng, lt, values, flags = (ds.read(1, window=w) for ds in (lon, lat, mask, qa))
                value, flag = int(values[1, 1]), int(flags[1, 1])
                require(
                    value == int(sparse["FP_confidence"][index]) == {"n": 8, "h": 9}[p.confidence],
                    "Catalog/sparse/native classification agrees",
                )
                require(
                    abs(lng[1, 1] - sparse["FP_longitude"][index]) <= 1e-5
                    and abs(lt[1, 1] - sparse["FP_latitude"][index]) <= 1e-5,
                    "Native sparse orientation",
                )
                support = center_patch_polygon(lng, lt, r)
                polygons[p.detection_id] = support
                projected = transform(
                    Transformer.from_crs(6933, corine.crs, always_xy=True).transform, support
                )
                areas = class_areas(corine, projected)
                independent = exact_extract(
                    corine,
                    gpd.GeoDataFrame(geometry=[projected], crs=corine.crs),
                    ["unique", "frac"],
                )[0]["properties"]
                fractions = dict(
                    zip(
                        map(int, independent["unique"]),
                        map(float, independent["frac"]),
                        strict=True,
                    )
                )
                require(set(fractions) == set(areas), "Independent reference classes agree")
                error = max(abs(fractions[k] - a / projected.area) for k, a in areas.items())
                require(error < 1e-6, "Independent CORINE support fractions")
                scan = r // 32
                times = {
                    name: (
                        pd.Timestamp("1993-01-01T00:00:00Z")
                        + pd.to_timedelta(float(scan_fields[name][scan]) - leap, unit="s")
                    ).isoformat()
                    for name in ("scan_start_time", "scan_end_time")
                }
                require(
                    pd.Timestamp(times["scan_start_time"]).floor("min") == FIRST,
                    "Native scan agrees with catalog minute",
                )
                records.append(
                    {
                        "detection_id": p.detection_id,
                        "grid_id": p.grid_id,
                        "planned_primary_center": bool(p.planned_primary_center),
                        "same_minute_component_sha256": p.same_minute_component_sha256,
                        "catalog_longitude": p.longitude,
                        "catalog_latitude": p.latitude,
                        "native_row": r,
                        "native_column": c,
                        "scan_index": scan,
                        **times,
                        "catalog_native_center_distance_m": GEOD.inv(
                            p.longitude, p.latitude, float(lng[1, 1]), float(lt[1, 1])
                        )[2],
                        "fire_mask": value,
                        "qa": flag,
                        "qa_set_bits": [i for i in range(32) if flag & (1 << i)],
                        "input_low7": flag & 127,
                        "m13_non_nominal": bool(flag & (1 << 6)),
                        "geolocation_non_nominal": bool(flag & (1 << 5)),
                        "residual_bowtie": bool(flag & (1 << 22)),
                        "scan_quality": int(scan_fields["scan_quality"][scan]),
                        "sensor_mode": int(scan_fields["sensor_mode"][scan]),
                        "native_mask_3x3": values.tolist(),
                        "approximate_support_corners_6933": list(
                            map(list, support.exterior.coords)
                        ),
                        "approximate_support_area_m2": support.area,
                        "cgls_2017": overlap_reference_map(support, cgls),
                        "corine_2018": [
                            {
                                "raster_value": k,
                                "legend": legend.get(str(k)),
                                "fraction": a / projected.area,
                            }
                            for k, a in sorted(areas.items())
                        ],
                        "independent_corine_fraction_max_error": error,
                        "target": None,
                        "habitat_admission": "undecided",
                    }
                )
    out = (
        BASE
        / "marmaris_native_support_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    full_pass.to_csv(out / "complete_AOI_first_pass.csv", index=False)
    cohort.to_csv(out / "graph_context_centers.csv", index=False)
    primary = [r for r in records if r["planned_primary_center"]]
    require(len(primary) == 5, "All five planned centers retained")
    result = {
        "scope": "one_Marmaris_cached_swath_native_context_no_admission",
        "source_case_id": "marmaris_2022",
        "sample_id": pair["sample_id"],
        "planned_primary_count": len(primary),
        "graph_context_native_count": len(records),
        "same_minute_AOI_catalog_count": len(full_pass),
        "scenarios": scenarios,
        "points": records,
        "native_scan_count": len({r["scan_index"] for r in records}),
        "primary_approximate_support_union_area_m2": unary_union(
            [polygons[r["detection_id"]] for r in primary]
        ).area,
        "official_pixel_corners": False,
        "subpixel_fire_location_known": False,
        "quality_flag_used_to_accept_or_reject_real_fire": False,
        "source_three_vs_four_start_discrepancy_resolved": False,
        "additional_raw_downloads": 0,
        "network_used": False,
        "L_memberships_created": 0,
        "labels_created": False,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "code_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in [
                Path(__file__),
                ROOT / "src/wildfire_risk_prediction/native_cover_context.py",
                ROOT / "src/wildfire_risk_prediction/event_lineage.py",
                ROOT / "src/wildfire_risk_prediction/event_review.py",
                ROOT / "scripts/firms/inspect_l2_observation_sample.py",
                ROOT / "scripts/quality/measure_corine_review_supports.py",
            ]
        },
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    require(all(digest(p) == h for p, h in pins.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "JSON readback")
    print(path.relative_to(ROOT).as_posix(), digest(path))
    print("PASS native_context_and_reference_cover; no L/target admission")


if __name__ == "__main__":
    main()
