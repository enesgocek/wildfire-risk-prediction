"""Verify retained native scan witnesses and measure out-of-window raw-transfer candidates."""

import hashlib
import io
import json
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require, utc_times
from wildfire_risk_prediction.observation_expansion import raw_references
from wildfire_risk_prediction.observation_window import classify_intervals

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset/observation_expansion_v1/20261014T233502Z_81275155"
SOURCE = ROOT / "outputs/reports/dataset/observation_core_transfer_v1/20261015T104255Z_9750c1c4"
NATIVE = ROOT / "outputs/reports/dataset/observation_core_spatial_v1/20261015T110104Z_9512936a"


def classify_pair(frame, day, expected_scans):
    require(len(frame) == expected_scans and expected_scans > 0, "Full native scan inventory")
    require(np.array_equal(frame.scan_index, np.arange(expected_scans)), "Contiguous native scans")
    require(
        np.array_equal(frame.first_native_row, np.arange(expected_scans) * 32),
        "Native detector row binding",
    )
    starts = utc_times(frame.start_utc)
    ends = utc_times(frame.end_utc)
    require(starts.lt(ends).all() and (np.diff(starts.array.asi8) > 0).all(), "Native scan order")
    classes = classify_intervals(frame, day)
    keep = classes.ne("outside").any()
    return {
        "decision": "retain_raw_inside_or_boundary" if keep else "outside_by_full_scan_witness",
        "scan_count": expected_scans,
        "inside_scan_count": int(classes.eq("inside").sum()),
        "boundary_scan_count": int(classes.eq("boundary_unknown").sum()),
        "outside_scan_count": int(classes.eq("outside").sum()),
    }


def run():
    pins = {}

    def retain(path, sha=None):
        value = digest(path)
        require(sha is None or value == sha, "Retained witness input hash")
        pins[path.relative_to(ROOT).as_posix()] = value
        return path

    parent = json.loads(
        retain(
            BASE / "readback.json",
            "8a29ea70339965497e4e5499ef718c684ecdbc9c833e3e2fa0c0db824a14e7c2",
        ).read_text(encoding="utf-8")
    )
    for name in ("calendar_core.csv", "source_day_inventory.csv"):
        retain(BASE / name, parent["artifact_sha256"][name])
    retain(
        SOURCE / "native_plan.json",
        "fa3cce2822c3825e28352468fa4db8e107f59215f95fab7b8272454900d44edc",
    )
    plan = json.loads((SOURCE / "native_plan.json").read_text(encoding="utf-8"))
    for name, sha in plan["input_sha256"].items():
        retain(ROOT / name, sha)
    retain(Path(__file__))
    retain(ROOT / "src/wildfire_risk_prediction/observation_expansion.py")
    retain(ROOT / "src/wildfire_risk_prediction/observation_window.py")
    native_report = json.loads(
        retain(
            NATIVE / "readback.json",
            "e8870f29a99e2c7bb5aaad3b853cabda0f3df76442072c3ea7229a8e88c0fed2",
        ).read_text(encoding="utf-8")
    )
    retain(NATIVE / "all_scans.csv", native_report["artifact_sha256"]["all_scans.csv"])
    native_frame = pd.read_csv(NATIVE / "all_scans.csv", dtype={"pair_key": str})
    core = pd.read_csv(BASE / "calendar_core.csv")
    days = sorted(core.target_day.unique())
    inventory = pd.read_csv(BASE / "source_day_inventory.csv").set_index("source_nominal_day")
    pairs = plan["all_pairs_inventory_only"]
    rows, scans = [], []
    native_comparison = False
    by_day = {}
    for pair in pairs:
        by_day.setdefault(pair["source_day"], []).append(pair)
    for nominal_day, group in sorted(by_day.items()):
        month_path = (
            ROOT
            / "outputs/gcp_delivery/2026-10-14/compact/products/month"
            / nominal_day[:7]
            / "payload.zip"
        )
        month_name = month_path.relative_to(ROOT).as_posix()
        accepted_key = next(n for n in parent["input_sha256"] if n.replace("\\", "/") == month_name)
        if month_name not in pins:
            retain(month_path, parent["input_sha256"][accepted_key])
        with zipfile.ZipFile(month_path) as month:
            packet_bytes = month.read(nominal_day + ".zip")
        with zipfile.ZipFile(io.BytesIO(packet_bytes)) as packet:
            report_bytes = packet.read("report.json")
            require(
                hashlib.sha256(report_bytes).hexdigest()
                == inventory.loc[nominal_day, "report_sha256"],
                "Accepted daily report witness",
            )
            report = json.loads(report_bytes)
            contents = packet.read("scans.csv")
            require(
                hashlib.sha256(contents).hexdigest() == report["outputs_sha256"]["scans.csv"],
                "Daily native scan CSV hash",
            )
        reference = raw_references(report).set_index("source_id")
        times = pd.read_csv(io.BytesIO(contents), dtype={"pair_key": str})
        require(
            not times.duplicated(["sensor", "pair_key", "scan_index"]).any(),
            "Unique source scan keys",
        )
        sources = {s["sample_id"]: s for s in report["sources"]}
        for pair in group:
            sample = pair["sample_id"]
            sensor, key = sample.split(":")
            source = sources[sample]
            for member in pair["sources"]:
                prior = reference.loc[member["source_id"]]
                require(
                    prior.filename == member["filename"]
                    and prior.sha256 == member["sha256"]
                    and prior.bytes == member["bytes"],
                    "Exact source-version/SHA witness",
                )
            selected = times.loc[times.sensor.eq(sensor) & times.pair_key.eq(key)].sort_values(
                "scan_index"
            )
            expected_scans = source["area_audit"]["scan_count"]
            require(
                source["audit"]["shape"][0] == expected_scans * 32,
                "Scan count matches audited native dimensions",
            )
            begin, end = (
                pd.Timestamp(source["audit"]["start_utc"]),
                pd.Timestamp(source["audit"]["end_utc"]),
            )
            actual_start, actual_end = (
                pd.to_datetime(selected.start_utc, utc=True),
                pd.to_datetime(selected.end_utc, utc=True),
            )
            require(
                actual_start.min().value >= begin.value - 2_000_000_000
                and actual_end.max().value <= end.value + 2_000_000_000,
                "Native/nominal sanity envelope",
            )
            if sample == "SNPP:2018045.0000":
                require(len(selected) == len(native_frame), "Reopened native witness length")
                for column in ("start_utc", "end_utc", "ev_mid_utc"):
                    require(
                        np.array_equal(
                            pd.to_datetime(selected[column], utc=True).array.asi8,
                            pd.to_datetime(native_frame[column], utc=True).array.asi8,
                        ),
                        "Reopened native scan time exact match",
                    )
                native_comparison = True
            target_days = [
                d for d in days if abs((pd.Timestamp(d) - pd.Timestamp(nominal_day)).days) <= 1
            ]
            require(len(target_days) == 1, "One fixed target day per source witness")
            decision = classify_pair(selected, target_days[0], expected_scans)
            rows.append(
                {
                    "sample_id": sample,
                    "source_nominal_day": nominal_day,
                    "target_day": target_days[0],
                    "raw_bytes": pair["bytes"],
                    **decision,
                    "daily_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
                    "daily_scans_sha256": report["outputs_sha256"]["scans.csv"],
                }
            )
            selected = selected.copy()
            selected["sample_id"], selected["target_day"] = sample, target_days[0]
            scans.append(selected)
    table = pd.DataFrame(rows)
    require(
        len(table) == 292 and table.sample_id.is_unique and native_comparison,
        "Complete planned witness triage",
    )
    require(all(digest(ROOT / n) == h for n, h in pins.items()), "Time witness input closure")
    out = (
        ROOT
        / "outputs/reports/dataset/observation_pilot_time_triage_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    table.to_csv(out / "pair_window_triage.csv", index=False)
    pd.concat(scans, ignore_index=True).to_csv(out / "retained_scan_inventory.csv", index=False)
    keep = table.decision.eq("retain_raw_inside_or_boundary")
    result = {
        "status": "full_retained_native_time_triage_verified_not_spatial_acceptance",
        "input_sha256": pins,
        "pair_count": len(table),
        "required_geometry_pairs": int(keep.sum()),
        "outside_witness_pairs": int((~keep).sum()),
        "required_raw_bytes": int(table.loc[keep, "raw_bytes"].sum()),
        "outside_raw_bytes": int(table.loc[~keep, "raw_bytes"].sum()),
        "reference_raw_bytes": int(table.raw_bytes.sum()),
        "native_reopened_scan_witness_exact_match": native_comparison,
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
        "labels_created": False,
        "model_ready": False,
        "negative_label_permitted": False,
        "daily_observation_status": "unknown",
        "network_bytes": 0,
        "limitations": [
            "Exact time exclusion only; inside/boundary sources still need geometry",
            "Historical retained native evidence, not a new read of all 584 raw files",
            "No window margin used to decide exclusion; all actual scans must be outside",
            "No label threshold, performance or download-speed improvement claimed",
        ],
    }
    (out / "readback.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "completion_readback.json").write_text(
        json.dumps({"status": "passed", "report_sha256": digest(out / "readback.json")}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    run()
