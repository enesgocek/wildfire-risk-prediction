"""Check exact UTC windows in the fixed PU review sample and retained event cases."""

import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
from prepare_pu_calendar_sample import digest
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.observation_window import review_window, source_schedule
from wildfire_risk_prediction.observation_window_source import read_month_offline
from wildfire_risk_prediction.target_admission import assert_targets_unassigned, detection_windows

OBS = BASE / "observation_materialization_v1/20261014T145638Z_c0881064/accepted_readback.json"
SAMPLE = BASE / "pu_calendar_sample_v1/20261108T013027Z_d2b1102c"
EVENTS = BASE / "stratified_event_candidate_v1/20261108T004510Z_5cca8b52/readback.json"
LINKS = BASE / "pu_link_sensitivity_v1/20261108T005041Z_7b083915/readback.json"
LAND = "loaded_nominal_land_center_definite_count"
GAP = "loaded_nominal_land_center_longest_envelope_gap_seconds"


def nominal_class(land, gap):
    if land == 0:
        return "no_selected_land_center"
    return "land_gap_ge_12h" if gap >= 43200 else "land_gap_lt_12h"


def sample_windows(rows, master, pins):
    deferred = set(master["missing_source_days"])
    schedules, requested = {}, defaultdict(lambda: defaultdict(set))
    for row in rows.itertuples(index=False):
        schedule = source_schedule(row.prediction_day_utc, deferred)
        schedules[row.grid_id, row.prediction_day_utc] = schedule
        for nominal in schedule.loc[
            schedule.source_status.eq("available_training_packet"), "source_nominal_day"
        ]:
            requested[nominal[:7]][nominal].add(row.grid_id)
    reports = {r["month"]: r for r in master["reports"]}
    frames, inner = {}, {}
    for month, days in sorted(requested.items()):
        packet = read_month_offline(ROOT, reports[month], days, time.monotonic() + 120)
        frames.update(packet["frames"])
        inner.update(packet["inner"])
        pins.update(packet["inputs"])
        if month.endswith(("06", "12")):
            print("Checked through", month, flush=True)
    require(
        set(frames) == {day for days in requested.values() for day in days}, "Exact loaded days"
    )
    result = []
    for row in rows.itertuples(index=False):
        grid, day = row.grid_id, row.prediction_day_utc
        schedule = schedules[grid, day]
        parts = [frames[d] for d in schedule.source_nominal_day if d in frames]
        require(parts, "At least one permitted source day per sample")
        source = pd.concat(parts, ignore_index=True)
        source = source.loc[source.grid_id.eq(grid)]
        scans, summary = review_window(source, day, grid, schedule)
        # Recheck time bounds independently on the resulting scan rows.
        t = pd.Timestamp(day, tz="UTC").as_unit("ns")
        end = t + pd.Timedelta(24, unit="h")
        classes = [
            "inside"
            if a > t and b <= end
            else "outside"
            if b <= t or a > end
            else "boundary_unknown"
            for a, b in zip(
                pd.to_datetime(scans.start_utc, utc=True, format="ISO8601"),
                pd.to_datetime(scans.end_utc, utc=True, format="ISO8601"),
                strict=True,
            )
        ]
        require(classes == scans.window_classification.tolist(), "Independent scan interval check")
        loaded_nominal_land = int(
            source.loc[source.source_nominal_day.eq(day), "land_nominal_input_no_residual"].sum()
        )
        nominal_land = row.obs_land_nominal_input_no_residual
        require(
            (day in deferred and pd.isna(nominal_land)) or loaded_nominal_land == nominal_land,
            "Nominal source matches published sample",
        )
        result.append(
            {
                **summary,
                "sample": row.sample,
                "contrast": row.contrast,
                "province": row.province,
                "nominal_observation_context": row.observation_context,
                "nominal_land_center_count": nominal_land,
                "loaded_window_observation_context": nominal_class(summary[LAND], summary[GAP]),
                "nominal_land_count_changed": not pd.isna(nominal_land)
                and summary[LAND] != nominal_land,
            }
        )
    return pd.DataFrame(result), inner


def compare_cases(events, links):
    cases = {row["slot"]: row for row in events["cases"]}
    require(len(cases) == 5 and all(r["target"] is None for r in cases.values()), "Fixed cases")
    first = pd.Series({slot: row["detected_utc"] for slot, row in cases.items()})
    windows = detection_windows(first)
    result = []
    for slot, case in cases.items():
        t, end, edge = windows.loc[slot]
        (day_window,) = (r for r in case["observation_windows"] if r["day_offset"] == 0)
        require(
            not edge
            and t.isoformat() == case["prediction_utc"]
            and day_window["prediction_timestamp_utc"] == case["prediction_utc"],
            "Candidate prediction day and scan window agree",
        )
        hypotheses = []
        for link in links["source_hypotheses"]:
            if link["slot"] != slot:
                continue
            local_day = pd.Timestamp(case["detected_utc"]).tz_convert("Europe/Istanbul").date()
            stamp = pd.Timestamp(f"{local_day}T{link['local_time']}", tz="Europe/Istanbul")
            stamp = stamp.tz_convert("UTC")
            hypotheses.append(
                {
                    "kind": link["time_type"],
                    "reported_utc": stamp.isoformat(),
                    "inside_same_window": bool(t < stamp <= end),
                }
            )
        result.append(
            {
                "slot": slot,
                "prediction_utc": t.isoformat(),
                "first_satellite_utc": first[slot],
                "inside_thermal_centers": day_window["loaded_thermal_center_definite_count"],
                "reported_times": hypotheses,
                "independent_origin_verified": case["independent_origin_verified"],
                "target": None,
            }
        )
    return result


def main():
    pins = {}

    def retain(path, expected=None):
        actual = digest(path)
        require(expected is None or actual == expected, "Input hash changed")
        pins[path.relative_to(ROOT).as_posix()] = actual
        return path

    master = read_json(
        retain(OBS, "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14")
    )
    sample = read_json(
        retain(
            SAMPLE / "readback.json",
            "84ab70f35c201ea36453e91c7e50a69c4123328456c37140ec4f6efafbdb5bf4",
        )
    )
    events = read_json(
        retain(EVENTS, "95fe28b6c421797552a550d0461f18f3f8224e8a0e9f2ef08942aa82ad77bd57")
    )
    links = read_json(
        retain(LINKS, "39a52dcd71ff5d53b36c507e018991e6608b197d7948ef836beb2af0f628c402")
    )
    for record in (sample, events, links):
        require(
            record["daily_observation_status"] == "unknown"
            and all(
                record[k] is False
                for k in (
                    "positive_label_permitted",
                    "negative_label_permitted",
                    "labels_created",
                    "final_merge_performed",
                )
            ),
            "Closed research gates",
        )
    core = pd.read_csv(retain(SAMPLE / "sample.csv", sample["output_sha256"]["sample.csv"]))
    contrast = pd.read_csv(
        retain(SAMPLE / "contrasts.csv", sample["output_sha256"]["contrasts.csv"])
    )
    rows = pd.concat(
        [core.assign(sample="core", contrast=""), contrast.assign(sample="contrast")],
        ignore_index=True,
    )
    assert_targets_unassigned(rows)
    require(
        len(rows) == 127 and not rows.duplicated(["grid_id", "prediction_day_utc"]).any(),
        "Fixed review units",
    )
    case_audit = compare_cases(events, links)
    result, inner = sample_windows(rows, master, pins)
    assert_targets_unassigned(result)

    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "pu_target_windows_v1" / run
    out.mkdir(parents=True, exist_ok=False)
    table = out / "windows.csv"
    result = result.assign(target=float("nan"), contrast=result.contrast.replace("", float("nan")))
    result.to_csv(table, index=False, mode="x", encoding="utf-8-sig")
    pd.testing.assert_frame_equal(result, pd.read_csv(table), check_dtype=False)
    for path in (
        Path(__file__).resolve(),
        ROOT / "src/wildfire_risk_prediction/observation_window.py",
        ROOT / "src/wildfire_risk_prediction/observation_window_source.py",
        ROOT / "src/wildfire_risk_prediction/target_admission.py",
    ):
        retain(path)
    report = {
        "source_sha256": pins,
        "nominal_packets": inner,
        "windows_sha256": digest(table),
        "sample_counts": result.groupby("sample").size().to_dict(),
        "event_cases": case_audit,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    write_json(out / "readback.json", report)
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))


if __name__ == "__main__":
    main()
