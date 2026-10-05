"""Native training-sample scan/quality diagnostics. Never daily coverage or labels.

Earth-view scan envelopes bound acquisition times of selected centers; their
union is NOT a duration of continuous observation of a grid cell.
"""

import importlib.util
import json
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from pyproj import Transformer
from rasterio.windows import Window

SPEC = importlib.util.spec_from_file_location(
    "timing_area", Path(__file__).with_name("combine_l2_area_estimates.py")
)
combine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(combine)
area, audit = combine.area, combine.audit
ROOT, OUTPUT = area.ROOT, area.OUTPUT
KEYS = (
    "2019014.0042",
    "2019014.1018",
    "2019014.1024",
    "2019014.1200",
    "2019014.2242",
    "N20:2019014.0930",
    "N20:2019014.1112",
    "N20:2019014.2330",
)
COUNTS = list(audit.CLASSES) + [
    "input_non_nominal",
    "geo_non_nominal",
    "residual_bowtie",
    "land_nominal_input_no_residual",
    "pixel_center_count",
]
GEO_GUIDE = (
    "https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/archives/"
    "Document%20Archive/Science%20Data%20Product%20Documentation/"
    "NASA_VIIRS_L1B_UG_August_2021.pdf"
)


def scan_quality_fields(value):
    """Geo Table D3: two coded fields; SCE side is metadata, not a failure."""
    audit.require(int(value) == value and 0 <= value <= 8191, "Invalid geo scan quality")
    value = int(value)
    return {
        "geo_gap_code": value & 3,
        "geo_encoder_code": (value >> 2) & 3,
        "geo_sce_side": (value >> 8) & 1,
        "geo_other_bits": value & ~271,
    }


def envelope_metrics(intervals, begin, finish):
    """Union envelopes and measure gaps, including both day edges, in ns."""
    begin, finish = pd.Timestamp(begin), pd.Timestamp(finish)
    audit.require(begin.tzinfo is not None and finish.tzinfo is not None, "Timezone required")
    audit.require(begin < finish, "Bad window")
    pairs = []
    for start, end in intervals:
        audit.require(
            combine.classify_scan_interval(start, end, begin, finish) == "inside",
            "Only wholly inside envelopes may enter gap metrics",
        )
        pairs.append((pd.Timestamp(start).value, pd.Timestamp(end).value))
    cursor, union_ns, longest_ns = begin.value, 0, 0
    for start, end in sorted(pairs):
        longest_ns = max(longest_ns, start - cursor)
        union_ns += max(0, end - max(cursor, start))
        cursor = max(cursor, end)
    longest_ns = max(longest_ns, finish.value - cursor)
    return union_ns / 1e9, longest_ns / 1e9


def count_centers(ids, scans, mask, qa):
    """Preserve overlapping QA flags independently of mutually exclusive classes."""
    audit.require(len(ids) == len(scans) == len(mask) == len(qa), "Center lengths differ")
    audit.require(np.isin(mask, np.arange(10)).all(), "Unexpected fire class")
    bad, geo_bad, residual = audit.input_quality_flags(qa)
    frame = pd.DataFrame({"grid_id": ids, "scan_index": scans})
    for label, name in enumerate(audit.CLASSES):
        frame[name] = (mask == label).astype("int64")
    for name, flag in zip(
        COUNTS[10:14], (bad, geo_bad, residual, audit.diagnostic_land(mask, qa)), strict=True
    ):
        frame[name] = flag.astype("int64")
    frame["pixel_center_count"] = 1
    return frame.groupby(["grid_id", "scan_index"], sort=True)[COUNTS].sum().reset_index()


def source_scans(sensor, key, aoi, transformer, grid_ids):
    stem = audit.sample_stem(sensor, key)
    prior_path = OUTPUT / f"{stem}_audit.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    audit.require(prior["sensor"] == sensor and prior["pair_key"] == key, "Wrong source")
    audit.require(prior["script_sha256"] == audit.digest(Path(audit.__file__)), "Stale inspector")
    for field, path in (
        ("aoi_sha256", ROOT / "data/aoi/aoi.geojson"),
        ("grid_sha256", ROOT / "data/aoi/grid_5km.geojson"),
    ):
        audit.require(prior[field] == audit.digest(path), "Geography changed")
    paths = {name: ROOT / item["path"] for name, item in prior["sources"].items()}
    for name, path in paths.items():
        audit.require(audit.product_identity(path.name)[:3] == (sensor, name, key), "Wrong pair")
        audit.require(audit.digest(path) == prior["sources"][name]["sha256"], "Raw changed")
    scan_path, grid_path = (OUTPUT / f"{stem}_scan_times.csv", OUTPUT / f"{stem}_grid_centers.csv")
    area_path = OUTPUT / f"{stem}_area_estimate.json"
    area_report = json.loads(area_path.read_text(encoding="utf-8"))
    audit.require(
        area_report["sources"]["previous_audit_sha256"] == audit.digest(prior_path),
        "Stale source audit",
    )
    audit.require(
        area_report["sources"]["scan_times_sha256"] == audit.digest(scan_path), "Stale times"
    )
    audit.require(
        area_report["sources"]["script_sha256"] == audit.digest(Path(area.__file__)),
        "Stale time conversion code",
    )
    reference_scans = pd.read_csv(scan_path)
    before = {p: audit.digest(p) for p in (prior_path, scan_path, grid_path, area_path)}
    blocks = []
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        mask, qa = (audit.layer(stack, paths["fire"], n) for n in ("fire_mask", "algorithm_QA"))
        lon, lat = (
            audit.layer(stack, paths["geolocation"], f"geolocation_data/{n}")
            for n in ("longitude", "latitude")
        )
        tags = lat.tags()
        audit.validate_pair(paths["fire"], paths["geolocation"], mask.tags(), tags)
        audit.require(mask.shape == qa.shape == lon.shape == lat.shape, "Shape mismatch")
        audit.require(mask.dtypes == ("uint8",) and qa.dtypes == ("uint32",), "Wrong data types")
        audit.require(mask.height % 32 == 0, "Incomplete scans")
        nscans = mask.height // 32
        raw = {
            n: audit.layer(stack, paths["geolocation"], f"scan_line_attributes/{n}").read(1).ravel()
            for n in (
                "scan_start_time",
                "scan_end_time",
                "ev_mid_time",
                "scan_quality",
                "sensor_mode",
            )
        }
        audit.require(all(len(v) == nscans for v in raw.values()), "Scan length mismatch")
        audit.require(np.isin(raw["sensor_mode"], np.arange(7)).all(), "Unknown sensor mode")
        for value in raw["scan_quality"]:
            scan_quality_fields(value)
        offset = int(tags["TAI93_leapseconds"])
        starts, ends, mids = (
            area.tai93_utc(raw[n], offset)
            for n in ("scan_start_time", "scan_end_time", "ev_mid_time")
        )
        audit.require(
            ((starts < ends) & (starts <= mids) & (mids <= ends)).all()
            and (np.diff(starts.asi8) > 0).all(),
            "Invalid scan order",
        )
        audit.require(len(reference_scans) == nscans, "Reference scan length mismatch")
        for column, actual in (
            ("scan_index", np.arange(nscans)),
            ("first_native_row", np.arange(nscans) * 32),
            ("geolocation_scan_quality", raw["scan_quality"]),
            ("sensor_mode", raw["sensor_mode"]),
        ):
            audit.require(
                np.array_equal(reference_scans[column], actual), f"Scan mismatch: {column}"
            )
        for column, actual in (("start_utc", starts), ("end_utc", ends), ("ev_mid_utc", mids)):
            audit.require(
                np.array_equal(
                    pd.to_datetime(reference_scans[column], utc=True).array.asi8, actual.asi8
                ),
                f"Time mismatch: {column}",
            )
        orbit = int(tags["OrbitNumber"])
        audit.require(orbit > 0, "Missing orbit identity")
        begin = pd.Timestamp(prior["start_utc"]).normalize()
        finish = pd.Timestamp(begin.value + 86_400_000_000_000, unit="ns", tz="UTC")
        times = reference_scans.copy()
        times["day_window_status"] = [
            combine.classify_scan_interval(s, e, begin, finish)
            for s, e in zip(starts, ends, strict=True)
        ]
        for name in scan_quality_fields(0):
            times[name] = [scan_quality_fields(v)[name] for v in raw["scan_quality"]]
        for row in range(0, mask.height, 256):
            window = Window(0, row, mask.width, min(256, mask.height - row))
            longitudes, latitudes = lon.read(1, window=window), lat.read(1, window=window)
            _, _, selected = audit.pilot_selection(longitudes, latitudes, aoi)
            if not selected.any():
                continue
            x, y = transformer.transform(longitudes[selected], latitudes[selected])
            ids = [
                f"E6933_5K_V1_C{c}_R{r}"
                for c, r in zip(
                    np.floor(x / 5000).astype(int), np.floor(y / 5000).astype(int), strict=True
                )
            ]
            audit.require(set(ids) <= grid_ids, "Unregistered grid")
            scan_indices = (np.nonzero(selected)[0] + row) // 32
            blocks.append(
                count_centers(
                    ids,
                    scan_indices,
                    mask.read(1, window=window)[selected],
                    qa.read(1, window=window)[selected],
                )
            )
        centers = (
            pd.concat(blocks, ignore_index=True)
            if blocks
            else pd.DataFrame(columns=["grid_id", "scan_index", *COUNTS])
        )
        expected = pd.read_csv(grid_path).set_index("grid_id").sort_index()
        audit.require(
            set(expected.index) == grid_ids and expected.index.is_unique, "Wrong grid keys"
        )
        audit.require(
            expected.daily_observation_status.eq("unknown").all()
            and expected.negative_label_permitted.eq(False).all(),
            "Reference label policy",
        )
        summed = centers.groupby("grid_id")[COUNTS].sum().reindex(expected.index, fill_value=0)
        audit.require(
            np.array_equal(summed.to_numpy(), expected[COUNTS].to_numpy()), "Native grid mismatch"
        )
        result = centers.merge(times, on="scan_index", validate="many_to_one")
        result["sensor"], result["pair_key"], result["orbit_number"] = sensor, key, orbit
        result["orbit_id"] = f"{sensor}:{orbit}"
        all_scans = times.copy()
        all_scans["sensor"], all_scans["pair_key"], all_scans["orbit_number"] = sensor, key, orbit
    for name, path in paths.items():
        audit.require(
            audit.digest(path) == prior["sources"][name]["sha256"], "Raw changed during read"
        )
    for path, digest in before.items():
        audit.require(audit.digest(path) == digest, "Reference changed during read")
    provenance = {
        "orbit_number": orbit,
        "sources": prior["sources"],
        "references": {str(p.relative_to(ROOT)): digest for p, digest in before.items()},
        "whole_swath_scan_count": nscans,
        "pilot_scan_count": int(result.scan_index.nunique()),
        "pilot_center_count": int(result.pixel_center_count.sum()),
        "native_grid_counts_exact_match": True,
    }
    return result, all_scans, provenance, begin


def summarize_grid(centers, grid_ids, begin):
    finish = pd.Timestamp(begin.value + 86_400_000_000_000, unit="ns", tz="UTC")
    grouped = dict(tuple(centers.groupby("grid_id")))
    rows = []
    for grid_id in sorted(grid_ids):
        frame = grouped.get(grid_id, centers.iloc[:0])
        inside = frame.loc[frame.day_window_status.eq("inside")]
        nominal = inside.loc[inside.land_nominal_input_no_residual.gt(0)]
        record = {"grid_id": grid_id, **{n: int(frame[n].sum()) for n in COUNTS}}
        record["boundary_unknown_scan_count"] = int(
            frame.day_window_status.eq("boundary_unknown").sum()
        )
        for name, sample in (("any_center", inside), ("nominal_land_center", nominal)):
            union, gap = envelope_metrics(
                zip(sample.start_utc, sample.end_utc, strict=True), begin, finish
            )
            record.update(
                {
                    f"{name}_granule_count": len(sample[["sensor", "pair_key"]].drop_duplicates()),
                    f"{name}_orbit_count": sample.orbit_id.nunique(),
                    f"{name}_scan_count": len(sample),
                    f"{name}_day_scan_count": int(sample.sensor_mode.eq(4).sum()),
                    f"{name}_night_scan_count": int(sample.sensor_mode.eq(5).sum()),
                    f"{name}_other_mode_scan_count": int((~sample.sensor_mode.isin([4, 5])).sum()),
                    f"{name}_first_start_utc": sample.start_utc.min() if len(sample) else None,
                    f"{name}_last_end_utc": sample.end_utc.max() if len(sample) else None,
                    f"{name}_envelope_union_seconds": union,
                    f"{name}_longest_envelope_gap_seconds": gap,
                }
            )
        record["daily_observation_status"] = "unknown"
        record["negative_label_permitted"] = False
        rows.append(record)
    return pd.DataFrame(rows)


def main():
    aoi = gpd.read_file(ROOT / "data/aoi/aoi.geojson").to_crs(4326).geometry.union_all()
    shapely.prepare(aoi)
    grid_ids = set(gpd.read_file(ROOT / "data/aoi/grid_5km.geojson").grid_id)
    transformer = Transformer.from_crs(4326, 6933, always_xy=True)
    frames, scan_frames, sources, dates = [], [], {}, set()
    for value in KEYS:
        sensor, key = area.parse_key(value)
        frame, scans, source, begin = source_scans(sensor, key, aoi, transformer, grid_ids)
        frames.append(frame)
        scan_frames.append(scans)
        sources[f"{sensor}:{key}"] = source
        dates.add(begin)
        print(f"Native scan/grid reconciliation passed: {sensor}:{key}", flush=True)
    audit.require(len(dates) == 1, "Different training days")
    begin = dates.pop()
    centers, scans = pd.concat(frames, ignore_index=True), pd.concat(scan_frames, ignore_index=True)
    audit.require(
        not centers.duplicated(["sensor", "pair_key", "scan_index", "grid_id"]).any(),
        "Duplicate rows",
    )
    daily = summarize_grid(centers, grid_ids, begin)
    prefix = OUTPUT / f"observation_timing_{begin.date()}"
    hashes = {}
    for suffix, table in (("scan_grid", centers), ("all_scans", scans), ("grid", daily)):
        path = prefix.with_name(prefix.name + f"_{suffix}.csv")
        table.to_csv(path, index=False)
        readback = pd.read_csv(path)
        audit.require(
            len(readback) == len(table) and list(readback.columns) == list(table.columns),
            "CSV shape",
        )
        hashes[str(path.relative_to(ROOT))] = audit.digest(path)
    present = daily.nominal_land_center_scan_count.gt(0)
    report = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "training_day": str(begin.date()),
        "status": "native_scan_quality_and_time_diagnostic_completed",
        "window_definition": "(T,T+24h]",
        "T_utc": begin.isoformat(),
        "sources": sources,
        "script_sha256": audit.digest(Path(__file__)),
        "helpers": {
            str(Path(m.__file__).relative_to(ROOT)): audit.digest(Path(m.__file__))
            for m in (combine, area, audit)
        },
        "outputs_sha256": hashes,
        "grid_count": len(daily),
        "scan_grid_rows": len(centers),
        "source_granule_count": len(sources),
        "distinct_sensor_orbit_count": len(
            {(s.split(":")[0], p["orbit_number"]) for s, p in sources.items()}
        ),
        "orbits_with_pilot_centers": centers.orbit_id.nunique(),
        "pilot_center_counts": daily[COUNTS].sum().astype(int).to_dict(),
        "grids_without_nominal_land_centers": int((~present).sum()),
        "longest_nominal_envelope_gap_hours_present_grids": {
            str(q): float(
                daily.loc[present, "nominal_land_center_longest_envelope_gap_seconds"].quantile(q)
                / 3600
            )
            for q in (0, 0.5, 0.95, 1)
        },
        "nominal_orbit_count_histogram": daily.nominal_land_center_orbit_count.value_counts()
        .sort_index()
        .to_dict(),
        "scan_quality_histogram": scans.geolocation_scan_quality.value_counts()
        .sort_index()
        .to_dict(),
        "sensor_mode_histogram": scans.sensor_mode.value_counts().sort_index().to_dict(),
        "day_window_status_histogram": scans.day_window_status.value_counts().to_dict(),
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "guides": [audit.GUIDE, GEO_GUIDE],
        "limitations": [
            "One listed training day only; no full-period catalogue completeness claim",
            "Pixel-center diagnostics, not footprint areas or physical absence of observations",
            "A scan envelope bounds selected acquisition times, not continuous observation",
            "No threshold, scan-quality exclusion, eligibility rule or negative label selected",
            "Nominal land-center diagnostic uses class 5 and fire input QA, not vegetation area",
            "Geo scan quality is decoded separately; nonzero SCE side is not a failure",
            "No new satellite download; raw sources and previous outputs remain unchanged",
        ],
    }
    destination = prefix.with_suffix(".json")
    destination.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Report: {destination}")


if __name__ == "__main__":
    main()
