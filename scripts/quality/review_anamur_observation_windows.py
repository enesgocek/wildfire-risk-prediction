"""Reconcile Anamur's catalogue minutes with retained UTC scan envelopes offline."""

import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
from prepare_pu_calendar_sample import digest
from review_anamur_preevent_cover import CASE_RECEIPT, CASE_SHA, GRID
from review_manavgat_reported_starts import OBS
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.observation_window import review_window, source_schedule
from wildfire_risk_prediction.observation_window_source import read_month_offline
from wildfire_risk_prediction.target_admission import DAY_NS

COVER = BASE / "anamur_preevent_cover_v1/20261108T032025Z_2e88ca22/readback.json"
INPUTS = {
    CASE_RECEIPT: CASE_SHA,
    COVER: "ef0333fce0b9339f6559d7f4516f9f49b2f03b73c59f52a9da2b24b88b5f1c0e",
    OBS: "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14",
}


def inspect_minutes(scans):
    signatures = Counter()
    for row in scans.itertuples(index=False):
        centers = int(row.nominal_confidence_fire + row.high_confidence_fire)
        if centers:
            begin, end = pd.Timestamp(row.start_utc), pd.Timestamp(row.end_utc)
            require(begin.floor("min") == end.floor("min"), "One UTC minute per selected scan")
            signatures[row.sensor, begin.floor("min").isoformat()] += centers
    return signatures


def main():
    require(all(digest(p) == v for p, v in INPUTS.items()), "Frozen source receipts")
    case = read_json(CASE_RECEIPT)["cases"]["anamur_belensazak_approximate"]
    prior = read_json(COVER)
    master = read_json(OBS)
    target = pd.Timestamp(case["target_window_start_utc"])
    next_target = pd.Timestamp(case["target_window_end_utc"])
    require(
        target.isoformat() == prior["cutoff_utc"] and next_target.value - target.value == DAY_NS,
        "Consecutive UTC windows",
    )
    days = [stamp.date().isoformat() for stamp in (target, next_target)]
    schedules = {day: source_schedule(day, set(master["missing_source_days"])) for day in days}
    request = {}
    for schedule in schedules.values():
        require(
            schedule.source_status.eq("available_training_packet").all(), "All packets accepted"
        )
        request.update({d: {GRID} for d in schedule.source_nominal_day})
    month = next(row for row in master["reports"] if row["month"] == days[0][:7])
    packet = read_month_offline(ROOT, month, request, time.monotonic() + 120)

    minutes, windows, thermal_scans = Counter(), [], []
    before_first_land_end = None
    first = pd.Timestamp(prior["points"]["tespit_1"]["time_utc"])
    for day, schedule in schedules.items():
        rows = pd.concat(
            [packet["frames"][d] for d in schedule.source_nominal_day], ignore_index=True
        )
        scans, summary = review_window(rows, day, GRID, schedule)
        require(summary["loaded_boundary_scan_rows"] == 0, "No ambiguous boundary rows in case")
        inside = scans.loc[scans.window_classification.eq("inside")].copy()
        minutes.update(inspect_minutes(inside))
        thermal = inside.loc[(inside.nominal_confidence_fire + inside.high_confidence_fire).gt(0)]
        thermal_scans.extend(thermal.to_dict("records"))
        if day == days[0]:
            before = inside.loc[
                inside.land_nominal_input_no_residual.gt(0)
                & pd.to_datetime(inside.end_utc, utc=True, format="ISO8601").lt(first)
            ]
            before_first_land_end = pd.to_datetime(before.end_utc, utc=True, format="ISO8601").max()
            require(pd.notna(before_first_land_end), "Prior retained land-supporting scan")
        windows.append({**summary, "target": None})
    expected = Counter(
        (row["sensor"], row["time_utc"]) for row in prior["points"].values() if "sensor" in row
    )
    require(minutes == expected and sum(minutes.values()) == 5, "Frozen event minute signatures")
    thermal_scans.sort(key=lambda row: pd.Timestamp(row["start_utc"]))
    first_scan = pd.Timestamp(thermal_scans[0]["start_utc"])
    elapsed = (first_scan.value - before_first_land_end.value) / 1_000_000_000
    report = {
        "source_sha256": {
            **{p.relative_to(ROOT).as_posix(): h for p, h in INPUTS.items()},
            **packet["inputs"],
            Path(__file__).resolve().relative_to(ROOT).as_posix(): digest(Path(__file__)),
        },
        "nominal_inner_sha256": packet["inner"],
        "windows": windows,
        "minute_reconciliation": [
            {"sensor": s, "minute_utc": t, "catalogue_rows": n, "thermal_centers": n}
            for (s, t), n in sorted(minutes.items(), key=lambda item: item[0][1])
        ],
        "thermal_scans": thermal_scans,
        "last_retained_land_scan_end_before_first_utc": before_first_land_end.isoformat(),
        "first_thermal_scan_start_utc": first_scan.isoformat(),
        "gap_between_these_scan_envelopes_seconds": float(elapsed),
        "point_level_pixel_identity_verified": False,
        "original_ignition_verified": False,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
    }
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "anamur_observation_windows_v1" / run / "readback.json"
    out.parent.mkdir(parents=True, exist_ok=False)
    write_json(out, report)
    print(out.relative_to(ROOT).as_posix(), digest(out))


if __name__ == "__main__":
    main()
