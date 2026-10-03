"""Geometric union of verified approximate swath areas; never daily labels."""

import argparse
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

SPEC = importlib.util.spec_from_file_location(
    "area_estimate", Path(__file__).with_name("estimate_l2_observed_area.py")
)
area = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(area)
audit, OUTPUT = area.audit, area.OUTPUT


def classify_scan_interval(start, end, window_start, window_end):
    """Classify a scan envelope against the model's (T,T+24h] interval."""
    start, end, window_start, window_end = (
        pd.Timestamp(t) for t in (start, end, window_start, window_end)
    )
    audit.require(
        all(t.tzinfo is not None for t in (start, end, window_start, window_end)),
        "Timezone required",
    )
    audit.require(start.value < end.value and window_start.value < window_end.value, "Bad interval")
    if end.value <= window_start.value or start.value > window_end.value:
        return "outside"
    if start.value > window_start.value and end.value <= window_end.value:
        return "inside"
    return "boundary_unknown"


def combine(keys):
    parsed = [area.parse_key(k) for k in keys]
    audit.require(len(parsed) >= 2 and len(set(parsed)) == len(parsed), "Need distinct swaths")
    parts_path, parts = area.load_parts()
    reference = parts.grid_id.tolist()
    pieces = {g: [[] for _ in reference] for g in area.GROUPS}
    sensor_pieces, dates, sources, temporal_checks = {}, set(), {}, {}
    for sensor, key in parsed:
        stem = audit.sample_stem(sensor, key)
        rp = OUTPUT / f"{stem}_area_estimate.json"
        report = json.loads(rp.read_text(encoding="utf-8"))
        audit.require(report["sensor"] == sensor and report["pair_key"] == key, "Wrong report")
        audit.require(report["method"] == area.METHOD, "Area method mismatch")
        audit.require(not report["negative_label_permitted"], "Unexpected label permission")
        provenance = report["sources"]
        audit.require(provenance["aoi_parts_sha256"] == audit.digest(parts_path), "AOI changed")
        audit.require(
            provenance["script_sha256"] == audit.digest(Path(area.__file__)), "Stale area"
        )
        prior_path = OUTPUT / f"{stem}_audit.json"
        audit.require(
            audit.digest(prior_path) == provenance["previous_audit_sha256"], "Stale audit"
        )
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        audit.require(
            prior["script_sha256"] == audit.digest(Path(audit.__file__)), "Stale inspector"
        )
        for source in prior["sources"].values():
            audit.require(
                audit.digest(area.ROOT / source["path"]) == source["sha256"], "Raw changed"
            )
        dates.add(pd.Timestamp(prior["start_utc"]).date().isoformat())
        gpkg = OUTPUT / f"{stem}_area_estimate.gpkg"
        csv = OUTPUT / f"{stem}_area_estimate.csv"
        scans = OUTPUT / f"{stem}_scan_times.csv"
        for field, path in [
            ("geometry_sha256", gpkg),
            ("area_csv_sha256", csv),
            ("scan_times_sha256", scans),
        ]:
            audit.require(audit.digest(path) == provenance[field], "Saved area source changed")
        scan_table = pd.read_csv(scans)
        window_start = pd.Timestamp(prior["start_utc"]).normalize()
        window_end = pd.Timestamp(window_start.value + 86_400_000_000_000, unit="ns", tz="UTC")
        statuses = [
            classify_scan_interval(a, b, window_start, window_end)
            for a, b in zip(scan_table.start_utc, scan_table.end_utc, strict=True)
        ]
        temporal_checks[f"{sensor}:{key}"] = {
            "window_definition": "(T,T+24h]",
            "T_utc": window_start.isoformat(),
            "end_utc": window_end.isoformat(),
            "scan_interval_counts": pd.Series(statuses).value_counts().to_dict(),
            "limit": "Time-envelope check only; not continuous temporal coverage or labels",
        }
        table = pd.read_csv(csv).set_index("grid_id")
        audit.require(len(table) == len(reference) and table.index.is_unique, "Bad area keys")
        audit.require(table.negative_label_permitted.eq(False).all(), "Saved label permission")
        audit.require(table.daily_observation_status.eq("unknown").all(), "Saved daily status")
        sensor_pieces.setdefault(sensor, [[] for _ in reference])
        for group in area.GROUPS:
            frame = gpd.read_file(gpkg, layer=group)
            audit.require(frame.crs.to_epsg() == 6933, "Wrong area CRS")
            audit.require(
                frame.grid_id.is_unique and set(frame.grid_id) == set(reference),
                "Bad geometry keys",
            )
            frame = frame.set_index("grid_id").loc[reference]
            audit.require(
                np.allclose(
                    frame.geometry.area,
                    table.loc[reference, f"{group}_area_estimate_m2"],
                    rtol=1e-10,
                    atol=0.01,
                ),
                "Geometry/CSV area mismatch",
            )
            for i, geometry in enumerate(frame.geometry):
                if geometry is not None and not geometry.is_empty:
                    pieces[group][i].append(geometry)
                    if group == "nominal_nonfire_land":
                        sensor_pieces[sensor][i].append(geometry)
        sources[f"{sensor}:{key}"] = {"area_report_sha256": audit.digest(rp), **provenance}
    audit.require(len(dates) == 1, "Different training days cannot be combined")
    regions = parts.geometry.to_numpy()
    unions = {
        g: [area.union_clipped(p, r) for p, r in zip(items, regions, strict=True)]
        for g, items in pieces.items()
    }
    sensor_unions = {
        s: [area.union_clipped(p, r) for p, r in zip(items, regions, strict=True)]
        for s, items in sensor_pieces.items()
    }
    day = next(iter(dates))
    sensors = [s for s in ("SNPP", "N20") if s in sensor_unions]
    stem = f"l2_area_union_{day}_{'_'.join(sensors)}_{len(parsed)}samples"
    table, gpkg = area.write_area_output(stem, parts, unions)
    attribution = {
        s: float(sum(g.area for g in geometries) / 1e6) for s, geometries in sensor_unions.items()
    }
    if set(sensors) == {"SNPP", "N20"}:
        a, b = np.asarray(sensor_unions["SNPP"]), np.asarray(sensor_unions["N20"])
        attribution["N20_added_to_SNPP"] = float(shapely.area(shapely.difference(b, a)).sum() / 1e6)
        attribution["both_sensors_overlap"] = float(
            shapely.area(shapely.intersection(a, b)).sum() / 1e6
        )
        expected = attribution["SNPP"] + attribution["N20"] - attribution["both_sensors_overlap"]
        actual = table.nominal_nonfire_land_area_estimate_m2.sum() / 1e6
        audit.require(abs(expected - actual) < 1e-5, "Sensor union area identity failed")
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "day_utc": day,
        "method": area.METHOD,
        "status": "approximate_listed_swaths_union_only",
        "sample_keys": [f"{s}:{k}" for s, k in parsed],
        "grid_count": len(parts),
        "aoi_area_km2": float(table.aoi_area_m2.sum() / 1e6),
        "area_estimate_km2": {
            g: float(table[f"{g}_area_estimate_m2"].sum() / 1e6) for g in area.GROUPS
        },
        "nominal_nonfire_land_sensor_attribution_km2": attribution,
        "sources": sources,
        "temporal_checks": temporal_checks,
        "script_sha256": audit.digest(Path(__file__)),
        "geometry_sha256": audit.digest(gpkg),
        "area_csv_sha256": audit.digest(OUTPUT / f"{stem}.csv"),
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "limitations": [
            "Spatial union of approximate interiors; not all-day temporal observation",
            "Same-area repeats across scans/sensors counted once",
            "No exact official footprints, vegetation denominator, eligibility threshold or labels",
            "Scan time tables retained separately; no per-pixel temporal coverage certified",
        ],
    }
    destination = OUTPUT / f"{stem}.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair-keys", nargs="+", required=True)
    combine(parser.parse_args().pair_keys)
