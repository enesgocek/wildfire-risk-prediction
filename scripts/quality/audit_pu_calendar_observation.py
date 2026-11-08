"""Audit a detection-independent training frame and nominal observation availability."""

import hashlib
import io
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import geopandas as gpd
import numpy as np
import pandas as pd
from review_public_event_cover import require, sha
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json

from wildfire_risk_prediction.dataset_batch import GRID_COUNT, calendar_inventory
from wildfire_risk_prediction.feature_month import calendar_days
from wildfire_risk_prediction.observation_expansion import province_support
from wildfire_risk_prediction.observation_window_source import (
    COMPACT_SHA,
    DELIVERY,
    JULY,
    PARTS_SHA,
)

FEATURES = BASE / "candidate_audit_v1/20261014T143254Z_0a72ff05/readback.json"
OBS = BASE / "observation_materialization_v1/20261014T145638Z_c0881064"
OBS_SHA = "fb5fa5ce8c83be2c4e21b130bb06935a5e2d8014e45460c1f61660b73262cb14"
PARTS = ROOT / "data/interim/grid_aoi_parts.geojson"
PROVINCES = ROOT / "data/raw/boundaries/gaul2025/20261014T231843Z_2271840f/provinces.geojson"
SENSORS = ("SNPP", "N20")
SCAN_COLUMNS = ["grid_id", "sensor", "land_nominal_input_no_residual"]
OBS_COLUMNS = [
    "grid_id",
    "prediction_timestamp_utc",
    "obs_product_present",
    "obs_source_status",
    "obs_daily_observation_status",
    "obs_negative_label_permitted",
    "obs_nominal_granule_day",
    "obs_target_window_alignment",
    "obs_cloud",
    "obs_land_nominal_input_no_residual",
    "obs_nominal_land_center_longest_envelope_gap_seconds",
]
SEASONS = ("DJF", "MAM", "JJA", "SON")


def scan_days(report, grid_ids, retain):
    month = report["month"]
    monthly = f"{DELIVERY}/month/{month}/payload.zip"
    pins = report["input_payload_sha256"]
    archive = None
    if month == "2023-07":
        archive = ZipFile(retain(ROOT / JULY, pins[JULY]))
    elif monthly in pins:
        archive = ZipFile(retain(ROOT / monthly, pins[monthly]))
    try:
        for day in report["days"]:
            if day in report["missing_source_days"]:
                yield day, None
                continue
            if month == "2023-07":
                meta = archive.read(f"{day}/report.json")
                raw = archive.read(f"{day}/scan_grid.csv")
            else:
                day_path = f"{DELIVERY}/day/{day}/payload.zip"
                payload = (
                    io.BytesIO(archive.read(f"{day}.zip"))
                    if archive is not None
                    else retain(ROOT / day_path, pins[day_path])
                )
                with ZipFile(payload) as daily:
                    meta, raw = daily.read("report.json"), daily.read("scan_grid.csv")
            source = json.loads(meta)
            require(
                source["day"] == day
                and source["parts_sha256"] == PARTS_SHA
                and source["compact_code_sha256"] == COMPACT_SHA
                and source["negative_label_permitted"] is False
                and source["daily_observation_status"] == "unknown"
                and hashlib.sha256(raw).hexdigest() == source["outputs_sha256"]["scan_grid.csv"],
                "Verified compact scan identity",
            )
            rows = pd.read_csv(io.BytesIO(raw), usecols=SCAN_COLUMNS)
            require(
                rows.grid_id.isin(grid_ids).all()
                and rows.sensor.isin(SENSORS).all()
                and rows.land_nominal_input_no_residual.ge(0).all(),
                "Known scan keys and nonnegative counts",
            )
            land = rows.groupby(["sensor", "grid_id"]).land_nominal_input_no_residual.sum()
            yield day, (set(rows.sensor), land)
    finally:
        if archive is not None:
            archive.close()


def audit_month(entry, report, grids):
    pins = {}

    def retain(path, digest):
        require(path.resolve(strict=True).is_relative_to(ROOT), "Contained input")
        require(sha(path) == digest, "Input digest")
        pins[path.relative_to(ROOT).as_posix()] = digest
        return path

    month = entry["month"]
    days = calendar_days(month)
    feature = read_json(retain(ROOT / entry["path"], entry["sha256"]))
    require(
        feature["month"] == month
        and feature["split"] == "train"
        and feature["days"] == days
        and feature["rows"] == entry["rows"]
        and not feature["labels_created"]
        and feature["inputs_sha256"][PARTS.relative_to(ROOT).as_posix()] == PARTS_SHA,
        "Feature calendar identity",
    )
    require(
        report["days"] == days and report["negative_label_permitted"] is False,
        "Observation calendar",
    )
    folder = OBS / month
    require(read_json(folder / "readback.json") == report, "Monthly receipt matches master")
    pins[(folder / "readback.json").relative_to(ROOT).as_posix()] = sha(folder / "readback.json")
    sidecar = pd.read_csv(
        retain(folder / "observations.csv.gz", report["table_sha256"]), usecols=OBS_COLUMNS
    )
    require(
        len(sidecar) == len(days) * GRID_COUNT
        and sidecar.obs_daily_observation_status.eq("unknown").all()
        and sidecar.obs_negative_label_permitted.eq(False).all()
        and sidecar.obs_target_window_alignment.eq("boundary_timing_unresolved").all()
        and set(sidecar.obs_nominal_granule_day) == set(days),
        "Complete nominal calendar, closed gates",
    )
    strata, source_days = {}, {}
    metrics = OBS_COLUMNS[-3:]
    for (day, scan), (table_day, frame) in zip(
        scan_days(report, grids.index, retain),
        sidecar.groupby("obs_nominal_granule_day"),
        strict=True,
    ):
        require(
            day == table_day
            and frame.grid_id.is_unique
            and set(frame.grid_id) == set(grids.index)
            and frame.prediction_timestamp_utc.eq(day + "T00:00:00+00:00").all(),
            "Exact day/grid membership",
        )
        frame = frame.set_index("grid_id").loc[grids.index]
        present = scan is not None
        state = "accepted_compact_product" if present else "deferred_source_day"
        require(
            frame.obs_product_present.eq(present).all() and frame.obs_source_status.eq(state).all(),
            "Product presence preserved",
        )
        if not present:
            require(frame[metrics].isna().all().all(), "Missing source is not observed zero")
            source_days[day] = None
        else:
            active, land = scan
            source_days[day] = sorted(active)
            by_sensor = land.unstack("sensor", fill_value=0).reindex(
                index=grids.index, columns=SENSORS, fill_value=0
            )
            require(
                np.array_equal(by_sensor.sum(axis=1), frame.obs_land_nominal_input_no_residual),
                "Sensor sums match observation sidecar",
            )
        for province in grids.unique():
            members = grids.eq(province)
            counts = strata.setdefault(province, Counter())
            size = int(members.sum())
            counts["calendar_rows"] += size
            if not present:
                counts["missing_product"] += size
                continue
            obs = frame.loc[members]
            snpp, n20 = (by_sensor.loc[members, key].gt(0) for key in SENSORS)
            counts["product_rows"] += size
            counts["with_cloud_centers"] += int(obs.obs_cloud.gt(0).sum())
            counts["nominal_land_gap_at_least_12h"] += int(
                obs.obs_nominal_land_center_longest_envelope_gap_seconds.ge(43200).sum()
            )
            counts["with_land_centers"] += int((snpp | n20).sum())
            if active == set(SENSORS):
                counts["both_sensor_source_rows"] += size
                counts["both_land"] += int((snpp & n20).sum())
                counts["only_snpp_land"] += int((snpp & ~n20).sum())
                counts["only_n20_land"] += int((~snpp & n20).sum())
                counts["neither_land"] += int((~snpp & ~n20).sum())
    for counts in strata.values():
        require(
            counts["calendar_rows"] == counts["product_rows"] + counts["missing_product"],
            "Row conservation",
        )
        require(
            counts["both_sensor_source_rows"]
            == sum(
                counts[k] for k in ("both_land", "only_snpp_land", "only_n20_land", "neither_land")
            ),
            "Exclusive sensor witness groups",
        )
    return {
        "month": month,
        "province_counts": {k: dict(v) for k, v in strata.items()},
        "source_days": source_days,
        "source_sha256": pins,
    }


def rollup(months):
    groups = {}
    for result in months:
        month = result["month"]
        season = SEASONS[int(month[5:7]) % 12 // 3]
        for province, counts in result["province_counts"].items():
            for key in ("all", province, month[:4], season, f"{province}|{month[:4]}|{season}"):
                groups.setdefault(key, Counter()).update(counts)
    return {key: dict(counts) for key, counts in sorted(groups.items())}


def main():
    root_pins = {
        FEATURES: "c39536f74cf1b44dec1eec08b94941b495132e759d6ed0005a88110c1f46dbe8",
        OBS / "accepted_readback.json": OBS_SHA,
        PARTS: PARTS_SHA,
        PROVINCES: "ffb43d77b0e7cba1dbe3c605454e468eb46d4eaefdcc5d2ebd6612ea9e75d2fb",
    }
    require(
        all(sha(path) == digest for path, digest in root_pins.items()), "Frozen calendar sources"
    )
    features, observation = read_json(FEATURES), read_json(OBS / "accepted_readback.json")
    entries = {e["month"]: e for e in features["reports"]}
    obs = {e["month"]: e for e in observation["reports"]}
    months = [r["month"] for r in calendar_inventory()]
    require(
        len(entries) == len(obs) == len(months) == 72
        and set(entries) == set(obs) == set(months)
        and features["candidate_calendar_complete"]
        and observation["scope_is_full_training"],
        "Full training calendar only",
    )
    parts, borders = gpd.read_file(PARTS), gpd.read_file(PROVINCES)
    primary, _ = province_support(parts, borders)
    grids = primary.set_index("grid_id").primary_province.sort_index()
    require(
        len(grids) == GRID_COUNT and grids.notna().all() and grids.nunique() == 4,
        "Four-province frame",
    )
    results = []
    with ThreadPoolExecutor(max_workers=2) as workers:
        for result in workers.map(
            lambda month: audit_month(entries[month], obs[month], grids), months
        ):
            results.append(result)
            if result["month"].endswith(("-06", "-12")):
                print("Checked through", result["month"], flush=True)
    totals = rollup(results)
    overall = totals["all"]
    require(
        overall["calendar_rows"]
        == features["verified_candidate_rows"]
        == observation["totals"]["rows"]
        and overall["product_rows"] == observation["totals"]["rows_with_product"]
        and overall["missing_product"] == observation["totals"]["rows_missing_product"]
        and overall["with_cloud_centers"] == observation["totals"]["rows_with_cloud_centers"]
        and overall["with_land_centers"] == observation["totals"]["rows_with_nominal_land_centers"],
        "Full frame totals reconcile",
    )
    dates = {day: sensors for month in results for day, sensors in month["source_days"].items()}
    require(
        len(dates) == 2191
        and [d for d, v in dates.items() if v is None] == observation["missing_source_days"],
        "Exact missing days",
    )
    root_pins[Path(__file__).resolve()] = sha(Path(__file__))
    require(all(sha(path) == digest for path, digest in root_pins.items()), "Root inputs unchanged")
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "pu_calendar_observation_v1" / run
    out.mkdir(parents=True, exist_ok=False)
    frame = {
        "unit": "grid_id × prediction_day_utc",
        "rows_before_eligibility": overall["calendar_rows"],
        "grid_primary_provinces": grids.to_dict(),
        "prediction_days_utc": list(dates),
        "constructed_without_event_selection": True,
        "eligible_unlabelled_training_pool_accepted": False,
    }
    write_json(out / "frame.json", frame)
    report = {
        "source_sha256": {
            p.relative_to(ROOT).as_posix(): digest for p, digest in root_pins.items()
        },
        "frame_sha256": sha(out / "frame.json"),
        "months": results,
        "counts": totals,
        "province_boundary_cells": int(primary.province_intersection_count.gt(1).sum()),
        "nominal_source_days": dates,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    write_json(out / "readback.json", report)
    print((out / "readback.json").relative_to(ROOT).as_posix(), sha(out / "readback.json"))


if __name__ == "__main__":
    main()
