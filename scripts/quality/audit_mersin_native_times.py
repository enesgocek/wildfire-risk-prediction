"""Check actual scan times before admitting cached sources to point review."""

import importlib.util
import json
import time
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from uuid import uuid4

import pandas as pd
import rasterio
from audit_mersin_open_incidents import ARCHIVE, GRID, PINS, PROVINCES
from audit_mersin_scan_times import ROOT, incident_windows, selected_windows
from audit_stage_one_selection import OBS, read_report, verify

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require, utc_times
from wildfire_risk_prediction.observation_window import (
    classify_intervals,
    review_window,
    source_schedule,
)
from wildfire_risk_prediction.observation_window_source import read_month_offline


def prepare_pair(source_ids, receipt):
    """Reuse the reviewed single-pair runner with a newly pinned selected scope."""
    spec = importlib.util.spec_from_file_location(
        "native_pair_runner", ROOT / "scripts/firms/run_observation_core_pair.py"
    )
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    parent = ROOT / (
        "outputs/reports/dataset/observation_core_transfer_v1/"
        "20261015T104255Z_9750c1c4/native_plan.json"
    )
    require(
        digest(parent) == "fa3cce2822c3825e28352468fa4db8e107f59215f95fab7b8272454900d44edc",
        "Reviewed source plan",
    )
    plan, _ = native.load_plan(parent)
    pairs = [p for p in plan["all_pairs_inventory_only"] if p["sample_id"] in source_ids]
    require(len(pairs) == len(source_ids) == 1, "One temporally selected pair")
    plan["all_pairs_inventory_only"] = pairs
    plan["first_pair"], plan["first_pair_bytes"] = pairs[0]["sample_id"], pairs[0]["bytes"]
    plan["selection_parent_sha256"] = digest(receipt)
    for path in (parent, receipt):
        plan["input_sha256"][path.relative_to(ROOT).as_posix()] = digest(path)
    folder = parent.parent.parent / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    folder.mkdir(parents=True, exist_ok=False)
    target = folder / "native_plan.json"
    target.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "single_mersin_pair_prepared_not_downloaded",
        "artifact_sha256": {"native_plan.json": digest(target)},
        "source_evidence_sha256": digest(receipt),
        "labels_created": False,
    }
    report_path = folder / "readback.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (folder / "completion_readback.json").write_text(
        json.dumps({"report_sha256": digest(report_path)}, indent=2) + "\n", encoding="utf-8"
    )
    checked, pair = native.load_plan(target)
    require(
        pair["sample_id"] in source_ids and len(checked["all_pairs_inventory_only"]) == 1,
        "Prepared plan normal entry point",
    )
    return target


def scan_times(path):
    with warnings.catch_warnings(), ExitStack() as stack:
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        geo = stack.enter_context(
            rasterio.open(f'HDF5:"{path.as_posix()}"://geolocation_data/latitude')
        )
        leap = int(geo.tags()["TAI93_leapseconds"])
        require(0 <= leap <= 100, "Recorded TAI offset")
        columns = {}
        for field, column in (("scan_start_time", "start_utc"), ("scan_end_time", "end_utc")):
            layer = stack.enter_context(
                rasterio.open(f'HDF5:"{path.as_posix()}"://scan_line_attributes/{field}')
            )
            raw = layer.read(1).ravel()
            require(pd.Series(raw).notna().all() and (raw >= 0).all(), "Valid scan time")
            columns[column] = pd.Timestamp("1993-01-01T00:00:00Z") + pd.to_timedelta(
                raw - leap, unit="s"
            )
        frame = pd.DataFrame(columns)
        require(len(frame) * 32 == geo.height, "Complete native scan rows")
        require(frame.start_utc.lt(frame.end_utc).all(), "Positive scan intervals")
        return frame


def main():
    for path in (ARCHIVE, GRID, PROVINCES):
        verify(path, PINS[path])
    receipt = ROOT / (
        "outputs/reports/dataset/mersin_local_sources_v1/20261117T204342Z_e2380a4a/readback.json"
    )
    require(
        digest(receipt) == "b367e738160b6490e6e3d1c21fd0366cbb14afaa69230afe529cf9f76f436dfb",
        "Fixed source inventory",
    )
    inventory = json.loads(receipt.read_bytes())
    master = read_report(OBS / "accepted_readback.json")
    windows = selected_windows(incident_windows())
    evidence, comparisons = [], []
    for pair in inventory["pairs"]:
        require(pair["complete_pair"], "Complete cached pair")
        for source in pair["sources"]:
            require(digest(ROOT / source["path"]) == source["sha256"], "Native source hash")
        geo = next(s for s in pair["sources"] if s["role"] == "geolocation")
        times = scan_times(ROOT / geo["path"])
        evidence.append(
            {
                "sample_id": pair["sample_id"],
                "scans": len(times),
                "start_utc": times.start_utc.min().isoformat(),
                "end_utc": times.end_utc.max().isoformat(),
            }
        )
        for row in windows.itertuples(index=False):
            day = row.prediction_timestamp_utc[:10]
            schedule = source_schedule(day, set(master["missing_source_days"]))
            if pair["source_day"] not in set(schedule.source_nominal_day):
                continue
            classification = classify_intervals(times.map(pd.Timestamp.isoformat), day)
            comparisons.append(
                {
                    "archive_row": row.archive_row,
                    "basis": row.basis,
                    "stated_utc": row.stated_time.isoformat(),
                    "prediction_timestamp_utc": row.prediction_timestamp_utc,
                    "sample_id": pair["sample_id"],
                    "inside_scans": int(classification.eq("inside").sum()),
                    "boundary_scans": int(classification.eq("boundary_unknown").sum()),
                    "inside_scans_after_stated_time": int(
                        (classification.eq("inside") & times.start_utc.gt(row.stated_time)).sum()
                    ),
                    "hours_from_last_scan_end_to_stated": (
                        row.stated_time - times.end_utc.max()
                    ).total_seconds()
                    / 3600,
                }
            )
    affected = {(r["archive_row"], r["basis"]) for r in comparisons}
    needed, compact_inputs, compact_members = [], {}, {}
    for row in windows.itertuples(index=False):
        if (row.archive_row, row.basis) not in affected:
            continue
        day = row.prediction_timestamp_utc[:10]
        schedule = source_schedule(day, set(master["missing_source_days"]))
        requests = {
            d: {row.grid_id}
            for d in schedule.loc[
                schedule.source_status.eq("available_training_packet"), "source_nominal_day"
            ]
        }
        frames = {}
        for month in sorted({d[:7] for d in requests}):
            report = next(r for r in master["reports"] if r["month"] == month)
            package = read_month_offline(
                ROOT,
                report,
                {d: g for d, g in requests.items() if d.startswith(month)},
                time.monotonic() + 120,
            )
            frames.update(package["frames"])
            compact_inputs.update(package["inputs"])
            compact_members.update(package["inner"])
        scans, _ = review_window(
            pd.concat(frames.values(), ignore_index=True), day, row.grid_id, schedule
        )
        keep = (
            scans.window_classification.eq("inside")
            & utc_times(scans.start_utc).gt(row.stated_time)
            & scans.pixel_center_count.gt(0)
        )
        for scan in scans.loc[keep].itertuples(index=False):
            needed.append(
                {
                    "archive_row": row.archive_row,
                    "basis": row.basis,
                    "grid_id": row.grid_id,
                    "sample_id": f"{scan.sensor}:{scan.pair_key}",
                    "scan_index": int(scan.scan_index),
                    "start_utc": scan.start_utc,
                    "end_utc": scan.end_utc,
                    "land_centers": int(scan.land_nominal_input_no_residual),
                }
            )
    result = {
        "inventory_sha256": digest(receipt),
        "native_scan_envelopes": evidence,
        "comparisons": comparisons,
        "after_stated_cell_scans_for_source_lookup": needed,
        "compact_source_sha256": compact_inputs,
        "compact_member_sha256": compact_members,
        "pixel_classification_status": "pending_temporally_eligible_sources",
        "daily_observation_status": "unknown",
        "negative_label_permitted": False,
    }
    out = (
        ROOT
        / "outputs/reports/dataset/mersin_native_times_v1"
        / (f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}")
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Receipt readback")
    plan_path = prepare_pair({row["sample_id"] for row in needed}, path)
    print(json.dumps(result, indent=2))
    print(path.relative_to(ROOT), digest(path))
    print("Prepared native plan", plan_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
