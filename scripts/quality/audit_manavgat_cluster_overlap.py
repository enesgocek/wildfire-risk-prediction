"""Compare which published Manavgat starts share exploratory satellite components."""

import csv
from datetime import UTC, datetime, timedelta
from itertools import combinations
from pathlib import Path
from uuid import uuid4

import pandas as pd
from prepare_pu_calendar_sample import digest
from review_manavgat_reported_starts import CATALOG
from run_stratified_cover_pilot import BASE, ROOT, read_json, write_json

from wildfire_risk_prediction.event_review import GEOD, training_detections
from wildfire_risk_prediction.feature_join import require

MANAVGAT = BASE / "manavgat_reported_starts_v1/20261108T022757Z_358ef972/readback.json"
GRAPH = BASE.parent / "events/review_v1/20261010T001137Z_320433ed/review.json"
RADII = (1000, 2000, 3000)


def catalogue_matches(cases, detections):
    matched = {}
    for case in cases:
        start = pd.Timestamp(case["reported_start_utc"])
        end = pd.Timestamp(case["prediction_utc"]) + timedelta(days=1)
        daily = detections.loc[detections.timestamp.ge(start) & detections.timestamp.le(end)]
        lon, lat = case["approximate_lon_lat"]
        distances = GEOD.inv(
            [lon] * len(daily), [lat] * len(daily), daily.longitude, daily.latitude
        )[2]
        for radius, previous in zip(RADII, case["scenarios"], strict=True):
            ids = set(daily.loc[distances <= radius, "detection_id"])
            require(
                previous["radius_m"] == radius
                and len(ids) == previous["catalogue_rows_at_or_after_reported_start"],
                "Reconciled Manavgat counts",
            )
            matched[case["case"], radius] = ids
    return matched


def summarize(cases, radius, matched, assignments, first):
    groups = {
        case["case"]: set(assignments.loc[sorted(matched[case["case"], radius]), "cluster_id"])
        for case in cases
    }
    later = {
        case["case"]: {
            group
            for group in groups[case["case"]]
            if first.loc[group] >= pd.Timestamp(case["reported_start_utc"])
        }
        for case in cases
    }
    pairs = [
        {
            "cases": [a, b],
            "shared_components": len(groups[a] & groups[b]),
            "same_only_component": len(groups[a]) == len(groups[b]) == 1,
            "shared_components_with_no_earlier_record": len(later[a] & later[b]),
        }
        for a, b in combinations(groups, 2)
        if groups[a] & groups[b]
    ]
    return {
        "radius_m": radius,
        "cases": [
            {
                "case": n,
                "matching_components": len(groups[n]),
                "components_with_no_earlier_record": len(later[n]),
            }
            for n in groups
        ],
        "overlapping_pairs": pairs,
    }


def main():
    pins = {}

    def retain(path, expected):
        require(digest(path) == expected, "Frozen audit input")
        pins[path.relative_to(ROOT).as_posix()] = expected
        return path

    prior = read_json(
        retain(MANAVGAT, "cf24f1c2839f3f92942de1d569644e599a84a854b76cb5263cd6e1871e3c7b9e")
    )
    graph = read_json(
        retain(GRAPH, "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e")
    )
    cases = prior["cases"]
    require(
        len(cases) == 7
        and all(c["target"] is None for c in cases)
        and graph["source_sha256"] == prior["source_sha256"][CATALOG]
        and graph["scenario_selected"] is None,
        "Frozen evidence scope",
    )
    with retain(ROOT / CATALOG, graph["source_sha256"]).open(encoding="utf-8-sig", newline="") as f:
        detections = training_detections(
            pd.DataFrame(
                [r for r in csv.DictReader(f) if r["detection_timestamp_utc"].startswith("2021-")]
            )
        )
    matched = catalogue_matches(cases, detections)
    results = []
    for scenario, hashes in sorted(graph["artifact_sha256"].items()):
        assignments = pd.read_csv(
            retain(
                ROOT / f"data/interim/event_grouping/{scenario}_assignments.csv",
                hashes["assignments_sha256"],
            )
        ).set_index("detection_id", verify_integrity=True)
        times = pd.to_datetime(assignments.timestamp, utc=True, format="ISO8601")
        expected = detections.set_index("detection_id").timestamp
        require(times.loc[expected.index].equals(expected), "Exact 2021 assignment times")
        first = times.groupby(assignments.cluster_id).min()
        results.append(
            {
                "scenario": scenario,
                "radii": [
                    summarize(cases, radius, matched, assignments, first) for radius in RADII
                ],
            }
        )
    require(len(results) == 9, "Nine exploratory grouping choices")
    pins[Path(__file__).resolve().relative_to(ROOT).as_posix()] = digest(Path(__file__))
    run = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
    out = BASE / "manavgat_cluster_overlap_v1" / run
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "source_sha256": pins,
        "scenarios": results,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "scenario_selected": None,
    }
    write_json(out / "readback.json", report)
    print((out / "readback.json").relative_to(ROOT).as_posix(), digest(out / "readback.json"))


if __name__ == "__main__":
    main()
