"""Daily diagnostics from validated swaths; no official footprints or labels.

Spatial union uses all interiors of nominal-date granules. Boundary scans remain
unresolved; temporal center metrics separately use wholly inside (T,T+24h].
"""

import importlib.util
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "compact_summer", Path(__file__).with_name("run_l2_summer.py")
)
summer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(summer)
timing, area, audit = summer.timing, summer.area, summer.audit
require, digest = audit.require, audit.digest
NAMES = ("area.csv", "centers.csv", "scan_grid.csv", "scans.csv", "report.json")


def union_arrays(arrays, domains):
    require(len(arrays) > 0 and all(len(a) == len(domains) for a in arrays), "Union dimensions")
    values = shapely.intersection(shapely.union_all(np.stack(arrays), axis=0), domains)
    require(shapely.is_valid(values).all(), "Invalid daily union")
    measured, limits = shapely.area(values), shapely.area(domains)
    require((measured >= 0).all() and (measured <= limits + 0.1).all(), "Daily union bounds")
    return values


def sweep(intervals, begin, finish):
    events = defaultdict(int, {begin: 0, finish: 0})
    for start, end in intervals:
        require(begin < start < end <= finish, "Only wholly inside envelopes")
        events[start] += 1
        events[end] -= 1
    active = union = longest = gap = 0
    previous = begin
    for stamp, delta in sorted(events.items()):
        duration = stamp - previous
        if active:
            union += duration
            gap = 0
        else:
            gap += duration
            longest = max(longest, gap)
        active += delta
        require(active >= 0, "Envelope ordering")
        previous = stamp
    require(active == 0, "Unclosed envelopes")
    return union / 1e9, longest / 1e9


def validate_day(output, day, expected_ids, expected_context=None):
    report = json.loads((output / "report.json").read_text())
    require(
        report["day"] == day
        and report["negative_label_permitted"] is False
        and report["daily_observation_status"] == "unknown",
        "Daily identity/policy",
    )
    require(
        report["method"] == area.METHOD and report["compact_code_sha256"] == digest(Path(__file__)),
        "Daily code/method",
    )
    require(
        set(report["pair_ids"]) == set(expected_ids)
        and len(report["pair_ids"]) == len(set(expected_ids)),
        "Daily pair set",
    )
    if expected_context is not None:
        require(report["context"] == expected_context, "Daily lineage")
    require(set(report["outputs_sha256"]) == set(NAMES[:-1]), "Daily output list")
    for name, checksum in report["outputs_sha256"].items():
        require(digest(output / name) == checksum, "Daily output changed")
    parts_path, parts = area.load_parts()
    require(report["parts_sha256"] == digest(parts_path), "Daily geography")
    ids = sorted(parts.grid_id)
    regions = parts.set_index("grid_id").loc[ids].geometry
    tables = {n: pd.read_csv(output / n, dtype={"pair_key": str}) for n in NAMES[:-1]}
    areas, centers, scans, scan_grid = (
        tables[n] for n in ("area.csv", "centers.csv", "scans.csv", "scan_grid.csv")
    )
    for table in (areas, centers):
        require(table.grid_id.tolist() == ids and table.grid_id.is_unique, "Daily grid keys")
        require(
            table.daily_observation_status.eq("unknown").all()
            and table.negative_label_permitted.eq(False).all(),
            "Daily labels",
        )
    require(
        np.allclose(areas.aoi_area_m2, regions.area, rtol=1e-10, atol=0.01), "Daily denominator"
    )
    require(areas.method.eq(area.METHOD).all(), "Daily table method")
    for group in area.GROUPS:
        measured = areas[f"{group}_area_estimate_m2"]
        require(
            np.isfinite(measured).all()
            and (measured >= 0).all()
            and (measured <= areas.aoi_area_m2 + 0.1).all(),
            "Daily area bounds",
        )
        require(
            np.allclose(
                measured / areas.aoi_area_m2,
                areas[f"{group}_fraction_estimate"],
                rtol=1e-10,
                atol=1e-12,
            ),
            "Daily fractions",
        )
    for group in area.GROUPS[1:]:
        require(
            (
                areas[f"{group}_area_estimate_m2"]
                <= areas.reconstructed_domain_area_estimate_m2 + 0.1
            ).all(),
            "Daily class outside domain",
        )
    require(
        not scan_grid.duplicated(["sensor", "pair_key", "scan_index", "grid_id"]).any(),
        "Duplicate scan grid",
    )
    require(not scans.duplicated(["sensor", "pair_key", "scan_index"]).any(), "Duplicate scan")
    require(set(scans.sensor + ":" + scans.pair_key) == set(expected_ids), "Scan source set")
    require(
        set(scan_grid.sensor + ":" + scan_grid.pair_key) <= set(expected_ids), "Center source set"
    )
    require(set(scan_grid.grid_id) <= set(ids), "Unregistered daily grid")
    values = scan_grid[timing.COUNTS].to_numpy()
    require(
        np.isfinite(values).all() and (values >= 0).all() and (values == np.floor(values)).all(),
        "Invalid daily native counts",
    )
    expected_counts = scan_grid.groupby("grid_id")[timing.COUNTS].sum().reindex(ids, fill_value=0)
    require(
        np.array_equal(expected_counts.to_numpy(), centers[timing.COUNTS].to_numpy()),
        "Daily native counts",
    )
    begin = pd.Timestamp(day + "T00:00:00Z")
    finish = pd.Timestamp(begin.value + 86400 * 10**9, unit="ns", tz="UTC")
    for table in (scans, scan_grid):
        statuses = [
            timing.combine.classify_scan_interval(s, e, begin, finish)
            for s, e in zip(table.start_utc, table.end_utc, strict=True)
        ]
        require(table.day_window_status.tolist() == statuses, "Daily scan window status")
    keys = ["sensor", "pair_key", "scan_index"]
    joined = scan_grid.merge(
        scans[keys + ["start_utc", "end_utc"]],
        on=keys,
        how="left",
        validate="many_to_one",
        suffixes=("", "_native"),
    )
    require(
        joined.start_utc.eq(joined.start_utc_native).all()
        and joined.end_utc.eq(joined.end_utc_native).all(),
        "Daily scan time lineage",
    )
    groups = dict(tuple(scan_grid.groupby("grid_id")))
    for row in centers.itertuples():
        frame = groups.get(row.grid_id, scan_grid.iloc[:0])
        inside = frame.loc[frame.day_window_status.eq("inside")]
        for name, sample in (
            ("any_center", inside),
            ("nominal_land_center", inside.loc[inside.land_nominal_input_no_residual.gt(0)]),
        ):
            intervals = [
                (pd.Timestamp(s).value, pd.Timestamp(e).value)
                for s, e in zip(sample.start_utc, sample.end_utc, strict=True)
            ]
            union, gap = sweep(intervals, begin.value, finish.value)
            require(
                np.isclose(union, getattr(row, f"{name}_envelope_union_seconds"), rtol=0, atol=1e-9)
                and np.isclose(
                    gap, getattr(row, f"{name}_longest_envelope_gap_seconds"), rtol=0, atol=1e-9
                ),
                "Independent daily time readback",
            )
    return report


def reduce_day(day, pairs, inputs, output, context, verify_geometry=True):
    require(pairs and all(p["start_utc"].startswith(day) for p in pairs), "Mixed/empty day")
    require(len({p["sample_id"] for p in pairs}) == len(pairs), "Duplicate daily pair")
    parts_path, parts = area.load_parts()
    ids = sorted(parts.grid_id)
    regions = parts.set_index("grid_id").loc[ids].geometry.to_numpy()
    pieces = {g: [] for g in area.GROUPS}
    records, center_tables, scan_tables = [], [], []
    for pair in pairs:
        if verify_geometry:
            summer.compare_pair(pair, inputs)
        stem = pair["stem"]
        prior = json.loads((inputs / f"{stem}_audit.json").read_text())
        estimate = json.loads((inputs / f"{stem}_area_estimate.json").read_text())
        records.append(
            {
                "sample_id": pair["sample_id"],
                "audit": prior,
                "area_audit": estimate,
                "input_sha256": {
                    f"{stem}_{s}": digest(inputs / f"{stem}_{s}") for s in summer.SUFFIXES
                },
            }
        )
        center_tables.append(pd.read_csv(inputs / f"{stem}_scan_grid.csv", dtype={"pair_key": str}))
        scan_tables.append(pd.read_csv(inputs / f"{stem}_all_scans.csv", dtype={"pair_key": str}))
        for group in area.GROUPS:
            frame = (
                gpd.read_file(inputs / f"{stem}_area_estimate.gpkg", layer=group)
                .set_index("grid_id")
                .loc[ids]
            )
            require(frame.crs.to_epsg() == 6933, "Daily geometry CRS")
            pieces[group].append(frame.geometry.to_numpy())
    area_table = pd.DataFrame({"grid_id": ids, "aoi_area_m2": shapely.area(regions)})
    for group, arrays in pieces.items():
        geometry = union_arrays(arrays, regions)
        measured = shapely.area(geometry)
        area_table[f"{group}_area_estimate_m2"] = measured
        area_table[f"{group}_fraction_estimate"] = measured / area_table.aoi_area_m2
    for group in area.GROUPS[1:]:
        require(
            (
                area_table[f"{group}_area_estimate_m2"]
                <= area_table.reconstructed_domain_area_estimate_m2 + 0.1
            ).all(),
            "Daily class outside domain",
        )
    area_table["method"] = area.METHOD
    area_table["daily_observation_status"] = "unknown"
    area_table["negative_label_permitted"] = False
    scan_grid, scans = (
        pd.concat(center_tables, ignore_index=True),
        pd.concat(scan_tables, ignore_index=True),
    )
    begin = pd.Timestamp(day + "T00:00:00Z")
    centers = timing.summarize_grid(scan_grid, set(ids), begin)
    output.mkdir(parents=True, exist_ok=True)
    for name, table in (
        ("area.csv", area_table),
        ("centers.csv", centers),
        ("scan_grid.csv", scan_grid),
        ("scans.csv", scans),
    ):
        table.to_csv(output / name, index=False)
    report = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "day": day,
        "context": context,
        "pair_ids": [p["sample_id"] for p in pairs],
        "sources": records,
        "compact_code_sha256": digest(Path(__file__)),
        "parts_sha256": digest(parts_path),
        "outputs_sha256": {n: digest(output / n) for n in NAMES[:-1]},
        "method": area.METHOD,
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
        "limitations": [
            "Approximate interiors; no official physical footprint or negative labels",
            "Spatial union of nominal-date granules; scan boundary timing unresolved",
            "Overlaps unioned, not area-summed; repeated center counts remain repeated views",
            "Wholly-inside center envelopes used for temporal metrics; not continuous observation",
            "Full geometry/QA audit preserved in separate pair journals",
        ],
    }
    summer.atomic_json(output / "report.json", report)
    validate_day(output, day, report["pair_ids"], context)
    return report
