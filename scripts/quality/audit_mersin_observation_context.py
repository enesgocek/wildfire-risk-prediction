"""Compare public incident records with catalogue and nominal scan evidence."""

import csv
import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pandas as pd
from audit_mersin_open_incidents import (
    ARCHIVE,
    CATALOG,
    GRID,
    PINS,
    PROVINCES,
    ROOT,
    YEARS,
    clock_diagnostics,
    read_incidents,
    spatial_diagnostics,
)
from audit_stage_one_selection import (
    GAP,
    KEYS,
    LAND,
    OBS,
    OBS_COLUMNS,
    PRESENT,
    read_report,
    verify,
)
from audit_stage_one_selection import PINS as OBS_PINS

from wildfire_risk_prediction.event_review import training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import detection_windows, specification

THERMAL = ["obs_nominal_confidence_fire", "obs_high_confidence_fire"]
AREA_CLASSES = {True: "under_1_ha", False: "at_least_1_ha"}


def incident_windows():
    events, _ = read_incidents()
    cells, _ = spatial_diagnostics(events)
    clocks = clock_diagnostics(events)
    records = events.join(cells.rename("grid_id"), how="inner").join(clocks, how="inner")
    minutes = records.ignition_hour.map(lambda hour: round(Decimal(hour) * 60))
    stated = pd.to_datetime(records.date) + pd.to_timedelta(minutes, unit="m")
    records["small"] = records.burned_area_ha.map(Decimal).lt(1)
    scenarios = []
    for basis, zone in (("if_source_utc", "UTC"), ("if_source_turkiye", "Europe/Istanbul")):
        times = stated.dt.tz_localize(zone).dt.tz_convert("UTC")
        windows = detection_windows(times.map(pd.Timestamp.isoformat))
        require(
            not windows.training_window_boundary_review.any()
            and windows.prediction_timestamp_utc.dt.date.eq(records[basis]).all(),
            "Published clock scenarios must be in the training window",
        )
        scenarios.append(
            records[["grid_id", "small"]].assign(
                basis=basis,
                stated_time=times,
                prediction_timestamp_utc=windows.prediction_timestamp_utc.map(
                    pd.Timestamp.isoformat
                ),
            )
        )
    return pd.concat(scenarios).rename_axis("archive_row").reset_index()


def nominal_rows(windows):
    path = OBS / "accepted_readback.json"
    report = read_report(path)
    manifest = {row["month"]: row["table_sha256"] for row in report["reports"]}
    unique = windows[KEYS].drop_duplicates()
    parts, hashes = [], {}
    for month, keys in unique.groupby(unique[KEYS[1]].str[:7]):
        table = verify(OBS / month / "observations.csv.gz", manifest[month])
        hashes[month] = manifest[month]
        monthly = pd.read_csv(table, usecols=[*OBS_COLUMNS, *THERMAL])
        parts.append(keys.merge(monthly, on=KEYS, how="inner", validate="one_to_one"))
    result = pd.concat(parts, ignore_index=True)
    present = result[PRESENT].eq(True)
    require(
        len(result) == len(unique)
        and result[PRESENT].notna().all()
        and result.obs_daily_observation_status.eq("unknown").all()
        and result.obs_negative_label_permitted.eq(False).all()
        and result.obs_target_window_alignment.eq("boundary_timing_unresolved").all()
        and result.loc[present, [LAND, GAP, *THERMAL]].notna().all().all()
        and result.loc[~present, [LAND, GAP, *THERMAL]].isna().all().all(),
        "Expected complete nominal key and explicit missingness",
    )
    return result, hashes


def catalogue_flags(frame):
    prefixes = tuple(f"{year}-" for year in sorted(YEARS))
    cells = set(frame.grid_id)
    with CATALOG.open(encoding="utf-8-sig", newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["detection_timestamp_utc"].startswith(prefixes) and row["grid_id"] in cells
        ]
    detections = training_detections(pd.DataFrame(rows))
    dates = detection_windows(detections.timestamp.map(pd.Timestamp.isoformat))
    dates = dates.loc[~dates.training_window_boundary_review]
    detections = detections.loc[dates.index, ["grid_id", "timestamp"]].assign(
        prediction_timestamp_utc=dates.prediction_timestamp_utc.map(pd.Timestamp.isoformat)
    )
    latest = detections.groupby(KEYS).timestamp.max().rename("last_candidate")
    joined = frame.merge(latest, on=KEYS, how="left", validate="many_to_one")
    joined["catalogue_same_window"] = joined.last_candidate.notna()
    joined["catalogue_at_or_after"] = joined.last_candidate.ge(joined.stated_time)
    return joined


def summarize(frame):
    metrics = [
        "product_present",
        "zero_land_centers",
        "gap_at_least_12h",
        "thermal_centers_present",
        "catalogue_same_window",
        "catalogue_at_or_after",
    ]
    groups = []
    for (basis, small), rows in frame.groupby(["basis", "small"]):
        context = {}
        for name, subset in rows.groupby("observation_context"):
            context[name] = {"rows": len(subset), **subset[metrics].sum().astype(int).to_dict()}
        groups.append(
            {
                "clock_basis": basis,
                "area_group": AREA_CLASSES[small],
                "rows": len(rows),
                **rows[metrics].sum().astype(int).to_dict(),
                "by_nominal_context": context,
            }
        )
    both = frame.pivot(index="archive_row", columns="basis", values="catalogue_at_or_after")
    small = frame.drop_duplicates("archive_row").set_index("archive_row").small.reindex(both.index)
    agreement = {}
    for flag, group_name in AREA_CLASSES.items():
        flags = both.loc[small.eq(flag)].sum(axis=1)
        agreement[group_name] = {
            "both": int(flags.eq(2).sum()),
            "one_only": int(flags.eq(1).sum()),
            "neither": int(flags.eq(0).sum()),
        }
    return groups, agreement


def main():
    inputs = {path: PINS[path] for path in (ARCHIVE, PROVINCES, GRID, CATALOG)}
    for path, digest in inputs.items():
        verify(path, digest)
    windows = incident_windows()
    require(len(windows) == 2 * windows.archive_row.nunique(), "One row per clock interpretation")
    observed, hashes = nominal_rows(windows)
    frame = catalogue_flags(windows.merge(observed, on=KEYS, validate="many_to_one"))
    present = frame[PRESENT].eq(True)
    frame["product_present"] = present
    frame["zero_land_centers"] = present & frame[LAND].eq(0)
    frame["gap_at_least_12h"] = present & frame[GAP].ge(43200)
    frame["thermal_centers_present"] = present & frame[THERMAL].sum(axis=1).gt(0)
    frame["observation_context"] = "land_centers_gap_under_12h"
    frame.loc[frame.gap_at_least_12h, "observation_context"] = "land_centers_gap_at_least_12h"
    frame.loc[frame.zero_land_centers, "observation_context"] = "zero_selected_land_centers"
    frame.loc[~present, "observation_context"] = "product_missing"
    groups, agreement = summarize(frame)
    result = {
        "scope": "2018_2023_mersin_archive_row_diagnostics_only",
        "archive_rows": windows.archive_row.nunique(),
        "unique_nominal_grid_day_keys": len(observed),
        "input_sha256": {
            path.relative_to(ROOT).as_posix(): digest
            for path, digest in {
                **inputs,
                OBS / "accepted_readback.json": OBS_PINS[OBS / "accepted_readback.json"],
            }.items()
        },
        "observation_table_sha256_by_month": hashes,
        "by_clock_and_reported_final_area": groups,
        "same_window_at_or_after_catalogue_agreement": agreement,
        "target_admission": specification(),
    }
    out = (
        OBS.parent.parent
        / "mersin_observation_context_v1"
        / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / "readback.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == result, "Output roundtrip")
    print(path.relative_to(ROOT).as_posix())
    print(hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
