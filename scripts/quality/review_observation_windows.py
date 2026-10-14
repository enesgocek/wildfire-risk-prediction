"""Offline neighbouring-day readback for eleven purpose-selected training windows."""

import hashlib
import io
import json
import socket
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.observation_window import FIELDS, review_window, source_schedule
from wildfire_risk_prediction.water_scope import attach_water_scope

ROOT = Path(__file__).resolve().parents[2]
OBS = "outputs/reports/dataset/observation_materialization_v1/20261014T145638Z_c0881064"
REVIEW = "outputs/reports/dataset/observation_review_v1/20261014T174956Z_cca3d882"
WATER = "outputs/reports/dataset/water_scope_v1/20261014T185242Z_f2e469bd"
PROTECTED = (
    "outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/"
    "protected_inputs_readback_20261013.json"
)
REGISTRY = "configs/gcp_source_blocks_2026-10-13.json"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def deny(*args, **kwargs):
    raise RuntimeError("Offline observation-window review")


def run():
    pins = {}

    def retained(name, expected=None):
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(), "Regular window input")
        digest = pins.get(name) or sha(path)
        require(expected is None or digest == expected, "Window input hash changed")
        pins[name] = digest
        return path

    def report(name, expected):
        return json.loads(retained(name, expected).read_text(encoding="utf-8"))

    master = report(
        OBS + "/accepted_readback.json",
        "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14",
    )
    prior = report(
        REVIEW + "/readback.json",
        "32f75f98feeef857e979fa50340c3b1a01053617f97aa72db6be53bf4a297c44",
    )
    prior_files = {n: retained(REVIEW + "/" + n, h) for n, h in prior["artifact_sha256"].items()}
    examples = pd.read_csv(prior_files["human_examples.csv"], float_precision="round_trip")
    water_report = report(
        WATER + "/readback.json",
        "7b5d296bae6c3744790817409db4bce3a947e92919a06abde9271eac07814cae",
    )
    scope = pd.read_csv(
        retained(
            WATER + "/grid_water_scope.csv", water_report["artifact_sha256"]["grid_water_scope.csv"]
        )
    )
    registry = report(REGISTRY, "c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95")
    deferred = set(registry["deferred_days"])
    units = examples[["example_id", "grid_id", "obs_nominal_granule_day"]].rename(
        columns={"example_id": "window_id", "obs_nominal_granule_day": "day"}
    )
    extras = pd.DataFrame(
        [
            ("G_after_midnight_boundary", "E6933_5K_V1_C522_R918", "2022-01-19"),
            ("H_before_june_source_gap", "E6933_5K_V1_C568_R865", "2018-06-12"),
            ("I_before_december_source_gap", "E6933_5K_V1_C568_R865", "2023-12-30"),
            ("J_training_end_source_gap", "E6933_5K_V1_C568_R865", "2023-12-31"),
            ("K_training_start", "E6933_5K_V1_C522_R918", "2018-01-01"),
        ],
        columns=["window_id", "grid_id", "day"],
    )
    units = pd.concat([units, extras], ignore_index=True)
    require(len(units) == 11 and units.window_id.is_unique, "Fixed purpose selection")
    schedules, requested = {}, {}
    for row in units.itertuples():
        schedule = source_schedule(row.day, deferred)
        schedules[row.window_id] = schedule
        for day in schedule.loc[
            schedule.source_status.eq("available_training_packet"), "source_nominal_day"
        ]:
            requested.setdefault(day, set()).add(row.grid_id)
    reports = {r["month"]: r for r in master["reports"]}
    cache = {}
    inner_hashes = {}
    for day, grids in sorted(requested.items()):
        monthly = reports[day[:7]]
        # The accepted master embeds the exact monthly report; changed metadata is rejected.
        local = json.loads(retained(OBS + "/" + day[:7] + "/readback.json").read_text())
        require(local == monthly, "Monthly report equals accepted master")
        payloads = monthly["input_payload_sha256"]
        if day[:7] == "2023-07":
            name = "outputs/cloud_month/received/l2_month_2023_07_results.zip"
            with zipfile.ZipFile(retained(name, payloads[name])) as archive:
                raw = {n: archive.read(day + "/" + n) for n in ("report.json", "scan_grid.csv")}
        else:
            month_name = (
                "outputs/gcp_delivery/2026-10-14/compact/products/month/" + day[:7] + "/payload.zip"
            )
            if month_name in payloads:
                with zipfile.ZipFile(retained(month_name, payloads[month_name])) as archive:
                    data = archive.read(day + ".zip")
            else:
                name = (
                    "outputs/gcp_delivery/2026-10-14/compact/products/day/" + day + "/payload.zip"
                )
                data = retained(name, payloads[name]).read_bytes()
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                raw = {n: archive.read(n) for n in ("report.json", "scan_grid.csv")}
        daily = json.loads(raw["report.json"])
        digest = hashlib.sha256(raw["scan_grid.csv"]).hexdigest()
        require(
            daily["day"] == day
            and daily["daily_observation_status"] == "unknown"
            and daily["negative_label_permitted"] is False
            and daily["parts_sha256"]
            == "f589f6027d28ce1911d080763e195062dcaaf4e9567fb4072d14c454bf28a2f9"
            and daily["compact_code_sha256"]
            == "f09e73837732160a65cc059c382c2ed85a95de0985aa470c1ec5789f6dc17b54"
            and daily["outputs_sha256"]["scan_grid.csv"] == digest,
            "Accepted daily scan identity and closed gates",
        )
        inner_hashes[day] = {n: hashlib.sha256(b).hexdigest() for n, b in raw.items()}
        frame = pd.read_csv(
            io.BytesIO(raw["scan_grid.csv"]), usecols=FIELDS, dtype={"pair_key": str}
        )
        require(
            not frame.duplicated(["grid_id", "sensor", "pair_key", "scan_index"]).any(),
            "Unique daily scan-grid keys",
        )
        frame = frame.loc[frame.grid_id.isin(grids)].copy()
        frame["source_nominal_day"] = day
        cache[day] = frame
        print("Neighbour source checked:", day, flush=True)

    all_scans, summaries, all_schedules = [], [], []
    for row in units.itertuples():
        schedule = schedules[row.window_id]
        pieces = [
            cache[d].loc[cache[d].grid_id.eq(row.grid_id)]
            for d in schedule.source_nominal_day
            if d in cache
        ]
        frame = (
            pd.concat(pieces, ignore_index=True)
            if pieces
            else pd.DataFrame(columns=FIELDS + ["source_nominal_day"])
        )
        scans, summary = review_window(frame, row.day, row.grid_id, schedule)
        scans["window_id"] = row.window_id
        summary["window_id"] = row.window_id
        schedule = schedule.assign(window_id=row.window_id, grid_id=row.grid_id)
        all_scans.append(scans)
        summaries.append(summary)
        all_schedules.append(schedule)
    summary = attach_water_scope(pd.DataFrame(summaries), scope)
    scans = pd.concat(all_scans, ignore_index=True)
    schedule = pd.concat(all_schedules, ignore_index=True)
    for name in (
        "src/wildfire_risk_prediction/observation_window.py",
        "src/wildfire_risk_prediction/water_scope.py",
        "src/wildfire_risk_prediction/target_admission.py",
        "scripts/quality/review_observation_windows.py",
        PROTECTED,
    ):
        retained(name)
    protected = json.loads((ROOT / PROTECTED).read_text())
    for name, digest in protected.items():
        retained(name, digest)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "outputs/reports/dataset/observation_windows_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, frame in (
        ("window_summary.csv", summary),
        ("window_scan_rows.csv", scans),
        ("source_day_schedule.csv", schedule),
    ):
        path = out / name
        frame.to_csv(path, index=False, mode="x")
        strings = {
            c: str
            for c in frame
            if not frame[c].dropna().empty
            and frame[c].dropna().map(lambda v: isinstance(v, str)).all()
        }
        reread = pd.read_csv(path, dtype=strings, float_precision="round_trip")
        expected = (
            frame.reset_index(drop=True)
            .astype(object)
            .where(frame.reset_index(drop=True).notna(), None)
        )
        actual = reread.astype(object).where(reread.notna(), None)
        pd.testing.assert_frame_equal(expected, actual, check_exact=True)
        artifacts[name] = sha(path)
    result = {
        "status": "neighbour_scan_window_readback_passed",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha256": pins,
        "inner_daily_sha256": inner_hashes,
        "artifact_sha256": artifacts,
        "purpose_selected_windows": len(summary),
        "distinct_nominal_source_days_read": len(cache),
        "windows_with_all_three_nominal_packets": int(
            summary.all_three_nominal_packets_present.sum()
        ),
        "windows_with_loaded_boundary_scans": int(summary.loaded_boundary_scan_rows.gt(0).sum()),
        "windows_with_loaded_boundary_thermal_centers": int(
            summary.loaded_thermal_center_boundary_count.gt(0).sum()
        ),
        "source_schedule_status_counts": schedule.source_status.value_counts().to_dict(),
        "water_scope_excluded_windows_retained_for_audit": int(
            (~summary.water_scope_included).sum()
        ),
        "protected_inputs_verified": len(protected),
        "daily_observation_status": "unknown",
        "labels_created": False,
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "model_ready": False,
        "validation_accessed": False,
        "final_test_accessed": False,
        "network_requests": 0,
        "limits": [
            "Purpose-selected windows; no population rate or full training window acceptance",
            "Counts and gaps refer to loaded source packets, not missing-source upper bounds",
            "Three available nominal packets do not establish scientific observation completeness",
            "Boundary centers stay unassigned; one center may be uncertain in two windows",
            "No exact pixel time is reconstructed from scan midpoint or FIRMS acquisition minute",
            "Area unions are not re-clipped and do not become window-aligned coverage",
            "Center envelope gaps are not continuous no-observation or fire lifetime intervals",
        ],
    }
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "Input closure")
    path = out / "readback.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text()) == result, "Report JSON readback")
    require(all(sha(out / n) == h for n, h in artifacts.items()), "Artifact closure")
    (out / "completion_readback.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "report_sha256": sha(path),
                "input_files_verified": len(pins),
                "artifacts_verified": len(artifacts),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Window review result:", out.relative_to(ROOT).as_posix(), flush=True)
    return out


if __name__ == "__main__":
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    run()
