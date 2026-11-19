"""Schedule one sampled source-row check using only timing/coverage metadata, not fire counts."""

import hashlib
import io
import json
import time
import zipfile
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
PINS = {
    SAMPLE: "9647a69248ac158aad6f7a864b48bfad8eb61860be08ff3250f8dc643cd4d453",
    OBS: "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14",
}


def main():
    pins = dict(PINS)
    require(all(digest(p) == h for p, h in pins.items()), "Pinned outcome-independent selection")
    sample, master = [json.loads(p.read_text(encoding="utf-8")) for p in (SAMPLE, OBS)]
    keys = SAMPLE.parent / "frozen_selected_keys.csv"
    pins[keys] = sample["selection_sha256"]
    require(digest(keys) == pins[keys], "Sample frozen before any scan reads")
    ordered = sorted(sample["intake"], key=lambda r: (r["year"], r["archive_row"]))
    eligible = [
        r
        for r in ordered
        if len(r["candidate_grid_ids"]) == 1
        and r["clock_hypotheses"]
        and all(w["inside_current_fit_role"] for w in r["clock_hypotheses"])
    ]
    require(bool(eligible), "No transportable row; do not replace the source sample")
    selected = eligible[0]
    after = max(pd.Timestamp(w["reported_time_utc"]) for w in selected["clock_hypotheses"]).as_unit(
        "ns"
    )
    day = after.date().isoformat()
    grid = selected["candidate_grid_ids"][0]
    schedule = source_schedule(day, set(master["missing_source_days"]))
    dates = schedule.loc[
        schedule.source_status.eq("available_training_packet"), "source_nominal_day"
    ]
    require(all(2018 <= int(d[:4]) <= 2022 for d in dates), "Current fit-role dates only")
    reports = {r["month"]: r for r in master["reports"]}
    frames, payload_pins, daily_pins = [], {}, {}
    for month in sorted({d[:7] for d in dates}):
        request = {d: {grid} for d in dates if d[:7] == month}
        packet = read_month_offline(ROOT, reports[month], request, time.monotonic() + 120)
        frames.extend(packet["frames"].values())
        payload_pins.update(packet["inputs"])
        daily_pins.update(packet["inner"])
    scans = unique_scans(pd.concat(frames, ignore_index=True))
    # Discard the diagnostic outcome columns before source choice.
    metadata = scans[
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
    starts = utc_times(metadata.start_utc)
    finish = pd.Timestamp(after.value + 86_400_000_000_000, unit="ns", tz="UTC")
    choices = metadata.loc[starts.ge(after) & starts.le(finish)]
    require(not choices.empty, "No next recorded pass; preserve case without replacement")
    choice = choices.sort_values(["start_utc", "sensor", "pair_key", "scan_index"]).iloc[0]
    pair_key = str(choice.pair_key)
    source_reports = []
    for nominal in json.loads(choice.source_nominal_days_json):
        month_path = (
            "outputs/gcp_delivery/2026-10-14/compact/products/month/" + nominal[:7] + "/payload.zip"
        )
        day_path = (
            "outputs/gcp_delivery/2026-10-14/compact/products/day/" + nominal + "/payload.zip"
        )
        if month_path in payload_pins:
            with zipfile.ZipFile(ROOT / month_path) as archive:
                with zipfile.ZipFile(io.BytesIO(archive.read(nominal + ".zip"))) as daily:
                    raw = daily.read("report.json")
        else:
            require(day_path in payload_pins, "Pinned partial-month daily source")
            with zipfile.ZipFile(ROOT / day_path) as daily:
                raw = daily.read("report.json")
        require(
            hashlib.sha256(raw).hexdigest() == daily_pins[nominal]["report.json"],
            "Same accepted daily report",
        )
        matches = [
            r
            for r in json.loads(raw)["sources"]
            if r["audit"]["sensor"] == choice.sensor and r["audit"]["pair_key"] == pair_key
        ]
        source_reports.extend((nominal, r) for r in matches)
    require(source_reports, "Selected scan has historical source identity")
    historical = source_reports[0][1]
    sample_id = historical["sample_id"]
    require(all(r == historical for _, r in source_reports), "Repeated historical source agrees")
    out = (
        BASE
        / "source_sample_first_pass_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    )
    out.mkdir(parents=True, exist_ok=False)
    metadata.to_csv(out / "available_scan_metadata.csv", index=False)
    result = {
        "status": "first_sampled_source_row_transport_plan_only",
        "archive_row": selected["archive_row"],
        "source_row_retained": selected,
        "all_ten_source_rows_retained": True,
        "processable_for_transport_count": len(eligible),
        "first_pass_chosen_after_both_clock_hypotheses_utc": after.isoformat(),
        "source_scan_choice_fields": list(metadata.columns),
        "fire_quality_or_land_counts_used_for_choice": False,
        "selected_scan": choice.to_dict(),
        "sample_id": sample_id,
        "nominal_source_days": [d for d, _ in source_reports],
        "historical_source_audit": historical["audit"],
        "point_inside_native_scan_verified": False,
        "source_clock_standard_verified": False,
        "source_coordinate_start_role_verified": False,
        "L_memberships_created": 0,
        "labels_created": False,
        "gate": specification(),
        "model_trained": False,
        "final_merge_performed": False,
        "input_sha256": {
            **{p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
            **payload_pins,
        },
        "daily_member_sha256": daily_pins,
        "producer_sha256": digest(Path(__file__)),
        "artifact_sha256": {p.name: digest(p) for p in out.iterdir()},
    }
    require(
        all(digest(ROOT / rel) == h for rel, h in result["input_sha256"].items()), "Input closure"
    )
    p = out / "readback.json"
    p.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(p.read_text(encoding="utf-8")) == result, "Readback")
    print(p.relative_to(ROOT).as_posix(), digest(p))
    print("Selected source row", selected["archive_row"], "pair", sample_id)


if __name__ == "__main__":
    main()
