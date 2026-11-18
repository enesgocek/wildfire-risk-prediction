"""Inspect approximate native pixel footprints at a reported Mersin coordinate."""

import importlib.util
import json
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from uuid import uuid4

import numpy as np
import pandas as pd
import rasterio
import shapely
from audit_mersin_open_incidents import ARCHIVE, GRID, PINS, PROVINCES, ROOT, read_incidents
from audit_stage_one_selection import verify
from pyproj import Transformer
from rasterio.windows import Window

from wildfire_risk_prediction.core_transfer import check_file, digest
from wildfire_risk_prediction.feature_join import require

PLAN = ROOT / (
    "outputs/reports/dataset/observation_core_transfer_v1/"
    "20261117T205200Z_ec3e6131/native_plan.json"
)


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/firms" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def context(polygons, mask, nominal_land, point, radius):
    """Union overlapping footprints before computing local class fractions."""
    circle = point.buffer(radius)
    clipped = shapely.intersection(polygons, circle)
    union = shapely.union_all(clipped)
    fractions = {
        str(code): float(shapely.union_all(clipped[mask == code]).area / circle.area)
        for code in range(10)
    }
    return {
        "radius_m": radius,
        "domain_fraction": float(union.area / circle.area),
        "class_fractions": fractions,
        "nominal_land_fraction": float(shapely.union_all(clipped[nominal_land]).area / circle.area),
        "point_mask_codes": sorted(set(map(int, mask[shapely.covers(polygons, point)]))),
        "point_nominal_land": bool((shapely.covers(polygons, point) & nominal_land).any()),
    }


def main():
    native = load_script("run_observation_core_pair")
    plan, pair = native.load_plan(PLAN)
    require(pair["sample_id"] == "N20:2021228.2312", "Fixed selected source")
    accepted = []
    for folder in native.OUTPUT.iterdir():
        result, done = folder / "native_probe.json", folder / "completion_readback.json"
        if not (result.is_file() and done.is_file()):
            continue
        report = json.loads(result.read_bytes())
        if report.get("plan_sha256") == digest(PLAN):
            require(
                digest(result) == json.loads(done.read_bytes())["report_sha256"],
                "Native completion receipt",
            )
            require(
                report["status"] == "one_pair_bytes_and_headers_passed", "Accepted native headers"
            )
            accepted.append(result)
    if not accepted:
        print("PENDING completed Earthdata transfer for the selected pair")
        return
    for path in (ARCHIVE, GRID, PROVINCES):
        verify(path, PINS[path])
    cache = ROOT / "data/raw/observation_core_v1" / digest(PLAN)[:16]
    for source in pair["sources"]:
        check_file(cache / source["filename"], source)
    native.native_headers(pair, cache)
    events, _ = read_incidents()
    event = events.loc["WF1487"]
    transform = Transformer.from_crs(4326, 6933, always_xy=True)
    point = shapely.Point(*transform.transform(float(event.longitude), float(event.latitude)))
    area = load_script("estimate_l2_observed_area")
    inspector = area.audit
    paths = {s["role"]: cache / s["filename"] for s in pair["sources"]}
    evidence = []
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask, qa = (inspector.layer(stack, paths["fire"], n) for n in ("fire_mask", "algorithm_QA"))
        lon, lat = (
            inspector.layer(stack, paths["geolocation"], "geolocation_data/" + n)
            for n in ("longitude", "latitude")
        )
        leap = int(lat.tags()["TAI93_leapseconds"])
        times = {
            name: area.tai93_utc(
                inspector.layer(stack, paths["geolocation"], "scan_line_attributes/" + field)
                .read(1)
                .ravel(),
                leap,
            )
            for name, field in (("start", "scan_start_time"), ("end", "scan_end_time"))
        }
        quality_fields = {
            name: inspector.layer(stack, paths["geolocation"], "scan_line_attributes/" + name)
            .read(1)
            .ravel()
            for name in ("scan_quality", "sensor_mode")
        }
        require(
            mask.height % 32 == 0 and mask.height // 32 == len(times["start"]),
            "Complete scan timing",
        )
        require(
            all(len(v) == len(times["start"]) for v in quality_fields.values()),
            "Complete scan quality metadata",
        )
        require(
            (
                (times["start"] > pd.Timestamp("2021-08-16T21:30:00Z"))
                & (times["end"] <= pd.Timestamp("2021-08-17T00:00:00Z"))
            ).all(),
            "All loaded scans after stated time and within target window",
        )
        bounds = point.buffer(1000).bounds
        for scan in range(mask.height // 32):
            window = Window(0, scan * 32, mask.width, 32)
            lng, lt = lon.read(1, window=window), lat.read(1, window=window)
            valid = np.isfinite(lng) & np.isfinite(lt) & (abs(lng) <= 180) & (abs(lt) <= 90)
            x, y = transform.transform(np.where(valid, lng, np.nan), np.where(valid, lt, np.nan))
            quads, eligible = area.interior_corners(x, y)
            low, high = np.min(quads, axis=-2), np.max(quads, axis=-2)
            use = eligible & (high[..., 0] >= bounds[0]) & (low[..., 0] <= bounds[2])
            use &= (high[..., 1] >= bounds[1]) & (low[..., 1] <= bounds[3])
            if not use.any():
                continue
            polygons = shapely.polygons(quads[use])
            require(shapely.is_valid(polygons).all(), "Valid local footprints")
            values = mask.read(1, window=window)[1:-1, 1:-1][use]
            quality = qa.read(1, window=window)[1:-1, 1:-1][use]
            require(np.isin(values, range(10)).all(), "Known mask classes")
            nominal = inspector.diagnostic_land(values, quality)
            evidence.append(
                {
                    "scan_index": scan,
                    "start_utc": times["start"][scan].isoformat(),
                    "end_utc": times["end"][scan].isoformat(),
                    "geolocation_scan_quality": int(quality_fields["scan_quality"][scan]),
                    "sensor_mode": int(quality_fields["sensor_mode"][scan]),
                    "contexts": [context(polygons, values, nominal, point, r) for r in (250, 1000)],
                }
            )
    result = {
        "archive_row": "WF1487",
        "sample_id": pair["sample_id"],
        "geometry_method": area.METHOD,
        "coordinate_basis": "published_archive_point_start_location_unverified",
        "archive_sha256": digest(ARCHIVE),
        "code_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p)
            for p in (
                ROOT / "scripts/quality/audit_mersin_point_pixels.py",
                ROOT / "scripts/firms/estimate_l2_observed_area.py",
                ROOT / "scripts/firms/inspect_l2_observation_sample.py",
            )
        },
        "scans_examined": mask.height // 32,
        "local_scan_contexts": evidence,
        "plan_sha256": digest(PLAN),
        "native_receipt_sha256": {p.relative_to(ROOT).as_posix(): digest(p) for p in accepted},
        "source_sha256": {s["filename"]: s["sha256"] for s in pair["sources"]},
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "labels_created": False,
    }
    for source in pair["sources"]:
        check_file(cache / source["filename"], source)
    out = (
        ROOT
        / "outputs/reports/dataset/mersin_point_pixels_v1"
        / (f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}")
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Point receipt roundtrip")
    print(json.dumps(result, indent=2))
    print(path.relative_to(ROOT), digest(path))


if __name__ == "__main__":
    main()
