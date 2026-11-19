"""Prepare the remaining seven frozen source-row passes entirely offline."""

import hashlib
import io
import json
import time
import zipfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require, utc_times
from wildfire_risk_prediction.observation_window import source_schedule, unique_scans
from wildfire_risk_prediction.observation_window_source import read_month_offline
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
SAMPLE = BASE / "source_sampling_review_v1/20261119T133150Z_f94ebe6e/readback.json"
OBS = BASE / "observation_materialization_v1/20261014T145638Z_c0881064/accepted_readback.json"
DONE = BASE / "source_sample_point_v1/20261119T140051Z_000dc2bf/readback.json"
PINS = {
    SAMPLE: "9647a69248ac158aad6f7a864b48bfad8eb61860be08ff3250f8dc643cd4d453",
    OBS: "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14",
    DONE: "9970de0d18f2717c0f72294e35a61938f55af452d034d3f341e2ecc10edc7efa",
}


def main():
    require(
        all(digest(p) == h for p, h in PINS.items()), "Frozen source frame and prior point result"
    )
    source, master, done = [json.loads(p.read_text(encoding="utf-8")) for p in (SAMPLE, OBS, DONE)]
    require(
        done["archive_row"] == "WF1206" and done["L_memberships_created"] == 0,
        "One completed review only",
    )
    eligible = [
        r
        for r in source["intake"]
        if len(r["candidate_grid_ids"]) == 1
        and r["clock_hypotheses"]
        and all(h["inside_current_fit_role"] for h in r["clock_hypotheses"])
    ]
    pending = [r for r in eligible if r["archive_row"] != "WF1206"]
    require(
        len(source["intake"]) == 10 and len(eligible) == 8 and len(pending) == 7,
        "No replacement source rows",
    )
    dates_by_unit, request = {}, defaultdict(lambda: defaultdict(set))
    for row in pending:
        after = max(pd.Timestamp(h["reported_time_utc"]) for h in row["clock_hypotheses"]).as_unit(
            "ns"
        )
        schedule = source_schedule(after.date().isoformat(), set(master["missing_source_days"]))
        dates = schedule.loc[
            schedule.source_status.eq("available_training_packet"), "source_nominal_day"
        ].tolist()
        require(all(2018 <= int(day[:4]) <= 2022 for day in dates), "Fit-role sources only")
        dates_by_unit[row["archive_row"]] = (after, dates)
        for day in dates:
            request[day[:7]][day].add(row["candidate_grid_ids"][0])
    reports = {r["month"]: r for r in master["reports"]}
    frames, payloads, inner = {}, {}, {}
    for month, day_grids in sorted(request.items()):
        packet = read_month_offline(ROOT, reports[month], day_grids, time.monotonic() + 120)
        frames.update(packet["frames"])
        payloads.update(packet["inputs"])
        inner.update(packet["inner"])
    daily_cache = {}

    def day_report(day):
        if day not in daily_cache:
            month = (
                "outputs/gcp_delivery/2026-10-14/compact/products/month/" + day[:7] + "/payload.zip"
            )
            direct = "outputs/gcp_delivery/2026-10-14/compact/products/day/" + day + "/payload.zip"
            if month in payloads:
                with zipfile.ZipFile(ROOT / month) as z:
                    with zipfile.ZipFile(io.BytesIO(z.read(day + ".zip"))) as daily:
                        raw = daily.read("report.json")
            else:
                require(direct in payloads, "Accepted partial-month day")
                with zipfile.ZipFile(ROOT / direct) as daily:
                    raw = daily.read("report.json")
            require(
                hashlib.sha256(raw).hexdigest() == inner[day]["report.json"], "Pinned daily report"
            )
            daily_cache[day] = json.loads(raw)
        return daily_cache[day]

    out = (
        BASE
        / "source_queue_metadata_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    units = []
    for row in pending:
        after, dates = dates_by_unit[row["archive_row"]]
        grid = row["candidate_grid_ids"][0]
        scans = unique_scans(
            pd.concat([frames[d].loc[frames[d].grid_id.eq(grid)] for d in dates], ignore_index=True)
        )
        meta = scans[
            [
                "grid_id",
                "sensor",
                "pair_key",
                "scan_index",
                "start_utc",
                "end_utc",
                "source_nominal_days_json",
            ]
        ].copy()
        times = utc_times(meta.start_utc)
        finish = pd.Timestamp(after.value + 86_400_000_000_000, unit="ns", tz="UTC")
        candidates = meta.loc[times.ge(after) & times.le(finish)].copy()
        require(not candidates.empty, "Missing next pass; keep source row without replacement")
        chosen = (
            candidates.assign(_order=utc_times(candidates.start_utc))
            .sort_values(["_order", "sensor", "pair_key", "scan_index"])
            .drop(columns="_order")
            .iloc[0]
        )
        matches = []
        for day in json.loads(chosen.source_nominal_days_json):
            matches.extend(
                r
                for r in day_report(day)["sources"]
                if r["audit"]["sensor"] == chosen.sensor
                and r["audit"]["pair_key"] == str(chosen.pair_key)
            )
        require(bool(matches), "Exact historical source for selected pass")
        historical = matches[0]["audit"]
        require(
            all(r["audit"]["sources"] == historical["sources"] for r in matches),
            "Repeated native source identity",
        )
        meta.to_csv(out / (row["archive_row"] + "_scan_metadata.csv"), index=False)
        units.append(
            {
                "archive_row": row["archive_row"],
                "source_row": row,
                "after_both_clock_hypotheses_utc": after.isoformat(),
                "selected_scan": chosen.to_dict(),
                "sample_id": matches[0]["sample_id"],
                "historical_source_audit": historical,
                "fire_or_quality_counts_used_for_choice": False,
            }
        )
    result = {
        "scope": "seven_remaining_frozen_source_rows_native_transport_only",
        "units": units,
        "all_ten_source_rows_retained": True,
        "excluded_completed_review": ["WF1206"],
        "untransportable_source_rows": ["WF1342", "WF1556"],
        "L_memberships_created": 0,
        "labels_created": False,
        "gate": specification(),
        "model_trained": False,
        "final_merge_performed": False,
        "input_sha256": {
            **{p.relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
            **payloads,
        },
        "daily_member_sha256": inner,
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    require(all(digest(ROOT / n) == h for n, h in result["input_sha256"].items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT).as_posix(), digest(path))
    print("PASS seven outcome-independent source-pass identities prepared")


if __name__ == "__main__":
    main()
