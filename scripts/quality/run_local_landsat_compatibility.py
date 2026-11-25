"""Run only the authorized one-cell local Landsat diagnostic, never feature admission."""

import argparse
import csv
import json
import math
import subprocess
import sys
import warnings
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import numpy as np
import rasterio
from affine import Affine
from pyproj import Transformer
from rasterio.warp import Resampling, reproject, transform_bounds
from rasterio.windows import Window, from_bounds
from shapely.geometry import box, shape
from shapely.ops import transform

from wildfire_risk_prediction import landsat_local_pilot as local
from wildfire_risk_prediction.core_transfer import digest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
DECISION = ROOT / "configs/local_landsat_compatibility_pilot_execution_v1.json"
PROPOSAL = ROOT / "configs/local_landsat_compatibility_pilot_proposal_v1.json"


def save(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def work(out):
    decision = json.loads(DECISION.read_bytes())
    continuation_path = ROOT / "configs/local_landsat_compatibility_continuation_v1.json"
    continuation = json.loads(continuation_path.read_bytes())
    previous = ROOT / continuation["previous_directory"]
    local.require(
        digest(previous / "network_checkpoint.json") == continuation["previous_network_sha256"],
        "previous_network_identity",
    )
    local.require(
        digest(previous / "public_scene_inventory.json") == continuation["previous_catalog_sha256"],
        "previous_catalog_identity",
    )
    decision["prior_probe_body_bytes"] = continuation["prior_body_bytes"]
    decision["prior_probe_request_attempts"] = continuation["prior_requests"]
    proposal = json.loads(PROPOSAL.read_bytes())
    local.require(digest(PROPOSAL) == decision["proposal_sha256"], "proposal_identity")
    pins = {
        DECISION: digest(DECISION),
        PROPOSAL: digest(PROPOSAL),
        Path(__file__): digest(Path(__file__)),
        Path(local.__file__): digest(Path(local.__file__)),
    }
    for relative, expected in proposal["reference_method_code_sha256"].items():
        path = ROOT / relative
        local.require(digest(path) == expected, "reference_code_changed")
        pins[path] = expected
    geometry_path = ROOT / "data/interim/grid_aoi_parts.geojson"
    pins[geometry_path] = digest(geometry_path)
    item = next(
        x
        for x in json.loads(geometry_path.read_bytes())["features"]
        if x["properties"]["grid_id"] == proposal["cell"]
    )
    geo = shape(item["geometry"])
    projected = transform(Transformer.from_crs(4326, 6933, always_xy=True).transform, geo)
    x0, y0, x1, y1 = projected.bounds
    left, top = math.floor(x0 / 30) * 30, math.ceil(y1 / 30) * 30
    width, height = math.ceil((x1 - left) / 30), math.ceil((top - y0) / 30)
    affine = Affine(30, 0, left, 0, -30, top)
    weights = np.array(
        [
            [
                projected.intersection(
                    box(left + c * 30, top - (r + 1) * 30, left + (c + 1) * 30, top - r * 30)
                ).area
                for c in range(width)
            ]
            for r in range(height)
        ]
    )
    np.savez_compressed(out / "candidate_AOI_weights.npz", area_m2=weights)
    http, proxy = local.BudgetHTTP(decision, out), None
    results, catalog, scene_arrays = [], [], {}
    status, stop = "pilot_not_completed", None
    try:
        all_scenes = []
        catalog = json.loads((previous / "public_scene_inventory.json").read_bytes())
        for record in catalog:
            stamp = datetime.fromisoformat(record["datetime"])
            year = record["year"]
            target = datetime(year, 7, 1, tzinfo=UTC)
            local.require(
                year in (2022, 2024) and target - timedelta(days=60) <= stamp < target,
                "retained_scene_time",
            )
            scene = {
                "id": record["id"],
                "assets": {k: {"href": v} for k, v in record["assets"].items()},
            }
            all_scenes.append((year, scene, stamp))
        print("Reused complete retained scene lists:", len(all_scenes), flush=True)
        local.require(0 < len(all_scenes) <= decision["max_unique_scenes"], "scene_count_bound")
        save(out / "public_scene_inventory.json", catalog)
        save(
            out / "candidate_target_grid.json",
            {
                "crs": "EPSG:6933",
                "affine": list(affine)[:6],
                "shape": [height, width],
                "origin_zero_is_hypothesis_not_old_grid_acceptance": True,
                "AOI_area_m2": float(projected.area),
                "weights_sum_m2": float(weights.sum()),
            },
        )
        proxy = local.ProcessProxy(
            http,
            [
                scene["assets"][key]["href"]
                for _, scene, _ in all_scenes
                for key in proposal["asset_keys_to_verify"]
            ],
        )
        with rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            GDAL_HTTP_MAX_RETRY=0,
            GDAL_HTTP_TIMEOUT=20,
            CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
            VSI_CACHE="FALSE",
        ):
            for year, scene, stamp in all_scenes:
                native, source_transform, source_crs, window = {}, None, None, None
                for key in proposal["asset_keys_to_verify"]:
                    http.check()
                    url = proxy.url(scene["assets"][key]["href"])
                    with rasterio.open(url) as source:
                        local.require(
                            source.count == 1 and source.crs is not None,
                            "one_georeferenced_band_required",
                        )
                        if window is None:
                            bb = transform_bounds(4326, source.crs, *geo.bounds, densify_pts=21)
                            tentative = from_bounds(*bb, transform=source.transform)
                            c0, r0 = (
                                max(0, math.floor(tentative.col_off) - 2),
                                max(0, math.floor(tentative.row_off) - 2),
                            )
                            c1, r1 = (
                                min(
                                    source.width, math.ceil(tentative.col_off + tentative.width) + 2
                                ),
                                min(
                                    source.height,
                                    math.ceil(tentative.row_off + tentative.height) + 2,
                                ),
                            )
                            local.require(c1 > c0 and r1 > r0, "empty_native_window")
                            window = Window(c0, r0, c1 - c0, r1 - r0)
                            source_transform, source_crs = (
                                source.window_transform(window),
                                source.crs,
                            )
                        local.require(
                            source.crs == source_crs
                            and source.window_transform(window) == source_transform,
                            "native_band_grids_disagree",
                        )
                        native[key] = source.read(1, window=window, masked=False)
                ndvi, ndmi = local.native_indices(
                    native["red"],
                    native["nir08"],
                    native["swir16"],
                    native["qa_pixel"],
                    native["qa_radsat"],
                )
                destination = []
                for index in (ndvi, ndmi):
                    dest = np.full((height, width), np.nan)
                    reproject(
                        index,
                        dest,
                        src_transform=source_transform,
                        src_crs=source_crs,
                        src_nodata=np.nan,
                        dst_transform=affine,
                        dst_crs="EPSG:6933",
                        dst_nodata=np.nan,
                        resampling=Resampling.nearest,
                    )
                    destination.append(dest)
                name = scene["id"] + "_diagnostic.npz"
                np.savez_compressed(out / name, ndvi=destination[0], ndmi=destination[1])
                scene_arrays[scene["id"]] = (year, stamp, *destination)
                print("Scene window read:", scene["id"], "body bytes", http.bytes, flush=True)
        for year in (2022, 2024):
            target = datetime(year, 7, 1, tzinfo=UTC)
            for days in (30, 60):
                chosen = [
                    x
                    for x in scene_arrays.values()
                    if x[0] == year and target - timedelta(days=days) <= x[1] < target
                ]
                local.require(chosen, "empty_window_no_feature_admitted")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    ndvi = np.nanmedian(np.stack([x[2] for x in chosen]), axis=0)
                    ndmi = np.nanmedian(np.stack([x[3] for x in chosen]), axis=0)
                valid = np.isfinite(ndvi) & np.isfinite(ndmi)
                support = float(weights[valid].sum())
                results.append(
                    {
                        "year": year,
                        "window_days": days,
                        "scenes": len(chosen),
                        "local_support_m2": support,
                        "local_ndvi": float(np.sum(ndvi[valid] * weights[valid]) / support)
                        if support
                        else None,
                        "local_ndmi": float(np.sum(ndmi[valid] * weights[valid]) / support)
                        if support
                        else None,
                        "feature_admitted": False,
                        "grid_and_area_rule_equivalence_accepted": False,
                    }
                )
        reference_dir = ROOT / "data/interim/vegetation/full_grid_v1/2022-07-01_b64"
        manifest_path = reference_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        pins[manifest_path] = digest(manifest_path)
        table_path = reference_dir / "snapshots.csv"
        local.require(digest(table_path) == manifest["table_sha256"], "old_snapshot_identity")
        pins[table_path] = manifest["table_sha256"]
        with table_path.open(encoding="utf-8", newline="") as handle:
            reference = [r for r in csv.DictReader(handle) if r["grid_id"] == proposal["cell"]]
        for row in results:
            if row["year"] == 2022:
                old = next(x for x in reference if int(x["window_days"]) == row["window_days"])
                row.update(
                    {
                        "old_support_m2": float(old["valid_area_m2"]),
                        "old_ndvi": float(old["ndvi_median_mean"]),
                        "old_ndmi": float(old["ndmi_median_mean"]),
                        "ndvi_local_minus_old": row["local_ndvi"] - float(old["ndvi_median_mean"])
                        if row["local_ndvi"] is not None
                        else None,
                        "ndmi_local_minus_old": row["local_ndmi"] - float(old["ndmi_median_mean"])
                        if row["local_ndmi"] is not None
                        else None,
                    }
                )
        save(out / "diagnostic_summaries.json", results)
        status = "local_access_and_diagnostic_composites_complete_equivalence_not_accepted"
    except Exception as exc:
        stop = (
            proxy.last_stop
            if proxy and proxy.last_stop
            else str(exc)
            if isinstance(exc, local.PilotStop)
            else type(exc).__name__
        )
        status = "pilot_stopped_outputs_retained"
    finally:
        if proxy:
            proxy.close()
        local.require(all(digest(p) == h for p, h in pins.items()), "input_closure")
        result = {
            "status": status,
            "stop_code": stop,
            "analysis_date": "2026-11-25",
            "global_elapsed_seconds": (datetime.now(UTC) - http.start).total_seconds(),
            "body_bytes_including_prior_probe": http.bytes,
            "requests_including_prior_probes": http.requests,
            "scene_count": len(catalog),
            "diagnostic_summary_count": len(results),
            "reference_equivalence_accepted": False,
            "new_features_or_labels_admitted": False,
            "new_model_training_or_prediction": False,
            "final_merge": False,
            "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
            "artifact_sha256": {
                p.name: digest(p) for p in out.iterdir() if p.is_file() and p.name != "child.log"
            },
            "producer_sha256": digest(Path(__file__)),
        }
        save(out / "readback.json", result)
        print(status, stop or "", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker:
        out = args.worker.resolve()
        local.require(out.is_relative_to(BASE / "local_landsat_compatibility_v1"), "output_scope")
        work(out)
        return
    out = (
        BASE
        / "local_landsat_compatibility_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    decision = json.loads(DECISION.read_bytes())
    remaining = (
        decision["max_seconds"]
        - (
            datetime.now(UTC) - datetime.fromisoformat(decision["original_probe_start_utc"])
        ).total_seconds()
    )
    local.require(remaining > 0, "original_pilot_time_limit")
    print(out.relative_to(ROOT).as_posix(), flush=True)
    with (out / "child.log").open("w", encoding="utf-8") as log:
        try:
            child = subprocess.run(
                [sys.executable, str(Path(__file__)), "--worker", str(out)],
                cwd=ROOT,
                stdout=log,
                stderr=log,
                timeout=remaining,
                check=False,
            )
            receipt = {
                "status": "child_completed"
                if child.returncode == 0
                else "child_failed_outputs_retained",
                "returncode": child.returncode,
            }
        except subprocess.TimeoutExpired:
            receipt = {"status": "original_pilot_timeout_outputs_retained"}
    receipt["closed_child_log_sha256"] = digest(out / "child.log")
    save(out / "launcher_receipt.json", receipt)
    print(receipt["status"], flush=True)


if __name__ == "__main__":
    main()
