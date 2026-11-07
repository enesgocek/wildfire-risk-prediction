"""Compare two documented incident contexts with frozen FIRMS and EFFIS records."""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import geopandas as gpd
import pandas as pd
from review_pu_candidate_timeline import GRAPH, sha
from review_pu_stable_batch import EFFIS

from wildfire_risk_prediction.event_review import training_detections
from wildfire_risk_prediction.feature_join import require
from wildfire_risk_prediction.perimeter_review import effis_gml

ROOT = Path(__file__).resolve().parents[2]
BASE = "outputs/reports/dataset"
DISPATCH = {
    "urla": (
        f"{BASE}/izmir_dispatch_context_v1/20261107T231548Z_ae86420f/readback.json",
        "5168e06ef72e6da9ebd7190d06b93141418acea34e9c60a01c93ac48d88ad49d",
    ),
    "karaburun": (
        f"{BASE}/izmir_dispatch_context_v1/20261107T231523Z_42caa85a/readback.json",
        "0c3b4f3aa7206ce7e674ecf5db6b855f4993ed40d840a4af31a8a8cc5e4e3a6a",
    ),
}
CASES = (
    ("urla_karaburun", "2021-08-14", "52498"),
    ("aydincik_pembecik", "2021-07-15", "50667"),
)


def source_detections(path, expected_skipped):
    rows, skipped = [], 0
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["detection_timestamp_utc"].startswith("2024-"):
                skipped += 1
            else:
                rows.append(row)
    require(skipped == expected_skipped, "Comparison years excluded")
    return training_detections(pd.DataFrame(rows))


def select_contexts(refs, points):
    result = {}
    for code, day, polygon_id in CASES:
        reference = refs.loc[refs.reference_id.eq(polygon_id)]
        require(len(reference) == 1, "Exact reference polygon")
        ref = reference.iloc[0]
        require(ref.geometry_valid and ref.FIREDATE.startswith(day), "Pinned reference date")
        begin = pd.Timestamp(day, tz="UTC")
        matches = points.loc[
            points.geometry.within(ref.geometry) | points.geometry.touches(ref.geometry)
        ]
        nearby_days = matches.loc[
            matches.timestamp.gt(begin - pd.Timedelta(days=3))
            & matches.timestamp.le(begin + pd.Timedelta(days=2))
        ]
        day_rows = nearby_days.loc[
            nearby_days.timestamp.gt(begin) & nearby_days.timestamp.le(begin + pd.Timedelta(days=1))
        ]
        require(not day_rows.empty, "Case requires at least one same-day spatial witness")
        first = day_rows.timestamp.min()
        first_rows = day_rows.loc[day_rows.timestamp.eq(first)]
        result[code] = {
            "day": day,
            "effis_id": polygon_id,
            "effis_start_as_reported": ref.FIREDATE,
            "effis_end_as_reported": ref.FINALDATE,
            "effis_area_ha_as_reported": float(ref.AREA_HA),
            "in_perimeter_earlier_three_utc_days": int(nearby_days.timestamp.le(begin).sum()),
            "in_perimeter_utc_day_rows": len(day_rows),
            "first_in_perimeter_utc": first.isoformat(),
            "first_in_perimeter_ids": sorted(first_rows.detection_id),
            "first_in_perimeter_cells": sorted(set(first_rows.grid_id)),
            "scenarios": [],
            "target": None,
        }
    return result


def attach_scenarios(contexts, graph, retain):
    for name, expected in sorted(graph["artifact_sha256"].items()):
        assignments = pd.read_csv(
            retain(
                f"data/interim/event_grouping/{name}_assignments.csv",
                expected["assignments_sha256"],
            )
        ).set_index("detection_id", verify_integrity=True)
        catalogue = pd.read_csv(
            retain(f"{GRAPH}/{name}_review.csv", expected["review_sha256"])
        ).set_index("cluster_id", verify_integrity=True)
        require(len(assignments) == graph["training_detection_count"], "Assignment scope")
        for row in contexts.values():
            groups = sorted(set(assignments.loc[row["first_in_perimeter_ids"], "cluster_id"]))
            row["scenarios"].append(
                {
                    "scenario": name,
                    "groups": [
                        {
                            "cluster_id": group,
                            "first_utc": catalogue.loc[group, "first_detection_utc"],
                            "member_count": int(catalogue.loc[group, "detection_count"]),
                            "first_cells": json.loads(
                                catalogue.loc[group, "earliest_grid_ids_json"]
                            ),
                        }
                        for group in groups
                    ],
                }
            )


def main():
    pins = {}

    def retain(name, expected):
        path = ROOT / name
        require(path.resolve(strict=True).is_relative_to(ROOT), "Contained input")
        require(sha(path) == expected, f"Source hash mismatch: {name}")
        pins[name] = expected
        return path

    graph = json.loads(
        retain(
            f"{GRAPH}/review.json",
            "61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e",
        ).read_text()
    )
    table = source_detections(
        retain("data/interim/firms_combined_candidates_2018_2024.csv", graph["source_sha256"]),
        graph["validation_rows_excluded"],
    )
    require(len(table) == graph["training_detection_count"], "Frozen catalogue scope")
    points = gpd.GeoDataFrame(
        table, geometry=gpd.points_from_xy(table.longitude, table.latitude), crs=4326
    )
    refs = effis_gml(
        retain(
            EFFIS, "351506b52949e292aaaf62b51556ae0cfd9d553c2c198d24b81ecdb758e65eba"
        ).read_bytes()
    )
    require(len(refs) == 84, "Frozen EFFIS slice")
    contexts = select_contexts(refs, points)
    attach_scenarios(contexts, graph, retain)
    dispatch = {
        name: json.loads(retain(path, expected).read_text(encoding="utf-8"))
        for name, (path, expected) in DISPATCH.items()
    }
    urla = dispatch["urla"]["event_context_rows"]
    require(len(urla) == 5 and len(dispatch["karaburun"]["event_context_rows"]) == 3, "API scope")
    report = next(row for row in urla if row["_id"] == 7632)
    require(
        report["TARIH"].startswith("2021-08-14")
        and report["CIKIS_SAATI"] == "07:28"
        and report["ILCE"] == "URLA"
        and report["YANGIN_TURU"].startswith("ORMAN/"),
        "Independent dispatch row identity",
    )
    contexts["urla_karaburun"]["dispatch_context"] = report
    contexts["urla_karaburun"]["dispatch_time_is_ignition"] = False
    for name in (
        Path(__file__).relative_to(ROOT).as_posix(),
        "src/wildfire_risk_prediction/event_review.py",
        "src/wildfire_risk_prediction/perimeter_review.py",
    ):
        retain(name, sha(ROOT / name))
    require(all(sha(ROOT / name) == expected for name, expected in pins.items()), "Inputs changed")
    result = {
        "status": "public_incident_context_compared_no_exact_origin_match",
        "source_sha256": pins,
        "cases": contexts,
        "daily_observation_status": "unknown",
        "positive_label_permitted": False,
        "negative_label_permitted": False,
        "labels_created": False,
        "final_merge_performed": False,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    path = ROOT / BASE / "public_reference_cases_v1" / stamp / "readback.json"
    path.parent.mkdir(parents=True, exist_ok=False)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    require(json.loads(path.read_text(encoding="utf-8")) == result, "JSON readback")
    print(path.relative_to(ROOT).as_posix(), sha(path), "pins", len(pins))
    for code, row in contexts.items():
        counts = {
            (len(scenario["groups"]), tuple(group["first_utc"] for group in scenario["groups"]))
            for scenario in row["scenarios"]
        }
        print(code, row["in_perimeter_utc_day_rows"], row["first_in_perimeter_utc"], sorted(counts))


if __name__ == "__main__":
    main()
