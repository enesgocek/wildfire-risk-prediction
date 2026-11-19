"""Offline point/area diagnostics for one frozen source row and a verified native pair."""

import argparse
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
import shapely
from audit_mersin_point_pixels import context, load_script
from pyproj import Transformer, network
from rasterio.windows import Window

from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SAMPLE = BASE / "source_sampling_review_v1/20261119T133150Z_f94ebe6e/readback.json"
SAMPLE_SHA = "9647a69248ac158aad6f7a864b48bfad8eb61860be08ff3250f8dc643cd4d453"
DEFAULT_PLAN = BASE / "observation_core_transfer_v1/20261119T133754Z_a9bf9118/native_plan.json"
DEFAULT_PROBE = BASE / "observation_core_native_v1/20261119T134819Z_b9d99fad/native_probe.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-row", default="WF1206")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--probe", type=Path, default=DEFAULT_PROBE)
    args = parser.parse_args()

    def deny(*a, **kw):
        raise RuntimeError("Offline source-point review")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    network.set_network_enabled(False)
    plan_path, probe_path = args.plan.resolve(), args.probe.resolve()
    require(
        probe_path.is_relative_to(BASE / "observation_core_native_v1"), "Contained native receipt"
    )
    require(digest(SAMPLE) == SAMPLE_SHA, "Frozen ten-row source frame")
    source = json.loads(SAMPLE.read_text(encoding="utf-8"))
    selected = [r for r in source["intake"] if r["archive_row"] == args.archive_row]
    require(len(selected) == 1, "Exactly one frozen source row")
    selected = selected[0]
    require(
        2018 <= selected["year"] <= 2022 and len(selected["candidate_grid_ids"]) == 1,
        "Fit-role, spatially prepared source row",
    )
    runner = load_script("run_observation_core_pair")
    plan, pair = runner.load_plan(plan_path)
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    completion = probe_path.parent / "completion_readback.json"
    require(
        digest(probe_path) == json.loads(completion.read_text(encoding="utf-8"))["report_sha256"]
        and probe["plan_sha256"] == digest(plan_path)
        and probe["status"] == "one_pair_bytes_and_headers_passed",
        "Completed exact pair",
    )
    require(
        plan.get("source_review_archive_row", "WF1206") == args.archive_row, "Plan/row identity"
    )
    cache = ROOT / probe["cache_directory"]
    require(
        cache.resolve() == ROOT / "data/raw/observation_core_v1" / digest(plan_path)[:16],
        "Expected dedicated cache",
    )
    paths = {s["role"]: cache / s["filename"] for s in pair["sources"]}
    for s in pair["sources"]:
        check_file(paths[s["role"]], s)
    runner.native_headers(pair, cache)
    area = load_script("estimate_l2_observed_area")
    inspector = area.audit
    require(
        all(inspector.product_identity(p.name)[3].year <= 2022 for p in paths.values()),
        "Fit-role files",
    )
    project = Transformer.from_crs(4326, 6933, always_xy=True)
    point = shapely.Point(*project.transform(selected["longitude"], selected["latitude"]))
    evidence = []
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask, qa = (inspector.layer(stack, paths["fire"], n) for n in ("fire_mask", "algorithm_QA"))
        lon, lat = (
            inspector.layer(stack, paths["geolocation"], "geolocation_data/" + n)
            for n in ("longitude", "latitude")
        )
        leap = int(lat.tags()["TAI93_leapseconds"])
        timing = {
            name: area.tai93_utc(
                inspector.layer(stack, paths["geolocation"], "scan_line_attributes/" + field)
                .read(1)
                .ravel(),
                leap,
            )
            for name, field in (("start", "scan_start_time"), ("end", "scan_end_time"))
        }
        quality = {
            name: inspector.layer(stack, paths["geolocation"], "scan_line_attributes/" + name)
            .read(1)
            .ravel()
            for name in ("scan_quality", "sensor_mode")
        }
        require(
            mask.height % 32 == 0
            and all(len(v) * 32 == mask.height for v in [*timing.values(), *quality.values()]),
            "Complete scan metadata",
        )
        bounds = point.buffer(1000).bounds
        for scan in range(mask.height // 32):
            window = Window(0, scan * 32, mask.width, 32)
            lng, lt = lon.read(1, window=window), lat.read(1, window=window)
            valid = np.isfinite(lng) & np.isfinite(lt) & (abs(lng) <= 180) & (abs(lt) <= 90)
            x, y = project.transform(np.where(valid, lng, np.nan), np.where(valid, lt, np.nan))
            corners, eligible = area.interior_corners(x, y)
            low, high = np.min(corners, axis=-2), np.max(corners, axis=-2)
            use = eligible & (high[..., 0] >= bounds[0]) & (low[..., 0] <= bounds[2])
            use &= (high[..., 1] >= bounds[1]) & (low[..., 1] <= bounds[3])
            if not use.any():
                continue
            polygons = shapely.polygons(corners[use])
            require(shapely.is_valid(polygons).all(), "Valid local approximate support")
            raw_mask, raw_qa = mask.read(1, window=window), qa.read(1, window=window)
            values, flags = raw_mask[1:-1, 1:-1][use], raw_qa[1:-1, 1:-1][use]
            require(np.isin(values, range(10)).all(), "Known mask codes")
            distances = np.where(valid, (x - point.x) ** 2 + (y - point.y) ** 2, np.inf)
            r, c = np.unravel_index(distances.argmin(), distances.shape)
            evidence.append(
                {
                    "scan_index": scan,
                    "start_utc": timing["start"][scan].isoformat(),
                    "end_utc": timing["end"][scan].isoformat(),
                    "scan_quality": int(quality["scan_quality"][scan]),
                    "sensor_mode": int(quality["sensor_mode"][scan]),
                    "contexts": [
                        context(
                            polygons,
                            values,
                            inspector.diagnostic_land(values, flags),
                            point,
                            radius,
                        )
                        for radius in (250, 1000)
                    ],
                    "nearest_native_pixel": {
                        "row": int(scan * 32 + r),
                        "column": int(c),
                        "projected_distance_m": float(np.sqrt(distances[r, c])),
                        "mask_code": int(raw_mask[r, c]),
                        "qa_raw": int(raw_qa[r, c]),
                        "mask_neighbour_codes": sorted(
                            set(
                                map(
                                    int,
                                    raw_mask[max(0, r - 1) : r + 2, max(0, c - 1) : c + 2].ravel(),
                                )
                            )
                        ),
                    },
                    "clock_context": [
                        {
                            "basis": h["basis"],
                            "minutes_scan_start_after_report": (
                                timing["start"][scan] - pd.Timestamp(h["reported_time_utc"])
                            ).total_seconds()
                            / 60,
                            "is_detection_latency_measurement": False,
                        }
                        for h in selected["clock_hypotheses"]
                    ],
                }
            )
    out = (
        BASE
        / "source_sample_point_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    inputs = {
        p.relative_to(ROOT).as_posix(): digest(p)
        for p in [SAMPLE, plan_path, probe_path, completion, *paths.values()]
    }
    result = {
        "scope": "one_frozen_source_row_single_swath_diagnostic_only",
        "archive_row": args.archive_row,
        "sample_id": pair["sample_id"],
        "source_row": selected,
        "geometry_method": area.METHOD,
        "scans_examined": mask.height // 32,
        "local_scan_contexts": evidence,
        "source_coordinate_start_role_verified": False,
        "source_clock_standard_verified": False,
        "fire_still_active_at_scan_verified": False,
        "official_pixel_corners": False,
        "L_memberships_created": 0,
        "labels_created": False,
        "gate": specification(),
        "model_trained": False,
        "final_merge_performed": False,
        "network_used": False,
        "input_sha256": inputs,
        "code_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in [
                Path(__file__),
                ROOT / "scripts/quality/audit_mersin_point_pixels.py",
                ROOT / "scripts/firms/estimate_l2_observed_area.py",
                ROOT / "scripts/firms/inspect_l2_observation_sample.py",
            ]
        },
    }
    require(all(digest(ROOT / p) == h for p, h in inputs.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == result, "Readback")
    print(path.relative_to(ROOT).as_posix(), digest(path))
    print("PASS source point diagnostic; no fire label or L assignment")


if __name__ == "__main__":
    main()
