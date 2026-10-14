"""Reconstruct retained training witness areas by native scan, time, QA and sensor/orbit."""

import hashlib
import importlib.util
import json
import socket
import uuid
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Transformer
from rasterio.windows import Window

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from wildfire_risk_prediction.feature_join import require, training_day
from wildfire_risk_prediction.observation_window import classify_intervals, loaded_envelope_metrics
from wildfire_risk_prediction.scan_support import read_scan_table, temporal_repeat_support

ROOT = Path(__file__).resolve().parents[2]
BASE = Path("outputs/reports/observation_coverage")
TIMING = "e2dd39df16edd27fbc54270ede9a5ab8f8aa5d517770168d501be3a9f1c4d361"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)
GROUPS = ("reconstructed_domain", "nominal_nonfire_land", "cloud")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline scan-area pilot")


def run():
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(
            path.resolve().is_relative_to(ROOT) and path.is_file() and not path.is_symlink(),
            "Project-local regular pilot source",
        )
        digest = sha(path)
        require(expected is None or digest == expected, "Pilot source hash changed")
        pins[path.relative_to(ROOT).as_posix()] = digest
        return path

    def report(name, expected=None):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    config = report("configs/scan_support_pilot_v1.json")
    require(
        config["status"] == "diagnostic_only_not_label_policy"
        and config["negative_label_permitted"] is False
        and config["daily_observation_status"] == "unknown"
        and config["different_sensor_orbit_required_for_repeat"] is True,
        "Diagnostic-only pilot configuration",
    )
    day = config["training_day"]
    training_day(day)
    require(
        day == "2019-01-14" and config["minimum_scan_gap_hours"] == [1, 6, 12],
        "Fixed training witness experiment",
    )
    parent = Path(config["selection_parent"])
    previous = report(parent / "readback.json", config["selection_parent_sha256"])
    require(previous["day_utc"] == day and not previous["labels_created"], "Training parent")
    selection_name = config["selection_artifact"]
    selected = pd.read_csv(
        retained(parent / selection_name, previous["artifact_sha256"][selection_name])
    )
    ids = selected.grid_id.tolist()
    require(len(ids) == len(set(ids)) == 3, "Three purpose-selected witnesses")
    timing = report(BASE / "observation_timing_2019-01-14.json", TIMING)
    require(
        timing["training_day"] == day and not timing["negative_label_permitted"],
        "Closed native timing reference",
    )
    retained("scripts/firms/audit_l2_observation_timing.py", timing["script_sha256"])
    for name, digest in timing["helpers"].items():
        retained(name, digest)
    protected = report(PROTECTED)
    for name, digest in protected.items():
        retained(name, digest)
    retained(Path(__file__).relative_to(ROOT))
    for name in ("scan_support.py", "feature_join.py", "observation_window.py"):
        retained("src/wildfire_risk_prediction/" + name)
    spec = importlib.util.spec_from_file_location(
        "retained_scan_timing", ROOT / "scripts/firms/audit_l2_observation_timing.py"
    )
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    area, audit = native.area, native.audit
    combined = report(
        BASE / "l2_area_union_2019-01-14_SNPP_N20_8samples.json",
        "d4598b888465069898543ec844b83b17fd24f65e36f9a5ff46eedcd5f6dea1cc",
    )
    parts_path = retained(
        "data/interim/grid_aoi_parts.geojson",
        next(iter(combined["sources"].values()))["aoi_parts_sha256"],
    )
    parts = gpd.read_file(parts_path).to_crs(6933).set_index("grid_id").loc[ids].reset_index()
    regions = parts.geometry.to_numpy()
    require(shapely.is_valid(regions).all() and (shapely.area(regions) > 0).all(), "Witness AOI")
    tree = shapely.STRtree(regions)
    west, south, east, north = parts.total_bounds
    projection = Transformer.from_crs(4326, 6933, always_xy=True)
    frames, shapes, inventory, reconciliation = [], {g: [] for g in GROUPS}, [], []
    for key, item in timing["sources"].items():
        sensor, pair = key.split(":")
        require(pair.startswith("2019014.") and sensor in {"SNPP", "N20"}, "Training source")
        paths = {}
        for role, source in item["sources"].items():
            paths[role] = retained(source["path"], source["sha256"])
            require(
                audit.product_identity(paths[role].name)[:3] == (sensor, role, pair),
                "Native source identity",
            )
        for name, digest in item["references"].items():
            retained(name, digest)
        stem = audit.sample_stem(sensor, pair)
        area_report = report(
            BASE / f"{stem}_area_estimate.json", combined["sources"][key]["area_report_sha256"]
        )
        reference = pd.read_csv(
            retained(BASE / f"{stem}_scan_times.csv", area_report["sources"]["scan_times_sha256"])
        )
        gpkg = retained(
            BASE / f"{stem}_area_estimate.gpkg", area_report["sources"]["geometry_sha256"]
        )
        expected = {
            g: gpd.read_file(gpkg, layer=g).set_index("grid_id").loc[ids].geometry.to_numpy()
            for g in GROUPS
        }
        scheduled = {r["scan_index"] for r in area_report["spatial_scan_diagnostics"]}
        per_scan = {g: {} for g in GROUPS}
        with warnings.catch_warnings(), ExitStack() as stack:
            warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
            mask, qa = (audit.layer(stack, paths["fire"], n) for n in ("fire_mask", "algorithm_QA"))
            lon, lat = (
                audit.layer(stack, paths["geolocation"], f"geolocation_data/{n}")
                for n in ("longitude", "latitude")
            )
            audit.validate_pair(paths["fire"], paths["geolocation"], mask.tags(), lat.tags())
            require(
                mask.shape == qa.shape == lon.shape == lat.shape and mask.height % 32 == 0,
                "Native dimensions",
            )
            require(mask.dtypes == ("uint8",) and qa.dtypes == ("uint32",), "Native mask/QA types")
            count = mask.height // 32
            raw = {
                n: audit.layer(stack, paths["geolocation"], f"scan_line_attributes/{n}")
                .read(1)
                .ravel()
                for n in (
                    "scan_start_time",
                    "scan_end_time",
                    "ev_mid_time",
                    "scan_quality",
                    "sensor_mode",
                )
            }
            require(
                all(len(a) == count for a in raw.values()) and len(reference) == count,
                "Full scan inventory",
            )
            require(all(0 <= s < count for s in scheduled), "Retained AOI scan schedule")
            offset = int(lat.tags()["TAI93_leapseconds"])
            start, end, mid = (
                area.tai93_utc(raw[n], offset)
                for n in ("scan_start_time", "scan_end_time", "ev_mid_time")
            )
            require(
                ((start < end) & (start <= mid) & (mid <= end)).all()
                and (np.diff(start.asi8) > 0).all(),
                "Acquisition order",
            )
            for name, values in (("start_utc", start), ("end_utc", end), ("ev_mid_utc", mid)):
                require(
                    np.array_equal(
                        pd.to_datetime(reference[name], utc=True).array.asi8, values.asi8
                    ),
                    "Native/retained acquisition time",
                )
            for name, values in (
                ("scan_index", np.arange(count)),
                ("geolocation_scan_quality", raw["scan_quality"]),
                ("sensor_mode", raw["sensor_mode"]),
            ):
                require(np.array_equal(reference[name], values), "Native/retained scan flags")
            orbit = int(lat.tags()["OrbitNumber"])
            require(orbit == item["orbit_number"] and orbit > 0, "Native sensor/orbit identity")
            flags = [native.scan_quality_fields(v) for v in raw["scan_quality"]]
            require(np.isin(raw["sensor_mode"], np.arange(7)).all(), "Sensor modes")
            for scan in sorted(scheduled):
                window = Window(0, scan * 32, mask.width, 32)
                longitudes, latitudes = lon.read(1, window=window), lat.read(1, window=window)
                valid = np.isfinite(longitudes) & np.isfinite(latitudes)
                valid &= (abs(longitudes) <= 180) & (abs(latitudes) <= 90)
                x, y = projection.transform(
                    np.where(valid, longitudes, np.nan), np.where(valid, latitudes, np.nan)
                )
                corners, eligible = area.interior_corners(x, y)
                low, high = np.min(corners, axis=-2), np.max(corners, axis=-2)
                candidate = eligible & (high[..., 0] >= west) & (low[..., 0] <= east)
                candidate &= (high[..., 1] >= south) & (low[..., 1] <= north)
                if not candidate.any():
                    continue
                polygons = shapely.polygons(corners[candidate])
                require(
                    shapely.is_valid(polygons).all() and (shapely.area(polygons) > 0).all(),
                    "Reconstructed scan interiors",
                )
                values = mask.read(1, window=window)[1:-1, 1:-1][candidate]
                quality = qa.read(1, window=window)[1:-1, 1:-1][candidate]
                require((values < 10).all(), "Mask classifications")
                classes = {
                    GROUPS[0]: np.ones(len(values), dtype=bool),
                    GROUPS[1]: audit.diagnostic_land(values, quality),
                    GROUPS[2]: values == 4,
                }
                pix, grid = tree.query(polygons, predicate="intersects")
                intersections = shapely.intersection(polygons[pix], regions[grid])
                positive = shapely.area(intersections) > 0
                for group, flag in classes.items():
                    for index in range(len(ids)):
                        keep = positive & (grid == index) & flag[pix]
                        if keep.any():
                            per_scan[group][scan, index] = shapely.union_all(intersections[keep])
            rows, local_shapes = [], {g: [] for g in GROUPS}
            for scan in range(count):
                for index, grid_id in enumerate(ids):
                    row = {
                        "grid_id": grid_id,
                        "sensor": sensor,
                        "pair_key": pair,
                        "scan_index": scan,
                        "scan_id": f"{key}:{scan}",
                        "orbit_id": f"{sensor}:{orbit}",
                        "start_utc": start[scan].isoformat(),
                        "end_utc": end[scan].isoformat(),
                        "geolocation_scan_quality": int(raw["scan_quality"][scan]),
                        "sensor_mode": int(raw["sensor_mode"][scan]),
                        **flags[scan],
                    }
                    for group in GROUPS:
                        geom = per_scan[group].get((scan, index), shapely.GeometryCollection())
                        row[group + "_m2"] = geom.area
                        local_shapes[group].append(geom)
                    rows.append(row)
            frame = pd.DataFrame(rows)
            frame["window_status"] = classify_intervals(frame, day)
            require(frame.window_status.eq("inside").all(), "Fixed native day envelopes")
            frame["daily_observation_status"], frame["negative_label_permitted"] = "unknown", False
            frames.append(frame)
            for group in GROUPS:
                arr = np.asarray(local_shapes[group], dtype=object)
                shapes[group].extend(arr)
                for index, grid_id in enumerate(ids):
                    fresh = shapely.union_all(arr[frame.grid_id.eq(grid_id)])
                    difference = fresh.symmetric_difference(expected[group][index]).area
                    require(
                        difference <= max(0.05, regions[index].area * 1e-8),
                        "Scan decomposition versus retained granule geometry",
                    )
                    reconciliation.append(
                        {
                            "grid_id": grid_id,
                            "swath_key": key,
                            "group": group,
                            "symmetric_difference_m2": difference,
                        }
                    )
            inventory.append(
                {
                    "swath_key": key,
                    "orbit_id": f"{sensor}:{orbit}",
                    "native_scan_count": count,
                    "retained_aoi_scan_count": len(scheduled),
                    "witness_domain_scan_grid_rows": int(frame[GROUPS[0] + "_m2"].gt(0).sum()),
                }
            )
        print("Native scan decomposition verified:", key, flush=True)

    scans = pd.concat(frames, ignore_index=True)
    require(not scans.duplicated(["grid_id", "scan_id"]).any(), "Complete unique scan lattice")
    arrays = {g: np.asarray(a, dtype=object) for g, a in shapes.items()}
    orbit_rows, summaries, repeats, pairs, repeat_geometry = [], [], [], [], []
    for index, grid_id in enumerate(ids):
        choose = scans.grid_id.eq(grid_id).to_numpy()
        frame = scans.loc[choose].reset_index(drop=True)
        geoms = {g: a[choose] for g, a in arrays.items()}
        union = {g: shapely.union_all(a) for g, a in geoms.items()}
        orbit_land = []
        for orbit_id in sorted(frame.orbit_id.unique()):
            take = frame.orbit_id.eq(orbit_id).to_numpy()
            areas = {g + "_m2": shapely.union_all(a[take]).area for g, a in geoms.items()}
            orbit_land.append(areas[GROUPS[1] + "_m2"])
            orbit_rows.append({"grid_id": grid_id, "orbit_id": orbit_id, **areas})
        support, witnesses = temporal_repeat_support(
            frame, geoms[GROUPS[1]], regions[index], day, config["minimum_scan_gap_hours"]
        )
        witnesses.insert(0, "grid_id", grid_id)
        pairs.append(witnesses)
        summary = {
            "grid_id": grid_id,
            "aoi_area_m2": regions[index].area,
            "daily_nominal_land_m2": union[GROUPS[1]].area,
            "best_sensor_orbit_land_m2": max(orbit_land),
            "land_supported_sensor_orbits": sum(a > 0 for a in orbit_land),
            "land_scan_longest_envelope_gap_hours": loaded_envelope_metrics(
                frame.loc[frame[GROUPS[1] + "_m2"].gt(0)], day
            )[1]
            / 3600,
            "daily_observation_status": "unknown",
            "negative_label_permitted": False,
        }
        original = selected.set_index("grid_id").loc[grid_id]
        require(
            abs(original.land_union_m2 - union[GROUPS[1]].area) <= 0.05,
            "Native scan union versus selected parent",
        )
        previous_area = regions[index].area
        for cut in sorted(support):
            geom = support[cut]
            require(
                geom.difference(union[GROUPS[1]]).area <= 0.05
                and geom.area <= previous_area + 0.05,
                "Nested temporal support areas",
            )
            previous_area = geom.area
            repeats.append(
                {
                    "grid_id": grid_id,
                    "minimum_gap_hours": cut,
                    "repeat_land_area_m2": geom.area,
                    "repeat_land_aoi_fraction": geom.area / regions[index].area,
                }
            )
            repeat_geometry.append(geom)
            summary[f"repeat_land_gap_{cut:g}h_m2"] = geom.area
        summaries.append(summary)
    out = (
        ROOT
        / "outputs/reports/dataset/scan_support_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    tables = {
        "scan_support.csv": scans,
        "orbit_support.csv": pd.DataFrame(orbit_rows),
        "grid_summary.csv": pd.DataFrame(summaries),
        "temporal_repeat.csv": pd.DataFrame(repeats),
        "repeat_pairs.csv": pd.concat(pairs, ignore_index=True),
        "scan_inventory.csv": pd.DataFrame(inventory),
        "reconciliation.csv": pd.DataFrame(reconciliation),
    }
    for name, frame in tables.items():
        path = out / name
        frame.to_csv(path, index=False)
        pd.testing.assert_frame_equal(
            frame.reset_index(drop=True),
            read_scan_table(path)
            if name == "scan_support.csv"
            else pd.read_csv(path, float_precision="round_trip"),
            check_dtype=False,
        )
        artifacts[name] = sha(path)
    keep = scans[GROUPS[0] + "_m2"].gt(0).to_numpy()
    geometry_path = out / "scan_support.gpkg"
    for group in GROUPS:
        frame = gpd.GeoDataFrame(
            scans.loc[keep, ["grid_id", "scan_id"]].reset_index(drop=True),
            geometry=arrays[group][keep],
            crs=6933,
        )
        frame.to_file(geometry_path, layer=group, driver="GPKG", index=False)
        saved = gpd.read_file(geometry_path, layer=group)
        require(
            saved.crs.to_epsg() == 6933
            and saved[["grid_id", "scan_id"]].equals(frame[["grid_id", "scan_id"]]),
            "Saved scan geometry keys/CRS",
        )
        require(
            (
                shapely.area(shapely.symmetric_difference(saved.geometry, frame.geometry)) <= 0.05
            ).all(),
            "Saved scan geometry readback",
        )
    artifacts[geometry_path.name] = sha(geometry_path)
    repeat_path = out / "repeat_support.gpkg"
    repeat_frame = gpd.GeoDataFrame(
        tables["temporal_repeat.csv"], geometry=repeat_geometry, crs=6933
    )
    repeat_frame.to_file(repeat_path, layer="repeat_support", driver="GPKG", index=False)
    saved = gpd.read_file(repeat_path, layer="repeat_support")
    require(
        np.allclose(
            saved.geometry.area,
            tables["temporal_repeat.csv"].repeat_land_area_m2,
            rtol=1e-10,
            atol=0.01,
        ),
        "Repeat area/geometry readback",
    )
    require(
        (shapely.area(shapely.symmetric_difference(saved.geometry, repeat_geometry)) <= 0.05).all(),
        "Repeat geometry position readback",
    )
    artifacts[repeat_path.name] = sha(repeat_path)
    fig, ax = plt.subplots(figsize=(11, 5))
    fig.subplots_adjust(bottom=0.28, top=0.82, left=0.08, right=0.98)
    summary = tables["grid_summary.csv"]
    columns = [
        ("daily_nominal_land_m2", "Daily union"),
        ("best_sensor_orbit_land_m2", "Best sensor/orbit"),
        *[(f"repeat_land_gap_{h}h_m2", f"Repeat >= {h} h") for h in (1, 6, 12)],
    ]
    for i, (col, label) in enumerate(columns):
        ax.bar(
            np.arange(3) + (i - 2) * 0.16,
            summary[col] / summary.aoi_area_m2,
            width=0.16,
            label=label,
        )
    ax.set(
        xticks=np.arange(3),
        xticklabels=[s.replace("E6933_5K_V1_", "") for s in ids],
        ylabel="Fraction of AOI-clipped cell",
        ylim=(0, 1.05),
        title=(
            "2019-01-14: three purpose-selected spatial witnesses\n"
            "Repeat: shared land, distinct sensor/orbit, separated scan envelopes"
        ),
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, fontsize=8)
    fig.text(
        0.5,
        0.02,
        "Approximate scan interiors; illustrative time cuts, no label admission.",
        ha="center",
        fontsize=8,
    )
    path = out / "support_by_time.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    artifacts[path.name] = sha(path)
    result = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "passed_diagnostic_only",
        "training_day": day,
        "selected_grids": ids,
        "listed_granules": len(inventory),
        "distinct_sensor_orbits": scans.orbit_id.nunique(),
        "native_scan_grid_rows": len(scans),
        "nonempty_domain_scan_grid_rows": int(keep.sum()),
        "reconciliation_checks": len(reconciliation),
        "grid_results": summaries,
        "geolocation_scan_quality_histogram": {
            str(k): v
            for k, v in scans.drop_duplicates("scan_id")
            .geolocation_scan_quality.value_counts()
            .to_dict()
            .items()
        },
        "input_sha256": pins,
        "artifact_sha256": artifacts,
        "protected_inputs_verified": len(protected),
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
        "model_ready": False,
        "final_merge_performed": False,
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "limitations": [
            "Three purpose-selected cells on one training day, no error-rate inference",
            "Scan geometry is approximate and times are acquisition envelopes",
            "Native AOI scan schedule reused and checked against retained unions",
            "Nominal input QA land only; geo quality retained, no new exclusion rule",
            "No new completeness claim for neighbouring source days or habitat area",
            "Repeat hour cuts are diagnostic, not a negative policy",
        ],
    }
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Native pilot input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Pilot report readback")
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Native pilot artifact closure")
    completion = {
        "status": "passed",
        "report_sha256": sha(path),
        "inputs_verified": len(pins),
        "artifacts_verified": len(artifacts),
    }
    (out / "completion_readback.json").write_text(
        json.dumps(completion, indent=2) + "\n", encoding="utf-8"
    )
    print("Scan-area-time result:", out.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
