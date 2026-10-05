"""Independent event-sweep readback of native scan/grid timing diagnostics."""

import importlib.util
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

SPEC = importlib.util.spec_from_file_location(
    "timing_readback", Path(__file__).with_name("audit_l2_observation_timing.py")
)
timing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(timing)
audit, OUTPUT, ROOT = timing.audit, timing.OUTPUT, timing.ROOT


def read_result_table(path):
    # YYYYDDD.HHMM is an identifier; numeric inference silently removes trailing zeros.
    return pd.read_csv(path, dtype={"pair_key": str})


def event_sweep(intervals, begin, finish):
    """Count active envelopes between timestamp events; no generator gap helper."""
    events = defaultdict(int)
    events[begin] = events[finish] = 0
    for start, end in intervals:
        audit.require(begin < start < end <= finish, "Bad event interval")
        events[start] += 1
        events[end] -= 1
    active, union, longest_gap, ongoing_gap = 0, 0, 0, 0
    previous = begin
    for stamp, delta in sorted(events.items()):
        duration = stamp - previous
        if active:
            union += duration
            ongoing_gap = 0
        else:
            ongoing_gap += duration
            longest_gap = max(longest_gap, ongoing_gap)
        active += delta
        audit.require(active >= 0, "Invalid envelope event ordering")
        previous = stamp
    audit.require(active == 0, "Unclosed event intervals")
    return union / 1e9, longest_gap / 1e9


def main():
    prefix = OUTPUT / "observation_timing_2019-01-14"
    report_path = prefix.with_suffix(".json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    audit.require(report["script_sha256"] == audit.digest(Path(timing.__file__)), "Stale code")
    for filename, digest in report["helpers"].items():
        audit.require(audit.digest(ROOT / filename) == digest, "Stale helper")
    for filename, digest in report["outputs_sha256"].items():
        audit.require(audit.digest(ROOT / filename) == digest, "CSV changed")
    frames = {
        name: read_result_table(prefix.with_name(prefix.name + f"_{name}.csv"))
        for name in ("grid", "scan_grid", "all_scans")
    }
    grids, centers, scans = (frames[n] for n in ("grid", "scan_grid", "all_scans"))
    features = json.loads((ROOT / "data/aoi/grid_5km.geojson").read_text(encoding="utf-8"))[
        "features"
    ]
    reference_ids = {feature["properties"]["grid_id"] for feature in features}
    audit.require(grids.grid_id.is_unique and set(grids.grid_id) == reference_ids, "Grid changed")
    audit.require(
        grids.daily_observation_status.eq("unknown").all()
        and grids.negative_label_permitted.eq(False).all(),
        "Label policy changed",
    )
    audit.require(
        not centers.duplicated(["sensor", "pair_key", "scan_index", "grid_id"]).any(),
        "Duplicate centers",
    )
    audit.require(
        not scans.duplicated(["sensor", "pair_key", "scan_index"]).any(), "Duplicate scans"
    )
    sources = report["sources"]
    actual_keys = set(zip(scans.sensor, scans.pair_key, strict=True))
    audit.require(actual_keys == {tuple(k.split(":")) for k in sources}, "Source set changed")
    for sample_id, provenance in sources.items():
        sensor, key = sample_id.split(":")
        for source in provenance["sources"].values():
            path = ROOT / source["path"]
            audit.require(2018 <= audit.product_identity(path.name)[3].year <= 2023, "Not training")
            audit.require(audit.digest(path) == source["sha256"], "Raw source changed")
        for path, digest in provenance["references"].items():
            audit.require(audit.digest(ROOT / path) == digest, "Frozen reference changed")
        stem = audit.sample_stem(sensor, key)
        frozen_scans = pd.read_csv(OUTPUT / f"{stem}_scan_times.csv")
        sample_scans = scans.loc[scans.sensor.eq(sensor) & scans.pair_key.eq(key)].reset_index(
            drop=True
        )
        pd.testing.assert_frame_equal(sample_scans[frozen_scans.columns], frozen_scans)
        audit.require(
            sample_scans.orbit_number.eq(provenance["orbit_number"]).all(), "Orbit changed"
        )
        sample = centers.loc[centers.sensor.eq(sensor) & centers.pair_key.eq(key)]
        audit.require(
            sample.orbit_id.eq(f"{sensor}:{provenance['orbit_number']}").all(), "Wrong orbit key"
        )
        frozen = pd.read_csv(OUTPUT / f"{stem}_grid_centers.csv").set_index("grid_id").sort_index()
        actual = sample.groupby("grid_id")[timing.COUNTS].sum().reindex(frozen.index, fill_value=0)
        audit.require(
            np.array_equal(actual.to_numpy(), frozen[timing.COUNTS].to_numpy()),
            "Native counts differ",
        )
    joined = centers.merge(
        scans,
        on=["sensor", "pair_key", "scan_index"],
        suffixes=("", "_source"),
        validate="many_to_one",
    )
    for name in scans.columns.difference(["sensor", "pair_key", "scan_index"]):
        audit.require(
            joined[name].equals(joined[name + "_source"]), f"Scan/grid join differs: {name}"
        )
    for name in timing.COUNTS:
        audit.require((centers[name] >= 0).all() and (centers[name] % 1 == 0).all(), "Bad counts")
    audit.require(
        np.array_equal(centers[list(audit.CLASSES)].sum(axis=1), centers.pixel_center_count),
        "Class sum differs",
    )
    audit.require(
        centers.land_nominal_input_no_residual.le(centers.land).all(), "Nominal exceeds land"
    )
    begin = pd.Timestamp(report["T_utc"]).value
    finish = begin + 86_400_000_000_000
    stamps = {
        s: pd.Timestamp(s).value for s in pd.concat([scans.start_utc, scans.end_utc]).unique()
    }
    for row in scans.itertuples():
        start, end = stamps[row.start_utc], stamps[row.end_utc]
        status = (
            "outside"
            if end <= begin or start > finish
            else "inside"
            if start > begin and end <= finish
            else "boundary_unknown"
        )
        audit.require(row.day_window_status == status, "Window status changed")
        q = row.geolocation_scan_quality
        audit.require(
            row.geo_gap_code == q % 4
            and row.geo_encoder_code == (q // 4) % 4
            and row.geo_sce_side == (q // 256) % 2
            and row.geo_other_bits == q & ~271,
            "Scan quality decode differs",
        )
    grouped = dict(tuple(centers.groupby("grid_id")))
    checks = 0
    for row in grids.itertuples():
        frame = grouped.get(row.grid_id, centers.iloc[:0])
        for name in timing.COUNTS:
            audit.require(getattr(row, name) == int(frame[name].sum()), "Daily counts differ")
        audit.require(
            row.boundary_unknown_scan_count
            == int(frame.day_window_status.eq("boundary_unknown").sum()),
            "Boundary count differs",
        )
        inside = frame.loc[frame.day_window_status.eq("inside")]
        for name, sample in (
            ("any_center", inside),
            ("nominal_land_center", inside.loc[inside.land_nominal_input_no_residual.gt(0)]),
        ):
            union, gap = event_sweep(
                [
                    (stamps[s], stamps[e])
                    for s, e in zip(sample.start_utc, sample.end_utc, strict=True)
                ],
                begin,
                finish,
            )
            for field, actual in (
                ("envelope_union_seconds", union),
                ("longest_envelope_gap_seconds", gap),
                ("granule_count", len(set(zip(sample.sensor, sample.pair_key, strict=True)))),
                ("orbit_count", len(set(sample.orbit_id))),
                ("scan_count", len(sample)),
                ("day_scan_count", int(sample.sensor_mode.eq(4).sum())),
                ("night_scan_count", int(sample.sensor_mode.eq(5).sum())),
                ("other_mode_scan_count", int((~sample.sensor_mode.isin([4, 5])).sum())),
            ):
                audit.require(
                    abs(getattr(row, f"{name}_{field}") - actual) <= 1e-9, f"Daily {field} differs"
                )
                checks += 1
            for field, expected in (
                ("first_start_utc", sample.start_utc.min()),
                ("last_end_utc", sample.end_utc.max()),
            ):
                actual = getattr(row, f"{name}_{field}")
                audit.require(
                    (pd.isna(actual) and pd.isna(expected)) or actual == expected,
                    "Endpoint differs",
                )
                checks += 1
    audit.require(
        report["pilot_center_counts"] == grids[timing.COUNTS].sum().astype(int).to_dict(),
        "Totals differ",
    )
    audit.require(
        report["grid_count"] == len(grids) and report["scan_grid_rows"] == len(centers),
        "Row totals differ",
    )
    present = grids.nominal_land_center_scan_count.gt(0)
    audit.require(report["source_granule_count"] == len(sources), "Granule total differs")
    audit.require(
        report["distinct_sensor_orbit_count"]
        == len({(row.sensor, row.orbit_number) for row in scans.itertuples()}),
        "Orbit total differs",
    )
    audit.require(
        report["orbits_with_pilot_centers"] == centers.orbit_id.nunique(), "Pilot orbits differ"
    )
    audit.require(
        report["grids_without_nominal_land_centers"] == int((~present).sum()),
        "No-center total differs",
    )
    audit.require(
        report["negative_label_permitted"] is False
        and report["daily_observation_status"] == "unknown",
        "Report label policy differs",
    )
    for quantile, value in report["longest_nominal_envelope_gap_hours_present_grids"].items():
        actual = (
            grids.loc[present, "nominal_land_center_longest_envelope_gap_seconds"].quantile(
                float(quantile)
            )
            / 3600
        )
        audit.require(abs(actual - value) <= 1e-12, "Quantile differs")
    for field, series in (
        ("nominal_orbit_count_histogram", grids.nominal_land_center_orbit_count),
        ("scan_quality_histogram", scans.geolocation_scan_quality),
        ("sensor_mode_histogram", scans.sensor_mode),
        ("day_window_status_histogram", scans.day_window_status),
    ):
        actual = {str(k): int(v) for k, v in series.value_counts().items()}
        audit.require(report[field] == actual, f"Histogram differs: {field}")
    result = {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "all_columns_reconciled_independent_event_sweep_passed",
        "report_sha256": audit.digest(report_path),
        "verifier_sha256": audit.digest(Path(__file__)),
        "grid_count": len(grids),
        "scan_grid_rows": len(centers),
        "daily_time_and_count_checks": checks,
        "time_comparison_tolerance_seconds": 1e-9,
        "native_reference_counts_exact_match": True,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
    }
    path = prefix.with_name(prefix.name + "_readback.json")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Readback passed: {path}")


if __name__ == "__main__":
    main()
