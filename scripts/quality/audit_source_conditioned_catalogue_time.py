"""Inspect fixed source hypotheses and preceding catalogue context; never admit events."""

import csv
import json
from bisect import bisect_right
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from wildfire_risk_prediction.core_transfer import digest
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.target_admission import specification

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/reports/dataset"
PARENT = BASE / "source_conditioned_pu_protocol_v1/20261119T200942Z_3bc1ded8/readback.json"
PARENT_SHA = "c22b246a5f93563115a193de7022d63accdabb18938ac5a635f4916ff3951df9"
CATALOGUE = ROOT / "data/interim/firms_combined_candidates_2018_2024.csv"
CATALOGUE_SHA = "37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5"
FIT_START = datetime(2018, 1, 1, tzinfo=UTC)
FIT_END = datetime(2023, 1, 1, tzinfo=UTC)


def fit_catalogue_index(rows):
    by_cell = defaultdict(list)
    seen = set()
    for row in rows:
        # Metadata role first: do not inspect other fields of calibration/heldout rows.
        value = row["detection_timestamp_utc"]
        if value[:4] not in {str(y) for y in range(2018, 2023)}:
            continue
        stamp = datetime.fromisoformat(value)
        require(
            stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0), "UTC catalogue metadata"
        )
        require(FIT_START <= stamp < FIT_END, "Fit catalogue timestamps")
        key = row["detection_id"]
        require(key not in seen, "Unique catalogue detection key")
        seen.add(key)
        by_cell[row["grid_id"]].append((stamp, key))
    return {cell: sorted(values) for cell, values in by_cell.items()}, len(seen)


def interval_hits(index, cells, start, end):
    found = []
    for cell in sorted(set(cells)):
        values = index.get(cell, [])
        stamps = [x[0] for x in values]
        found.extend(values[bisect_right(stamps, start) : bisect_right(stamps, end)])
    return sorted(found)


def inspect_window(index, cells, start):
    stamp = datetime.fromisoformat(start)
    require(stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0), "UTC source window")
    require(stamp.time().replace(tzinfo=None) == datetime.min.time(), "Midnight source window")
    end = stamp + timedelta(days=1)
    require(FIT_START <= stamp and end < FIT_END, "Fit source window")
    previous_start = stamp - timedelta(days=7)
    previous = interval_hits(index, cells, previous_start, stamp)
    current = interval_hits(index, cells, stamp, end)
    return {
        "window_start_utc": stamp.isoformat(),
        "window_end_inclusive_utc": end.isoformat(),
        "preceding_days": 7,
        "preceding_context_within_fit_period": previous_start >= FIT_START,
        "preceding_catalogue_detection_rows": len(previous),
        "window_catalogue_detection_rows": len(current),
        "last_preceding_catalogue_time": previous[-1][0].isoformat() if previous else None,
        "first_catalogue_time_in_this_window": current[0][0].isoformat() if current else None,
        "window_hit_proves_new_event": False,
        "previous_hit_proves_same_event": False,
        "no_hit_proves_fire_absence": False,
        "target": None,
    }


def examine_cases(cases, index):
    results = []
    for case in cases:
        if not case["diagnostic_focus"]:
            continue
        require(not case["researcher_retained_outside_L"], "WF1538 remains outside focus")
        require(case["target"] is None and case["membership"] == "review_unassigned", "Review only")
        for space in case["spatial_alternatives"]:
            for time in case["temporal_alternatives"]:
                item = {
                    "archive_row": case["archive_row"],
                    "radius_projection_plane_m": space["radius_projection_plane_m"],
                    "day_shift": time["day_shift"],
                    "inside_fit": time["inside_fit"],
                    "target": None,
                    "membership": "review_unassigned",
                }
                if time["inside_fit"]:
                    item.update(inspect_window(index, space["grid_ids"], time["window_start_utc"]))
                results.append(item)
    summaries = []
    for radius in (0, 250, 1000):
        for shift in (-1, 0, 1):
            selected = [
                x
                for x in results
                if x["radius_projection_plane_m"] == radius and x["day_shift"] == shift
            ]
            valid = [x for x in selected if x["inside_fit"]]
            summaries.append(
                {
                    "radius_projection_plane_m": radius,
                    "day_shift": shift,
                    "source_hypotheses_retained": len(selected),
                    "in_fit_reviewed": len(valid),
                    "with_window_catalogue_context": sum(
                        x["window_catalogue_detection_rows"] > 0 for x in valid
                    ),
                    "with_preceding_seven_day_context": sum(
                        x["preceding_catalogue_detection_rows"] > 0 for x in valid
                    ),
                    "with_both_contexts": sum(
                        x["window_catalogue_detection_rows"] > 0
                        and x["preceding_catalogue_detection_rows"] > 0
                        for x in valid
                    ),
                    "preceding_context_reaches_before_fit": sum(
                        not x["preceding_context_within_fit_period"] for x in valid
                    ),
                }
            )
    return results, summaries


def main():
    pins = {PARENT: PARENT_SHA, CATALOGUE: CATALOGUE_SHA}
    require(all(digest(p) == h for p, h in pins.items()), "Frozen protocol and catalogue")
    parent = json.loads(PARENT.read_bytes())
    pins.update({ROOT / p: h for p, h in parent["input_sha256"].items()})
    require(
        all(digest(p) == h for p, h in pins.items()), "Source, decision and previous L/U intact"
    )
    with CATALOGUE.open(encoding="utf-8-sig", newline="") as f:
        index, count = fit_catalogue_index(csv.DictReader(f))
    rows, summary = examine_cases(parent["cases"], index)
    require(
        len(rows) == 380 * 9 and all(x["source_hypotheses_retained"] == 380 for x in summary),
        "Fixed focus and nine scenarios without outcome selection",
    )
    report = {
        "status": "fixed_source_catalogue_time_context_reviewed_not_event_acceptance",
        "fit_catalogue_detection_rows": count,
        "source_rows_retained_in_parent": 424,
        "source_focus_rows": 380,
        "source_hypothesis_rows": len(rows),
        "catalogue_location_rule": (
            "centres_in_prepared_possible_cells;not_point_distance_or_native_support"
        ),
        "preceding_days_are_event_quiet_period": False,
        "detection_free_period_proves_new_event": False,
        "summaries": summary,
        "rows": rows,
        "matching_sources_selected_for_L": False,
        "clock_selected_from_matches": False,
        "catalogue_context_fraction_is_recall_or_positive_purity": False,
        "nominal_or_daily_observation_verified": False,
        "new_L_memberships": 0,
        "binary_labels_created": 0,
        "rates_estimated": False,
        "model_trained": False,
        "final_merge_performed": False,
        "gate": specification(),
        "input_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
        "producer_sha256": digest(Path(__file__)),
    }
    out = (
        BASE
        / "source_conditioned_catalogue_time_v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
    )
    out.mkdir(parents=True)
    path = out / "readback.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_bytes()) == report, "Saved catalogue context readback")
    require(all(digest(p) == h for p, h in pins.items()), "Inputs unchanged at closure")
    print(out.relative_to(ROOT).as_posix())
    print(json.dumps(summary))
    print("PASS fixed_source_time_context_only; not new events, recall, labels or PU acceptance")
    print("readback_sha256", digest(path))


if __name__ == "__main__":
    main()
