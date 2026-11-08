"""Stress-test time and distance screens for candidate links without assigning targets."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd
from review_pu_candidate_timeline import GRAPH
from review_pu_stable_batch import catalogue_sources
from review_public_event_cover import require, sha
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json

from wildfire_risk_prediction.event_review import GEOD

CASE = BASE / "stratified_event_candidate_v1/20261108T004510Z_5cca8b52/readback.json"
DISPATCH = BASE / "izmir_dispatch_context_v1/20261108T004400Z_7094bbfd/readback.json"
RADII = (500, 1000, 2000, 5000)
MINUTES = (15, 30, 60, 90, 120)
OFFSETS = (*range(-7, 0), *range(1, 8))
# These coordinates are settlement reference points, not incident origins.
PROXIES = {
    "H03": (31.5995893, 36.7709979),
    "H04": (29.800556, 36.291944),
    "H12": (27.70947, 38.41904),
    "H22": (27.580235, 37.280785),
}
# Reported approximate local start times. Dispatch is evaluated separately.
REPORT_TIMES = {"H03": ("12:30",), "H04": ("12:00",), "H12": ("14:06",), "H22": ("13:00", "13:30")}


def utc_at(day, local_hour):
    offset = "+03:00"
    return pd.Timestamp(f"{day}T{local_hour}:00{offset}").tz_convert("UTC")


def first_points(graph, source, retain):
    frames = {}
    for scenario, meta in sorted(graph["artifact_sha256"].items()):
        table = pd.read_csv(
            retain(
                f"data/interim/event_grouping/{scenario}_assignments.csv",
                meta["assignments_sha256"],
            )
        )
        require(
            table.detection_id.is_unique and set(table.detection_id) == set(source.index),
            "Complete training assignments",
        )
        table["utc"] = pd.to_datetime(table.timestamp, utc=True, format="ISO8601")
        first = table.loc[table.utc.eq(table.groupby("cluster_id").utc.transform("min"))].copy()
        selected = source.loc[first.detection_id]
        require(
            first.utc.tolist() == selected.timestamp.tolist()
            and first.grid_id.tolist() == selected.grid_id.tolist(),
            "First point time and grid",
        )
        first["longitude"] = selected.longitude.to_numpy()
        first["latitude"] = selected.latitude.to_numpy()
        frames[scenario] = first
    require(len(frames) == 9, "All registered scenarios")
    return frames


def match_windows(frames, lon, lat, starts, anchor_id):
    results = {}
    for scenario, frame in frames.items():
        first_day, last_day = min(starts.values()), max(starts.values())
        nearby_time = frame.loc[
            frame.utc.ge(first_day) & frame.utc.le(last_day + timedelta(minutes=max(MINUTES)))
        ].copy()
        _, _, distances = GEOD.inv(
            [lon] * len(nearby_time),
            [lat] * len(nearby_time),
            nearby_time.longitude.to_numpy(),
            nearby_time.latitude.to_numpy(),
        )
        nearby_time["distance_m"] = distances
        windows = {}
        for offset, start in starts.items():
            elapsed = (nearby_time.utc - start).dt.total_seconds() / 60
            sample = nearby_time.loc[elapsed.between(0, max(MINUTES))].copy()
            sample["elapsed_minutes"] = elapsed.loc[sample.index]
            windows[str(offset)] = {
                f"{radius}m_{minutes}min": {
                    "group_count": int(matches.cluster_id.nunique()),
                    "point_count": len(matches),
                    "contains_anchor": bool(matches.detection_id.eq(anchor_id).any()),
                }
                for radius in RADII
                for minutes in MINUTES
                for matches in [
                    sample.loc[sample.distance_m.le(radius) & sample.elapsed_minutes.le(minutes)]
                ]
            }
        results[scenario] = windows
    return results


def summarise(scenarios):
    same, shifted = {}, {}
    for radius in RADII:
        for minutes in MINUTES:
            key = f"{radius}m_{minutes}min"
            observed = [s["0"][key] for s in scenarios.values()]
            group_counts = [r["group_count"] for r in observed]
            same[key] = {
                "group_count_range": [min(group_counts), max(group_counts)],
                "anchor_scenarios": sum(r["contains_anchor"] for r in observed),
            }
            shifted[key] = sum(
                any(s[str(day)][key]["group_count"] > 0 for s in scenarios.values())
                for day in OFFSETS
            )
    return same, shifted


def main():
    pins = {}

    def retain(name, expected=None):
        path = ROOT / name
        require(path.resolve(strict=True).is_relative_to(ROOT), "Contained input")
        digest = sha(path)
        require(expected is None or digest == expected, "Input identity")
        pins[path.relative_to(ROOT).as_posix()] = digest
        return path

    cases = read_json(
        retain(CASE, "95fe28b6c421797552a550d0461f18f3f8224e8a0e9f2ef08942aa82ad77bd57")
    )
    dispatch = read_json(
        retain(DISPATCH, "0adaa6638c320b276bd63860cc48f97956d6cd7fae4f82397b530eb75e4342c6")
    )
    graph = read_json(
        retain(
            f"{GRAPH}/review.json",
            "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e",
        )
    )
    require(
        len(cases["cases"]) == 5
        and all(
            not r["independent_origin_verified"] and r["target"] is None for r in cases["cases"]
        ),
        "Unconfirmed pilot",
    )
    source = catalogue_sources(retain, graph).set_index("detection_id", verify_integrity=True)
    frames = first_points(graph, source, retain)
    (h12,) = (r for r in dispatch["records"] if r["TARIH"].startswith("2023-07-25"))
    (hour_key,) = (key for key in h12 if key.endswith("_CIKIS_SAATI"))
    require(
        h12[hour_key] == "14:17" and h12["YANGIN_TURU"].startswith("ORMAN/"), "Dispatch context"
    )
    results = []
    for case in cases["cases"]:
        slot = case["slot"]
        if slot not in PROXIES:
            continue
        day = case["detected_utc"][:10]
        lon, lat = PROXIES[slot]
        _, _, distance = GEOD.inv(lon, lat, case["longitude"], case["latitude"])
        hypotheses = [(hour, "approximate_reported_start") for hour in REPORT_TIMES[slot]]
        if slot == "H12":
            hypotheses.append((h12[hour_key], "municipal_dispatch"))
        for hour, kind in hypotheses:
            start = utc_at(day, hour)
            require(start.tz_convert("UTC").date().isoformat() == day, "Same UTC date")
            starts = {offset: start + timedelta(days=offset) for offset in (0, *OFFSETS)}
            scenarios = match_windows(frames, lon, lat, starts, case["id"])
            same, shifted = summarise(scenarios)
            results.append(
                {
                    "slot": slot,
                    "time_type": kind,
                    "local_time": hour,
                    "anchor_distance_to_settlement_m": float(distance),
                    "anchor_minutes_after_report": (
                        pd.Timestamp(case["detected_utc"]) - start
                    ).total_seconds()
                    / 60,
                    "observed_day": same,
                    "shifted_days_with_any_candidate": shifted,
                    "scenarios": scenarios,
                    "target": None,
                }
            )
    require(len(results) == 6, "Four anchors and six source times")
    pool = []
    for name, size in (("strongest_context", 2), ("all_reviewed_contexts", 5)):
        for wrong in range(3):
            pool.append(
                {
                    "pool": name,
                    "hypothetical_pool_size": size,
                    "assumed_wrong_links": wrong,
                    "assumed_wrong_fraction": wrong / size,
                    "remaining_if_other_links_valid": size - wrong,
                }
            )
    retain(Path(__file__).resolve())
    require(
        all(sha(ROOT / name) == expected for name, expected in pins.items()), "Unchanged sources"
    )
    result = {
        "source_sha256": pins,
        "radius_m": list(RADII),
        "after_report_minutes": list(MINUTES),
        "shifted_day_offsets": list(OFFSETS),
        "shifted_days_are_confirmed_negatives": False,
        "matching_origin_verified_cases": 0,
        "cases_without_usable_source_time_for_screen": ["H14"],
        "source_hypotheses": results,
        "hypothetical_link_error": pool,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "pu_link_sensitivity_v1" / stamp
    out.mkdir(parents=True, exist_ok=False)
    receipt = out / "readback.json"
    write_json(receipt, result)
    print(receipt.relative_to(ROOT).as_posix(), sha(receipt))


if __name__ == "__main__":
    main()
