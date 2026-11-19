"""Audit the exact 74-member Salur prefix in one cached swath, without label changes."""

import hashlib
import json
import socket
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
import rasterio
from prepare_salur_native_pair import BASE, ROOT, module
from pyproj import network
from rasterio.windows import Window

from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.event_review import GEOD, spatial_links, training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.native_cover_context import rounded_coordinate_matches
from wildfire_risk_prediction.target_admission import specification

CONTEXT = BASE / "salur_event_context_v1/20261118T230221Z_cab0c9e1/readback.json"
CONTEXT_SHA = "89ffb290079ae4167cbf3b577e9787cbbde5092118acaab0d43d704189dad846"
PLAN = BASE / "observation_core_transfer_v1/20261119T113530Z_92bbba6c/native_plan.json"
PLAN_SHA = "060a2456898a709a07b1a3e95b3abd05bf6921fa91bb11477a0439c6f4d4c4c8"
PROBE = BASE / "observation_core_native_v1/20261119T113907Z_b104e81d/native_probe.json"
PROBE_SHA = "2fb726fb9467091ddcffcbf49590bc26d6e9b97fd025a36a9de4541c357608b8"
GUIDE = BASE / "salur_native_support_v1/sources/VIIRS_C2_AF-375m_User_Guide_1.2.pdf"
GUIDE_SHA = "fb957afb6e465cb312fb8229a2b6e424c489344bb09e76a7baee80a248d1ccb7"
ANCHOR = "N20_815590_134793"
SCENARIO = "d1000m_t24h"


def anchored_component(frame):
    """Use the frozen graph's exact geodesic links; never infer physical fire identity."""
    frame = training_detections(frame)
    require(frame.timestamp.nunique() == 1, "One simultaneous catalog timestamp")
    links = spatial_links(frame, 1000)
    neighbours = [set() for _ in range(len(frame))]
    for i, later in enumerate(links.neighbours):
        for j in later:
            neighbours[i].add(int(j))
            neighbours[int(j)].add(i)
    selected = frame.index[frame.detection_id.eq(ANCHOR)]
    require(len(selected) == 1, "Unique first-local anchor")
    seen, todo = {int(selected[0])}, [int(selected[0])]
    while todo:
        for j in neighbours[todo.pop()] - seen:
            seen.add(j)
            todo.append(j)
    return frame.iloc[sorted(seen)].copy(), frame.loc[~frame.index.isin(seen)].copy()


def main():
    def deny(*args, **kwargs):
        raise RuntimeError("Offline first-prefix quality audit")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    network.set_network_enabled(False)
    pins = {CONTEXT: CONTEXT_SHA, PLAN: PLAN_SHA, PROBE: PROBE_SHA, GUIDE: GUIDE_SHA}
    require(all(digest(p) == h for p, h in pins.items()), "Frozen source inputs")
    context = json.loads(CONTEXT.read_text())
    members = CONTEXT.parent / "component_members.csv"
    pins[members] = context["artifact_sha256"][members.name]
    require(digest(members) == pins[members], "Saved full component membership")
    frame = pd.read_csv(members)
    frame = frame.loc[frame.scenario.eq(SCENARIO)].copy()
    require(frame.target.isna().all(), "No accepted targets")
    frame = training_detections(frame)
    frame = frame.loc[frame.timestamp.eq(pd.Timestamp(context["first_local_detection_utc"]))]
    cohort, excluded = anchored_component(frame)
    # Independent edge enumeration avoids the indexed neighbour search above.
    all_points = training_detections(frame)
    xy = all_points[["longitude", "latitude"]].to_numpy(float)
    n = len(xy)
    require(n <= 100, "Bounded all-pairs verification")
    distance = np.asarray(
        GEOD.inv(
            np.repeat(xy[:, 0], n),
            np.repeat(xy[:, 1], n),
            np.tile(xy[:, 0], n),
            np.tile(xy[:, 1], n),
        )[2]
    ).reshape(n, n)
    reach = distance <= 1000
    for k in range(n):
        reach |= reach[:, k, None] & reach[k, None, :]
    anchor_index = int(all_points.index[all_points.detection_id.eq(ANCHOR)][0])
    require(
        set(all_points.loc[reach[anchor_index], "detection_id"]) == set(cohort.detection_id),
        "All-pairs transitive closure agrees with saved/indexed cohort",
    )
    expected = next(s for s in context["scenarios"] if s["scenario"] == SCENARIO)
    expected = expected["at_first_local_detection"][0]
    signature = hashlib.sha256("\n".join(sorted(cohort.detection_id)).encode()).hexdigest()
    require(
        signature == expected["prefix_membership_sha256"] and len(cohort) == 74,
        "Exact prefix, not all same-minute members of later full component",
    )
    require(
        sorted(cohort.grid_id.unique()) == json.loads(expected["earliest_grid_ids_json"]),
        "All first cells preserved",
    )
    runner = module("prefix_pair_runner", "scripts/firms/run_observation_core_pair.py")
    _, pair = runner.load_plan(PLAN)
    probe = json.loads(PROBE.read_text())
    require(
        probe["plan_sha256"] == PLAN_SHA and probe["status"] == "one_pair_bytes_and_headers_passed",
        "Completed selected pair",
    )
    require(
        json.loads((PROBE.parent / "completion_readback.json").read_text())["report_sha256"]
        == PROBE_SHA,
        "Probe completion",
    )
    require(
        pair["sample_id"] == "N20:2021209.1012" and cohort.source_sensor.eq("N20").all(),
        "Single swath cohort",
    )
    cache = ROOT / probe["cache_directory"]
    require(
        cache.resolve().is_relative_to(ROOT / "data/raw/observation_core_v1"),
        "Contained native input",
    )
    paths = {s["role"]: cache / s["filename"] for s in pair["sources"]}
    for s in pair["sources"]:
        check_file(paths[s["role"]], s)
        pins[paths[s["role"]]] = s["sha256"]
    native = module("prefix_native_inspector", "scripts/firms/inspect_l2_observation_sample.py")
    records = []
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask = native.layer(stack, paths["fire"], "fire_mask")
        qa = native.layer(stack, paths["fire"], "algorithm_QA")
        lat = native.layer(stack, paths["geolocation"], "geolocation_data/latitude")
        lon = native.layer(stack, paths["geolocation"], "geolocation_data/longitude")
        native.validate_pair(paths["fire"], paths["geolocation"], mask.tags(), lat.tags())
        sparse = native.read_sparse(stack, paths["fire"], int(mask.tags()["FirePix"]))
        times = {
            n: native.layer(stack, paths["geolocation"], "scan_line_attributes/" + n)
            .read(1)
            .ravel()
            for n in ("scan_start_time", "scan_end_time")
        }
        leap = int(lat.tags()["TAI93_leapseconds"])
        require(
            0 <= leap <= 100 and all(len(t) * 32 == mask.height for t in times.values()),
            "Scan timing dimensions",
        )
        native_positions = set()
        for p in cohort.itertuples():
            match = rounded_coordinate_matches(
                p.latitude, p.longitude, sparse["FP_latitude"], sparse["FP_longitude"]
            )
            require(len(match) == 1, "Unique native match for every prefix member")
            index = int(match[0])
            r, c = int(sparse["FP_line"][index]), int(sparse["FP_sample"][index])
            require((r, c) not in native_positions, "No duplicate native fire centers")
            native_positions.add((r, c))
            window = Window(c, r, 1, 1)
            value, flag = (
                int(mask.read(1, window=window).item()),
                int(qa.read(1, window=window).item()),
            )
            lng, lt = (
                float(lon.read(1, window=window).item()),
                float(lat.read(1, window=window).item()),
            )
            require(
                value == int(sparse["FP_confidence"][index]) == {"n": 8, "h": 9}[p.confidence],
                "Native mask/sparse/catalog confidence",
            )
            require(
                abs(lng - sparse["FP_longitude"][index]) <= 1e-5
                and abs(lt - sparse["FP_latitude"][index]) <= 1e-5,
                "Native orientation",
            )
            scan = r // 32
            interval = {
                n: (
                    pd.Timestamp("1993-01-01T00:00:00Z")
                    + pd.to_timedelta(float(t[scan]) - leap, unit="s")
                ).isoformat()
                for n, t in times.items()
            }
            records.append(
                {
                    "detection_id": p.detection_id,
                    "grid_id": p.grid_id,
                    "native_row": r,
                    "native_column": c,
                    "scan_index": scan,
                    **interval,
                    "fire_mask": value,
                    "qa": flag,
                    "input_low7": flag & 127,
                    "m13_non_nominal": bool(flag & (1 << 6)),
                    "geolocation_non_nominal": bool(flag & (1 << 5)),
                    "residual_bowtie": bool(flag & (1 << 22)),
                    "target": None,
                }
            )
    result_frame = pd.DataFrame(records)
    result_frame["target"] = pd.Series(float("nan"), index=result_frame.index)
    require(result_frame.target.isna().all(), "Targets remain unassigned")
    strict = result_frame.loc[result_frame.input_low7.eq(0)]
    summary = {
        "saved_same_minute_full_component_members": len(frame),
        "exact_anchor_prefix_members": len(cohort),
        "other_same_minute_full_component_members": len(excluded),
        "native_matches": len(records),
        "native_scans": result_frame.scan_index.nunique(),
        "catalog_first_cells": sorted(cohort.grid_id.unique()),
        "strict_low7_clear_count": len(strict),
        "strict_low7_removed_count": len(result_frame) - len(strict),
        "anchor_retained_by_strict_low7": ANCHOR in set(strict.detection_id),
        "m13_flag_count": int(result_frame.m13_non_nominal.sum()),
        "geolocation_flag_count": int(result_frame.geolocation_non_nominal.sum()),
        "residual_bowtie_count": int(result_frame.residual_bowtie.sum()),
        "confidence_mask_counts": {
            str(k): int(v) for k, v in result_frame.fire_mask.value_counts().items()
        },
        "low7_counts": {str(k): int(v) for k, v in result_frame.input_low7.value_counts().items()},
        "all_fields_nominal_is_not_proposed_positive_policy": True,
        "independent_all_pairs_prefix_check": True,
        "high_confidence_with_all_low7_clear": int(
            (result_frame.fire_mask.eq(9) & result_frame.input_low7.eq(0)).sum()
        ),
    }
    out = (
        BASE
        / "salur_prefix_quality_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    table = out / "native_prefix.csv"
    result_frame.to_csv(table, index=False)
    pd.testing.assert_frame_equal(result_frame, pd.read_csv(table), check_dtype=False)
    code = [
        Path(__file__),
        ROOT / "src/wildfire_risk_prediction/event_review.py",
        ROOT / "src/wildfire_risk_prediction/native_cover_context.py",
        ROOT / "scripts/firms/inspect_l2_observation_sample.py",
    ]
    result = {
        "scope": "one_frozen_Salur_prefix_quality_and_scan_diagnostic_only",
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "code_sha256": {p.relative_to(ROOT).as_posix(): digest(p) for p in code},
        "artifact_sha256": {table.name: digest(table)},
        "scenario": SCENARIO,
        "prefix_membership_sha256": signature,
        "summary": summary,
        "excluded_same_minute_ids": sorted(excluded.detection_id),
        "scan_intervals": result_frame[["scan_index", "scan_start_time", "scan_end_time"]]
        .drop_duplicates()
        .to_dict("records"),
        "counts_by_cell": result_frame.groupby("grid_id").size().to_dict(),
        "strict_clear_counts_by_cell": strict.groupby("grid_id").size().to_dict(),
        "gate": specification(),
        "labels_created": False,
        "first_cell_policy_changed": False,
        "model_trained": False,
        "final_merge_performed": False,
        "heldout_data_read": False,
    }
    require(
        not any(
            result["gate"][k]
            for k in ("positive_label_permitted", "negative_label_permitted", "model_ready")
        )
        and result["gate"]["daily_observation_status"] == "unknown",
        "Closed acceptance",
    )
    require(all(digest(p) == h for p, h in pins.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Report readback")
    print(path.relative_to(ROOT), digest(path))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
